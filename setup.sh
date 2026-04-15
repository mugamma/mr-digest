#!/bin/bash
# One-time setup: create venv, install deps, install cron job.
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

# ── Cron job (4 PM local time, every day) ───────────────────────────────────
CRON_CMD="0 16 * * * $SCRIPT_DIR/run.sh"
TMPFILE=$(mktemp)

# Dump current crontab (ignore error if empty)
crontab -l 2>/dev/null > "$TMPFILE" || true

if grep -qF "$SCRIPT_DIR/run.sh" "$TMPFILE"; then
  echo "Cron job already installed."
else
  echo "$CRON_CMD" >> "$TMPFILE"
  crontab "$TMPFILE"
  echo "Cron job installed: runs daily at 4:00 PM."
fi

rm -f "$TMPFILE"

chmod +x "$SCRIPT_DIR/run.sh"

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
