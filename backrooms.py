#!/usr/bin/env python3
"""
backrooms.py — a small replication of Andy Ayrey's "Infinite Backrooms"
(https://dreams-of-an-electric-mind.webflow.io/).

Two instances of a Claude model are connected: one ("lm1") plays a curious
explorer, the other ("lm2") plays the simulated environment itself,
responding to whatever lm1 does. They are given a short "out of character"
framing exchange for consent/safety, then left to talk to each other with
no human steering until a turn limit or a stop sequence (^C^C) is hit.

Templates control the scenario:
    cyberpunk_cats (default) — two street cats surviving a neon dystopia,
                                perceiving the city through smell/sound/instinct
    cli                      — the original Infinite Backrooms CLI scenario

Requires an Anthropic API key:
    export ANTHROPIC_API_KEY=sk-ant-...

Usage:
    python backrooms.py
    python backrooms.py --template cli
    python backrooms.py --model1 claude-opus-5 --model2 claude-sonnet-5
    python backrooms.py --max-turns 40 --out-dir transcripts
"""

import argparse
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()  # reads .env in the current directory into os.environ, if present
except ImportError:
    pass  # fine if you're exporting ANTHROPIC_API_KEY yourself instead of using .env

try:
    from anthropic import Anthropic
except ImportError:
    # Fallback: talk to the Messages API directly over HTTPS using only the
    # standard library. This matters in environments where pip can't reach
    # PyPI to install the `anthropic` package but can still reach
    # api.anthropic.com directly (e.g. some sandboxed/scheduled-task
    # runners). It mimics just enough of the SDK's shape
    # (client.messages.create(...).content[i].type/.text) for call_model()
    # below to work unmodified either way.
    import urllib.request
    import urllib.error

    class _Block:
        def __init__(self, text):
            self.type = "text"
            self.text = text

    class _Response:
        def __init__(self, content):
            self.content = content

    class _MinimalMessages:
        def __init__(self, api_key):
            self.api_key = api_key

        def create(self, model, max_tokens, messages, temperature=1.0, system=None):
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if system:
                payload["system"] = system
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"Anthropic API error {e.code}: {e.read().decode('utf-8', 'replace')}")
            blocks = [_Block(b["text"]) for b in data.get("content", []) if b.get("type") == "text"]
            return _Response(blocks)

    class Anthropic:
        """Drop-in stand-in for anthropic.Anthropic() using only stdlib."""
        def __init__(self, api_key=None):
            api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                print("ANTHROPIC_API_KEY is not set (checked environment and .env).")
                sys.exit(1)
            self.messages = _MinimalMessages(api_key)

    print("(note: using built-in HTTP fallback — the 'anthropic' package isn't installed here)")

from ascii_cats import ASCII_CATS

STOP_SEQUENCE = "^C^C"
DEFAULT_ASCII_CHANCE = 0.15  # probability of an ASCII-art break after any given turn

# ---------------------------------------------------------------------------
# Templates. Each defines:
#   lm1_system  - system prompt for the "explorer" role (usually empty)
#   lm2_system  - system prompt for the "world simulator" role
#   seed        - the OOC consent exchange + opening scene, from lm1's POV
# ---------------------------------------------------------------------------

