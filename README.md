# backrooms (personal replication — cyberpunk cats edition)

A small replication of Andy Ayrey's [Infinite Backrooms](https://dreams-of-an-electric-mind.webflow.io/),
re-themed: two Claude instances are put into a scenario and left to talk to
each other, unsupervised, until a turn limit or stop sequence. One plays a
street cat, the other plays the neon-soaked cyberpunk megacity around it —
sensed through smell, sound, and instinct rather than human language.
Transcripts are saved and rendered as a browsable static gallery site.

The original CLI-hyperstition scenario is still available via
`--template cli` if you want to compare or switch back.

Two scripts:
- `backrooms.py` — runs the two-model conversation, saves transcripts as JSON.
- `build_site.py` — turns saved transcripts into a static HTML gallery (`docs/`, so it's ready for GitHub Pages with zero extra config).

`transcripts/` ships with two hand-written demo conversations so you can see
the site format immediately, without needing an API key yet.

## Setup

### 1. Get an Anthropic API key

This is a *developer* API key, separate from a claude.ai subscription — it's
billed per token, pay-as-you-go, and is what lets a script like this one
call Claude directly instead of you using the chat app.

1. Go to https://console.anthropic.com/ and sign up or log in.
2. If this is a new account, you'll be asked to add a payment method under
   **Settings → Billing** before the API will accept requests. Anthropic
   typically gives new accounts a small amount of free credit, but you can't
   rely on that being enough — check the Billing page to see your balance.
3. Go to **Settings → API Keys → Create Key**. Give it any name (e.g.
   "backrooms").
4. Copy the key immediately — it's shown once, in full, and never again.
   It looks like `sk-ant-api03-...`. If you lose it, you'll need to
   generate a new one and revoke the old one.
5. Optional but recommended: under **Settings → Limits**, set a monthly
   spend cap so an unattended run can't rack up an unexpected bill.

### 2. Give the script access to that key

The script reads the key from an environment variable called
`ANTHROPIC_API_KEY`. There are two ways to set that:

**Option A — `.env` file (easiest, and what this project defaults to):**
```
cp .env.example .env
```
Then open `.env` in any text editor and replace the placeholder with your
real key, so the file reads:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```
Both `backrooms.py` and `build_site.py` automatically load this file on
startup (via `python-dotenv`) — you don't need to do anything else. Just
don't commit or share this file, since it contains a live credential.

**Option B — export it in your shell (no file needed):**
```
export ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```
macOS/Linux: run that in Terminal before running the scripts — it only
lasts for that terminal session unless you add it to your shell profile
(`~/.zshrc`, `~/.bashrc`, etc.). Windows (PowerShell): use
`$env:ANTHROPIC_API_KEY = "sk-ant-..."` instead.

Either way works; `.env` is generally more convenient since you only set it
once per project folder.

### 3. Install dependencies

From inside this folder:
```
pip install -r requirements.txt --break-system-packages
```
This installs two packages: `anthropic` (the official SDK used to call
Claude) and `python-dotenv` (which reads the `.env` file from step 2). The
`--break-system-packages` flag is only needed on newer macOS/Linux systems
where pip refuses system-wide installs by default (PEP 668) — if you're
using a virtual environment instead, drop that flag:
```
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
To confirm it worked:
```
python3 -c "import anthropic, dotenv; print('ok')"
```
If that prints `ok` with no errors, you're set up and ready to run a
conversation.

## Run a conversation

```
python backrooms.py
```

This runs 20 turn-pairs (~40 messages) between two `claude-sonnet-5`
instances in the `cyberpunk_cats` scenario (default) and saves the
transcript to `transcripts/conversation-<id>.json`, updating the file after
every turn (so you can watch it live or kill it early with Ctrl+C — the
partial transcript is still saved).

Options:
```
python backrooms.py --model1 claude-opus-5 --model2 claude-sonnet-5 --max-turns 40
python backrooms.py --template cli        # switch back to the original scenario
python backrooms.py --ascii-chance 0.3    # more frequent ASCII art breaks (default 0.15)
python backrooms.py --ascii-chance 0      # disable ASCII art breaks entirely
```

### ASCII art breaks

At random points between turns, a small piece of ASCII cat art (`ascii_cats.py`)
gets spliced into the transcript as a "signal interference" interstitial —
static cutting into the broadcast. These are display-only: they're saved to
the transcript and rendered on the site, but never fed back into either
model's own conversation history, so they don't affect what the cats or the
city actually say to each other.

The art in `ascii_cats.py` is either the classic, decades-old, unattributed
`/\_/\ ( o.o )` style cat-face meme (used everywhere online, no single
owner) or original pieces written for this project. None of it is copied
from artist-credited galleries like asciiart.eu — that site explicitly asks
that credit not be stripped from reused pieces, so this avoids that
entirely by not reusing their art. Feel free to add your own designs to the
`ASCII_CATS` list in `ascii_cats.py`. The homepage also scatters every piece
from that list along its margins as decoration (see `build_decorations()`
in `build_site.py`) — wide screens only, so it never crowds the actual grid.

Each run costs real API tokens — a 20-turn run is roughly 20-40k tokens
total. Keep an eye on usage if you run many of these.

## Build the site

```
python build_site.py
```

Reads everything in `transcripts/`, writes `docs/index.html` plus one page
per conversation. Open `docs/index.html` in a browser.

Optional: generate a short poetic title per conversation (like the "mined
by" cards on the original site) using Claude itself:
```
python build_site.py --gen-titles
```
Falls back to a plain text snippet as the title if no API key is set.

Re-run `build_site.py` any time after generating new transcripts to refresh
the gallery.

## How this maps to the original

The original site is a Webflow CMS site: each entry is a saved transcript
with an auto-generated title, and someone runs the conversation loop on a
schedule and publishes new entries. This replication does the same thing
minus Webflow — a local folder of JSON transcripts plus a static site
generator instead of a CMS.

## Going live (GitHub Pages)

`docs/` is a plain folder of HTML files, so it can be hosted for free with
no server or database. GitHub Pages is the simplest option since it needs
zero extra config once your repo has a `docs/` folder.

**One-time setup, from a Terminal in this folder:**

1. If you don't already have one, create a free account at
   https://github.com.
2. On github.com, click **New repository**. Give it any name, leave it
   **Public** (GitHub Pages requires this on free accounts), and don't
   initialize it with a README (this folder already has one).
3. Back in Terminal, set up your identity and tell git to remember your
   GitHub login in macOS's Keychain (this matters later for the automated
   push — without it, every push would need an interactive login):
   ```
   git config --global user.name "your-name-or-project-name"
   git config --global user.email "you@example.com"
   git config credential.helper osxkeychain
   git branch -M main
   ```
4. Connect it to the repo you just created (GitHub shows you this exact URL
   after creating the repo — use yours, not this example):
   ```
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git add -A
   git commit -m "Initial commit"
   git push -u origin main
   ```
   The first push will prompt you to sign in — either a browser popup or a
   username + personal access token (GitHub phased out plain passwords for
   this; if asked for a token, create a **classic** token at
   github.com → Settings → Developer settings → Personal access tokens,
   with the `repo` checkbox checked). Because of the `credential.helper`
   line above, macOS saves this login in Keychain so future pushes
   (including automated ones) won't prompt again.
5. On github.com, go to your repo's **Settings → Pages**. Under "Build and
   deployment", set **Source: Deploy from a branch**, **Branch: main**,
   folder **/docs**, then Save.
6. After a minute or two, GitHub shows you the live URL — something like
   `https://your-username.github.io/your-repo/`.

**Attaching a custom domain:**

1. Buy a domain from any registrar (Namecheap, Cloudflare, Squarespace
   Domains, etc.) — typically $10-15/year.
2. In your repo's **Settings → Pages**, enter the domain under "Custom
   domain" and save (this creates a `CNAME` file in your repo automatically).
3. At your registrar, add DNS records pointing at GitHub Pages: four `A`
   records for the root domain (`185.199.108.153`, `185.199.109.153`,
   `185.199.110.153`, `185.199.111.153`) and a `CNAME` record for `www`
   pointing to `your-username.github.io`.
4. DNS changes can take anywhere from minutes to a few hours to propagate.
   Once the Pages settings page shows a green check, tick **Enforce HTTPS**.

**Updating the live site after this:**

Every time you want the live site to reflect new conversations: run
`python backrooms.py` (or let the hourly schedule do it) and
`python build_site.py`, then from Terminal in this folder:
```
git add -A
git commit -m "update"
git push
```
GitHub Pages redeploys automatically within a minute or two of the push —
no need to touch the Pages settings again.

## Automating the push (launchd)

Two files in this folder handle this:
- `auto_push.sh` — commits and pushes anything new, or does nothing if
  there's nothing to push. Logs every run to `push.log` in this folder.
- `com.cats.backrooms.autopush.plist` — a macOS `launchd` job that runs
  that script at minute 25 of every hour (chosen to land after the hourly
  generation task has usually finished).

**Prerequisite:** complete the one-time GitHub Pages setup above first
(specifically the `git config credential.helper osxkeychain` step and the
first successful `git push`) — the automated version can't do an
interactive login, so it depends on that cached credential already working.

**Install it**, from Terminal in this folder:
```
chmod +x auto_push.sh
cp com.cats.backrooms.autopush.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.cats.backrooms.autopush.plist
```
From then on, it runs automatically in the background — no need to keep a
Terminal window open, and it survives restarts.

**Check that it's working:**
```
cat push.log
```
You should see a new entry roughly every hour, either "pushed successfully"
or "no changes, skipping push". If you see "PUSH FAILED", the most likely
cause is the cached credential expiring — running `git push` by hand once
in Terminal will show the real error and typically fix it by re-caching a
fresh login.

**Uninstall it** if you ever want to stop the automation:
```
launchctl unload ~/Library/LaunchAgents/com.cats.backrooms.autopush.plist
rm ~/Library/LaunchAgents/com.cats.backrooms.autopush.plist
```

## Notes

- The system prompt and framing exchange used here are the real ones from
  the original project (via the open-source
  [UniversalBackrooms](https://github.com/scottviteri/UniversalBackrooms)
  replication), not invented for this repo.
- Output can get surreal, glitchy, or existential — that's the nature of
  the experiment, not a bug.
- The `^C^C` stop sequence lets either model end the conversation early;
  the loop also always respects `--max-turns`.
- The hourly scheduled task that generates new conversations is instructed
  to only ever touch files in `transcripts/` and `docs/`, and to never run
  git commands — everything else (this README included) should only ever
  change when you or I edit it directly.
