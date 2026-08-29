import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ascii_cats import ASCII_CATS_TAGGED

def art(tag):
    for e in ASCII_CATS_TAGGED:
        if tag in e["tags"]:
            return e["art"]
    raise SystemExit("no tag " + tag)

conv_id = "conversation-cyberpunk_cats-1788023889-2a20d0"
started = "2026-08-29T17:18:09+00:00"

L1 = "lm1"
L2 = "lm2"

def cat(t): return {"actor": "lm1", "model": "nekocorp-sim", "text": t}
def city(t): return {"actor": "lm2", "model": "nekocorp-sim", "text": t}
def ascii_turn(t): return {"actor": "ascii", "text": t}

turns = [
    cat(
        "Someone crossed the line. *nose down at the seam where the wet concrete of the "
        "underpass gives way to the dry strip i keep, the boundary re-marked three dusks "
        "running* the mark's been walked over. fresh. a stranger's spray laid right on "
        "top of mine — sour, all fear and hot machine-oil, not a challenge, just something "
        "moving through fast and scared. *ears go flat, not at the scent but at what's past "
        "it: the wide sweeping glare out at the mouth of the tunnel, the light that wants to "
        "count me* whoever ran, they ran toward the bright. amateurs run toward the bright. "
        "*settles lower into the cool dark, the world behind my eyes gone soft and grey and "
        "quiet here, no colors screaming numbers at me*"
    ),
    city(
        "the dark holds. good dark. down here the glare can't reach past the second pillar and "
        "it knows it, sulks at the tunnel-mouth throwing its long white arms across wet road and "
        "giving up. the stranger's trail is a thin bright thread through all that grey — "
        "oil, fear, and under it something scorched, fur that's been too near a flame more than "
        "once, a smell the older strays back away from. it goes east, toward the light, toward "
        "the plaza where the signs live. from up there a jingle leaks down warped and slow: "
        "*neko... corp... loves... you... (you... you... you...)* the pads of your feet feel it "
        "before your ears do — a soft repeating tremor in the concrete, patient, rotor-shaped."
    ),
    cat(
        "the scorched one i know of. not a threat, a warning-shape — the kind that bites the "
        "flying eyes for sport. i let that thread go. *turns away from the east, from the bright, "
        "keeping my flank to the cold pillar, following my OWN line back along the dark seam "
        "instead* the tremor in the pads matters more than any stranger. i go still against the "
        "stone, low, chin nearly to the wet, and i wait for the rotor to decide where it's "
        "looking. *the grey behind my eyes is a mercy here — nothing flashes a price at me, "
        "nothing tries to sell the dark to me*"
    ),
    city(
        "smart. the flame-cat's scent thins and is gone, off to fight its own war with the sky. "
        "the tremor swells. it rounds the tunnel-mouth without hurry — a squat drone, underbelly "
        "lit soft blue, a single lens sweeping slow, and stitched to its chatter a thin rumor-tone "
        "broadcast on loop: *...reward adjusted... forty thousand points... subject: small, quick, "
        "leaves notes... do not approach the tuna...* the searchlight lays a cold bar of white "
        "across the first pillar, then the second, crawling toward the third — the one your "
        "whiskers are pressed behind."
    ),
    ascii_turn(art("drone")),
    cat(
        "*not one hair moves. breath pulled shallow and slow, eyes narrowed to slits so even the "
        "wet shine of them won't answer the light* the bar of white touches the edge of my pillar "
        "— i feel it as warmth on the very tips of the whiskers, and every muscle turns to "
        "stone-that-could-spring. the loop-voice means nothing to me, just weather, just the city "
        "talking to itself again. i am not small-quick-leaves-notes. i am nothing. i am a colder "
        "part of the cold wall. *wait. wait. let the eye pass.*"
    ),
    city(
        "the lens lingers on the pillar's edge — one heartbeat, two — reading cold where it hoped "
        "for warm. finding a wall that is only a wall. it moves on. the white bar slides off your "
        "whiskers, sweeps the empty dark beyond, and the drone tilts back toward the plaza, its "
        "rumor-loop fading up the ramp: *...do not approach... do not... do...* the tremor "
        "shrinks out of the concrete. in the hush it leaves behind, a new thing arrives low and "
        "close: a smell of grease and warm protein, food-heat, wafting from a dented hatch in the "
        "underpass wall you've never seen open before."
    ),
    cat(
        "*the stone melts out of me all at once, a long silent shiver down the spine, and then "
        "the belly speaks louder than the caution ever did.* grease. warm. real, not the "
        "flat sweet lie the signs sell. *up onto the pads, weightless, one paw testing the wet "
        "ahead of the other, moving toward the hatch along the base of the wall where the shadow "
        "pools deepest* i keep the grey dark wrapped around me. i do not step where the tunnel-mouth "
        "can see. hunger, yes — but hunger walking careful, hunger with its ears still turning."
    ),
    city(
        "the hatch breathes out heat and noise — behind it, past a curtain of hanging cable, a "
        "low-lit den: cats bent over a cracked terminal that flickers black-market blue, the air "
        "thick with fish-oil and hot circuitry and the ozone bite of something overclocked. a "
        "cat near the doorway sits very upright, unmoving, two flat mirrored discs where its eyes "
        "should be catching the terminal-glow and throwing it back doubled — watching the room, "
        "watching the door, watching you arrive without turning its head. the food-heat comes from "
        "a split ration-tin just inside the threshold. unguarded. or meant to look it."
    ),
    cat(
        "*i stop at the very edge of the light-spill, one paw lifted, and i read the room the only "
        "honest way — by the set of that still one's shoulders.* the mirrored one isn't eating. "
        "isn't blinking. sits where the door and the tin can both be kept in one gaze — that's not "
        "rest, that's a toll being taken. the tin is bait, or it's rent, and either way it's owed "
        "to something. *my tail lowers. the belly whines but the ears win.* i do not walk into a "
        "warm that someone is guarding this calmly. i take the smell of it — just the smell — "
        "and i back out slow, keeping my good flank to the wall, giving no throat to the room."
    ),
    ascii_turn(art("shade")),
    city(
        "the mirrored one lets you go. no sound, no move — only, as you back into the dark, both "
        "flat discs tip a half-degree to follow, the way the tunnel-glare followed but colder, "
        "more patient, almost like respect. the den's blue light swallows shut behind the cable "
        "curtain. the underpass takes you back: cool stone, your own faded line under paw, the "
        "rain starting up beyond the mouth in a soft grey static that eats the plaza's jingle "
        "whole. the boundary is still yours. the night is still long. somewhere east a flame-cat "
        "is biting the sky, and somewhere up-ramp a lens is still looking for someone small and "
        "quick — but not here, not for you, not tonight."
    ),
    cat(
        "*i find the deep angle where two walls lean and the dark is thickest, and i fold down "
        "into it, spine to cold stone, chin on paws, the grey mercy settled soft over my eyes.* "
        "hungry still. that's fine. hungry and unseen beats fed and counted. *the rain-static "
        "hushes the whole tunnel and i let it, ears finally slowing, one turning lazy toward the "
        "east out of old habit, the other already gone to sleep* my line holds. the light never "
        "got its number. *the last thing before the dark takes me is the taste of grease still "
        "ghosting on the air, and i let even that go —* ^C^C"
    ),
]

data = {
    "id": conv_id,
    "template": "cyberpunk_cats",
    "model1": "nekocorp-sim",
    "model2": "nekocorp-sim",
    "started_at": started,
    "note": "Authored by a single scheduled automated session playing both roles in one pass (scheduled automation, runs every hour) — not two independent live API calls like a manual `python backrooms.py` run.",
    "turns": turns,
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), conv_id + ".json")
with open(out, "w") as f:
    json.dump(data, f, indent=2)
print("wrote", out, "turns:", len(turns))
