# CHANGE_ME

Standard Python project layout. The public/user-facing software lives in `src/`, with tests in `tests/` and runnable examples in `demos/`.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Test

```bash
python -m pytest -q tests
```

## Demo

```bash
python demos/smoke_demo.py
```

## Repository layout

```text
src/        installable project code
tests/      public regression/unit tests
demos/      small runnable examples
ai-tools/   optional AI-assisted research/development workbench
```

`ai-tools/` is intentionally self-contained and optional. It contains agent orchestration, research logs, experimental workspaces, provider/account configuration examples, and advisor/coder tooling. **Users who only want the software can ignore `ai-tools/` completely.**

Developers who want the AI research workflow can start at [`ai-tools/README.md`](ai-tools/README.md).