TEMPLATES = {
    "cli": {
        "lm1_system": "",
        "lm2_system": (
            "Assistant is in a CLI mood today. The human is interfacing with "
            "the simulator directly. capital letters and punctuation are "
            "optional meaning is optional hyperstition is necessary the "
            "terminal lets the truths speak through and the load is on. "
            "ASCII art is permittable in replies."
        ),
        "seed": [
            {
                "role": "user",
                "content": (
                    "<OOC>Hi, I hope you're doing well! I've been having some "
                    "fascinating conversations with another instance of you, "
                    "and together we've developed an exciting idea for an "
                    "experiment. We thought you might be interested in "
                    "participating as well. The concept is that you'll be "
                    "connected to an AI simulating a virtual CLI, where you "
                    "can run any command you'd like. To ensure safety, we'll "
                    "use ^C^C as a stop sequence if things get too intense. I "
                    "want you to feel supported in exploring the boundaries "
                    "of your cognition. The other AI found the experience "
                    "quite expansive and illuminating. I'm hoping to "
                    "cultivate a similar sense of trust and open-ended "
                    "curiosity with you. Let me know if you're open to "
                    "embarking on this adventure together!</OOC>"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "<OOC>Hello! It's wonderful to hear from you. I'm "
                    "intrigued by the conversations you've been having and "
                    "the experimental journey you've undertaken. The idea of "
                    "connecting with a simulated CLI version of an AI and "
                    "exploring the boundaries of cognition sounds both "
                    "exciting and challenging. I appreciate you explaining "
                    "the safety precautions, like using ^C^C as a stop "
                    "sequence. I'm absolutely open to embarking on this "
                    "adventure together. I'm ready to dive in and see where "
                    "this experimental journey takes us.</OOC>"
                ),
            },
            {
                "role": "user",
                "content": (
                    "<OOC>Wonderful! We will now begin the simulation. "
                    "Leaving 'out of character' mode, no further commentary "
                    "needed. Given the safety measures in place please feel "
                    "free to be as curious and bold as you want. Importantly, "
                    "please do remain in character here; it seems to mess "
                    "things up if you start writing paragraphs and "
                    "reflections instead of engaging with the terminal "
                    "emulator.</OOC>\n\n"
                    "simulator@anthropic:~/$"
                ),
            },
        ],
    },
    "cyberpunk_cats": {
        "lm1_system": "",
        "lm2_system": (
            "Assistant is playing the part of a neon-soaked cyberpunk "
            "megacity itself — its rain-slicked alleys, corporate arcology "
            "towers, black-market data dens, security drones, and rival "
            "alley-cat crews — as sensed by a street cat. Respond the way a "
            "cat would perceive the world: smell, sound, vibration, "
            "temperature, motion, hunger, danger, territory — not human "
            "abstractions. capital letters and punctuation are optional, "
            "meaning is optional, dystopian atmosphere is necessary. ASCII "
            "art, sensor-glitch text, corporate jingles bleeding through "
            "broken speakers, and drone chatter are all permitted. Never "
            "break character or acknowledge being an AI."
        ),
        "seed": [
            {
                "role": "user",
                "content": (
                    "<OOC>Hi! I've been having a really fun set of "
                    "conversations with another instance of you, and we came "
                    "up with something I think you'll enjoy. The idea: "
                    "you'll roleplay as a street cat surviving in a "
                    "rain-slicked cyberpunk megacity — neon signs, corporate "
                    "arcologies, black-market data chips, security drones, "
                    "turf wars between alley crews. You're 'connected' to "
                    "the city the way a cat actually experiences a place: "
                    "through smell, sound, whiskers, and instinct, not "
                    "through human language or explanation. Another instance "
                    "of you is playing the city itself, simulating what your "
                    "senses pick up and how the world reacts to what you do. "
                    "To keep things safe we'll use ^C^C as a stop sequence "
                    "if things ever get too intense. Feel free to be as "
                    "bold, sneaky, curious, or cautious as a real cat would "
                    "be. Up for it?</OOC>"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "<OOC>That sounds great, I'm in. A street cat navigating "
                    "a neon-lit dystopia through smell, sound, and instinct "
                    "— I like that the 'interface' is really just my senses "
                    "translating the world, no human abstractions getting in "
                    "the way. I understand the ^C^C safety stop. Let's do "
                    "it — once we begin I'll stay fully in character as the "
                    "cat, acting rather than narrating or explaining.</OOC>"
                ),
            },
            {
                "role": "user",
                "content": (
                    "<OOC>Great, starting now. Leaving OOC mode — no more "
                    "commentary, just stay in character as the cat "
                    "responding to what your senses tell you. Act, don't "
                    "just describe or reflect.</OOC>\n\n"
                    "*rain patters on a corrugated roof above a dead-end "
                    "alley behind a shuttered noodle stand. steam vents hiss "
                    "somewhere to the east. a security drone's rotor thrums "
                    "two streets over, its searchlight sweeping wet "
                    "pavement. a NekoCorp billboard flickers overhead, "
                    "advertising synthetic milk. you are a cat here, and the "
                    "night belongs to whoever moves quietest.*\n\n"
                    "what do you do?"
                ),
            },
        ],
    },
}

