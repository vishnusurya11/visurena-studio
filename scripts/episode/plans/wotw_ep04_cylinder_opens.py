r"""The War of the Worlds, episode 4 -- "The Cylinder Opens", chapter 4.

THE BRICK.  One event: the lid comes off, and the man who spent all day trying
to get nearer runs away from it.

  QUESTION  Today, can the narrator hold his ground when the cylinder opens?
  TURN      shot 14, his own act: he stops being a spectator and shoulders
            backward out of the crush -- "one of the privileged few inside the
            rail -> a man shoving his way back from the edge".
  ANSWER    shot 18, he runs.
  BUTTON    line 22, the newspaper boy among the pines: nobody is going down
            for the shopman.  The world's answer, not the lead's.

REFERENCES-ONLY.  One wide per location (horsell_pit, horsell_common), one
sheet per person, one sheet for the cylinder.  ONE picture was drawn for this
episode: the Martian's sheet, redrawn -- v1 was a standing biped with a torso,
arms, legs and clawed feet, and chapter 4's whole horror is a bulk that is
wholly head and cannot stand.  v1 is kept as `sheet_v1.png`.

CAMERA (docs/calibration/camera_catalog.md).  Ten catalog moves over 24 shots,
none on more than a quarter, never the same head twice running, no orbit, no
push-in, no crane-down, tilt-down or rack.

SINGULARITY PROMPTING (docs/calibration/singularity_prompting.md, 2026-09-19).
Every `motion` is three clauses in the shape the fine-tune was trained on:
  1. the camera, in the official token vocabulary (static shot / tracking shot
     / truck / pan / tilt / pull out / pedestal), with an AMPLITUDE and no
     distance, ending on what it KEEPS in frame (R5, R6);
  2. ONE action chain -- trigger, action, displacement, contact -- never two
     unrelated beats (R4);
  3. a physical-feedback or expression clause -- dust, sand, cloth, breath,
     gaze -- tied to the contact moment, and still inside the opening frame
     (R8, R10).
The word "slow" never appears: `episode_ref_official.l3_slow` refuses it and
R13 says write the gait instead.  Colour is never asked for: the fine-tune
desaturates on purpose (R9), so light is source + direction + exposure +
material response, and the grade happens in the edit.

CROWDS (R3, and the ep03 clone fault).  No group is described once.  Two or
three hundred people are at this pit; the plan names two to four of them by
hat, height, dress and posture, and gives the rest as a BAND -- "a ragged line
of hats and shoulders along the rim, faces turned down into the pit" -- never
as a countable set of identical roles.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep04" / "plan.json"

WHERE = "Horsell, Surrey, 1894"
"""Not "Horsell Common": `stray_capitals` flags a capital in the style line whose
lower-case form appears elsewhere in the same prompt, and shot 20 writes "the
common round the sand-pits" in lower case (L20 STYLE, T20)."""
LIGHT = "low sun from the left, black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

NARR = ("the Narrator in the grey herringbone tweed suit and the straw boater with a black band, "
        "his dark moustache neat")
OGIL = ("Ogilvy, bare-headed with his auburn hair damp and pushed back, in the mustard-ochre tweed "
        "suit with the jacket open over the ochre waistcoat, round steel spectacles, sand on his "
        "trousers")
STENT = ("Stent, the tall fair-haired Astronomer Royal, in the black frock coat and the black silk "
         "top hat, his long face crimson and streaming with sweat, a rolled sheet of notes in one "
         "fist")
BOY = ("the newspaper boy in the grey flat cap and the oversized ginger corduroy jacket with "
       "patched elbows, his freckled face and gapped front teeth")
SHOP = ("the young Woking shopman in the brown cloth cap, the high white celluloid collar and "
        "violet tie, and the shiny black alpaca shop jacket with black sleeve protectors, his "
        "pinstriped trousers smeared with yellow sand")
MART = ("the Martian, a greyish rounded bulk the size of a bear that is wholly head, its oily "
        "grey-brown hide glistening like wet leather, two immense glossy black eyes set wide above "
        "a quivering V-shaped lipless mouth, sixteen whip tentacles hanging in two bunches")
CYL = "the huge crusted cylinder"

PIT_SUNSET = (
    "The great raw crater on Horsell Common with the sun going down in 1894: walls of loose yellow "
    "sand and grey gravel dug back and scored by spades, a charred rim of blackened turf heaped "
    "with spoil, planks and pickaxes on the gravel floor, a broken length of new white railing "
    "trodden flat into the sand along the near lip, and lying half-buried across the pit a "
    "colossal cylinder thirty yards across, one long hull running back into the sand, its huge "
    "circular end tilted up out of it and ringed by a thin bright seam, its skin caked in a scaly "
    "dun-grey crust of clinker; a ragged band of hats, bonnets and shoulders lines the rim above, "
    "faces turned down into the pit; the low sun comes from the LEFT, level and lemon-yellow, the "
    "sand reads bleached and the crust matte, and the near wall and the underside of the hull are "
    "black")
COMMON_SUNSET = (
    "Horsell Common with the sun going down in 1894: knee-deep purple-brown heather and dark "
    "furze, a stand of young Scots pines, a low raw ring of flung yellow sand round the crater a "
    "hundred yards off with a black band of heads and shoulders standing along it, a pale sandy "
    "road at the far left lined with deserted cabs and a lordly carriage, and the black roofs and "
    "church tower of Woking small on the horizon; the low sun comes from the LEFT, level and "
    "lemon-yellow, the heather reads dark and matte against a burning sky, and the pines and the "
    "standing figures are black")
