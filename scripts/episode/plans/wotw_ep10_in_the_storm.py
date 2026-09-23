r"""The War of the Worlds, episode 10 -- "In the Storm", chapter 10.

THE BRICK.  A man who wanted to be in at the death drives back into the dark
to keep a promise, and the death he is in at is the man he promised.

  QUESTION  Why does he drive back into it? He promised the landlord his cart
            by midnight -- and "I wanted to be in at the death".
  TURN      shot 17. He stoops in the lane and turns the dead man over: the
            lead acting on another person, by his own choice ("overcoming the
            repugnance natural to one who had never before touched a dead body").
  ANSWER    shot 18: the face in the third flash is the landlord of the Spotted
            Dog, whose cart he took. He came back to be in at a death, and this
            is the one he gets.
  BUTTON    line 25, the hussar at the head of the lane: "Down to the bridge,
            all of you! Keep moving!" CHAPTER 10 HAS NO QUOTED SPEECH. The
            contract needs a non-lead line on camera to close, so the words are
            made from the book's own "voices and the sound of feet" toward
            Maybury Bridge, and the speaker is ep09's hussar, whose sheet and
            voice exist. Invented, and said so (owner's call to overrule;
            decided under "decide and go", 2026-09-23). So is the narrator's
            "Steady! Steady, boy!" to the bolting horse: without it dialogue
            falls under the 5 % floor.

THE TRIPODS ARE SEEN AS THE BOOK SEES THEM: "all vaguely for the flickering of
the lightning". Two far silhouettes, one heeling stride, one rush through the
pines, one near pass, one brass dome turning -- and the sheet drawn for them
has three legs (refs/props/fighting_machine/sheet.png, v3 of six draws).
"Tripod" is said ONLY in those six shots: the word stages the sheet.

THE STORM IS IN THE WORDS AS SMALL, FAR BOLTS. A whole-frame flash steps the
brightness 34-53 between frames against the hard cut wall of 30 (ep10 prep,
measured on the storm references), and "bright as day" reads as day to the
content gate. So the lightning stands in the far clouds and nothing is lit
"like daylight".

WHAT TODAY'S GATES ASK OF THIS PLAN (2026-09-23): every move aims at a noun its
own at_rest holds (G-AIM); no sideways truck across a person anchored to the
set (G-ANCHOR); every setup says "night" (the panel gate's night control reads
the words); tags carry their own chapter, so this plan regenerates whatever
chapter is bound later. The horse is never shown dead; the landlord is a face
with closed eyes and rain on it, nothing more.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep10" / "plan.json"

WHERE = "Surrey, 1894"
LIGHT = "violet lightning from the west, black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

from studio import cast_refs  # noqa: E402

NARRATOR = cast_refs.tag(BOOK, "unnamed_first_person_narrator", "the narrator", [
    "Neat close-trimmed dark brown moustache", "Bareheaded, hair plastered flat to the brow by rain",
    "Mid-grey tweed lounge suit soaked to dark charcoal and clinging"], chapter=10)
WIFE = cast_refs.tag(BOOK, "narrators_wife", "the narrator's wife", [
    "Thick chestnut-auburn hair", "Sage-green linen walking costume",
    "Small sage-green felt toque with a cream ostrich tip"], chapter=10)
LANDLORD = cast_refs.tag(BOOK, "unnamed_landlord", "the landlord of the Spotted Dog", [
    "Heavy grey-brown mutton-chop whiskers joined to a full moustache",
    "Bare head with hair plastered flat by rain"], chapter=10)
HUSSAR = cast_refs.tag(BOOK, "unnamed_hussar", "the hussar", [
    "Brown curly hair cropped close to the skull", "Clean-shaven boyish jaw",
    "dark rifle-green serge hussar jacket with yellow cord frogging"], chapter=10)

# ---- the five places, each at NIGHT, naming its light and where it comes from ----
DOORWAY_NIGHT = (
    "the front of a pale two-storey Georgian house at Leatherhead at night in 1894, calm before the "
    "storm: rows of lit sash windows glowing warm yellow, an arched front door with a fanlight and a "
    "lamp either side standing open at the top of three stone steps, a gravel drive running up to it "
    "between dark shrubs, two white gate piers with their gates swung open at the near end, a gas "
    "lantern on a post at the left, and heavy clouds driving fast across a black sky; the light is "
    "lamplight from the open door and the lit windows, and the gas lantern at the LEFT, so the "
    "gravel reads warm near the door and the garden reads black")
ROAD_NIGHT = (
    "a country road at night in 1894 climbing a little hill between high hedges and dark pines "
    "toward Maybury Hill, under a thunderstorm: the pale sandy road running from the near edge up "
    "and away over the rise, a dark field beyond the hedge on the left, and far ahead along the "
    "western horizon a blood-red glow with masses of black and red smoke creeping up into the "
    "driving storm clouds; the light is the red glow on the horizon ahead at the LEFT and small "
    "far bolts of violet lightning in the clouds, so the road reads pale grey, the hedges read "
    "black and the sky reads red low down and black above")
POOL_NIGHT = (
    "a shallow pool of black rainwater beside a gravel road at the foot of Maybury Hill at night in "
    "1894, in a thunderstorm: hailstones dimpling the black water, a big clump of dark furze with a "
    "few yellow blossoms rising behind the pool, a young pine and wet heather beyond, the gravel "
    "verge of the road along the right, and storm clouds low over the heath with a far bolt of "
    "violet lightning at the top right; the light is the violet lightning from the right and "
    "its reflection in the pool, so the water reads black and glinting, the furze reads black-green "
    "and the gravel reads grey")
LANE_NIGHT = (
    "a steep sandy lane climbing Maybury Hill toward the College Arms at night in 1894, in a "
    "thunderstorm: the lane running up from the near edge between a weathered grey paling fence "
    "along the left and cottage gardens on the right, a white cottage with lit windows and red roses "
    "at the right, brick and weatherboard houses with one lit window higher up the lane, the College "
    "Arms at the top of it, and storm clouds with a far bolt of violet lightning over the hill; the "
    "light is the lit cottage windows at the RIGHT and far violet lightning from the TOP, so the "
    "sand reads pale, the palings read grey and the gardens read black")
HALL_NIGHT = (
    "the front hall of the narrator's own house at Maybury at night in 1894, in a storm: a narrow "
    "hall with a patterned tiled floor, the dark wooden staircase rising on the right with a turned "
    "newel post and banister, the front door shut and bolted at the far end with a fanlight over it, "
    "a coat stand and a hall chair against the papered wall on the left, and the house dark; the "
    "light is grey storm light through the fanlight BEHIND the door at the far end, so the tiles "
    "read grey, the stair reads black and the walls read dark")

# ---- the geometry of each place: WHERE things are, in cells --------------------------
GEO_DOORWAY = (
    "The gravel drive runs from the BOTTOM CENTRE up to the lit front door at the CENTRE between two "
    "white gate piers standing at the BOTTOM LEFT and the BOTTOM RIGHT with their gates swung open. "
    "The pale house fills the TOP half from the LEFT third to the RIGHT third with its lit windows "
    "in rows, the gas lantern stands at the LEFT edge, dark shrubs fill the LEFT and RIGHT edges, "
    "and driving clouds fill the TOP edge.")
GEO_ROAD = (
    "The pale road runs from the BOTTOM CENTRE straight up and away over the rise at the CENTRE, a "
    "black hedge lines it along the LEFT third with the dark field beyond, a tall hedge and dark "
    "pines line it along the RIGHT third, the blood-red glow with its black smoke stands low along "
    "the horizon at the CENTRE LEFT, a far violet bolt stands in the clouds at the TOP LEFT, and "
    "black storm clouds fill the TOP third.")
GEO_POOL = (
    "The shallow black pool lies across the BOTTOM half from the LEFT third to the CENTRE RIGHT, "
    "dimpled with hail. The dark clump of furze rises behind it at the CENTRE LEFT to the TOP third, "
    "the young pine stands behind the furze at the CENTRE, the grey gravel verge runs along the "
    "RIGHT edge, and the storm clouds with a far violet bolt fill the TOP RIGHT.")
GEO_LANE = (
    "The pale sandy lane runs from the BOTTOM CENTRE up and away to the TOP CENTRE, the grey paling "
    "fence runs along the LEFT third from the BOTTOM edge up the hill, the white cottage with its lit "
    "windows and red roses stands at the RIGHT third, the brick and weatherboard houses stand higher "
    "up at the CENTRE LEFT, and storm clouds with a far violet bolt fill the TOP edge.")
GEO_HALL = (
    "The tiled floor runs from the BOTTOM edge away to the shut front door at the CENTRE, its "
    "fanlight glowing grey above it in the TOP third. The dark staircase rises along the RIGHT third "
    "from the BOTTOM RIGHT with its newel post at the RIGHT edge, and the coat stand and hall chair "
    "stand against the dark papered wall at the LEFT third.")

# ---- the cells of every tighter shot: where ITS subject sits (G-SCALE) ---------------
GEO_WIFE = (
    "The narrator's wife stands at the CENTRE in the lit doorway, the warm light of the passage "
    "behind her filling the TOP half, the door frame at the LEFT edge and the RIGHT edge. Her head "
    "is a third of the frame's height, and her face is pale in the lamplight.")
GEO_CLIMB = (
    "The narrator stands with his back to the camera at the CENTRE RIGHT, one boot on the step of "
    "the dog cart, which stands along the LEFT half with its two lamps lit and the horse's dark "
    "rump at the LEFT edge. The lit house is behind them in the TOP third.")
GEO_REINS = (
    "The narrator sits at the CENTRE on the seat of the dog cart with the reins in both hands, "
    "hunched against the rain, the dark hedge behind him at the LEFT third and the storm sky with a "
    "far violet bolt in the TOP RIGHT. His head is a quarter of the frame's height.")
GEO_FAR_TRIPOD = (
    "The black silhouette of a tripod stands far off on the slope at the CENTRE RIGHT, its three "
    "thin legs a tenth of the height of the frame, higher than the pines around it. The dark field "
    "fills the BOTTOM half, the hedge crosses the BOTTOM edge, and storm clouds fill the TOP third.")
GEO_HEELING = (
    "A tripod heels over across the CENTRE, one leg lifted high to the LEFT and two planted at the "
    "RIGHT, a fifth of the height of the frame, over the dark heather that fills the BOTTOM third. "
    "The red glow stands low along the horizon at the RIGHT third and storm clouds fill the TOP.")
GEO_RUSH = (
    "A tripod bursts out of the dark pines at the CENTRE, its brass dome at the TOP third and its "
    "three legs reaching down to the BOTTOM edge, snapped pine trunks falling away at the LEFT third "
    "and the RIGHT third, and the pale road running into the BOTTOM CENTRE toward it.")
GEO_WHEEL = (
    "The yellow-spoked wheel of the overturned dog cart stands at the CENTRE, turning, the black "
    "bulk of the cart behind it filling the RIGHT half and the black pool across the BOTTOM third, "
    "dimpled with hail, with the dark furze at the LEFT edge.")
GEO_CROUCH = (
    "The narrator crouches under the clump of furze at the CENTRE LEFT, his feet in the black water "
    "at the BOTTOM LEFT, soaked and shivering, the pool across the BOTTOM half and the gravel verge "
    "at the RIGHT edge. His head is a quarter of the frame's height.")
GEO_PASS = (
    "A tripod strides past at the CENTRE, seen from low down, its three legs reaching from the "
    "BOTTOM edge to the TOP third, one long tentacle at the LEFT third gripping a young pine, the "
    "white basket slung behind the body at the TOP RIGHT, green smoke at its knee joints, and wet "
    "heather across the BOTTOM edge.")
GEO_DOME = (
    "The brass dome of a tripod fills the CENTRE, its band of dark green glass across the middle "
    "of it, the white body under it at the BOTTOM third and storm clouds with a far violet bolt "
    "filling the TOP third and the RIGHT edge.")
GEO_TWO = (
    "Two tripods stand half a mile off at the CENTRE, stooping over a pale cylinder in the field "
    "between them, each a fifth of the height of the frame. The dark hedge tops cross the BOTTOM "
    "third and storm clouds fill the TOP third.")
GEO_WALK = (
    "The narrator walks up the pale lane at the CENTRE, a quarter of the height of the frame, the "
    "grey palings along the LEFT third and the lit cottage at the RIGHT third, the lane climbing "
    "away to the TOP CENTRE.")
GEO_BLUNDER = (
    "The narrator staggers back at the CENTRE LEFT as a stranger in a dark coat blunders past him "
    "at the CENTRE RIGHT, the grey palings behind them along the LEFT third and the lit cottage "
    "window at the RIGHT edge. His head is a quarter of the frame's height.")
GEO_BOOTS = (
    "A heap of black broadcloth and a pair of black boots lie at the CENTRE at the foot of the grey "
    "palings, which run across the TOP half, with rain standing on the sand of the lane across the "
    "BOTTOM third.")
GEO_TURNS = (
    "The narrator stoops at the CENTRE RIGHT over the landlord, who lies against the foot of the "
    "grey palings at the CENTRE LEFT, one of the narrator's hands on his shoulder. The palings fill "
    "the TOP half. The narrator's head is a quarter of the frame's height.")
GEO_FACE = (
    "The landlord's face fills the CENTRE, lying back on the sand with his eyes closed and rain on "
    "his cheeks, his whiskers dark and wet, the foot of a grey paling at the LEFT edge. His head is "
    "half the frame's height.")
GEO_PALINGS = (
    "The narrator climbs the lane at the CENTRE LEFT with one hand along the grey palings, which "
    "run along the LEFT third, the lit cottage window at the RIGHT third and the sand running up to "
    "the TOP CENTRE. His head is a sixth of the frame's height.")
GEO_HUSSAR = (
    "The hussar stands at the CENTRE at the head of the lane, turned half back over his shoulder, "
    "his mouth open and shouting, rain on his face, the storm sky with a far violet bolt behind "
    "him at the TOP RIGHT. His head is half the frame's height.")
GEO_STAIRS = (
    "The narrator sits at the CENTRE on the bottom stair with his back to the wall, soaked and "
    "shivering, the newel post at the RIGHT third, the grey fanlight at the TOP LEFT and the dark "
    "tiled floor across the BOTTOM third. His head is a quarter of the frame's height.")

SETUPS = {
    "doorway": dict(
        described=DOORWAY_NIGHT, cast=["narrators_wife", "unnamed_first_person_narrator"],
        landmark="the lit front door at the top of its steps", landmark_at="far_end",
        landmark_size="is a fifth of the height of the frame",
        route="from the gate piers up the gravel drive to the lit front door",
        geometry=GEO_DOORWAY, crowd="",
        outdoors=True, props=["dog_cart"], location="cousins_house_leatherhead", view="wide_establishing"),
    "road": dict(
        described=ROAD_NIGHT, cast=["unnamed_first_person_narrator"],
        landmark="the blood-red glow on the horizon", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the foot of the road up over the rise toward the red glow",
        geometry=GEO_ROAD, crowd="",
        outdoors=True, props=["fighting_machine", "dog_cart"], location="road_ockham_ripley_pyrford",
        view="wide_road_storm_night"),
    "pool": dict(
        described=POOL_NIGHT, cast=["unnamed_first_person_narrator"],
        landmark="the clump of dark furze behind the pool", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the pool's edge past the furze out over the heath",
        geometry=GEO_POOL, crowd="",
        outdoors=True, props=["fighting_machine", "dog_cart", "martian_cylinder"],
        location="maybury_hill", view="medium_pool_furze"),
    "lane": dict(
        described=LANE_NIGHT, cast=["unnamed_first_person_narrator", "unnamed_landlord", "unnamed_hussar"],
        landmark="the lit windows of the College Arms at the top of the lane", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the foot of the lane up along the palings toward the College Arms",
        geometry=GEO_LANE, crowd="",
        outdoors=True, props=[], location="college_arms_lane", view="wide_establishing"),
    "hall": dict(
        described=HALL_NIGHT, cast=["unnamed_first_person_narrator"],
        landmark="the grey fanlight over the bolted front door", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the tiled floor to the foot of the stair",
        geometry=GEO_HALL, crowd="",
        outdoors=False, props=[], location="narrators_home", view="interior_hall_staircase"),
}

#  setup   size   faces  path  move   frame / motion / camera / cells / section / why
S = [
    # ---- doorway: the promise, and the wish -----------------------------------------
    ("doorway", "wide", [], 0.1, "crane_up",
     "Wide on the pale house at Leatherhead at night, its sash windows lit, the front door standing "
     "open at the top of its steps, the dog cart waiting on the gravel drive with its two lamps lit, "
     "and heavy clouds driving across the black sky above the roof.",
     "The camera rises from the gravel with small amplitude until the lit front of the house and "
     "the dog cart before it stand inside the picture, travelling one short stride; the cart lamps "
     "go on flickering; the clouds go on driving across the black sky.",
     "on the drive at a standing man's eye between the gate piers, a 35mm lens. The lamplight comes "
     "from the open door at the CENTRE; the gravel reads warm and the garden reads black",
     GEO_DOORWAY + " The dog cart stands on the gravel at the CENTRE RIGHT with its two lamps lit.",
     "hook", "Leatherhead is about twelve miles from Maybury Hill."),

    ("doorway", "medium_close", ["narrators_wife"], 0.5, "push_in",
     "Medium close on " + WIFE + " standing in the lit doorway at night, her face very white, "
     "the warm passage light behind her and her hand on the door frame.",
     "The camera pushes in toward her with small amplitude until her head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; she speaks and her eyes go on searching "
     "his face; her hand goes on tightening on the door frame.",
     "on the step level with her eyes, three paces from her, an 85mm lens. The lamplight comes from "
     "the passage BEHIND her and edges her hair; her face reads pale and the costume reads sage",
     GEO_WIFE, "setup", "Her face, I remember, was very white as we parted."),

    ("doorway", "medium", ["unnamed_first_person_narrator"], 0.8, "follow",
     "Medium on " + NARRATOR + " seen from behind with his back to the camera, climbing up into the "
     "dog cart before the lit house at night, one boot on the step and one hand on the rail.",
     "The camera tracks behind him as he climbs up into the dog cart, a follow with small "
     "amplitude, travelling a hand's breadth; he goes on pulling himself up onto the seat at a steady pace; his free "
     "hand goes on reaching for the reins.",
     "on the drive behind him at a standing man's eye, four paces from him, a 50mm lens. The "
     "lamplight comes from the lit house AHEAD; his soaked tweed reads charcoal against it",
     GEO_CLIMB, "setup", "I jumped up into the dog cart; then abruptly she turned and went in."),

    # ---- road: the red glow, the falling star, the first tripods ---------------------
    ("road", "wide", [], 0.1, "pan_to",
     "Wide down a dark country road at night climbing between black hedges, and far ahead along the "
     "western horizon a blood-red glow creeping up into the storm clouds with black smoke in it.",
     "The camera pans from the black hedge across to the red glow already in the picture until the "
     "glow is at the centre, travelling a hand's breadth; the red glow goes on creeping up the "
     "sky; the hedge tops go on shivering in the first wind of the storm.",
     "on the road at a driver's eye, a 35mm lens. The light is the red glow on the horizon AHEAD "
     "at the CENTRE; the road reads pale grey and the hedges read black",
     GEO_ROAD, "setup", "Along the western horizon a blood-red glow crept slowly up the sky."),

    ("road", "insert", [], 0.3, "tilt_up",
     "Insert over the hedge at night on a thread of green fire falling out of the storm clouds into "
     "the dark field on the left, the clouds lit green for a moment around it.",
     "The camera tilts up from the hedge to the storm clouds already in the picture until the "
     "clouds stand in the middle of the frame, travelling a forearm; the thread of green fire goes "
     "on falling into the field; the clouds go on driving across the sky.",
     "on the road at a driver's eye looking over the hedge, a 50mm lens. The green fire lights the "
     "clouds from the LEFT; the field reads black and the hedge reads black",
     "The black hedge crosses the BOTTOM third from the LEFT edge to the RIGHT edge, the dark field "
     "lies beyond it at the LEFT half, and the storm clouds fill the TOP half with the thread of "
     "green fire falling through them at the CENTRE LEFT into the field.",
     "spike", "It was the third falling star."),

    ("road", "medium_close", ["unnamed_first_person_narrator"], 0.45, "push_in",
     "Medium close on " + NARRATOR + " on the seat of the dog cart at night with the reins hauled "
     "tight in both hands, hunched against the rain, a far violet bolt in the clouds behind him.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; he shouts and hauls back on the reins; "
     "his head goes on turning toward the hill.",
     "beside the cart level with his eyes, three paces from him, an 85mm lens. The far violet "
     "lightning comes from BEHIND him at the TOP RIGHT; his wet face reads pale and the sky black",
     GEO_REINS, "spike", "The horse took the bit between his teeth and bolted."),

    ("road", "wide", [], 0.6, "push_in",
     "Wide across the dark field at night at a tripod far off on the slope of Maybury Hill, its "
     "three thin legs striding over the young pines, black against the storm clouds.",
     "The camera pushes in toward the tripod already in the picture with small amplitude, "
     "travelling one short stride; the tripod goes on striding down the slope; the pines go on "
     "swaying in the wind.",
     "on the road at a driver's eye, a 50mm lens. A far violet bolt lights the slope from the TOP "
     "RIGHT; the tripod reads black and the field reads dark",
     GEO_FAR_TRIPOD, "spike", "A monstrous tripod, higher than many houses, striding over the young pine trees."),

    ("road", "medium", [], 0.75, "track_lateral",
     "Medium over the heather at night on a tripod heeling over as it strides, one long leg lifted "
     "high in the air, the red glow low on the horizon behind it.",
     "The camera tracks sideways to the left along the hedge, a truck with small amplitude, until "
     "the tripod already in the picture is at the centre, travelling one short stride; the tripod "
     "goes on heeling over and swinging its lifted leg forward; the heather goes on tossing.",
     "on the road at a driver's eye, a 50mm lens. The red glow comes from the horizon at the RIGHT; "
     "the tripod reads dark metal and the heather reads black",
     GEO_HEELING, "friction", "Can you imagine a milking stool tilted and bowled violently along the ground?"),

    ("road", "medium", [], 0.9, "push_in",
     "Medium down the pale road at night at a tripod bursting out of the dark pines ahead of it, "
     "snapping the trunks aside, its brass dome high above the road.",
     "The camera pushes in toward the tripod already in the picture with small amplitude, "
     "travelling one short stride; the tripod goes on bursting through the pines; the snapped "
     "trunks go on falling away to either side.",
     "on the road at a driver's eye, a 35mm lens. A far violet bolt lights the pines from the TOP; "
     "the dome reads brass and the pines read black",
     GEO_RUSH, "spike", "The trees in the pine wood ahead of me were parted as reeds are parted."),

    # ---- pool: the fall, and the machines going by ------------------------------------
    ("pool", "insert", [], 0.1, "push_in",
     "Insert at night on the yellow-spoked wheel of the overturned dog cart turning in the air "
     "beside a black pool, hail dimpling the water below it.",
     "The camera pushes in on the wheel at the centre of the picture, travelling a hand's breadth; "
     "the wheel goes on turning; the hail goes on dimpling the black water.",
     "low at the pool's edge, a 50mm lens. The far violet lightning comes from the TOP RIGHT and "
     "glints on the spokes; the wheel reads yellow and the water reads black",
     GEO_WHEEL, "spike", "The dog cart had heeled over upon the horse; the shafts smashed noisily."),

    ("pool", "medium_close", ["unnamed_first_person_narrator"], 0.3, "push_in",
     "Medium close on " + NARRATOR + " crouched under a clump of dark furze at night with his feet "
     "in a black pool, soaked and shivering, rain running down his face.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; he goes on shivering and pulls his "
     "knees in; his head goes on lifting toward the heath.",
     "at the pool's edge level with his eyes, three paces from him, an 85mm lens. The violet "
     "lightning comes from the TOP RIGHT; his wet face reads pale and the furze reads black",
     GEO_CROUCH, "reaction", "I crouched, my feet still in the water, under a clump of furze."),

    ("pool", "medium", [], 0.5, "low_angle",
     "Medium from low in the heather at night on a tripod striding past, one long tentacle gripping "
     "a young pine, its white basket slung behind and green smoke puffing at its knees.",
     "The camera tilts up from the heather to the tripod already in the picture until the tripod "
     "stands in the middle of the frame, travelling a forearm; the tripod goes on striding past; "
     "the gripped pine goes on bending.",
     "low in the heather, a 24mm lens. The far violet lightning comes from the TOP RIGHT and "
     "catches the metal; the tripod reads white and the heather reads black",
     GEO_PASS, "spike", "A tentacle gripped a young pine tree as it went striding by me."),

    ("pool", "insert", [], 0.65, "push_in",
     "Insert on the brass dome of a tripod at night turning to and fro against the storm clouds, "
     "its band of dark green glass catching a far bolt of lightning.",
     "The camera pushes in toward the brass dome already in the picture with small amplitude, "
     "travelling a hand's breadth; the dome goes on swinging to and fro; the clouds go on driving "
     "behind it.",
     "low in the heather looking up, a 50mm lens. The far violet lightning comes from the TOP RIGHT "
     "and glints on the brass; the dome reads gold and the sky reads black",
     GEO_DOME, "friction", "The brazen hood moved to and fro with the suggestion of a head looking about."),

    ("pool", "wide", [], 0.9, "crane_up",
     "Wide over the dark hedge tops at night at two tripods half a mile off, stooping over a pale "
     "cylinder in the field between them, blurred by the falling hail.",
     "The camera rises above the hedge tops with small amplitude until the two tripods already in "
     "the picture stand at the centre, travelling one short stride; the two tripods go on stooping "
     "over the cylinder; the hail goes on falling.",
     "in the furze at a crouching man's eye, a 50mm lens. The far violet lightning comes from the "
     "TOP; the tripods read grey and the field reads black",
     GEO_TWO, "reaction", "In another minute it was with its companion, stooping over something in the field."),

    # ---- lane: the way home, and the dead man ------------------------------------------
    ("lane", "medium", ["unnamed_first_person_narrator"], 0.1, "follow",
     "Medium up a steep sandy lane at night on " + NARRATOR + " walking up it away from the camera, "
     "between a grey paling fence and a lit cottage.",
     "The camera tracks behind him up the lane as he walks toward the lit cottage, a follow with "
     "small amplitude, travelling one short stride; he goes on walking up the lane at a steady pace; his arms go on "
     "swinging wet at his sides.",
     "in the lane at a standing man's eye, six paces behind him, a 35mm lens. The lit cottage "
     "windows glow from the RIGHT; the sand reads pale and the palings read grey",
     GEO_WALK, "friction", "I had a vague idea of going on to my own house."),

    ("lane", "medium_close", ["unnamed_first_person_narrator"], 0.3, "push_in",
     "Medium close on " + NARRATOR + " in the lane at night staggering back as a stranger in a dark coat "
     "blunders into him, the grey palings behind them.",
     "The camera pushes in toward the two of them with small amplitude, travelling a hand's "
     "breadth; he calls out as the stranger goes on rushing past; his head goes on turning after him.",
     "in the lane at a standing man's eye, four paces from them, a 50mm lens. The lit cottage "
     "window comes from the RIGHT; the palings read grey and the coats read black",
     GEO_BLUNDER, "friction", "There in the darkness a man blundered into me and sent me reeling back."),

    ("lane", "insert", [], 0.5, "push_in",
     "Insert at night on a heap of black broadcloth and a pair of black boots lying at the foot of "
     "the grey palings, rain standing on the sand of the lane.",
     "The camera pushes in on the boots at the centre of the picture, travelling a hand's breadth; "
     "the rain goes on running over the broadcloth; the water goes on streaming past the boots.",
     "low in the lane looking down, a 50mm lens. The far violet lightning comes from the TOP and "
     "shines on the wet cloth; the broadcloth reads black and the sand reads pale",
     GEO_BOOTS, "friction", "I saw between my feet a heap of black broadcloth and a pair of boots."),

    ("lane", "medium_close", ["unnamed_first_person_narrator", "unnamed_landlord"], 0.6, "push_in",
     "Medium close on " + NARRATOR + " stooping at night over a man lying at the foot of the grey "
     "palings, one hand on the man's shoulder, turning him over.",
     "The camera pushes in toward the two of them with small amplitude, travelling a hand's "
     "breadth; the narrator goes on turning the man over by the shoulder; his head goes on bending "
     "down toward the man's face.",
     "low in the lane level with the narrator's eyes, three paces away, an 85mm lens. The far "
     "violet lightning comes from the TOP; his hand reads pale and the broadcloth reads black",
     GEO_TURNS, "turn", "I stooped and turned him over to feel for his heart."),

    ("lane", "close", ["unnamed_landlord"], 0.7, "push_in",
     "Close on the face of " + LANDLORD + " lying back on the sand at night with his eyes closed "
     "and rain on his cheeks, lit for a moment by the lightning.",
     "The camera pushes in toward his face with small amplitude until it fills the middle of the "
     "picture, travelling a hand's breadth; the rain goes on running over his cheeks; his head goes "
     "on lying back against the sand.",
     "low over him, two paces away, an 85mm lens. The far violet lightning comes from the TOP and "
     "lights his face blue-white; his whiskers read dark and his skin reads pale",
     GEO_FACE, "answer", "It was the landlord of the Spotted Dog, whose conveyance I had taken."),

    ("lane", "medium", ["unnamed_first_person_narrator"], 0.8, "track_lateral",
     "Medium on " + NARRATOR + " climbing the lane at night with one hand trailing along the grey "
     "palings, head down against the rain.",
     "The camera tracks sideways with him up the lane at his own pace, a truck with small "
     "amplitude, keeping him in the middle of the picture, travelling one short stride; he goes on "
     "climbing the lane at a steady pace; his hand goes on trailing along the palings.",
     "in the lane level with his chest, four paces from him, a 50mm lens. The lit cottage window "
     "comes from the RIGHT; the palings read grey and his tweed reads charcoal",
     GEO_PALINGS, "reaction", "I stepped over him gingerly and pushed on up the hill."),

    ("lane", "wide", [], 0.9, "pan_to",
     "Wide up the lane at night toward the lit windows of the College Arms at the top of the hill, "
     "and the red glare of the common beating up into the storm clouds beyond.",
     "The camera pans from the grey palings across to the lit cottage already in the picture until "
     "the cottage is at the centre, travelling a hand's breadth; the red glare goes on beating up "
     "into the clouds; the rain goes on streaming down the lane.",
     "in the lane at a standing man's eye, a 35mm lens. The lit windows glow from the RIGHT and the "
     "red glare from the TOP; the sand reads pale and the sky reads red and black",
     GEO_LANE, "runout", "From the common there still came a red glare and a rolling tumult of smoke."),

    ("lane", "close", ["unnamed_hussar"], 0.95, "locked",
     "Close on " + HUSSAR + " at the head of the lane at night, turned half back over his shoulder "
     "and shouting, rain on his face and a far violet bolt behind him.",
     "The camera holds a locked-off frame; he shouts back over his shoulder; his arm goes on "
     "waving the others down the hill.",
     "in the lane level with his eyes, three paces from him, an 85mm lens. The far violet lightning "
     "comes from BEHIND him at the TOP RIGHT; his wet face reads pale and the frogging reads yellow",
     GEO_HUSSAR, "button", "Down the road towards Maybury Bridge there were voices and the sound of feet."),

    # ---- hall: home, and nothing to be done -----------------------------------------------
    ("hall", "medium", ["unnamed_first_person_narrator"], 0.5, "push_in",
     "Medium on " + NARRATOR + " sitting at night on the bottom stair of his own dark hall with his "
     "back to the wall, soaked and shivering, the front door bolted behind him.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling one short stride; he goes on shivering; his hands go on "
     "gripping his knees.",
     "on the tiles level with his chest, four paces from him, a 50mm lens. The grey storm light "
     "comes through the fanlight BEHIND the door; his soaked tweed reads charcoal and the hall reads dark",
     GEO_STAIRS, "runout", "I crouched at the foot of the staircase with my back to the wall, shivering violently."),
]

MOVES = {i: s[4] for i, s in enumerate(S)}

BEATS = {18: (1.0, 1.4), 19: (1.2, 1.4), 20: (1.4, 1.2), 21: (1.0, 1.0), 22: (1.2, 1.5)}
"""Everything else takes the default (0.8, 0.9). The shot before the button
holds a beat of 1.0 s or more (the contract); the silent last shot takes the
longest coda the 6.0 s silence wall allows with the button's coda before it."""

