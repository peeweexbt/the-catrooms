#!/usr/bin/env python3
"""
post_to_x.py — posts a not-yet-tweeted LITTERPOSTING rant from transcripts/
to X (Twitter, @thecatrooms), as the catrooms' account. The account's voice
is STRAY (Meowizen #13).

The site's own generation ratio (how often STRAY vs. one of the ten named
Meowizens narrates a given rant) is intentionally kept separate from the X
account's ratio — the site is meant to show a wider variety of narrators,
while X leans much more heavily on STRAY as its dominant, near-constant
voice. So rather than just tweeting whatever's freshest overall, this
script does its own weighted pick each run (see STRAY_TWEET_WEIGHT): most
of the time it looks specifically for the newest untweeted STRAY-narrated
rant; occasionally it instead looks for the newest untweeted rant from one
of the ten named Meowizens. Either way it reads the transcript's top-level
"narrator" field (also shown on the live site) rather than guessing.

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
    python3 post_to_x.py --dry-run    # prints what would currently be picked/tweeted, ignoring the time window; no post, no state change

State is tracked in x_post_state.json: the set of already-tweeted
transcript ids (so nothing gets posted twice, regardless of which category
it was picked from) and next_eligible_at (so a burst of runs doesn't post
more than once per window).
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

# Probability that a given run prefers a STRAY-narrated rant over a
# named-Meowizen one. This is independent of whatever ratio the site's own
# generation task uses — X is meant to be much more STRAY-dominant.
STRAY_TWEET_WEIGHT = 0.9

MIN_HOURS_BETWEEN_POSTS = 3
MAX_HOURS_BETWEEN_POSTS = 6


def _entry_sort_key(data):
    try:
        return datetime.fromisoformat(data["started_at"])
    except (KeyError, ValueError, TypeError):
        return datetime.min.replace(tzinfo=timezone.utc)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            state = json.load(f)
    else:
        state = {}

    if "tweeted_ids" not in state:
        # migrate from the older single-last-id format
        tweeted_ids = [state["last_tweeted_id"]] if state.get("last_tweeted_id") else []
        state["tweeted_ids"] = tweeted_ids
    state.setdefault("next_eligible_at", None)
    return state


def schedule_next_window(state, now):
    """Pick a random point 3-6 hours from now and stash it in state as the
    next time this script is allowed to post."""
    next_at = now + timedelta(hours=random.uniform(MIN_HOURS_BETWEEN_POSTS, MAX_HOURS_BETWEEN_POSTS))
    state["next_eligible_at"] = next_at.isoformat()


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def load_all_litterposting():
    """Return every litterposting transcript dict, newest-first by
    started_at."""
    paths = glob.glob(os.path.join(TRANSCRIPTS_DIR, "conversation-litterposting-*.json"))
    items = []
    for path in paths:
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        items.append(data)
    items.sort(key=_entry_sort_key, reverse=True)
    return items


def pick_transcript(tweeted_ids):
    """Weighted pick among untweeted litterposting rants: usually the
    newest untweeted STRAY-narrated one, occasionally the newest untweeted
    one from a named Meowizen instead — falling back to whichever category
    actually has candidates if the preferred one is empty."""
    untweeted = [t for t in load_all_litterposting() if t["id"] not in tweeted_ids]
    if not untweeted:
        return None

    stray_posts = [t for t in untweeted if (t.get("narrator") or "STRAY") == "STRAY"]
    named_posts = [t for t in untweeted if (t.get("narrator") or "STRAY") != "STRAY"]

    prefer_stray = random.random() < STRAY_TWEET_WEIGHT
    primary, fallback = (stray_posts, named_posts) if prefer_stray else (named_posts, stray_posts)
    if primary:
        return primary[0]
    return fallback[0] if fallback else None


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


def _oauth_session():
    from requests_oauthlib import OAuth1Session

    required = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required .env keys: {', '.join(missing)}")

    return OAuth1Session(
        client_key=os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def post_tweet(text):
    oauth = _oauth_session()
    resp = oauth.post("https://api.x.com/2/tweets", json={"text": text})
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"X API error {resp.status_code}: {resp.text}")
    return resp.json()


def whoami():
    """Read-only sanity check: confirms the OAuth1 credentials authenticate
    at all, independent of whether the app actually has write access."""
    oauth = _oauth_session()
    resp = oauth.get("https://api.x.com/2/users/me")
    print(f"GET /2/users/me -> {resp.status_code}")
    print(resp.text)
    return resp.status_code in (200, 201)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print what would be tweeted right now, ignoring the time window; don't post or touch state")
    parser.add_argument("--whoami", action="store_true", help="read-only auth check against X's API; doesn't touch transcripts or state")
    args = parser.parse_args()

    if args.whoami:
        ok = whoami()
        return 0 if ok else 1

    state = load_state()
    now = datetime.now(timezone.utc)

    if args.dry_run:
        transcript = pick_transcript(state["tweeted_ids"])
        if transcript is None:
            print("No untweeted litterposting transcripts found.")
            return 0
        tweet_text = build_tweet_text(transcript)
        print(f"Transcript: {transcript['id']} (narrator: {transcript.get('narrator') or 'STRAY'})")
        print(f"Tweet ({len(tweet_text)} chars):\n{tweet_text}")
        print("\n[dry run — not posting, not updating state, ignoring the 3-6hr window]")
        return 0

    next_eligible_at = state.get("next_eligible_at")
    if next_eligible_at:
        next_eligible_dt = datetime.fromisoformat(next_eligible_at)
        if now < next_eligible_dt:
            print(f"Not yet — next posting window opens at {next_eligible_dt.isoformat()}.")
            return 0

    transcript = pick_transcript(state["tweeted_ids"])
    if transcript is None:
        print("Window is open but nothing new to post. Trying again next window.")
        schedule_next_window(state, now)
        save_state(state)
        return 0

    tweet_text = build_tweet_text(transcript)
    print(f"Transcript: {transcript['id']} (narrator: {transcript.get('narrator') or 'STRAY'})")
    print(f"Tweet ({len(tweet_text)} chars):\n{tweet_text}")

    result = post_tweet(tweet_text)
    tweet_id = result.get("data", {}).get("id")
    print(f"\nPosted. Tweet id: {tweet_id}")

    state["tweeted_ids"].append(transcript["id"])
    state["last_tweeted_at"] = now.isoformat()
    schedule_next_window(state, now)
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
