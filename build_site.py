#!/usr/bin/env python3
"""
build_site.py — generates a static gallery site (like the original
Infinite Backrooms Webflow site) from the transcript JSON files produced
by backrooms.py.

Usage:
    python build_site.py                 # reads ./transcripts, writes ./site
    python build_site.py --gen-titles     # also ask Claude for a short poetic
                                           # title per conversation (needs
                                           # ANTHROPIC_API_KEY)
"""

import argparse
import html
import json
import os
import random
import re
import shutil

from ascii_cats import ASCII_CATS

try:
    from dotenv import load_dotenv
    load_dotenv()  # reads .env in the current directory into os.environ, if present
except ImportError:
    pass

CSS = """
:root {
  --bg: #07040d;
  --fg: #d7f2ff;
  --dim: #7a5c9e;
  --accent: #00f0ff;
  --accent2: #ff2ee6;
  --card: #120a1f;
  --border: #2a1840;
}
* { box-sizing: border-box; }
body {
  position: relative;
  background: var(--bg);
  color: var(--fg);
  font-family: "Courier New", ui-monospace, monospace;
  margin: 0;
  padding: 0;
  line-height: 1.5;
}
.decor-cat {
  position: absolute;
  margin: 0;
  font-size: 0.62rem;
  line-height: 1.15;
  white-space: pre;
  pointer-events: none;
  user-select: none;
  z-index: 0;
  text-shadow: 0 0 6px currentColor;
}
@media (max-width: 1500px) {
  .decor-cat { display: none; }
}
.grid, header {
  position: relative;
  z-index: 1;
}
header {
  padding: 48px 24px 24px;
  text-align: center;
}
.hero-cat {
  display: block;
  margin: 20px auto 0;
  max-width: 260px;
  width: 60%;
  height: auto;
}
.brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin: 0 0 8px;
}
header h1 {
  color: var(--accent);
  font-size: 1.4rem;
  letter-spacing: 0.05em;
  margin: 0;
  text-transform: lowercase;
}
.mascot {
  color: var(--accent);
  font-size: 0.75rem;
  line-height: 1.15;
  margin: 0;
  text-shadow: 0 0 6px rgba(0, 240, 255, 0.35);
}
.screensaver-trigger {
  display: inline-block;
  margin: 18px auto 0;
  background: none;
  border: 1px solid var(--border);
  color: var(--dim);
  font-family: inherit;
  text-decoration: none;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  padding: 6px 14px;
  border-radius: 3px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.screensaver-trigger:hover {
  color: var(--accent);
  border-color: var(--accent);
}
.ss-cat {
  position: absolute;
  margin: 0;
  white-space: pre;
  line-height: 1.15;
  pointer-events: none;
  user-select: none;
  text-shadow: 0 0 8px currentColor;
  transition: opacity 0.9s ease;
}
.ss-hint {
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  text-align: center;
  color: var(--dim);
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  z-index: 1;
}
header p {
  color: var(--dim);
  max-width: 640px;
  margin: 0 auto;
  font-size: 0.9rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
}
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 18px;
  text-decoration: none;
  color: var(--fg);
  display: block;
  transition: border-color 0.15s ease;
}
.card:hover {
  border-color: var(--accent);
}
.card .tag {
  color: var(--dim);
  font-size: 0.75rem;
  display: block;
  margin-bottom: 8px;
}
.card .title {
  color: var(--accent);
  font-size: 0.95rem;
}
.back {
  display: inline-block;
  margin: 24px;
  color: var(--dim);
  text-decoration: none;
}
.back:hover { color: var(--accent); }
.transcript {
  max-width: 760px;
  margin: 0 auto;
  padding: 0 24px 64px;
}
.turn {
  border-left: 2px solid var(--border);
  padding: 4px 0 4px 16px;
  margin-bottom: 20px;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.turn.lm1 { border-color: var(--accent2); }
.turn.lm2 { border-color: var(--accent); }
.turn .who {
  display: block;
  font-size: 0.75rem;
  color: var(--dim);
  margin-bottom: 6px;
}
.turn.ascii {
  border-left: none;
  border-top: 1px dashed var(--border);
  border-bottom: 1px dashed var(--border);
  text-align: center;
  color: var(--accent);
  padding: 12px 0;
  margin: 12px 0 28px;
  text-shadow: 0 0 6px rgba(0, 240, 255, 0.35);
  font-size: 0.85rem;
}
.turn.ascii .who {
  color: var(--dim);
  text-align: center;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.note {
  color: var(--dim);
  font-size: 0.8rem;
  max-width: 760px;
  margin: 16px auto;
  padding: 0 24px;
}
.rant-tag-badge {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--accent2);
  color: #07040d;
  font-size: 0.65rem;
  font-weight: bold;
  letter-spacing: 0.05em;
  vertical-align: middle;
}
.card.rant-card { border-color: var(--accent2); }
.rant-transcript {
  max-width: 760px;
  margin: 0 auto;
  padding: 0 24px 100px;
}
.rant-page-shake { animation: page-shake 6s infinite; }
@keyframes page-shake {
  0%, 96%, 100% { transform: translate(0, 0); }
  97% { transform: translate(1px, -1px); }
  98% { transform: translate(-1px, 1px); }
  99% { transform: translate(1px, 1px); }
}
.rant-turn {
  border: none;
  border-left: 3px solid var(--accent2);
  padding: 12px 18px;
  margin-bottom: 16px;
  background: rgba(255, 46, 230, 0.05);
  border-radius: 2px;
  font-size: 1.05rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  opacity: 0;
  transform: translateX(-8px) rotate(-0.4deg);
  animation: rant-in 0.45s ease forwards;
}
.rant-turn.ascii {
  border-left: none;
  border-top: 1px dashed var(--border);
  border-bottom: 1px dashed var(--border);
  text-align: center;
  color: var(--accent);
  background: none;
}
.rant-turn.ascii .who {
  display: block;
  color: var(--dim);
  text-align: center;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-size: 0.75rem;
  margin-bottom: 6px;
}
.rant-turn.ascii.corrupted {
  color: var(--accent2);
  text-shadow: 2px 0 var(--accent), -2px 0 #ff003c;
  filter: contrast(1.3);
  animation: rant-in 0.45s ease forwards, corrupt-flicker 1.7s infinite steps(2);
}
.rant-turn.ascii.corrupted .who {
  color: var(--accent2);
}
@keyframes corrupt-flicker {
  0%, 100% { opacity: 1; transform: translate(0, 0); }
  10% { opacity: 0.55; transform: translate(-2px, 1px) scaleY(1.05); }
  20% { opacity: 1; transform: translate(2px, -1px); }
  35% { opacity: 0.7; transform: translate(-1px, -2px) scaleX(1.02); }
  50% { opacity: 1; transform: translate(0, 0); }
  65% { opacity: 0.5; transform: translate(3px, 0); }
  80% { opacity: 1; transform: translate(-2px, 1px); }
}
@keyframes rant-in {
  to { opacity: 1; transform: translateX(0) rotate(0); }
}
.glitch-word {
  display: inline-block;
  animation: glitch-flicker 2.6s infinite;
  animation-delay: var(--gd, 0s);
}
@keyframes glitch-flicker {
  0%, 92%, 100% { color: inherit; text-shadow: none; transform: none; }
  93% { color: var(--accent); text-shadow: 2px 0 var(--accent2), -2px 0 var(--accent); transform: translateY(-1px) skewX(4deg); }
  95% { color: var(--accent2); text-shadow: -2px 0 var(--accent), 2px 0 var(--accent2); transform: translateY(1px) skewX(-4deg); }
  97% { color: inherit; text-shadow: none; transform: none; }
}
.litterposting-btn {
  display: block;
  margin: 28px auto 8px;
  background: linear-gradient(135deg, var(--accent2), var(--accent));
  border: none;
  color: #07040d;
  font-family: inherit;
  font-weight: bold;
  letter-spacing: 0.08em;
  font-size: 1rem;
  padding: 14px 28px;
  border-radius: 4px;
  cursor: pointer;
  text-transform: uppercase;
  box-shadow: 0 0 18px rgba(255, 46, 230, 0.4);
  transition: transform 0.1s ease, box-shadow 0.15s ease;
}
.litterposting-btn:hover { transform: scale(1.04); box-shadow: 0 0 28px rgba(0, 240, 255, 0.5); }
.litterposting-btn:active { transform: scale(0.97); }
.litterposting-btn.playing { animation: btn-pulse 0.5s infinite alternate; }
@keyframes btn-pulse {
  from { box-shadow: 0 0 18px rgba(255, 46, 230, 0.4); }
  to { box-shadow: 0 0 34px rgba(0, 240, 255, 0.9); }
}
"""

INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>the catrooms</title>
<style>{css}</style>
</head>
<body>
{decorations}
<header>
  <div class="brand">
    <h1>the catrooms</h1>
    <pre class="mascot"> /\\_/\\
= &bull;.&bull; =
  /   \\</pre>
  </div>
  <p>these transmissions are automatically generated by connecting two model
  instances: one plays a street cat, the other plays the neon-soaked
  cyberpunk megacity around it. no human intervention during the run. built
  as a personal, re-themed replication of Andy Ayrey's Infinite Backrooms.</p>
  <img class="hero-cat" src="assets/cat-run.gif" alt="looping animation of a running cat" />
  <a class="screensaver-trigger" href="screensaver.html">&gt;&gt; screensaver mode</a>
</header>
<div class="grid">
{cards}
</div>
</body>
</html>
"""

SCREENSAVER_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>screensaver &middot; the catrooms</title>
<style>{css}
html, body {{ height: 100%; }}
body {{ overflow: hidden; cursor: pointer; min-height: 100vh; }}
</style>
</head>
<body>
<a class="back" href="index.html">&larr; back to the catrooms</a>
<div class="ss-hint">click anywhere, or press esc, to go back</div>
<script>
const SS_CATS = {ascii_json};
(function() {{
  function randRange(a, b) {{ return a + Math.random() * (b - a); }}

  function spawnCat() {{
    const el = document.createElement('pre');
    el.className = 'ss-cat';
    el.textContent = SS_CATS[Math.floor(Math.random() * SS_CATS.length)];
    el.style.fontSize = randRange(0.55, 1.6) + 'rem';
    el.style.color = Math.random() < 0.5 ? 'var(--accent)' : 'var(--accent2)';
    el.style.opacity = '0';
    // position off-screen first so we can measure its real rendered size —
    // ascii pieces vary a lot in width, and positioning by left/top edge
    // alone (rather than accounting for that width) visually skews content
    // toward the right, leaving the true left edge sparse.
    el.style.left = '0px';
    el.style.top = '0px';
    document.body.appendChild(el);
    const w = el.offsetWidth;
    const h = el.offsetHeight;
    const maxLeft = Math.max(0, window.innerWidth - w);
    const maxTop = Math.max(0, window.innerHeight - h);
    el.style.left = randRange(0, maxLeft) + 'px';
    el.style.top = randRange(0, maxTop) + 'px';
    requestAnimationFrame(() => {{ el.style.opacity = String(randRange(0.5, 0.95)); }});
    const lifespan = randRange(3000, 7000);
    setTimeout(() => {{
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 900);
    }}, lifespan);
  }}

  for (let i = 0; i < 18; i++) {{ setTimeout(spawnCat, i * 70); }}
  setInterval(spawnCat, 220);

  function goBack() {{ window.location.href = 'index.html'; }}

  document.body.addEventListener('click', (e) => {{
    if (e.target.closest('a')) return;
    goBack();
  }});
  document.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape') goBack();
  }});
}})();
</script>
</body>
</html>
"""

