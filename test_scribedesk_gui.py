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


class TestMoveToProcessed(unittest.TestCase):
    """move_to_processed(input_path) -> str: the audio's final location in
    all three cases — moved into PROCESSED_DIR, left alone because it wasn't
    in INBOX_DIR, or left alone because the move raised."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.inbox = os.path.join(self.tmp, "inbox")
        self.processed = os.path.join(self.tmp, "processed")
        os.makedirs(self.inbox)
        self._inbox_patch = mock.patch.object(scribedesk_gui, "INBOX_DIR", self.inbox)
        self._processed_patch = mock.patch.object(scribedesk_gui, "PROCESSED_DIR", self.processed)
        self._inbox_patch.start()
        self._processed_patch.start()

    def tearDown(self):
        self._inbox_patch.stop()
        self._processed_patch.stop()

    def test_moves_a_file_that_lived_in_inbox(self):
        src = os.path.join(self.inbox, "meeting.wav")
        with open(src, "w") as f:
            f.write("audio")
        result = scribedesk_gui.move_to_processed(src)
        self.assertEqual(result, os.path.join(self.processed, "meeting.wav"))
        self.assertTrue(os.path.isfile(result))
        self.assertFalse(os.path.exists(src))

    def test_leaves_a_file_outside_inbox_unmoved(self):
        outside_dir = os.path.join(self.tmp, "elsewhere")
        os.makedirs(outside_dir)
        src = os.path.join(outside_dir, "meeting.wav")
        with open(src, "w") as f:
            f.write("audio")
        result = scribedesk_gui.move_to_processed(src)
        self.assertEqual(result, src)
        self.assertTrue(os.path.isfile(src))

    def test_returns_input_path_unchanged_when_the_move_raises(self):
        src = os.path.join(self.inbox, "meeting.wav")
        with open(src, "w") as f:
            f.write("audio")
        with mock.patch.object(scribedesk_gui.shutil, "move",
                                side_effect=OSError("disk full")):
            result = scribedesk_gui.move_to_processed(src)
        self.assertEqual(result, src)
        self.assertTrue(os.path.isfile(src))


class TestRequeueAudio(unittest.TestCase):
    """requeue_audio(path) -> bool: never raises, mirrors open_transcript."""

    def test_existing_file_returns_true(self):
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            self.assertTrue(scribedesk_gui.requeue_audio(path))
        finally:
            os.remove(path)

    def test_missing_path_returns_false_without_raising(self):
        missing = "/tmp/does-not-exist-scribedesk-requeue-test.wav"
        self.assertFalse(os.path.exists(missing))
        self.assertFalse(scribedesk_gui.requeue_audio(missing))

    def test_empty_path_returns_false_without_raising(self):
        self.assertFalse(scribedesk_gui.requeue_audio(""))


class TestResultCarriesAudioPath(unittest.TestCase):
    """A successful result dict records where the audio actually ended up,
    so the done screen can offer it back for a second pass."""

    def test_worker_run_records_audio_key_on_success(self):
        tmp = tempfile.mkdtemp()
        inbox = os.path.join(tmp, "inbox")
        processed = os.path.join(tmp, "processed")
        output_dir = os.path.join(tmp, "out")
        os.makedirs(inbox)
        src = os.path.join(inbox, "meeting.wav")
        with open(src, "w") as f:
            f.write("audio")

        with mock.patch.object(scribedesk_gui, "INBOX_DIR", inbox), \
             mock.patch.object(scribedesk_gui, "PROCESSED_DIR", processed):
            worker = scribedesk_gui.Worker(
                [src], {"format": "text", "model": "scribe_v2", "timestamps": "word"},
                output_dir,
                __import__("queue").Queue(), __import__("threading").Event())

            def fake_popen(cmd, **kwargs):
                # Write the expected output file, as if scribe-desk-stt ran.
                out_path = cmd[cmd.index("-o") + 1]
                with open(out_path, "w") as f:
                    f.write("transcript")
                m = mock.Mock()
                m.stdout = iter(["stage: done\n"])
                m.wait.return_value = 0
                m.poll.return_value = 0
                return m

            with mock.patch.object(scribedesk_gui.subprocess, "Popen", side_effect=fake_popen):
                worker.run()

        results = worker.q.get_nowait()
        # Drain remaining queue messages to find "all_done".
        all_done = None
        msgs = [results]
        while True:
            try:
                msgs.append(worker.q.get_nowait())
            except Exception:
                break
        for m in msgs:
            if m[0] == "all_done":
                all_done = m[1]
        self.assertIsNotNone(all_done)
        self.assertEqual(len(all_done), 1)
        r = all_done[0]
        self.assertTrue(r["ok"])
        self.assertIn("audio", r)
        self.assertEqual(r["audio"], os.path.join(processed, "meeting.wav"))


if __name__ == "__main__":
    unittest.main()
