"""The TUI's colour palettes.

Two themes, registered by ``DocMaxApp`` and switchable from Textual's own
command palette (``ctrl+p``). Every colour in ``tui/styles.py`` is a design
*token* (``$primary``, ``$surface``, ``$error`` ...), never a literal, so a
palette is the only thing that has to change to restyle the whole application --
the same one-seam reasoning ``core/branding.py`` applies to the product's name.

The dark palette is a cool ink background with a blue primary and a teal accent:
the primary carries actions (Run, focus), the accent carries structure (headings,
the active tool), and the three status colours are kept far enough apart in hue
that success, warning and failure never read as one another.

This module imports Textual, like the rest of ``docmax.tui``, and nothing imports
``docmax.tui`` except the CLI's guarded entry point, so the base install is
unaffected.
"""

from __future__ import annotations

from textual.theme import Theme

from docmax.core.branding import CLI_NAME

DARK = Theme(
    name=CLI_NAME,
    primary="#5b8def",
    secondary="#8b7cf6",
    accent="#2dd4bf",
    foreground="#e6e9ef",
    background="#0e1117",
    surface="#151a23",
    panel="#1c2330",
    success="#4ade80",
    warning="#fbbf24",
    error="#f87171",
    dark=True,
)

LIGHT = Theme(
    name=f"{CLI_NAME}-light",
    primary="#2f62d8",
    secondary="#6d5bdb",
    accent="#0f9d8f",
    foreground="#1b2230",
    background="#f6f7fb",
    surface="#ffffff",
    panel="#e9ecf4",
    success="#16a34a",
    warning="#b7791f",
    error="#dc2626",
    dark=False,
)

#: The theme a fresh session starts in.
DEFAULT = DARK.name

THEMES = (DARK, LIGHT)

__all__ = ["DARK", "DEFAULT", "LIGHT", "THEMES"]