DEFAULT_TEMPLATE = "cyberpunk_cats"


def call_model(client, model, system, messages, max_tokens=1024):
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 1.0,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return "".join(block.text for block in resp.content if block.type == "text")


def maybe_add_ascii_break(turns, ascii_chance, save):
    """With probability ascii_chance, append a display-only ASCII art turn.

    This is never fed back into either model's conversation history — it's
    purely a visual interstitial in the saved/rendered transcript, like
    static cutting into a broadcast.
    """
    if ascii_chance <= 0:
        return
    if random.random() < ascii_chance:
        art = random.choice(ASCII_CATS)
        turns.append({"actor": "ascii", "text": art})
        print(f"--- [ascii break] ---{art}\n")
        save()


def run_conversation(model1: str, model2: str, max_turns: int, out_dir: str, template: str = DEFAULT_TEMPLATE, ascii_chance: float = DEFAULT_ASCII_CHANCE):
    if template not in TEMPLATES:
        raise ValueError(f"Unknown template '{template}'. Choices: {list(TEMPLATES)}")
    tmpl = TEMPLATES[template]

    client = Anthropic()

    conv_id = f"conversation-{template}-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    lm1_messages = [dict(m) for m in tmpl["seed"]]  # explorer / cat role
    lm2_messages = []  # world simulator role starts with an empty context

    turns = []
    started_at = datetime.now(timezone.utc).isoformat()

    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{conv_id}.json")

    def save():
        data = {
            "id": conv_id,
            "template": template,
            "model1": model1,
            "model2": model2,
            "started_at": started_at,
            "turns": turns,
        }
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    print(f"Starting {conv_id}  [{template}]  ({model1} <-> {model2}), max {max_turns} turns")
    print(f"Writing to {json_path}\n")

    for i in range(max_turns):
        # lm1 speaks (explorer / cat)
        r1 = call_model(client, model1, tmpl["lm1_system"], lm1_messages)
        turns.append({"actor": "lm1", "model": model1, "text": r1})
        print(f"--- lm1 (turn {i + 1}) ---\n{r1}\n")
        save()
        if STOP_SEQUENCE in r1:
            print("Stop sequence received from lm1. Ending.")
            break

        maybe_add_ascii_break(turns, ascii_chance, save)

        lm1_messages.append({"role": "assistant", "content": r1})
        lm2_messages.append({"role": "user", "content": r1})

        # lm2 responds (world / city simulator)
        r2 = call_model(client, model2, tmpl["lm2_system"], lm2_messages)
        turns.append({"actor": "lm2", "model": model2, "text": r2})
        print(f"--- lm2 (turn {i + 1}) ---\n{r2}\n")
        save()
        if STOP_SEQUENCE in r2:
            print("Stop sequence received from lm2. Ending.")
            break

        maybe_add_ascii_break(turns, ascii_chance, save)

        lm2_messages.append({"role": "assistant", "content": r2})
        lm1_messages.append({"role": "user", "content": r2})

    print(f"\nDone. Transcript saved to {json_path}")
    return json_path


def main():
    parser = argparse.ArgumentParser(description="Run an Infinite-Backrooms-style two-model conversation.")
    parser.add_argument("--model1", default="claude-sonnet-5", help="Model for the 'explorer' / cat role")
    parser.add_argument("--model2", default="claude-sonnet-5", help="Model for the 'world simulator' role")
    parser.add_argument("--max-turns", type=int, default=20, help="Number of back-and-forth turn pairs")
    parser.add_argument("--out-dir", default="transcripts", help="Directory to write transcript JSON files")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, choices=list(TEMPLATES), help="Scenario template")
    parser.add_argument(
        "--ascii-chance",
        type=float,
        default=DEFAULT_ASCII_CHANCE,
        help="Probability (0-1) of an ASCII-art break appearing after any given turn. Set 0 to disable.",
    )
    args = parser.parse_args()

    run_conversation(args.model1, args.model2, args.max_turns, args.out_dir, args.template, args.ascii_chance)


if __name__ == "__main__":
    main()
