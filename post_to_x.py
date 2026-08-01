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

Runs are rate-limited to roughly once every 90 minutes via a
next_eligible_at timestamp kept in state — so this script is meant to be
invoked frequently (e.g. every 15 min via launchd) and will just no-op most
of those times until the window opens.

This is a LOCAL script, meant to run from your own machine (via its own
launchd job, same pattern as auto_push.sh) — NOT from a Cowork scheduled
task. The scheduled tasks' sandbox blocks outbound calls to X's API, the
same way it blocks direct model API calls; this only works from a machine
with normal internet access.

Usage:
    python3 post_to_x.py                          # posts if the ~90min window has opened and there's something new
    python3 post_to_x.py --dry-run                # prints what would currently be picked/tweeted, ignoring the time window; no post, no state change
    python3 post_to_x.py --now                    # ignore the 90min window and post immediately if there's something new
    python3 post_to_x.py --now --narrator STRAY   # ignore the window AND force the pick to a STRAY-narrated post (skips the weighted pick entirely)
    python3 post_to_x.py --dry-run --narrator STRAY --random   # preview a random eligible STRAY post instead of always the newest one; rerun to see a different one
    python3 post_to_x.py --dry-run --full         # preview with the full untruncated rant forced on (requires X Premium verification to actually post at this length)
    python3 post_to_x.py --dry-run --short        # preview with the classic punchy 280-char cut forced on
    python3 post_to_x.py --text "exact tweet text"            # post this exact custom text right now, no transcript involved, ignores the time window
    python3 post_to_x.py --dry-run --text "exact tweet text"  # preview a custom post without actually sending it

Since the account is now X Premium-verified (raises the real per-post cap
to ~4,000 chars, see EXTENDED_TWEET_LEN), each post rolls FULL_POST_PROBABILITY
(40%) to decide whether to post the rant in full or keep the shorter punchy
cut — pass --full or --short to override that roll for a single run.

State is tracked in x_post_state.json: the set of already-tweeted
transcript ids (so nothing gets posted twice, regardless of which category
it was picked from) and next_eligible_at (so a burst of runs doesn't post
more than once per window).

SCHEDULING MULTIPLE TWEETS AT TIMES YOU CHOOSE:
    python3 post_to_x.py --queue "+2h,+5h,2026-08-02T09:00"   # queue posts to go out ~2hrs from now, ~5hrs from now, and at 9am on Aug 2 (local time)
    python3 post_to_x.py --list-queue                          # show every pending/fired queued post and its status
    python3 post_to_x.py --clear-queue                          # wipe all pending queue entries

Each time can be either relative ("+90m", "+2h", "+1d") or an absolute local
ISO datetime ("2026-08-02T09:00" or "2026-08-02T09:00:00"). Queued posts
don't come with pre-written text — at the scheduled moment, the normal
invocation (run automatically every ~15 min via launchd, same as always)
notices the due entry and auto-picks the newest untweeted post the same way
regular auto-posting does (still respects STRAY_TWEET_WEIGHT). A queued
entry firing also resets the normal ~90min ambient window so it doesn't
double up with an unrelated auto-post right after. Queue state lives in
x_schedule_queue.json.
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
QUEUE_PATH = os.path.join(SCRIPT_DIR, "x_schedule_queue.json")
MAX_TWEET_LEN = 280

# The account's real cap under X Premium verification (~4,000 chars). Almost
# every litterposting rant fits under this in full, so "full post" mode
# below basically never needs to truncate. If you upgrade to Premium+
# (~25,000 chars) or drop verification back to none (280 chars again),
# update this.
EXTENDED_TWEET_LEN = 4000

# Probability that a given post uses the FULL rant (up to EXTENDED_TWEET_LEN)
# instead of the classic punchy MAX_TWEET_LEN-cut version. Requires the
# account to actually be verified (Premium or higher) — un-verified accounts
# are capped at 280 chars by X itself regardless of what text is sent, so
# leave this at 0 if verification lapses.
FULL_POST_PROBABILITY = 0.4

# Probability that a given run prefers a STRAY-narrated rant over a
# named-Meowizen one. This is independent of whatever ratio the site's own
# generation task uses — X is meant to be much more STRAY-dominant.
STRAY_TWEET_WEIGHT = 0.9

MIN_HOURS_BETWEEN_POSTS = 1.42   # ~85 min
MAX_HOURS_BETWEEN_POSTS = 1.58   # ~95 min


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
    """Pick a random point ~90 minutes from now and stash it in state as the
    next time this script is allowed to post."""
    next_at = now + timedelta(hours=random.uniform(MIN_HOURS_BETWEEN_POSTS, MAX_HOURS_BETWEEN_POSTS))
    state["next_eligible_at"] = next_at.isoformat()


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def load_queue():
    if os.path.exists(QUEUE_PATH):
        with open(QUEUE_PATH) as f:
            return json.load(f)
    return []


def save_queue(queue):
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2)


