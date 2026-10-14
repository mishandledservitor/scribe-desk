# Tasks: Scribe Desk runs from any folder with no machine-specific paths

**Input**: `specs/004-portable-paths/plan.md`, `specs/004-portable-paths/spec.md`

- [X] T001 Write a test in `test_scribedesk_stt.py` that `load_api_key` checks only the repo's `.env` when the environment has no key, and show it failing.
- [X] T002 Write `test_launchers.py`: with a fake sibling virtual environment under a temporary `HOME` and no repo `venv/`, `scribe-desk-stt` exits 1 and names `setup.sh`. Show it failing.
- [X] T003 Write `test_build_app.py`: the built bundle has a 1.0.0 `Info.plist`, an executable launcher, the icon, and, once moved, starts the repo's GUI script. Show it failing.
- [X] T004 Write `test_repo_hygiene.py`: no tracked file contains a home-folder path or the former sibling tool's name. Show it failing.
- [X] T005 Remove the fallback from `scribedesk_stt.py` and `scribe-desk-stt` (T001, T002 green).
- [X] T006 Add `build_app.py`, move the icon to `app/icon.icns`, point `make_icon.py` at it, call the builder from `setup.sh`, untrack `Scribe Desk.app` and ignore it (T003 green).
- [X] T007 Clean the remaining home-folder paths and sibling-tool mentions from docs and docstrings (T004 green).
- [X] T008 Run the full suite.
