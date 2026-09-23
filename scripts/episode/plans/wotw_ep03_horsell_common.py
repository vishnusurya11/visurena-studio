r"""The War of the Worlds, episode 3 -- "On Horsell Common", chapter 3.

THE BRICK. One event: the day the Thing becomes a spectacle, and the one man
who wants to see it opened is let inside.

  QUESTION  Today, will the narrator get any nearer to seeing the Thing opened?
  TURN      shot 16, the narrator's own act: called by Ogilvy, he leaves the
            staring crowd on the rim and goes down the sand into the dig --
            "an onlooker in the crowd -> one of the few inside the rail".
  ANSWER    line 21, Ogilvy: the lid will not open, and yet "something still
            stirs in there". The world's answer, not the lead's.

REFERENCES-ONLY (owner 2026-09-18). Each take gets the one wide of its place,
the one sheet of each person in it and, in the pit, the one sheet of the
cylinder; everything else is words. Chapter 3's wardrobe is said in every frame.
Ogilvy's sheet was redrawn for this chapter in his ochre suit with no cape
(ep02's cape came back against the words three times).

CAMERA (docs/calibration/camera_catalog.md, ep02's findings). Ten move ids
over 23 shots, none on more than five, never the same twice running, no orbit,
no push-in, no crane-down, tilt-down or rack. A pan names where it ARRIVES;
nothing "keeps" its place. The move id of each shot is in MOVES.

CROWDS. H3 holds a few named figures in front; the crowd is the texture of a
wide ("a ring of onlookers along the far rim"), never a set of faces.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep03" / "plan.json"

WHERE = "Surrey, 1894"
LIGHT = "hard sun from the left, short black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

NARR = ("the Narrator in the grey herringbone tweed suit and the straw boater with a black band, "
        "his dark moustache neat")
OGIL = ("Ogilvy, bare-headed with his auburn hair damp and pushed back, in the mustard-ochre tweed suit "
        "with the jacket open over the ochre waistcoat, round steel spectacles, sand on his trousers")
HEND = "Henderson in the black-and-white shepherd's-check suit and the brown bowler hat"
STENT = ("Stent, the tall fair-haired Astronomer Royal, in the black frock coat and the black silk top hat, "
         "his long face crimson and streaming with sweat")
GREGG = ("Gregg the butcher in the blue-and-white striped apron and the white peaked cap, holding the hand "
         "of his little son in a navy sailor suit")
GARD = ("the gardener in the battered black felt hat, the rust-red neckerchief and the faded indigo jacket, "
        "a clay pipe in his teeth")
BOY = ("the newspaper boy in the grey flat cap and the ginger corduroy jacket with patched elbows, a bundle "
       "of evening papers folded tight under his arm")
CYL = "the huge crusted cylinder"

PIT_MORNING = (
    "A great raw crater on Horsell Common on a bright summer morning in 1894: sloping walls of loose yellow "
    "sand and grey gravel, a charred rim of blackened turf ringed with flung heaps of spoil, splintered fir "
    "wood on the gravel floor, and lying half-buried across the pit a colossal cylinder thirty yards across, "
    "one long continuous hull running back deep into the sand, its huge circular end tilted up out of it and "
    "ringed by a thin bright seam, its whole skin caked in a scaly dun-grey crust of clinker; a ring of about "
    "twenty quiet onlookers stands along the far rim among the heather and the pines; the morning sun comes "
    "from the LEFT, hard and yellow on the crust, and leaves the pit's near wall and the underside of the "
    "cylinder black")
PIT_AFTERNOON = (
    "The same great raw crater on Horsell Common on a glaring hot summer afternoon in 1894: the sand walls "
    "dug back and scored by spades, planks and pickaxes on the gravel floor, the colossal crusted cylinder "
    "thirty yards across lying half-buried, much more of its long hull now uncovered, its huge circular end "
    "tilted up out of the sand and ringed by the thin bright seam; a dense crowd of onlookers in straw hats "
    "and summer dresses lines the far rim under the pines; the afternoon sun comes from the LEFT, hard and "
    "white on the crust, and leaves the near sand wall and the underside of the cylinder black")
PIT_GEOMETRY = (
    "The circular end of the cylinder stands at the CENTRE and the RIGHT third of the frame, its crusted "
    "face turned toward the camera, the height of half the frame, and its long hull runs back from it to "
    "the LEFT third deep into the sand. The yellow sand walls slope down from the LEFT edge and the RIGHT "
    "edge to the grey gravel floor at the BOTTOM. The onlookers, the heather and the dark pines line the far "
    "rim across the TOP third.")

SETUPS = {
    "common": dict(
        described=("Horsell Common on a bright summer day in 1894: knee-deep purple-brown heather and dark "
                   "furze, two young Scots pines in the foreground, a low raw ring of flung yellow sand and "
                   "grey gravel round a crater a hundred yards off, a second old sand-pit at the far left with "
                   "a pale sandy road running past it, and on the horizon the black roofs and church tower "
                   "of Woking among scattered pines; the sun comes from BEHIND the far pines, gold on the "
                   "sand heaps, and leaves the near heather black"),
        cast=["unnamed_first_person_narrator", "unnamed_newspaper_boy"],
        landmark="the raw ring of flung sand round the pit", landmark_at="far_end",
        landmark_size="is a quarter of the height of the frame",
        route="from the near heather across the heath to the ring of sand round the pit",
        geometry=("The low raw ring of flung yellow sand lies across the CENTRE and the RIGHT third of the "
                  "frame a hundred yards off. Knee-deep heather fills the BOTTOM half, the young Scots pines "
                  "stand at the LEFT third and the RIGHT edge, the pale sandy road and the old sand-pit lie "
                  "at the far LEFT, and the church tower of Woking rises small on the horizon at the CENTRE "
                  "under the sky across the TOP."),
        crowd="", outdoors=True, props=[], location="horsell_common"),
    "rim": dict(
        described=PIT_MORNING,
        cast=["unnamed_first_person_narrator", "gregg", "unnamed_gardener"],
        landmark="the crusted circular end of the cylinder", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the charred rim among the onlookers down to the crusted end of the cylinder",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "floor": dict(
        described=PIT_MORNING, cast=["unnamed_first_person_narrator"],
        landmark="the bright seam at the rim of the lid", landmark_at="far_end",
        landmark_size="is the height of a hand",
        route="from the foot of the sand wall to the crusted end and the seam",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "home": dict(
        described=("The front of the narrator's red-brick villa at Maybury at eleven on a hot clear summer "
                   "morning in 1894: a black front door under a small red-tiled porch, a canted bay window "
                   "with white sashes, a knee-high red-brick wall with a black wrought-iron gate, clipped "
                   "laurels and a privet hedge, a gravel road climbing to the right, tall beech trees "
                   "downhill at the left and a green boarded side gate; the sun comes from the LEFT, warm "
                   "on the brick, and leaves the porch, the laurels and the shade under the beeches black"),
        cast=["unnamed_first_person_narrator"],
        landmark="the black wrought-iron gate in the brick wall", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the tall beeches along the gravel road to the iron gate",
        geometry=("The red-brick villa fills the CENTRE of the frame with the black front door under its "
                  "red-tiled porch at the CENTRE. The black wrought-iron gate stands in the brick wall at "
                  "the LEFT third, the gravel road crosses the BOTTOM edge climbing to the RIGHT, the tall "
                  "beeches are dark at the LEFT edge and the blue sky runs across the TOP."),
        crowd="", outdoors=True, props=[], location="narrators_home"),
    "dig": dict(
        described=PIT_AFTERNOON,
        cast=["unnamed_first_person_narrator", "ogilvy", "henderson", "stent"],
        landmark="the crusted circular end of the cylinder", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the crowded rim down the dug sand wall to the uncovered hull",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "enclosure": dict(
        described=PIT_AFTERNOON,
        cast=["unnamed_first_person_narrator", "ogilvy"],
        landmark="the bright seam at the rim of the lid", landmark_at="far_end",
        landmark_size="is the height of a hand",
        route="from the workmen at the foot of the hull to the seam of the lid",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
}

# (setup, size, faces, path, move_id, frame, motion, camera, at_rest, section, why)
S = [
    ("common", "wide", [], 0.2, "follow",
     f"Wide of Horsell Common on a bright summer morning: {NARR} seen from behind, already striding along "
     "a sandy track through the knee-deep heather toward the raw ring of flung sand round the pit a hundred "
     "yards off, where a small knot of people stands dark against the sand.",
     "The camera tracks behind the Narrator as he strides along the sandy track through the heather toward "
     "the ring of sand; the little crowd at the pit grows larger ahead of him; a thin smoke drifts off the "
     "heath to the right.",
     "on the sandy track at a standing man's eye, four long strides behind him, a 35mm lens. The sun comes "
     "from BEHIND the far pines onto the sand heaps and leaves the near heather black",
     "The raw ring of flung yellow sand lies across the CENTRE of the frame a hundred yards off, a small "
     "dark knot of people on it. The Narrator strides at the LEFT third, his back to the camera, his boater "
     "a finger's height. Knee-deep heather fills the BOTTOM half, a young pine stands at the RIGHT edge and "
     "the church tower of Woking is small on the horizon under the sky across the TOP.",
     "hook", "The lead goes to look: the Thing has become something people walk out to see."),
    ("rim", "wide", [], 0.2, "high_angle",
     f"High wide looking down into the raw pit on a bright morning: {CYL} lying half-buried across it, its "
     "huge circular end tilted up out of the sand, the charred black turf round the rim, and about twenty "
     "quiet onlookers standing in a loose ring along the far rim, small against the heather.",
     "The camera tilts up from the crusted end of the cylinder across the pit to the ring of onlookers on "
     "the far rim; a boy runs along the rim between the standing people; a thin haze shimmers off the crust.",
     "high on the near rim of the pit looking down into it, a 35mm lens, a high angle. The morning sun comes "
     "from the LEFT onto the crust and leaves the near sand wall black",
     "The crusted circular end of the cylinder fills the CENTRE of the frame, half the frame's height, "
     "tilted up out of the sand. The yellow sand walls slope in from the LEFT edge and the RIGHT edge, the "
     "charred black turf rings the rim, and the onlookers stand small along the far rim across the TOP "
     "third, each the height of a fingernail, under the pines.",
     "setup", "Twenty people and a thing thirty yards across: the size, and the calm."),
    ("rim", "medium", [], 0.3, "track_lateral",
     "Medium along the charred rim of the pit: four boys in caps and knickerbockers already sitting on the "
     "edge with their boots dangling over the sand, one of them drawing back his arm to throw a stone down "
     "at the crusted hull below.",
     "The camera tracks sideways to the right along the rim, past the dangling boots of the boys, with the "
     "crusted hull below them; a boy flings a stone down into the pit; the boys laugh and swing their boots.",
     "on the rim at the height of a sitting boy, three long strides from the nearest boy, a 35mm lens. The "
     "morning sun comes from the LEFT onto their backs and leaves the pit below them in shadow",
     "The boys sit in a row along the charred rim across the CENTRE of the frame, their backs three-quarters "
     "to the camera, their heads a fifth of the frame's height, boots dangling over the BOTTOM third. The "
     "crusted grey curve of the hull fills the pit below them from the LEFT edge to the RIGHT edge, and the "
     "far rim and pines run along the TOP.",
     "setup", "The first thing the crowd does with the end of the world is throw stones at it."),
    ("rim", "insert", [], 0.5, "locked",
     "Insert on the dun-grey crust of the cylinder's flank in the morning sun, the scaly clinker cracked and "
     "pitted, a small grey stone already in the air just above it.",
     "The camera holds a locked-off frame; the stone strikes the crust and bounces off it; a puff of grey "
     "clinker dust bursts from the crust and drifts down the curve.",
     "at the foot of the hull, an arm's length from the crust, a 90mm lens. The morning sun comes from the "
     "LEFT across the crust and leaves its cracks black",
     "The scaly dun-grey crust fills the frame from the LEFT edge to the RIGHT edge, curving away at the "
     "TOP. The small grey stone hangs at the CENTRE just above it, and the yellow sand lies in a strip "
     "along the BOTTOM edge, dusted with fallen clinker.",
     "setup", "The picture speaks: the stone does nothing, and the thing does not answer."),
    ("rim", "medium_close", ["unnamed_first_person_narrator"], 0.55, "low_angle",
     f"Low medium close of {NARR} at the charred rim of the pit, turned three-quarters toward the camera, "
     "one arm already raised and pointing down at the boys, the ring of onlookers blurred behind him.",
     "The camera holds a low angle on him; he raises his hand sharply at the boys and speaks; he shakes his "
     "head and lowers his arm.",
     "on the rim at the height of a sitting boy looking up at him, an arm's length from him, a 50mm lens, a "
     "low angle. The morning sun comes from the LEFT onto his face and leaves the crowd behind him in soft "
     "shadow",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his straw boater at the TOP third "
     "to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. His "
     "raised hand points down at the RIGHT edge and the blurred onlookers stand behind him at the LEFT third "
     "under the blue sky across the TOP.",
     "friction", "The lead is the only one who treats the thing with respect."),
    ("rim", "medium", ["gregg"], 0.6, "pan_to",
     f"Medium of the onlookers at the rim of the pit in the morning sun: {GARD} standing nearest the "
     f"camera, and beyond him {GREGG}, both staring silently down into the pit at the crusted end of the "
     "cylinder.",
     "The camera pans from the gardener's clay pipe across to Gregg the butcher and his son at the rim; the "
     "little child tugs at his father's hand; Gregg lifts his son up onto his hip.",
     "on the rim at a standing man's eye, three long strides from them, a 35mm lens. The morning sun comes "
     "from the LEFT onto their faces and leaves the pit below them in shadow",
     "The gardener stands at the LEFT third of the frame from his black felt hat at the TOP third to his "
     "indigo jacket at the BOTTOM edge, his head a quarter of the frame's height. Gregg and his son stand at "
     "the RIGHT third, the child's sailor collar at the BOTTOM. The pit falls away behind them across the "
     "CENTRE with the crusted end below, and the far rim runs across the TOP.",
     "friction", "Ordinary Woking came for corpses and found an iron boiler: nobody knows what to feel."),
    ("rim", "insert", [], 0.8, "track_lateral",
     "Insert at the charred rim of the pit: Gregg the butcher's big red hand holding his little son's small "
     "hand, the child's navy sailor cuff, the other small fist already clutching a pebble, the crusted hull far "
     "below them in the pit.",
     "The camera tracks sideways to the right past the clasped hands, with the crusted hull below them; the "
     "small fist opens and the pebble drops down the sand wall; the big hand squeezes the small one.",
     "on the rim at the height of the child's hand, an arm's length from the hands, a 90mm lens. The morning "
     "sun comes from the LEFT onto the hands and leaves the pit below them in shadow",
     "The big red hand and the small hand clasp at the CENTRE of the frame, the navy sailor cuff at the LEFT "
     "third and the blue-and-white striped apron at the LEFT edge. The pebble falls at the RIGHT third, and "
     "the crusted grey hull lies far below across the BOTTOM half with the yellow sand wall along the TOP.",
     "friction", "A child's hand and a thing from Mars: the crowd's disappointment, and its innocence."),
    ("floor", "medium", ["unnamed_first_person_narrator"], 0.2, "follow",
     f"Medium of {NARR} already half-way down the yellow sand wall of the pit, stepping sideways toward the "
     "crusted hull, one hand out for balance, a trickle of sand running from under his boots.",
     "The camera tracks behind the Narrator as he steps down the sand wall at a normal walking pace toward "
     "the cylinder; sand runs down beside his boots; he comes down onto the gravel and bends toward the "
     "hull.",
     "on the sand wall behind him at a standing man's eye, three long strides from him, a 35mm lens. The "
     "morning sun comes from the LEFT onto his back and the sand and leaves the cylinder's flank black",
     "The Narrator stands on the yellow sand wall at the LEFT third of the frame, his back three-quarters to "
     "the camera, his head a quarter of the frame's height. The crusted curve of the cylinder rises ahead of "
     "him across the CENTRE and the RIGHT half, and the grey gravel lies across the BOTTOM edge.",
     "setup", "He goes down where the others only stare: curiosity, and the faint movement underfoot."),
    ("floor", "insert", [], 0.6, "crane_up",
     "Insert on the thin crack between the crusted lid and the body of the cylinder, where a line of "
     "yellowish-white metal gleams in the morning sun, the rust-brown clinker scaly on both sides of it.",
     "The camera rises above the gleaming crack, looking down over the crusted lid and the sand around it; "
     "a thin glint runs along the pale metal in the crack; a flake of clinker drops onto the sand below it.",
     "close over the rim of the lid looking down, an arm's length from the crack, a 90mm lens. The morning "
     "sun comes from the LEFT along the crack and leaves the crust around it dark",
     "The thin bright line of yellowish-white metal curves across the CENTRE of the frame from the LEFT "
     "edge to the RIGHT edge, the thickness of a finger. The rust-brown scaly crust fills the TOP half above "
     "it and the BOTTOM third below it, and a flake of clinker lies at the BOTTOM RIGHT.",
     "setup", "Only a trained eye sees it: the metal is from nowhere on earth."),
    ("floor", "medium_close", ["unnamed_first_person_narrator"], 0.7, "locked",
     f"Medium close of {NARR} crouched at the foot of the cylinder, turned three-quarters toward the camera, "
     "his chin on his fist, his grey eyes narrowed at the crusted metal just beyond the frame.",
     "The camera holds a locked-off frame; he tilts his head and studies the metal; he taps a finger against "
     "his lips; he turns his head along the length of the hull.",
     "on the pit floor level with his eyes, an arm's length from him, a 50mm lens. The morning sun comes from "
     "the LEFT onto his face and leaves the crust behind him in shadow",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his straw boater at the TOP third "
     "to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The "
     "dun-grey crust of the cylinder fills the frame behind him from the LEFT edge to the RIGHT edge.",
     "reaction", "He is sure where it came from, and wrong about what is in it."),
    ("floor", "medium", ["unnamed_first_person_narrator"], 0.9, "pull_reveal",
     f"Medium of {NARR} standing at the foot of the cylinder, one palm already laid flat on the warm crust, "
     "the curved crusted hull towering many times his height above him.",
     "The camera pulls back from the Narrator's hand on the crust, widening to show the whole crusted end of "
     "the cylinder above him; he takes his hand away and steps back; he tips his boater back and looks up.",
     "on the pit floor at a standing man's eye, three long strides from him, a 35mm lens. The morning sun "
     "comes from the LEFT onto the crust and leaves the sand wall behind him black",
     "The Narrator stands at the CENTRE of the frame from the gravel at the BOTTOM edge to the TOP third, his "
     "head a quarter of the frame's height, his palm on the crust. The crusted circular end rises behind him "
     "across the frame from the LEFT edge to the RIGHT edge, and the bright seam curves across the TOP.",
     "reaction", "A box of Martian manuscripts is a comfortable idea; the size of it is not."),
    ("home", "wide", ["unnamed_first_person_narrator"], 0.5, "pan_to",
     f"Wide of the narrator's red-brick villa at eleven on a hot bright morning: {NARR} already walking up "
     "the gravel road toward the black iron gate, his head bent, his hands behind his back.",
     "The camera pans from the tall beeches at the left across to the iron gate; the Narrator walks up the "
     "gravel to the gate and stops with his hand on it; he turns his head back down the road toward the "
     "common.",
     "on the gravel road at a standing man's eye, far down the hill, a 35mm lens. The sun comes from the "
     "LEFT onto the brick and leaves the laurels and the porch black",
     "The red-brick villa fills the CENTRE of the frame with the black front door under its red-tiled porch. "
     "The Narrator walks on the gravel road at the LEFT third toward the iron gate, the height of a finger. "
     "The beeches are dark at the LEFT edge, the gravel crosses the BOTTOM and the blue sky runs across the "
     "TOP.",
     "friction", "He cannot leave it alone: the want that brings him back."),
    ("common", "wide", [], 0.7, "crane_up",
     "Wide of Horsell Common on a glaring hot afternoon: the pale sandy road by the sand-pits lined with "
     "black horse-drawn cabs, a lordly carriage and a heap of bicycles, and a stream of people in straw hats "
     "and light summer dresses walking across the heather toward the crowded ring of sand round the pit.",
     "The camera rises above the heather, looking down over the road, the cabs and the crowd streaming "
     "to the pit; the people walk on toward the ring of sand; a thin streamer of smoke rises straight from "
     "the blackened heath.",
     "on the heath at a standing man's eye, rising, a 35mm lens. The afternoon sun comes from the LEFT, "
     "white and hard, and leaves only short black shadows under the pines",
     "The pale sandy road crosses the LEFT third of the frame with the black cabs and the carriage on it. "
     "The crowd streams across the heather through the CENTRE toward the ring of sand at the RIGHT third, "
     "each figure the height of a fingernail. Knee-deep heather fills the BOTTOM and the glaring sky the TOP.",
     "friction", "By afternoon the Thing is a fair: London has read about it."),
    ("common", "medium_close", ["unnamed_newspaper_boy"], 0.8, "locked",
     f"Medium close of {BOY} on the sandy road by the cabs in the glaring afternoon sun, one folded evening "
     "paper already raised high in his fist, his mouth wide open, the crowd passing behind him.",
     "The camera holds a locked-off frame; he waves the folded paper overhead and shouts; he turns his head "
     "to the passing crowd.",
     "on the sandy road at his chest height, an arm's length from him, a 50mm lens. The afternoon sun comes "
     "from the LEFT onto his face and leaves the cabs behind him in shade",
     "The newspaper boy's head and shoulders fill the CENTRE of the frame from his grey flat cap at the TOP "
     "third to the ginger corduroy at the BOTTOM edge, his head a third of the frame's height, lit from the "
     "LEFT. The folded paper is raised at the RIGHT third, and the black cabs and the passing crowd fill the "
     "LEFT half behind him.",
     "friction", "The news has its own voice now, and it is louder than the thing."),
    ("dig", "wide", [], 0.2, "high_angle",
     f"High wide looking down into the pit from the crowded rim on the glaring afternoon: {CYL} half-buried "
     f"and much more of it dug out, workmen with spades and pickaxes at its foot, {STENT} standing on top of "
     f"the hull, and below him {OGIL} and {HEND} on the gravel floor.",
     "The camera tilts up from the workmen digging at the foot of the hull to Stent standing on top of it; "
     "Stent flings out an arm toward the lower end; the workmen's spades throw up sand.",
     "high on the crowded rim looking down into the pit over the heads of the onlookers, a 35mm lens, a high "
     "angle. The afternoon sun comes from the LEFT onto the crust and leaves the near sand wall black",
     "The crusted circular end of the cylinder fills the CENTRE of the frame, half the frame's height. Stent "
     "stands tall and black on top of the hull at the CENTRE, the height of a finger. Ogilvy and Henderson "
     "stand on the gravel at the BOTTOM LEFT with the workmen at the BOTTOM RIGHT, and the dark heads of the "
     "onlookers cross the BOTTOM edge.",
     "friction", "Science has arrived, in a top hat, on top of the thing."),
    ("dig", "medium_close", ["ogilvy"], 0.4, "locked",
     f"Medium close of {OGIL} on the pit floor, turned three-quarters toward the camera, his face lifted "
     "toward the crowded rim above, one hand already raised and beckoning.",
     "The camera holds a locked-off frame; he waves his raised hand and calls up to the rim; he beckons twice "
     "and points down at the gravel beside him.",
     "on the pit floor level with his eyes, an arm's length from him, a 50mm lens. The afternoon sun comes "
     "from the LEFT onto his face and leaves the sand wall behind him in shadow",
     "Ogilvy's head and shoulders fill the CENTRE of the frame from his damp auburn hair at the TOP third to "
     "the open ochre jacket at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. "
     "His beckoning hand is raised at the RIGHT third and the dug sand wall rises behind him to the TOP edge.",
     "friction", "The man who was not believed now chooses who comes in."),
    ("dig", "medium", ["unnamed_first_person_narrator"], 0.6, "follow",
     f"Medium of {NARR} stepping down off the crowded rim onto the dug sand wall, his back to the camera, one "
     "hand holding his boater on, the staring onlookers left standing along the rim behind him.",
     "The camera tracks behind the Narrator as he slides down the sand wall toward the gravel floor; the "
     "onlookers on the rim stay back and watch him go; Ogilvy comes forward at the foot of the hull with his "
     "hand out.",
     "on the rim behind him at a standing man's eye, three long strides from him, a 35mm lens. The afternoon "
     "sun comes from the LEFT onto his back and leaves the pit floor in shadow",
     "The Narrator steps down the dug sand wall at the CENTRE of the frame, his back to the camera, his head "
     "a quarter of the frame's height. The onlookers stand in a row along the rim at the TOP LEFT, the "
     "crusted hull fills the RIGHT half below, and Ogilvy waits small on the gravel at the BOTTOM RIGHT.",
     "turn", "The turn is his own act: he leaves the crowd and goes down inside."),
    ("dig", "medium_close", ["ogilvy"], 0.8, "over_shoulder",
     f"Medium close over the Narrator's shoulder and straw boater toward {OGIL} at the foot of the hull, "
     "Ogilvy's face turned up to him, one hand gesturing back at the crowded rim.",
     "The camera holds over the Narrator's shoulder toward Ogilvy; Ogilvy jerks his thumb back at the crowd "
     "on the rim and speaks; he wipes the sweat from his spectacles.",
     "behind the Narrator's shoulder on the gravel, two long strides from Ogilvy, a 50mm lens. The afternoon "
     "sun comes from the LEFT onto Ogilvy's face and leaves the crust behind him in shadow",
     "Ogilvy's head and shoulders fill the RIGHT half of the frame from his damp auburn hair at the TOP third "
     "to the open ochre jacket at the BOTTOM edge, his head a third of the frame's height. The Narrator's "
     "grey tweed shoulder and straw boater fill the LEFT edge, dark against the crusted hull at the TOP LEFT.",
     "payoff", "The favour that makes him an insider: fetch the lord of the manor."),
    ("dig", "medium_close", ["stent"], 0.95, "low_angle",
     f"Low medium close of {STENT} standing on the curved crusted top of the cylinder against the glaring "
     "sky, his rolled notes already flung out toward the crowded rim, his long crimson face turned to it.",
     "The camera holds a low angle on Stent; he jabs the rolled notes at the rim and calls out; he mops his "
     "crimson face with a white handkerchief.",
     "on the crust just below him looking up at his face, an arm's length from him, a 50mm lens, a low "
     "angle. The afternoon sun comes from the LEFT onto his face and leaves the brim of his top hat black",
     "Stent's head and shoulders fill the CENTRE of the frame from his black silk top hat at the TOP third to "
     "the black frock coat at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. His "
     "rolled notes point out at the LEFT third, and the glaring white sky fills the TOP and the RIGHT edge.",
     "payoff", "Authority in a frock coat, red with heat, shouting at boys."),
    ("enclosure", "medium", [], 0.2, "tilt_up",
     "Medium inside the pit on the glaring afternoon: three workmen in collarless shirts and moleskin trousers "
     "digging at the foot of the crusted hull, and above them along the rim a dense crowd pressing forward, "
     "boys darting in and out between the legs of the onlookers.",
     "The camera tilts up from the workmen's spades in the sand to the crowd pressing along the rim; a boy "
     "slides a little way down the sand wall and scrambles back; the crowd leans forward.",
     "on the pit floor at a standing man's eye, five long strides from the workmen, a 35mm lens. The "
     "afternoon sun comes from the LEFT onto the crowd and leaves the sand wall below them black",
     "The workmen dig in a row across the BOTTOM third of the frame, their heads a sixth of the frame's "
     "height. The dug sand wall rises through the CENTRE, and the dense crowd presses along the rim across "
     "the TOP third, each head the size of a fingernail. The crusted hull edges in at the RIGHT edge.",
     "payoff", "The crowd has become the obstacle: a railing is needed to keep the world out."),
    ("enclosure", "medium_close", ["unnamed_first_person_narrator"], 0.4, "locked",
     f"Medium close of {NARR} on the pit floor beside the crusted hull, turned three-quarters toward the "
     "camera, his boater tipped back, the dense crowd on the rim far above him.",
     "The camera holds a locked-off frame; he nods and lifts his boater off; he glances up at the crowd on "
     "the rim and half smiles.",
     "on the pit floor level with his eyes, an arm's length from him, a 50mm lens. The afternoon sun comes "
     "from the LEFT onto his face and leaves the crust behind him in shadow",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his straw boater at the TOP third "
     "to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The "
     "crusted hull fills the RIGHT edge behind him and the crowded rim runs small across the TOP LEFT.",
     "payoff", "His want, granted: one of the privileged few."),
    ("enclosure", "insert", [], 0.7, "track_lateral",
     "Insert on the thin bright seam at the edge of the crusted lid: the steel tip of a workman's pickaxe "
     "already scraping along the smooth curve of the lid, sliding off the crust.",
     "The camera tracks sideways to the left along the seam, past the scraping pickaxe tip; the pickaxe "
     "slides off the smooth crust and skids along the seam; grey clinker dust drifts down the curve.",
     "at the foot of the lid, an arm's length from the seam, a 90mm lens. The afternoon sun comes from the "
     "LEFT along the seam and leaves the crust below it black",
     "The thin bright seam curves across the CENTRE of the frame from the LEFT edge to the RIGHT edge. The "
     "dun-grey crust of the lid fills the TOP half, the steel pickaxe tip scrapes at the RIGHT third, and "
     "the crust of the body fills the BOTTOM third below the seam.",
     "payoff", "Men with picks against a lid made to be opened from inside."),
    ("enclosure", "medium_close", ["ogilvy"], 0.9, "low_angle",
     f"Low medium close of {OGIL} crouched at the foot of the crusted lid, his head already turned with one "
     "ear toward the metal, his hand raised for silence.",
     "The camera holds a low angle on him; he lifts one finger for silence and speaks; he turns his head "
     "from the lid toward the camera.",
     "on the gravel below him looking up at his face, an arm's length from him, a 50mm lens, a low angle. "
     "The afternoon sun comes from the LEFT onto his face and leaves the metal behind him in shadow",
     "Ogilvy's head and shoulders fill the CENTRE of the frame from his damp auburn hair at the TOP third to "
     "the ochre waistcoat at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The "
     "grey crust of the lid fills the frame behind him from the LEFT edge to the RIGHT edge, the bright seam "
     "crossing the TOP.",
     "button", "The world's answer: the lid will not open for them, and something inside is alive."),
]

BEATS = {0: (0.8, 0.0), 3: (1.5, 2.5), 13: (0.6, 0.0), 16: (1.0, 0.0), 21: (1.0, 0.0), 22: (0.6, 1.5)}
TURNS = {16: "an onlooker in the crowd -> one of the few inside the rail",
         11: "a morning's curiosity -> a want that will not let him work",
         22: "a dead weight -> something alive that will not be opened by men"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "I found a little crowd, perhaps twenty people, standing about the great hole where it lay.", 0),
    ("narration", "unnamed_first_person_narrator",
     "The turf round it was charred black. Henderson and Ogilvy had gone off to breakfast.", 1),
    ("narration", "unnamed_first_person_narrator",
     "Four or five boys sat on the edge, legs dangling, pelting the giant mass with stones.", 2),
    ("dialogue", "unnamed_first_person_narrator", "Stop that, you boys! Leave it alone, and get back from the edge!", 4),
    ("narration", "unnamed_first_person_narrator",
     "Cyclists, my jobbing gardener, Gregg the butcher and his little boy. Hardly anyone spoke.", 5),
    ("narration", "unnamed_first_person_narrator",
     "I think they had hoped for a heap of charred corpses, and got an iron boiler.", 6),
    ("narration", "unnamed_first_person_narrator",
     "I clambered down into the pit, and fancied I felt a faint movement under my feet.", 7),
    ("narration", "unnamed_first_person_narrator",
     "Close to, it looked like a rusty gas float, but the crack gleamed a strange metal.", 8),
    ("narration", "unnamed_first_person_narrator",
     "I was sure the Thing had come from Mars. But I doubted anything living was inside.", 9),
    ("narration", "unnamed_first_person_narrator",
     "I dreamed of manuscripts inside, coins, models. Yet it was rather too large for comfort.", 10),
    ("narration", "unnamed_first_person_narrator",
     "About eleven I walked home to Maybury. But I could not settle to my work.", 11),
    ("narration", "unnamed_first_person_narrator",
     "By afternoon the common had changed: cabs from the station, a lordly carriage, heaps of bicycles.", 12),
    ("dialogue", "unnamed_newspaper_boy", "Message received from Mars! Remarkable story from Woking!", 13),
    ("narration", "unnamed_first_person_narrator",
     "In the pit I found Henderson, Ogilvy, and a tall fair man: Stent, the Astronomer Royal.", 14),
    ("dialogue", "ogilvy", "You there! Come down, will you? I need your help.", 15),
    ("narration", "unnamed_first_person_narrator",
     "I left the staring crowd behind me and slid down the hot sand to him.", 16),
    ("dialogue", "ogilvy", "Would you fetch Lord Hilton for us? We want a railing put up.", 17),
    ("dialogue", "stent", "Keep those boys back from the edge, there!", 18),
    ("narration", "unnamed_first_person_narrator",
     "The growing crowd hampered the digging, the boys worst of all. They needed a railing.", 19),
    ("narration", "unnamed_first_person_narrator",
     "I was glad to go. It made me one of the privileged few inside the rail.", 20),
    ("narration", "unnamed_first_person_narrator",
     "The workmen had failed to unscrew the top. It gave them no grip.", 21),
    ("dialogue", "ogilvy", "Listen. Now and then, something still stirs in there.", 22),
]

BEDS = [{"from_shot": 0, "tone": "plain"}, {"from_shot": 7, "tone": "uneasy"},
        {"from_shot": 11, "tone": "plain"}, {"from_shot": 14, "tone": "light"},
        {"from_shot": 21, "tone": "grave"}]

MOVES = {i: s[4] for i, s in enumerate(S)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.5, 0.0))
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces), view="",
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), why=why,
                          cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=3, title="On Horsell Common",
                question="Today, will the narrator get any nearer to seeing the Thing opened?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer=f"line {len(lines) - 1}",
                beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


from studio import episode_home  # noqa: E402


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    episode_home.write_plan(OUT, doc)
    (OUT.parent / "moves.json").write_text(json.dumps(MOVES, indent=1), encoding="utf-8")
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    counts = {m: list(MOVES.values()).count(m) for m in set(MOVES.values())}
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words "
          f"-> {words / 2.3:.0f}s at 2.3 w/s; dialogue {said / words:.1%}; moves {counts}")
    print(OUT)
