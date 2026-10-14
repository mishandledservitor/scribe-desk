# Scribe Desk

## What this repo is

A macOS Tk GUI and CLI for transcribing audio and video files through the ElevenLabs Scribe speech-to-text API, organised around **projects**: named transcription contexts that each carry their own keyterms, Scribe settings and output folder. It needs an ElevenLabs key with Speech to Text access, read from `ELEVENLABS_API_KEY` in the environment or in the repo's `.env`. Principles live in `.specify/memory/constitution.md`, features in `specs/`, release decisions in `docs/decisions.md`.

Three modules, no framework:

| File | Role |
|---|---|
| `scribedesk_config.py` | Project registry (`projects.json`), per-project settings (`config/<slug>.json`), path resolution, and every operation that can delete user data. |
| `scribedesk_stt.py` | ElevenLabs Scribe wrapper with the full API surface, driven by CLI flags. |
| `scribedesk_gui.py` | Tk front end; it shells out to `scribe-desk-stt` per file and parses its stage markers for the progress bar. |

`scribe-desk` and `scribe-desk-stt` are the launchers. `build_app.py` writes `Scribe Desk.app` (untracked) with the clone's absolute path in its launcher; `setup.sh` runs it. `make_icon.py` regenerates `app/icon.icns`.

## Conventions

- **The slug is the identity.** A project's display name is editable; its slug never changes, and it names the config file and the default output folder. Every function taking a slug calls `assert_safe_slug` first, because the registry is a hand-editable JSON file, so a slug is untrusted input on a path.
- **Registry and settings are local state, not config.** Keyterms are often the names of real people, and `output_dir` is a path on one machine. Both stay gitignored. Don't add a "commit your settings" convenience, and never paste a keyterm list into a doc, a test fixture or a commit message. The repo is public.
- **Only `output/<slug>/` is ours to delete.** A project can point `output_dir` at any folder the user owns, which will contain files this tool never wrote. `delete_project` gates removal on `is_managed_output`, and the GUI doesn't offer the option for a custom folder. Keep both halves: the GUI check is the UX, the config check is the guarantee.
- **Settings survive an unknown key, not a missing one.** `load_settings` merges over `DEFAULT_SETTINGS` and drops anything unrecognised, so adding a setting means adding it to `DEFAULT_SETTINGS` and nowhere else for old config files to keep loading.
- **The live field decides where bytes go.** The GUI reads the live field, not the saved one, when resolving the output folder (`_current_output_dir`), so an unsaved edit is what takes effect on Transcribe. Match that pattern for anything else that decides where files are written.
- **No machine-specific paths.** Paths come from settings or from the repo folder (`SCRIPT_DIR`). `test_repo_hygiene.py` fails on a home-folder path in any tracked file.
- **`elevenlabs` is imported inside `main()` only.** That keeps `scribedesk_stt.py` importable in a test with no SDK and no key.
- **Example people are generic.** Tests and docs use names such as John Doe and Jane Smith.

## Standing rules

Binding on any agent working in this repo. These are process rules, not project conventions. **This file is the only source of truth for them.** Delete one only deliberately, never because it looks like unused scaffolding.

