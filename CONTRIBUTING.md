# Contributing to DocMax

Thanks for helping. This project is deliberately strict about architecture, so a few minutes
with this page will save you a review round.

## Set up

```bash
git clone https://github.com/megabyte44/docmax.git
cd docmax
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

Before you push, run the same gate CI runs:

```bash
pytest && ruff check . && ruff format --check . && mypy && lint-imports
```

## Read these first

[CLAUDE.md](CLAUDE.md) holds the ten working rules (written for AI agents, equally useful for
people). Most are enforced by a test, so breaking one fails the build. The ones that trip up
newcomers:

- **No per-tool code in an interface.** A tool is declared once in its `ToolSpec`; the CLI, TUI,
  server and MCP adapter are generated from it. If you need a surface to know something about a
  tool, add a spec field.
- **Library code raises, only `cli` exits.** Raise a typed error from `core/errors.py` with a `remedy`.
- **Only `core/atomic.py` writes files.**
- **Heavy imports live inside functions.** `docmax --help` must not import a document library.

If you disagree with a rule, change the relevant ADR in [docs/adr/](docs/adr/) and its test in the
same pull request. Please don't work around it.

## Adding a tool

1. `src/docmax/tools/<name>/tool.py`: the `ToolSpec`. Copy `merge/tool.py`.
2. `src/docmax/tools/<name>/local.py`: the strategy, with heavy imports inside methods.
3. `src/docmax/tools/<name>/validators.py`: what makes the output correct.
4. `tests/unit/test_<name>.py`: only behaviour specific to the tool.
5. A command in `src/docmax/cli/commands.py`, copying the shape of its neighbours exactly.

## Pull requests

- Keep each PR to one change. Link the issue it closes.
- Add or update tests. A bug fix starts with a test that fails.
- Update [CHANGELOG.md](CHANGELOG.md) for anything a user would notice.
- Commit messages use a bracket tag: `[FEATURE] add X`, `[FIX] handle Y`, `[DOCS] clarify Z`.

## Regenerating the README demos

The GIFs in `docs/assets/` are rendered from real command output:

```bash
pip install -e . pillow
python scripts/make_demo_gifs.py        # CLI demos, from real command output
pip install -e ".[tui]"
python scripts/make_tui_gif.py          # TUI demo, driving the real Textual app
```

## Conduct

Be kind and assume good faith. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
