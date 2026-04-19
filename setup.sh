#!/bin/bash
# One-time setup: create venv, install deps, install systemd user timer.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Virtual environment ──────────────────────────────────────────────────────
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "Dependencies installed."

# ── .env file ────────────────────────────────────────────────────────────────
if [ ! -f "$SCRIPT_DIR/.env" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo ""
  echo "Created .env from .env.example — edit it with your credentials:"
  echo "  $SCRIPT_DIR/.env"
fi

chmod +x "$SCRIPT_DIR/run.sh"

# ── systemd user timer (runs daily at 4 PM, catches up missed runs) ─────────
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"

sed "s|@SCRIPT_DIR@|$SCRIPT_DIR|g" "$SCRIPT_DIR/systemd/mr-digest.service.in" \
  > "$UNIT_DIR/mr-digest.service"
cp "$SCRIPT_DIR/systemd/mr-digest.timer" "$UNIT_DIR/mr-digest.timer"

systemctl --user daemon-reload
systemctl --user enable --now mr-digest.timer
echo "systemd timer installed and enabled."

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and fill in:"
echo "       GMAIL_USER         — Gmail address used to send the digest"
echo "       GMAIL_APP_PASSWORD — 16-char app password (see below)"
echo "       DIGEST_TO_EMAIL    — address where the digest is delivered"
echo ""
echo "  How to get a Gmail App Password:"
echo "    a. Go to myaccount.google.com → Security"
echo "    b. Enable 2-Step Verification (required)"
echo "    c. Search for 'App passwords', create one (name it 'MR Digest')"
echo "    d. Copy the 16-character password into GMAIL_APP_PASSWORD"
echo ""
echo "  2. Test a manual run:"
echo "       bash $SCRIPT_DIR/run.sh"
echo "     Then check logs/digest.log"
echo ""
echo "  Timer commands:"
echo "       systemctl --user list-timers mr-digest.timer   # next scheduled run"
echo "       systemctl --user status mr-digest.service      # last run status"
echo "       systemctl --user start mr-digest.service       # trigger now"
