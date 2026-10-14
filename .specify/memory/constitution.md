<!--
Sync Impact Report
- Version change: 1.0.0 → 1.0.1
- Modified principles: none (wording only: Principle I points at the GUI rule in CLAUDE.md by name)
- Modified sections: Development Workflow (states the Spec Kit flow without outside references)
- Removed sections: none
- Deferred items: none
-->

# Scribe Desk Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)
Every non-GUI change starts with a test that fails for the right reason, run against the real module (or a `tmp_path`-style sandbox of it), before the fix that makes it pass. No production code in `scribedesk_config.py` or `scribedesk_stt.py` is written without a preceding failing test. GUI wiring that cannot be exercised without a window server is code-reviewed and the limitation is stated plainly, per the GUI rule in the repo's CLAUDE.md.

### II. Data-Loss Safety Over Convenience
`scribedesk_config.py` owns every operation that can destroy a user's hand-curated data (keyterms, transcripts). Any change to slug allocation, registry read/rebuild, or deletion gating must reason explicitly about what happens when a project is recreated, a file is unreadable (not just corrupt), or two writers race — and must fail closed (refuse / warn) rather than silently destroy or silently drop data.

### III. Slug and Path Identity Discipline
A slug is the identity for a config file and an output folder, but it is recyclable. Any function that allocates or frees a slug must treat the registry, the config file, and the output folder as one three-way check, matching the standard `_migrate_locked` already sets. A folder or registry entry that merely cannot be read is never treated as corrupt without distinguishing the two.

### IV. Reproduce Against the Real Artefact, Never a Fixture Built From the Bug Report
Regression tests for a destructive-path bug run against copies of the actual module and a scratch sandbox (reassigned path constants), never against a hand-rolled fixture that encodes the reviewer's description of the bug. Destructive operations are never exercised against a real transcript directory.

## Development Workflow

Spec Kit governs every change a user can see: specify → (clarify) → plan → tasks → implement, with `spec.md`, `plan.md`, and `tasks.md` kept under `specs/<NNN>-<slug>/`. Small reversible changes that no user can see, such as a typo or a comment, are exempt.

## Governance

This constitution amends the informal conventions in the repo's own `CLAUDE.md`; where they conflict, this file governs Spec Kit-driven feature work and `CLAUDE.md` continues to govern day-to-day conventions (commit discipline, worktree use, GUI verification).

**Version**: 1.0.1 | **Ratified**: 2026-09-02 | **Last Amended**: 2026-10-14
