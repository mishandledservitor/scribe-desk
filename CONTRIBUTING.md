# Contributing to Scribe Desk

Bug reports, fixes and new features are all welcome.

## Before you start

- **For a security problem,** such as a way to expose an API key or delete files the tool does not own, do not open a public issue. Report it privately from the repository's **Security** tab with **Report a vulnerability**.
- **For a bug,** open an issue that says what you did, what you expected and what happened instead. Include your macOS and Python versions. Never paste an API key, a real transcript, real audio or a key-term list of real people's names.
- **For a new feature or a change in behaviour,** open an issue first and describe the problem it solves. Agreeing on the idea before you write code saves you from building something that won't be merged.
- **For a typo or a small fix,** go straight to a pull request.

## Setting up

You need macOS and Python 3.10 or later with tkinter.

```sh
git clone https://github.com/<your-account>/scribe-desk.git
cd scribe-desk
./setup.sh
python3 -m pip install pytest
```

`setup.sh` creates `venv/` with the ElevenLabs SDK and builds `Scribe Desk.app`. The README explains how to get the ElevenLabs key you need to try a real transcription. No automated test needs a key.

## How changes are made here

**Every change to what a user sees starts with a spec.** The project uses [Spec Kit](https://github.com/github/spec-kit). A feature has its own folder under `specs/` with a `spec.md` (what it does and why), a `plan.md` (how it is built) and a `tasks.md` (the steps). If your change adds or alters behaviour, add or update the spec in the same pull request. A fix that makes the code match an existing spec does not need a new one. The principles that outrank everything else are in `.specify/memory/constitution.md`.

**Tests come first.** Write a test that fails because the behaviour is missing, then write the code that makes it pass, then tidy up with the tests still passing. A pull request that changes behaviour without a test for it will be asked for one.

**Tests never touch real data or the network.** Tests that create, move or delete files point the module's folders at a temporary directory, and the API is replaced with fakes. Never add a real API key, real audio, a real transcript or real people's names to the repository. Example people use generic names such as John Doe and Jane Smith.

**Deleting data needs extra care.** `scribedesk_config.py` owns every operation that can destroy a user's key terms or transcripts. A change there must fail safe: when in doubt, it refuses or warns rather than deletes.

**GUI changes are tried by hand.** The tests cover the plain functions behind the Tk callbacks, not the widgets. If you change the GUI, also start it and try the change by hand, and say in the pull request what you tried.

## Before you open a pull request

Run the same checks as CI:

```sh
python3 -m compileall -q *.py
bash -n setup.sh scribe-desk scribe-desk-stt
python3 -m pytest -q
```

Then open the pull request against `main`:

- Keep it to one change, and say in the description what it does and why. Link the issue it closes.
- If it changes what a user sees, add a line under `## [Unreleased]` in [`CHANGELOG.md`](CHANGELOG.md), written for the people who use the tool.
- CI must pass. On your first pull request, CI starts once a maintainer approves the run.
- Expect review comments; a maintainer merges the pull request once it is ready.

## Using coding agents

[`CLAUDE.md`](CLAUDE.md) holds the working rules for AI coding agents, and the Spec Kit commands are in `.claude/skills/`. Contributions written with an agent are welcome on the same terms as any other: the spec, the tests and the checks above all apply, and you are responsible for what you submit.

## Licence

Scribe Desk is released under the MIT licence. By opening a pull request, you agree that your contribution is released under the same licence.
