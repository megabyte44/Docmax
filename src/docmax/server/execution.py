"""The bridge from an HTTP request back to the registry.

This is the part that makes the server a thin adapter rather than a second
implementation of the product. It resolves a tool name against the same registry
the CLI uses and runs the same ``EngineStrategy`` — the *local* one. That is the
whole trick of the Cloud Engine: the server is a machine that already has
Ghostscript, Tesseract, and a LaTeX distribution installed, running exactly the
code a user would run if they had installed them too.

So the cloud engine is not a separate feature with separate behaviour, and a
cloud result cannot quietly diverge from a local one. There is one
implementation of ``compress``; the only question is whose machine it runs on.

## Jobs run here, in this request

Synchronously, in the request that submitted them.
[ADR 0016](../../../docs/adr/0016-jobs-run-in-process.md) records why and what
it costs — no broker to deploy, and no durability across a restart. The wire
contract already permits it: the small-file path is specified as a synchronous
``200`` carrying the output, and the client treats a terminal job as finished
without polling. A future queued implementation can start answering ``202``
without a client change, which is the property that makes this reversible.

## The input is deleted either way

The contract says documents are deleted "on job completion or failure", and
those are different words for a reason. The discard happens in a ``finally``,
so a tool that raises leaves nothing behind — the case that is easy to write
and easy to get wrong.
"""

from __future__ import annotations

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from docmax.core.atomic import atomic_write
from docmax.core.branding import CLI_NAME
from docmax.core.cancellation import NEVER_CANCELLED
from docmax.core.errors import DocMaxError, InternalError
from docmax.core.models import DocumentRef, Engine, JobStatus, OutputTarget
from docmax.core.registry import get_tool

if TYPE_CHECKING:
    from docmax.core.registry import ToolSpec
    from docmax.server.jobs import Job
    from docmax.server.storage import Storage


#: Names the staging directory so an operator looking at a full disk can tell
#: whose temp files they are. Built from ``CLI_NAME`` because
#: ``core/branding.py`` is the only module allowed to spell the brand out.
_TEMP_PREFIX = f"{CLI_NAME}-job-"


class ToolRunner(Protocol):
    """Whatever actually performs the work behind an endpoint."""

    def resolve(self, tool_name: str) -> ToolSpec:
        """Find the tool, or explain that this endpoint does not offer it."""
        ...

    def start(
        self,
        job: Job,
        payload: bytes,
        *,
        filename: str,
        base_url: str,
        storage: Storage,
        owner: str,
        extra_payloads: list[tuple[bytes, str]] | None = None,
    ) -> Job:
        """Begin the work. May finish synchronously or leave the job running.

        ``base_url`` is passed per call rather than held on the runner because
        it belongs to the request — a server reachable by two names must hand
        each caller back a URL on the name they used, not on whichever one
        started the process.

        ``owner`` is the caller's identity (its API key), threaded through so
        the output this call produces is reserved in storage under the same
        owner as the job and its input — see ADR 0035.

        ``extra_payloads`` carries additional ``(bytes, filename)`` pairs for
        tools that accept multiple inputs (``accepts_multiple_inputs=True``,
        e.g. ``merge`` and ``from-images``). The primary ``payload``/``filename``
        is always the first document; these are appended in order.
        """
        ...


