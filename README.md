# Scribe Desk

Scribe Desk is a small macOS app and command-line tool that transcribes audio and video files with the ElevenLabs Scribe speech-to-text API. Work is organised into projects, such as a team's meetings, a podcast or a tabletop game group. Each project keeps its own key terms (names and jargon Scribe should spell right), speaker labels, diarization settings, output format and output folder, so picking a project loads its whole setup. You drop recordings into a folder, pick a project, press **Transcribe** and get text, SRT, VTT or JSON files.

It runs on your own ElevenLabs API key. Audio goes from your computer straight to ElevenLabs, and nothing goes through a server of ours.

## What you need

| What | Why |
|---|---|
| macOS | The app bundle, the folder buttons and the "open transcript" action use macOS. The `scribe-desk-stt` command-line tool also runs on Linux. |
| Python 3.10 or later with tkinter | The GUI is written in Tk. With Homebrew, `brew install python python-tk` provides both. CI runs on Python 3.12, and it has also been run on 3.14. |
| An ElevenLabs API key with **Speech to Text** access | This key pays for the transcription. Create it at [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys). |
| Optional: **User: Read** access on the same key | With it, the GUI shows your plan, credits left and renewal date. Without it, transcription still works and the account line says the details are unavailable. |

`setup.sh` installs the only third-party package, the [`elevenlabs`](https://github.com/elevenlabs/elevenlabs-python) Python SDK, into a virtual environment inside the repository.

## Quick start

1. Clone the repository and run the setup script. It creates `venv/`, installs the SDK and builds `Scribe Desk.app` for this clone.

   ```sh
   git clone https://github.com/mishandledservitor/scribe-desk.git
   cd scribe-desk
   ./setup.sh
   ```

2. Copy `.env.example` to `.env` and paste your key after `ELEVENLABS_API_KEY=`. You can export `ELEVENLABS_API_KEY` in your shell instead; the environment variable wins over the file.
3. Double-click `Scribe Desk.app` in the repository folder, or run `./scribe-desk`. You can drag the app to `/Applications` or the Dock; it still opens this clone.
4. Put a recording in `inbox/`, or click **➕ Add file...** in the window.
5. Pick a project in the top bar. The first run creates one called "Default". Use **+ New project…** and **Manage…** to add, rename, duplicate or delete projects.
6. Select the files and click **Transcribe**. Clicking it saves the project's settings, transcripts are written to the project's output folder, and audio from `inbox/` moves to `processed/`.

If you move the repository folder, run `./setup.sh` again so the app points at the new location. If the app doesn't open, look in `app-launch.log` in the repository.

## Updating

Run `git pull` in the repository, then `./setup.sh` to update the SDK and rebuild the app. Your projects, settings and transcripts aren't tracked by git, so an update leaves them alone.

## Using it

**Key terms.** Enter one term per line; a term may contain a comma. Scribe accepts up to 1,000 terms of up to five words each, and ElevenLabs bills key terms per term, so keep each project's list to the names it needs.

**Speaker labels.** Run a first pass with diarization on and no labels. The transcript comes back with lines such as `Speaker 0:` and `Speaker 1:`. Type those numbers into **Speaker labels**, for example `0=Jane Smith,1=John Doe`, and later passes in the same project get names. If a label matches nobody in the audio, the run says so. A finished result can be sent back for another pass with **↩ Re-transcribe**, and double-clicking a result opens the transcript.

**Output folder.** Leave the **Output** field blank to use `output/<project>/` inside the repository. Type or choose any other folder to write the project's transcripts there instead, for example next to the rest of that work. `~` and relative paths are accepted, the hint under the field shows the resolved folder, and a missing folder is created on the first run. The hint also warns when another project writes to the same folder.

**Deleting a project.** Its settings are archived to `config/<project>.json.deleted-<time>` rather than removed. The tool only ever deletes transcripts in its own `output/<project>/` folder, and only when you ask it to; a folder you chose yourself is never deleted.

**Other settings.** Each project also stores the model (`scribe_v2` or `scribe_v1`), language (automatic or an ISO 639 code), speaker count and diarization sensitivity, speaker-role detection, audio-event tags such as `[laughter]`, the clean-transcript option that drops filler words, temperature and seed, timestamp granularity, and inline `[hh:mm:ss]` prefixes for text output.

**Command line.** `./scribe-desk-stt recording.m4a -o recording.txt` transcribes one file with the same options as flags. Run `./scribe-desk-stt -h` for the full list. Supported inputs are mp3, mp4, wav, m4a, ogg, flac, aac, webm, mkv, mov, avi and opus.

## Your data

- Audio files, together with the project's key terms and settings, are sent to ElevenLabs (`api.elevenlabs.io`) for each transcription. The GUI also asks the same API for your subscription details. Scribe Desk talks to no other service.
- ElevenLabs may keep and use uploaded audio under its own terms. Check your account's data settings on elevenlabs.io.
- Your key is read from the `ELEVENLABS_API_KEY` environment variable or from `.env` in the repository, and nowhere else. `.env` is ignored by git.
- Projects (`projects.json`), per-project settings and key terms (`config/`), audio (`inbox/`, `processed/`) and transcripts (`output/`) stay on your computer and are ignored by git. Key terms are often real people's names, so don't commit them.
- Recording people can need their consent where you live.

## Known limitations

- Files are uploaded whole and transcribed one at a time; there is no live transcription.
- The GUI and the app need macOS; on other systems, use `scribe-desk-stt`.
- The app is built locally and isn't notarised. It works only while the repository stays where it was when `setup.sh` last ran.
- The interface is in English.

## Development

```sh
python3 -m pytest -q                        # the whole test suite
python3 -m unittest test_scribedesk_stt -v  # one module, standard library only
python3 -m compileall -q *.py               # syntax check, as in CI
python3 make_icon.py                        # regenerate app/icon.icns (macOS, needs Pillow)
```

No test calls the ElevenLabs API or needs a key. Features are built with [Spec Kit](https://github.com/github/spec-kit): each has a spec, plan and task list under `specs/`, the project's principles are in `.specify/memory/constitution.md`, and release decisions are in [`docs/decisions.md`](docs/decisions.md). [`CLAUDE.md`](CLAUDE.md) holds the conventions and working rules for coding agents. To propose a change, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence

Scribe Desk is released under the MIT licence; see [`LICENSE`](LICENSE). Third-party files are listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
