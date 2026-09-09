# Tasks: A GitHub Actions workflow runs the test suite on every push

**Input**: `specs/003-ci-workflow/plan.md`, `specs/003-ci-workflow/spec.md`

## Tasks

- [X] T001 Read `test_scribedesk_gui.py` and `scribedesk_gui.py` in full to confirm no widget tree
  is built outside `if __name__ == "__main__":` — the fact FR-003's "no xvfb" decision rests on.
- [X] T002 Write `.github/workflows/test.yml`: triggers on `push` and `pull_request` to `main`;
  one `ubuntu-latest` job; checkout; `sudo apt-get update && sudo apt-get install -y python3-tk`;
  `python3 -m venv .venv` then `.venv/bin/pip install --upgrade pip pytest`; a step running
  `.venv/bin/python -m pytest -q`; a separate step running
  `.venv/bin/python -m unittest test_scribedesk_gui -v`.
- [X] T003 Validate the workflow file parses as YAML
  (`python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/test.yml'))"`).
- [X] T004 Run both test commands locally, in the worktree, exactly as the workflow spells them
  (via the venv), foreground, 300000 ms timeout each; paste the output (SC-002).
- [X] T005 Prove the workflow's pytest step actually catches a regression: temporarily flip one
  assertion in a pytest-collected test file to false, re-run `python3 -m pytest -q`, paste the red,
  revert, confirm green again (SC-003).
- [X] T006 Commit `.github/workflows/test.yml` and `specs/003-ci-workflow/` by named path.

## Notes

- No application code changes; no `requirements.txt` added, matching the repo's existing
  dependency shape (standard library plus pytest, installed ad hoc).
- This dispatch owns exactly `.github/workflows/test.yml` and `specs/003-ci-workflow/`; nothing
  else in this worktree is touched or staged.
