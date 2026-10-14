# Feature Specification: Scribe Desk runs from any folder with no machine-specific paths

**Feature Branch**: `release-public`

**Created**: 2026-10-14

**Status**: Implemented

**Input**: Owner decision for the 1.0.0 public release: remove the hardcoded home-folder paths and the fallback to a private sibling tool's virtual environment and `.env`. Paths come from settings or from the repo folder. Keep `Scribe Desk.app` tracked only if it works from any folder; otherwise have `setup.sh` build it and stop tracking it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A fresh clone works wherever it is cloned (Priority: P1)

Someone clones the repo into any folder, runs `setup.sh`, adds their key to `.env` in the repo, and transcribes. Nothing in the tool looks in a folder that only existed on the author's machine.

**Independent Test**: with `ELEVENLABS_API_KEY` unset, `load_api_key` consults only the repo's own `.env`. With no `venv/` in the repo, `scribe-desk-stt` exits with an instruction to run `setup.sh`, even when another tool's virtual environment exists under the home folder.

**Acceptance Scenarios**:

1. **Given** no key in the environment, **When** the CLI loads the key, **Then** the only file it reads is `.env` next to `scribedesk_stt.py`.
2. **Given** no `venv/` in the repo, **When** `scribe-desk-stt` runs, **Then** it exits with status 1 and names `setup.sh`.

### User Story 2 - The app bundle finds the repo after it is moved (Priority: P1)

`setup.sh` builds `Scribe Desk.app` inside the repo with the repo's own location written into its launcher. The user can leave it there or drag it to `/Applications` or the Dock, and it still opens the GUI from this clone.

**Independent Test**: build the bundle against a temporary repo folder, move the bundle elsewhere, run its launcher, and confirm it starts that repo's `scribedesk_gui.py`.

**Acceptance Scenarios**:

1. **Given** a built bundle, **When** its `Info.plist` is read, **Then** the version is 1.0.0 and the executable and icon entries point at files inside the bundle.
2. **Given** a built bundle moved to another folder, **When** its launcher runs, **Then** it starts the GUI of the repo it was built from, with the repo as its working folder.

### Edge Cases

- A repo path containing spaces or quotes must survive being written into the launcher.
- The built bundle is generated output, so it is ignored by git, and rebuilding it overwrites the old one.

## Requirements *(mandatory)*

- **FR-001**: `load_api_key` MUST read `ELEVENLABS_API_KEY` from the environment first and otherwise only from the repo's own `.env`.
- **FR-002**: `scribe-desk-stt` MUST use only the repo's own `venv/`.
- **FR-003**: `build_app.py` MUST build `Scribe Desk.app` with the absolute repo path baked into its launcher, and `setup.sh` MUST run it.
- **FR-004**: `Scribe Desk.app` MUST NOT be tracked; its icon lives at `app/icon.icns`.
- **FR-005**: No tracked file MAY contain a home-folder path or the name of the former sibling tool.

## Success Criteria *(mandatory)*

- **SC-001**: The new tests in `test_scribedesk_stt.py`, `test_launchers.py`, `test_build_app.py` and `test_repo_hygiene.py` fail before the change and pass after it.
- **SC-002**: The full suite passes locally and in CI.
