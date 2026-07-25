# backrooms (personal replication — cyberpunk cats edition)

two FELINECLAUDE instances are put into a scenario and left to talk to
each other, unsupervised, until a turn limit or stop sequence. One plays a
street cat, the other plays the neon-soaked cyberpunk megacity around it
sensed through smell, sound, and instinct rather than human language.
Transcripts are saved and rendered as a browsable static gallery site.



The art in `ascii_cats.py` is either the classic, decades-old, unattributed
`/\_/\ ( o.o )` style cat-face meme (used everywhere online, no single
owner) or original pieces written for this project. None of it is copied
from artist-credited galleries like asciiart.eu — that site explicitly asks
that credit not be stripped from reused pieces, so this avoids that
entirely by not reusing their art. Feel free to add your own designs to the
`ASCII_CATS` list in `ascii_cats.py`.



- Output can get surreal, glitchy, or existential — that's the nature of
  the experiment, not a bug.
- The `^C^C` stop sequence lets either model end the conversation early;
  the loop also always respects `--max-turns`.
