"""Metadata for ``merge``.

This module is imported during discovery — every time the tool list is built, on
every ``--help``. So it imports nothing but ``core`` and does no work at import
time. The pypdf import lives in ``local.py``, which nobody touches until this
tool is actually run.
"""

from __future__ import annotations

from docmax.core.models import Engine
from docmax.core.registry import Param, ToolSpec, register

SPEC = register(
    ToolSpec(
        name="merge",
        summary=(
            "Combine PDFs (and Office documents) into one PDF, in the order given. "
            "PPTX, DOCX, ODT, XLSX and other LibreOffice-supported formats are "
            "converted to PDF automatically when LibreOffice is installed."
        ),
        category="assemble",
        module=__name__.rpartition(".")[0],
        # No cloud engine, deliberately. See the module docstring.
        supported_engines=frozenset({Engine.LOCAL}),
        accepts_multiple_inputs=True,
        default_suffix=".pdf",
        # soffice is only needed when a non-PDF input is present; it is listed
        # here so `doctor` can surface it and guide the user to install it.
        requires_binaries=("soffice",),
        params=(
            Param(
                name="outline",
                description="Add a bookmark per source file, named after it.",
                type_="bool",
                default=True,
            ),
        ),
    )
)

__all__ = ["SPEC"]
