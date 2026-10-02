# DocMax

<p align="center">
  <strong>Terminal-native document engineering toolkit.</strong><br>
  Local-first · Dual-engine · Atomic safety · AI-agent ready via MCP
</p>

<p align="center">
  <a href="https://pypi.org/project/Docmax/"><img src="https://img.shields.io/pypi/v/Docmax.svg?color=blue&style=flat-square" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/Docmax/"><img src="https://img.shields.io/pypi/pyversions/Docmax.svg?style=flat-square" alt="Python Versions"></a>
  <a href="https://github.com/megabyte44/docmax/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-Compatible-8A2BE2.svg?style=flat-square" alt="MCP Compatible"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square" alt="Ruff"></a>
  <a href="https://github.com/python/mypy"><img src="https://img.shields.io/badge/type_checker-mypy-blue.svg?style=flat-square" alt="MyPy"></a>
</p>

---

## Overview

**DocMax** is a high-performance, terminal-native document toolkit for developers, power users, and AI assistants. Merge, split, OCR, compress, convert, protect, sanitize, watermarking, and reorder PDFs and images — locally, privately, with no background servers or browser dependencies required.

```bash
# Install the core CLI
pip install Docmax

# Combine PDFs with source bookmarks
docmax merge report_q1.pdf report_q2.pdf -o annual_report.pdf

# OCR a scanned PDF with auto-deskewing
docmax ocr scan.pdf -o searchable.pdf --lang eng+fra

# Compress a heavy PDF using Ghostscript presets
docmax compress document.pdf -o compressed.pdf --preset ebook

# Connect directly to your AI assistant (Claude Desktop, Cursor, Claude Code)
docmax mcp connect
```

---

## Why DocMax?

Most document tools require running heavy web services (Docker containers, local HTTP servers, browser tabs) or rely on fragile, non-atomic shell scripts that can corrupt documents on interruption.

DocMax takes a **terminal-native, architecture-first** approach:

| Feature | DocMax | Traditional Web Tools | Ad-Hoc Scripts |
|---|:---:|:---:|:---:|
| **Installation** | Single `pip install` | Docker + container orchestration | Fragmented CLI tools |
| **Interface** | CLI, Full-Screen TUI & MCP | Web browser UI | Terminal only |
| **Scripting & CI/CD** | Native argv + `--json` | REST API against running daemon | Shell scripts |
| **Over SSH / Headless** | First-class native support | Requires SSH port forwarding | Works |
| **AI Assistant (MCP)** | Built-in stdio & HTTP bridge | Unsupported / Custom bridge | Custom wrappers |
| **Integrity Guarantees** | Atomic staging & validation | Varies by service | Vulnerable to partial writes |
| **Document Privacy** | 100% Local by default | Local server | Local machine |

---

## Architectural Guarantees & Safety

DocMax was built from the ground up to prevent destructive file operations and silent data loss. Every guarantee is enforced through automated tests across Linux, macOS, and Windows:

- **Atomic File Swaps:** All outputs are written to temporary staging files, verified, and only then atomically swapped into place via `core/atomic.py`. If a process is interrupted or fails midway, your target file remains intact or absent — never half-written.
- **In-Place Overwrite Prevention:** Input files can never be used as the output destination (`docmax merge a.pdf b.pdf -o a.pdf` is refused before processing begins).
- **Accidental Overwrite Protection:** Overwriting an existing destination strictly requires the `--force` flag.
- **Zero Raw Tracebacks:** Known errors produce human-actionable messages with clear remedy hints (or structured JSON objects in automated pipelines).
- **Predictable Cleanups:** Intermediate files from pipelines, OCR rasterizations, and image conversions live in isolated temporary directories that are automatically purged on success, cancellation, or error.

---

## Core Capabilities

### 1. Dual-Engine Architecture (Local vs. Cloud)

Every tool can run two ways, with your privacy always in your control:

- **Local Engine (Default):** Runs 100% offline on your machine using local binaries and Python libraries.
- **Cloud Engine (Optional):** Offloads compute-heavy operations (`compress`, `convert`, `ocr`) to an external or self-hosted Cloud Engine server without requiring heavy local system dependencies.

```bash
docmax ocr scan.pdf                     # Automatically selects available engine
docmax ocr scan.pdf --engine local      # Forces local offline processing
docmax ocr scan.pdf --engine cloud      # Offloads processing to cloud engine
```

> **Privacy Contract:** Nothing is ever transmitted to the cloud without explicit consent. Consents are granted per-tool via `docmax cloud agree`, recorded locally, and can be revoked at any time. Setting `offline = true` in your configuration permanently disables all outbound network traffic regardless of flags.

### 2. Four Unified Interfaces

