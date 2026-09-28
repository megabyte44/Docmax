"""The local engine for ``merge``.

Nothing in here is imported until the router has resolved ``local`` for a
``merge`` call — which is why the pypdf import sits inside the methods that use
it rather than at module scope. ``tests/hygiene/test_no_heavy_imports.py`` runs
that check in a subprocess.

The strategy declares no base class. It satisfies ``EngineStrategy`` structurally,
and :func:`build`'s return annotation is what makes mypy verify that it does.

## Non-PDF inputs

``merge`` now accepts any file that LibreOffice can export as PDF — which covers
the common Office formats (PPTX, DOCX, ODT, ODP, XLS, XLSX, …) as well as
plain text, HTML, and images. A non-PDF input is silently converted to a
temporary PDF before merging, so the output is always a single, valid PDF.

If LibreOffice is not installed, the tool raises :class:`LocalDependencyMissingError`
*only when at least one non-PDF input is present* — a merge of PDFs still needs
nothing beyond pypdf.
"""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from docmax.core.errors import (
    CorruptDocumentError,
    EncryptedDocumentError,
    ExternalToolFailedError,
    InvalidParameterError,
    UnsupportedFormatError,
)
from docmax.core.models import Engine, ToolResult
from docmax.tools import _binaries

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pypdf import PdfReader

    from docmax.core.cancellation import CancellationToken
    from docmax.core.models import DocumentRef, OutputTarget
    from docmax.core.protocols import EngineStrategy, ProgressSink

DEPENDENCY = "pypdf"

# Extensions that pypdf can open directly.
_PDF_SUFFIXES = frozenset({".pdf"})

# Extensions LibreOffice can export to PDF.  This is intentionally broad —
# LibreOffice itself decides whether it handles the file; we only need to know
# that we should *try* to convert rather than hard-refuse.
_SOFFICE_SUFFIXES = frozenset(
    {
        # Presentations
        ".pptx", ".ppt", ".odp", ".pps", ".ppsx",
        # Word-processor documents
        ".docx", ".doc", ".odt", ".rtf",
        # Spreadsheets
        ".xlsx", ".xls", ".ods", ".csv",
        # Other
        ".txt", ".html", ".htm",
    }
)


