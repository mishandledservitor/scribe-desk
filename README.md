# Scribe Desk

A project-selectable GUI for transcribing audio via ElevenLabs Scribe. Each **project** is a transcription context — a company's meetings, a podcast, a TTRPG table — and carries its own keyterms, Scribe settings, and output folder. Pick a project and its whole setup loads: the keyword list that stops Scribe mangling names, the speaker labels, the diarization defaults, the format, and where the transcripts get written.

Adapted from `voxbox/projects`, and previously lived inside a knowledge-base repo as "KB Transcriber" — the per-project output folder is what let it move out.

## Launch

- **Double-click `Scribe Desk.app`** (Finder, Dock, or Spotlight). The bundle finds a tkinter-capable `python3` and opens the GUI. Keep it in place, or drag it to `/Applications` or the Dock — a moved copy still finds the code via the repo path baked into its launcher.
- Or from a terminal:

```bash
~/git/mishandled/scribe-desk/scribe-desk          # GUI
~/git/mishandled/scribe-desk/scribe-desk-stt -h   # CLI
```

First launch from Finder may need a right-click → **Open** (unsigned app, Gatekeeper). Launch errors, if any, land in `app-launch.log` (gitignored).

## Setup (one-time)

```bash
~/git/mishandled/scribe-desk/setup.sh
echo 'ELEVENLABS_API_KEY=sk_...' > ~/git/mishandled/scribe-desk/.env
```

If the voxbox repo is present, its `speech-to-text/venv` and `.env` are used as fallbacks — with voxbox set up, this tool works with zero setup.

## Workflow

1. Drop recordings in `inbox/` (or ➕ Add file in the GUI).
2. Pick a **project** in the top bar; edit keyterms (one per line) as the cast changes. **+ New project…** / **Manage…** to add, rename, duplicate, delete.
3. Select files → **Transcribe**. Settings auto-save to the project.
4. Transcripts land in the project's output folder; source audio moves to `processed/`.

Tip for meetings: set **Speaker labels** per project, e.g. `0=Simon,1=George`, after checking which id Scribe gave each voice in a first pass.

## Output folder, per project

The **Output** row sits directly under the project selector, because that's what governs it — switching project switches where transcripts land.

- **Blank** means the managed default, `output/<slug>/` inside this repo. Scratch space: gitignored, and the tool is free to delete it when you delete the project.
- **Anything else** is your folder. `Choose…` opens a picker; `~` is honoured if you type a path; a relative path resolves against this repo. `📂` opens whichever one is live, and the hint line under the row always shows the resolved path — including whether it exists yet. A folder that doesn't exist is created on the first run.

The point is that a transcript usually belongs with the rest of the work it came from, not in a scratch folder here — a repo's `docs/`, a meetings archive, a client folder. Set it once per project and the file is where it belongs the moment it's written, instead of being moved by hand every time.

**A project pointed at your own folder never has that folder deleted.** Delete such a project and the GUI says the transcripts stay put; `delete_project` gates the removal on `is_managed_output` regardless of what it's asked to do. Only `output/<slug>/` is ever removed, because it's the only folder this tool owns.

## What a project stores

Everything in the options panel plus keyterms and the output folder, in `config/<slug>.json`: model (`scribe_v2`/`scribe_v1`), language (auto or ISO-639), diarization + speaker count + sensitivity, speaker labels, speaker-role detection, audio-event tags, clean transcript (`no_verbatim`), temperature/seed, timestamp granularity, output format (text/srt/vtt/json), inline `[hh:mm:ss]` prefixes, `output_dir`.

Scribe caps keyterms at 1000 terms, ≤5 words each; ElevenLabs bills the biasing per term, so a list that just accretes costs money and dilutes the terms that matter. Cap each project's list at what it actually needs and prune it on a cadence.

## Files & state

| Path | Tracked? | Contents |
|------|----------|----------|
| `projects.json` | no | project registry (slug = immutable id) |
| `config/<slug>.json` | no | per-project settings + keyterms + output folder |
| `inbox/` | dir only | drop-folder for audio |
| `output/<slug>/` | dir only | default per-project transcripts |
| `processed/` | dir only | audio moved here after a successful run |
| `Scribe Desk.app` | yes | macOS launcher bundle (icon + launch script; no code) |
| `app-launch.log` | no | GUI stderr when launched from the .app (debug only) |

Registry and settings are local state, not config — a project's keyterms are the names of the people in its meetings, and its output folder is a path on this machine. Both are gitignored, as in voxbox.

Source of the design: `~/git/mishandled/voxbox/projects/` — if that tool grows features worth having, re-diff against it.
