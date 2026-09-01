#!/usr/bin/env python3
"""Regression tests for scribedesk_config.py.

Every test reassigns the module's path constants to a fresh tempfile
sandbox and exercises the real functions in the module directly -- no
mocking of anything under test, and never against this repo's own
config/, output/, or projects.json. This is the technique the
2026-09-01 adversarial review's own probe scripts used to reproduce
findings 0, 4 and 6 of reports/2026-09-01-adversarial-review-scribe-desk.md
in vl-management, and this file's tests are that reproduction, kept.
"""

import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

import scribedesk_config as cfg


class SandboxTestCase(unittest.TestCase):
    """Base class: points cfg's module-level path constants at a scratch dir."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="sd-test-")
        self._root = Path(self._tmp)
        self._orig = {
            name: getattr(cfg, name)
            for name in (
                "SCRIPT_DIR", "INBOX_DIR", "OUTPUT_DIR",
                "PROCESSED_DIR", "CONFIG_DIR", "PROJECTS_FILE",
            )
        }
        cfg.SCRIPT_DIR = self._root
        cfg.INBOX_DIR = self._root / "inbox"
        cfg.OUTPUT_DIR = self._root / "output"
        cfg.PROCESSED_DIR = self._root / "processed"
        cfg.CONFIG_DIR = self._root / "config"
        cfg.PROJECTS_FILE = self._root / "projects.json"
        cfg.ensure_dirs()

    def tearDown(self):
        for name, value in self._orig.items():
            setattr(cfg, name, value)
        # A test that chmod'd something unreadable must be restorable before
        # rmtree can walk it.
        for dirpath, dirnames, filenames in os.walk(self._tmp):
            for name in dirnames + filenames:
                try:
                    os.chmod(os.path.join(dirpath, name), 0o755)
                except OSError:
                    pass
        try:
            os.chmod(self._tmp, 0o755)
        except OSError:
            pass
        shutil.rmtree(self._tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# User Story 1 (P1, CRITICAL) -- a recreated project must not adopt a deleted
# project's kept-on-purpose transcripts.
# --------------------------------------------------------------------------- #

class RecreatedProjectDoesNotAdoptKeptTranscripts(SandboxTestCase):
    def test_recreated_project_does_not_adopt_kept_transcripts(self):
        acme = cfg.add_project("Acme")
        self.assertEqual(acme["slug"], "acme")

        kept_transcript = cfg.managed_output_dir("acme") / "board-meeting.txt"
        kept_transcript.parent.mkdir(parents=True, exist_ok=True)
        kept_transcript.write_text("minutes of the meeting", encoding="utf-8")

        removed = cfg.delete_project("acme", delete_output=False)
        self.assertFalse(removed, "delete_output=False must not remove transcripts")
        self.assertTrue(kept_transcript.exists(), "kept transcript must survive the delete")

        acme_again = cfg.add_project("Acme")
        self.assertNotEqual(
            acme_again["slug"], "acme",
            "recreating 'Acme' must not reuse a slug whose output folder "
            "already holds another project's kept transcripts",
        )
        new_output = cfg.managed_output_dir(acme_again["slug"])
        self.assertFalse(
            (new_output / "board-meeting.txt").exists(),
            "the new project's managed folder must not contain the old "
            "project's kept transcript",
        )

        really_removed = cfg.delete_project(acme_again["slug"], delete_output=True)
        self.assertTrue(really_removed)
        self.assertTrue(
            kept_transcript.exists(),
            "deleting the NEW project's transcripts must never destroy the "
            "OLD project's kept transcripts",
        )


# --------------------------------------------------------------------------- #
# User Story 2 (P2) -- an unreadable registry must raise, not silently rebuild.
# --------------------------------------------------------------------------- #

class UnreadableRegistryRaisesInsteadOfRebuilding(SandboxTestCase):
    def test_unreadable_registry_raises_instead_of_rebuilding(self):
        cfg.add_project("Acme")
        cfg.add_project("Podcast")
        before = {p["slug"] for p in cfg.list_projects()}
        self.assertEqual(before, {"acme", "podcast"})

        os.chmod(cfg.PROJECTS_FILE, 0o000)
        try:
            if os.access(cfg.PROJECTS_FILE, os.R_OK):
                self.skipTest(
                    "process can read a 0o000 file (likely running as root); "
                    "cannot exercise an OSError-on-read in this environment"
                )
            with self.assertRaises(cfg.ConfigError):
                cfg.list_projects()
        finally:
            os.chmod(cfg.PROJECTS_FILE, 0o644)

        self.assertTrue(
            cfg.PROJECTS_FILE.exists(),
            "the original registry must still be at its original name",
        )
        corrupt_siblings = list(cfg.PROJECTS_FILE.parent.glob("projects.json.corrupt-*"))
        self.assertEqual(
            corrupt_siblings, [],
            "an unreadable-but-not-corrupt registry must not be renamed away",
        )
        # And nothing was silently overwritten: the original two projects
        # are still there once the file is readable again.
        after = {p["slug"] for p in cfg.list_projects()}
        self.assertEqual(after, {"acme", "podcast"})


class CorruptJsonRegistryStillRebuilds(SandboxTestCase):
    """Pins the non-regression half of FR-003: genuine corruption/emptiness
    must still trigger the existing archive-and-rebuild path unchanged."""

    def test_corrupt_json_registry_still_rebuilds(self):
        cfg.add_project("Acme")
        cfg.PROJECTS_FILE.write_text("{not valid json", encoding="utf-8")

        projects = cfg.list_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], cfg.DEFAULT_PROJECT_NAME)

        corrupt_siblings = list(cfg.PROJECTS_FILE.parent.glob("projects.json.corrupt-*"))
        self.assertEqual(len(corrupt_siblings), 1)


# --------------------------------------------------------------------------- #
# User Story 3 (P3) -- a keyterm containing a comma must survive as one term.
# --------------------------------------------------------------------------- #

class KeytermWithCommaSurvivesRoundTrip(SandboxTestCase):
    def test_keyterm_with_comma_survives_round_trip(self):
        # A raw string is what save_settings actually receives from a
        # hand-edited config/<slug>.json (this repo's own CLAUDE.md calls the
        # registry "hand-editable JSON") and from the GUI's one-per-line
        # editor before this fix -- a *list* input never touched the
        # comma-splitting code path at all, so it would have passed even
        # against the unfixed module. This is the real reproduction.
        cfg.add_project("Acme")
        settings = dict(cfg.DEFAULT_SETTINGS)
        settings["keyterms"] = "Acme, Inc.\nDr. Zhang"
        cfg.save_settings("acme", settings)

        loaded = cfg.load_settings("acme")
        self.assertEqual(
            loaded["keyterms"], ["Acme, Inc.", "Dr. Zhang"],
            "a keyterm containing a comma must round-trip as one term",
        )

    def test_comma_free_keyterms_are_unaffected(self):
        """FR-006: a keyterms value with no commas must behave exactly as
        before -- this must already pass and stay passing."""
        cfg.add_project("Acme")
        settings = dict(cfg.DEFAULT_SETTINGS)
        settings["keyterms"] = ["Acme", "Dr Zhang", "  ", ""]
        cfg.save_settings("acme", settings)

        loaded = cfg.load_settings("acme")
        self.assertEqual(loaded["keyterms"], ["Acme", "Dr Zhang"])


if __name__ == "__main__":
    unittest.main()
