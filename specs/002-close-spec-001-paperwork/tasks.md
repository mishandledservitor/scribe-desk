# Tasks: Close spec 001's paperwork gap

- [x] T001 Read e3b6242's diff in full, and `specs/001-recycled-slug-transcripts/tasks.md`, `spec.md`, `quickstart.md`, to know what each of the 25 task boxes actually asserts.
- [x] T002 Reproduce the red history: check out `scribedesk_config.py` from e3b6242's parent (5cc0c88) into a scratch directory alongside the shipped `test_scribedesk_config.py`, run it, confirm the three new-feature tests fail and the two non-regression tests already pass, and keep the output.
- [x] T003 Reproduce the green history: run the same test file against `main`'s current (shipped) `scribedesk_config.py`, confirm all five tests pass.
- [x] T004 Run `test_scribedesk_stt -v` against `main` to confirm no regression from the shipped change.
- [x] T005 Attempt the GUI build check per this repo's own rule 5 (`tk.Tk()` + `withdraw()`); report plainly if no window server is available rather than silently skipping it.
- [x] T006 Manually walk `specs/001-recycled-slug-transcripts/quickstart.md`'s three scenarios by hand in a fresh script, distinct from the unittest run.
- [x] T007 Tick every box in `specs/001-recycled-slug-transcripts/tasks.md` whose work is confirmed present by T001-T006; leave any unconfirmed box unchecked and name it in the closing report.
- [x] T008 Extend `CHANGELOG.md`'s existing Fixed entry for the recycled-slug fix (added by e3b6242 itself) so it contains the word "recycled", cut-and-add only, no new paragraph, same voice.
- [x] T009 Update `CLAUDE.md`'s `Last updated:` date to 2026-09-09; change nothing else in that file.
- [x] T010 Run `python3 -m pytest -q` in the foreground with an explicit timeout, record the actual count.
- [x] T011 Stage exactly the four owned paths (`specs/001-recycled-slug-transcripts/tasks.md`, `CHANGELOG.md`, `CLAUDE.md`, `specs/002-close-spec-001-paperwork/`), confirm `git diff --cached --name-only` shows only those, and commit.
