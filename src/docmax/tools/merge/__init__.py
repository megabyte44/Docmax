"""Combine PDFs and Office documents into one PDF.

Non-PDF inputs (PPTX, DOCX, ODT, XLSX, …) are converted to PDF by LibreOffice
in headless mode before merging, so the caller always receives a valid PDF.
LibreOffice is only required when at least one non-PDF input is present — a
pure-PDF merge depends only on pypdf, as before.
"""

from __future__ import annotations
