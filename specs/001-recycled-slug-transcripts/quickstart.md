# Quickstart: validating this feature

All three scenarios below reproduce and then verify a real defect against the real module. Every command runs inside a scratch temp directory and never touches this repository's own `config/`, `output/`, or `projects.json`.

## Prerequisites

- Python 3 (standard library only, no install step).
- A scratch sandbox directory, created fresh per scenario, e.g. `mkdir -p /tmp/sd-quickstart && cd /tmp/sd-quickstart`.
- A copy of `scribedesk_config.py` from this feature branch on `sys.path` (or run `test_scribedesk_config.py` directly from the repo root, which does this via monkeypatched constants — see below).

## Running the regression suite

```sh
cd /Users/simon/git/vantage-labs/vl-projects/scribe-desk-wt-fix5
python3 -m unittest test_scribedesk_config -v
```

Expected after implementation: all tests pass, including (at minimum) one test per user story below.

## Scenario 1 — recycled slug no longer adopts old transcripts (User Story 1 / SC-001)

1. In a sandbox with the module's path constants repointed at it, call `add_project("Acme")`.
2. Write a file into `managed_output_dir("acme")` (simulating a finished transcript).
3. Call `delete_project("acme", delete_output=False)` — the project is removed but the transcript file remains on disk.
4. Call `add_project("Acme")` again.
5. **Expected**: the new project's slug is NOT `acme` (it is `acme-2` or similar), and its managed output folder does not contain the transcript written in step 2.
6. Call `delete_project(<new slug>, delete_output=True)`.
7. **Expected**: the transcript written in step 2 still exists on disk afterward.

## Scenario 2 — an unreadable registry raises instead of erasing (User Story 2 / SC-002)

1. In a sandbox, call `add_project("Acme")` and `add_project("Podcast")`.
2. Make `projects.json` unreadable, e.g. `os.chmod(PROJECTS_FILE, 0o000)`.
3. Call `list_projects()`.
4. **Expected**: a `ConfigError` is raised naming the registry path; `projects.json` is not renamed to a `.corrupt-*` name, and no new registry is written. (Restore permissions, e.g. `0o644`, in test teardown so cleanup can remove the directory.)

## Scenario 3 — a keyterm with a comma survives (User Story 3 / SC-003)

1. In a sandbox, call `add_project("Acme")`.
2. Call `save_settings("acme", {**DEFAULT_SETTINGS, "keyterms": ["Acme, Inc.", "Dr. Zhang"]})`.
3. Call `load_settings("acme")`.
4. **Expected**: `result["keyterms"] == ["Acme, Inc.", "Dr. Zhang"]` — two entries, the comma-containing one intact.

## Non-goals for this quickstart

- No GUI is launched (no window server available in this environment, per the repo's own CLAUDE.md rule 5).
- No live ElevenLabs API call.
- No scenario ever points the module's path constants at this repository's real `config/`, `output/`, or `projects.json`.
