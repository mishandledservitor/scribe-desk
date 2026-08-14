# Changelog

Notable changes to this repo. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **Per-project output folder.** A project can write its transcripts anywhere — the repo it belongs to, a meetings archive, a client folder — via the `output_dir` setting, edited in the Output row under the project selector. Blank keeps the managed default, `output/<slug>/`. `~` expands, relative paths resolve against the repo, and the hint line shows the resolved path and whether it exists yet. Missing folders are created on the first run.
- Guard on deleting a project's transcripts: only the managed `output/<slug>/` is ever removed, and only when no other project writes there. A project pointed at a folder the user owns keeps it, and the delete dialog says so instead of offering the option.
- Deleting a project archives its settings to `config/<slug>.json.deleted-<stamp>` instead of unlinking them. Keyterms are curated over months and live in no repo by design; "remove the project" shouldn't be indistinguishable from "burn the list".
- The hint under the Output row warns when another project resolves to the same folder. Sharing one is allowed but shouldn't be a surprise — the transcripts interleave with nothing left to say which project produced which.

### Fixed

- `duplicate_project` no longer copies a custom `output_dir`, which silently pointed two projects at one folder. The copy gets its own managed folder; everything else, keyterms included, still carries over.
- Deleting a project whose managed folder another project had been pointed at no longer takes that other project's transcripts with it.
- Folder identity is decided by `st_dev`/`st_ino` rather than string comparison (`same_dir`). Normalised strings see through neither symlinks nor macOS's case-insensitive filesystem, so `output/target` and `output/TARGET` — the same directory, differently typed — compared unequal and opened both delete gates. Where a path doesn't exist yet there is nothing to stat, so the comparison falls back to `realpath` and then casefolded `realpath`, deliberately over-matching: a false "same" costs a folder not deleted, a false "different" costs someone else's transcripts.
- Archive stamps carry microseconds and are made unique before the rename. At second resolution, deleting the same project twice within a second had the second archive silently overwrite the first — the archive destroying the archive.
- A failed archive rename leaves the live settings alone instead of falling through to `unlink`. An orphan config is something `unique_slug` already copes with; settings deleted with neither archive nor error is not.
- Slugs are capped at 64 characters. A long project name made the settings write fail with `ENAMETOOLONG` *after* the registry entry was committed, leaving a project that half-existed.
- `scan_inbox` survives a file leaving `inbox/` between the listing and the stat — a live race, since recordings land there while the window is open, and it left the window half-built.
- The Output field's shared-folder check catches `OSError` as well as `ConfigError`. It runs on every keystroke, so an unreadable registry or a full disk raised once per key.
- `unique_slug` budgets for its own `-2` suffix, `add_project` validates the slug before writing the registry, and `_validate` drops over-long slugs on read. The 64-character cap otherwise turned one long project name entered twice into a registry entry the code refused to load — with `last_used_slug` pointing at it, so the GUI wouldn't start, recoverable only by hand-editing JSON.
- Deleting a project's transcripts targets `managed_output_dir(slug)` rather than the path the setting resolved to. With a symlinked output folder the gate opened, `rmtree` refused the symlink, and `ignore_errors` swallowed it — so the dialog promised a deletion that never happened.
- `ValueError`, not just `OSError`, is caught around path comparisons: it's what the path layer raises for a NUL byte in a hand-edited config, and it escaped both the delete path and the keystroke handler.
- `projects_using_output` fails closed, returning `(slug, reason)` so a blocked deletion says whether the other project shares the folder or merely can't be read. An error can't open a gate that guards a deletion, and a project isn't accused of sharing a folder it may not.
- A slug from before the length cap is shortened on load, under the registry lock and with its settings and transcripts renamed to match, instead of being dropped. The lock is taken before anything moves: `_lock` opens a file beside `projects.json`, so the one condition that makes the registry write fail — an unwritable directory — makes acquiring the lock fail too, and acquiring it afterwards meant the failure raised before the rollback could run, leaving files renamed and the registry not. Dropping is right for an entry whose settings write failed — nothing is orphaned — but a pre-cap install has a real config and output folder, and dropping made both unreachable while the empty registry seeded a fresh "Default" over the top.
- `delete_project` returns whether transcripts were actually deleted, and the GUI says so when they weren't. A project that never transcribed anything counts as deleted — it's the commonest delete there is, and answering no made the GUI explain an absence that needed no explaining. The remaining case is a managed folder that is itself a symlink: the files it points at aren't this tool's to remove, so both are left alone and the user is told, rather than being shown a deletion that didn't happen.
- The 📂 button no longer creates a directory at a half-typed path, or raises out of the Tk callback when the path names a file. `Transcribe` already guarded this; the button didn't.
- Window title still carried the name of the company the tool was built at — the last place that was hardcoded.

### Changed

- **Extracted from a private knowledge-base repo into its own.** It had outgrown being a folder in someone's notes — three projects across three unrelated contexts, only one of them that knowledge base. The original history is not carried over: it contained a working keyterm list, which is a directory of real colleagues' names.
- Renamed "KB Transcriber" → "Scribe Desk" throughout: `scribedesk_config.py`, `scribedesk_gui.py`, `scribedesk_stt.py`, the `scribe-desk` / `scribe-desk-stt` launchers, and `Scribe Desk.app` (new bundle id `com.simonstrehler.scribedesk`).
- Results list shows a `~`-shortened absolute path for output outside the repo, instead of a stack of `../`.

### Removed

- The hardcoded 99-term keyterm list that seeded the first-run project. A general tool shouldn't ship one company's staff directory in its source; first run now seeds an empty "Default" project. Live keyterm lists are unaffected — they live in the gitignored `config/<slug>.json`.