TURNS = {17: "a man who wanted to be in at the death -> a man kneeling over one"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "Leatherhead is twelve miles from Maybury Hill. We were there by nine.", 0),
    ("dialogue", "narrators_wife", "Must you go back tonight?", 1),
    ("narration", "unnamed_first_person_narrator",
     "His cart was promised back by midnight.", 1),
    ("narration", "unnamed_first_person_narrator",
     "And I wanted to be in at the death.", 2),
    ("narration", "unnamed_first_person_narrator",
     "Past Ockham a red glow crept up the sky.", 3),
    ("narration", "unnamed_first_person_narrator",
     "A thread of green fire fell into a field. The third falling star.", 4),
    ("dialogue", "unnamed_first_person_narrator", "Steady! Steady, boy!", 5),
    ("narration", "unnamed_first_person_narrator",
     "Something was striding down the far slope of the hill.", 6),
    ("narration", "unnamed_first_person_narrator",
     "It came on like a milking stool, tilted and bowled along.", 7),
    ("narration", "unnamed_first_person_narrator",
     "Then the pines ahead snapped aside, and a second one came at me.", 8),
    ("narration", "unnamed_first_person_narrator",
     "I wrenched him round. The cart went over, and I into a pool.", 9),
    ("narration", "unnamed_first_person_narrator",
     "The horse lay dead, poor brute.", 10),
    ("narration", "unnamed_first_person_narrator",
     "It went striding by me, a tentacle round a young pine.", 11),
    ("narration", "unnamed_first_person_narrator",
     "Its hood swung to and fro like a head. Then it howled.", 12),
    ("narration", "unnamed_first_person_narrator",
     "Half a mile off, the two of them stooped over the third cylinder.", 13),
    ("narration", "unnamed_first_person_narrator",
     "I should have gone back to her. I went on toward home.", 14),
    ("dialogue", "unnamed_first_person_narrator", "Who's there? Hallo!", 15),
    ("narration", "unnamed_first_person_narrator",
     "A man blundered into me, cried out, and ran.", 15),
    ("narration", "unnamed_first_person_narrator",
     "Near the top I stumbled on something soft. Broadcloth, and boots.", 16),
    ("narration", "unnamed_first_person_narrator",
     "I had never touched a dead man. I turned him over.", 17),
    ("narration", "unnamed_first_person_narrator",
     "The landlord of the Spotted Dog. I had taken his cart.", 18),
    ("narration", "unnamed_first_person_narrator",
     "I stepped over him and pushed on up the hill.", 19),
    ("narration", "unnamed_first_person_narrator",
     "Down toward the bridge there were voices, and running feet.", 20),
    ("dialogue", "unnamed_hussar", "Down to the bridge, all of you! Keep moving!", 21),
]