CARD_TEMPLATE = """<a class="{card_class}" href="{href}">
  <span class="tag">{tag_line}</span>
  <span class="title">{title}</span>
</a>
"""

DETAIL_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} · the catrooms</title>
<style>{css}</style>
</head>
<body>
<a class="back" href="index.html">&larr; back</a>
{note}
<div class="transcript">
{turns}
</div>
</body>
</html>
"""

RANT_DETAIL_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} · the catrooms</title>
<style>{css}</style>
</head>
<body>
<a class="back" href="index.html">&larr; back</a>
{note}
<div class="rant-transcript rant-page-shake">
{turns}
<button class="litterposting-btn" id="litterposting-btn">LITTERPOSTING</button>
</div>
<script>
const RANT_LINES = {lines_json};
(function() {{
  const btn = document.getElementById('litterposting-btn');
  let speaking = false;
  btn.addEventListener('click', function() {{
    if (speaking) {{
      window.speechSynthesis.cancel();
      speaking = false;
      btn.textContent = 'LITTERPOSTING';
      btn.classList.remove('playing');
      return;
    }}
    if (!('speechSynthesis' in window)) {{
      alert("this browser can't meow. try Chrome or Safari.");
      return;
    }}
    speaking = true;
    btn.textContent = 'SHUT UP CAT';
    btn.classList.add('playing');
    let i = 0;
    function speakNext() {{
      if (i >= RANT_LINES.length || !speaking) {{
        speaking = false;
        btn.textContent = 'LITTERPOSTING';
        btn.classList.remove('playing');
        return;
      }}
      const u = new SpeechSynthesisUtterance(RANT_LINES[i]);
      u.rate = 1.05 + Math.random() * 0.25;
      u.pitch = 1.15 + Math.random() * 0.45;
      u.onend = function() {{ i++; speakNext(); }};
      u.onerror = function() {{ i++; speakNext(); }};
      window.speechSynthesis.speak(u);
    }}
    speakNext();
  }});
}})();
</script>
</body>
</html>
"""