DocMax provides four consistent entry points into the exact same registry and engine router:

1. **UNIX CLI:** Standard UNIX semantics, flag-driven execution, and a global `--json` mode for scripting.
2. **Interactive TUI:** Full-terminal dashboard powered by Textual (`docmax tui` or simply typing `docmax` in an interactive shell).
3. **Visual Pickers:** Interactive browser-assisted helpers (`--interactive`) for visual tasks like bounding-box selection (`docmax crop`) and page sequencing (`docmax reorder`). They compute coordinates and return them to the CLI without touching the original document.
4. **Model Context Protocol (MCP):** Connects your tools directly to LLM agents (Claude Desktop, Cursor, Claude Code, Cline) via stdio or streamable HTTP.

---

## Complete Tool Suite

DocMax provides over 20+ purpose-built tools across document and image workflows:

### PDF Assembly & Page Operations
| Command | Description | Engine |
|---|---|:---:|
| `docmax merge` | Combine multiple PDFs in specified order with bookmarks/outline preservation | Local |
| `docmax split` | Split PDF into individual pages or specific range-based output files | Local |
| `docmax rotate` | Rotate entire document or specified pages by 90°, 180°, or 270° | Local |
| `docmax pages` | Extract or drop specific pages and ranges (`1-3,5,7-end`) | Local |
| `docmax reorder` | Rearrange page sequences manually or via visual drag-and-drop (`--interactive`) | Local |
| `docmax crop` | Trim page margins to explicit point coordinates or visual box (`--interactive`) | Local |

### Security, Sanitation & Inspection
| Command | Description | Engine |
|---|---|:---:|
| `docmax protect` | Encrypt PDF with AES-256 / AES-128 and granular access permissions | Local |
| `docmax unlock` | Remove encryption from password-protected documents | Local |
| `docmax permissions` | Inspect active PDF encryption flags, permissions, and security restrictions | Local |
| `docmax sanitize` | Scrub metadata, hidden annotations, JavaScript, forms, and embedded files | Local |
| `docmax metadata` | Read or update document title, author, subject, keywords, and producer | Local |
| `docmax get-info` | Fast document summary (page count, dimensions, PDF version, encryption) | Local |

### Document Enhancement & Conversion
| Command | Description | Engine |
|---|---|:---:|
| `docmax ocr` | Generate searchable PDFs with Tesseract OCR, auto-deskew, and language selection | Local / Cloud |
| `docmax compress` | Optimize and downsample PDFs via Ghostscript presets (`screen`, `ebook`, `printer`) | Local / Cloud |
| `docmax watermark` | Apply custom text watermarks with opacity, rotation, and 9 alignment anchors | Local |
| `docmax stamp` | Overlay a page from another PDF as a stamp or official letterhead | Local |
| `docmax convert` | Convert documents between Markdown, HTML, Word, ODT, LaTeX, EPUB, and TXT | Local / Cloud |
| `docmax to-images` | Rasterize PDF pages to high-resolution PNG, JPEG, or TIFF images | Local |
| `docmax from-images` | Assemble raster images into a single PDF (lossless JPEG passthrough) | Local |

### Image Processing
| Command | Description | Engine |
|---|---|:---:|
| `docmax compress-image` | Lossy and lossless image compression (JPEG, PNG, WebP) | Local |
| `docmax convert-image` | Transcode between modern image formats (PNG, JPEG, WebP, TIFF, BMP) | Local |
| `docmax resize` | Scale images by dimensions, scale factor, or aspect-fit bounds | Local |
| `docmax remove-bg` | AI-powered automatic background removal via `rembg` | Local |
| `docmax watermark-image` | Overlay text or watermark stamps onto image assets | Local |

---

## Installation & Setup

### Package Extras

DocMax maintains an ultra-lightweight base installation. Advanced dependencies are isolated into modular extras:

```bash
# Core installation (pure Python, fast install)
pip install Docmax

# Add specific capabilities
pip install "Docmax[ocr]"       # OCR image pre-processing & deskewing
pip install "Docmax[tui]"       # Interactive Textual dashboard
pip install "Docmax[crypto]"    # AES-256 PDF encryption/decryption
pip install "Docmax[mcp]"       # Model Context Protocol server for AI assistants
pip install "Docmax[images]"    # Advanced image rasterization and assembly
pip install "Docmax[tables]"    # Table extraction from PDFs
pip install "Docmax[remove-bg]" # AI-powered background removal

# Install all features
pip install "Docmax[all]"
```

### External Binaries

Certain local engines rely on battle-tested system binaries:
- **Ghostscript** (`gs`): Used by `compress`
- **Tesseract** (`tesseract`): Used by `ocr`
- **Poppler** (`pdftoppm`): Used by `to-images` and `ocr`
- **Pandoc** (`pandoc`): Used by `convert`

