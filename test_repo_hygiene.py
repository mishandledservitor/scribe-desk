#!/usr/bin/env python3
"""Guards against machine-specific paths in tracked files."""

import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent
SELF = Path(__file__).name
# Built from pieces so this file does not match itself.
PATTERNS = [
    re.compile("/" + "Users/"),
    re.compile(r"~/" + "git/"),
    re.compile(r"\$HOME/" + "git"),
    re.compile("vox" + "box", re.IGNORECASE),
]


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True)
    return [p for p in out.stdout.decode().split("\0") if p]


class TestNoMachineSpecificPaths(unittest.TestCase):
    def test_tracked_text_files_have_no_home_paths(self):
        hits = []
        for rel in tracked_files():
            if rel == SELF:
                continue
            path = REPO / rel
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if any(p.search(line) for p in PATTERNS):
                    hits.append(f"{rel}:{n}: {line.strip()[:120]}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
