# Implementation Plan: Scribe Desk runs from any folder with no machine-specific paths

**Branch**: `release-public` | **Spec**: `specs/004-portable-paths/spec.md`

## Summary

Drop the sibling-tool fallback from `load_api_key` and `scribe-desk-stt`. Replace the tracked app bundle, whose launcher fell back to a hardcoded home-folder path when moved, with `build_app.py`, which writes the bundle into the repo with the repo's absolute path baked in. `setup.sh` calls it. The icon moves to `app/icon.icns` and `make_icon.py` writes there.

## Technical Context

- **Language**: Python 3 standard library (`plistlib`, `shlex`, `shutil`) and Bash.
- **Testing**: unittest-style tests collected by pytest. The launcher tests run the real scripts with `subprocess` in temporary folders.
- **Target platform**: macOS for the bundle; the tests also run on the Ubuntu CI runner, where the bundle launcher is exercised with the system `python3` and `python3-tk`.

## Constitution check

- **I. Test-First**: each requirement gets a failing test before the code changes.
- **II. Data-Loss Safety**: no change to deletion, registry or settings code.
- **III. Slug and Path Identity**: no change to slug handling. Repo-relative paths stay resolved from `SCRIPT_DIR`.
- **IV. Reproduce against the real artefact**: the launcher tests run the real scripts, copied into a sandbox.

## Design

- `build_app.build(dest_dir, repo_dir)` returns the bundle path. It writes `Contents/Info.plist` with `plistlib`, copies `app/icon.icns` to `Contents/Resources/icon.icns`, and writes `Contents/MacOS/scribe-desk` from a template with `REPO=<shlex-quoted path>`. The launcher keeps the existing tkinter interpreter probe and `app-launch.log`.
- The bundle is not code-signed. It is created locally, so it carries no quarantine flag and Gatekeeper does not block it.
