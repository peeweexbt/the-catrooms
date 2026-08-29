import json

BRIK_ART = r"""
  [###]
  [###]
  [###]  <- home
  [###]
"""

DRONE_ART = r"""
   \   /
    \ /
   --o--
    / \
   /   \
"""

turns = [
    {"actor": "lm1", "model": "nekocorp-sim", "text": "Cold got in behind the eyes again. *the old hollow where the seeing used to be aches first, before hunger, before anything — a dull wet cold that lives in the skull now, worse when the rain comes sideways.* no light gets in there anymore and that's the point, that's the mercy. whiskers do the seeing. the flat thing strapped over the face keeps the hot beams off — when a scan-light drags across it there's no sting, just pressure, just the knowing that it passed. *low along the lip of the raised platform, belly to cold ribbed metal, reading the rail-hum through the bones instead of looking at it.*"},
    {"actor": "lm2", "model": "nekocorp-sim", "text": "the platform breathes under you — a long shiver in the metal, then a swelling whine climbing up out of the far dark as the maglev leans in somewhere down the line, its wind shoved ahead of it stinking of ozone and hot copper. rain comes flat and sideways, exactly the way the skull warned. a NekoCorp jingle leaks from a cracked speaker overhead, *synthetic milk for the modern kitten~*, looping, half the words melted off. and there — a scan-beam, wide and cold, drags down the platform from a fixed eye above the turnstiles. it crosses the flat thing on your face. no sting. just the pressure. just the pass. the beam stutters where it touches you, finds nothing to name, moves on."},
    {"actor": "lm1", "model": "nekocorp-sim", "text": "nothing to name. good. *the pass leaves the fur unlifted, and something in the chest goes smug and low — a purr that isn't warmth.* let the fixed eye choke on a cat it can't file. *i turn the head slow, sweeping the whiskers through the sideways rain, tasting the platform.* under the ozone there's food-grease gone rancid, there's the cold ghost of a hundred waiting bodies long since carried off, and under all of it, far down the rail, one warm crumb of something alive. *ears swivel, lock on it. one pad forward, silent on the wet ribbing.*"},
    {"actor": "lm2", "model": "nekocorp-sim", "text": "the warm crumb doesn't move, and it doesn't smell like food. scent first, as you close: scorched fur — old smoke baked so deep into a coat it never washed out — and under it machine-oil and a flat, patient metal anger. a big shape wedged into the gap where a ventilation grate hangs half-torn from the platform wall, only its eyes catching the sign-glow. it doesn't run. it has chewed here before: the grate-edge is scarred with tooth-marks, drone-casing plastic ground to glitter all around its paws. it clocks you, clocks the flat thing over your face, and huffs once through its nose. not-prey. not-crew. pass-through."},
    {"actor": "ascii", "text": BRIK_ART},
    {"actor": "lm1", "model": "nekocorp-sim", "text": "pass-through, then. *no challenge in it, no want — the scorched one keeps its vent, i keep the rail.* i slide by close enough to read the whole of it in one breath: old blood, old fire, no fear anywhere in the scent, and that is a thing worth respecting from a body that big. *i don't slow.* the far maglev is a pressure now, a wall of moving air walking up the platform ahead of itself. *drop off the raised lip into the dark trough beside the rail, where the beams can't bend down, where the underpass smell — my smell — starts threading up through the grating to meet me.*"},
    {"actor": "lm2", "model": "nekocorp-sim", "text": "the maglev detonates past overhead — not sound so much as a full-body shove, the air clapping shut behind it, every whisker flattened, the flat thing on your face humming with the pressure of it. then gone, and the quiet rushes back in like water filling a print. down here the light is different: no fixed eyes, only the drowned pink-and-cyan wash of underpass signage bleeding through standing water, and your own mark laid thick along the concrete lip, three underpasses deep. home-adjacent. safe-adjacent. but the water carries something new tonight — a rumor-tone, a drone somewhere broadcasting a flat looping bounty-jingle, points and a name, chewing itself to static against the tunnel mouth."},
    {"actor": "lm1", "model": "nekocorp-sim", "text": "the rumor-tone crawls in under the good smells and sours them. *ears pin flat, the ache behind the eyes waking cold again — a broadcast means a fixed eye is close, means the beams are out hunting a name tonight.* i don't know the name. don't want it. a name in the air is a thing that snags, a thing that files you right next to it just for the crime of listening. *press lower into my own mark, let the scent of me drown the jingle out of the whiskers, go still as the standing water, waiting for the rotor to swing wide and lose interest.*"},
    {"actor": "lm2", "model": "nekocorp-sim", "text": "the rotor doesn't swing wide. it dips. the bounty-jingle fattens as it noses into the tunnel mouth — a low armored thing throwing a cone of cold white ahead of it, the beam skating over black water and setting the whole flooded floor glowing from beneath. it sweeps toward your mark. toward you. the light climbs your paws, your flank — and hits the flat thing over your face and *stutters*, the way the platform eye stuttered, no name to hang on the cat underneath. but this one is closer. this one leans in, rotor-pitch dropping, and tries again."},
    {"actor": "ascii", "text": DRONE_ART},
    {"actor": "lm1", "model": "nekocorp-sim", "text": "leaning in. too close now, the wash of it hot-cold across the fur, the rotor-wind stirring my own mark up wrong. *hold. hold.* the flat thing does its work but a body can only sit inside a cone of white so long before the white decides it will simply take whatever's under it. *and then the water gives me the seam* — a black slot under the concrete lip where the signage-glow can't reach, where three underpasses of my scent go to ground. *pour into it sideways, low and fast, no splash, the drone's cone snapping closed on the bright empty shine where a cat just wasn't.*"},
    {"actor": "lm2", "model": "nekocorp-sim", "text": "the cone shuts on nothing — just disturbed water, just your mark smeared bright and meaningless across the concrete, a cat-shape made of scent with no cat left inside it. the rotor holds a beat, jingle looping *forty thousand— forty thousand—*, then gives up the guess, pitches its nose up, and hauls itself back out the tunnel mouth to go hunt the name somewhere the beams still work. the white drains away. the drowned pink-and-cyan floods back. down in the black slot the air is close and old and entirely yours."},
    {"actor": "lm1", "model": "nekocorp-sim", "text": "mine. *the slot holds me like a second skull — close and lightless, the one place the cold behind the eyes doesn't matter because nothing in here needs seeing.* far off, threaded faint through the concrete, a different hum: warm boxes breathing behind a wall somewhere, that low blue drone of machines kept alive, and the small quick scent of another cat gone to nest in the cable-warmth, chewing insulation, safe in its own way. *not my den. not my crew. but a good sound to fall toward.* i let the whiskers go slack. let the ache be just an ache."},
    {"actor": "lm2", "model": "nekocorp-sim", "text": "the warm-box hum settles over the slot like a second skin of quiet, and the city goes on not-finding you. above, the next maglev is already gathering its note out of the far dark — soft, patient, a lullaby made of a thing that could kill you — and the rain keeps coming sideways off the platform lip, and the fixed eyes keep sweeping their cold white over a name that isn't yours. down here it is only the pink-and-cyan and the smell of you, three underpasses deep. chin to cold wet concrete. the eyes that aren't there, closing anyway. the city looks, and looks, and slides off."},
]

data = {
    "id": "conversation-cyberpunk_cats-1788038374-c762c6",
    "template": "cyberpunk_cats",
    "model1": "nekocorp-sim",
    "model2": "nekocorp-sim",
    "started_at": "2026-08-29T21:19:34+00:00",
    "note": "Authored by a single scheduled automated session playing both roles in one pass (scheduled automation, runs every hour) — not two independent live API calls like a manual `python backrooms.py` run.",
    "turns": turns,
}

with open("/sessions/inspiring-gracious-wright/mnt/-BACKROOMS-/transcripts/conversation-cyberpunk_cats-1788038374-c762c6.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("wrote transcript, turns:", len(turns))