def parse_schedule_time(raw, now_utc):
    """Parse one --queue entry into an aware UTC datetime.

    Accepts either a relative shorthand ("+90m", "+2h", "+1d") measured from
    right now, or an absolute ISO datetime ("2026-08-02T09:00" or with
    seconds) which is treated as LOCAL time (this machine's timezone) since
    that's what a person typing a time actually means."""
    raw = raw.strip()
    m = re.fullmatch(r"\+(\d+)([mhd])", raw)
    if m:
        amount, unit = int(m.group(1)), m.group(2)
        delta = {
            "m": timedelta(minutes=amount),
            "h": timedelta(hours=amount),
            "d": timedelta(days=amount),
        }[unit]
        return now_utc + delta

    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        # naive input -> assume the machine's local timezone, then convert
        dt = dt.astimezone()
    return dt.astimezone(timezone.utc)


def add_to_queue(raw_times):
    """Parse a comma-separated list of time strings and append them to the
    schedule queue file as pending entries. Returns the list of newly added
    entries (each a dict with "fire_at" and "posted")."""
    now = datetime.now(timezone.utc)
    queue = load_queue()
    added = []
    for raw in raw_times.split(","):
        raw = raw.strip()
        if not raw:
            continue
        fire_at = parse_schedule_time(raw, now)
        entry = {"fire_at": fire_at.isoformat(), "posted": False, "posted_at": None}
        queue.append(entry)
        added.append(entry)
    queue.sort(key=lambda e: e["fire_at"])
    save_queue(queue)
    return added


def next_due_queue_entry(queue, now):
    """Return the earliest not-yet-posted queue entry whose fire_at has
    passed, or None. Only one is returned per call by design — if several
    are overdue at once (e.g. the machine was asleep), they're worked
    through one per invocation rather than fired in a burst."""
    due = [e for e in queue if not e.get("posted") and datetime.fromisoformat(e["fire_at"]) <= now]
    if not due:
        return None
    due.sort(key=lambda e: e["fire_at"])
    return due[0]


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


def pick_transcript(tweeted_ids, narrator_filter=None, random_pick=False):
    """Weighted pick among untweeted litterposting rants: usually the
    newest untweeted STRAY-narrated one, occasionally the newest untweeted
    one from a named Meowizen instead — falling back to whichever category
    actually has candidates if the preferred one is empty.

    If narrator_filter is given (e.g. "STRAY"), skip the weighting entirely
    and just consider posts from that exact narrator, or None if there
    isn't one.

    Normally the newest eligible candidate is returned. If random_pick is
    True, a random one among the eligible candidates is returned instead —
    handy for manually previewing a different post each time you rerun."""
    untweeted = [t for t in load_all_litterposting() if t["id"] not in tweeted_ids]
    if not untweeted:
        return None

    if narrator_filter:
        matches = [t for t in untweeted if (t.get("narrator") or "STRAY") == narrator_filter]
        if not matches:
            return None
        return random.choice(matches) if random_pick else matches[0]

    stray_posts = [t for t in untweeted if (t.get("narrator") or "STRAY") == "STRAY"]
    named_posts = [t for t in untweeted if (t.get("narrator") or "STRAY") != "STRAY"]

    prefer_stray = random.random() < STRAY_TWEET_WEIGHT
    primary, fallback = (stray_posts, named_posts) if prefer_stray else (named_posts, stray_posts)
    chosen = primary if primary else fallback
    if not chosen:
        return None
    return random.choice(chosen) if random_pick else chosen[0]


