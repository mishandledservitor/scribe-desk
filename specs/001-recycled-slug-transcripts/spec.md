# Feature Specification: A recycled project slug no longer adopts or destroys another project's transcripts

**Feature Branch**: `098-recycled-slug-transcripts`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: "Fix three data-loss bugs in scribedesk_config.py found by an adversarial review (findings 0, 4, 6 of reports/2026-09-01-adversarial-review-scribe-desk.md): (1) a recreated project silently inherits and can then destroy a deleted project's kept-on-purpose transcripts because slug allocation does not check the output folder; (2) an unreadable (not corrupt) registry is renamed away and every project vanishes; (3) a keyterm containing a comma is silently split into two billed terms. Reproduce every defect against the real module in a temp sandbox, red-first."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deleting a project and keeping its transcripts must actually keep them (Priority: P1)

A user deletes a project ("Acme"), choosing "keep the transcripts on disk" rather than delete them. Weeks later they start a new engagement and name a new project "Acme" again — a name they are entitled to reuse. The tool must not hand this new project the old one's transcripts folder. If the user later deletes the *new* "Acme" and chooses to delete its transcripts, only the new project's own transcripts may be removed; the old, deliberately-kept transcripts must still exist afterward, untouched.

**Why this priority**: This is the only finding that destroys user data with no warning and no undo, and it strikes precisely the user who took the careful, safer option at delete time. It is CRITICAL in the source review.

**Independent Test**: Reproduce end-to-end against a sandboxed copy of `scribedesk_config.py` (path constants repointed at a scratch directory, never a real transcript directory): create "Acme", write a transcript into its managed output folder, delete it with `delete_output=False`, recreate "Acme", assert the new project's managed output folder is *not* the old one and the old transcript is untouched; then delete the new project with `delete_output=True` and assert the old transcript still exists.

**Acceptance Scenarios**:

1. **Given** a deleted project whose transcripts were kept on disk, **When** a new project is created with the same display name, **Then** the new project is assigned a slug whose managed output folder does not already contain files, and the old project's kept transcripts are not visible inside it.
2. **Given** the scenario in (1), **When** the new project is later deleted with "also delete transcripts" selected, **Then** only the new project's own (empty or newly-written) output folder is removed, and the original kept transcripts survive on disk.

---

### User Story 2 - An unreadable registry fails loudly instead of erasing every project (Priority: P2)

A user's `projects.json` becomes temporarily unreadable (a permissions error, a full disk, a locked file, an NFS/iCloud stall) — the bytes on disk are untouched and would parse fine if read. Today the tool cannot tell "unreadable" apart from "corrupt": it renames the file away and starts a brand-new empty registry, so every project the user has ever created appears to have vanished, silently. The tool must instead tell the user their registry could not be read and refuse to proceed, rather than quietly replacing their data with an empty one.

**Why this priority**: Every project "disappearing" with no explanation is severe, but nothing is actually deleted (the settings files and the renamed-away registry both survive on disk), so it ranks below the transcript-destroying finding.

**Independent Test**: In a sandbox, create two projects, make the registry file unreadable (e.g. `chmod 000`), call the function that lists projects, and assert it raises a clear, path-naming error rather than silently returning a fresh single "Default" project.

**Acceptance Scenarios**:

1. **Given** a `projects.json` that is valid JSON but cannot be read due to an OS-level error, **When** the registry is loaded, **Then** the tool raises an error naming the path and the underlying reason, and does not rename the file away or write a new empty registry.
2. **Given** a `projects.json` that is genuinely unparsable (invalid JSON) or empty/zero-byte, **When** the registry is loaded, **Then** the existing rename-to-`.corrupt-<stamp>` and rebuild behaviour is unchanged.

---

### User Story 3 - A keyterm containing a comma stays one term (Priority: P3)

A user adds a keyterm such as "Acme, Inc." — a real, singular proper noun that happens to contain a comma — to a project's keyterm list (documented as "one per line"). Today it is silently split into two terms ("Acme" and "Inc.") at the point settings are read and written, and ElevenLabs bills per keyterm, so the user is billed for two useless fragments of one term they intended to add once.

**Why this priority**: No data is destroyed and nothing is exposed, but a documented input contract is silently violated and it costs the user money per occurrence. Lowest of the three in this feature, but folded in because the fix touches the same settings-normalization code path.

**Independent Test**: In a sandbox, save settings with a keyterms list containing an entry with an embedded comma, reload the settings, and assert the entry survives intact as a single list element, matching the count of terms that went in.

**Acceptance Scenarios**:

1. **Given** a keyterms list where one entry contains a comma, **When** the settings are saved and then reloaded, **Then** the number of keyterms after reload equals the number before, and the comma-containing entry is unchanged.

### Edge Cases