DocMax makes checking and installing these effortless:

```bash
# Inspect system dependency status
docmax doctor

# Automatically install missing binaries for your platform (brew / apt / winget)
docmax setup
```

---

## Power Workflows: Pipelines, Batch & Watch

Compose and automate operations across documents without writing glue code:

### 1. Multi-Stage Pipelines (`docmax pipeline`)

Chain multiple tools into a single, cohesive operation defined in a simple TOML configuration:

```toml
# clean_scan.toml
name = "clean-scan"

[[stage]]
tool = "ocr"
params = { lang = "eng", dpi = 300 }

[[stage]]
tool = "compress"
params = { preset = "ebook" }

[[stage]]
tool = "watermark"
params = { text = "CONFIDENTIAL", opacity = 0.2, position = "center" }
```

Run the pipeline:
```bash
docmax pipeline unverified_scan.pdf --pipeline clean_scan.toml -o final_document.pdf
```
*Guaranteed safety:* Intermediate stages write only to an isolated temporary sandbox. If stage three fails, intermediate files are cleanly discarded and your destination remains untouched.

### 2. Resilient Batch Processing (`docmax batch`)

Process hundreds of files in bulk with independent error handling:

```bash
docmax batch incoming/*.pdf --output-dir processed/ --tool ocr
```
*Resilient execution:* If file 14 is corrupted, it is logged with a structured error while the remaining 199 files proceed to completion.

### 3. Directory Watcher (`docmax watch`)

Monitor drop directories and automatically process arriving files:

```bash
docmax watch ~/Downloads/Scans --output-dir ~/Documents/Archive --tool ocr
```
*Loop and race protection:* Incoming files are processed only after their byte size has settled across polling intervals, and output directories cannot overlap watched directories.

---

## AI Agent Integration (MCP)

DocMax turns your local document tools into an extensible tool suite for AI assistants via the **Model Context Protocol (MCP)**.

### Auto-Configuration

Connect DocMax to your local AI applications with a single command:

```bash
docmax mcp connect
```

This automatically detects and safely updates configurations for **Claude Desktop**, **Claude Code**, and **Cursor**, inserting the server definition:

```json
{
  "mcpServers": {
    "docmax": {
      "command": "docmax",
      "args": ["mcp", "--root", "/path/to/documents"]
    }
  }
}
```

### Security & Agent Sandboxing

When driven by an AI agent, DocMax enforces strict security perimeters:
- **Directory Confinement (`--root`):** The agent cannot read or write outside designated directories. Path traversal (`..`) and symlink escapes are strictly rejected.
- **Destructive Overwrites Forbidden:** Overwrite flags (`--force`) are disabled for agent invocations. Existing destinations return structured errors.
- **No Unsolicited Cloud Uploads:** Cloud execution is disabled by default. An agent cannot grant consent on your behalf.
- **Cancellation Propagation:** Interrupting a running agent request triggers immediate cancellation of the underlying worker thread, leaving files undamaged.

---

## Scripting & Automation (`--json`)

Every DocMax command supports global machine-readable output:

```bash
docmax get-info sample.pdf --json
```

Output:
```json
{
  "ok": true,
  "data": {
    "pages": 12,
    "title": "Quarterly Report",
    "encrypted": false,
    "pdf_version": "1.7",
    "file_size": 245120
  }
}
```

Diagnostics and progress bars are routed exclusively to `stderr`, leaving `stdout` clean for programmatic consumption.

---

## Developer Guide & Architecture

DocMax is structured with a strict, lint-enforced layered architecture ([ADR 0035](docs/adr/0035-remote-mcp-is-a-transport-bridge-over-the-cloud-server.md)):

```
   CLI Interface (docmax.cli)          TUI Interface (docmax.tui)
             \                                    /
              v                                  v
     Engine Router (docmax.core.router) <--> Tool Registry (docmax.core.registry)
             /                                    \
            v                                      v
  Local Tools (docmax.tools.*)            Shared Schemas (docmax.mcpschema)
            |                                      |
            v                                      v
     Atomic Writers & Protocols             Model Context Protocol (docmax.mcp)
```

### Contributing & Development

```bash
# Clone repository
git clone https://github.com/megabyte44/docmax.git
cd docmax

# Set up virtual environment and development dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run test suite & linters
pytest
ruff check .
mypy
lint-imports
```

Explore our architectural documentation:
- [Architecture Overview](docs/architecture/overview.md) — Structural design and constraints
- [Architectural Decision Records (ADRs)](docs/adr/README.md) — The rationale behind every core decision
- [Implementation Guides](docs/implementation/core.md) — Deep dives into core, runner, and MCP subsystems

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
