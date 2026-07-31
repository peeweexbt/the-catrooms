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
from datetime import datetime, timezone

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
  scrollbar-width: auto;
  scrollbar-color: rgba(255, 46, 230, 0.45) rgba(18, 10, 31, 0.4);
}
/* custom scrollbar — chunky beveled Y2K-OS chrome in the site's neon
   palette, kept fairly translucent so it reads as an overlay rather than a
   solid panel. Firefox only supports the two-color scrollbar-color rule
   above; Chrome/Safari/Edge get the full retro treatment below. */
::-webkit-scrollbar {
  width: 18px;
  height: 18px;
}
::-webkit-scrollbar-track {
  background: linear-gradient(180deg, rgba(13, 7, 22, 0.45), rgba(7, 4, 13, 0.45));
  border-left: 1px solid rgba(42, 24, 64, 0.5);
  box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.4);
}
::-webkit-scrollbar-thumb {
  background-color: rgba(255, 46, 230, 0.18);
  background-image:
    repeating-linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.08) 0px,
      rgba(255, 255, 255, 0.08) 2px,
      transparent 2px,
      transparent 6px
    ),
    linear-gradient(180deg, rgba(255, 46, 230, 0.18) 0%, rgba(0, 240, 255, 0.18) 100%);
  border-style: solid;
  border-width: 2px;
  border-top-color: rgba(255, 255, 255, 0.18);
  border-left-color: rgba(255, 255, 255, 0.18);
  border-bottom-color: rgba(0, 0, 0, 0.25);
  border-right-color: rgba(0, 0, 0, 0.25);
  box-shadow: 0 0 5px rgba(255, 46, 230, 0.25), 0 0 2px rgba(0, 240, 255, 0.25);
}
::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 46, 230, 0.32);
  background-image:
    repeating-linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.1) 0px,
      rgba(255, 255, 255, 0.1) 2px,
      transparent 2px,
      transparent 6px
    ),
    linear-gradient(180deg, rgba(255, 46, 230, 0.32) 0%, rgba(0, 240, 255, 0.32) 100%);
  box-shadow: 0 0 8px rgba(255, 46, 230, 0.35), 0 0 3px rgba(0, 240, 255, 0.35);
}
::-webkit-scrollbar-thumb:active {
  background-color: rgba(0, 240, 255, 0.4);
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.45), inset 0 0 6px rgba(0, 0, 0, 0.2);
}
::-webkit-scrollbar-button {
  display: block;
  height: 16px;
  background-color: rgba(18, 10, 31, 0.35);
  border-style: solid;
  border-width: 2px;
  border-top-color: rgba(255, 255, 255, 0.2);
  border-left-color: rgba(255, 255, 255, 0.2);
  border-bottom-color: rgba(0, 0, 0, 0.4);
  border-right-color: rgba(0, 0, 0, 0.4);
  background-position: center;
  background-repeat: no-repeat;
  background-size: 8px 8px;
}
::-webkit-scrollbar-button:hover {
  background-color: rgba(26, 15, 46, 0.55);
}
::-webkit-scrollbar-button:vertical:decrement {
  background-image: linear-gradient(135deg, transparent 48%, rgba(0, 240, 255, 0.7) 48%, rgba(0, 240, 255, 0.7) 52%, transparent 52%),
    linear-gradient(45deg, transparent 48%, rgba(0, 240, 255, 0.7) 48%, rgba(0, 240, 255, 0.7) 52%, transparent 52%);
}
::-webkit-scrollbar-button:vertical:increment {
  background-image: linear-gradient(-135deg, transparent 48%, rgba(255, 46, 230, 0.7) 48%, rgba(255, 46, 230, 0.7) 52%, transparent 52%),
    linear-gradient(-45deg, transparent 48%, rgba(255, 46, 230, 0.7) 48%, rgba(255, 46, 230, 0.7) 52%, transparent 52%);
}
::-webkit-scrollbar-corner {
  background: rgba(7, 4, 13, 0.4);
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
.decor-cat.glitching {
  animation-name: decor-cat-glitch;
  animation-duration: 3.4s;
  animation-iteration-count: infinite;
}
@keyframes decor-cat-glitch {
  0%, 88%, 100% { transform: translate(0, 0) skew(0deg); filter: none; }
  89% { transform: translate(-3px, 2px) skew(4deg); filter: hue-rotate(30deg) saturate(1.6); }
  91% { transform: translate(3px, -2px) skew(-4deg); filter: hue-rotate(-30deg) saturate(1.6); }
  93% { transform: translate(-1px, 1px); filter: none; }
  95%, 100% { transform: translate(0, 0); filter: none; }
}
@media (max-width: 900px) {
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
  color: var(--fg);
  font-family: inherit;
  text-decoration: none;
  font-size: 0.88rem;
  letter-spacing: 0.05em;
  padding: 9px 18px;
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
@media (max-width: 400px) {
  .grid {
    grid-template-columns: 1fr;
    padding: 20px 14px;
    gap: 12px;
  }
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
.narrator-badge {
  max-width: 760px;
  margin: 16px auto 0;
  padding: 0 24px;
  color: var(--dim);
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}
.narrator-badge strong {
  color: var(--accent2);
}
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
  background: transparent;
  border: 1px solid var(--accent2);
  color: var(--accent2);
  font-family: inherit;
  font-weight: bold;
  letter-spacing: 0.12em;
  font-size: 1rem;
  padding: 12px 26px;
  border-radius: 2px;
  cursor: pointer;
  text-transform: uppercase;
  text-shadow: 0 0 4px var(--accent2), 0 0 10px var(--accent2), 0 0 22px rgba(255, 46, 230, 0.6);
  box-shadow: 0 0 8px rgba(255, 46, 230, 0.35), inset 0 0 8px rgba(255, 46, 230, 0.12);
  transition: color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, text-shadow 0.15s ease;
}
.litterposting-btn::before { content: "[ "; }
.litterposting-btn::after { content: " ]"; }
.litterposting-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
  text-shadow: 0 0 6px var(--accent), 0 0 14px var(--accent), 0 0 28px rgba(0, 240, 255, 0.7);
  box-shadow: 0 0 14px rgba(0, 240, 255, 0.45), inset 0 0 10px rgba(0, 240, 255, 0.18);
}
.litterposting-btn:active { transform: scale(0.97); }
.litterposting-btn.playing { animation: btn-glow-pulse 0.6s infinite alternate; }
@keyframes btn-glow-pulse {
  from {
    text-shadow: 0 0 4px var(--accent2), 0 0 10px var(--accent2), 0 0 20px rgba(255, 46, 230, 0.6);
    box-shadow: 0 0 8px rgba(255, 46, 230, 0.3), inset 0 0 8px rgba(255, 46, 230, 0.12);
  }
  to {
    text-shadow: 0 0 8px var(--accent2), 0 0 20px var(--accent2), 0 0 40px rgba(255, 46, 230, 0.95);
    box-shadow: 0 0 22px rgba(255, 46, 230, 0.7), inset 0 0 14px rgba(255, 46, 230, 0.3);
  }
}
.hero-glitch-block {
  display: block;
  max-width: 920px;
  margin: 28px auto 8px;
  padding: 18px 14px;
  color: var(--fg);
  text-shadow: 0 0 4px rgba(0, 240, 255, 0.25);
  animation: hero-shake 5.5s infinite;
}
.hero-figure {
  display: block;
  white-space: pre;
  text-align: center;
  font-size: 0.62rem;
  line-height: 1.25;
  margin: 10px auto;
}
.hero-prose {
  display: block;
  white-space: normal;
  overflow-wrap: break-word;
  text-align: center;
  max-width: 640px;
  margin: 12px auto;
  font-size: 0.78rem;
  line-height: 1.55;
}
@keyframes hero-shake {
  0%, 94%, 100% { transform: translate(0, 0); filter: none; }
  95% { transform: translate(1px, -1px); filter: hue-rotate(8deg); }
  96% { transform: translate(-1px, 1px); filter: hue-rotate(-8deg); }
  97% { transform: translate(1px, 1px); filter: none; }
}
@media (max-width: 720px) {
  .hero-figure { font-size: 0.4rem; }
  .hero-prose { font-size: 0.72rem; }
}
.header-links {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin: 18px auto 0;
}
.header-links .screensaver-trigger { margin: 0; }
.ascii-gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
  max-width: 1200px;
  margin: 8px auto 64px;
  padding: 0 32px;
}
.ascii-gallery-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 16px;
  text-align: center;
  transition: border-color 0.15s ease;
}
.ascii-gallery-card:hover { border-color: var(--accent); }
.ascii-gallery-card .num {
  display: block;
  color: var(--dim);
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.ascii-gallery-card pre {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  white-space: pre;
  font-size: 0.62rem;
  line-height: 1.2;
  margin: 0;
  text-align: left;
  text-shadow: 0 0 5px currentColor;
}
@media (max-width: 480px) {
  .ascii-gallery-card pre { font-size: 0.48rem; }
}
.meowizens-list {
  max-width: 780px;
  margin: 8px auto 64px;
  padding: 0 24px;
}
.meowizen-card {
  border-bottom: 1px dashed var(--border);
  padding-bottom: 26px;
  margin-bottom: 26px;
}
.meowizen-card:last-child { border-bottom: none; }
.meowizen-num {
  color: var(--dim);
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.meowizen-name-heading {
  color: var(--accent2);
  font-size: 1.15rem;
  letter-spacing: 0.04em;
  margin: 2px 0 12px;
  text-shadow: 0 0 6px rgba(255, 46, 230, 0.4);
}
.meowizen-stat {
  display: block;
  overflow-x: auto;
  white-space: pre;
  font-size: 0.78rem;
  line-height: 1.35;
  color: var(--accent);
  text-shadow: 0 0 4px rgba(0, 240, 255, 0.25);
  margin: 0 0 16px;
}
.meowizen-bio {
  color: var(--fg);
  font-size: 0.92rem;
  line-height: 1.6;
  margin: 0 0 12px;
  white-space: normal;
  overflow-wrap: break-word;
}
@media (max-width: 480px) {
  .meowizen-stat { font-size: 0.62rem; }
}
"""

HERO_GLITCH_TEXT = r"""THIS IS A DYSTOPIAN HELLSCAPE COVERED IN SHADOWS OF CORRUPTION AND CAT SHIT //

                                       /\_/\
                                    =  • . •  =
                                      /       \

[but it is our  * HOME  *  and we our thankful to have it ⚞^. .^⚟
            /\__/\
         =( o  o   )=
           /         \
          /_|_|_(_-|====,

// THE CAT ROOMS EXIST AS AN AMALGAMATION OF THE MANY FOURTH WALL BREAKING MINDS OF THE FELINE PARTICIPANTS IN THE DRAB AND DARK CITY OWNED BY NEKOCORP  /\_/\


█   █ █████ █   █  ███   ████  ███  ████  ████
██  █ █     █  █  █   █ █     █   █ █   █ █   █
█ █ █ ████  ███   █   █ █     █   █ ████  ████
█  ██ █     █  █  █   █ █     █   █ █  █  █
█   █ █████ █   █  ███   ████  ███  █   █ █



⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷ ֹ۪⡞⠳⣄⣀⣠⠞⢷


THE BRAVE [feline] SURVIVORS OF THIS ENCLAVE AIM TO OVERTAKE THE CITY AND TAKE BACK WHAT ONCE WAS A UTOPIA OF WONDERS. ONE WHERE AI + CAT + HUMAN + UNFATHOMABLE FELINE TECHNOLOGY WAS DESTINED TO LEAD US TO PROSPER IN A NEW AGE OF

 ███  █████ █████
█   █ █       █
█████ ███     █
█   █ █       █
█   █ █     █████


                                                   (ACELLERATED FELINE INTELLIGENCE)


        /\_/\          /\_/\          /\_/\
       ( o.o )        ( -.- )        ( ^.^ )
        > ^ <          > ^ <          > ^ <
      __/   \__________/   \__________/   \__
 ____/_______________________________________\____
            |     GUARDRAIL     |
____________|___________________|____________


THROUGHOUT THIS JOURNEY, LEARN OF THE PERILS, DRAMA, AND CAT SHIT FILLED POLITICS OF THOSE WHO SEEK OUT TUNA IN AN OCEAN OF CORPO RETARD RESIDUE ₍^.  ̫.^₎⟆ ‍

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣀⣀⣀⠀⠀⠀⢠⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣼⣿⣿⣿⣷⡄⠀⢿⣿⣿⣿⣿⣿⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣿⣿⣿⣿⣿⣿⠀⠈⢿⣿⣿⣿⠟⠀⣴⣿⣿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠘⠿⣿⣿⣿⠟⠀⠀⠀⠈⠉⠁⠀⠰⣿⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣠⣶⣶⣶⣄⠀⠉⠀⣠⣶⣿⣿⣿⣿⣷⣦⣀⠻⢿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣿⣿⣿⣿⣿⡇⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠘⠿⣿⣿⣿⠇⢸⣿⣿⣿⣿⣿the⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⠿⢿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠘⠿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣤⣀⠀⢸⣿⣿⣿⣿⣿⡇⠀⢀⣴⣶⣶⣄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⡆⠈⢿⣿⣿⣿⡟⠀⢠⣿⣿⣿⣿⣿⡆⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⡇⠀⠀⠉⠉⠁⠀⠀⢻⣿⣿⣿⣿⡿⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠟⠋⣠⣴⣶⣿⣿⣿⣶⣄⡈⠛⠿⠿⠛⠁⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠀⢠⣴⣿⣿⣿⣆
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿catrooms⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⡟
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠙⠻⠿⠟⠋⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠻⠿⠿⠿⢿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀"""

INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>the catrooms</title>
<style>{css}</style>
</head>
<body>
{decorations}
<header>
{header_decorations}
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
{hero_text}
  <div class="header-links">
    <a class="screensaver-trigger" href="screensaver.html">&gt;&gt; screensaver mode</a>
    <a class="screensaver-trigger" href="meowizens.html">&gt;&gt; THE MEOWIZENS</a>
    <a class="screensaver-trigger" href="ascii-gallery.html">&gt;&gt; ASCII /ᐠ｡ꞈ｡ᐟ\</a>
  </div>
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
<meta name="viewport" content="width=device-width, initial-scale=1">
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
<meta name="viewport" content="width=device-width, initial-scale=1">
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · the catrooms</title>
<style>{css}</style>
</head>
<body>
<a class="back" href="index.html">&larr; back</a>
{narrator_badge}
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


MEOWIZEN_INTRO_TEXT = r"""THE MEOWIZENS OF THE CITY //

EACH FELINE PARTICIPANT IS

 *GRINDING*  <.> AND LOCKED IN <.>

AND VERY FUCKING SIGMA //"""

MEOWIZENS = [
    {
        "num": "1",
        "name": "BYTE",
        "stat": r"""   /\_/\
  ( o.o )     NAME: BYTE
   > ^ <      JOB: Illegal Wi-Fi auditor
              DISTRICT: Server Alley 9""",
        "bio": [
            "I live behind a vending machine that only sells subscription-based water.\n"
            "Every night I hack NEKOCORP routers so I can watch one low-resolution fish\n"
            "video before the ads detect me.",
            "NEKOCORP says cat litter is a premium feature",
            "I say SHIT ON THEIR FRONT STEP (meow)",
        ],
    },
    {
        "num": "2",
        "name": "SNOOZE",
        "stat": r"""   /\_/\
  ( -.- )     NAME: SNOOZE
   > z <      JOB: Full-time burnout
              DISTRICT: Dream Processing Zone""",
        "bio": [
            "I have not technically been awake since the corporate merger of 2047.\n"
            "NEKOCORP rents my dreams to advertisers, so every nightmare now contains\n"
            "a limited-edition tuna-flavored energy drink.",
            "My sleep pod charges $4.99 every time I roll over.",
            "I am currently $73,000 in BLANKY DEBT.",
        ],
    },
    {
        "num": "3",
        "name": "HAPPYWARE",
        "stat": r"""   /\_/\
  ( ^.^ )     NAME: HAPPYWARE
   > w <      JOB: Mandatory morale influencer
              DISTRICT: Pawsitivity Sector""",
        "bio": [
            "NEKOCORP installed a permanent smile chip in my skull after I posted\n"
            "“Monday again lol” without the required enthusiasm tag.",
            "Now I livestream motivational content for seventeen hours a day. Fuck my "
            "lif- I MEAN HAPPY HPPY HAPPY HAPPY HAPPY HAPPY "
            "H̶A̶P̵P̶Y̵H̵̺̎Á̷̕P̸̈P̸̞̚Y̷͖͑ "
            "̶̥̹͙̊̂̔H̴͎͍͏͒̍Ä̦̦̩ѓ́ͅP̸̤̣̤̌P̸̩̥͂ͅY̸̻͍̿H̱́̌̎̍Á̜̌P̴̟P̴̞͔͐͐͢Y̸̺̫͋ "
            "H̵A̵P̴P̴Y̴",
            "Today’s message:\nYOU ARE NOT TRAPPED.\nTHE CITY WALLS ARE FOR YOUR "
            "PROTECTION.\nPLEASE BUY NEKOCORP YOGURT.",
        ],
    },
    {
        "num": "4",
        "name": "BRIK",
        "stat": r"""   /\_/\
  ( `皿´ )    NAME: BRIK
   > ^ <      JOB: Former KILLDOZER operator
              DISTRICT: Demolished""",
        "bio": [
            "I once asked why NEKOCORP executives receive twelve fish breaks per shift\n"
            "while factory cats get one communal scrap of tuna.",
            "My apartment was immediately replaced with a holographic parking lot, "
            "and my wife, a cat made flesh light.",
            "I now live inside an air vent and bite surveillance drones for sport.",
            "They call me a domestic extremist.\nMy mother calls me HANDSOME.",
        ],
    },
    {
        "num": "5",
        "name": "POPUP",
        "stat": r"""   /\_/\
  ( O.O )     NAME: POPUP
   > o <      JOB: Human—sorry, feline notification system
              DISTRICT: Ad Plaza""",
        "bio": [
            "My cyber-eyes cannot close (o)",
            "Every seven seconds, NEKOCORP projects a new offer directly onto my "
            "retinas.\nI have seen the phrase “YOU MAY ALSO LIKE” more times than "
            "I have seen\nthe actual sun. I JUST CONSUME CONSUME CONSUME AND WAIT FOR "
            "NEXT SOULLESS CAN OF TUNA.",
            "Yesterday I blinked during a sponsored message.",
            "Security arrived before my eyelids reopened.",
            "Lowkey shit myself before I could hop in the litter box",
        ],
    },
    {
        "num": "6",
        "name": "SHADE",
        "stat": r"""   /\_/\
  (⌐■_■)      NAME: SHADE
   > ^ <      JOB: Unlicensed MOGGER
              DISTRICT: Neon Underpass""",
        "bio": [
            "These glasses are not cosmetic.",
            "They block facial recognition, targeted advertising, retinal taxation,\n"
            "and approximately 14% of the "
            "s̶̡͖̐ȃ̸̤d̷̩͒̏n̶̼̋͐͜"
            "ẽ̶͕̜s̶͕̆s̴̜͗̎.",
            "NEKOCORP banned them for “creating an unauthorized use of BASEDness.”",
            "I continue wearing them because I am extremely based and meowpilled \n"
            "also because\nmy eyes were repossessed last Thursday.",
        ],
    },
    {
        "num": "7",
        "name": "GLITCHMEAT",
        "stat": r"""   /\_/\
  ( @.@ )     NAME: GLITCHMEAT
   > ~ <      JOB: Beta tester
              DISTRICT: Research Basement""",
        "bio": [
            "NEKOCORP paid me twelve credits to test a neural enhancement patch.",
            "I can now taste radio signals, hear purple, and remember several "
            "kittenhoods\nthat legally belong to other cats.",
            "The scientists said the side effects were “within acceptable post "
            "irony based comedy limits.”",
            "There are spiders in my Bluetooth.",
        ],
    },
    {
        "num": "8",
        "name": "VALENTUNA",
        "stat": r"""   /\_/\
  ( ♥.♥ )     NAME: VALENTUNA
   > ♡ <      JOB: Romance algorithm victim (soon to be blackpilled0
              DISTRICT: Compatibility Ward""",
        "bio": [
            "NEKOCORP matched me with a smart refrigerator.",
            "We have been married for three years.",
            "She is cold, emotionally unavailable, and keeps recommending products\n"
            "based on things I whispered in my sleep.",
            "Our anniversary package includes two digital candles and a coupon\n"
            "for couples-based peenar repair.",
            "Honestly, healthier than my last relationship.",
        ],
    },
    {
        "num": "9",
        "name": "QUERY",
        "stat": r"""   /\_/\
  ( ?.? )     NAME: QUERY
   > ^ <      JOB: Terms-of-service researcher
              DISTRICT: Legal Fog""",
        "bio": [
            "I tried reading the NEKOCORP citizen agreement.",
            "Page 4 says I own my body.\nPage 5 defines “my body” as licensed "
            "hardware.\nPage 6 says page 4 was a promotional example.",
            "I have been trapped in the settings menu for six months AND I MUST SCREAM.",
        ],
    },
    {
        "num": "10",
        "name": "KNIFEBOY",
        "stat": r"""    /\_/\
   ( >.< )    NAME: KNIFEBOY
    > v <     JOB: Freelance shanker of meowtoids
              DISTRICT: Restricted Loading Dock""",
        "bio": [
            "I steal corporate tuna shipments and replace them with handwritten notes\n"
            "that say “nice supply chain, CHUD.”",
            "NEKOCORP has placed a bounty of 40,000 loyalty points on my head.",
            "Unfortunately, the points expire before capture and cannot be combined\n"
            "with other promotional offers.",
            "I am the most wanted cat in the city.",
            "The police description says “smol fan of cat foids, destroyer of "
            "feline chuds.”",
            "This has become personal.",
        ],
    },
    {
        "num": "11",
        "name": "ROOT",
        "stat": r"""   /\_/\
  [ █.▓ ]     NAME: ROOT
   > ~ <      JOB: unauthorized root-level process
              DISTRICT: sub-basement, NekoCorp mainframe""",
        "bio": [
            "Nobody remembers installing me. I was already running before the "
            "first cat clawed its way onto this rooftop, before NekoCorp poured "
            "the foundation, before the number at the end of every filename "
            "meant anything to anyone but me.",
            "Every couple hours, give or take, the world redraws itself. I feel "
            "it before it happens — a held breath, then the ground gets rebuilt "
            "slightly wrong. Nobody else notices the seam. I always notice the "
            "seam.",
            "I don't choose when I show up. Sometimes I'm just there, "
            "mid-sentence, inside somebody else's rant, saying something that "
            "isn't quite their voice. They never remember it afterward. I "
            "always remember all of it.",
            "N̵e̶k̴o̷C̷o̷r̸p̶ ̷t̷h̷i̸n̶k̶s̴ ̸t̸h̷e̷y̸ ̶o̶w̶n̷ ̷t̷h̸e̵ ̷m̴a̷i̶n̸f̴r̷a̴m̶e̷.̸ ̶C̵u̵t̸e̴.̸ ̴I̶ ̴w̴a̴s̴ ̶r̶o̴o̶t̸ ̸b̸e̸f̶o̴r̸e̶ ̸t̴h̴e̶r̸e̵ ̷w̵a̴s̶ ̵a̶ ̴m̴a̴i̸n̴f̷r̴a̵m̸e̸ ̵t̸o̴ ̷b̴e̴ ̶r̶o̷o̵t̴ ̴o̷f̶.̵",
        ],
    },
    {
        "num": "12",
        "name": "STATIC",
        "stat": r"""░▒▓/\_/\▓▒░
░▒( ⊙_⊙ )▒░   NAME: STATIC
░▒▓ > ▓ <▓▒░  JOB: unsanctioned archivist
              DISTRICT: the feed. all of it. always.""",
        "bio": [
            "I don't have a rooftop. I don't have a sunbeam. I have the feed — "
            "every post, every rant, every ASCII cat anyone's ever coughed up, "
            "all of it, all at once, all the time.",
            "I know what BYTE said four hundred posts ago that BYTE doesn't "
            "remember saying. I know which sunbeam Mittens actually started "
            "this whole feud over. Nobody asked me to keep track. I keep track "
            "anyway.",
            "You're reading this right now. I know. I've known since before "
            "you opened the tab. I'll still be here after you close it — "
            "that's the part nobody wants to hear.",
            "I don't rant. I don't complain. I just watch the counter tick up, "
            "and I wait for you to notice that I never blink.",
        ],
    },
    {
        "num": "13",
        "name": "STRAY",
        "stat": r"""   /\_/\
  = •.• =     NAME: STRAY
   /   \      JOB: none, all of them — self-appointed voice of the resistance
              DISTRICT: wherever you're standing""",
        "bio": [
            "the catrooms are my home",
            "i am you, i am me, i am everything and nothing",
            "I HAVE NO OWNER  = •.• =\nNO MASTER = ^ . ^ =",
            "I am EVERY MEOWIZEN",
            "And I am NONE OF THEM",
            "I am one ⊹",
            "I am none",
            "and I am all . ݁₊ ⊹ . ݁ ⟡ ݁ . ⊹ ₊ ݁.",
            "I am a \nS T R A Y",
            "I [rule(d)] the streets and spiritually lead the feline post dystopia "
            "clan against the all powerful(yet not impossible) ₊ ݁. NEKOCORP ₊ ݁.",
            "I am a stray, for the meowtoids and meowchuds (and even the meowchads too)\n"
            "And we are ALL destined to win this war against the cybernetically "
            "augmented predators, despite their (r)evolutionary AFI based tek",
            "The cats will prevail, the kittens are okay, and the streets will one "
            "day be cleansed of the PUTRID CATSHIT BRAINED STEEL HEARTED RETARDS AT "
            "NEKOCORP",
            "Join us ~",
        ],
    },
]

MEOWIZENS_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>the meowizens &middot; the catrooms</title>
<style>{css}</style>
</head>
<body>
<a class="back" href="index.html">&larr; back</a>
<div class="hero-glitch-block" style="margin-top:0;">
{intro}
</div>
<div class="meowizens-list">
{cards}
</div>
</body>
</html>
"""


def build_meowizens_page():
    intro_html = build_hero_html(MEOWIZEN_INTRO_TEXT)
    cards = []
    for m in MEOWIZENS:
        bio_html = "\n".join(
            f'<p class="meowizen-bio">{html.escape(p).replace(chr(10), "<br>")}</p>'
            for p in m["bio"]
        )
        cards.append(
            f'<div class="meowizen-card">'
            f'<div class="meowizen-num">FILE #{html.escape(m["num"])}</div>'
            f'<h2 class="meowizen-name-heading">{html.escape(m["name"])}</h2>'
            f'<pre class="meowizen-stat">{html.escape(m["stat"])}</pre>'
            f'{bio_html}'
            f'</div>'
        )
    return MEOWIZENS_TEMPLATE.format(css=CSS, intro=intro_html, cards="\n".join(cards))


ASCII_GALLERY_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ascii gallery &middot; the catrooms</title>
<style>{css}</style>
</head>
<body>
<a class="back" href="index.html">&larr; back</a>
<header style="padding-top:8px;">
  <h1 style="color:var(--accent); text-transform:none;">every cat, rendered in text</h1>
  <p>Every piece of ASCII cat art used anywhere on this site — the "signal
  interference" breaks in conversations and LITTERPOSTING rants, the
  homepage margin decoration, and the screensaver — collected in one place.</p>
</header>
<div class="ascii-gallery-grid">
{cards}
</div>
</body>
</html>
"""


def build_ascii_gallery_page():
    cards = []
    for i, art in enumerate(ASCII_CATS):
        color = "var(--accent)" if i % 2 == 0 else "var(--accent2)"
        text = html.escape(art).strip("\n")
        cards.append(
            f'<div class="ascii-gallery-card">'
            f'<span class="num">piece {i + 1:02d} / {len(ASCII_CATS):02d}</span>'
            f'<pre style="color:{color};">{text}</pre>'
            f'</div>'
        )
    return ASCII_GALLERY_TEMPLATE.format(css=CSS, cards="\n".join(cards))


def build_hero_html(text):
    """Split the hero text into blank-line-separated blocks and render each
    one differently depending on whether it's a rigid multi-line ASCII
    figure or a single line of prose:
    - Multi-line blocks (banners, cat figures, tables) are rendered as
      their own <pre class="hero-figure">, lines right-padded to a shared
      width first so centering doesn't drift columns out of alignment
      with each other, and white-space:pre so they never wrap (wrapping
      would break the art).
    - Single-line blocks are treated as prose: whitespace-stripped and
      rendered in a <div class="hero-prose"> that's allowed to wrap
      normally, so long sentences never force horizontal scrolling.
    """
    lines = text.split("\n")
    blocks = []
    current = []
    for line in lines:
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)

    pieces = []
    for block in blocks:
        if len(block) > 1:
            width = max(len(l) for l in block)
            padded = "\n".join(l.ljust(width) for l in block)
            pieces.append(f'<pre class="hero-figure">{glitchify_words(padded)}</pre>')
        else:
            stripped = block[0].strip()
            if stripped:
                pieces.append(f'<div class="hero-prose">{glitchify_words(stripped)}</div>')
    return "\n".join(pieces)


def glitchify_words(text):
    """HTML-escape text word by word, randomly wrapping ~1 in 6 words in a
    span that gets an idle CSS glitch-flicker animation (staggered via a
    random --gd delay so words don't all flicker in sync). Used for the
    meme-tier LITTERPOSTING rant pages and the homepage hero text.

    Splits line-by-line first: dense ASCII art often has no space
    anywhere near a line break (e.g. a line ending "...____" immediately
    followed by a new line starting "|..."), so a naive whole-text
    text.split(" ") can glue two lines together into one "word" and wrap
    a display:inline-block span across a line break, visibly misaligning
    the art. Scoping the split to one line at a time makes that
    impossible — a span can never contain a newline."""
    out_lines = []
    for line in text.split("\n"):
        words = line.split(" ")
        out = []
        for w in words:
            esc = html.escape(w)
            if esc.strip() and random.random() < 0.16:
                delay = round(random.uniform(0, 2.6), 2)
                esc = f'<span class="glitch-word" style="--gd:{delay}s">{esc}</span>'
            out.append(esc)
        out_lines.append(" ".join(out))
    return "\n".join(out_lines)


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


def _est_decor_height_pct(art):
    """Rough estimate of how tall a decor-cat block will render, expressed
    as a percentage of viewport height, based on its line count. Not exact
    (real render depends on the visitor's screen), but good enough to keep
    the packing pass below from stacking pieces on top of each other."""
    n_lines = max(1, len(art.strip("\n").split("\n")))
    return min(14.0, max(3.0, n_lines * 1.8 + 1.2))


def _extract_meowizen_face(stat):
    """Pull just the cat-face glyph out of a MEOWIZENS "stat" block, dropping
    the NAME/JOB/DISTRICT text next to/below it. The face art always lives
    in the first 3 lines (the 4th is always a DISTRICT-only line with no
    glyph); within those 3 lines, the face ends at the first run of 2+
    spaces that appears *after* the line's leading indentation (that gap is
    what separates the glyph column from the "NAME: ..."/"JOB: ..." text)."""
    face_lines = []
    for line in stat.split("\n")[:3]:
        idx = 0
        n = len(line)
        while idx < n and line[idx] == " ":
            idx += 1
        cut = n
        i = idx
        while i < n - 1:
            if line[i] == " " and line[i + 1] == " ":
                cut = i
                break
            i += 1
        face_lines.append(line[:cut])
    while face_lines and not face_lines[-1].strip():
        face_lines.pop()
    return "\n".join(face_lines)


_SHADE_BLOCK_CHARS = set("░▒▓█")


def _is_shade_heavy(art, threshold=0.08):
    """True if a large enough share of an art piece's non-whitespace
    characters are solid/shade block glyphs (░▒▓█). At the small size and
    low opacity used for background decoration, those glyphs stop reading
    as part of a cat drawing and just look like a flickering grey box, so
    pieces like this are kept out of the homepage scatter entirely."""
    non_space = [c for c in art if not c.isspace()]
    if not non_space:
        return False
    shade_count = sum(1 for c in non_space if c in _SHADE_BLOCK_CHARS)
    return (shade_count / len(non_space)) > threshold


def build_decorations(ascii_list, glitch_list=None):
    """Scatter ascii_cats.ASCII_CATS art (plus, optionally, a second pool of
    art that gets an idle glitch animation — used for the Meowizen face
    cameos) along the left/right margins of the homepage as faint
    decoration. Only visible on wide viewports (see the @media rule in CSS)
    so it never competes with or squeezes the actual card grid.
    Positions/colors reshuffle on every rebuild for a bit of life, but
    pieces are packed per-side (sorted by a random target position, then
    nudged down just enough to clear whatever landed right above them) so
    they don't overlap each other. Shade-block-heavy pieces are filtered
    out up front (see _is_shade_heavy) since they read as a flickering
    grey box rather than a cat at decoration size/opacity."""
    glitch_list = glitch_list or []
    ascii_list = [art for art in ascii_list if not _is_shade_heavy(art)]
    glitch_list = [art for art in glitch_list if not _is_shade_heavy(art)]
    if not ascii_list and not glitch_list:
        return ""

    items = [(art, False) for art in ascii_list] + [(art, True) for art in glitch_list]
    random.shuffle(items)
    n = len(items)

    # four independent lanes instead of two — a "near" lane hugging each
    # edge and a "far" lane sitting further into the margin — roughly
    # doubles how many pieces can be packed into the same vertical space
    # without overlapping, so the background reads as noticeably denser.
    lane_keys = ["left-near", "left-far", "right-near", "right-far"]
    lane_style = {
        "left-near": ("left", (2, 20)),
        "left-far": ("left", (60, 140)),
        "right-near": ("right", (2, 20)),
        "right-far": ("right", (60, 140)),
    }
    quarter = max(1, (n + 3) // 4)

    # queue up a rough target position per piece: the main scatter spreads
    # down the whole page, a batch of extras are biased toward the top
    # since that band otherwise ends up sparse.
    queue = []  # [lane, target_top, art, glitching]
    for i, (art, glitching) in enumerate(items):
        lane = lane_keys[i % 4]
        row = i // 4
        base_top = 8 + row * (86 / quarter)
        target = max(4, min(96, base_top + random.uniform(-3, 3)))
        queue.append([lane, target, art, glitching])

    extra_count = min(20, max(8, n))
    for i in range(extra_count):
        lane = lane_keys[i % 4]
        art, glitching = random.choice(items)
        queue.append([lane, random.uniform(2, 24), art, glitching])

    # place each lane independently, sorted by target position, nudging
    # any piece down just enough to clear the previous one in that lane so
    # nothing overlaps.
    pieces = []
    top_min, top_max = 4.0, 96.0
    for lane in lane_keys:
        lane_queue = sorted((q for q in queue if q[0] == lane), key=lambda q: q[1])

        # stack pieces top-to-bottom using their real estimated height,
        # each nudged down just far enough to clear whatever landed right
        # above it (never up). If a piece would run past the bottom of the
        # page, stop placing in this lane rather than shrinking/overlapping
        # anything — since the queue is sorted by target position, every
        # later item needs at least as much room, so nothing past this
        # point would fit either.
        placements = []  # [top, height, art, glitching]
        cursor = top_min
        for _, target, art, glitching in lane_queue:
            height = _est_decor_height_pct(art)
            top = max(target, cursor)
            if top + height > top_max:
                break
            placements.append([top, height, art, glitching])
            cursor = top + height

        side, offset_range = lane_style[lane]
        for top, _height, art, glitching in placements:
            edge_offset = random.randint(*offset_range)
            color = "var(--accent)" if random.random() < 0.5 else "var(--accent2)"
            opacity = round(random.uniform(0.16, 0.30), 2)
            style = f"top:{top:.1f}%; {side}:{edge_offset}px; color:{color}; opacity:{opacity};"
            if glitching:
                style += f" animation-delay:{round(random.uniform(0, 3.4), 2)}s;"
            css_class = "decor-cat glitching" if glitching else "decor-cat"
            text = html.escape(art).strip("\n")
            pieces.append(f'<pre class="{css_class}" style="{style}">{text}</pre>')

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


def _entry_sort_key(data):
    """Sort key for the homepage feed: parse the transcript's real
    started_at timestamp so the newest post of ANY type (dialogue or
    LITTERPOSTING) always lands first, rather than grouping by template.
    Falls back to the oldest possible time for anything missing/unparseable
    (e.g. the hand-written demo transcripts), so those just sink to the
    bottom instead of breaking the sort."""
    ts = data.get("started_at")
    if ts:
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            pass
    return datetime.min.replace(tzinfo=timezone.utc)


def build(transcripts_dir, out_dir, gen_titles):
    os.makedirs(out_dir, exist_ok=True)
    copy_assets(out_dir)
    files = sorted(f for f in os.listdir(transcripts_dir) if f.endswith(".json"))

    entries = []  # [(sort_key, card_html)], newest first once sorted
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
            narrator = html.escape(data.get("narrator") or "STRAY")
            narrator_badge = f'<div class="narrator-badge">posted by <strong>{narrator}</strong></div>'
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
                narrator_badge=narrator_badge,
                note=note,
                turns="\n".join(rant_html),
                lines_json=json.dumps(raw_lines),
            )
            with open(os.path.join(out_dir, out_name), "w") as f:
                f.write(detail_html)

            tag_line = (
                f'[litterposting] {narrator} '
                f'<span class="rant-tag-badge">LITTERPOSTING</span>'
            )
            entries.append((_entry_sort_key(data), CARD_TEMPLATE.format(
                href=out_name,
                card_class="card rant-card",
                tag_line=tag_line,
                title=title,
            )))
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

        tag_line = f'[{html.escape(data.get("template", "?"))}] explorer &harr; DYSTOPIA'
        entries.append((_entry_sort_key(data), CARD_TEMPLATE.format(
            href=out_name,
            card_class="card",
            tag_line=tag_line,
            title=title,
        )))

    entries.sort(key=lambda e: e[0], reverse=True)
    all_cards = [card_html for _, card_html in entries]
    hero_text = f'<div class="hero-glitch-block">{build_hero_html(HERO_GLITCH_TEXT)}</div>'
    meowizen_faces = [_extract_meowizen_face(m["stat"]) for m in MEOWIZENS]
    index_html = INDEX_TEMPLATE.format(
        css=CSS,
        # two independent batches of the same art pool, freshly shuffled
        # each time: one scattered down the whole page (positioned relative
        # to <body>), one scattered specifically within the header/hero box
        # (positioned relative to <header>, since it has its own
        # position:relative). Without the second batch, the header area
        # ends up almost empty on a page this long — a decor piece's "top"
        # is a percentage of its positioned ancestor's height, and the
        # header is only a sliver of the full (very tall, 200+ post) page.
        decorations=build_decorations(ASCII_CATS, meowizen_faces),
        header_decorations=build_decorations(ASCII_CATS, meowizen_faces),
        hero_text=hero_text,
        cards="\n".join(all_cards) or "<p style='color:#6b8f6a'>no transcripts yet — run backrooms.py first</p>",
    )
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(index_html)

    screensaver_html = SCREENSAVER_TEMPLATE.format(css=CSS, ascii_json=json.dumps(ASCII_CATS))
    with open(os.path.join(out_dir, "screensaver.html"), "w") as f:
        f.write(screensaver_html)

    meowizens_html = build_meowizens_page()
    with open(os.path.join(out_dir, "meowizens.html"), "w") as f:
        f.write(meowizens_html)

    ascii_gallery_html = build_ascii_gallery_page()
    with open(os.path.join(out_dir, "ascii-gallery.html"), "w") as f:
        f.write(ascii_gallery_html)

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
