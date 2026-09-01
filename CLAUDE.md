# Scribe Desk

## What this repo is

A macOS Tk GUI + CLI for transcribing audio through ElevenLabs Scribe, organised around **projects** — named transcription contexts that each carry their own keyterms, Scribe settings, and output folder.

Three modules, no framework, no build step:

| File | Role |
|---|---|
| `scribedesk_config.py` | project registry (`projects.json`), per-project settings (`config/<slug>.json`), path resolution |
| `scribedesk_stt.py` | ElevenLabs Scribe wrapper — the full API surface, driven by CLI flags |
| `scribedesk_gui.py` | Tk front-end; shells out to `scribe-desk-stt` per file and parses its stage markers for the progress bar |

`scribe-desk` and `scribe-desk-stt` are the launchers; `Scribe Desk.app` is an icon and a launch script, no code. `make_icon.py` regenerates the icon.

## Conventions

- **The slug is the identity.** A project's display name is editable; its slug never changes, and it's what names the config file and the default output folder. Every function taking a slug calls `assert_safe_slug` first — the registry is a hand-editable JSON file, so a slug is untrusted input on a path.
- **Registry and settings are local state, not config.** Keyterms are the names of real people; `output_dir` is a path on one machine. Both stay gitignored. Don't add a "commit your settings" convenience.
- **Only `output/<slug>/` is ours to delete.** A project can point `output_dir` at any folder the user owns, which will contain files this tool never wrote. `delete_project` gates removal on `is_managed_output` and the GUI doesn't offer the option for a custom folder. Keep both halves — the GUI check is the UX, the config check is the guarantee.
- **Settings survive an unknown key, not a missing one.** `load_settings` merges over `DEFAULT_SETTINGS` and drops anything unrecognised, so adding a setting means adding it to `DEFAULT_SETTINGS` and nowhere else for old config files to keep loading. `output_dir` was added this way and existing files with no such key read as `""`.
- The GUI reads the **live** field, not the saved one, when resolving the output folder (`_current_output_dir`), so an unsaved edit is what takes effect on Transcribe. Match that pattern for anything else that decides where bytes go.

## Standing rules

Process rules, binding on any agent working here.

1. **No agent memory.** Everything durable lives in the repo — this file and `CHANGELOG.md`. If a memory and the repo disagree, the repo wins.
2. **All development happens on a worktree.** Never write code on a checkout of `main`. Repo management (merging, tagging, reading) is the exception.
3. **Commit every round.** Stage specific paths, never `-A`. New commits only; no `--amend` unless asked, no force-push.
4. **Refresh `Current status` before each commit**, including its date, in the same commit.
5. **Verify GUI changes by building the GUI.** `tk.Tk()` + `root.withdraw()` + construct `ProjectsGUI` exercises the whole widget tree without a visible window, and the handlers can be called directly. It catches real breakage, and it is the only check the GUI layer has. Note that `tk.Tk()` blocks outright in a session with no window server, so an agent that can't get a window has to say so rather than report the GUI unverified as verified.
6. **Non-GUI changes get a test.** `test_scribedesk_stt.py` runs on the standard library alone — `python3 -m unittest test_scribedesk_stt -v`, no pytest, no install. Write the failing test first. `scribedesk_stt.py` imports the `elevenlabs` package inside `main()` and nowhere else, which is what makes the module importable in a test with no SDK and no key; keep it that way.

Spec Kit is *not* set up here, unlike the repo template's default. This is a three-file tool, and a spec-per-feature workflow would cost more than it returns. Revisit if it grows.

## Current status

Last updated: 2026-09-02

**A recreated project no longer inherits a deleted project's kept transcripts.** Deleting a project while choosing "keep the transcripts" freed its slug for reuse, but `unique_slug` only checked the registry and any orphaned config file, not the output folder — so a later project of the same name silently got the old project's `output/<slug>/` folder as its own, and the tool's own "delete transcripts" option could then destroy exactly what the first delete promised to keep. `unique_slug` and `_migrate_locked` (which already got this right) now share one three-way check via `_slug_in_use`. Two smaller findings from the same review, fixed alongside it since the hand was in the same module: `_read_registry_or_rebuild` no longer treats an unreadable (not corrupt) `projects.json` the same as a corrupt one — an `OSError` now raises instead of silently erasing every project from the UI; and keyterms containing a comma (e.g. "Acme, Inc.") no longer get silently split into two ElevenLabs-billed terms, via a shared `parse_keyterms_text` used by both the GUI's form collection and `scribedesk_config.py`'s settings normalization. Verified by `test_scribedesk_config.py` (new — the module's first test coverage), each of the three fixes proven red against the shipped code and green after, run against a sandboxed copy of the module, never a real transcript directory. Found by the 2026-09-01 adversarial review recorded in vl-management's `reports/2026-09-01-adversarial-review-scribe-desk.md`.