@dataclass(slots=True)
class RegistryRunner:
    """Runs tools through the registry, in this process."""

    def resolve(self, tool_name: str) -> ToolSpec:
        """Resolve the tool from the registry.

        Every registered tool can run here via the server's local engine —
        the server is a machine that already has the binaries installed. The
        Cloud-only filter that once lived here was removed when the remote MCP
        route was extended to expose all tools, not just the cloud-capable
        subset. ``EngineNotSupportedError`` is still raised for the genuine
        "no local engine at all" case (a tool with neither engine declared),
        but that cannot happen today: every registered tool has a local engine.
        """
        return get_tool(tool_name)

    def start(
        self,
        job: Job,
        payload: bytes,
        *,
        filename: str,
        base_url: str,
        storage: Storage,
        owner: str,
        extra_payloads: list[tuple[bytes, str]] | None = None,
    ) -> Job:
        """Stage the payload(s), run the local engine over them, publish the output.

        ``extra_payloads`` carries additional ``(bytes, filename)`` pairs for
        tools that accept multiple inputs (``merge``, ``from-images``,
        ``stamp``). All inputs are staged into the same temp directory.
        """
        spec = self.resolve(job.tool)
        strategy = spec.load_strategy(Engine.LOCAL)

        job.status = JobStatus.RUNNING
        started = time.monotonic()

        # `ignore_cleanup_errors` because a tool holding a handle open on
        # Windows must not turn a finished job into a 500 on the way out.
        with tempfile.TemporaryDirectory(prefix=_TEMP_PREFIX, ignore_cleanup_errors=True) as work:
            root = Path(work)
            # Build the full ordered list of (bytes, filename) pairs, primary first.
            all_inputs: list[tuple[bytes, str]] = [(payload, filename)]
            if extra_payloads:
                all_inputs.extend(extra_payloads)

            # Stage every input into a uniquely-named file in the temp dir so
            # names from different uploads cannot collide. The suffix is
            # preserved because tools decide what to read from it.
            sources: list[Path] = []
            for idx, (inp_bytes, inp_name) in enumerate(all_inputs):
                safe = _safe_name(inp_name)
                # Prefix with index so two uploads with the same filename
                # (e.g. two "document.pdf"s passed to merge) don't collide.
                dest_name = f"{idx}_{safe}" if len(all_inputs) > 1 else safe
                staged = root / dest_name
                with atomic_write(OutputTarget(destination=staged, force=True)) as handle:
                    handle.write(inp_bytes)
                sources.append(staged)

            # A directory-producing tool (`ToolSpec.produces_directory`, ADR
            # 0031) writes into `output/` as a real directory -- appending
            # `default_suffix` would turn it into a file-shaped path the local
            # engine then creates as a directory anyway. See ADR 0034.
            if spec.produces_directory:
                destination = root / "output"
            else:
                destination = root / f"output{spec.default_suffix}"
            try:
                result = strategy.run(
                    [DocumentRef.from_path(s) for s in sources],
                    OutputTarget(destination=destination, force=True),
                    progress=_NO_PROGRESS,
                    cancellation=_NEVER,
                    **job.params,
                )
            except DocMaxError as exc:
                return _fail(job, exc, started)
            except Exception as exc:
                # Anything untyped escaping a tool is that tool's bug. Wrapped
                # here for the same reason the router wraps it: a request must
                # answer with the contract's envelope, never a traceback.
                return _fail(
                    job,
                    InternalError(
                        f"The local engine for {job.tool!r} failed unexpectedly: {exc}",
                        context={"tool": job.tool},
                    ),
                    started,
                )

            if spec.produces_directory:
                # The wire contract carries exactly one file per job. A
                # directory's many outputs travel as a zip archive -- the same
                # shape the client's `CloudEngine` unpacks on the way back in.
                # See ADR 0034 and `tools/_archive.py`.
                from docmax.tools._archive import zip_directory

                output_bytes = zip_directory(destination)
                output_name = f"{destination.name}.zip"
            else:
                produced = Path(result.outputs[0]) if result.outputs else destination
                output_bytes = produced.read_bytes()
                output_name = produced.name

        # Outside the temp directory: the staged input and the tool's output are
        # both gone by now, and what survives is the copy in storage.
        file_id = storage.reserve(filename=output_name, size_bytes=len(output_bytes), owner=owner)
        storage.put(file_id, output_bytes, owner=owner)

        job.status = JobStatus.SUCCEEDED
        job.duration_ms = result.duration_ms or int((time.monotonic() - started) * 1000)
        job.engine_version = result.engine_version
        job.output_url = f"{base_url.rstrip('/')}/v1/outputs/{file_id}"
        job.output_size_bytes = len(output_bytes)
        job.output_content_type = (
            "application/zip" if spec.produces_directory else _content_type(output_bytes)
        )
        return job


def _fail(job: Job, error: DocMaxError, started: float) -> Job:
    job.status = JobStatus.FAILED
    job.error = error
    job.duration_ms = int((time.monotonic() - started) * 1000)
    return job


def _safe_name(filename: str) -> str:
    """The submitted name, reduced to something that cannot escape the temp dir.

    A filename arrives from the network. ``Path(filename).name`` drops any
    directory part, so ``../../etc/passwd`` becomes ``passwd``; an empty or
    all-separator name falls back to a fixed one. The *suffix* matters and is
    kept, because tools decide what they will read from it — ``convert`` reads
    ``.md`` and refuses ``.pdf``, and that decision has to survive the trip.
    """
    stem = Path(filename).name.strip()
    return stem or "document"


def _content_type(payload: bytes) -> str:
    """Mirror of ``routes/outputs.py``'s sniff, so the job and the download agree."""
    if payload.startswith(b"%PDF-"):
        return "application/pdf"
    return "application/octet-stream"


class _NullProgress:
    """The server reports progress over HTTP status, not over a sink."""

    def start(self, description: str, *, total: int | None = None) -> None:
        """Ignore."""

    def advance(self, amount: int = 1) -> None:
        """Ignore."""

    def finish(self) -> None:
        """Ignore."""


_NO_PROGRESS = _NullProgress()


#: The request *is* the job's lifetime here, so there is nothing to cancel it
#: from — an HTTP client that disconnects has already stopped waiting, and the
#: contract has no cancel endpoint. A queued implementation would carry a real
#: token; ADR 0015 and ADR 0016 both name that as future work.
_NEVER = NEVER_CANCELLED


__all__ = ["RegistryRunner", "ToolRunner"]