1. **No agent memory.** Never rely on assistant-side memory, per-project memory files, or recall from a previous session. Everything durable lives in the repo: this file, `CHANGELOG.md`, `docs/decisions.md`, `.specify/memory/constitution.md` and `specs/`. If something is worth remembering, write it here in the same turn you learn it. If a memory and the repo disagree, the repo wins.
2. **Spec Kit governs all development.** Every feature flows through `/speckit-specify` → (`/speckit-clarify` as needed) → `/speckit-plan` → `/speckit-tasks` → (`/speckit-analyze` / `/speckit-checklist` as needed) → `/speckit-implement`. No production code is written outside a spec'd, planned, tasked feature. The constitution outranks this file on anything about the code itself; these standing rules govern process and agent behaviour.
3. **All development happens on a worktree.** Never write code, tests, specs, or plans on a checkout of the main branch. Create a worktree with its own branch and work there. Only repo management belongs outside a worktree: opening and merging PRs, reviewing, tagging, releases, branch cleanup, and reading.
4. **Commit every round.** Each round (one user request plus its completion) ends with a git commit of whatever that round changed, without waiting to be asked. This includes Spec Kit artifacts (`spec.md`, `plan.md`, `tasks.md`). Stage specific paths, never `-A`; review what's staged first; new commits only (no `--amend` unless asked); no force-push. A pure Q&A round that changes no files has nothing to commit.
5. **Refresh `Current status` before each commit.** Update the "Current status" section below, including its `Last updated:` date, to match reality as part of the same commit, so the summary can never drift from the repo.
6. **Context and delegation.** Keep long sessions clean: hand work that would produce large exploratory output (broad searches, file dumps, log reads) or that can run on its own to a subagent, and keep only its conclusion in the main conversation. Use a separate worktree per independent phase when phases don't touch the same files.
7. **Don't narrate no-ops.** A check that came back empty doesn't need a line of output. Report what you did and what the user has to decide. With no `.specify/extensions.yml`, every `/speckit-*` hook check is a guaranteed no-op; skip it silently.
8. **True TDD: red, green, refactor.** No production code without a failing test first. For every unit of work: write a test that fails for the right reason (red), write the minimum code to make it pass (green), then clean up with the tests still green (refactor). This happens inside `/speckit-implement`: each task's test is written and shown failing before that task's implementation is written. Tests that touch the filesystem reassign the module's path constants to a temporary sandbox and never run against a real transcript folder.
9. **Spec Kit and TDD apply whatever door the work came in by**: an issue, a chat message, or the user typing at a session directly. Act on what is genuinely urgent, then spec and test the build rather than implementing straight from a request. The only exception is a small, reversible, non-shipping change such as a typo, a comment or a note. If a user can see the behaviour change, it is spec'd and tested.
10. **Verify GUI changes by building the GUI.** `tk.Tk()` + `root.withdraw()` + constructing `ProjectsGUI` exercises the whole widget tree without a visible window, and the handlers can be called directly. The automated tests cover only the plain functions behind the callbacks. `tk.Tk()` blocks outright in a session with no window server, so an agent that can't get a window says so rather than reporting the GUI as verified.
11. **Never hard-wrap text meant for a human to read.** No fixed-column line breaks in UI copy, generated reports, chat messages, docs prose, or commit-message bodies: one paragraph is one line, and the device does the wrapping. This does not touch code: source lines, docstrings, `<pre>` blocks, ASCII tables, and fixed-width terminal output stay as they are.
12. **Never touch a `.env` file without asking the user.** Not to untrack it, delete it, move it, or rewrite it. Report what you found, say what reads the file (`load_api_key` in `scribedesk_stt.py`, and through it the GUI's account line), and ask. Reading one to classify a key is allowed, changing one is not, and no value ever appears in a report, a commit message, or a prompt. `.env.example` may be edited.

## Commands

Python 3.10 or later with tkinter. Tests need pytest and nothing else; `setup.sh` installs the `elevenlabs` SDK into `venv/` for real runs.

```sh
./setup.sh                                  # venv with the SDK, then builds Scribe Desk.app
./scribe-desk                               # GUI
./scribe-desk-stt -h                        # CLI
python3 -m pytest -q                        # all tests (what CI runs)
python3 -m unittest test_scribedesk_stt -v  # one module, standard library only
python3 -m compileall -q *.py && bash -n setup.sh scribe-desk scribe-desk-stt   # syntax check, as in CI
python3 build_app.py                        # rebuild the app only
python3 make_icon.py                        # regenerate app/icon.icns (macOS, needs Pillow)
```

## Structure

- `scribedesk_*.py`: the three modules above. `build_app.py`, `make_icon.py`: the app bundle and its icon. `app/`: the icon source for the bundle.
- `test_*.py`: one test module per source module, plus `test_launchers.py` (runs the shell launcher in a sandbox), `test_build_app.py` and `test_repo_hygiene.py`.
- `inbox/`, `processed/`, `output/`, `config/`: local data folders, tracked only as empty folders. `projects.json`, `app-launch.log`, `venv/` and `Scribe Desk.app` are untracked.
- `specs/NNN-*/`: Spec Kit feature folders. `.specify/` and `.claude/skills/speckit-*`: Spec Kit itself (see `THIRD_PARTY_NOTICES.md`).

## CI/CD

- `.github/workflows/ci.yml` (`CI`) runs on every pull request and every push to main: installs `python3-tk` and pytest on Ubuntu, checks Python and shell syntax, and runs `pytest`. It uses no secrets, and no test calls the ElevenLabs API.

## Current status

Last updated: 2026-10-14

- Release 1.0.0, the first public release (`CHANGELOG.md`). Constitution v1.0.1. Decisions 1-7 in `docs/decisions.md`.
- Built: projects with per-project keyterms, settings and output folder; safe project deletion; CLI with the full Scribe option set; readable API errors; speaker labels with a warning for unmatched labels; re-transcribe and open-transcript actions in the results panel; `Scribe Desk.app` built by `setup.sh` for the clone (spec 004).
- On 2026-10-14 the GUI widget tree was built against a sandboxed data folder (rule 10), and the built app was checked by the test that runs its launcher from a moved copy. Nobody has yet run a real transcription since the release changes.
- `.claude/skills/` holds only the Spec Kit `speckit-*` skills. Personal skills, `HANDOFF.md` and `notes/` are gitignored.
- Licence: MIT (`LICENSE`). Third-party files: `THIRD_PARTY_NOTICES.md`. The history before 1.0.0 is not public: commit hashes in the older specs belong to it.
- If this section contradicts what you see in the repo, trust the repo and flag the mismatch.
