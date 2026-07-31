"""
ascii_cats.py — a small library of ASCII cat art used as random "static
bursts" / interstitials between conversation turns in the cyberpunk_cats
scenario.

Note on originality: sites like asciiart.eu host a lot of cat ASCII art
credited to named artists, and explicitly ask that credit not be stripped
when their pieces are reused. To stay clear of that, none of the art below
is copied from there. The first couple of entries use the classic
`/\_/\ ( o.o )` style cat face, which is a decades-old, unattributed,
public-domain-style meme convention repeated everywhere online (chat
clients, forums, etc.) rather than a specific artist's work. Everything
else here is original, written for this project's cyberpunk theme.
"""

ASCII_CATS = [
    # classic unattributed meme cat face
    r"""
 /\_/\
( o.o )
 > ^ <
""",
    # classic unattributed meme cat face, alert variant
    r"""
  /\___/\
 (  o.o  )
  > ^ ^ <
""",
    # original — cybernetic ear antenna, scanning for a signal
    r"""
     /\___/\
    ( o   o )   >> scanning...
     )  Y  (    >> ears: antenna mod v2
    (   |   )
     \_____/
""",
    # original — single glowing cyber-eye, half the face in shadow
    r"""
      .-=====-.
     ( [0]  .. )
      '-==Y==-'
       |  |  |
   ...picking through the neon rain...
""",
    # original — crouched, tail plugged into a data jack
    r"""
        /\_/\
       ( -.- )
        > ^ <
   ~~~~~~|||~~~~~~[DATA JACK: LINKED]
""",
    # original — startled by a drone, fur on end
    r"""
     /\/\_/\/\
    (  O   O  )
     \  ^Y^  /
      )=====(      -- ears up, rotor incoming --
""",
    # original — two cats, backs to a chain-link fence, skyline behind
    r"""
   ___                                  ___
  /___\   [] [] [] [] [] [] [] []    /___\
  ( ..)\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/(.. )
   '''                                '''
""",
    # original — low battery / hunger indicator blinking
    r"""
   /\_/\        [ ENERGY: LOW ]
  ( >.< )       [ ]  [ ]  [ ]  [ ]
   > ~ <        one bar left, keep moving
""",
    # original — glitch/static burst, cat barely visible through interference
    r"""
  ░▒▓ /\_/\ ▓▒░
  ░▒▓( o█o )▓▒░   -- signal interference --
  ░▒▓ > ▓ < ▓▒░
""",
    # original — perched on a ledge above the city, tail hanging over the edge
    r"""
        ,--.
       ( o.o)__
        '--'   \___
                 \  \__/\_/\
                  \_(  o.o  )
                     > ^ < (watching the towers blink)
""",
    # user-provided — kaomoji, ears back
    r"""
へ  ♡  ╱|、
         ૮  >  <)     (˚ˎ 。7
          /  ⁻  ៸|       |、˜〵
     乀(ˍ, ل ل      じしˍ,)ノ
""",
    # user-provided — cat in a data-frame border
    r"""
•.,¸,.•*`•.,¸¸,.•*¯.——————.
•.,¸,.•*`•.,¸¸,.•*¯| : : : : :/\____/\
•.,¸,.•*`•.,¸¸,.•*¯|: : : : :( ｡OωO｡)
•.,¸,.•*`•.,¸¸,.•*¯ し——し——Ｊ
""",
    # user-provided — kaomoji, mid-meow
    r"""
        /⸌ —⸍\
     =(˶•ㅅ•˵)=      ᵐᵉᵒʷ
　 l       ~乀   ╭
    し しf_, )ノ
""",
    # user-provided — kaomoji under a starfield
    r"""
┊         ┊       ┊   ┊   ┊。 ┊
┊         ┊       ┊   ⋆   ˚★⋆｡˚  ⋆
┊         ┊       ★⋆ ◦
★⋆       ┊ .  ˚
           ˚★
☆ ∧,,,∧
ପ(„• ༝ •„)ଓ
┏━∪∪━━━━━━━━━━━
""",
    # user-provided — cat framed in a broken screen/monitor, stars scattered around
    r"""
                  ☆
☆  --------------
  /__________ \         ☆
 |                       |
 \___________ /                                  ☆
   \.._______../
    |   /\__/\   |
    | ( •    •    ) |   ☆                     ☆
    | / U  U  \  |
    =========
     \________/.
                               ☆                           ☆

   ☆                                         ☆
                     ☆                               ☆
""",
    # user-provided — kaomoji, diagonal lean
    r"""
                              ╱|、
                         =(˚˕ 。 7
                             |、 ~〵
                            じし   ˍ,)づ
""",
    # user-provided — cat + "we live in a society" box meme
    r"""
)     /\__/\
( =/   • •   \=
-------U-U-----------------
|                                |
|    we live in a society        |
|                                |
------------------------------
""",
    # user-provided — kaomoji, heart-eyed
    r"""
.      ∧,,,,∧,,,,,,,∧
     (  _  _ )⩊^ )~♡
     /      ⊂      \
""",
    # user-provided — kaomoji, small flower nose
    r"""
    /\,,,/\
>(  • . •   )<
  / >❀<  \
""",
]


