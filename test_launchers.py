#!/usr/bin/env python3
"""Tests for the shell launchers, run for real in a sandbox folder."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent


class TestSttLauncher(unittest.TestCase):
    def test_without_a_repo_venv_it_asks_for_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = tmp / "repo"
            repo.mkdir()
            shutil.copy2(REPO / "scribe-desk-stt", repo / "scribe-desk-stt")
            # A virtual environment belonging to some other tool under HOME
            # must not be picked up.
            home = tmp / "home"
            other_venv = home / "git" / "other-tool" / "venv" / "bin"
            other_venv.mkdir(parents=True)
            (other_venv / "activate").write_text("")
            env = dict(os.environ, HOME=str(home))
            proc = subprocess.run(["bash", str(repo / "scribe-desk-stt"), "-h"],
                                  capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("setup.sh", proc.stderr)


if __name__ == "__main__":
    unittest.main()
