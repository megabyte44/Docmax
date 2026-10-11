"""The TUI's stylesheet.

One string, kept out of ``app.py`` so the screens read as behaviour and this
reads as design. Colours are tokens from the active theme (``tui/theme.py``);
nothing here is a literal colour, so both palettes -- and any theme a user picks
from the command palette -- restyle the whole application.

## The design in four rules

1. **Surfaces step up in lightness.** ``$background`` is the page, ``$surface``
   is a card or the sidebar, ``$panel`` is a control or a bar. Depth comes from
   those three steps, not from borders everywhere.
2. **Blue acts, teal organises.** ``$primary`` is for things you press and the
   focused row; ``$accent`` is for headings, the active item and focus rings.
3. **Buttons are flat and consistent.** One height, no bevel, a clear primary.
   The destructive/stop action is warning-coloured and sits at the far right so
   it is never next to Run by accident.
4. **Status is colour *and* glyph.** Success, warning and error each have their
   own hue and their own icon, so none relies on colour alone.

``Button.tool-button`` keeps the type-plus-class selector on purpose: Textual's
built-in Button style sets its borders as longhand rules that a bare class
selector loses to.
"""

from __future__ import annotations

STYLES = """
Screen { background: $background; }

/* -- type ---------------------------------------------------------------- */

.title { text-style: bold; color: $foreground; padding: 0 0 1 0; }
.hint { color: $text-muted; padding: 0 0 1 0; }
.remedy { color: $accent; padding: 1 0 0 0; }

/* -- controls: flat buttons, quiet inputs ------------------------------------ */

Button {
    border: none;
    height: 3;
    min-width: 12;
    padding: 0 2;
    background: $panel;
    color: $foreground;
    text-style: bold;
}
Button:hover { background: $panel-lighten-1; }
Button:focus { background: $panel-lighten-2; text-style: bold reverse; }
Button.-primary { background: $primary; color: $background; }
Button.-primary:hover { background: $primary-lighten-1; }
Button.-primary:focus { background: $primary-lighten-2; }
Button.-success { background: $success; color: $background; }
Button.-warning { background: $warning; color: $background; }
Button.-warning:hover { background: $warning-lighten-1; }
Button.-error { background: $error; color: $background; }
Button:disabled { background: $surface; color: $text-muted; text-style: none; }

/* Fields are flat, filled single rows: dense enough that a long form (resize,
   watermark) still fits above the action dock, and a focus bar on the left
   edge rather than a box that doubles every field's height. */
Input, Select > SelectCurrent {
    height: 1;
    padding: 0 1;
    background: $panel;
    border: none;
    border-left: outer $panel;
}
Input:hover, Select:hover > SelectCurrent { background: $panel-lighten-1; }
Input:focus, Select:focus > SelectCurrent {
    background: $panel-lighten-1;
    border-left: outer $accent;
}
Input.-invalid, Input.invalid { border-left: outer $error; }
Label { color: $text-muted; text-style: bold; padding: 1 0 0 0; }
.panel > Label:first-of-type { padding: 0; }

DataTable { background: $surface; }
DataTable > .datatable--header { background: $panel; color: $accent; text-style: bold; }
DataTable > .datatable--cursor { background: $primary 35%; }

/* -- chrome: brand header and key-hint footer ----------------------------------- */

.help-bar {
    height: 1;
    background: $panel;
    color: $text-muted;
    padding: 0 2;
}

/* -- workspace: sidebar + preview --------------------------------------------- */

#body { height: 1fr; }

#sidebar {
    width: 40;
    background: $surface;
    padding: 0 1;
}
#search { margin: 1 0 1 0; }
#open-batch { width: 1fr; margin: 0 0 1 0; background: $panel; color: $accent; }
#open-batch:hover { background: $panel-lighten-1; }
#tools { padding: 0 0 1 0; scrollbar-size-vertical: 1; }

.category {
    color: $accent;
    text-style: bold;
    padding: 1 0 0 1;
    border-bottom: solid $panel-lighten-1;
    margin: 0 0 0 0;
}
.tool-column { height: auto; padding: 0; }
Button.tool-button {
    width: auto;
    height: 1;
    min-width: 0;
    margin: 0;
    padding: 0 2;
    border-top: none;
    border-bottom: none;
    background: transparent;
    color: $foreground;
    text-style: none;
    content-align: left middle;
}
Button.tool-button:hover { background: $panel; color: $foreground; border-top: none; }
Button.tool-button:focus {
    background: $primary 35%;
    color: $foreground;
    text-style: bold;
}

#preview {
    width: 1fr;
    padding: 2 4;
}
#preview-title { color: $accent; text-style: bold; padding: 0 0 1 0; }
#preview-body { color: $foreground; }

/* -- run screen: a single card -------------------------------------------------- */

#form { padding: 1 3; }
#batch-form { padding: 1 1 1 3; width: 1fr; }
#batch-live { width: 1fr; margin: 1 3 1 1; height: 1fr; }
#batch-body.-stacked { layout: vertical; }
#batch-body.-stacked #batch-form { padding: 1 3 0 3; height: auto; max-height: 55%; }
#batch-body.-stacked #batch-live { margin: 1 3; }
#batch-bar { width: 1fr; padding: 1 0 0 0; }
#batch-bar Bar { width: 1fr; }
#batch-bar Bar > .bar--bar { color: $primary; background: $panel; }
#batch-bar Bar > .bar--complete { color: $success; }
#batch-stats { padding: 1 0 0 0; }
#open-batch-output { margin-right: 1; }
.panel {
    height: auto;
    border: round $panel-lighten-2;
    background: $surface;
    padding: 1 3;
}
.panel > .title { color: $accent; }

.input-row { height: auto; }
.input-row Input { width: 1fr; }
.input-row Button { margin-left: 1; min-width: 12; height: 1; }
/* issue #25: a typed path that doesn't resolve says so in the field itself,
   not only in the hint line underneath it. */
.input-row Input.invalid { border-left: outer $error; }
.hint.invalid { color: $error; }
.component-row { height: auto; }
.component { width: 1fr; margin-right: 1; height: auto; }
.mode-group { height: auto; }
.component-label { color: $text-muted; text-style: bold; }

/* The action row: Run is the one filled button, secondary actions are quiet,
   and Cancel sits alone at the far right. A rule above separates "what to do"
   from "what to fill in". */
#dock {
    height: auto;
    max-height: 50%;
    background: $surface;
    border-top: solid $panel-lighten-1;
    padding: 0 3;
}
.actions { height: auto; padding: 1 0 0 0; }
.actions Button { margin-right: 1; }
.actions #cancel { dock: right; margin-right: 0; }

/* Hidden by default (`RunScreen.on_mount`); shown by `_show_result_actions`
   once a run has actually succeeded, hidden again by `_start` the moment the
   next one begins. */
.result-actions {
    height: auto;
    margin: 1 0 1 0;
    padding: 1 2;
    background: $success 12%;
    border-left: thick $success;
}
.result-actions Button { margin-right: 1; }

#details { color: $text-muted; padding: 0; height: auto; }

/* Status line: idle / running / succeeded / failed read as distinct states --
   colour and weight driven by ``RunScreen._set_status``'s ``state``, never by
   anything about a particular tool. See issue #26. */
#status { padding: 0; }
#status.status-idle { color: $text-muted; text-style: none; }
#status.status-running { color: $warning; text-style: bold; }
#status.status-success { color: $success; text-style: bold; }
#status.status-error { color: $error; text-style: bold; }

/* -- modals ------------------------------------------------------------------------ */

ModalScreen { align: center middle; background: $background 70%; }
.modal {
    width: 72;
    height: auto;
    padding: 1 3;
    border: round $accent;
    background: $surface;
}
.modal > .title { color: $accent; }
/* Heavier than the round/$accent border every other modal gets: an error is
   deliberately the most visually weighty thing the TUI shows. */
.modal.error { border: heavy $error; background: $error 10%; }
.error-heading { height: auto; padding: 0 0 1 0; }
.error-icon {
    width: auto;
    color: $error;
    text-style: bold;
    padding: 0 1 0 0;
}
.modal.error .title { color: $error; padding: 0; }
.error-message { text-style: bold; padding: 0 0 1 0; }
/* Same weight as `.modal.error`, in `$warning` rather than `$error`: a missing
   dependency is a stop-and-fix condition, but not a failure this run caused --
   see `DependencyMissingScreen` (ADR 0036). */
.modal.warning { border: heavy $warning; background: $warning 10%; }
.modal.warning .title { color: $warning; padding: 0; }

.menu-actions { height: auto; padding: 1 0 0 0; }
.menu-actions Button { width: 1fr; margin-bottom: 1; }

/* -- help, system check, cloud status: static/table content ------------------------ */

#help-content, #system-check-content, #cloud-status-content { padding: 1 3; }
.help-heading {
    color: $accent;
    text-style: bold;
    padding: 1 0 0 0;
}
.help-body { color: $foreground; padding: 0 0 1 0; }
#system-check-table, #cloud-status-table { margin: 1 0; }
#batch-results { margin: 1 0; height: 1fr; }
"""

__all__ = ["STYLES"]
