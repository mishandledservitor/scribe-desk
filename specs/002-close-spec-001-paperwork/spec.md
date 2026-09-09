# Spec 002: Close spec 001's paperwork gap

## Problem

Commit e3b6242 ("Fix a recycled slug adopting a deleted project's kept transcripts") shipped and is on `main`, green. But three of its own records never caught up with it: `specs/001-recycled-slug-transcripts/tasks.md` still shows every one of its 25 boxes unchecked, `CHANGELOG.md`'s existing entry for the fix never uses the word "recycled" (so a reader searching the changelog for the incident by name finds nothing), and `CLAUDE.md`'s `Last updated` date is a week stale relative to today even though its Current status prose already names the fix correctly. The code and tests are not in question — only whether the repo's own paper trail can be trusted to say what shipped.

## Scope

In scope: ticking `specs/001-recycled-slug-transcripts/tasks.md`'s boxes against verified evidence (not by assumption), making `CHANGELOG.md` discoverable by the term "recycled", and refreshing `CLAUDE.md`'s `Last updated` date in the same commit as required by this repo's own rule 4. Out of scope: any change to `scribedesk_config.py`, `scribedesk_gui.py`, or `scribedesk_stt.py` — nothing shipped here changes behaviour a user can see, so rule 12's failing-test-first clause does not bind this spec (it is a small, reversible, non-shipping change: record-keeping only).

## Success criteria

- SC-001: `grep -c "^- \[x\]" specs/001-recycled-slug-transcripts/tasks.md` prints 25, or a smaller true count with the shortfall named and explained in the closing commit/report.
- SC-002: `grep -n -i recycled CHANGELOG.md` finds a line.
- SC-003: `CLAUDE.md`'s Current status section still names the fix and its `Last updated` line reads 2026-09-09.
- SC-004: `python3 -m unittest test_scribedesk_config -v` and `python3 -m unittest test_scribedesk_stt -v`, run individually in the foreground, both stay green (this work touches no code, so this is a non-regression check, not a red/green pair).

## Evidence standard

Every ticked task box in `specs/001-recycled-slug-transcripts/tasks.md` must correspond to something actually verified against `main`'s code and tests — the diff of e3b6242, a re-run of the shipped test suite, and, for the "confirm red/green" procedural tasks, an actual reproduction (checking out the pre-fix module against the shipped test to see it fail, then confirming it passes against the fix) rather than trusting the commit message's own account of having done so.
