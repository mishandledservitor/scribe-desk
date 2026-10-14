#!/usr/bin/env python3
"""Tests for build_app.py, which writes Scribe Desk.app for this clone."""

import os
import plistlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import build_app

PYTHON_CANDIDATES = ("/opt/homebrew/bin/python3", "/usr/local/bin/python3", "/usr/bin/python3")


def _has_tk_python():
    for c in PYTHON_CANDIDATES:
        if os.access(c, os.X_OK):
            r = subprocess.run([c, "-c", "import tkinter"], capture_output=True)
            if r.returncode == 0:
                return True
    return False


class TestBuildApp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        # A repo path with a space and a quote must survive the launcher.
        self.repo = self.tmp / "my repo's clone"
        self.repo.mkdir()
        self.bundle = build_app.build(self.tmp / "dest", self.repo)

    def tearDown(self):
        self._tmp.cleanup()

    def test_bundle_layout_and_version(self):
        self.assertEqual(self.bundle.name, "Scribe Desk.app")
        contents = self.bundle / "Contents"
        with open(contents / "Info.plist", "rb") as f:
            info = plistlib.load(f)
        self.assertEqual(info["CFBundleShortVersionString"], "1.0.0")
        self.assertEqual(info["CFBundleVersion"], "1.0.0")
        launcher = contents / "MacOS" / info["CFBundleExecutable"]
        self.assertTrue(os.access(launcher, os.X_OK))
        self.assertTrue((contents / "Resources" / f"{info['CFBundleIconFile']}.icns").is_file())
        self.assertNotIn("$HOME", launcher.read_text())

    def test_rebuild_overwrites(self):
        again = build_app.build(self.tmp / "dest", self.repo)
        self.assertEqual(again, self.bundle)
        self.assertTrue((again / "Contents" / "Info.plist").is_file())

    @unittest.skipUnless(_has_tk_python(), "no python3 with tkinter at a standard path")
    def test_moved_bundle_starts_the_repo_gui(self):
        (self.repo / "scribedesk_gui.py").write_text(
            "import os\nopen('started.txt', 'w').write(os.getcwd())\n")
        moved = self.tmp / "Applications" / "Scribe Desk.app"
        moved.parent.mkdir()
        shutil.move(str(self.bundle), moved)
        launcher = moved / "Contents" / "MacOS" / "scribe-desk"
        proc = subprocess.run([str(launcher)], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        marker = self.repo / "started.txt"
        self.assertTrue(marker.is_file())
        self.assertEqual(os.path.realpath(marker.read_text()), os.path.realpath(self.repo))


if __name__ == "__main__":
    unittest.main()