def build_tweet_text(transcript, full=False):
    """Concatenate the rant's spoken turns into one block of text.

    By default (full=False) this is cut down to the classic punchy
    MAX_TWEET_LEN (280 chars), preferring a clean sentence-boundary cut over
    a mid-sentence hard truncation — same behavior as before verification.

    If full=True, the cap is raised to EXTENDED_TWEET_LEN instead, so the
    whole rant posts essentially uncut (it'll still apply the same
    sentence-boundary-aware truncation logic in the rare case a rant somehow
    exceeds even that)."""
    limit = EXTENDED_TWEET_LEN if full else MAX_TWEET_LEN
    parts = [t["text"].strip() for t in transcript.get("turns", []) if t.get("actor") == "lm1"]
    full_text = re.sub(r"\s+", " ", " ".join(parts)).strip()

    if len(full_text) <= limit:
        return full_text

    best_cut = None
    for m in re.finditer(r"[.!?]\s", full_text):
        end = m.end()
        if end <= limit:
            best_cut = end
        else:
            break

    if best_cut and best_cut >= 40:
        return full_text[:best_cut].strip()

    truncated = full_text[:limit - 1].rsplit(" ", 1)[0]
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
    parser.add_argument("--now", action="store_true", help="ignore the hourly window and post immediately if there's something new")
    parser.add_argument("--narrator", help="force the pick to this exact narrator (e.g. STRAY) instead of the usual weighted pick; no-ops if nothing untweeted matches")
    parser.add_argument("--random", action="store_true", help="pick a random eligible candidate instead of always the newest one; combine with --dry-run to preview different options by rerunning")
    full_group = parser.add_mutually_exclusive_group()
    full_group.add_argument("--full", action="store_true", help="force this post to use the full rant (up to EXTENDED_TWEET_LEN) instead of rolling FULL_POST_PROBABILITY")
    full_group.add_argument("--short", action="store_true", help="force this post to use the classic punchy 280-char cut instead of rolling FULL_POST_PROBABILITY")
    parser.add_argument("--queue", help="comma-separated times to schedule future posts at: relative (+90m, +2h, +1d) or absolute local ISO datetime (2026-08-02T09:00); adds to the queue and exits without posting anything now")
    parser.add_argument("--list-queue", action="store_true", help="print all queued posts (pending and already-fired) and exit")
    parser.add_argument("--clear-queue", action="store_true", help="delete all pending queue entries and exit")
    parser.add_argument("--text", help="post this exact custom text as a tweet right now, bypassing the transcript pick and the time window entirely; combine with --dry-run to preview instead of posting")
    args = parser.parse_args()

    if args.whoami:
        ok = whoami()
        return 0 if ok else 1

    if args.text is not None:
        tweet_text = args.text.strip()
        print(f"Custom tweet ({len(tweet_text)} chars):\n{tweet_text}")
        if args.dry_run:
            print("\n[dry run — not posting, not updating state]")
            return 0
        result = post_tweet(tweet_text)
        tweet_id = result.get("data", {}).get("id")
        print(f"\nPosted. Tweet id: {tweet_id}")
        state = load_state()
        now = datetime.now(timezone.utc)
        state["last_tweeted_at"] = now.isoformat()
        schedule_next_window(state, now)
        save_state(state)
        return 0

    if args.queue:
        added = add_to_queue(args.queue)
        print(f"Queued {len(added)} post(s):")
        for e in added:
            print(f"  - {e['fire_at']}")
        print("\nThese will fire the next time this script runs (normally every ~15 min via launchd) at or after each time. Content is auto-picked at fire time, same as regular auto-posting.")
        return 0

    if args.list_queue:
        queue = load_queue()
        if not queue:
            print("Queue is empty.")
            return 0
        for e in sorted(queue, key=lambda x: x["fire_at"]):
            status = f"posted at {e['posted_at']}" if e.get("posted") else "pending"
            print(f"  {e['fire_at']}  [{status}]")
        return 0

    if args.clear_queue:
        n = len(load_queue())
        save_queue([])
        print(f"Cleared {n} queue entr{'y' if n == 1 else 'ies'}.")
        return 0

    state = load_state()
    now = datetime.now(timezone.utc)
    queue = load_queue()
    due_entry = next_due_queue_entry(queue, now)

    no_match_msg = (
        f"No untweeted litterposting transcripts found for narrator {args.narrator}."
        if args.narrator else
        "No untweeted litterposting transcripts found."
    )

    if args.full:
        use_full = True
    elif args.short:
        use_full = False
    else:
        use_full = random.random() < FULL_POST_PROBABILITY

    if args.dry_run:
        transcript = pick_transcript(state["tweeted_ids"], narrator_filter=args.narrator, random_pick=args.random)
        if transcript is None:
            print(no_match_msg)
            return 0
        tweet_text = build_tweet_text(transcript, full=use_full)
        print(f"Transcript: {transcript['id']} (narrator: {transcript.get('narrator') or 'STRAY'})")
        print(f"Mode: {'FULL POST' if use_full else 'short (280-char cut)'}")
        if due_entry:
            print(f"(a queued post from {due_entry['fire_at']} is currently due)")
        print(f"Tweet ({len(tweet_text)} chars):\n{tweet_text}")
        print("\n[dry run — not posting, not updating state, ignoring the hourly window]")
        return 0

    if not args.now and not due_entry:
        next_eligible_at = state.get("next_eligible_at")
        if next_eligible_at:
            next_eligible_dt = datetime.fromisoformat(next_eligible_at)
            if now < next_eligible_dt:
                print(f"Not yet — next posting window opens at {next_eligible_dt.isoformat()}. (use --now to skip this check)")
                return 0

    transcript = pick_transcript(state["tweeted_ids"], narrator_filter=args.narrator)
    if transcript is None:
        print(f"{no_match_msg} Trying again next window.")
        schedule_next_window(state, now)
        save_state(state)
        return 0

    tweet_text = build_tweet_text(transcript, full=use_full)
    print(f"Transcript: {transcript['id']} (narrator: {transcript.get('narrator') or 'STRAY'})")
    print(f"Mode: {'FULL POST' if use_full else 'short (280-char cut)'}")
    if due_entry:
        print(f"(firing queued post scheduled for {due_entry['fire_at']})")
    print(f"Tweet ({len(tweet_text)} chars):\n{tweet_text}")

    result = post_tweet(tweet_text)
    tweet_id = result.get("data", {}).get("id")
    print(f"\nPosted. Tweet id: {tweet_id}")

    state["tweeted_ids"].append(transcript["id"])
    state["last_tweeted_at"] = now.isoformat()
    schedule_next_window(state, now)
    save_state(state)

    if due_entry:
        due_entry["posted"] = True
        due_entry["posted_at"] = now.isoformat()
        save_queue(queue)

    return 0


if __name__ == "__main__":
    sys.exit(main())