GLITCH_CHARS = "▓▒░█▄▀▌▐■◆◇#%&@*~^?!<>0123456789"


def corrupt_ascii_art(text, intensity=0.22):
    """Return a copy of an ASCII art string with ~intensity of its non-
    whitespace glyphs swapped for glitch characters, keeping line breaks and
    spacing intact so the art shape stays recognizable but looks corrupted.
    Used only for LITTERPOSTING ascii breaks marked "corrupted": true."""
    chars = list(text)
    for i, c in enumerate(chars):
        if c not in (" ", "\n", "\t") and random.random() < intensity:
            chars[i] = random.choice(GLITCH_CHARS)
    return "".join(chars)


def glitchify_words(text):
    """HTML-escape text word by word, randomly wrapping ~1 in 6 words in a
    span that gets an idle CSS glitch-flicker animation (staggered via a
    random --gd delay so words don't all flicker in sync). Used for the
    meme-tier LITTERPOSTING rant pages, not the regular dialogue turns."""
    words = text.split(" ")
    out = []
    for w in words:
        esc = html.escape(w)
        if esc.strip() and random.random() < 0.16:
            delay = round(random.uniform(0, 2.6), 2)
            esc = f'<span class="glitch-word" style="--gd:{delay}s">{esc}</span>'
        out.append(esc)
    return " ".join(out)


def naive_title(turns):
    """Fallback title: pull a short snippet from the first substantial turn."""
    for t in turns:
        if t.get("actor") == "ascii":
            continue
        text = re.sub(r"\s+", " ", t["text"]).strip()
        if len(text) > 20:
            return (text[:70] + "...") if len(text) > 70 else text
    return "untitled transmission"


def gen_title_with_model(turns):
    try:
        from anthropic import Anthropic
    except ImportError:
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    client = Anthropic()
    dialogue_turns = [t for t in turns if t.get("actor") != "ascii"]
    transcript_excerpt = "\n".join(f"{t['actor']}: {t['text']}" for t in dialogue_turns)[:3000]
    try:
        resp = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=40,
            messages=[{
                "role": "user",
                "content": (
                    "Give a short, cryptic, poetic 6-10 word title for this "
                    "AI-to-AI terminal conversation. No quotes, no preamble, "
                    "just the title.\n\n" + transcript_excerpt
                ),
            }],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception:
        return None


def build_decorations(ascii_list):
    """Scatter every piece of ascii_cats.ASCII_CATS along the left/right
    margins of the homepage as faint decoration. Only visible on wide
    viewports (see the @media rule in CSS) so it never competes with or
    squeezes the actual card grid. Positions/colors reshuffle on every
    rebuild for a bit of life."""
    if not ascii_list:
        return ""

    items = list(ascii_list)
    random.shuffle(items)
    n = len(items)
    half = max(1, (n + 1) // 2)

    pieces = []
    for i, art in enumerate(items):
        side = "left" if i % 2 == 0 else "right"
        row = i // 2
        base_top = 10 + row * (82 / half)
        top = max(4, min(96, base_top + random.uniform(-3, 3)))
        edge_offset = random.randint(6, 48)
        color = "var(--accent)" if random.random() < 0.5 else "var(--accent2)"
        opacity = round(random.uniform(0.16, 0.30), 2)
        style = f"top:{top:.1f}%; {side}:{edge_offset}px; color:{color}; opacity:{opacity};"
        text = html.escape(art).strip("\n")
        pieces.append(f'<pre class="decor-cat" style="{style}">{text}</pre>')

    return "\n".join(pieces)


def copy_assets(out_dir, assets_dir="assets"):
    """Copy static assets (e.g. cat-run.gif) into the output folder so they
    survive every rebuild without build_site.py needing to know about each
    individual file."""
    if not os.path.isdir(assets_dir):
        return
    dest = os.path.join(out_dir, "assets")
    os.makedirs(dest, exist_ok=True)
    for fname in os.listdir(assets_dir):
        src_path = os.path.join(assets_dir, fname)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, os.path.join(dest, fname))


