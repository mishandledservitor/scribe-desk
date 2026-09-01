# Tasks: A recycled project slug no longer adopts or destroys another project's transcripts

**Input**: Design documents from `specs/001-recycled-slug-transcripts/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md (all present)

**Tests**: Explicitly requested by the spec (every user story's Acceptance Scenarios and the feature's SC-004 require a red-first regression test) — tests are included and are not optional for this feature.

**Organization**: Tasks are grouped by user story (spec.md priorities P1/P2/P3), each independently testable.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Create `test_scribedesk_config.py` at repository root with a shared `_Sandbox` test-mixin/helper: for each test, create a fresh `tempfile.mkdtemp()`, monkeypatch the module-level constants `scribedesk_config.SCRIPT_DIR`, `INBOX_DIR`, `OUTPUT_DIR`, `PROCESSED_DIR`, `CONFIG_DIR`, `PROJECTS_FILE` to point inside it, call `scribedesk_config.ensure_dirs()`, and restore the originals plus remove the temp tree in `tearDown`. No mocking of any function under test. Follow the plain-`unittest` style of the existing `test_scribedesk_stt.py`/`test_scribedesk_gui.py` (no pytest).

## Phase 2: Foundational (Blocking Prerequisites)

None beyond Phase 1 — this is a three-function bugfix in one existing module with no new schema, no new dependency, and no shared model work beyond the sandbox harness itself.

**Checkpoint**: Once T001 exists and one trivial smoke test inside it passes (e.g. asserting `list_projects()` returns the seeded "Default" project in an empty sandbox), all three user stories below can proceed in priority order.

---

## Phase 3: User Story 1 - Deleting a project and keeping its transcripts must actually keep them (Priority: P1) 🎯 MVP

**Goal**: A recreated project never gets allocated a slug whose managed output folder already holds another project's (kept-on-delete) transcripts.

**Independent Test**: Run `test_recreated_project_does_not_adopt_kept_transcripts` in isolation — it must fail against today's code and pass after the fix, with no dependency on Phase 4/5 changes.

### Tests for User Story 1 ⚠️ write first, confirm red against today's code

- [ ] T002 [US1] In `test_scribedesk_config.py`, write `test_recreated_project_does_not_adopt_kept_transcripts`: `add_project("Acme")` → write a file into `managed_output_dir("acme")` → `delete_project("acme", delete_output=False)` → `add_project("Acme")` again → assert the new entry's `slug` != `"acme"` AND assert the file written earlier is absent from the new project's `managed_output_dir(<new slug>)`. Then `delete_project(<new slug>, delete_output=True)` and assert the original file still exists on disk.
- [ ] T003 [US1] Run `python3 -m unittest test_scribedesk_config.test_recreated_project_does_not_adopt_kept_transcripts -v`, confirm it fails, and paste the red output into the PR/commit evidence (per the dispatch brief's red-first requirement). Do not proceed to T004 until this failure is captured.

### Implementation for User Story 1

- [ ] T004 [US1] In `scribedesk_config.py`, add a private helper `_slug_in_use(candidate: str, taken: set[str]) -> bool` returning `candidate in taken or (CONFIG_DIR / f"{candidate}.json").exists() or (OUTPUT_DIR / candidate).exists()`, placed near `unique_slug`.
- [ ] T005 [US1] In `scribedesk_config.py`, change `unique_slug`'s inner `in_use` check to call `_slug_in_use(candidate, taken)` instead of its current two-way check (adds the output-folder check).
- [ ] T006 [US1] In `scribedesk_config.py`, replace `_migrate_locked`'s inline three-way `while` condition with a call to `_slug_in_use(new, taken)` so both call sites share one definition (behavior-preserving there; refactor only).
- [ ] T007 [US1] Update the docstring comment above `unique_slug` (currently: "Archived settings ... deliberately don't reserve a slug") to also note that a stray/kept output folder now does reserve the slug, so a future reader does not "fix" this back out.
- [ ] T008 [US1] Re-run `python3 -m unittest test_scribedesk_config.test_recreated_project_does_not_adopt_kept_transcripts -v`, confirm it passes, paste the green output.
- [ ] T009 [US1] Run the full existing suites (`python3 -m unittest test_scribedesk_stt -v` and `python3 -m unittest test_scribedesk_gui -v`, if a window server is available for the latter — otherwise state that limitation) to confirm no regression from the `unique_slug`/`_migrate_locked` change.

**Checkpoint**: User Story 1 fully functional and independently verified — this alone is the MVP that closes the CRITICAL finding.

---

## Phase 4: User Story 2 - An unreadable registry fails loudly instead of erasing every project (Priority: P2)

**Goal**: `_read_registry_or_rebuild` raises a `ConfigError` naming the path on a genuine `OSError`, and never renames-and-rebuilds in that case; only `JSONDecodeError` (or empty file) still triggers rebuild.

**Independent Test**: Run `test_unreadable_registry_raises_instead_of_rebuilding` in isolation — passes/fails independent of US1/US3 changes.

### Tests for User Story 2 ⚠️ write first, confirm red against today's code

- [ ] T010 [US2] In `test_scribedesk_config.py`, write `test_unreadable_registry_raises_instead_of_rebuilding`: `add_project("Acme")`, `add_project("Podcast")` → `os.chmod(PROJECTS_FILE, 0o000)` → assert `list_projects()` (or `load_registry()`) raises `scribedesk_config.ConfigError` → assert `PROJECTS_FILE` still exists at its original name (no `.corrupt-*` sibling created) → in `finally`, `os.chmod(PROJECTS_FILE, 0o644)` before teardown removes the sandbox (root-run environments where chmod 000 does not block reads should skip with a clear reason rather than silently passing — note this in the test).
- [ ] T011 [US2] Write a second test, `test_corrupt_json_registry_still_rebuilds`, asserting today's behavior is preserved for a genuinely unparsable file: write invalid bytes to `PROJECTS_FILE`, call `list_projects()`, assert it succeeds, returns a seeded "Default" project, and a `.corrupt-*` sibling file now exists. This one should already pass against today's code (it pins the non-regression half of FR-003) — run it and confirm green before touching implementation, so the later refactor's baseline is known.
- [ ] T012 [US2] Run `python3 -m unittest test_scribedesk_config.test_unreadable_registry_raises_instead_of_rebuilding -v`, confirm it fails against today's code, and paste the red output.

### Implementation for User Story 2

- [ ] T013 [US2] In `scribedesk_config.py`'s `_read_registry_or_rebuild`, split the single `except (OSError, json.JSONDecodeError)` into two: keep `except json.JSONDecodeError` with the existing rename-and-rebuild body unchanged, and add `except OSError as e: raise ConfigError(f"Could not read project registry at {PROJECTS_FILE}: {e}") from e` with no rename and no write.
- [ ] T014 [US2] Re-run both T010's and T011's tests, confirm both pass, paste the output.
- [ ] T015 [US2] Grep the module for any other caller that currently assumes `_read_registry_or_rebuild`/`load_registry` never raises (e.g. `add_project`, `rename_project`, `delete_project`, `set_last_used`, all of which call it under `_lock`) and confirm by inspection that letting `ConfigError` propagate there is acceptable (it already is the module's user-facing error type) — no code change expected here, just confirmation, recorded in the commit message.

**Checkpoint**: User Stories 1 AND 2 both independently verified.

---

## Phase 5: User Story 3 - A keyterm containing a comma stays one term (Priority: P3)

**Goal**: `load_settings`/`save_settings` split keyterms on newline only, not comma, so a comma-containing entry round-trips intact.

**Independent Test**: Run `test_keyterm_with_comma_survives_round_trip` in isolation.

### Tests for User Story 3 ⚠️ write first, confirm red against today's code

- [ ] T016 [US3] In `test_scribedesk_config.py`, write `test_keyterm_with_comma_survives_round_trip`: `add_project("Acme")` → `save_settings("acme", {**DEFAULT_SETTINGS, "keyterms": ["Acme, Inc.", "Dr. Zhang"]})` → `load_settings("acme")` → assert the loaded `keyterms == ["Acme, Inc.", "Dr. Zhang"]` (length 2, comma-containing entry intact).
- [ ] T017 [US3] Run `python3 -m unittest test_scribedesk_config.test_keyterm_with_comma_survives_round_trip -v`, confirm it fails against today's code (splits into more than 2 entries), and paste the red output.

### Implementation for User Story 3

- [ ] T018 [US3] In `scribedesk_config.py`'s `load_settings`, change the keyterms-normalization line from `kt = re.split(r"[,\n]", kt)` to `kt = kt.splitlines()` (only reached when `kt` is a `str`).
- [ ] T019 [US3] Apply the identical change in `save_settings`'s keyterms-normalization block.
- [ ] T020 [US3] Re-run `test_keyterm_with_comma_survives_round_trip`, confirm it passes, paste the output.
- [ ] T021 [US3] Add a small non-regression check in the same test or a sibling one, asserting a keyterms value that is already a clean `list[str]` with no commas is completely unaffected (guards FR-006).

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T022 [P] Run the full `test_scribedesk_config.py` suite once more top-to-bottom (`python3 -m unittest test_scribedesk_config -v`), paste the final green output, and confirm no test leaves anything behind outside its own `tempfile.mkdtemp()` sandbox.
- [ ] T023 [P] Update `CHANGELOG.md`'s Fixed section (or equivalent) describing all three fixes in the terms the repo's own changelog convention uses, and refresh `CLAUDE.md`'s "Current status" per that file's own rule 4 (refresh before each commit).
- [ ] T024 Run `python3 -m unittest test_scribedesk_stt -v` and, if a window server is available, `python3 -m unittest test_scribedesk_gui -v`, to confirm the pre-existing suites are unaffected; if no window server is available, state that plainly rather than silently skipping it unremarked.
- [ ] T025 Run the three quickstart.md scenarios manually once against the finished code as an end-to-end sanity check, distinct from the unittest suite (paranoia pass, catches anything the unit tests' framing missed).

---

## Dependencies & Execution Order

- **Setup (T001)**: no dependencies, must land first.
- **Foundational**: none beyond T001.
- **US1 (T002-T009)**: depends only on T001. Independently testable and deliverable as the MVP (closes the CRITICAL finding alone).
- **US2 (T010-T015)**: depends only on T001; does not depend on US1's changes (different function). Can be done in parallel with US1 by a second contributor, or sequentially after.
- **US3 (T016-T021)**: depends only on T001; touches `load_settings`/`save_settings`, disjoint from both US1 (`unique_slug`/`_migrate_locked`) and US2 (`_read_registry_or_rebuild`). Fully independent.
- **Polish (T022-T025)**: after all three stories are complete.

### Parallel Opportunities

- T002-T009 (US1), T010-T015 (US2), and T016-T021 (US3) touch disjoint functions in the same file, so they are logically parallel-safe but physically the same file — recommend sequential commits in priority order (P1 → P2 → P3) to keep each commit's diff reviewable and each red/green pair unambiguous, rather than true concurrent editing.

## Implementation Strategy

### MVP First

1. T001 (setup harness).
2. Phase 3 (US1) — write red test, capture red, fix `unique_slug`/`_migrate_locked`, capture green. This alone closes the CRITICAL finding and is a valid, independently shippable increment.
3. Stop and validate before continuing, per the dispatch brief's instruction to report an honest partial result if time runs out.

### Incremental Delivery

1. T001 → US1 (P1, MVP) → US2 (P2) → US3 (P3) → Polish, in that order, each with its own red-then-green pair captured before moving to the next.
