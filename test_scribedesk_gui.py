#!/usr/bin/env python3
"""Tests for the testable functions behind scribedesk_gui.py.

Importing the module is safe with no window server — tk.Tk() only runs
under `if __name__ == "__main__"` — but no widget can be constructed here,
so anything GUI-callback-shaped is verified by unit-testing the plain
function behind it instead. See CLAUDE.md rule 5.
"""

import os
import tempfile
import unittest
from unittest import mock

import scribedesk_gui


class TestOpenTranscript(unittest.TestCase):
    """open_transcript(path) -> bool: shells out to `open` on an existing
    file, and reports failure instead of raising on a missing one."""

    def test_opens_existing_file_with_the_platform_opener(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            with mock.patch.object(scribedesk_gui.subprocess, "Popen") as popen:
                result = scribedesk_gui.open_transcript(path)
            popen.assert_called_once_with(["open", path])
            self.assertTrue(result)
        finally:
            os.remove(path)

    def test_missing_file_reports_failure_without_raising(self):
        missing = "/tmp/does-not-exist-scribedesk-test.txt"
        self.assertFalse(os.path.exists(missing))
        with mock.patch.object(scribedesk_gui.subprocess, "Popen") as popen:
            result = scribedesk_gui.open_transcript(missing)
        popen.assert_not_called()
        self.assertFalse(result)

    def test_empty_path_reports_failure_without_raising(self):
        with mock.patch.object(scribedesk_gui.subprocess, "Popen") as popen:
            result = scribedesk_gui.open_transcript("")
        popen.assert_not_called()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
