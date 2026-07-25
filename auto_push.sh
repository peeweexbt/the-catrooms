#!/bin/bash
# auto_push.sh — commits and pushes any new/changed files in this folder
# (new transcripts, rebuilt docs/) to GitHub, if there's anything to push.
# Meant to be run periodically by launchd, shortly after the hourly
# Cowork task has generated a new conversation and rebuilt docs/.
#
# Safe to run even when there's nothing new: it just logs "no changes" and
# exits cleanly instead of erroring.

set -uo pipefail
cd "$(dirname "$0")"

LOG="push.log"

{
  echo "=== $(date) ==="

  git add -A

  if git diff --cached --quiet; then
    echo "no changes, skipping push"
  else
    git commit -m "auto update $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    if git push; then
      echo "pushed successfully"
    else
      echo "PUSH FAILED — check that 'git push' works manually from Terminal in this folder (credentials may need re-authenticating)"
    fi
  fi

  echo ""
} >> "$LOG" 2>&1