# ASCII_CATS_TAGGED — a second, separate library used for topic-relevant
# ASCII breaks: instead of picking any random cat, the generation tasks can
# pick from here based on what the current rant/turn is actually about (a
# specific Meowizen's signature object, or a recurring dystopia motif).
# Each entry is hand-drawn and checked for alignment ahead of time, same
# quality bar as ASCII_CATS above — this list exists so topical relevance
# doesn't come at the cost of quality. Kept as a separate list (not merged
# into ASCII_CATS) since build_site.py's decor/gallery/screensaver features
# expect ASCII_CATS to stay a flat list of general-purpose cat art; this one
# is for the generation tasks to consult directly, tags and all.
ASCII_CATS_TAGGED = [
    {
        "tags": ["valentuna", "fridge", "marriage", "smart fridge", "romance"],
        "art": r"""
 ________
|  []    |
|--------|
|  []  ♥ |
|________|
""",
    },
    {
        "tags": ["byte", "wifi", "router", "hacking", "server", "signal"],
        "art": r"""
      )))
     )) ))
    [ROUTER]
    |__||__|
""",
    },
    {
        "tags": ["snooze", "sleep", "dream", "pod", "billing", "nap"],
        "art": r"""
   .-----.
  /  zzz  \
 |_________|
 |[BILLED] |
 '---------'
""",
    },
    {
        "tags": ["happyware", "positivity", "smile", "corporate", "mandatory"],
        "art": r"""
   .-----.
  ( ^   ^ )
   \  -  /
    -----
 [SMILE: MANDATORY]
""",
    },
    {
        "tags": ["brik", "vent", "demolition", "killdozer", "grate"],
        "art": r"""
  [###]
  [###]
  [###]  <- home
  [###]
""",
    },
    {
        "tags": ["popup", "ad", "implant", "eye", "retina", "advertisement"],
        "art": r"""
   ____
  /    \
 | (AD) |
  \____/
    ||
 [ POPUP ]
""",
    },
    {
        "tags": ["shade", "sunglasses", "based", "surveillance", "seized"],
        "art": r"""
  _________
 |■       ■|
  ‾‾‾‾‾‾‾‾‾
    BASED
""",
    },
    {
        "tags": ["glitchmeat", "neural", "chip", "glitch", "bluetooth", "memory"],
        "art": r"""
  .-[CHIP]-.
  | + + + + |
  '---------'
     glitch~
""",
    },
    {
        "tags": ["query", "settings", "terms", "tos", "menu", "agreement"],
        "art": r"""
  [ SETTINGS ]
  [ ] option 1
  [ ] option 2
  [ ] ... (pg 247)
""",
    },
    {
        "tags": ["knifeboy", "tuna", "bounty", "wanted", "reward"],
        "art": r"""
  ___________
 | WANTED:   |
 |  KNIFEBOY |
 | 40,000 pts|
 |___________|
""",
    },
    {
        "tags": ["drone", "rotor", "surveillance", "patrol", "scan"],
        "art": r"""
   \   /
    \ /
   --o--
    / \
   /   \
""",
    },
    {
        "tags": ["vending", "machine", "kibble", "subscription", "snack"],
        "art": r"""
   _______
  |[A1][A2]|
  |[B1][B2]|
  |___[$]__|
""",
    },
    {
        "tags": ["loyalty", "tier", "card", "clawcoin", "nekocorp", "points"],
        "art": r"""
  .------------.
  | NEKOCORP   |
  | TIER: NONE |
  '------------'
""",
    },
]