class MergeLocal:
    """Concatenate PDFs (and Office documents) with pypdf + LibreOffice."""

    def is_available(self) -> bool:
        # find_spec, not an import: availability is asked on every routing
        # decision, including the ones that end up choosing the other engine.
        return importlib.util.find_spec(DEPENDENCY) is not None

    def unavailable_reason(self) -> str | None:
        if self.is_available():
            return None
        return f"{DEPENDENCY} is not installed."

    def run(
        self,
        docs: Sequence[DocumentRef],
        target: OutputTarget,
        *,
        progress: ProgressSink,
        cancellation: CancellationToken,
        **params: Any,
    ) -> ToolResult:
        """Merge ``docs`` into ``target``, in the order given.

        Non-PDF inputs are converted to PDF by LibreOffice first.  Pure-PDF
        merges never touch LibreOffice, so the dependency is optional unless
        you actually pass a non-PDF file.

        **Progress convention, worth copying.** The tool calls ``start`` and
        ``advance``; it does *not* call ``finish``. Only the tool knows what the
        work is called and how many units it has, and only the router can
        guarantee the region closes on every path — it does so in a ``finally``.
        A tool that finished its own sink would double-finish on the happy path
        and still leak on the paths it did not anticipate.
        """
        import time

        from docmax.core.atomic import atomic_write
        from docmax.tools.merge.validators import is_readable_pdf, page_count_is

        if not docs:
            raise InvalidParameterError(
                "Merge needs at least one document.",
                remedy="Pass the files to merge, in the order you want them.",
            )

        outline = self._outline_option(params)
        started = time.monotonic()

        # Decide up-front whether we need LibreOffice.  Only count suffixes that
        # _SOFFICE_SUFFIXES knows about — an unknown extension will be refused
        # inside _convert_to_pdf with UnsupportedFormatError, which is more
        # informative than "soffice missing" and should always fire first.
        needs_conversion = any(
            d.suffix.lower() in _SOFFICE_SUFFIXES for d in docs
        )
        soffice_path: str | None = None
        if needs_conversion:
            soffice_path = _binaries.require("soffice", tool="merge")

        # pypdf is imported here rather than at module scope so that discovering
        # this tool — which happens on every `--help` — costs nothing.
        from pypdf import PdfWriter

        writer = PdfWriter()
        bookmarks: list[tuple[str, int]] = []

        progress.start(f"Merging {len(docs)} document(s)", total=len(docs))

        # We use a single temp directory for all LibreOffice conversions.
        # It is cleaned up whenever the run finishes (success, error, cancel).
        with tempfile.TemporaryDirectory(prefix="docmax_merge_") as tmp_str:
            tmp = Path(tmp_str)
            for document in docs:
                # Between files is the safe checkpoint: nothing is on disk yet.
                cancellation.raise_if_cancelled(operation="merge")

                if document.suffix.lower() in _PDF_SUFFIXES:
                    pdf_path = document.path
                else:
                    pdf_path = self._convert_to_pdf(
                        document,
                        tmp,
                        soffice=soffice_path,  # type: ignore[arg-type]
                        cancellation=cancellation,
                    )

                reader = self._open_pdf(pdf_path, original_name=document.path.name)
                bookmarks.append((document.path.stem, len(writer.pages)))
                for page in reader.pages:
                    writer.add_page(page)
                progress.advance()

        if outline:
            for title, first_page in bookmarks:
                writer.add_outline_item(title, first_page)

        pages = len(writer.pages)
        cancellation.raise_if_cancelled(operation="merge")

        with atomic_write(
            target,
            validators=(is_readable_pdf, page_count_is(pages)),
        ) as handle:
            writer.write(handle)

        return self._result(
            target,
            duration_ms=int((time.monotonic() - started) * 1000),
            pages=pages,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _outline_option(params: dict[str, Any]) -> bool:
        """Read the ``outline`` parameter, or explain what it should have been.

        Declared in ``tool.py`` as a bool defaulting to true. Both interfaces
        validate parameters against that declaration before calling, so this is
        a second line rather than the first — but a library caller reaches this
        method directly, and ``outline="yes"`` silently meaning *true* is the
        class of bug the project's config layer already refuses.
        """
        value = params.get("outline", True)
        if isinstance(value, bool):
            return value
        raise InvalidParameterError(
            f"outline must be true or false, not {value!r}.",
            remedy="Pass --outline or --no-outline.",
            context={"parameter": "outline"},
        )

    @staticmethod
    def _convert_to_pdf(
        document: DocumentRef,
        tmp: Path,
        *,
        soffice: str,
        cancellation: CancellationToken,
    ) -> Path:
        """Convert *document* to PDF with LibreOffice and return the PDF path.

        LibreOffice writes ``<stem>.pdf`` into the directory given by
        ``--outdir``.  We use a private temp directory so concurrent runs
        cannot collide, and so cleanup is automatic.
        """
        suffix = document.suffix.lower()
        if suffix not in _SOFFICE_SUFFIXES:
            # Known-PDF suffixes were handled before this call; anything that
            # reaches here and is also not a known Office format gets a typed
            # refusal that names the fix instead of a confusing LibreOffice error.
            raise UnsupportedFormatError(
                f"merge cannot convert {document.path.name} to PDF automatically. "
                f"Supported non-PDF formats: {', '.join(sorted(_SOFFICE_SUFFIXES))}.",
                context={"path": str(document.path), "suffix": document.suffix},
            )

        _binaries.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmp),
                str(document.path),
            ],
            tool="merge",
            cancellation=cancellation,
        )

        expected = tmp / (document.path.stem + ".pdf")
        if not expected.exists():
            raise ExternalToolFailedError(
                f"LibreOffice did not produce {expected.name} for {document.path.name}.",
                context={"path": str(document.path), "expected": str(expected)},
            )
        return expected

    @staticmethod
    def _open_pdf(path: Path, *, original_name: str) -> PdfReader:
        """Open a PDF path, raising typed errors that name what went wrong."""
        from pypdf import PdfReader
        from pypdf.errors import PyPdfError

        try:
            reader = PdfReader(str(path))
        except (PyPdfError, OSError, ValueError) as exc:
            raise CorruptDocumentError(
                f"{original_name} could not be read as a PDF: {exc}",
                context={"path": str(path)},
            ) from exc

        if reader.is_encrypted:
            # Checked before touching .pages, which raises its own error for
            # this case with a far less useful message.
            raise EncryptedDocumentError(
                f"{original_name} is password-protected.",
                context={"path": str(path)},
            )

        return reader

    def _result(self, target: OutputTarget, *, duration_ms: int, pages: int) -> ToolResult:
        """Shape of what ``run`` returns, once it does.

        ``engine_version`` names whatever actually did the work, in the same
        form the cloud engine reports it (``gs/10.03.0``), so a result is
        traceable to an implementation regardless of which engine produced it.
        """
        from importlib.metadata import version

        return ToolResult(
            outputs=(target.destination,),
            engine_used=Engine.LOCAL,
            duration_ms=duration_ms,
            engine_version=f"{DEPENDENCY}/{version(DEPENDENCY)}",
            details={"pages": pages},
        )


def build() -> EngineStrategy:
    """Factory the registry calls. Every strategy module exposes exactly this."""
    return MergeLocal()


__all__ = ["MergeLocal", "build"]
