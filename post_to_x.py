#!/usr/bin/env python3
"""
post_to_x.py — posts the freshest not-yet-tweeted LITTERPOSTING rant from
transcripts/ to X (Twitter), as the catrooms' account. The account's voice
is STRAY (Meowizen #13): the litterposting generation task narrates about
35% of rants as STRAY, with the ten named Meowizens (BYTE, KNIFEBOY, SHADE,
etc.) making up the other 65%, rotating between them. Every transcript now
carries an explicit top-level "narrator" field (also shown on the live
site), so this script doesn't need any detection logic of its own — it
just always tweets whatever the freshest litterposting rant is, and the
STRAY/named-cast ratio falls out naturally from how often each actually
gets written.

Runs are rate-limited to roughly every 3-6 hours (randomized each time, not
a fixed interval) via a next_eligible_at timestamp kept in state — so this
script is meant to be invoked frequently (e.g. every 15-30 min via launchd)
and will just no-op most of those times until the window opens.

This is a LOCAL script, meant to run from your own machine (via its own
launchd job, same pattern as auto_push.sh) — NOT from a Cowork scheduled
task. The scheduled tasks' sandbox blocks outbound calls to X's API, the
same way it blocks direct model API calls; this only works from a machine
with normal internet access.

Usage:
    python3 post_to_x.py              # posts if the 3-6hr window has opened and there's something new
    python3 post_to_x.py --dry-run    # prints what would currently be tweeted, ignoring the time window; no post, no state change

State is tracked in x_post_state.json: the last-tweeted transcript id (so
the same rant never gets posted twice) and next_eligible_at (so a burst of
runs doesn't post more than once per window, and a gap in runs doesn't
cause a backlog dump — it always just posts whatever is currently newest
once the window opens).
"""

import argparse
import glob
import json
import os
import random
import re
import sys
from datetime import datetime, timedelta, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_DIR = os.path.join(SCRIPT_DIR, "transcripts")
STATE_PATH = os.path.join(SCRIPT_DIR, "x_post_state.json")
MAX_TWEET_LEN = 280


def _entry_sort_key(data):
    try:
        return datetime.fromisoformat(data["started_at"])
    except (KeyError, ValueError, TypeError):
        return datetime.min.replace(tzinfo=timezone.utc)


MIN_HOURS_BETWEEN_POSTS = 3
MAX_HOURS_BETWEEN_POSTS = 6


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"last_tweeted_id": None, "next_eligible_at": None}


def schedule_next_window(state, now):
    """Pick a random point 3-6 hours from now and stash it in state as the
    next time this script is allowed to post."""
    next_at = now + timedelta(hours=random.uniform(MIN_HOURS_BETWEEN_POSTS, MAX_HOURS_BETWEEN_POSTS))
    state["next_eligible_at"] = next_at.isoformat()


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def find_newest_litterposting():
    """Return (transcript_dict, path) for the newest litterposting
    transcript by started_at, or (None, None) if there are none."""
    paths = glob.glob(os.path.join(TRANSCRIPTS_DIR, "conversation-litterposting-*.json"))
    best = None
    best_path = None
    best_key = None
    for path in paths:
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        key = _entry_sort_key(data)
        if best_key is None or key > best_key:
            best, best_path, best_key = data, path, key
    return best, best_path


def build_tweet_text(transcript):
    """Concatenate the rant's spoken turns and cut it down to fit a
    tweet, preferring a clean sentence-boundary cut over a mid-sentence
    hard truncation."""
    parts = [t["text"].strip() for t in transcript.get("turns", []) if t.get("actor") == "lm1"]
    full_text = re.sub(r"\s+", " ", " ".join(parts)).strip()

    if len(full_text) <= MAX_TWEET_LEN:
        return full_text

    best_cut = None
    for m in re.finditer(r"[.!?]\s", full_text):
        end = m.end()
        if end <= MAX_TWEET_LEN:
            best_cut = end
        else:
            break

    if best_cut and best_cut >= 40:
        return full_text[:best_cut].strip()

    truncated = full_text[:MAX_TWEET_LEN - 1].rsplit(" ", 1)[0]
    return truncated.rstrip(",;: ") + "…"


def post_tweet(text):
    from requests_oauthlib import OAuth1Session

    required = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required .env keys: {', '.join(missing)}")

    oauth = OAuth1Session(
        client_key=os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = oauth.post("https://api.x.com/2/tweets", json={"text": text})
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"X API error {resp.status_code}: {resp.text}")
    return resp.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print what would be tweeted right now, ignoring the time window; don't post or touch state")
    args = parser.parse_args()

    transcript, path = find_newest_litterposting()
    if transcript is None:
        print("No litterposting transcripts found.")
        return 0

    state = load_state()
    now = datetime.now(timezone.utc)

    if args.dry_run:
        tweet_text = build_tweet_text(transcript)
        print(f"Transcript: {transcript['id']}")
        print(f"Tweet ({len(tweet_text)} chars):\n{tweet_text}")
        print("\n[dry run — not posting, not updating state, ignoring the 3-6hr window]")
        return 0

    next_eligible_at = state.get("next_eligible_at")
    if next_eligible_at:
        next_eligible_dt = datetime.fromisoformat(next_eligible_at)
        if now < next_eligible_dt:
            print(f"Not yet — next posting window opens at {next_eligible_dt.isoformat()}.")
            return 0

    if transcript["id"] == state.get("last_tweeted_id"):
        print(f"Window is open but nothing new — newest litterposting post ({transcript['id']}) was already tweeted. Trying again next window.")
        schedule_next_window(state, now)
        save_state(state)
        return 0

    tweet_text = build_tweet_text(transcript)
    print(f"Transcript: {transcript['id']}")
    print(f"Tweet ({len(tweet_text)} chars):\n{tweet_text}")

    result = post_tweet(tweet_text)
    tweet_id = result.get("data", {}).get("id")
    print(f"\nPosted. Tweet id: {tweet_id}")

    state["last_tweeted_id"] = transcript["id"]
    state["last_tweeted_at"] = now.isoformat()
    schedule_next_window(state, now)
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
