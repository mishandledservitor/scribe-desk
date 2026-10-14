# Implementation Plan: A recycled project slug no longer adopts or destroys another project's transcripts

**Branch**: `098-recycled-slug-transcripts` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-recycled-slug-transcripts/spec.md`

## Summary

Three bugs in `scribedesk_config.py`, all reproduced by the 2026-09-01 adversarial review, get fixed together because the fix touches the same module: (1) slug allocation (`unique_slug`) must treat an existing `output/<candidate>` folder as taken, using the same three-way check `_migrate_locked` already implements correctly, so a recreated project never inherits a deleted-but-kept project's transcripts folder; (2) `_read_registry_or_rebuild` must raise on a genuine `OSError` (unreadable file) instead of treating it the same as a `JSONDecodeError` (corrupt file) and silently replacing the whole registry; (3) keyterm normalization in `load_settings`/`save_settings` must split only on newline, not comma, so a keyterm containing a comma survives as one term. Each fix ships with a red-first regression test in a new `test_scribedesk_config.py`, run against a real copy of the module repointed at a `tmp_path`-style sandbox — never a hand-built fixture, never a real transcript directory.

## Technical Context

**Language/Version**: Python 3 (matches the rest of the repo; no version pin beyond what's already implied by `from __future__ import annotations`)

**Primary Dependencies**: Standard library only — `json`, `os`, `re`, `shutil`, `tempfile`, `unittest`, `fcntl` (POSIX, already guarded with an ImportError fallback in the module). No new dependency.

**Storage**: Local filesystem JSON files (`projects.json`, `config/<slug>.json`) and plain-text transcript files under `output/<slug>/`. N/A for any external store.

**Testing**: `unittest`, run via `python3 -m unittest test_scribedesk_config -v`, matching the existing two test modules' convention (no pytest, no install). Tests reassign the module's path constants (`SCRIPT_DIR`/`INBOX_DIR`/`OUTPUT_DIR`/`PROCESSED_DIR`/`CONFIG_DIR`/`PROJECTS_FILE`) to a `tempfile.mkdtemp()` sandbox per test, the same technique the review's own probe scripts used.

**Target Platform**: macOS desktop (the module also runs stubbed on other POSIX/Windows via the `fcntl` fallback, unchanged by this feature).

**Project Type**: Single-project CLI/GUI-backing library — one flat module, no framework, no build step.

**Performance Goals**: N/A — this is a correctness fix on infrequent, human-triggered operations (create/delete a project, save settings). No new hot path.

**Constraints**: No behavior change to any currently-correct path: existing single-collision slug allocation, existing corrupt/empty-registry rebuild, and existing keyterm handling for comma-free entries must all continue to work exactly as before. No GUI dialog wiring in this feature (the GUI widget tree cannot be exercised in this environment, per the repo's own CLAUDE.md rule 5); the new registry-unreadable error is raised at the `scribedesk_config.py` layer with the path and reason in its message, ready for the GUI to catch and display.

**Scale/Scope**: Three functions changed (`unique_slug`, `_read_registry_or_rebuild`, `load_settings`/`save_settings`'s shared keyterm normalization), one new shared helper for the three-way in-use check, one new test file. No schema migration needed — no on-disk format changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Test-First (NON-NEGOTIABLE)**: PASS by construction — Phase 2 (`/speckit-tasks`) orders a failing test before each fix, and `/speckit-implement` must run each test red before writing the fix. No GUI wiring is touched, so the GUI exception in this principle does not need to be invoked.
- **II. Data-Loss Safety Over Convenience**: PASS — this feature exists to close two data-loss/data-hiding gaps and is checked directly by SC-001/SC-002 (old transcripts survive; project list is never silently emptied).
- **III. Slug and Path Identity Discipline**: PASS — FR-001/FR-002 explicitly unify the three-way check into one shared definition instead of leaving two divergent copies, which is the named standard.
- **IV. Reproduce Against the Real Artefact, Never a Fixture Built From the Bug Report**: PASS — Technical Context above commits to reassigning the real module's path constants in a `tmp_path`-style sandbox, never a hand-rolled stand-in, and never a real transcript directory.

No violations. Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-recycled-slug-transcripts/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

No `contracts/` directory: this feature changes an internal library module (`scribedesk_config.py`) consumed only by the GUI and CLI inside this same repo. There is no external API, network endpoint, or cross-repo contract to document — the closest thing to a contract is the function signatures themselves, which `data-model.md` covers under "Key operations."

### Source Code (repository root)

```text
scribedesk_config.py         # unique_slug, _read_registry_or_rebuild, load_settings,
                              # save_settings all modified; one new shared helper added
test_scribedesk_config.py    # NEW — the module had zero test coverage (review finding 3,
                              # out of scope to fully close here, but this feature's three
                              # tests are its first entries and follow the pattern any
                              # later completion of that finding should extend)
```

**Structure Decision**: Single flat module, matching the rest of the repo (`scribedesk_config.py`, `scribedesk_gui.py`, `scribedesk_stt.py` at the repository root, "no framework, no build step" per the repo's own CLAUDE.md). The new test file follows the existing sibling tests' naming and location (`test_scribedesk_gui.py`, `test_scribedesk_stt.py` are both at repo root, not under a `tests/` directory) — consistency with the two existing test files outweighs the generic template's `tests/` layout suggestion.

## Complexity Tracking

*No violations — table not needed.*