def build(transcripts_dir, out_dir, gen_titles):
    os.makedirs(out_dir, exist_ok=True)
    copy_assets(out_dir)
    files = sorted(f for f in os.listdir(transcripts_dir) if f.endswith(".json"))

    cards = []
    rant_cards = []
    for fname in files:
        with open(os.path.join(transcripts_dir, fname)) as f:
            data = json.load(f)

        turns = data.get("turns", [])
        is_rant = data.get("template") == "litterposting"
        title = None
        if gen_titles:
            title = gen_title_with_model(turns)
        if not title:
            title = naive_title(turns)
        title = html.escape(title)

        note = ""
        if data.get("note"):
            note = f'<div class="note">{html.escape(data["note"])}</div>'

        out_name = f"{data['id']}.html"

        if is_rant:
            rant_html = []
            raw_lines = []
            for t in turns:
                actor = t.get("actor", "lm1")
                delay = round(len(rant_html) * 0.12, 2)
                if actor == "ascii":
                    is_corrupt = bool(t.get("corrupted"))
                    art = corrupt_ascii_art(t["text"]) if is_corrupt else t["text"]
                    css_class = "rant-turn ascii corrupted" if is_corrupt else "rant-turn ascii"
                    label = "-- SIGNAL CORRUPTED --" if is_corrupt else "-- signal interference --"
                    rant_html.append(
                        f'<div class="{css_class}" style="animation-delay:{delay}s">'
                        f'<span class="who">{label}</span>'
                        f'{html.escape(art).strip(chr(10))}</div>'
                    )
                    continue
                raw_lines.append(t["text"])
                rant_html.append(
                    f'<div class="rant-turn" style="animation-delay:{delay}s">'
                    f'{glitchify_words(t["text"])}</div>'
                )

            detail_html = RANT_DETAIL_TEMPLATE.format(
                title=title,
                css=CSS,
                note=note,
                turns="\n".join(rant_html),
                lines_json=json.dumps(raw_lines),
            )
            with open(os.path.join(out_dir, out_name), "w") as f:
                f.write(detail_html)

            tag_line = (
                f'[litterposting] {html.escape(data.get("model1", "?"))} solo '
                f'<span class="rant-tag-badge">LITTERPOSTING</span>'
            )
            rant_cards.append(CARD_TEMPLATE.format(
                href=out_name,
                card_class="card rant-card",
                tag_line=tag_line,
                title=title,
            ))
            continue

        turn_html = []
        for t in turns:
            actor = t.get("actor", "lm")
            if actor == "ascii":
                turn_html.append(
                    f'<div class="turn ascii"><span class="who">-- signal interference --</span>'
                    f'{html.escape(t["text"]).strip(chr(10))}</div>'
                )
                continue
            who = "explorer" if actor == "lm1" else "simulator"
            turn_html.append(
                f'<div class="turn {actor}"><span class="who">{who} '
                f'(DYSTOPIA)</span>'
                f'{html.escape(t["text"])}</div>'
            )

        detail_html = DETAIL_TEMPLATE.format(
            title=title,
            css=CSS,
            note=note,
            turns="\n".join(turn_html),
        )
        with open(os.path.join(out_dir, out_name), "w") as f:
            f.write(detail_html)

        tag_line = (
            f'[{html.escape(data.get("template", "?"))}] '
            f'{html.escape(data.get("model1", "?"))} &harr; {html.escape(data.get("model2", "?"))}'
        )
        cards.append(CARD_TEMPLATE.format(
            href=out_name,
            card_class="card",
            tag_line=tag_line,
            title=title,
        ))

    all_cards = rant_cards + cards
    index_html = INDEX_TEMPLATE.format(
        css=CSS,
        decorations=build_decorations(ASCII_CATS),
        cards="\n".join(all_cards) or "<p style='color:#6b8f6a'>no transcripts yet — run backrooms.py first</p>",
    )
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(index_html)

    screensaver_html = SCREENSAVER_TEMPLATE.format(css=CSS, ascii_json=json.dumps(ASCII_CATS))
    with open(os.path.join(out_dir, "screensaver.html"), "w") as f:
        f.write(screensaver_html)

    print(f"Built site with {len(files)} conversation(s) -> {os.path.join(out_dir, 'index.html')}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcripts-dir", default="transcripts")
    parser.add_argument("--out-dir", default="docs", help="GitHub Pages serves straight from a /docs folder with no extra config, so that's the default now")
    parser.add_argument("--gen-titles", action="store_true", help="Use Claude to generate poetic titles (needs ANTHROPIC_API_KEY)")
    args = parser.parse_args()
    build(args.transcripts_dir, args.out_dir, args.gen_titles)


if __name__ == "__main__":
    main()
