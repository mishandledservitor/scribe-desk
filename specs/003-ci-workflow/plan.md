# Implementation Plan: A GitHub Actions workflow runs the test suite on every push

**Branch**: `ci/test-workflow` | **Spec**: `specs/003-ci-workflow/spec.md`

## Summary

Add a single-file GitHub Actions workflow, `.github/workflows/test.yml`, that checks out the repository on an Ubuntu runner, installs `python3-tk` (so `tkinter` imports without a display) and `pytest` into a virtual environment, then runs `python3 -m pytest -q` and `python3 -m unittest test_scribedesk_gui -v` as two separate steps. No application code changes; no requirements file exists or is added, matching the repo's "standard library plus pytest" shape.

## Technical Context

- **Language**: Python 3 (standard library + pytest; no other third-party runtime dependency).
- **Testing**: `test_scribedesk_config.py`, `test_scribedesk_stt.py` run under pytest; `test_scribedesk_gui.py` is invoked via `unittest` per the row's original wording, and per repo CLAUDE.md rule 6 (`test_scribedesk_stt.py` needs no install) and rule 5 (GUI verification hazard: `tk.Tk()` blocks with no window server).
- **Target platform**: GitHub-hosted `ubuntu-latest` runner — no display, no window server.
- **Project type**: single three-module tool, no build step.
- **Scope**: exactly `.github/workflows/test.yml` and `specs/003-ci-workflow/`. No other path in this repository is touched by this feature.

## Key decision: no `xvfb-run`

Read `test_scribedesk_gui.py` in full before writing the workflow. Its own docstring states the tests exercise plain functions behind the Tk callbacks, never a live widget tree, because `tk.Tk()` is only ever called from `main()` in `scribedesk_gui.py`, itself gated by `if __name__ == "__main__":`. `import scribedesk_gui` therefore only needs `tkinter` to be importable (the OS `python3-tk` package on a bare Ubuntu image), not a running display. Installing `xvfb-run` and wrapping the command would be unneeded complexity for a hazard this codebase does not currently have; the workflow does not carry it. If a future change to `scribedesk_gui.py` or its test module constructs a widget outside that guard, this decision needs revisiting — noted here so the next reader does not have to re-derive it.

## Key decision: a virtualenv, not a bare `pip install`

Ubuntu images newer than 22.04 mark the system Python "externally managed" (PEP 668) and refuse a bare `pip install`. Rather than assume which Ubuntu version `ubuntu-latest` resolves to on a given day, or reach for `--break-system-packages`, the workflow creates a venv with `python3 -m venv` before installing `pytest`. A venv shares the base interpreter's standard library and `lib-dynload` directory (only third-party `site-packages` are isolated), so the `python3-tk` package installed against the system interpreter is still visible inside it — proven locally in this same worktree (see `tasks.md` verification step).

## Constitution check

No constitution file exists for this repo (`.specify/memory/constitution.md` is absent; the repo's own CLAUDE.md says Spec Kit is not otherwise set up here, and this dispatch's brief names spec number 3 for this one feature). No conflict: this is process-only, no application code, and stays inside the two paths this dispatch owns.

## Phase 0: research

Covered above (both "why not xvfb", "why a venv"). No `research.md` needed beyond what is written here — no open unknowns remain.

## Phase 1: design

No data model, no contracts, no new code — a workflow file has no runtime behaviour of its own beyond invoking existing test commands. `tasks.md` covers the concrete steps and the local proof.
