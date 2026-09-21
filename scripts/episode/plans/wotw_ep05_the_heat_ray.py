r"""The War of the Worlds, episode 5 -- "The Heat-Ray", chapter 5.

THE BRICK.  One event: the common talks itself into walking toward the pit,
and the pit answers with fire.

  QUESTION  Today, can the narrator go near the pit and come back?
  TURN      shot 16, his own act and his own legs: he stops circling at a safe
            distance and walks in with the crescent -- "a man who has kept his
            hundred yards all evening -> a man closing on the pit with the rest".
  ANSWER    shot 24: the invisible heated finger is drawn through the heather
            BETWEEN him and the machines, and passes.  His own boots are in that
            frame, at the left edge, because "between him and them" is a
            geometry and a picture that holds only one of the two terms is not
            an answer.  He comes back by accident, not by courage.
  BUTTON    line 24, the neighbour, met again in the dark on the road home, and
            it is the SAME SENTENCE he said at sunset, word for word.  Wells:
            "He repeated this over and over again."  A man who has watched forty
            people burn and still has only the four words he had before is the
            world's answer; a man who could report the event would not be.

REFERENCES-ONLY.  ONE location for the whole episode -- `horsell_common` --
because chapter 5 never lets the narrator off the heather: he circles it, he
watches from a knoll, and the heated finger is drawn "through the heather
between me and the Martians".  Any shot standing in the pit would be a camera
standing where the narrator is not, in a first-person episode over first-person
narration -- the fault ep04's reviewer round found and fixed.  Six setups carry
the variety instead, each with its own plate and its own hour: two at sunset,
one at twilight, one at dusk, one at nightfall, one in the dark by firelight.

ONE PICTURE DRAWN: `refs/props/pit_mast_mirror/sheet.png`.  It is NOT
`heat_ray_generator`.  In chapter 5 Wells shows only "a thin rod rose up, joint
by joint, bearing at its apex a circular disk that spun with a wobbling motion"
and "slowly a humped shape rose out of the pit, and the ghost of a beam of
light seemed to flicker out from it"; the camera-like case on a jointed arm is
not described until chapter 11 and is carried by a fighting-machine that has
not been assembled yet.  Drawing the generator would put a chapter-11 machine
in the chapter-5 pit.

ONE VOICE CAST: `unnamed_neighbour`.  The narrator's own question is his own
dialogue line, and the newspaper boy -- cast in ep02 -- gets the one mid-episode
line as Wells's "lad trundling off the barrow of apples".  ep04 gave that boy
the button and twice running would be a tic, so the button is the neighbour's.

CAMERA (docs/calibration/camera_catalog.md): eight catalog moves over 28 shots,
none on more than a quarter, never the same move twice running, no orbit, no
push-in, no pull-back off a wide, no crane-down, tilt-down or rack.

EVERY SIZE IS ARITHMETIC, NOT A FEELING (optical review, 2026-09-20).  At the
chapter's fixed hundred yards a 35 mm square frame is about 63 m tall, a 50 mm
44 m, a 135 mm 16 m and a 300 mm 7 m; the drawn sheet's mast is about 6 m and
its dome about 2.8 m.  Every stated fraction in this plan is computed against
those numbers, and where the first draft was wrong it was wrong by a factor of
five: the "low raw ring" of sand was written a fifth of a 35 mm frame, which is
a four-storey wall.  A face at a third of frame on a 50 mm needs the lens 1.5 m
away, not "an arm's length", which frames 34 cm and is an eye.

EP04'S LESSONS, APPLIED BEFORE THE FIRST FRAME:
- A MOVING camera is never told to keep a subject in frame.  "keeping him in
  the centre of frame" is ep01's orbit request in gerund form, and 13 of ep04's
  24 shots carried it: churn 7.8, twelve blur dips on two takes, two late
  reframes.  Only a STATIC head names what it frames; every travelling head
  names where it ARRIVES and how far it goes.
- Every head opens on a move the builder's own vocabulary knows (`pans`,
  `tracks`, `tilts`, `rises`, `keeps`, `holds a static shot`) and carries
  `travelling <amount>`.  "trucks right" is not in that vocabulary, and one
  refusal aborts a whole retake batch in silence while the DQ comes back
  identical and looks like a fix that worked.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep05" / "plan.json"

WHERE = "Horsell, Surrey, 1894"
LIGHT = "low sun from the left, black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

NARR = ("the Narrator in the grey herringbone tweed suit and the straw boater with a black band, "
        "his dark moustache neat")
NEIGH = ("the neighbour, a tall spare stooping man of forty-eight in a cream straw panama and a "
         "sky-blue-and-white striped flannel blazer over white flannel trousers, his hollow cheeks "
         "and short pointed grey goatee, an ash walking stick in one fist")
BOY = ("the newspaper boy in the grey flat cap and the oversized ginger corduroy jacket with "
       "patched elbows, his freckled face and gapped front teeth")
MAST = "the thin jointed mast with its wobbling mirror"

COMMON_SUNSET = (
    "Horsell Common with the sun going down in 1894: knee-deep purple-brown heather and dark furze "
    "running back from the camera, two young Scots pines standing clear of it, a low raw ring of "
    "flung yellow sand round the crater a hundred yards off with a thin black band of heads and "
    "shoulders along its far rim and a thin jointed mast standing above it, the old sand-pits at "
    "the far LEFT with a row of deserted flys and a basket-chaise on their gravel floor, and the "
    "black roofs and church tower of Woking small on the horizon; the low sun comes from the LEFT, "
    "level and lemon-yellow, the heather reads dark and matte against a burning sky, and the pines "
    "and the standing figures are black")
COMMON_TWILIGHT = (
    "Horsell Common at twilight in 1894: knee-deep purple-brown heather and dark furze reading "
    "near-black, two young Scots pines standing black against the sky, a low raw ring of flung "
    "yellow sand round the crater a hundred yards off with a thin jointed mast standing above it, "
    "a straggling line of dark figures spread across the heather between the camera and the sand, "
    "the old sand-pits at the far LEFT with cabs and feeding horses on their gravel floor, and the "
    "roofs of Woking black on the horizon; the last daylight comes low from the LEFT under a pale "
    "greenish-blue sky, the sand ring reads pale grey and the heather, the pines and the figures "
    "are black")
COMMON_DUSK = (
    "Horsell Common at dusk in 1894: knee-deep heather and dark furze reading black, a low raw "
    "ring of flung yellow sand round the crater a hundred yards off with a thin jointed mast "
    "standing above it, a small wedge of dark figures out on the heather beyond the sand with a "
    "square of white linen on a long pale pole at its apex, a broken ring of other dark figures "
    "spread wide across the heather behind them, two young Scots pines black at the LEFT, and the "
    "roofs of Woking black on the horizon; the last of the daylight stands low from the LEFT "
    "alone, the linen reads bright, the sky above is deep blue, and "
    "the heather, the pines and the figures read black to the horizon")
COMMON_NIGHTFALL = (
    "Horsell Common at nightfall in 1894: the heather and the furze reading black, a low raw ring "
    "of flung yellow sand round the crater a hundred yards off with a smooth humped dome lifting "
    "over its rim and a thin jointed mast beside it, a scattered wedge of small dark figures out "
    "on the heather beyond the sand, two young Scots pines black at the LEFT, and the roofs of "
    "Woking black on the horizon under mustering stars; the last greenish daylight stands low from "
    "the LEFT, the sand ring reads pale grey and the heather, the pines and the figures are black")
COMMON_FIRELIGHT = (
    "Horsell Common in the dark in 1894: a low fire of burning furze on the LEFT throws hard black "
    "shadow across knee-deep heather, blackened patches smoking and glowing away over the ground, "
    "a low raw ring of flung yellow sand a hundred yards off at the CENTRE with a thin jointed "
    "mast standing black above it, a pale sandy road running grey across the middle distance, and "
    "the roofs of Woking black on the horizon with spires of flame going up from the houses beyond "
    "them; the pale bright greenish afterglow stands low on the LEFT behind the black tops of the "
    "pines under mustering stars, and the heather and the road banks are black")

GEO_HEATHER = (
    "Knee-deep purple-brown heather fills the BOTTOM half of the frame from the LEFT edge to the "
    "RIGHT edge. The low raw ring of flung yellow sand lies across the CENTRE a hundred yards off, "
    "a tenth of the height of the frame, with a thin black band of heads and shoulders along its "
    "far rim and the thin jointed mast standing above it. A young Scots pine stands at the RIGHT "
    "edge and a second at the LEFT third, the old sand-pits and the deserted flys lie at the far "
    "LEFT, the church tower of Woking rises small at the CENTRE on the horizon, and the burning "
    "lemon-yellow sky runs across the TOP third.")
GEO_KNOLL = (
    "The heathery knoll fills the BOTTOM third of the frame from the LEFT edge to the RIGHT edge "
    "and the heather falls away from it toward the CENTRE. The low raw ring of flung yellow sand "
    "lies across the CENTRE a hundred yards off, a tenth of the height of the frame, and the thin "
    "jointed mast stands above it at the CENTRE, a sixth of the height of the frame. A dark knot "
    "of standing people shows at the LEFT third toward Woking and a second knot at the RIGHT "
    "third toward Chobham, two young Scots pines stand at the LEFT edge, and the burning sky runs "
    "across the TOP third above the black roofs of Woking.")
GEO_DUSK = (
    "Knee-deep black heather fills the BOTTOM half of the frame from the LEFT edge to the RIGHT "
    "edge. The low raw ring of flung yellow sand lies across the CENTRE a hundred yards off, a "
    "tenth of the height of the frame, with the thin jointed mast standing above it at the CENTRE "
    "at a sixth of the height of the frame. A straggling line of dark figures crosses the frame "
    "between the heather and the sand, two young Scots pines stand at the LEFT edge, the old "
    "sand-pits lie at the far LEFT, and a pale greenish-blue sky runs across the TOP third.")
GEO_FLAG = (
    "Knee-deep black heather fills the BOTTOM third of the frame from the LEFT edge to the RIGHT "
    "edge. The low raw ring of flung yellow sand lies across the CENTRE a hundred yards off, a "
    "tenth of the height of the frame. The small wedge of dark figures stands out on the heather "
    "beyond the sand at the CENTRE RIGHT, the square of white linen showing above them as a white "
    "fleck as wide as one of their heads. Two young Scots pines stand black at the LEFT edge, "
    "and a deep blue sky runs across the TOP half.")
GEO_NIGHT = (
    "Black heather fills the BOTTOM third of the frame from the LEFT edge to the RIGHT edge. The "
    "low raw ring of flung yellow sand lies across the CENTRE a hundred yards off, a tenth of the "
    "height of the frame, the smooth humped dome lifting over its rim at the CENTRE and the thin "
    "jointed mast standing beside it at the CENTRE RIGHT at a sixth of the height of the frame. "
    "The scattered wedge of small dark figures stands on the heather at the RIGHT third, two young "
    "Scots pines stand at the LEFT edge, and the darkening sky runs across the TOP half.")
GEO_FIRE = (
    "Knee-deep black heather fills the BOTTOM half of the frame from the LEFT edge to the RIGHT "
    "edge, with a low fire of burning furze at the LEFT third. The pale sandy road runs grey "
    "across the CENTRE from the LEFT edge to the RIGHT third. The low raw ring of flung yellow "
    "sand lies beyond it at the CENTRE a hundred yards off, the thin jointed mast standing above "
    "it at a tenth of the height of the frame. The pale greenish afterglow stands low at the TOP "
    "LEFT behind the black pine tops, and the black roofs of Woking lie at the RIGHT third on the "
    "horizon with spires of flame above them.")

SETUPS = {
    "heather": dict(
        described=COMMON_SUNSET,
        cast=["unnamed_first_person_narrator"],
        landmark="the low raw ring of flung sand round the pit", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the young Scots pines across the open heather toward the ring of sand round the pit",
        geometry=GEO_HEATHER, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
    "knoll": dict(
        described=COMMON_SUNSET,
        cast=["unnamed_first_person_narrator", "unnamed_neighbour"],
        landmark="the low raw ring of flung sand round the pit", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the open heather round in a wide curve to the little heathery knoll above it",
        geometry=GEO_KNOLL, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
    "dusk": dict(
        described=COMMON_TWILIGHT,
        cast=["unnamed_first_person_narrator", "unnamed_newspaper_boy"],
        landmark="the thin jointed mast above the ring of sand", landmark_at="far_end",
        landmark_size="is a sixth of the height of the frame",
        route="from the little heathery knoll down across the heather to the gravel mouth of the sand-pits",
        geometry=GEO_DUSK, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
    "flag": dict(
        described=COMMON_DUSK,
        cast=["unnamed_first_person_narrator"],
        landmark="the square of white linen on its long pale pole", landmark_at="far_end",
        landmark_size="is a fleck as wide as one of the figures' heads",
        route="from the open heather in toward the ring of sand and the wedge of men beyond it",
        geometry=GEO_FLAG, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
    "ray": dict(
        described=COMMON_NIGHTFALL,
        cast=["unnamed_first_person_narrator"],
        landmark="the smooth humped dome over the rim of the sand", landmark_at="far_end",
        landmark_size="is a sixth of the height of the frame",
        route="from the black heather in toward the ring of sand with the dome lifting over it",
        geometry=GEO_NIGHT, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
    "dark": dict(
        described=COMMON_FIRELIGHT,
        cast=["unnamed_first_person_narrator", "unnamed_neighbour"],
        landmark="the thin jointed mast against the western afterglow", landmark_at="start",
        landmark_size="is a tenth of the height of the frame",
        route="from the ring of sand back across the black heather to the pale sandy road",
        geometry=GEO_FIRE, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
}

NAR = ["unnamed_first_person_narrator"]
NEI = ["unnamed_neighbour"]

# (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why)
S = [
    # ---- heather: paralysed in the heather, and the machines begin -----------------
    ("heather", "wide", NAR, 0.15, "track_lateral",
     f"Wide of Horsell Common with the sun going down: a black furze bush filling the near left of "
     f"the picture, {NARR} beyond it standing knee-deep in the purple-brown heather with his back "
     "three-quarters to the camera and both hands open at his sides, and past him the low raw ring "
     "of flung yellow sand a hundred yards off with a thin black band of heads along its far rim.",
     "The camera tracks sideways to the right, a truck with small amplitude past the black furze "
     "bush until the Narrator stands clear of it with the ring of sand beyond him, travelling one "
     "short stride; he drags a breath in with his chest lifting and his gaze fixed out on the "
     "black band of heads; the heather springs against his knees and his shoulders come round a "
     "hand's breadth toward the sand.",
     "on the heather two long strides behind him at a standing man's eye, a 35mm lens. The low sun "
     "comes from the LEFT; the sand ring reads bleached and the near heather and the pines are "
     "black",
     "A black furze bush fills the LEFT third of the frame from the TOP third to the BOTTOM edge. "
     "The Narrator stands at the CENTRE beyond it from his straw boater at the CENTRE to the "
     "heather at the BOTTOM third, his back three-quarters to the camera, his head a seventh of "
     "the height of the frame. The low raw ring of flung yellow sand crosses the CENTRE RIGHT a "
     "hundred yards off, a tenth of the height of the frame, a thin black band of heads along its "
     "top. Knee-deep heather fills the BOTTOM half and the burning lemon-yellow sky runs across "
     "the TOP third.",
     "hook", "The man who spent two chapters getting nearer is the one who cannot move."),

    ("heather", "medium_close", NAR, 0.2, "locked",
     f"Medium close of {NARR} in the heather at sunset, turned three-quarters toward the camera "
     "with the level light along one cheek, his lips parted, the sand ring small and soft behind "
     "his shoulder.",
     "The camera holds a static shot on the Narrator, keeping his face in the centre of frame; a "
     "breath goes out of him and his eyes travel along the far rim; his collar shifts at his "
     "throat and he brings his chin round a finger's breadth to follow what he is watching.",
     "on the heather level with his eyes, two paces from him, a 50mm lens. He has turned back "
     "toward the sun in the west and the low light comes from the RIGHT onto his cheek; his cheek "
     "reads bright and the heather behind him is black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his straw boater at the "
     "TOP third to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit "
     "from the RIGHT. Dark heather crosses the BOTTOM edge, the pale sand ring shows small and "
     "soft at the LEFT third, and the burning sky fills the TOP and the RIGHT edge.",
     "reaction", "Fear and curiosity in one face: the whole chapter in a held frame."),

    ("heather", "insert", [], 0.35, "pan_to",
     "Insert on the burning sunset sky above the raw sand heaps: the black top of a young Scots "
     "pine at the left of the picture, and out beyond it a bunch of black tentacles rooted "
     "together at one point in the sand, each one a different length and each one curling over on "
     "itself at a different height, like the arms of an octopus held up against the lemon-yellow "
     "light in flat silhouette, the dark line of the heaps running across the bottom.",
     "The camera pans right with small amplitude from the black top of the young Scots pine across "
     "to the tentacles above the sand, travelling a finger's breadth; the bunch of tentacles "
     "uncurls out across the sky, each one whipping out from the same root at its own speed and to "
     "its own height; the light runs along their backs and the whole bunch draws down a thumb's "
     "width toward the sand.",
     "on the heather looking out over the heaps at the sky, a 135mm lens. The low sun stands beyond "
     "the sand at the LEFT; the sky reads bright and the whips, the pine and the heaps are black",
     "The burning lemon-yellow sky fills the TOP two thirds of the frame from the LEFT edge to the "
     "RIGHT edge. The black top of a young Scots pine stands at the LEFT edge and the dark line of "
     "the sand heaps runs across the BOTTOM third. The bunch of black tentacles stands up from one "
     "root at the CENTRE RIGHT against the sky, a fifth of the height of the frame, the longest "
     "reaching twice the height of the shortest and every tip curled over at its own height.",
     "spike", "The first limb of the thing, and it is not a limb like ours."),

    ("heather", "medium", [], 0.5, "tilt_up",
     f"Medium on the raw yellow sand heaps against the sunset: the first joint of {MAST} standing "
     "a hand's height clear of the rim, a dark bronze rod in telescoping segments with the "
     "polished silver disk lying folded against it, and a black band of heads and shoulders small "
     "along the rim below.",
     "The camera tilts up with large amplitude from the black band of heads on the rim to the top "
     "of the mast, travelling two long strides; the mast drives out joint after joint from within "
     "and rides higher over the sand, and the disk at its apex swings over and begins to turn; the "
     "light flares off the silver and the whole rod leans a hand's breadth toward the camera.",
     "on the heather looking out across the heaps, a 135mm lens. The low sun comes from the LEFT "
     "along the rod; the silver disk reads specular and the sand heaps and the heads are black",
     "The raw yellow sand heaps cross the CENTRE of the frame from the LEFT edge to the RIGHT edge "
     "with a black band of heads and shoulders small along them. The first joint of the thin "
     "jointed mast stands up at the CENTRE a hand's height above the rim with the folded disk "
     "against it. Knee-deep black heather fills the BOTTOM third and the burning lemon-yellow sky "
     "fills the TOP half.",
     "spike", "They are not coming out to us. They are putting up an instrument."),

    # ---- knoll: the big curve, and the only other man on the heath -----------------
    ("knoll", "wide", NAR, 0.15, "follow",
     f"Wide of the open heather in the level sunset light: {NARR} walking away from the camera in a "
     "long curve through the knee-deep heather, his boater pushed back, a dark knot of standing "
     "people small at the left toward Woking and a second knot at the right toward Chobham, the "
     "ring of sand between them with the thin mast standing above it.",
     "The camera tracks behind the Narrator at a walking pace with large amplitude, coming round "
     "with the curve of his track until the ring of sand stands at the centre of the picture, "
     "travelling four long strides; he swings his weight from one boot to the other through the "
     "heather, his head turned out to the sand all the way; the furze drags at his trouser leg and "
     "his right arm comes up across his chest.",
     "on the heather three long strides behind him at a standing man's eye, a 35mm lens. The low "
     "sun comes from the LEFT; the heather reads dark and matte and the standing figures are black",
     "The Narrator walks at the LEFT third of the frame, his back to the camera, from his straw "
     "boater at the TOP third to the heather at the BOTTOM edge, his head a seventh of the height "
     "of the frame. Knee-deep heather fills the BOTTOM half from the LEFT edge to the RIGHT edge, "
     "the ring of sand lies across the CENTRE a tenth of the height of the frame, a dark knot of "
     "people stands at the LEFT edge and a second at the RIGHT third, and the burning sky runs "
     "across the TOP third.",
     "setup", "He cannot go back and he cannot leave, so he walks a circle round it."),

    ("knoll", "medium", NEI, 0.35, "track_lateral",
     f"Medium on the heather in the level sunset light: {NEIGH} standing alone among the furze "
     "with both fists on the head of his stick, his panama tipped forward, his face turned out at "
     "the sand heaps, the burning sky behind him.",
     "The camera tracks sideways to the left, a truck with small amplitude past a black furze bush "
     "in the foreground until the neighbour stands clear of it, travelling one short stride; he "
     "leans his weight down onto the stick with both fists on its head and drives the ferrule into "
     "the sand at his own boot; his blazer swings open at the hem and he shakes his head twice.",
     "on the heather at a standing man's eye, two long strides from him, a 50mm lens. The low sun "
     "comes from the LEFT onto his shoulder; his straw panama reads bright and the furze at his "
     "feet is black",
     "A black furze bush crosses the BOTTOM LEFT of the frame. The neighbour stands at the CENTRE "
     "from his cream straw panama at the TOP third to the furze at the BOTTOM edge, his head a "
     "quarter of the height of the frame. The raw sand heaps lie small at the RIGHT third, and the "
     "burning lemon-yellow sky fills the TOP and the RIGHT edge.",
     "friction", "One other man, on a common where two hundred are watching from a distance."),

    ("knoll", "medium_close", NEI, 0.5, "locked",
     f"Medium close of {NEIGH} turned three-quarters toward the camera with the level light on his "
     "hollow cheek, his mouth open, both fists still on the head of his stick, the heather black "
     "behind him.",
     "The camera holds a static shot on the neighbour, keeping his face in the centre of frame; he "
     "hauls a breath in, throws his chin up at the sand heaps with his goatee working, and speaks "
     "at the camera; one fist lifts a hand's breadth off the head of the stick.",
     "on the heather level with his eyes, two paces from him, a 50mm lens. He has turned back "
     "toward the sun in the west and the low light comes from the RIGHT onto his cheek; the "
     "burning lemon-yellow sky stands behind him and the heather at his shoulder is black",
     "The neighbour's head and shoulders fill the CENTRE of the frame from his cream straw panama "
     "at the TOP third to the striped flannel at the BOTTOM edge, his head a third of the frame's "
     "height, lit from the RIGHT. The head of his ash stick shows at the BOTTOM LEFT, dark heather "
     "crosses the BOTTOM edge, and the burning sky fills the TOP and the RIGHT edge.",
     "friction", "A grown man with one sentence for the arrival of another world."),

    ("knoll", "medium_close", NAR, 0.65, "over_shoulder",
     f"Medium close over the neighbour's striped flannel shoulder and the back of his cream straw "
     f"panama toward {NARR}, the Narrator square in the right of the picture with the level light "
     "on his face, the heather running away behind him.",
     "The camera keeps over the neighbour's shoulder, a static shot with the Narrator's face in "
     "the right of frame; the Narrator brings his chin round from the sand heaps to the lens and "
     "asks his question, his brows driving together; his hand lifts from his side and opens out "
     "toward the pit.",
     "behind the neighbour's shoulder on the heather, two long strides from the Narrator, a 50mm "
     "lens. The low sun comes from the LEFT along the two men; the Narrator's cheek reads bright "
     "and the shoulder in the foreground is black",
     "The Narrator's head and shoulders fill the RIGHT half of the frame from his straw boater at "
     "the TOP third to the grey tweed at the BOTTOM edge, his head a third of the frame's height. "
     "The neighbour's striped flannel shoulder and the back of his panama fill the LEFT edge dark "
     "against the sky, dark heather crosses the BOTTOM edge, and the burning sky runs across the "
     "TOP.",
     "friction", "He asks the only question that matters to him, and gets nothing back."),

    ("knoll", "medium", NAR + NEI, 0.8, "low_angle",
     f"Low medium from the heather looking up at the little heathery knoll: nearest the camera at "
     f"the left {NEIGH}, the blue and white stripes of his flannel blazer bright against the "
     f"burning sky and his ash stick planted in the sand at his boot; further off at the right and "
     f"much smaller, {NARR}, his face turned out at the sand heaps.",
     "The camera keeps low under the knoll, a static shot from the height of the heather with the "
     "striped blazer nearest at the left; the neighbour brings his stick across to his other fist "
     "and leans his weight down onto it, the striped sleeve swinging at his hip; further off the "
     "Narrator turns his grey tweed shoulders a hand's breadth toward the sand heaps.",
     "in the heather below the knoll looking up, two long strides from the neighbour and five from "
     "the Narrator, a 35mm lens, a low angle. The low sun comes from the LEFT; the striped blazer "
     "reads bright and the heather and the pines are black",
     "The neighbour stands nearest at the LEFT third of the frame from his cream straw panama at "
     "the TOP third to the heather at the BOTTOM edge, his head a third of the height of the "
     "frame, the blue and white stripes of his blazer running down him and his ash stick planted "
     "at the BOTTOM LEFT. The Narrator stands further off at the RIGHT third in grey herringbone "
     "tweed, his head a sixth of the height of the frame. Knee-deep heather fills the BOTTOM half "
     "from the LEFT edge to the RIGHT edge, a young Scots pine stands black at the LEFT edge, and "
     "the burning lemon-yellow sky fills the TOP half.",
     "reaction", "Two strangers standing together is the whole of what anybody can offer."),

    # ---- dusk: the courage of the crowd comes back ---------------------------------
    ("dusk", "wide", [], 0.12, "crane_up",
     "Wide from the little heathery knoll at twilight: the common going grey-blue, the black tops "
     "of two young Scots pines at the left, the raw ring of sand quiet a hundred yards off with "
     "the thin mast standing above it, a long black band of people grown along the skyline beyond, "
     "and a pale straw panama showing small among the heather between.",
     "The camera rises above the heather with large amplitude until the black pine tops at the "
     "left and the ring of sand both stand inside the picture, travelling one long stride; the "
     "band on the skyline thickens as more figures come up onto it from the Woking side; the "
     "heather runs grey-blue under the lens and the pale panama travels on across the ground "
     "toward the band.",
     "above the knoll looking out over the heather, a 35mm lens. The last daylight comes low from "
     "the LEFT; the sand ring reads pale grey and the heather and the standing figures are black",
     "The long black band of people runs across the CENTRE of the frame on the skyline from the "
     "LEFT edge to the RIGHT third. The raw ring of flung yellow sand lies below it at the CENTRE "
     "RIGHT, a tenth of the height of the frame, with the thin mast above it. Grey-blue heather "
     "fills the BOTTOM half, two black pine tops stand at the LEFT edge, a pale straw panama shows "
     "small at the LEFT third, and a pale greenish-blue sky runs across the TOP third.",
     "transition", "The sun goes, the pit stays quiet, and the crowd reads that as permission."),

    ("dusk", "medium", [], 0.25, "pan_to",
     "Medium across the darkening heather at twilight: a grey-bearded carter in a moleskin "
     "waistcoat turning back toward Chobham with his coat over one arm, a bonneted farmwife behind "
     "him gathering a shawl under her chin, and a bare-headed young shopkeeper in a high celluloid "
     "collar standing on with his hands in his pockets.",
     "The camera pans left with small amplitude from the young shopkeeper across to the carter, "
     "travelling one short stride; the carter swings his coat up onto his shoulder at a walking "
     "pace and heads off toward Chobham with the farmwife after him; the heather whips shut behind "
     "her skirts and the shopkeeper turns his head back toward the sand.",
     "on the heather at a standing man's eye, three long strides from them, a 50mm lens. The last "
     "daylight comes low from the LEFT onto their faces; their collars read pale and the heather "
     "is black",
     "The grey-bearded carter fills the LEFT third of the frame from his bare head at the TOP "
     "third to the heather at the BOTTOM edge, his head a quarter of the height of the frame. The "
     "bonneted farmwife stands at the CENTRE with her shawl in both fists, the young shopkeeper at "
     "the RIGHT third with his hands in his pockets, black heather fills the BOTTOM third, and the "
     "pale greenish sky runs across the TOP half.",
     "transition", "Half the common decides it is over and goes home to its supper."),

    ("dusk", "insert", [], 0.45, "track_lateral",
     f"Insert on the pale greenish afterglow above the sand: the polished silver disk at the apex "
     f"of {MAST}, tilted over on its short yoke, the top joint of the dark bronze rod under it, "
     "the sky bare behind them.",
     "The camera tracks sideways to the right, a truck with small amplitude along the sky until "
     "the disk stands at the centre of the picture, travelling a finger's breadth; the disk swings "
     "round on its yoke and wobbles as it turns, the rim catching the afterglow once each turn; "
     "the rod under it leans a thumb's width and the disk goes on turning above it.",
     "on the heather looking out over the heaps at the sky, a 300mm lens. The last daylight stands "
     "low from the LEFT beyond the rod; the disk reads specular and the rod is black",
     "The pale greenish-blue afterglow fills the frame from the LEFT edge to the RIGHT edge and "
     "from the TOP edge to the BOTTOM edge. The polished silver disk stands at the CENTRE LEFT, a "
     "fifth of the height of the frame, tilted over on its yoke. The top joint of the dark bronze "
     "rod runs down from it toward the BOTTOM edge.",
     "friction", "Something in there is looking at us, and it is the only thing that moves."),

    ("dusk", "medium", [], 0.6, "low_angle",
     "Low medium across the darkening heather: people coming on toward the sand in ones and twos, "
     "a stout washerwoman in a black straw bonnet with a shawl gripped under her chin, a thin "
     "governess in grey halted with one boot up on a tussock, and a bricklayer in a flat cap with "
     "a cold clay pipe in his teeth further back, both hands in his belt.",
     "The camera keeps low under the walkers, a static shot from the height of the heather with "
     "all of them against the sky; the washerwoman comes on at a walking pace, halts dead with her "
     "shawl bunched in her fist, then starts forward again toward the sand; the heather whips shut "
     "behind her skirts and the governess takes her boot off the tussock and follows.",
     "in the heather below them looking up, three long strides from the washerwoman, a 35mm lens, "
     "a low angle. The last daylight comes low from the LEFT onto their faces; their collars read "
     "pale and the heather is black",
     "The washerwoman in the black straw bonnet stands at the CENTRE of the frame from her bonnet "
     "at the TOP third to the heather at the BOTTOM edge, her head a quarter of the height of the "
     "frame. The thin governess stands at the LEFT third with one boot up on a tussock, the "
     "bricklayer small at the RIGHT edge, black heather fills the BOTTOM third, and the pale "
     "greenish sky runs across the TOP half.",
     "friction", "Advance, stop, watch, advance: a common learning to be brave together."),

    ("dusk", "medium_close", ["unnamed_newspaper_boy"], 0.75, "locked",
     f"Medium close of {BOY} at the gravel mouth of the old sand-pits at twilight, straightened up "
     "over the shafts of a low green barrow heaped with apples, turned toward the camera with his "
     "cap shoved back, the raw yellow digging face behind him.",
     "The camera holds a static shot on the boy, keeping his face in the centre of frame; he hauls "
     "the shafts up against his thighs, throws his chin up and calls to the camera over the top of "
     "the apples; his cap slides forward on his forehead and one hand comes off the shaft and "
     "swings back at the heather behind him.",
     "on the gravel floor of the sand-pits level with his eyes, two paces from him, a 50mm lens. "
     "The last daylight comes low from the RIGHT onto his face; his cheek reads pale and the "
     "digging face behind him is black",
     "The boy's head and shoulders fill the CENTRE of the frame from his grey flat cap at the TOP "
     "third to the ginger corduroy at the BOTTOM edge, his head a third of the frame's height, lit "
     "from the RIGHT. The heaped apples and the pale shafts of the barrow cross the BOTTOM edge, "
     "the raw yellow digging face rises at the LEFT third, and a strip of pale greenish sky shows "
     "across the TOP edge.",
     "friction", "Courage arrives, and the first use anybody makes of it is to take a barrow."),

    # OWNER 2026-09-20: "just horse head can't exist, it should be whole horse, we
    # need to focus on the horse head." This was written as a head in a nosebag and
    # drew exactly that -- a head with no body over the gravel, three renders
    # running. Appending "the panel contains the horse whole" to the prompt did not
    # move it: the plan's own opening clause leads, and it said head. So the whole
    # animal is in the plan's first sentence and the head is what the light and the
    # lens attend to.
    # Back to `insert` after the G-VARIETY gate counted 4 where 28 shots want 5.
    # The size was only moved to `medium` because `insert` had been carried
    # through as "the panel holds the object alone", which crops a horse to a
    # head. That wording is gone -- an insert now "comes in close on one
    # subject, which fills most of the frame" -- and a whole horse filling the
    # frame is exactly that.
    ("dusk", "insert", [], 0.9, "track_lateral",
     "Insert down on the gravel floor of the sand-pits at twilight, the raw yellow sand wall of "
     "the pit standing up close behind: ONE BLACK CAB HORSE, entire and unbroken inside the "
     "frame. A heavy-shouldered gelding about fifteen hands, black all over, deep in the chest, "
     "with a short upright mane, a long tail to the hocks and one narrow white blaze down its "
     "face. A padded collar sits on its shoulders and blinkers stand at its bridle. All four "
     "legs are down on the gravel and the two long shafts of a hansom run back from its "
     "shoulders to the dark cab. Its head is lowered into a pale canvas nosebag.",
     "The camera tracks sideways to the left, a truck with small amplitude past the standing "
     "horse until the cab behind it comes into the picture, travelling a finger's breadth; the "
     "horse works its jaw in the nosebag, throws its head up against the strap and drives its "
     "nose back down into the bag; the mane swings over the strap and both ears come round "
     "toward the heather.",
     "on the gravel three paces from the horse, low at the height of its chest, a 50mm lens. The "
     "last daylight comes low from the LEFT; the pale canvas nosebag and the white blaze catch "
     "it, the raw sand wall of the pit behind reads pale grey-blue, and the horse, the harness "
     "and the hansom are black",
     "THE FOCUS OF THE PICTURE IS THE HORSE'S LOWERED HEAD AND THE PALE NOSEBAG: they sit at the "
     "CENTRE of the frame, they are where the last daylight falls, they are the brightest and "
     "the sharpest thing in it, and the eye goes there first. The rest of the horse reads "
     "clearly around that: its ears at the TOP third, its black neck and shoulder running back "
     "to the RIGHT, its barrel and its four legs down to the hooves on the gravel at the BOTTOM "
     "edge, the shafts and the dark hansom at the RIGHT edge. The raw yellow sand wall of the "
     "pit rises close behind the horse and fills the whole TOP and the LEFT of the frame, "
     "closing the picture off above its ears.",
     "friction", "The one witness in the chapter that will never get a warning."),

    # ---- flag: he goes in with them, and the Deputation goes out ------------------
    ("flag", "medium_close", NAR, 0.1, "locked",
     f"Medium close of {NARR} at dusk on the black heather, turned square to the camera with the "
     "last light along one side of his bare head, his hair flat where the hat has been, the straw "
     "boater held down in his fist low at the left of the picture.",
     "The camera holds a static shot on the Narrator, keeping his face in the centre of frame; he "
     "pulls a breath in, brings his fist up with the boater in it and sets the hat back on his "
     "head; his hand comes down off the brim and his shoulders square toward the camera.",
     "on the heather level with his eyes, two paces from him, a 50mm lens. The last daylight comes "
     "low from the RIGHT onto his face; his cheek reads pale and the heather behind him is black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his bare head at the TOP "
     "third to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit from "
     "the RIGHT, the straw boater down in his fist at the BOTTOM LEFT. Black heather crosses the "
     "BOTTOM edge and the LEFT third, the pale sand ring shows small at the RIGHT third, and the "
     "deep blue sky fills the TOP.",
     "reaction", "He puts the hat back on. That is a man deciding something."),

    ("flag", "medium", NAR, 0.3, "follow",
     f"Medium of {NARR} at dusk walking away from the camera into the black heather toward the raw "
     "ring of sand, seen from behind at the waist up, other dark figures out on the heather to "
     "either side of him going the same way, the pale sand ring beyond.",
     "The camera tracks behind the Narrator at a walking pace with large amplitude, coming on "
     "through the heather until the ring of sand stands at the centre of the picture, travelling "
     "two long strides; he drives one boot and then the other forward through the heather and "
     "lengthens his stride as the sand comes up; the heather rakes past his thighs and his right "
     "arm swings up across his chest.",
     "on the heather two long strides behind him at a standing man's chest, a 35mm lens. The last "
     "daylight comes low from the LEFT; the sand ring reads pale grey and the heather and the "
     "figures are black",
     "The Narrator fills the CENTRE of the frame from his straw boater at the TOP third to the "
     "heather at the BOTTOM edge, his back to the camera, his head a fifth of the height of the "
     "frame. Two other dark figures walk at the LEFT third and the RIGHT edge, the raw ring of "
     "flung yellow sand lies across the CENTRE beyond them a tenth of the height of the frame, and "
     "the deep blue sky runs across the TOP third.",
     "turn", "He has kept his hundred yards all evening. He spends them."),

    ("flag", "wide", [], 0.5, "pan_to",
     "Wide across the black heather at dusk: two black pine tops at the left of the picture, a "
     "little wedge of dark figures out beyond the raw ring of sand walking in toward it with a "
     "white fleck of linen carried above them as wide as one of their heads, and a broken ring "
     "of other dark figures spread wide across the heather behind.",
     "The camera pans right with large amplitude from the black pine tops at the left across the "
     "heather to the wedge of figures under the white fleck, travelling two long strides; the "
     "wedge comes on toward the sand at a walking pace, the fleck swaying over it at each stride; "
     "the heather closes behind them and the broken ring of figures behind draws in after them.",
     "on the heather at a standing man's eye, out across the heather to the wedge, a 35mm lens. "
     "The last of the daylight stands low from the LEFT; the white linen reads bright and the "
     "heather and the figures read black to the horizon",
     "Black heather fills the BOTTOM third of the frame from the LEFT edge to the RIGHT edge. Two "
     "black pine tops stand at the LEFT edge. The raw ring of flung yellow sand lies across the "
     "CENTRE, a tenth of the height of the frame. The wedge of dark figures stands beyond it at "
     "the CENTRE RIGHT with the white fleck of linen above them, and the deep blue sky fills the "
     "TOP half.",
     "spike", "A tablecloth on a pole. It is the best idea anybody here has had."),

    ("flag", "medium", [], 0.65, "tilt_up",
     "Medium on the white flag out over the heather at dusk: the small square of white linen on "
     "the top of a long pale pole standing against the deep blue sky, the dark shoulders and hat "
     "of the bearer small below it, black heather across the bottom of the picture.",
     "The camera tilts up with large amplitude from the bearer's dark shoulders to the linen at "
     "the top of the pole, travelling two long strides; the pole swings over to the right and the "
     "linen runs out flat, then hauls back to the left and the linen cracks over; the cord snaps "
     "taut where it is lashed and the pole leans a forearm further out over the heather.",
     "on the heather looking out at the bearer, a 300mm lens. The last of the daylight stands low "
     "from the LEFT along the linen; the linen reads bright and the shoulders and the heather read "
     "black",
     "The square of white linen stands at the CENTRE of the frame just below the TOP third, an "
     "eighth of the height of the frame. The pale pole runs down from it to the bearer's dark "
     "shoulders and hat at the BOTTOM third, black heather crosses the BOTTOM edge, and the deep "
     "blue sky fills the TOP and both edges.",
     "spike", "Flutter, flutter: the whole of human diplomacy in a creased tablecloth."),

    ("flag", "medium", [], 0.8, "track_lateral",
     "Medium along the black heather at dusk with the ring of sand beyond: a thin governess in "
     "grey standing with both hands at her throat, a heavy carter in a bowler two paces in front "
     "of her with his fists at his sides, and a boy in a sailor collar crouched in the heather at "
     "their feet, all three faces turned out at the sand.",
     "The camera tracks sideways to the right, a truck with small amplitude past the governess "
     "until the carter in the bowler stands at the centre of the picture, travelling one short "
     "stride; the carter goes two paces further out toward the sand at a walking pace and halts "
     "with his chin up; the governess follows with her skirt gathered in one fist and the boy "
     "climbs onto his knees in the heather.",
     "on the heather at a standing man's eye, two long strides from the governess, a 50mm lens. "
     "The last of the daylight stands low from the LEFT onto their faces; their collars read pale "
     "and the heather reads black",
     "The heavy carter in the bowler stands at the CENTRE of the frame from his hat at the TOP "
     "third to the heather at the BOTTOM edge, his head a quarter of the height of the frame. The "
     "thin governess in grey stands at the LEFT third, the boy in the sailor collar crouches at "
     "the BOTTOM RIGHT, the pale sand ring lies across the CENTRE RIGHT beyond them, and the deep "
     "blue sky fills the TOP third.",
     "friction", "The ring closes. Everybody decides this is safe at the same moment."),

    ("flag", "insert", [], 0.95, "crane_up",
     "Insert on the deep blue sky above the raw ring of sand at dusk: one puff of luminous "
     "greenish smoke standing clear of the sand in the still air, its edges bright, the black line "
     "of the sand heaps running across the bottom of the picture.",
     "The camera rises above the heather with small amplitude, coming up with the smoke until "
     "three puffs stand one above another inside the picture, travelling a finger's breadth; a "
     "second puff and then a third drive up out of the sand and go on up into the still air; the "
     "smoke spreads and goes thin at the top of the frame and the sky behind it darkens.",
     "on the heather looking out over the heaps at the sky, a 135mm lens. The last of the daylight "
     "stands low from the LEFT; the green smoke reads bright and the sand heaps read black",
     "The deep blue sky fills the frame from the LEFT edge to the RIGHT edge and from the TOP edge "
     "to the BOTTOM third. One puff of luminous greenish smoke stands at the CENTRE just above the "
     "sand, a fifth of the height of the frame, and the black line of the sand heaps runs across "
     "the BOTTOM third.",
     "spike", "The first answer we get is not a word. It is a flash and three puffs."),

    # ---- ray: the humped shape, and the invisible sword --------------------------
    ("ray", "medium", [], 0.2, "tilt_up",
     "Medium on the raw ring of sand at nightfall: the top of a smooth humped black dome, like "
     "the curved back of a great whale, just rising over the rim out of the pit, the thin "
     "jointed mast standing beside it against the "
     "last greenish light, the heather black across the bottom of the picture.",
     "The camera tilts up with small amplitude from the black heather to the rim of the sand, "
     "travelling a hand's breadth; the dome rides up over the rim until its shallow funnel mouth "
     "is clear, swings the mouth round toward the heather, and a pale flicker runs out of it and "
     "travels over the ground; the sand streams off the dome's flank and the mast leans after it.",
     "on the heather looking out across the heaps, a 135mm lens. The last greenish daylight stands "
     "low from the LEFT; the sand ring reads pale grey and the dome and the heather are black",
     "The black heather crosses the BOTTOM third of the frame from the LEFT edge to the RIGHT "
     "edge. The raw ring of flung yellow sand runs across the CENTRE, and the crown of the smooth "
     "humped black dome shows over its rim at the CENTRE at a sixth of the height of the frame. "
     "The thin jointed mast stands at the CENTRE RIGHT and the last greenish light fills the TOP "
     "third.",
     "spike", "Not a man and not a machine we have a word for: a hump with a mouth."),

    ("ray", "medium", [], 0.4, "locked",
     "Medium on the men out beyond the sand at nightfall: a scattered wedge of small dark figures "
     "halted on the black heather under the white fleck of linen on its pole, a tall bare-headed "
     "one with an arm half raised, a stooped one leaning on a stick, a square one in a bowler with "
     "both fists on the pole, all their faces turned back toward the pit.",
     "The camera holds a static shot on the wedge of men, keeping the white fleck in the upper "
     "centre of frame; a green glare washes over them and the whole wedge flashes out pale and "
     "goes dark again, and the tall bare-headed one brings his raised arm down across his chest; "
     "the linen goes slack on its cord and the pole swings back toward the pit.",
     "on the heather looking out at the wedge, a 300mm lens. The last greenish daylight stands low "
     "from the LEFT with a green glare off the pit; the wedge reads pallid green and the heather "
     "and the figures are black",
     "The scattered dark figures stand at the CENTRE and the RIGHT third of the frame from their "
     "hats at the CENTRE to the heather at the BOTTOM third, each figure a fifth of the height of "
     "the frame. The white fleck of linen stands above them at the TOP third on its pale pole, "
     "black heather fills the BOTTOM third, and the darkening sky fills the TOP half.",
     "spike", "The light that shows us their shapes is the light that has come to end them."),

    ("ray", "medium", [], 0.6, "track_lateral",
     "Medium on the black heather beyond the sand at nightfall: a heavy figure in a frock coat "
     "standing dark among the others with both arms at his sides, two smaller dark shapes behind "
     "him, the white linen still up on its pole at the left of the picture.",
     "The camera tracks sideways to the left, a truck with small amplitude along the wedge until "
     "the heavy figure stands at the centre of the picture, travelling one short stride; white "
     "flame springs up his coat from his knees to his collar and he drops onto one hip in the "
     "heather; the furze under him takes fire with a flat thud and the two shapes behind drive "
     "their heels into the ground.",
     "on the heather looking out over the heaps, a 300mm lens. The last greenish daylight stands "
     "low from the LEFT and white flame breaks out at the CENTRE among them; the burning figure "
     "reads white and the heather and the other shapes are black",
     "The heavy figure in the frock coat stands at the CENTRE of the frame from his head at the "
     "CENTRE to the heather at the BOTTOM third, a fifth of the height of the frame, dark against "
     "the ground. Two smaller dark shapes stand at the RIGHT third, the white linen stands on its "
     "pole at the LEFT third, black heather fills the BOTTOM half, and the last greenish light "
     "runs across the TOP third.",
     "answer", "Each man turned to fire in his turn, and the word death has not arrived."),

    ("ray", "insert", [], 0.85, "pan_to",
     f"Insert low in the knee-deep heather at nightfall: the black knees and boots of {NARR} "
     "standing at the left of the picture, a dry furze bush at the centre with its spines standing "
     "out black, the ground smoking in a curving line through the heather between them, and the "
     "pale blur of the sand ring beyond.",
     "The camera pans right with small amplitude from the Narrator's black knees across to the "
     "furze bush, travelling a finger's breadth; the whole bush takes fire at once with a flat "
     "thud and burns white from the middle out, and the heather beyond it smokes and cracks along "
     "the same curving line; the flame throws up a sheet of sparks and the burnt heather stems "
     "curl over toward the camera.",
     "in the heather at the height of a kneeling man, two long strides from the bush, a 50mm lens. "
     "White flame breaks out at the CENTRE; the burning bush reads white and the heather around it "
     "is black",
     "The Narrator's black knees and boots stand at the LEFT third of the frame from the TOP third "
     "to the BOTTOM edge. The dry furze bush stands at the CENTRE from the CENTRE to the BOTTOM "
     "edge, a third of the height of the frame, its spines standing out black. Knee-deep heather "
     "fills the frame from the LEFT edge to the RIGHT edge around them, the smoking curved line of "
     "ground runs across the CENTRE between them, and the pale blur of the sand ring shows at the "
     "TOP RIGHT.",
     "answer", "The sword is drawn between him and them, and it does not turn his way."),

    # ---- dark: void of men, and the road home -------------------------------------
    ("dark", "wide", [], 0.2, "crane_up",
     f"Wide of the common in the dark: the heather black right to the horizon, a pale sandy road "
     f"running grey across the middle distance, {MAST} standing alone above the sand ring beyond "
     "it, burning furze bushes glowing here and there over the ground, and spires of flame going "
     "up from the houses beyond Woking under the first stars.",
     "The camera rises above the black heather with large amplitude until the pale road and the "
     "ring of sand both stand inside the picture, travelling two long strides; the fires along the "
     "ground burn up higher as the wind comes over the heath, and the disk at the top of the mast "
     "turns over against the afterglow; the smoke off the burning bushes runs across the pale road.",
     "above the heather looking out over the road to the sand ring, a 35mm lens. A low fire of "
     "burning furze stands at the LEFT; the road reads grey and pale and the heather and the roofs "
     "are black",
     "Black heather fills the BOTTOM half of the frame from the LEFT edge to the RIGHT edge with a "
     "burning furze bush at the LEFT third. The pale sandy road runs grey across the CENTRE, the "
     "raw ring of sand lies beyond it at the CENTRE, and the thin jointed mast stands above it at "
     "a tenth of the height of the frame. The pale greenish afterglow stands low at the TOP LEFT "
     "behind the black pine tops, and the black roofs of Woking lie at the RIGHT third with spires "
     "of flame above them.",
     "runout", "Nothing is changed except that everyone who walked out there is gone."),

    ("dark", "medium_close", NAR, 0.5, "low_angle",
     f"Low medium close of {NARR} on the black heather with the firelight on one side of his face, "
     "his straw boater jammed down over his hair, his mouth open, the pale afterglow behind him.",
     "The camera keeps low under the Narrator, a static shot from the height of the heather with "
     "his face in the centre of frame; his head comes round off the sand ring and his whole body "
     "follows it, his shoulders driving forward as he throws his weight off his back foot; the "
     "heather tears past his thighs and his near shoulder drives forward past the lens.",
     "in the heather below him looking up at his face, two paces from him, a 50mm lens, a low "
     "angle. A low fire of burning furze stands at the LEFT; his cheek reads warm and bright and "
     "the heather is black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his straw boater at the "
     "TOP third to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit "
     "from the LEFT. Black heather crosses the BOTTOM edge and the RIGHT third, a burning furze "
     "bush glows small at the LEFT edge, and the pale greenish afterglow fills the TOP.",
     "runout", "Fear arrives like a thing thrown at him from outside, and he runs."),

    ("dark", "medium_close", NEI, 0.8, "locked",
     f"Medium close of {NEIGH} on the pale sandy road in the dark, his head bare and his grey hair "
     "wild and his striped blazer buttoned askew, the firelight full on his hollow face, a burning "
     "furze bush at the left of the picture behind him.",
     "The camera holds a static shot on the neighbour, keeping his face in the centre of frame; he "
     "comes up out of the heather onto the road with his chest heaving and says it at the lens "
     "with his stride still going; his striped shoulder comes round past the camera and the stick "
     "swings forward and goes down into the sand of the road.",
     "on the road level with his eyes, two paces from him, a 50mm lens. A low fire of burning "
     "furze stands at the LEFT behind him; his hollow cheek reads warm and bright and the road and "
     "the heather are black",
     "The neighbour's head and shoulders fill the CENTRE of the frame from his wild grey hair at "
     "the TOP third to the striped flannel at the BOTTOM edge, his head a third of the "
     "frame's height, lit from the LEFT. The burning furze glows at the LEFT third behind him, the "
     "pale sandy road crosses the BOTTOM edge, and the black heather and the greenish afterglow "
     "fill the TOP RIGHT.",
     "button", "The same four words, an hour later, by firelight. He has no others, and neither have we."),
]

# shot -> (beat_s, coda_s); anything unnamed gets (0.6, 0.0)
BEATS = {0: (0.8, 0.0), 2: (0.8, 0.0), 3: (0.8, 0.4), 4: (1.5, 3.3), 8: (1.0, 0.6),
         9: (0.8, 0.0), 11: (0.8, 0.6), 14: (1.4, 2.0), 16: (1.0, 0.4), 18: (0.8, 0.0),
         19: (1.5, 1.9), 20: (0.8, 0.4), 21: (0.8, 0.0), 22: (0.8, 0.0), 23: (0.8, 0.0),
         24: (0.8, 0.4), 25: (0.8, 0.0), 26: (1.2, 0.4), 27: (1.0, 2.0)}

TURNS = {16: "a man who has kept his hundred yards all evening -> a man closing on the pit with the rest",
         3: "a crowd waiting for men to climb out -> a crowd watching an instrument go up",
         20: "a deputation going out to be answered -> a common that has been answered",
         23: "men walking out under a white flag -> men turned to fire in their turn",
         27: "a man with one sentence for a wonder -> the same sentence for a massacre"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "A kind of fascination held me where I stood.", 0),
    ("narration", "unnamed_first_person_narrator",
     "I was a battleground of fear and curiosity.", 1),
    ("narration", "unnamed_first_person_narrator",
     "Whatever they were doing down there, they were doing it without a thought of us.", 2),
    ("narration", "unnamed_first_person_narrator",
     "Nothing climbed out to meet us. Something down there put up an eye.", 3),
    ("narration", "unnamed_first_person_narrator",
     "One man stood near me. I knew his face from my road, and not his name.", 5),
    ("dialogue", "unnamed_neighbour",
     "What ugly brutes. Good God, what ugly brutes.", 6),
    ("dialogue", "unnamed_first_person_narrator",
     "Did you see a man in the pit? Did anybody fetch him out?", 7),
    ("narration", "unnamed_first_person_narrator",
     "He gave me no answer. We stood together, and that was some comfort.", 8),
    ("narration", "unnamed_first_person_narrator",
     "The sunset faded. My neighbour went off towards the crowd at Woking without a word.", 9),
    ("narration", "unnamed_first_person_narrator",
     "The little knot on our own side broke up and went off to supper.", 10),
    ("narration", "unnamed_first_person_narrator",
     "Their mirror turned above the heaps all evening and watched what we did.", 11),
    ("narration", "unnamed_first_person_narrator",
     "The quiet was what gave them courage. I could not tell if it gave me any.", 12),
    ("dialogue", "unnamed_newspaper_boy",
     "They are all in close now. Nobody is minding a barrow tonight.", 13),
    ("narration", "unnamed_first_person_narrator",
     "I had walked out to see the thing. That was my whole excuse.", 15),
    ("narration", "unnamed_first_person_narrator",
     "I did not decide to go in. I only stopped deciding to stay back.", 16),
    ("narration", "unnamed_first_person_narrator",
     "Out of Horsell came a handful of men, the first of them waving something white.", 17),
    ("narration", "unnamed_first_person_narrator",
     "A tablecloth on a pole: our argument that we could be talked to.", 18),
    ("narration", "unnamed_first_person_narrator",
     "A hissing came across the heather, so faint I thought it was my ears.", 20),
    ("narration", "unnamed_first_person_narrator",
     "The hissing became a humming, and a humped shape came out of the sand.", 21),
    ("narration", "unnamed_first_person_narrator",
     "Ogilvy was out there, and Stent, and Henderson. I only learned that afterwards.", 22),
    ("narration", "unnamed_first_person_narrator",
     "I watched them go down and did not know I was watching death.", 23),
    ("narration", "unnamed_first_person_narrator",
     "A horse screamed in the pits and stopped. The heat came between me and them.", 24),
    ("narration", "unnamed_first_person_narrator",
     "Had it swung a yard further round, it would have had me where I stood.", 25),
    ("narration", "unnamed_first_person_narrator",
     "Fear fell on me from outside. I ran, and did not look back.", 26),
    ("dialogue", "unnamed_neighbour",
     "What ugly brutes. Good God, what ugly brutes.", 27),
]

BEDS = [{"from_shot": 0, "tone": "plain"}, {"from_shot": 5, "tone": "uneasy"},
        {"from_shot": 11, "tone": "grave"}, {"from_shot": 17, "tone": "thrilling"},
        {"from_shot": 25, "tone": "grave"}]

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
    return dict(number=5, title="The Heat-Ray",
                question="Today, can the narrator go near the pit and come back?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 24",
                beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT.parent / "moves.json").write_text(json.dumps(MOVES, indent=1), encoding="utf-8")
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    counts = {m: list(MOVES.values()).count(m) for m in set(MOVES.values())}
    silent = [s["index"] for s in doc["shots"]
              if not any(l["shot"] == s["index"] for l in doc["lines"])]
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words; "
          f"dialogue {said / words:.1%}; silent shots {silent}")
    print(f"measured projection at 2.72 w/s: "
          f"{words / 2.72 + sum(s['beat_s'] + s['coda_s'] + 0.5 for s in doc['shots']):.0f}s")
    print(f"moves: {counts}")
    print(OUT)
