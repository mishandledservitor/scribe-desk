#!/bin/bash
# One-time setup: local venv with the ElevenLabs SDK.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install elevenlabs

echo
echo "✅ Done. Add your API key:"
echo "   echo 'ELEVENLABS_API_KEY=sk_...' > $SCRIPT_DIR/.env"
echo "   (or export ELEVENLABS_API_KEY; the voxbox speech-to-text .env also works)"
echo
echo "Launch the GUI with: $SCRIPT_DIR/scribe-desk"
