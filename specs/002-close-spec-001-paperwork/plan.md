# Plan 002: Close spec 001's paperwork gap

## Approach

1. Establish ground truth before touching any record: read e3b6242's diff in full (`git show e3b6242 --stat` and the per-file diffs for `scribedesk_config.py`, `scribedesk_gui.py`, `test_scribedesk_config.py`, `CHANGELOG.md`, `CLAUDE.md`), and read `specs/001-recycled-slug-transcripts/tasks.md`, `spec.md`, and `quickstart.md` to know what each task box actually asserts.
2. Reproduce the red/green history genuinely rather than taking the commit message's word for it: check out `scribedesk_config.py` from e3b6242's parent commit alongside the shipped `test_scribedesk_config.py` in a scratch directory, run the three new-feature tests, and confirm they fail for the stated reasons; then run the same tests against the shipped module and confirm they pass. This directly verifies every task box that asks to "confirm red" or "confirm green" and paste output.
3. Run the shipped test suites once more against `main`'s current code (`test_scribedesk_config`, `test_scribedesk_stt`) to verify the "no regression" and "polish" checkpoints, and attempt the GUI build check per the repo's own rule 5, reporting plainly if no window server is available rather than skipping unremarked.
4. Manually walk `specs/001-recycled-slug-transcripts/quickstart.md`'s three scenarios by hand, distinct from the unittest run, as the paranoia pass task 025 asks for.
5. Tick every task box whose work is confirmed present by steps 2-4; leave any box unchecked whose work cannot be confirmed, and name it in the closing report rather than ticking to make the count.
6. Edit `CHANGELOG.md`: since e3b6242 already added a `### Fixed` entry describing the recycled-slug fix in full, extend that entry's own wording (cut-and-add the minimum, in the same voice, no new paragraph) so it contains the word "recycled" and is discoverable by that grep — do not duplicate the entry.
7. Edit `CLAUDE.md`: change only the `Last updated:` date to 2026-09-09; the Current status prose already names the fix correctly and is left untouched, per the dispatching brief's instruction to change nothing else there.
8. Run `python3 -m pytest -q` in the foreground with an explicit timeout and record the actual count.
9. Stage exactly the four owned paths, diff `--cached` to confirm no stray path, and commit with a body under 72 characters in the subject and full detail in the body.

## Risks / non-goals

No production code changes. No new tests are required for this spec since nothing user-visible changes (rule 12's exception applies), but the existing suites are re-run as a non-regression check, and the historical red/green claims in the closed tasks are independently reproduced rather than trusted.
