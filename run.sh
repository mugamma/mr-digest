#!/bin/bash
# Wrapper called by cron. Activates the venv and runs the digest.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/logs/digest.log"

mkdir -p "$SCRIPT_DIR/logs"

{
  echo "========================================"
  echo "Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "========================================"

  source "$SCRIPT_DIR/.venv/bin/activate"
  python3 "$SCRIPT_DIR/digest.py"

  echo "Finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
} >> "$LOGFILE" 2>&1
