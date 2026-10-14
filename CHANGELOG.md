# Changelog

What changes in Scribe Desk from one release to the next, for people who use it. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-14

First public release. Scribe Desk is a macOS Tk app and a command-line tool that transcribe audio and video files with the ElevenLabs Scribe API, using your own API key.

### Added

- Projects each keep their own key terms, speaker labels, diarization settings, model, language, output format and output folder, and picking a project loads them all.
- The **Output** field sends a project's transcripts to any folder. Left blank, they go to `output/<project>/` in the repository. The hint under the field shows the resolved folder, says whether it exists yet, and warns when another project writes to the same one.
- Transcripts can be written as plain text (optionally with `[hh:mm:ss]` prefixes), SRT, VTT or JSON.
- Speaker labels accept `0=Jane Smith` as well as the raw `speaker_0=Jane Smith` form, and a run warns when a label matched nobody in the audio.
- A finished result opens with a double-click, and **↩ Re-transcribe** sends its audio back for another pass.
- Failed transcriptions report the API's message in one line with a hint for common causes, such as an invalid key, missing credits or a rejected option.
- The account line shows your ElevenLabs plan, credits left and renewal date when the key has **User: Read** access.
- `scribe-desk-stt` transcribes a single file from the command line with every option as a flag, and checks the file before it looks for a key.
- `setup.sh` builds `Scribe Desk.app` for your clone. The app can be moved to `/Applications` or the Dock and still opens that clone.

### Changed

- The API key is read only from the `ELEVENLABS_API_KEY` environment variable or from `.env` in the repository, and the command-line tool uses only the repository's own `venv/`.

### Fixed

- Deleting a project archives its settings instead of removing them, and only deletes transcripts in the tool's own `output/<project>/` folder when no other project uses it. A folder you chose yourself is never deleted, including when it is reached through a symlink or typed in a different case.
- A new project with the name of a deleted one no longer takes over the transcripts the deleted project kept.
- A project registry that cannot be read, as opposed to one that is corrupt, now shows an error instead of making every project disappear.
- A key term containing a comma, such as "Acme, Inc.", is no longer split into two billed terms.
- Very long project names no longer leave a half-created project behind.

### Known limitations

- The GUI and the app need macOS; on other systems, use `scribe-desk-stt`.
- The app is not notarised and must be rebuilt with `setup.sh` if the repository moves.