BEDS = [{"from_shot": 0, "tone": "uneasy"}, {"from_shot": 3, "tone": "grave"},
        {"from_shot": 14, "tone": "uneasy"}, {"from_shot": 17, "tone": "grave"}]

EXTRAS = {15: 1}   # the stranger who blunders into him in the lane

SECTIONS = {}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.8, 0.9))
        shots.append(dict(index=i, section=SECTIONS.get(i, section), setup=setup, size=size,
                          faces=list(faces), extras=EXTRAS.get(i, 0), view="",
                          path=path, frame=frame, motion=motion, camera=camera,
                          at_rest=at_rest, end="", changed="", beat_s=beat, coda_s=coda,
                          turn=TURNS.get(i, ""), why=why, cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=10, title="In the Storm",
                question="Why does he drive back into it?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 18",
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
    silent = [s["index"] for s in doc["shots"]
              if not any(l["shot"] == s["index"] for l in doc["lines"])]
    sizes = {z: [s["size"] for s in doc["shots"]].count(z)
             for z in {s["size"] for s in doc["shots"]}}
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words; "
          f"dialogue {said / words:.1%}; silent shots {silent}")
    print(f"measured projection at 2.62 w/s: "
          f"{words / 2.62 + sum(s['beat_s'] + s['coda_s'] + 0.5 for s in doc['shots']):.0f}s")
    print(f"sizes: {sizes}")
    print(f"moves: {counts}")
    print(OUT)