PIT_GEOMETRY = (
    "The circular end of the cylinder stands at the CENTRE and the RIGHT third of the frame, its "
    "crusted face turned toward the camera, half the height of the frame, and its long hull runs "
    "back from it to the LEFT third deep into the sand. The dug yellow sand walls slope down from "
    "the LEFT edge and the RIGHT edge to the grey gravel floor at the BOTTOM. The charred rim, the "
    "band of hats and shoulders and the dark pines run across the TOP third.")
COMMON_GEOMETRY = (
    "The low raw ring of flung yellow sand lies across the CENTRE and the RIGHT third of the frame "
    "a hundred yards off, a black band of heads and shoulders along its top. Knee-deep heather "
    "fills the BOTTOM half, young Scots pines stand at the LEFT third and the RIGHT edge, the pale "
    "sandy road and the deserted cabs lie at the far LEFT, and the church tower of Woking rises "
    "small on the horizon at the CENTRE under the burning sky across the TOP.")

SETUPS = {
    "road": dict(
        described=COMMON_SUNSET,
        cast=["unnamed_first_person_narrator", "unnamed_newspaper_boy"],
        landmark="the raw ring of flung sand round the pit", landmark_at="far_end",
        landmark_size="is a quarter of the height of the frame",
        route="from the young pines across the heather to the ring of sand round the pit",
        geometry=COMMON_GEOMETRY, crowd="", outdoors=True, props=[], location="horsell_common"),
    "rim": dict(
        described=PIT_SUNSET,
        cast=["unnamed_first_person_narrator", "stent", "ogilvy", "unnamed_shopman"],
        landmark="the crusted circular end of the cylinder", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the charred rim among the packed hats down the dug sand to the crusted hull",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "mouth": dict(
        described=PIT_SUNSET,
        cast=["unnamed_first_person_narrator"],
        landmark="the bright seam at the rim of the lid", landmark_at="far_end",
        landmark_size="is the height of a hand",
        route="from the crusted end of the cylinder back across the gravel to the lip of the pit",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "opening": dict(
        described=PIT_SUNSET,
        cast=["unnamed_first_person_narrator", "martians", "stent"],
        landmark="the open black mouth of the cylinder", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the open mouth of the cylinder up the sand wall to the lip of the pit",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "flight": dict(
        described=COMMON_SUNSET,
        cast=["unnamed_first_person_narrator"],
        landmark="the stand of young Scots pines", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the ring of sand round the pit across the heather to the young pines",
        geometry=COMMON_GEOMETRY, crowd="", outdoors=True, props=[], location="horsell_common"),
    "pines": dict(
        described=COMMON_SUNSET,
        cast=["unnamed_first_person_narrator", "unnamed_newspaper_boy", "unnamed_shopman"],
        landmark="the heaped yellow sand round the pit", landmark_at="far_end",
        landmark_size="is a thumb's height in the frame",
        route="from the young pines and furze out across the heather to the heaped sand",
        geometry=COMMON_GEOMETRY, crowd="", outdoors=True, props=[], location="horsell_common"),
}

# (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why)
S = [
    # ---- road: the walk back, with the sun going down -------------------------------
    ("road", "wide", [], 0.2, "follow",
     f"Wide of Horsell Common with the sun going down: {NARR} seen from behind, walking over the "
     "heather along a sandy track toward the raw ring of flung yellow sand a hundred yards off, "
     "where a black band of heads and shoulders stands along the rim against a burning sky.",
     "The camera tracks behind the Narrator, a tracking shot at a walking pace with large "
     "amplitude, keeping his back in the lower left of frame and the ring of sand in the centre; "
     "he lengthens his stride as the band of heads on the rim grows ahead of him, his gaze out "
     "ahead of him, and he plants a boot into the loose sand of the track and pushes off it; "
     "the heather drags at his trouser leg and he pushes his boater back off his forehead.",
     "on the sandy track at a standing man's eye, four long strides behind him, a 35mm lens. The "
     "low sun comes from the LEFT, level and lemon-yellow; the sand heaps read bleached and the "
     "near heather is black",
     "The raw ring of flung yellow sand lies across the CENTRE and the RIGHT third of the frame a "
     "hundred yards off, a black band of heads and shoulders along its top. The Narrator walks at "
     "the LEFT third, his back to the camera, his boater a finger's height. Knee-deep heather "
     "fills the BOTTOM half, a young Scots pine stands at the RIGHT edge, and the burning "
     "lemon-yellow sky runs across the TOP.",
     "hook", "He comes back at sunset and finds that the thing has drawn a town."),

    ("road", "medium", [], 0.45, "track_lateral",
     "Medium on the heather track in the level sunset light: a stout woman in a black straw bonnet "
     "hurrying toward the camera with her skirts gathered in both fists, behind her a young clerk "
     "in a high celluloid collar wheeling a bicycle with a buckled front wheel, and further back a "
     "bearded carter in a red waistcoat walking fast with his coat over his arm.",
     "The camera tracks sideways to the right, a truck with small amplitude past the hurrying "
     "woman, keeping the clerk and his bicycle in the right of frame; the woman catches her hem on "
     "the furze, hauls her skirts higher with her jaw set hard and comes on at a hurrying walk, "
     "and the clerk swings the buckled wheel round the same bush behind her; the furze springs "
     "back and dust lifts off the track under her boots as she comes on.",
     "on the heather track at a standing woman's eye, two long strides from her, a 35mm lens. The "
     "low sun comes from the LEFT along the track; their faces read bright and the furze is black",
     "The woman in the black straw bonnet fills the CENTRE of the frame from her bonnet at the TOP "
     "third to her gathered skirts at the BOTTOM edge, her head a quarter of the frame's height. "
     "The clerk and his bicycle stand at the RIGHT third, the bearded carter small at the RIGHT "
     "edge, dark furze crosses the BOTTOM LEFT, and the burning sky runs across the TOP.",
     "setup", "Half of Woking is leaving, and he is the one walking the other way."),

    ("road", "medium_close", ["unnamed_newspaper_boy"], 0.7, "locked",
     f"Medium close of {BOY} running up the heather track straight at the camera, his flat cap "
     "shoved back off his forehead, his mouth open, both fists down at his sides, the ring of sand "
     "small behind him.",
     "The camera holds a static shot on the boy, keeping his head in the upper centre of frame; he "
     "throws one arm back at the pit behind him, drops his shoulder into the run and shouts at the "
     "camera as he comes; his cap slides forward over his eyebrows, he drags it down with the "
     "other hand and his breath saws in his open mouth.",
     "on the heather track level with his eyes, an arm's length from him, a 50mm lens. The low sun "
     "comes from the LEFT onto his face; his skin reads bright and the heather behind him is black",
     "The boy's head and shoulders fill the CENTRE of the frame from his grey flat cap at the TOP "
     "third to the ginger corduroy at the BOTTOM edge, his head a third of the frame's height, lit "
     "from the LEFT. The black band of heads on the ring of sand is small behind him at the RIGHT "
     "third, and the burning sky fills the TOP.",
     "setup", "The first witness comes the other way, and he is a child."),

    # ---- rim: two or three hundred people, and a man in the hole --------------------
    ("rim", "wide", [], 0.15, "high_angle",
     f"High wide looking down into the pit from the rim with the sun going down: {CYL} lying "
     "half-buried across the dug sand, its huge circular end tilted up, and along the near rim a "
     "ragged band of hats, bonnets and shoulders leaning out over the edge, faces turned down into "
     "the pit, with a broken length of new white railing trodden flat into the sand under their "
     "boots.",
     "The camera keeps high above the rim, a static shot looking down over the band of hats with "
     "the crusted end in the centre of frame; the band leans further out over the lip, the loose "
     "sand under it gives, and a man's bowler tips off and rolls down the wall to the gravel; the "
     "sand runs after it in a thin sheet and a dozen heads crane down after the hat.",
     "high on the near rim of the pit looking down into it, a 35mm lens, a high angle. The low sun "
     "comes from the LEFT along the crust; the sand reads bleached and the near wall is black",
     "The crusted circular end of the cylinder fills the CENTRE of the frame, half the frame's "
     "height, tilted up out of the sand. The ragged band of hats and shoulders crosses the BOTTOM "
     "edge and the LEFT third with the flattened white railing in the sand under it, the dug "
     "yellow sand walls slope in from the LEFT edge and the RIGHT edge, and the burning sky runs "
     "across the TOP third.",
     "friction", "The scale has changed: the thing has an audience now, and the audience presses."),

    ("rim", "medium_close", ["stent"], 0.3, "low_angle",
     f"Low medium close of {STENT} standing on the heaped spoil at the rim, turned three-quarters "
     "toward the camera, both arms down at his sides, his top hat tipped back off his crimson "
     "forehead, the burning sky behind him.",
     "The camera keeps low under Stent, a static shot from the height of the heaped sand with his "
     "face in the centre of frame; a shove runs through the people below him, he rocks a half-step "
     "on the loose spoil, flings both arms out wide to steady himself with his jaw driving forward "
     "and shouts down at them; sand slides from under his boot heel and his coat tails swing out "
     "behind him.",
     "on the heaped spoil below him looking up at his face, an arm's length from him, a 50mm lens, "
     "a low angle. The low sun comes from the LEFT onto his crimson face; the brim of his top hat "
     "is black",
     "Stent's head and shoulders fill the CENTRE of the frame from his black silk top hat at the "
     "TOP third to the black frock coat at the BOTTOM edge, his head a third of the frame's "
     "height, lit from the LEFT. His rolled notes hang at the RIGHT third, and the burning sky "
     "fills the TOP and the LEFT edge.",
     "friction", "Authority has stopped explaining and started shouting at boys."),

    ("rim", "medium", [], 0.45, "pan_to",
     "Medium along the packed lip of the pit in the level sunset light: a big red-faced carter in "
     "a moleskin waistcoat pressed shoulder to shoulder against a thin governess in grey who holds "
     "her hat on with one hand, and at their feet a small boy in a sailor collar squeezing between "
     "their legs toward the edge of the sand.",
     "The camera pans right with small amplitude from the carter's moleskin shoulder across to the "
     "boy at the lip, keeping the governess in the centre of frame; the carter shoves forward into "
     "her, she rocks back on her heels onto the boy's hand and grabs a fistful of his sailor "
     "collar to haul him up, her hat brim tipping over her eyes; the boy's knees drag through the "
     "sand and his sailor collar rides up over his ears.",
     "on the rim at a standing man's eye, two long strides from the carter, a 35mm lens. The low "
     "sun comes from the LEFT along their faces; their cheeks read bright and the pit below is "
     "black",
     "The carter fills the LEFT third of the frame from his bare head at the TOP third to his "
     "moleskin waistcoat at the BOTTOM edge, his head a quarter of the frame's height. The "
     "governess in grey stands at the CENTRE with her hand on her hat, the small boy crouches at "
     "the RIGHT third at the lip of the sand, and the black pit falls away across the BOTTOM.",
     "friction", "The crowd has become a crush, and the crush is pushing toward a hole."),

    ("rim", "medium_close", ["ogilvy"], 0.6, "over_shoulder",
     f"Medium close over the Narrator's grey tweed shoulder and the back of his straw boater "
     f"toward {OGIL} down on the sand below him, Ogilvy's face turned up at the rim, both hands "
     "spread at his sides.",
     "The camera keeps over the Narrator's shoulder, a static shot with Ogilvy's face in the right "
     "of frame; a fall of sand comes down the wall beside Ogilvy, he steps out from under it, "
     "jerks both hands up at the rim above with his gaze on the lens and calls up through them; the "
     "loose sand smokes off his sleeve and he shoves his spectacles back up his nose.",
     "behind the Narrator's shoulder on the rim, two long strides from Ogilvy, a 50mm lens. The "
     "low sun comes from the LEFT onto Ogilvy's face; his shirt reads bright and the crust behind "
     "him is black",
     "Ogilvy's head and shoulders fill the RIGHT half of the frame from his damp auburn hair at "
     "the TOP third to the open ochre jacket at the BOTTOM edge, his head a third of the frame's "
     "height. The Narrator's grey tweed shoulder and the back of his straw boater fill the LEFT "
     "edge dark against the crust, and the dug yellow sand wall runs across the BOTTOM.",
     "friction", "The man who let him inside the rail now wants him for a fence."),

    ("rim", "medium", ["unnamed_shopman"], 0.8, "tilt_up",
     f"Medium of {SHOP} down in the pit, standing on the curved crusted flank of the cylinder with "
     "his cap knocked askew, one boot planted flat on the crust, both arms out at his sides for "
     "balance, the dug sand wall rising behind him to the band of hats along the far rim.",
     "The camera tilts up with large amplitude from the shopman on the crusted flank to the ragged "
     "band of hats along the far rim above him, keeping his cap in the lower centre of frame; his boot "
     "skids down the curve, he drops onto one knee on the crust, throws a hand at the sand wall "
     "and drags a furrow down it; the loose sand runs over his sleeve protector, his mouth opens "
     "and he cranes his face up at the rim.",
     "on the near lip of the pit looking down across the hull at him, a 135mm lens. The low sun "
     "comes from the LEFT along the crust; the crust reads matte grey and the sand wall and the "
     "faces above are black",
     "The shopman stands on the crusted flank at the CENTRE of the frame from his brown cloth cap "
     "at the TOP third to his boots at the BOTTOM third, his head a fifth of the frame's height. "
     "The dun-grey crust runs across the BOTTOM edge from the LEFT edge to the RIGHT edge, the dug "
     "yellow sand wall rises behind him on the RIGHT, and the ragged band of hats crosses the TOP "
     "edge.",
     "friction", "The first man the pit takes is nobody's business but his own."),

    # ---- mouth: the screw, the lid, the black hole ----------------------------------
    ("mouth", "insert", [], 0.2, "locked",
     "Insert on the crusted circular end of the cylinder in the level sunset light: the thin "
     "bright seam at its rim standing open a hand's width, and out of it nearly two feet of "
     "shining yellowish-white screw thread standing clear of the crust, grey gravel below.",
     "The camera holds a static shot on the end of the cylinder, keeping the bright screw in the "
     "centre of frame; the screw turns on its thread from within, rides further out of the crust "
     "and the open seam behind it widens; rust-brown clinker cracks off the rim where the thread "
     "bears on it and runs down the curve onto the gravel.",
     "on the near lip of the pit looking down at the crusted end, a 300mm lens. The low sun comes "
     "from the LEFT along the bright screw; the metal reads specular and the crust around it is "
     "black",
     "The scaly dun-grey crust fills the frame from the LEFT edge to the RIGHT edge and from the "
     "TOP edge to the BOTTOM edge. The thin bright seam curves across the CENTRE, standing open a "
     "hand's width, and the shining screw stands out of it at the CENTRE, two hands wide and a "
     "sixth of the frame's height.",
     "setup", "It is not being opened. It is opening itself, from inside."),

    ("mouth", "medium", [], 0.45, "pull_reveal",
     "Medium of the crusted circular end of the cylinder from the lip of the pit: the shining screw "
     "standing clear at its centre with the last thread of it loose, grey gravel and splintered "
     "fir wood across the pit floor below, the dug sand wall behind.",
     "The camera pulls out from the loose screw with large amplitude, widening to show the whole "
     "crusted end above the gravel and keeping the bright seam in the upper centre of frame; the "
     "screw drives the last thread off, the heavy lid comes clear of the rim and drops onto the "
     "stones, and it rocks on its edge and beds down flat; a sheet of grey dust lifts off the "
     "gravel round it and drifts up across the crust.",
     "on the near lip of the pit looking down at the crusted end, a 135mm lens. The low sun comes "
     "from the LEFT along the crust; the gravel reads bleached and the sand wall behind is black",
     "The crusted circular end stands at the CENTRE and the RIGHT half of the frame, two-thirds of "
     "the frame's height, its bright seam curving round it. The shining screw stands out of its "
     "centre at the CENTRE, the grey gravel and splintered fir wood cross the BOTTOM third from "
     "the LEFT edge to the RIGHT edge, and the dug sand wall and a strip of burning sky fill the "
     "TOP LEFT.",
     "spike", "The sound of the chapter: iron on stone, and then nothing at all."),

    ("mouth", "medium_close", ["unnamed_first_person_narrator"], 0.7, "locked",
     f"Medium close of {NARR} packed in the crush at the lip of the pit, turned three-quarters "
     "toward the camera, his boater knocked forward over one eye, a stranger's dark shoulder hard "
     "against his own, hats crowding the frame behind him.",
     "The camera holds a static shot on the Narrator, keeping his face in the centre of frame; the "
     "press behind him shoves, his boot slides on the lip and he goes a half-step out over the "
     "sand, then digs his elbow back into the man behind him and hauls himself square again; sand "
     "spills from under his boot down the wall, he shoves his boater straight and turns his face "
     "down at the gravel below.",
     "on the rim level with his eyes, an arm's length from him, a 50mm lens. The low sun comes "
     "from the LEFT onto his face; his cheek reads bright and the hats around him are black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his straw boater at the "
     "TOP third to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit "
     "from the LEFT. A stranger's dark shoulder fills the RIGHT edge, black hats crowd the LEFT "
     "third, and the burning sky runs across the TOP.",
     "reaction", "He is not watching this safely. He is one shove from the hole."),

    ("mouth", "insert", [], 0.9, "track_lateral",
     "Insert on the open mouth of the cylinder: a black circular cavity in the crusted end, the "
     "thin bright rim of the seam curving round it, the low sun flaring white along the top of the "
     "crust above it.",
     "The camera tracks sideways to the left, a truck with small amplitude along the bright rim of "
     "the cavity, keeping the black mouth in the centre of frame; the flare of the low sun runs "
     "off the crust as the frame travels, the cavity comes round square to the lens and reads flat "
     "black; a thread of grey vapour lifts out of the mouth and drifts along the crust toward the "
     "seam.",
     "on the near lip of the pit looking down at the open end, a 135mm lens. The low sun comes "
     "from the LEFT across the crust; the crust reads matte and the cavity is a flat black",
     "The black circular cavity fills the CENTRE of the frame, half the frame's height, ringed by "
     "the thin bright seam. The scaly dun-grey crust fills the frame around it from the LEFT edge "
     "to the RIGHT edge and from the TOP edge to the BOTTOM, and the low sun flares white along "
     "the crust at the TOP LEFT.",
     "spike", "The held breath of the chapter: everyone is waiting for a man to climb out."),

    # ---- opening: what comes out, and the man who stops watching --------------------
    ("opening", "medium", [], 0.15, "pan_to",
     "Medium on the lower rim of the open black mouth of the cylinder: inside the shadow a "
     "greyish billowy mass lying low in the opening, and set wide apart in it two dim luminous "
     "disks turned out at the camera.",
     "The camera pans left with small amplitude from the bright seam across to the open black "
     "mouth, keeping the mouth in the centre of frame; the greyish mass heaves up inside the "
     "shadow, rides forward against the rim and the two luminous disks come with it to the edge "
     "of the light; the light takes the wet of them and the mass goes on swelling out against "
     "the metal.",
     "on the near lip of the pit looking down at the lower rim of the aperture, a 300mm lens. The "
     "low sun comes from the LEFT across the rim; the metal reads specular and the inside of the "
     "cylinder is black",
     "The black cavity fills the frame from the LEFT edge to the RIGHT edge and from the TOP edge "
     "down to the bright lower rim, which curves across the BOTTOM third. The greyish billowy mass "
     "lies low in the opening at the CENTRE, four feet across, with the two luminous disks set "
     "wide apart above it, and wet sand lies along the BOTTOM edge.",
     "spike", "The first fact: it is not a man, and it is already looking back."),

    ("opening", "insert", [], 0.3, "tilt_up",
     "Insert at the bright rim of the cavity: a little grey snake as thick as a walking stick "
     "coiled up over the metal edge out of the writhing shadow inside, its tip lifted a hand above "
     "the rim, the black cavity behind it.",
     "The camera tilts up with small amplitude from the bright metal rim to the raised tip of the "
     "grey tentacle, keeping the coil on the rim in the lower centre of frame; the tentacle takes "
     "a grip on the metal, unrolls a further length out of the shadow and wriggles in the air "
     "toward the lens; a second tentacle comes up over the rim beside it, the metal wets where "
     "they cross it and the first tip curls back on itself.",
     "on the near lip of the pit looking down at the lower rim of the aperture, a 300mm lens. The "
     "low sun comes from the LEFT along the bright rim; the wet hide reads specular and the "
     "cavity behind is black",
     "The bright metal rim curves across the BOTTOM third of the frame from the LEFT edge to the "
     "RIGHT edge. The grey tentacle rises from it at the CENTRE, as thick as a walking stick, its "
     "tip a third of the way up the frame, and the black cavity fills the TOP half behind it.",
     "spike", "It reaches out at the crowd before it shows them anything of itself."),

    ("opening", "medium_close", ["unnamed_first_person_narrator"], 0.45, "follow",
     f"Medium close of {NARR} squared to the lip of the pit with a bonnet brim hard against his "
     "shoulder, his face down at the cylinder below, black hats and bonnets packed close behind "
     "him.",
     "The camera tracks behind the Narrator's shoulder, a tracking shot with small amplitude, "
     "keeping his face in the right of frame; the sight of the rim takes him, he drops his "
     "shoulder and drives backward into the packed hats, brings his free hand up behind him and "
     "pushes a man's chest out of his road; the man gives, the Narrator's boater tips on his head "
     "and he swings his face back round over his shoulder at the cylinder.",
     "behind his shoulder on the rim at a standing man's eye, an arm's length from him, a 50mm "
     "lens. The low sun comes from the LEFT onto his cheek; his face reads bright and the hats "
     "around him are black",
     "The Narrator's head and shoulder fill the CENTRE and the RIGHT third of the frame from his "
     "straw boater at the TOP third to the grey tweed at the BOTTOM edge, his head a third of the "
     "frame's height. Black hats and bonnets crowd the LEFT half behind him, the bright seam of "
     "the cylinder shows small at the BOTTOM RIGHT, and the burning sky fills the TOP LEFT.",
     "turn", "The turn is his own act, and it reverses the one he made this morning."),

    ("opening", "medium_close", ["stent"], 0.6, "locked",
     f"Medium close of {STENT} on the lip of the pit, turned three-quarters toward the camera, his "
     "black silk top hat shoved back and crooked on his head, his shoulder still wedged deep in a "
     "packed band of hats and bonnets behind him.",
     "The camera holds a static shot on Stent, keeping his face in the centre of frame; what he "
     "sees below the rim takes him, his eyebrows drive up, he wrenches his shoulder out of the "
     "press and shouts back along the rim at the hats behind him; his coat tails swing round after "
     "him and the loose sand of the edge goes out from under his boot.",
     "on the lip of the pit level with his eyes, a 135mm lens. The low sun comes from the LEFT "
     "onto his crimson face; his collar reads bright and the hats behind him are black",
     "Stent's head and shoulders fill the CENTRE of the frame from his black silk top hat at the "
     "TOP third to the black frock coat at the BOTTOM edge, his head a third of the frame's "
     "height, lit from the LEFT. A packed band of hats and bonnets crosses the LEFT third behind "
     "him, the black pit falls away at the BOTTOM RIGHT, and the burning sky runs across the TOP.",
     "reaction", "Authority breaks first: the man who shouted keep back is the first one gone."),

    ("opening", "medium", ["martians"], 0.8, "low_angle",
     f"Low medium from the lip of the pit: {MART} rising out of the black mouth of the cylinder, its "
     "hide wet and shining in the level sun, one lank tentacle hooked over the bright rim, the "
     "crusted end filling the frame around it.",
     "The camera keeps low on the bulk in the mouth of the cylinder, a static shot from the near "
     "lip with the grey bulk in the centre of frame; the hooked tentacle takes the weight on the rim, the bulk "
     "labours up against the earth's pull and bulges out over the metal, and it rides forward "
     "until the light runs across the whole wet curve of it; the hide sheets with wet where it "
     "catches the sun, sand dust smokes off the rim under the tentacle and the whole mass pulses.",
     "on the near lip of the pit looking down at the lower rim of the aperture, a 300mm lens, a "
     "low angle on the bulk. The low sun comes from the LEFT onto the wet hide; the hide reads "
     "specular and the cavity behind it is black",
     "The grey bulk fills the CENTRE of the frame, half the frame's height and about four feet "
     "across, up over the bright lower rim of the aperture. The rim curves across the BOTTOM third "
     "with one tentacle hooked over it at the BOTTOM RIGHT, and the black cavity fills the frame "
     "behind the bulk from the LEFT edge to the RIGHT edge and up to the TOP edge.",
     "spike", "The thing itself, and it has to fight the ground for every inch."),

    ("opening", "medium_close", ["martians"], 0.95, "locked",
     "Medium close of the Martian's face above the rim of the cylinder: two immense glossy black "
     "eyes set wide apart in the wet grey-brown hide, below them the quivering V-shaped lipless "
     "mouth with its pointed upper lip, and the whip tentacles hanging in two bunches on either "
     "side of it.",
     "The camera holds a static shot on the Martian's face, keeping the two black eyes in the "
     "upper centre of frame; the lipless mouth opens under the eyes, pants against the strange air "
     "and the wedge of the lower lip drives down, and a thread of saliva swings off its brim and "
     "runs onto the metal with the two black eyes on the lens; the whole bulk heaves once with the "
     "breath and the two bunches of tentacles sway across the wet hide.",
     "on the near lip of the pit looking down at the lower rim of the aperture, a 300mm lens. The "
     "low sun comes from the LEFT onto the wet hide; the eyes read glass black and the cavity "
     "behind is black",
     "The Martian's face fills the CENTRE of the frame, the bulk half the frame's height and about "
     "four feet across, from the domed brow at the TOP third to the bright lower rim at the BOTTOM "
     "edge. The two black eyes sit wide apart at the CENTRE with the V-shaped mouth below them, "
     "the tentacle bunches hang at the LEFT third and the RIGHT third, and the black cavity fills "
     "the TOP corners.",
     "spike", "The face with no chin and no brow, holding still and looking straight at him."),

    # ---- flight: he runs ------------------------------------------------------------
    ("flight", "wide", [], 0.4, "track_lateral",
     f"Wide of the heather between the pit and the pines with the sun going down: {NARR} running "
     "across the frame through the knee-deep heather with his boater crushed in one fist and his "
     "head twisted back over his shoulder, small black figures scattered far apart on the heath "
     "behind him, the stand of young Scots pines dark at the right.",
     "The camera tracks alongside the Narrator, a truck at a running pace with large amplitude, "
     "keeping him in the centre of frame with the pines at the right; his boot catches a furze "
     "root, he pitches forward onto one hand, drives off it and runs on toward the pines; heather "
     "stems whip back across his knees, his chest works and he twists his head back over his "
     "shoulder again.",
     "on the heather at a standing man's eye, abreast of him, a 35mm lens. The low sun comes from "
     "the LEFT along the heather; the heath reads dark and the pines and the running figure are "
     "black",
     "The Narrator runs at the CENTRE of the frame, side on to the camera, his head a fifth of "
     "the frame's height. The stand of young Scots pines stands dark at the RIGHT third, the raw "
     "ring of sand lies small at the LEFT edge with its black band of heads, knee-deep heather "
     "fills the BOTTOM half and the burning sky runs across the TOP.",
     "spike", "The man who wanted inside the rail is running, and he cannot look away."),

    # ---- pines: the ring of watchers, and the head above the gravel ------------------
    ("pines", "medium_close", ["unnamed_first_person_narrator"], 0.15, "locked",
     f"Medium close of {NARR} among the young pines and the furze, his back against a pine trunk "
     "and his shoulder turned three-quarters toward the camera, his boater crushed in one fist, "
     "his collar sprung open, his chest working.",
     "The camera holds a static shot on the Narrator, keeping his face in the centre of frame; he "
     "drags a long breath in against the trunk, drops the crushed boater to hang at his knee and "
     "wipes his forehead with the back of his wrist; the bark grits under his shoulder, his throat "
     "works as the breath goes down and he turns his head round the trunk toward the pit.",
     "among the pines level with his eyes, an arm's length from him, a 50mm lens. The low sun "
     "comes from the LEFT onto his face; his face reads bright and the pine trunks are black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his dark hair at the TOP "
     "third to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit from "
     "the LEFT. A dark pine trunk fills the RIGHT edge, furze crosses the BOTTOM LEFT, and the "
     "burning sky shows between the branches across the TOP.",
     "runout", "He will not go nearer and he will not leave. That is the rest of the book."),

    ("pines", "wide", [], 0.4, "crane_up",
     "Wide of the common round the sand-pits with the sun going down: watchers standing far apart "
     "in a great ragged circle, a man up on the bars of a field gate at the left, a woman lying "
     "in a ditch with only her head above the bank, a boy at the corner of a hedge on the right, "
     "every face turned in at the heaps of yellow sand where the pit lies.",
     "The camera rises above the heather, a pedestal up with large amplitude looking down over the "
     "ragged circle, keeping the heaped sand in the centre of frame; the field gate takes weight "
     "and its top bar bends down, a head and shoulders rise out of the ditch bank behind it, and "
     "a grey sleeve comes out round the corner of the hedge; the gate bars shift under the boots "
     "on them and the ditch weeds close over the bank.",
     "on the heath at a standing man's eye, rising, a 35mm lens. The low sun stands level beyond "
     "the heaped sand; the heath reads dark and the hedges and the standing figures are black",
     "The heaped yellow sand of the pit lies at the CENTRE of the frame a hundred yards off, the "
     "height of a thumb. Black standing figures are scattered far apart across the heather from "
     "the LEFT edge to the RIGHT edge, a field gate at the LEFT third and a hedge corner at the "
     "RIGHT third, knee-deep heather fills the BOTTOM and the burning sky the TOP half.",
     "runout", "Nobody goes home. The horror has become a spectacle again, at a safer distance."),

    ("pines", "wide", ["unnamed_shopman"], 0.65, "pan_to",
     f"Wide of the heaped gravel at the edge of the pit seen out through the pine branches: the "
     f"round black head of {SHOP} showing above the sand with one hand and a shoulder up over the "
     "lip, the rest of him below the gravel, the burning sky behind.",
     "The camera pans right with small amplitude from a dark pine branch across to the shopman's "
     "head above the gravel, keeping his head in the centre of frame; he gets a shoulder and then "
     "a knee up over the lip, the loose gravel gives under his knee and he slides back down it; "
     "the gravel runs after him in a black sheet and his hand rakes a furrow down through the "
     "sand.",
     "among the pines at a standing man's eye, out across the heather to the heaped sand, a 35mm "
     "lens. The low sun stands level beyond the heaped gravel; the sand reads bleached and the "
     "head and the pine branch are black",
     "The heaped grey gravel crosses the CENTRE of the frame from the LEFT edge to the RIGHT edge. "
     "The shopman's round black head shows above it at the CENTRE, a thumb's height, with one hand "
     "and a shoulder at the RIGHT of it. A dark pine branch cuts across the TOP LEFT and the "
     "burning sky fills the TOP.",
     "runout", "The one man who needs help is the one nobody will walk back for."),

    ("pines", "medium_close", ["unnamed_newspaper_boy"], 0.85, "low_angle",
     f"Low medium close of {BOY} crouched in the furze among the pines, his flat cap pushed back, "
     "his knees drawn up under his chin, his face turned out across the heather at the pit.",
     "The camera keeps low under the boy, a static shot from the height of the furze with his face "
     "in the centre of frame; he jerks his chin out at the heaps of sand, speaks at the camera out "
     "of the side of his mouth with his eyes out at the pit, and pulls his knees in tighter against "
     "himself; the furze springs against his shoulder and both arms wrap round his shins.",
     "in the furze below him looking up at his face, an arm's length from him, a 50mm lens, a low "
     "angle. The low sun comes from the LEFT onto his face; his skin reads bright and the furze "
     "and the pine trunks are black",
     "The boy's head and shoulders fill the CENTRE of the frame from his grey flat cap at the TOP "
     "third to his drawn-up knees at the BOTTOM edge, his head a third of the frame's height, lit "
     "from the LEFT. Dark furze fills the LEFT edge and the RIGHT edge, a pine trunk stands at the "
     "RIGHT third, and the burning sky fills the TOP.",
     "button", "The world's answer: the crowd will watch a man go under and stay in the furze."),

    ("pines", "insert", [], 0.95, "track_lateral",
     "Insert on the pale sandy road by the sand-pits with the sun going down: a ginger-beer barrow "
     "standing derelict on its shafts with a cloth still laid over its bottles, black against the "
     "burning sky, and beyond it the wheel of a deserted cab with a horse at a nosebag.",
     "The camera tracks sideways to the right, a truck with small amplitude past the barrow's "
     "black wheel, keeping the barrow in the left of frame and the cab wheel in the right; the "
     "wind comes off the heath, takes the cloth over the bottles and lifts one corner of it clear "
     "of the glass; the cloth falls back across the necks, the horse at the nosebag paws the sand "
     "and the sand drifts along the road.",
     "on the sandy road at the height of the barrow's wheel, an arm's length from it, a 50mm lens. "
     "The low sun comes from the LEFT behind the barrow; the road reads bleached and the barrow "
     "and the cab are black",
     "The ginger-beer barrow stands black at the CENTRE and the LEFT half of the frame, two-thirds "
     "of the frame's height, its shafts down on the sand at the BOTTOM. The wheel of a deserted "
     "cab shows at the RIGHT third with a horse at a nosebag beyond it, the pale sandy road "
     "crosses the BOTTOM edge, and the burning sky fills the TOP half.",
     "runout", "The fair is still standing and nobody has gone home to their tea."),
]

# shot -> (beat_s, coda_s); anything unnamed gets (0.6, 0.0)
BEATS = {0: (0.8, 0.0), 2: (0.8, 0.0), 7: (0.8, 0.0), 9: (1.0, 0.4), 11: (0.8, 0.0),
         13: (0.8, 0.0), 15: (0.8, 0.0), 16: (0.8, 0.3), 17: (1.0, 0.5), 18: (0.5, 0.0),
         20: (0.8, 0.0), 21: (1.0, 0.0), 22: (1.0, 0.5), 23: (0.8, 2.2)}

TURNS = {14: "one of the privileged few inside the rail -> a man shoving his way back from the edge",
         10: "a spectator with a good place -> a man one shove from the hole",
         18: "a witness who wants to see -> a man running who cannot look away",
         22: "a crowd that came to see -> a hundred people who will watch and stay put"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "I came back over the common with the sun going down over the pit.", 0),
    ("narration", "unnamed_first_person_narrator",
     "Not one of them would tell me what was happening. They walked faster when I asked.", 1),
    ("dialogue", "unnamed_newspaper_boy",
     "The thing is moving! Screwing and screwing its way out!", 2),
    ("narration", "unnamed_first_person_narrator",
     "The railing I fetched Lord Hilton for was trodden flat into the sand.", 3),
    ("dialogue", "stent",
     "Keep back, there! Keep back from the edge, all of you!", 4),
    ("narration", "unnamed_first_person_narrator",
     "They elbowed and jostled one another, and the ladies among them were the worst.", 5),
    ("dialogue", "ogilvy",
     "I say! Help me keep these idiots back, will you?", 6),
    ("narration", "unnamed_first_person_narrator",
     "The crowd had pushed a young shopman in, and he could not climb out again.", 7),
    ("narration", "unnamed_first_person_narrator",
     "Under the shouting I heard a humming. The end was being screwed out from within.", 8),
    ("narration", "unnamed_first_person_narrator",
     "Then the lid came away and fell on the gravel with a ringing concussion.", 9),
    ("narration", "unnamed_first_person_narrator",
     "Somebody blundered into me, and I came near to being pitched onto the screw.", 10),
    ("narration", "unnamed_first_person_narrator",
     "I think everyone expected a man to climb out of it. I know I did.", 11),
    ("narration", "unnamed_first_person_narrator",
     "The sunset was in my eyes. I could not make out what I saw.", 12),
    ("narration", "unnamed_first_person_narrator",
     "I had been so sure the thing held nothing but manuscripts and coins from Mars.", 13),
    ("narration", "unnamed_first_person_narrator",
     "A sudden chill came over me. Behind me a woman shrieked.", 14),
    ("dialogue", "stent",
     "Get away from it! For God's sake, run, all of you!", 15),
    ("narration", "unnamed_first_person_narrator",
     "The weight of our whole world dragged at it, and still it came up.", 16),
    ("narration", "unnamed_first_person_narrator",
     "The crush behind me was gone. I stood alone at the edge, and stared.", 17),
    ("narration", "unnamed_first_person_narrator",
     "It toppled over the brim with a thud. Another came up out of the dark.", 18),
    ("narration", "unnamed_first_person_narrator",
     "A hundred yards. That was the whole distance my courage was worth.", 19),
    ("narration", "unnamed_first_person_narrator",
     "Nobody said anything worth hearing, and nobody moved, and nobody went home.", 20),
    ("narration", "unnamed_first_person_narrator",
     "I had an impulse to go back down for him. My fear put it down.", 21),
    ("dialogue", "unnamed_newspaper_boy",
     "He went down a long while back. Nobody has fetched him.", 22),
]

BEDS = [{"from_shot": 0, "tone": "plain"}, {"from_shot": 3, "tone": "uneasy"},
        {"from_shot": 9, "tone": "grave"}, {"from_shot": 12, "tone": "thrilling"},
        {"from_shot": 19, "tone": "grave"}]

MOVES = {i: s[4] for i, s in enumerate(S)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.6, 0.0))
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces), view="",
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), why=why,
                          cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=4, title="The Cylinder Opens",
                question="Today, can the narrator hold his ground when the cylinder opens?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 18",
                beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT.parent / "moves.json").write_text(json.dumps(MOVES, indent=1), encoding="utf-8")
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    counts = {m: list(MOVES.values()).count(m) for m in set(MOVES.values())}
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words "
          f"-> {words / 2.3:.0f}s at 2.3 w/s; dialogue {said / words:.1%}; moves {counts}")
    print(OUT)
