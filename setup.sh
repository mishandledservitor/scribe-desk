#!/bin/bash
# One-time setup: a local venv with the ElevenLabs SDK, and Scribe Desk.app
# built for this clone. Safe to rerun, for example after moving the repo.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install elevenlabs

python3 build_app.py

echo
echo "✅ Done. Add your API key:"
echo "   cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env   # then paste the key after ELEVENLABS_API_KEY="
echo "   (or export ELEVENLABS_API_KEY in your shell)"
echo
echo "Launch the GUI with: $SCRIPT_DIR/scribe-desk, or double-click Scribe Desk.app"
