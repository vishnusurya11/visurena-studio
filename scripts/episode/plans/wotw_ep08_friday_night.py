r"""The War of the Worlds, episode 8 -- "Friday Night", chapter 8.

THE BRICK.  One event, and the event is that nothing happens: within five
miles of the thing that will end the world, an ordinary Friday evening goes
on being ordinary, and the not-noticing IS the chapter.

  QUESTION  On the night it began, who noticed?
  TURN      shot 8, nine o'clock at Woking junction.  Excited men come in
            off the last train with the news, and a whole station declines it
            -- "they caused no more disturbance than drunkards might have
            done" -- so the news is offered to a town and refused, where
            episode 7 offered it to three people at a gate.
  ANSWER    shot 16: the charred bodies lying out on the common all night
            under the stars, while a noise of hammering comes up out of the
            pit.  Nobody is coming for them.
  BUTTON    line 18, the paper boy: "Men from Mars!"  It is TRUE, he is
            shouting it to sell papers, and the trucks are louder.

THE THIRD PANEL OF A TRIPTYCH.  ep06 ended on a woman shrieking a thing that
was not true; ep07 on a wife saying the one true thing in the chapter and
being argued out of it; ep08 on a child hawking the truth as a headline while
a station shunts around him.  Same shape three times: the news, and what
people do with it.

NO NARRATOR IN THE PICTURE.  He says so himself -- "I have already described
the behaviour of the men and women to whom I spoke" -- so this is his account
of a night he spent indoors, and the pictures belong to other people.  He is
cast in no shot of it.

WHAT IS NEW HERE.  Three places the series has not drawn: a village street
going about its evening, Woking junction after dark, and the inside of a
lighted carriage.  The common and the bridge it already owns, and the bridge
needs its own hour -- the hour comes from the reference and never from the
words (MEASURED 2026-09-20 on ep05, twice).

THE CAST IS DESCRIBED FROM ITS BOUND ROWS (`refs.json`), never from memory.
ep07 shipped four characters that contradicted their own rows before the
content gate read a moustache on a man this plan had called clean-shaven.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep08" / "plan.json"

WHERE = "Horsell, Surrey, 1894"
LIGHT = "gaslight and black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

BOY = ("the newspaper boy, a skinny lad of thirteen with knobbly wrists, a narrow freckled face, "
       "a snub nose, big ears and a gap between his front teeth, his tousled mousy-brown hair "
       "under a grey flat cloth cap pushed back, in an oversized ginger-orange corduroy jacket "
       "with an empty canvas bag folded flat on its strap across his chest")
SHOPMAN = ("the young shopman, a slight narrow-shouldered man of twenty-one with an oval face, a "
           "pale indoor complexion, prominent ears and dark brown hair brushed up in a quiff, "
           "clean-shaven, in a brown cloth cap, a high white celluloid collar and a violet satin "
           "tie, his white pinstriped trousers smeared with yellow sand from the pit")

# ---- the five places, each naming its own light and where it comes from ------
PIT_NIGHT = (
    "the sand-pits on Horsell Common at night in 1894: the raw ring of flung yellow sand round the "
    "crater, a low red glow standing up out of it, knee-deep heather and dark furze black to a flat "
    "horizon closed by low pines, thin smoke lying along the ground, and dark shapes lying still "
    "out on the open sand; the only light is that low raking red glow out of the pit, so the "
    "sand ring reads dull red and the heather and the pines are black")
STREET_NIGHT = (
    "the main street of a Surrey village at night in 1894: a row of brick and stucco cottages with "
    "lit sash windows and low front gardens, a gas street lamp at the kerb, a public house with a "
    "lantern over its door partway along, clipped hedges and a pillar box, and the road going away "
    "pale between them; the light is gaslight from the left and the lit windows behind it, warm and "
    "low, so the road reads pale, the brick reads warm and the gardens are black")
JUNCTION_NIGHT = (
    "the platform of Woking junction at night in 1894: a long canopied platform under iron columns, "
    "gas lamps hanging in a row down it, a locomotive standing at the far end with steam about its "
    "wheels, goods trucks on the siding beyond, a wooden bookstall shuttered for the night, a "
    "wheeled porter's barrow standing empty, a cast-iron weighing machine, and milk churns and "
    "mail sacks stacked along the edge; the light is gaslight from above, hard and "
    "white, so the platform reads pale grey, the steam reads white and the track beyond is black")
CARRIAGE_NIGHT = (
    "the inside of a third-class railway carriage at night in 1894: a compartment with buttoned "
    "cloth seats facing each other, brass rails along the luggage rack above, a framed line map "
    "and an advertisement card on the panelling, a leather strap hanging by the door, a folded "
    "newspaper on one seat, one oil lamp in the roof, and a window with a leather window-strap "
    "and the night running past it; the light is that roof lamp, "
    "warm and from above, so the seats read warm brown, the faces read warm and the window is black")
BRIDGE_NIGHT = (
    "the Horsell bridge over the canal at night in 1894: a low brick parapet crossing the road, the "
    "pale road going over it toward the open common beyond, black canal water below the near side, "
    "a gas lamp at the near end, a white painted handrail along the parapet, a stone milestone at "
    "the near corner, and a red glow standing low in the sky over the common; the light "
    "is that lamp from the near end and the red glow beyond, so the road and the parapet read pale "
    "and the water and the far common are black")

GEO_PIT = (
    "Black heather fills the BOTTOM third of the frame from the LEFT edge to the RIGHT edge. The "
    "raw ring of flung yellow sand runs across the CENTRE, lit red from within, a tenth of the "
    "height of the frame, with thin smoke lying flat along the ground in front of it. Dark shapes "
    "lie still on the open sand at the CENTRE LEFT and the CENTRE RIGHT, and a black sky fills the "
    "TOP third.")
GEO_STREET = (
    "The pale road runs from the BOTTOM edge away into the CENTRE. Brick cottages with lit sash "
    "windows stand along the LEFT from the BOTTOM LEFT to the CENTRE, a gas lamp at the kerb at the "
    "CENTRE LEFT, and the lantern of the public house shows further along at the CENTRE. Black "
    "gardens fill the RIGHT third and a black sky fills the TOP third.")
GEO_JUNCTION = (
    "The pale platform runs from the BOTTOM edge away into the CENTRE, iron columns standing along "
    "it at the LEFT third and the RIGHT third with gas lamps hanging between them across the TOP "
    "third. The locomotive stands at the CENTRE at the far end with white steam about its wheels, "
    "the shuttered bookstall at the RIGHT third, and black track beyond the platform edge at the "
    "LEFT edge.")
GEO_CARRIAGE = (
    "The buttoned cloth seats fill the LEFT third and the RIGHT third of the frame facing each "
    "other, the black window between them at the CENTRE with the luggage rack across the TOP third "
    "above it. The roof lamp burns at the TOP CENTRE and its light falls on the seats and the floor "
    "in the BOTTOM third.")
GEO_BRIDGE = (
    "The brick parapet runs across the CENTRE of the frame from the LEFT edge to the RIGHT edge. "
    "The pale road crosses it at the CENTRE and runs away to the open common beyond, black canal "
    "water shows at the BOTTOM LEFT, a gas lamp burns at the LEFT third, and a low red glow lies "
    "along the CENTRE at the horizon under a black sky in the TOP third.")

SETUPS = {
    "street": dict(
        described=STREET_NIGHT, cast=[],
        landmark="the lantern over the door of the public house", landmark_at="far_end",
        landmark_size="is a sixth of the height of the frame",
        route="from the near cottages along the village street toward the public house",
        geometry=GEO_STREET,
        crowd="villagers about their own evening, watering a garden, carrying a child indoors, "
              "standing talking at a gate",
        outdoors=True, props=[], location="village_street"),
    "junction": dict(
        described=JUNCTION_NIGHT, cast=["unnamed_newspaper_boy", "unnamed_shopman"],
        landmark="the locomotive standing at the far end of the platform", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the shuttered bookstall along the platform toward the locomotive",
        geometry=GEO_JUNCTION,
        crowd="passengers alighting and waiting with bags, porters wheeling trucks, a knot of men "
              "arguing by the lamps",
        outdoors=True, props=[], location="woking_junction"),
    "carriage": dict(
        described=CARRIAGE_NIGHT, cast=[],
        landmark="the black window with the night running past it", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the compartment door across the seats to the window",
        geometry=GEO_CARRIAGE,
        crowd="passengers on both seats, one with a folded paper, two leaning to the glass",
        outdoors=False, props=[], location="railway_carriage"),
    "bridge": dict(
        described=BRIDGE_NIGHT, cast=[],
        landmark="the red glow standing low in the sky over the common", landmark_at="far_end",
        landmark_size="is a twelfth of the height of the frame",
        route="from the near end of the bridge across the parapet toward the open common",
        geometry=GEO_BRIDGE,
        crowd="a curious crowd along the parapet, people coming and going and the crowd staying, "
              "all of them facing the same way",
        outdoors=True, props=[], location="horsell_common"),
    "pit": dict(
        described=PIT_NIGHT, cast=[],
        landmark="the raw ring of flung yellow sand round the crater", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the black heather out across the open sand to the ring of the pit",
        geometry=GEO_PIT, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
}

#  setup   size   faces  path  move   frame / motion / camera / at_rest / section / why
S = [
    # ---- street: the evening goes on being an evening ---------------------------
    ("street", "wide", [], 0.1, "crane_up",
     "Wide down a Surrey village street at night: brick cottages with lit sash windows along the "
     "left, a gas lamp burning at the kerb, the lantern of the public house further along, and the "
     "pale road running away empty between the hedges.",
     "The camera rises from the road with small amplitude until the whole row of lit windows and "
     "the lantern beyond stand inside the picture, travelling one short stride; a curtain is drawn "
     "across one lit window and the light behind it goes on burning; moths go on turning about the "
     "gas lamp.",
     "in the middle of the road at a standing man's eye, a 35mm lens. The gaslight comes from the "
     "LEFT and the lit windows behind it; the road reads pale, the brick reads warm and the "
     "gardens are black",
     GEO_STREET, "hook", "Five miles from the pit, and the evening is an evening."),

    ("street", "medium", [], 0.3, "track_lateral",
     "Medium on a working man watering a garden at night by lamplight from his own window, in "
     "shirtsleeves with his braces down, a tin can in one hand, the rows of his vegetables black "
     "and wet in front of him and the lit window warm behind.",
     "The camera tracks sideways to the right along the garden rail, a truck with small amplitude, "
     "until the lit window already in the picture is at the centre, travelling one short stride; "
     "the water goes on running from the can along the row; he moves the can on to the next row "
     "and goes on pouring.",
     "at the garden rail level with his chest, four paces from him, a 50mm lens. The window light "
     "comes from behind him at the RIGHT; the wet earth reads dark and the rows are black",
     GEO_STREET, "setup", "Working men were gardening after the labours of the day."),

    ("street", "medium_close", [], 0.5, "tilt_up",
     "Medium close on a lit upstairs window at night seen from the road, the sash up a hand's "
     "breadth, a woman's shape crossing it with a child against her shoulder, and the warm light "
     "spilling out over the sill on to the dark hedge below.",
     "The camera tilts up the face of the cottage to the window, travelling a hand's breadth, "
     "until the lit sash is in the middle of the picture; the shape crosses the window and comes "
     "back; the light on the sill goes on moving as she moves.",
     "in the road below the window looking up, a 50mm lens, a low angle. The window is the light "
     "and it comes from the CENTRE; the brick around it reads warm and the hedge below is black",
     "The lit sash window fills the CENTRE of the frame, a third of the frame's height, warm "
     "against dark brick that fills the LEFT edge and the RIGHT edge. The black hedge crosses the "
     "BOTTOM third and a black sky fills the TOP third.",
     "setup", "Children were being put to bed."),

    ("street", "insert", [], 0.8, "pan_to",
     "Insert on the lantern over the door of the public house at night, close: a square iron "
     "lantern with smoked glass and a candle burning inside it, the painted board beside it dark, "
     "and a warm wash of light going down the bricks below.",
     "The camera pans to the left along the wall until the lantern already in the picture is at "
     "the centre, travelling a hand's breadth; the flame inside leans and rights itself as the "
     "door below opens; the wash of light on the bricks goes on widening.",
     "close under the lantern on the pavement, a 50mm lens, a low angle. The lantern is the light "
     "and it comes from the CENTRE; the bricks read warm and the street beyond is black",
     GEO_STREET, "setup", "A novel and dominant topic in the public-houses."),

    # ---- junction: the news arrives, and the town shunts on ----------------------
    ("junction", "wide", [], 0.1, "track_lateral",
     "Wide along the platform of Woking junction at night: iron columns down both sides with gas "
     "lamps hanging between them, passengers waiting with bags along the edge, milk churns and "
     "mail sacks stacked by the wall, and a locomotive standing at the far end in its own steam.",
     "The camera tracks sideways to the right along the platform, a truck with small amplitude, "
     "until the locomotive already in the picture is at the centre, travelling one short stride; "
     "steam goes on rolling out along the platform at ankle height; a porter wheels a truck of "
     "sacks across in front of the lamps.",
     "on the platform at a standing man's eye, a 35mm lens. The gas lamps come from ABOVE; the "
     "platform reads pale grey, the steam reads white and the track beyond is black",
     GEO_JUNCTION, "setup", "Everything was proceeding in the most ordinary way."),

    ("junction", "medium_close", ["unnamed_newspaper_boy"], 0.3, "follow",
     f"Medium close on {BOY} working the platform at night with a folded paper held up in one "
     "hand, his mouth open on a cry, the gas lamps hard on his face and the waiting passengers "
     "black behind him.",
     "The camera tracks with him along the platform at his own pace, a truck with small amplitude, "
     "keeping him in the middle of the picture, travelling a hand's breadth; he lifts the paper "
     "higher and calls again; his free hand goes on tugging the empty bag round on its strap.",
     "on the platform level with his face, three paces from him, a 50mm lens. The gas lamps come "
     "from ABOVE and are hard on his face; the passengers behind him are black",
     "The boy fills the CENTRE of the frame, the panel cutting him at the middle of the chest, his "
     "head a third the frame's height at the TOP third, the folded paper up at the RIGHT third. "
     "Black waiting passengers fill the LEFT edge and the RIGHT edge and the gas lamps hang across "
     "the TOP third.",
     "friction", "A boy from the town, trenching on Smith's monopoly."),

    ("junction", "insert", [], 0.5, "locked",
     "Insert on the front page of an evening paper held up at night, close: a column of small "
     "black type under a plain heading, the sheet creased where a thumb holds it, and the hard "
     "gaslight raking across the paper from above.",
     "The camera pushes in on the held sheet, a dolly with small amplitude, until the heading "
     "fills the middle of the picture, travelling a hand's breadth; the hand holding it lifts the "
     "sheet and lets it settle; the light goes on raking across the creases.",
     "close to the held paper on the platform, a 50mm lens. The gas lamps come from ABOVE; the "
     "paper reads bright and everything behind it is black",
     GEO_JUNCTION, "friction", "The afternoon's news, and none of it is this."),

    ("junction", "medium", [], 0.7, "pan_to",
     "Medium on a knot of five men under the platform lamps at night, hats on the backs of their "
     "heads, two of them talking at once with their hands going, the others listening with their "
     "arms folded, and the lit carriage windows of a stopped train behind them.",
     "The camera pans to the right across the knot until the furthest man already in the picture "
     "is at the centre, travelling a hand's breadth; the two who are talking go on talking over "
     "each other; one of the listeners turns away toward the train and keeps turning.",
     "on the platform level with their faces, four paces from them, a 50mm lens. The gas lamps "
     "come from ABOVE and the carriage windows from behind them; the platform reads pale",
     GEO_JUNCTION, "friction", "Excited men came into the station about nine o'clock."),

    ("junction", "medium_close", ["unnamed_shopman"], 0.9, "locked",
     f"Medium close on {SHOPMAN} at the platform lamps at night, telling it to somebody just out "
     "of frame with his cap pushed back and his hands going, the yellow sand of the pit still on "
     "his trousers, the hard gaslight full on his face.",
     "The camera pushes in on him a hand's breadth, a dolly with small amplitude, until his face "
     "fills the middle of the picture; he says it and his hands go on moving; his cap goes further "
     "back off his forehead as he talks.",
     "on the platform level with his face, two paces from him, a 50mm lens. The gas lamps come "
     "from ABOVE and are full on his face; the platform behind him is black",
     "The shopman fills the CENTRE of the frame, the panel cutting him at the middle of the chest, "
     "his head a third the frame's height at the TOP third, both hands up at the CENTRE. Black "
     "platform fills the LEFT edge and the RIGHT edge and the gas lamps hang across the TOP third.",
     "turn", "Incredible tidings, and no more disturbance than drunkards."),

    ("junction", "wide", [], 0.95, "crane_up",
     "Wide of the sidings beyond the platform at night: goods trucks being shunted along the rails "
     "under the lamps, a shunter walking beside them with a pole, steam standing about the wheels, "
     "and the lit platform small behind.",
     "The camera rises above the trucks with small amplitude until the whole line of them and the "
     "lit platform behind stand inside the picture, travelling one short stride; the trucks go on "
     "rolling and clashing along the rail; the shunter walks on beside them with his pole.",
     "beside the siding low to the rails, a 35mm lens. The lamps come from ABOVE at the RIGHT; the "
     "trucks read dull and the track between them is black",
     GEO_JUNCTION, "reaction", "The ringing impact of trucks, louder than the news."),

    # ---- carriage: Londonwards, and a spark on the horizon -----------------------
    ("carriage", "medium", [], 0.2, "track_lateral",
     "Medium across a lighted third-class compartment at night: four passengers on the facing "
     "seats, one with a folded paper on his knee, one asleep in the corner, the roof lamp burning "
     "above them and the black window running past between.",
     "The camera tracks sideways to the left along the compartment, a truck with small amplitude, "
     "until the black window already in the picture is at the centre, travelling one short stride; "
     "the whole compartment rocks steadily on the rail; the folded paper slides a hand's breadth "
     "along the knee and is caught.",
     "in the compartment level with their chests, four paces along it, a 35mm lens. The roof lamp "
     "comes from ABOVE; the seats read warm brown and the window is black",
     GEO_CARRIAGE, "setup", "People rattling Londonwards, and the night outside."),

    ("carriage", "medium_close", [], 0.5, "locked",
     "Medium close on two passengers leaning to the carriage window at night, an older man with "
     "his hand cupped against the glass and a young woman beside him with her forehead near it, "
     "both of them looking out into the dark with the roof lamp warm on the sides of their faces.",
     "The camera pushes in on the glass a hand's breadth, a dolly with small amplitude, until "
     "both faces and the black window fill the middle of the picture; his cupped hand goes on "
     "shading the glass; her breath goes on misting it and clearing.",
     "in the compartment level with their faces, three paces from them, a 50mm lens. The roof lamp "
     "comes from ABOVE behind them; their faces read warm and the window is black",
     "The two passengers fill the CENTRE of the frame side by side, the panel cutting them at the "
     "middle of the chest, each head a third the frame's height at the TOP third. The black window "
     "fills the frame behind them and the roof lamp shows at the TOP CENTRE.",
     "friction", "Peering into the darkness outside the carriage windows."),

    ("carriage", "insert", [], 0.8, "pan_to",
     "Insert through the carriage window at night: the black country running past, a single "
     "flickering spark dancing up from the direction of Horsell, a low red glow beyond it and a "
     "thin veil of smoke driving across the stars.",
     "The camera pans to the right with the running country until the red glow already in the "
     "picture is at the centre, travelling a hand's breadth; the spark goes on dancing up and "
     "away; the veil of smoke goes on driving across the stars.",
     "at the carriage glass looking out, a 50mm lens. The red glow on the horizon is the only "
     "light; the country is black and the smoke reads thin and pale",
     GEO_CARRIAGE, "friction", "A heath fire, they thought, and nothing more serious."),

    # ---- bridge: the ones who stayed to look --------------------------------------
    ("bridge", "wide", [], 0.1, "crane_up",
     "Wide of the Horsell bridge at night from the near side: the low brick parapet crossing the "
     "frame with a crowd standing all along it, the pale road going over and away toward the open "
     "common, a gas lamp burning at the near end, and a red glow standing low in the sky beyond.",
     "The camera rises from the road with small amplitude until the whole parapet and the red glow "
     "beyond stand inside the picture, travelling one short stride; two of the crowd leave the "
     "parapet and walk back past the camera; three more come up and take their places along it.",
     "on the road at the near end of the bridge, low, a 35mm lens. The gas lamp comes from the "
     "LEFT and the red glow from the CENTRE beyond; the road reads pale and the water is black",
     GEO_BRIDGE, "setup", "A curious crowd lingered, people coming and going."),

    ("bridge", "medium", [], 0.4, "track_lateral",
     "Medium along the parapet at night: six or seven people leaning on the brick side by side, "
     "all of them turned the same way toward the common, a man with a child up on the parapet "
     "beside him, and the red glow low on the horizon in front of them.",
     "The camera tracks sideways to the right behind them, a truck with small amplitude, until the "
     "man with the child already in the picture is at the centre, travelling one short stride; the "
     "child points out toward the glow and keeps pointing; the man shifts his weight on the brick.",
     "behind the parapet level with their shoulders, three paces from them, a 50mm lens. The red "
     "glow comes from the CENTRE beyond; their backs read black and the brick reads pale",
     GEO_BRIDGE, "friction", "The crowd remaining, on both the Chobham and Horsell bridges."),

    ("bridge", "insert", [], 0.7, "tilt_up",
     "Insert on a pale beam sweeping the black common at night, seen low from the bridge: a flat "
     "shaft of light like a warship's searchlight lying along the heather, the tops of the furze "
     "bright where it crosses them, and the dark closing again behind it.",
     "The camera tilts up from the heather along the beam, travelling a hand's breadth, until the "
     "far end of it is in the middle of the picture; the beam goes on sweeping across the heather "
     "from the left; the furze tops brighten in turn as it passes them.",
     "low on the bridge looking out over the common, a 35mm lens. The beam is the only light and "
     "it comes from the CENTRE; the heather reads black and the beam reads pale",
     GEO_BRIDGE, "spike", "A light-ray swept the common, and the Heat-Ray was ready to follow."),

    # ---- pit: what is out there while the evening goes on --------------------------
    ("pit", "wide", [], 0.2, "track_lateral",
     "Wide of the open common at night from out on the heather: the raw ring of flung yellow sand "
     "with a low red glow standing out of it, thin smoke lying flat along the ground, dark shapes "
     "lying still on the open sand, and a flat horizon of low pines behind.",
     "The camera tracks sideways to the left across the heather, a truck with small amplitude, "
     "until the red ring already in the picture is at the centre, travelling one short stride; the "
     "flat smoke goes on drifting across the sand; the glow out of the pit goes on rising and "
     "falling.",
     "out on the heather a hundred yards from the pit, low, a 35mm lens. The red glow out of the "
     "pit is the only light; the sand ring reads dull red and the heather and pines are black",
     GEO_PIT, "answer", "That big area of common was silent and desolate."),

    ("pit", "insert", [], 0.6, "pan_to",
     "Insert on the charred ground at night, close: heather burnt down to black stalks, the sand "
     "under it scorched and fused in patches, a man's boot lying on its side among the stalks, and "
     "the low red glow of the pit catching the rim of it.",
     "The camera pans to the left across the burnt ground until the boot already in the picture is "
     "at the centre, travelling a hand's breadth; thin smoke goes on rising from the stalks; a "
     "flake of ash lifts off the sand and goes on drifting.",
     "on the ground among the burnt stalks, a 50mm lens, a low angle. The red glow comes from the "
     "RIGHT; the sand reads dull red and the stalks are black",
     GEO_PIT, "answer", "The charred bodies lay about all night under the stars."),

    ("pit", "medium", [], 0.9, "crane_up",
     "Medium on the lip of the pit at night from out on the sand: the raw edge of flung sand with "
     "the red glow standing up behind it, a long shadow moving on the sand beyond the rim, and "
     "thin smoke going up straight in the still air.",
     "The camera rises from the sand with small amplitude until the lip of the pit and the glow "
     "behind it fill the middle of the picture, travelling one short stride; the shadow beyond the "
     "rim goes on moving back and forth; the smoke goes on climbing straight up.",
     "out on the sand thirty paces from the lip, low, a 35mm lens. The red glow comes from beyond "
     "the rim at the CENTRE; the sand reads dull red and everything above it is black",
     GEO_PIT, "answer", "A noise of hammering from the pit was heard by many people."),

    # ---- back to the junction for the last word ------------------------------------
    ("junction", "medium_close", ["unnamed_newspaper_boy"], 0.99, "locked",
     f"Medium close on {BOY} at the end of the platform at night with the last of his papers under "
     "his arm, his head back and his mouth wide on a cry, the gas lamps hard on his face and the "
     "shunting trucks black behind him.",
     "The camera pushes in on him a hand's breadth, a dolly with small amplitude, until his face "
     "fills the middle of the picture; he cries it out and his head stays back; the empty bag goes "
     "on swinging against his hip.",
     "on the platform level with his face, two paces from him, a 50mm lens. The gas lamps come "
     "from ABOVE and are hard on his face; the trucks behind him are black",
     "The boy fills the CENTRE of the frame, the panel cutting him at the middle of the chest, his "
     "head a third the frame's height at the TOP third, his chin up. Black shunting trucks fill "
     "the frame behind him and the gas lamps hang across the TOP third.",
     "button", "He is shouting the truth, and it is a way of selling papers."),
]

MOVES = {i: s[4] for i, s in enumerate(S)}

# EVERY SHOT HOLDS AS LONG AS ITS TAKE ALLOWS, computed rather than typed:
# `scratchpad/fit_beats.py` gives each shot the largest beat and coda that
# keep its line, its hold and the builder's handle inside the 8 s take at the
# narrator's MEASURED 2.58 words a second. Typed beats put this episode at
# 116 s when tight and nine shots over the budget when generous.
# Shots 0-4 hold a little less so the boy's first cry lands inside the first
# quarter: it was 35.3 s of 137.5, and the wall is a quarter.
BEATS = {0: (0.6, 0.6), 1: (0.4, 0.4), 2: (1.0, 1.2), 3: (0.4, 0.4),
         4: (0.6, 0.6), 5: (0.6, 0.6), 6: (1.5, 2.0), 7: (1.0, 1.3),
         8: (0.9, 1.0), 9: (0.7, 0.8), 10: (1.5, 2.0), 11: (0.7, 0.8),
         12: (0.9, 1.0), 13: (1.0, 1.3), 14: (0.7, 0.8), 15: (0.9, 1.0),
         16: (1.0, 1.3), 17: (1.0, 1.0), 18: (1.0, 1.7), 19: (1.5, 2.0)}

TURNS = {12: "a town that has not seen it -> a town that has seen it and called it a heath fire",
         18: "the news as news -> the news as a thing a child sells"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "The strangest thing about that Friday was how ordinary the rest of it stayed.", 0),
    ("narration", "unnamed_first_person_narrator",
     "Draw a circle five miles wide round the pit, and inside it people dug their gardens.", 1),
    ("narration", "unnamed_first_person_narrator",
     "Children went up to bed. Students sat over their books.", 2),
    ("narration", "unnamed_first_person_narrator",
     "At the junction the trains came in and went out as they always had.", 4),
    # THE FIRST VOICE, early, and it belongs to a child: ep04 opened on this
    # same boy and ep05 on a neighbour, both at a medium_close in the first
    # fifth. He is selling papers that say nothing about any of it.
    ("dialogue", "unnamed_newspaper_boy", "Evening paper! Read all about it!", 5),
    ("narration", "unnamed_first_person_narrator",
     "Nothing in it said a word about any of this.", 6),
    ("narration", "unnamed_first_person_narrator",
     "Men came in off the late train with it, talking over each other.", 7),
    ("dialogue", "unnamed_shopman",
     "I saw it myself. The thing has opened and there are men inside it.", 8),
    ("narration", "unnamed_first_person_narrator",
     "They made about as much stir as two drunks, and the trucks drowned them out.", 9),
    ("narration", "unnamed_first_person_narrator",
     "Londonwards, four to a compartment, the carriages rocked on.", 10),
    ("narration", "unnamed_first_person_narrator",
     "Two of them put their faces to the glass and looked out at the dark.", 11),
    ("narration", "unnamed_first_person_narrator",
     "A spark going up, a red glow, smoke across the stars: a heath fire.", 12),
    ("narration", "unnamed_first_person_narrator",
     "On the bridges the crowd stayed, though the people in it kept changing.", 13),
    ("narration", "unnamed_first_person_narrator",
     "One or two went out into the dark to look closer, and stayed out there.", 14),
    ("narration", "unnamed_first_person_narrator",
     "A beam went over the heather like a searchlight, hunting for something to burn.", 15),
    ("narration", "unnamed_first_person_narrator",
     "The common itself lay quiet all night, and the dead lay on it.", 16),
    ("narration", "unnamed_first_person_narrator",
     "Whatever the ray had touched was lying where it fell.", 17),
    ("narration", "unnamed_first_person_narrator",
     "Somewhere under the sand a hammering went on, and went on.", 18),
    # THE BUTTON IS NEVER THE PROTAGONIST'S (rule 5). The one true sentence
    # anybody says in the chapter, shouted by a child to sell a newspaper that
    # does not carry it, into a station too loud to hear him.
    ("dialogue", "unnamed_newspaper_boy", "Men from Mars! Read it here, men from Mars!", 19),
]

BEDS = [{"from_shot": 0, "tone": "plain"}, {"from_shot": 5, "tone": "uneasy"},
        {"from_shot": 10, "tone": "plain"}, {"from_shot": 13, "tone": "uneasy"},
        {"from_shot": 16, "tone": "grave"},
        # The button's own shot, which is 19: the bed named 20 and this
        # episode ends at 19, the same off-by-one the line map had.
        {"from_shot": 19, "tone": "grave"}]

PATHS = {
    0: 0.1, 1: 0.3, 2: 0.5, 3: 0.8,                     # street
    4: 0.1, 5: 0.3, 6: 0.5, 7: 0.7, 8: 0.9, 9: 0.95,    # junction
    10: 0.2, 11: 0.5, 12: 0.8,                          # carriage
    13: 0.1, 14: 0.4, 15: 0.7,                          # bridge
    16: 0.2, 17: 0.6, 18: 0.9,                          # pit
    19: 0.99,                                           # junction again, the button
}

SECTIONS = {
    0: "hook",
    1: "setup", 2: "setup", 3: "setup", 4: "setup",
    5: "friction", 6: "friction", 7: "friction",
    8: "friction",
    9: "friction", 10: "reaction",
    11: "setup",
    12: "turn",
    13: "setup", 14: "friction",
    15: "spike",
    16: "answer", 17: "answer", 18: "answer",
    19: "button",
}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.6, 0.0))
        shots.append(dict(index=i, section=SECTIONS.get(i, section), setup=setup, size=size,
                          faces=list(faces), view="",
                          path=PATHS.get(i, path), frame=frame, motion=motion, camera=camera,
                          at_rest=at_rest, end="", changed="", beat_s=beat, coda_s=coda,
                          turn=TURNS.get(i, ""), why=why, cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=8, title="Friday Night",
                question="On the night it began, who noticed?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 16",
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
    sizes = {z: [s["size"] for s in doc["shots"]].count(z)
             for z in {s["size"] for s in doc["shots"]}}
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words; "
          f"dialogue {said / words:.1%}; silent shots {silent}")
    print(f"measured projection at 2.72 w/s: "
          f"{words / 2.72 + sum(s['beat_s'] + s['coda_s'] + 0.5 for s in doc['shots']):.0f}s")
    print(f"sizes: {sizes}")
    print(f"moves: {counts}")
    print(OUT)
