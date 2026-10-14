#!/usr/bin/env python3
"""Build Scribe Desk.app for this clone.

The bundle is generated, not tracked: its launcher has this repo's absolute
path written into it, so the app keeps working after it is dragged to
/Applications or the Dock. setup.sh runs this; rerun it after moving the repo.

    python3 build_app.py            # writes ./Scribe Desk.app
"""

from __future__ import annotations

import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"
APP_NAME = "Scribe Desk"
EXECUTABLE = "scribe-desk"
PROJECT_ROOT = Path(__file__).resolve().parent
ICON = PROJECT_ROOT / "app" / "icon.icns"

INFO = {
    "CFBundleName": APP_NAME,
    "CFBundleDisplayName": APP_NAME,
    "CFBundleIdentifier": "io.github.mishandledservitor.scribedesk",
    "CFBundleVersion": VERSION,
    "CFBundleShortVersionString": VERSION,
    "CFBundlePackageType": "APPL",
    "CFBundleExecutable": EXECUTABLE,
    "CFBundleIconFile": "icon",
    "LSMinimumSystemVersion": "10.13",
    "NSHighResolutionCapable": True,
    "LSApplicationCategoryType": "public.app-category.productivity",
}

LAUNCHER = """#!/bin/bash
# Launcher for Scribe Desk.app, written by build_app.py. Finds a
# tkinter-capable python3 and starts the GUI of the clone it was built from.
set -uo pipefail

REPO=@REPO@

if [ ! -f "$REPO/scribedesk_gui.py" ]; then
    /usr/bin/osascript -e "display alert \\"Scribe Desk\\" message \\"Could not find scribedesk_gui.py in $REPO. If you moved the repo, run setup.sh again.\\" as critical" >/dev/null 2>&1
    exit 1
fi

# Finder launches with a minimal PATH, so probe absolute interpreters and pick
# the first one that actually has tkinter.
PY=""
for c in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [ -x "$c" ] && "$c" -c "import tkinter" >/dev/null 2>&1; then
        PY="$c"; break
    fi
done

if [ -z "$PY" ]; then
    /usr/bin/osascript -e 'display alert "Scribe Desk" message "No python3 with tkinter was found. Install Python with Homebrew (brew install python-tk) or use the scribe-desk-stt CLI." as critical' >/dev/null 2>&1
    exit 1
fi

cd "$REPO"
exec "$PY" "$REPO/scribedesk_gui.py" >>"$REPO/app-launch.log" 2>&1
"""


def build(dest_dir: Path, repo_dir: Path) -> Path:
    """Write `<dest_dir>/Scribe Desk.app` pointing at `repo_dir`; return its path."""
    dest_dir = Path(dest_dir)
    repo_dir = Path(repo_dir).resolve()
    bundle = dest_dir / f"{APP_NAME}.app"
    if bundle.exists():
        shutil.rmtree(bundle)
    contents = bundle / "Contents"
    (contents / "MacOS").mkdir(parents=True)
    (contents / "Resources").mkdir()

    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump(INFO, f)
    shutil.copy2(ICON, contents / "Resources" / "icon.icns")

    launcher = contents / "MacOS" / EXECUTABLE
    launcher.write_text(LAUNCHER.replace("@REPO@", shlex.quote(str(repo_dir))))
    launcher.chmod(0o755)
    return bundle


def main() -> None:
    bundle = build(PROJECT_ROOT, PROJECT_ROOT)
    if shutil.which("codesign"):
        # An ad-hoc signature, so macOS treats the bundle as one unit.
        subprocess.run(["codesign", "--force", "--sign", "-", str(bundle)],
                       check=False, capture_output=True)
    print(f"Built {bundle}")


if __name__ == "__main__":
    sys.exit(main())