**A successful result can be re-transcribed without a trip to Finder.** The README's two-pass workflow for speaker labels — run once to see the `Speaker 0:` / `Speaker 1:` numbers, label them, run again — used to strand the audio: a successful run moved the file from `inbox/` to `processed/` and the result dict discarded `dest`, so the main screen (which scans `inbox/` only) could no longer find it. The move now goes through `move_to_processed(input_path)`, which the worker calls instead of moving inline and which returns the audio's real final location in all three cases (moved, left alone because it wasn't in `inbox/`, left alone because the move failed). Every result carries that location under `"audio"`. Each successful row in the Results panel now has a **↩ Re-transcribe** action, wired with its own `Text` tag the same way the transcript-opening row is; it calls `requeue_audio(path)` (`True`/`False`, never raises, mirrors `open_transcript`) and on success adds the file back to the list and returns to the main screen with it selected. Verified by testing `move_to_processed` and `requeue_audio` directly, plus the worker's `run()` producing an `"audio"` key on a successful result — per rule 5, the tag wiring itself is code-reviewed only, since building the widget tree needs a window server this session doesn't have.

**A result in the results panel opens.** Double-clicking a successful line calls `open_transcript(path)`, a plain function that shells out to `open` and returns `False` on a missing file instead of raising, so `_open_result_transcript` can show a dialog rather than let a moved-or-deleted transcript crash the callback. Wired with per-result `Text` tags (`open_<i>`), the same idiom Tk uses for clickable regions in a widget that isn't a Listbox. Verified by testing `open_transcript` directly, per rule 5 — the tag wiring itself is code-reviewed only, not exercised by a test, since building the widget tree needs a window server this session doesn't have.

**Argument and file errors now surface before the API-key check.** The CLI used to validate `ELEVENLABS_API_KEY` before it looked at `args.audio` at all, so every mistake — a typo'd flag, a file that doesn't exist — reported "No ELEVENLABS_API_KEY found" when there was no key set, regardless of what was actually wrong. `validate_audio_file` in `scribedesk_stt.py` is now called from `main()` before the key is loaded, and again inside `process_file` for direct callers; the messages are unchanged, only the order in which they can fire.

**`.env.example` exists.** `.gitignore` already whitelisted it, but nobody had ever added the file, so a new user had to read `load_api_key` in `scribedesk_stt.py` to learn the only variable it reads is `ELEVENLABS_API_KEY`. The example now names it, with a one-line comment pointing at where to get a key.

**API failures are readable, and the repo has its first tests.** Every error from ElevenLabs used to reach the user as the SDK's own `__str__` — a twenty-field HTTP header dump with the actionable sentence at the end of it — so a mistyped key looked like a crash and a rejected option didn't say which option. `describe_api_error` in `scribedesk_stt.py` pulls out the API's message, names the offending field for validation errors, and appends a hint for the status codes that mean something (401, 402, 403, 413, 422, 429, 5xx). It is best-effort by construction and cannot raise: an error handler that throws is strictly worse than the ugly message it replaced. The GUI is unchanged and gets it anyway, because it echoes the CLI's stdout — which is the argument for keeping every user-facing message in the CLI layer rather than duplicating it in the front-end. Found by running the CLI against the live API with a deliberately invalid key, which costs nothing and is the only way to see what the failure path actually prints.

**Speaker labels work now.** They never had: Scribe returns speaker ids as `speaker_0`, every piece of documentation told people to write `0`, and the mismatch failed silently — the label simply didn't apply and the transcript said `Speaker speaker_0`. Both forms now normalise to the same key, the unlabelled fallback reads `Speaker 0`, and a label matching nobody says so instead of doing nothing. Found by using the tool rather than reading it, which is the only way this class of bug surfaces: the code is self-consistent, and only the round trip through the real API shows that the ids it returns aren't the ids the docs promise.

**`config/` is now ignored wholesale** — `config/*` with `!config/.gitkeep`, matching how `inbox/`, `output/` and `processed/` are already handled. The old pair of patterns listed `config/*.json` and `config/*.json.deleted-*` by name, which meant any other suffix on a settings file — a `.bak`, a hand-made copy — was tracked by default and could be committed without git objecting. A keyterm list is a directory of real people's names and this repo is public, so the ignore rule has to fail closed against filenames nobody thought of rather than enumerate the ones somebody did.

Extracted from a private knowledge-base repo, where it lived as a folder called "KB Transcriber". Renamed throughout; the hardcoded keyterm seed was dropped, so a first run now seeds an empty "Default" project. Added the per-project output folder — the feature that made the extraction worth doing.

Live local state moved across with it — the project registry, per-project settings, transcripts and processed audio. All of that is gitignored and stays on the machine it was made on.

- Full history: `CHANGELOG.md`.
- MIT licensed. **This repo is public**, which is the single most important fact when adding anything to it.
- A keyterm list is a directory of real people's names. It lives in gitignored per-project config and must stay there; don't add a convenience that commits it, and don't paste one into a doc, a test fixture, or a commit message. The original history was discarded for exactly this reason — it carried a working list.
