#!/bin/bash
# post_to_x.sh — wrapper so launchd can invoke post_to_x.py with a sane
# working directory and PATH, same pattern as auto_push.sh. Safe to run
# frequently: post_to_x.py itself no-ops most of the time until its
# internal 3-6hr posting window opens.

set -uo pipefail
cd "$(dirname "$0")"

LOG="x_post.log"

{
  echo "=== $(date) ==="
  python3 post_to_x.py
  echo ""
} >> "$LOG" 2>&1
