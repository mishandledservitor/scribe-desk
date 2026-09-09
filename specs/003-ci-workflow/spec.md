# Feature Specification: A GitHub Actions workflow runs the test suite on every push

**Feature Branch**: `ci/test-workflow`

**Created**: 2026-09-09

**Status**: Draft

**Input**: Board P0, queue row `scribe-desk-add-ci-workflow` (dashboard chat `728161623e8441c194acc3f161f2e0dd`, 2026-09-09): the census found no CI in this repository — the cleanest of the five small products relies on someone running the tests by hand to know it is green. Add a GitHub Actions workflow that runs `python3 -m pytest -q` and `python3 -m unittest test_scribedesk_gui -v` on every push, without hanging on the GUI test's Tk usage.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A push shows green or red without anyone running tests by hand (Priority: P1)

A maintainer pushes a commit, or opens a pull request against `main`. Without doing anything else, they can look at the GitHub Actions tab and see whether the test suite passed. Today that is only knowable by checking out the branch and running two commands locally.

**Why this priority**: this is the entire ask — the repository has no automated signal of its own health.

**Independent Test**: push a commit to a branch with this workflow present and confirm a workflow run appears and completes with a real pass/fail verdict, not stuck or skipped.

**Acceptance Scenarios**:

1. **Given** a push to any branch or a pull request targeting `main`, **When** the workflow runs, **Then** it executes `python3 -m pytest -q` as one step and `python3 -m unittest test_scribedesk_gui -v` as a second, separate step, so a failure names which command failed.
2. **Given** the GUI test module, **When** the workflow runs it on a GitHub-hosted Ubuntu runner (no display), **Then** the run completes rather than hanging — because the module only unit-tests the plain functions behind the Tk callbacks and never calls `tk.Tk()` outside `if __name__ == "__main__":`, the workflow only needs `tkinter` importable, not a virtual display.

### Edge Cases

- A GitHub-hosted Ubuntu runner has no window server. `test_scribedesk_gui.py`'s own module docstring states it constructs no widget tree; confirmed by reading `scribedesk_gui.py`, where `tk.Tk()` appears exactly once, inside `main()`, which only runs under the `if __name__ == "__main__":` guard the tests never exercise. The workflow therefore installs the OS `python3-tk` package (so `import tkinter` succeeds) and does not install or invoke `xvfb-run`.
- Ubuntu's system Python may mark itself "externally managed" (PEP 668), refusing a bare `pip install`. The workflow creates a virtual environment before installing `pytest`, which sidesteps that restriction without assuming a particular Ubuntu image version, and still sees the system `tkinter` because a venv shares the base interpreter's standard-library and lib-dynload directories.

## Requirements *(mandatory)*

- **FR-001**: The workflow MUST trigger on `push` and `pull_request` events targeting `main`.
- **FR-002**: The workflow MUST run on an Ubuntu GitHub-hosted runner with a current Python 3.
- **FR-003**: The workflow MUST install exactly what the tests need: `pytest`, plus the OS Tk bindings (`python3-tk`) so `scribedesk_gui` (imported by its test module) can `import tkinter`. It MUST NOT install or invoke `xvfb-run`, since no widget tree is ever constructed under test.
- **FR-004**: The workflow MUST run `python3 -m pytest -q` and `python3 -m unittest test_scribedesk_gui -v` as two separate steps, so a failing step names which command failed.
- **FR-005**: The workflow file MUST be valid YAML.

## Success Criteria *(mandatory)*

- **SC-001**: `.github/workflows/test.yml` parses as YAML.
- **SC-002**: Both test commands, run locally exactly as the workflow spells them, exit 0.
- **SC-003**: A deliberately broken assertion in one test makes the corresponding command exit non-zero, proving the workflow's step would actually catch a regression.