- What happens when the freed slug collides with an output folder AND a differently-named project already occupies the next numeric suffix? The allocator must keep incrementing until it finds a candidate free in registry, config file, and output folder all three.
- What happens when the output folder collision is a stray empty directory rather than one containing transcripts (e.g. left by a previous run that wrote nothing)? Treating any existing folder as in-use is the safe default — a false "in use" costs a numeric suffix; a false "free" costs another user's data.
- What happens when the registry file does not exist at all (first run)? This is not an `OSError` on the read (the code already special-cases missing-file into a fresh registry) and must continue to seed a fresh "Default" project as today.
- What happens when a keyterm entry is a bare comma, or is only whitespace around a comma? It should still collapse to nothing (matching today's whitespace-stripping and empty-entry-dropping behaviour) rather than being treated as two empty terms.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Slug allocation for a new or recreated project MUST treat an existing `output/<candidate>` folder as "in use", in addition to the existing registry and config-file checks, so a slug whose managed output folder already contains a previous (possibly kept-on-delete) project's data is never handed to a new project.
- **FR-002**: The three-way in-use check (registry, config file, output folder) MUST be the single shared definition used both by the migration path that already implements it correctly and by ordinary new/recreated-project slug allocation, so the two cannot drift apart again.
- **FR-003**: Loading the project registry MUST distinguish "the file could not be read" (an OS-level error) from "the file was read but is not valid JSON" (corrupt or empty). Only the latter (plus a genuinely empty/zero-byte file) may trigger the existing rename-to-archive-and-rebuild-fresh behavior.
- **FR-004**: When the registry cannot be read due to an OS-level error, the system MUST raise a user-facing error that names the registry's path and MUST NOT rename the existing file away, MUST NOT write a new registry, and MUST NOT report or seed any project list.
- **FR-005**: A keyterm containing a comma MUST survive as a single, unmodified term through settings save and load, matching the "one per line" contract the keyterm editor documents.
- **FR-006**: The keyterm normalization change MUST NOT change today's behavior for a keyterms value that is already a clean list of strings with no embedded commas, nor for whitespace-only or empty entries (still dropped).

### Key Entities

- **Project registry (`projects.json`)**: The list of live projects (slug, display name, timestamps) and which slug was last used.
- **Slug**: The immutable identity of a project; names its config file (`config/<slug>.json`) and its default managed output folder (`output/<slug>/`). Must be unique across three places at once: the live registry, any config file (including archived-but-not-yet-restored ones do NOT reserve it, by design), and the output folder.
- **Managed output folder (`output/<slug>/`)**: Where a project's transcripts land by default; the only folder the tool is ever allowed to delete on the project's behalf.
- **Keyterm**: One person/product/jargon name the user wants ElevenLabs Scribe to bias recognition toward; billed per term.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Deleting a project while keeping its transcripts, then creating a new project with the identical display name, never results in the new project's managed output folder containing any file that predates the new project's creation timestamp — verified by an automated regression test against the real module.
- **SC-002**: An unreadable (permission-denied) registry file never results in a previously non-empty project list appearing empty to any caller of `list_projects`/`load_registry` — instead an error is raised, verified by an automated regression test.
- **SC-003**: A keyterm list saved with N entries, one containing a comma, reloads with exactly N entries and the comma-containing entry unchanged — verified by an automated regression test.
- **SC-004**: All three regression tests are demonstrated red against the pre-fix code (pasted output) and green after the fix, run against copies of the real module rather than a hand-built fixture.

## Assumptions

- The fix for FR-001/FR-002 is scoped to `scribedesk_config.py`'s slug-allocation path (`unique_slug` and its callers); it does not need to change `_migrate_locked`, which already implements the correct three-way check and serves as the reference behavior.
- The fix for FR-003/FR-004 introduces a new exception type (or reuses the existing `ConfigError`) that the GUI layer can catch to show a dialog; wiring an actual Tk dialog is out of scope for this backend fix since the review's own verification limits note the GUI widget tree cannot be built in this environment — the GUI-facing wording from the review ("say where transcripts are kept" / "show a dialog naming the path and errno") is addressed at the point closest to the data (raising with the path and reason in the message) and left for a GUI-layer follow-up to surface visually if the review's suggested dialog text is wanted verbatim.
- The fix for FR-005/FR-006 is scoped to the shared settings normalization in `scribedesk_config.py` (`load_settings`/`save_settings`), since that is the one choke point both the GUI and CLI already pass through, per the review's own suggestion.
- Finding 5 (the leaked-settings-backup record) from the same review is explicitly out of scope for this feature and needs no code change.
- All reproduction and regression tests run against copies of the real module with path constants repointed at a `tmp_path`-style scratch sandbox; none run against any real transcript directory.
