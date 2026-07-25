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
]
