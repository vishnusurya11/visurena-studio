r"""The War of the Worlds, episode 7 -- "How I Reached Home", chapter 7.

THE BRICK.  One event: a man carries the worst news in England four miles
home, and every person he meets declines to take it -- until, at his own
table, he talks his wife out of the one true thing anybody says all evening.

  QUESTION  Can he bring what he saw back into his own house?
  TURN      shot 17, the laughter at the gate.  Up to there he is a witness;
            after it he is a man with a story nobody wants, and he stops
            trying to tell it -- "a man carrying the news" -> "a man carrying
            a story".
  ANSWER    shot 22: the cold dinner served and going cold on the table while
            he explains that the Martians cannot get out of their pit.
  BUTTON    line 25, his wife: "They may come here."  Wells gives her that
            line "again and again", and she is right; the narrator spends the
            rest of the evening being wrong at her.

THE MIRROR OF EPISODE 6.  There the last thing said was the neighbour's wife
shrieking "They're coming!" into a road where nothing was coming -- the only
untrue thing in the chapter.  Here the last thing said is a wife saying they
may come, which is the only TRUE thing in this one.  Same voice, opposite
value, one night apart.

THE CHAPTER IS A DESCENT INTO THE ORDINARY, so the pictures go from black
heather to gaslight to a laid table, and the light warms as the news dies.
Wells does the whole turn in one sentence -- "My terror had fallen from me
like a garment" -- and the cut has to carry that without a line for it.

WHAT IS NEW HERE.  Episodes 1-6 all played on Horsell Common and its road.
This one walks off the common for the first time: the canal bridge by the
gasworks, the Maybury arch and Oriental Terrace, and the narrator's own
dining room.  Three of the four locations already carry a
`wide_establishing.png`; what they do not carry is the HOUR, and the hour
comes from the reference and never from the words (MEASURED 2026-09-20 on
ep05: shots written "full dark" came back in evening light twice).  So this
episode's reference work is a NIGHT wide for the canal bridge and for Maybury
Hill, and one new interior for the dining room -- four pictures, local, free.

FOUR VOICES, WHICH IS THE CAP: the narrator, his wife, and the neighbour and
the neighbour's wife at the gate.  Wells's group at the gate is "two men and a
woman" with no names, and the couple who walked out to the common in episode 6
are exactly who would be standing at a gate on this road an hour later.  Her
laughing here, after what she shrieked there, is the episode's cruellest cut
and it costs nothing to stage: both already have sheets and rendered voices.

ORDER OF WORK (ep06 cost three whole picture stages by getting this wrong):
this plan goes through `takes_r2v.py ... --from-refs --prompts` until it is
clean BEFORE any audio, any grid and any take is rendered.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep07" / "plan.json"

# NO LEADING ARTICLE and no proper noun it has not earned: `where` is spliced
# into the STYLE LINE and L20 reads a stray capital as a name it does not know.
# Every one of ep01-06 says exactly this.
WHERE = "Horsell, Surrey, 1894"
LIGHT = "gaslight and black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

# THE CAST IS DESCRIBED FROM ITS BOUND ROWS (`refs.json`), never from memory.
# The content gate read a moustache on a narrator this plan had called
# clean-shaven, and the row is what the take prompt and the sheet both carry.
NARRATOR = ("the narrator, a slender narrow-shouldered man of thirty-four with a long oval face, "
            "grey eyes and dark brown hair parted on the left, a neat close-trimmed dark brown "
            "moustache and shaven cheeks, in a mid-grey herringbone tweed suit with the jacket "
            "torn at the left elbow, his starched collar sprung from its stud and his green tie "
            "pulled sideways, bareheaded")
WIFE = ("the narrator's wife, a slim straight-backed woman of twenty-nine with an oval face, wide "
        "hazel eyes and light freckles across the nose, her thick chestnut-auburn hair swept up "
        "into a soft pompadour, in a lilac-grey cotton house dress with a high collar and a white "
        "bibbed apron tied at the waist, a plain gold band on her hand")
NEIGHBOUR = ("the neighbour, a tall spare man of forty-eight with a slight stoop, hollow cheeks, "
             "grey-brown hair receding at the temples and a short pointed grey goatee with shaved "
             "cheeks and lip, in a sky-blue-and-white striped flannel blazer and white flannel "
             "trousers, a flat-crowned cream straw panama in his hand")
NEIGHBOURS_WIFE = ("the neighbour's wife, a slender straight-backed woman of forty-five with a "
                   "fine-boned oval face, thin lips and grey-green eyes, her iron-grey hair "
                   "centre-parted and drawn into a low smooth chignon, in a dark high-necked "
                   "dress")

# ---- the four places, each naming its own light and the direction it comes from --
COMMON_DARK = (
    "the open heather of Horsell Common at night in 1894, away from the pit: knee-deep purple-brown "
    "heather and dark furze standing black in every direction, young Scots pines in loose stands "
    "with bare trunks, bare sand tracks worn pale through the heather, the ground broken and "
    "uneven underfoot, a horizon that runs dead flat and level, closed by a line of low pines, "
    "and a low red glow "
    "in the sky behind on that horizon where the pit lies; the only light is that glow from behind, low and raking, so "
    "the heather reads black and the pine trunks catch a dull red down one side")
CANAL_NIGHT = (
    "the bridge that carries the road over the canal by the Woking gasworks at night in 1894: a "
    "low brick humpback bridge with a stone parapet, the black canal water below it, the tarred "
    "gasworks retort house and its two gasholders standing beyond, a grass verge and a milestone at "
    "the roadside, and a row of electric lamps burning along the works wall; the light is that lamp "
    "light from the right, hard and white, so the road and the parapet read pale grey, the water "
    "reads black, and everything away from the lamps is black")
MAYBURY_NIGHT = (
    "the road up Maybury Hill at night in 1894 where it passes under the railway arch: a brick "
    "railway arch across the road with the embankment above it, a pretty row of gabled brick villas "
    "called Oriental Terrace along the near side each with a low front gate and a strip of garden, "
    "lit windows and a gas street lamp at the kerb, and the hill going up dark beyond; the light is "
    "gaslight from the left and the lit windows behind it, warm and low, so the road reads pale, "
    "the gables read warm brick and the arch and the embankment are black")
DINING_LAMP = (
    "the narrator's dining room at night in 1894: a small square room with a papered wall and a "
    "framed engraving, a mahogany table laid with a white cloth, a cold joint and bread and a "
    "decanter of wine set out on it, two chairs drawn up, a sideboard against the wall and a "
    "curtained sash window; the light is one oil lamp standing on the table, warm and from below, "
    "so the cloth and the faces read warm and the corners of the room are black")

GEO_COMMON = (
    "Black heather fills the BOTTOM two thirds of the frame from the LEFT edge to the RIGHT edge. "
    "The nearest pine trunk stands at the LEFT third from the BOTTOM to the TOP third, its bark "
    "clearly lit red down the side that faces the glow and rough enough to read. A bare sand "
    "track runs from the BOTTOM CENTRE away into the CENTRE, pale and clearly lit against the "
    "black heather on both sides of it. Further trunks stand at the RIGHT third, a flat line of "
    "low pines closes the horizon across the CENTRE, and a low red glow lies along it under a "
    "black sky that fills the TOP third.")
GEO_CANAL = (
    "The pale road runs from the BOTTOM edge up over the hump of the bridge at the CENTRE and away. "
    "The stone parapet runs across the CENTRE from the LEFT edge to the RIGHT edge. Black canal "
    "water shows at the BOTTOM LEFT below it, the gasholders stand at the RIGHT third against the "
    "TOP third, and a line of hard white lamps burns along the RIGHT edge.")
GEO_MAYBURY = (
    "The brick railway arch crosses the CENTRE of the frame from the LEFT edge to the RIGHT edge, "
    "black, with the embankment above it filling the TOP third. The pale road runs from the BOTTOM "
    "edge through the arch at the CENTRE. The gabled villas of Oriental Terrace stand along the "
    "LEFT from the BOTTOM LEFT to the CENTRE with lit windows, and a gas lamp stands at the kerb at "
    "the CENTRE LEFT.")
GEO_DINING = (
    "The laid table fills the BOTTOM half of the frame from the LEFT edge to the RIGHT edge, its "
    "white cloth the brightest thing in the picture. The oil lamp stands at the CENTRE on the "
    "table, the cold joint and the decanter at the CENTRE RIGHT, and the papered wall with its "
    "framed engraving fills the TOP third behind, going black at the LEFT edge and the RIGHT edge.")

SETUPS = {
    "flight": dict(
        described=COMMON_DARK, cast=["unnamed_first_person_narrator"],
        landmark="the low red glow in the sky behind on the horizon", landmark_at="far_end",
        landmark_size="is a twelfth of the height of the frame",
        route="from out among the pines on the black common down toward the road",
        geometry=GEO_COMMON, crowd="", outdoors=True, props=[], location="horsell_common"),
    "canal": dict(
        described=CANAL_NIGHT, cast=["unnamed_first_person_narrator"],
        landmark="the lit gasholders of the gasworks beyond the bridge", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the grass verge at the roadside up over the hump of the canal bridge",
        geometry=GEO_CANAL, crowd="", outdoors=True, props=[], location="maybury_canal_bridge"),
    "arch": dict(
        described=MAYBURY_NIGHT, cast=["unnamed_first_person_narrator"],
        landmark="the brick railway arch across the road", landmark_at="far_end",
        landmark_size="fills the middle third of the frame",
        route="from the far side of the canal bridge up the road to the railway arch",
        geometry=GEO_MAYBURY, crowd="", outdoors=True, props=[], location="maybury_hill"),
    "gate": dict(
        described=MAYBURY_NIGHT, cast=["unnamed_first_person_narrator", "unnamed_neighbour",
                                       "unnamed_neighbours_wife"],
        landmark="the lit windows of the gabled villas of Oriental Terrace",
        landmark_at="start", landmark_size="is a quarter of the height of the frame",
        route="from under the arch along Oriental Terrace to the gate where the three stand",
        geometry=GEO_MAYBURY,
        crowd="two men and a woman standing about a front gate in the warm light of their own "
              "window, talking easily, at their ease",
        outdoors=True, props=[], location="maybury_hill"),
    "door": dict(
        described=MAYBURY_NIGHT, cast=["unnamed_first_person_narrator", "narrators_wife"],
        landmark="the lit fanlight over the narrator's own front door", landmark_at="far_end",
        landmark_size="is a sixth of the height of the frame",
        route="from the road along the garden strip to the narrator's own doorstep",
        geometry=GEO_MAYBURY, crowd="", outdoors=True, props=[], location="narrators_home"),
    "table": dict(
        described=DINING_LAMP, cast=["unnamed_first_person_narrator", "narrators_wife"],
        landmark="the oil lamp standing on the laid table", landmark_at="start",
        landmark_size="is a fifth of the height of the frame",
        route="from the dining room door round the laid table to the chairs drawn up at it",
        geometry=GEO_DINING, crowd="", outdoors=False, props=[], location="narrators_home"),
}

#  setup   size   faces  path  move   frame / motion / camera / at_rest / section / why
S = [
    # ---- flight: he remembers nothing of it ------------------------------------
    ("flight", "wide", [], 0.1, "track_lateral",
     "Wide of the black common at night among the pines, empty heather from edge to edge: bare "
     "pine trunks "
     "standing in a loose stand out of knee-deep black heather, the ground broken and uneven "
     "between them, and a low red glow lying along the horizon behind.",
     "The camera tracks sideways to the right, a truck with small amplitude between the trunks "
     "until the furthest pine already in the picture is at the centre, travelling one short "
     "stride; a track of bent heather stems runs away through the picture; the red glow behind "
     "goes on burning low.",
     "out among the pines at a standing man's eye, a 35mm lens. The only light is the red glow "
     "behind on the horizon; the heather and the trunks are black and each trunk catches a dull "
     "red down one side",
     GEO_COMMON, "hook", "He remembers nothing of the flight, so it is shown without him."),

    ("flight", "medium", ["unnamed_first_person_narrator"], 0.4, "follow",
     f"Medium on {NARRATOR} blundering through the heather at night, hatless, one arm up across "
     "his face, his collar burst open at the stud, running badly over broken ground with the "
     "black pines going past behind him.",
     "The camera tracks with him at his own pace, a truck with small amplitude, keeping him in the "
     "middle of "
     "the picture, travelling one short stride; he strikes a trunk with his shoulder and comes "
     "off it still running; his free hand goes on beating the heather aside.",
     "out among the pines level with his chest, four paces from him, a 35mm lens. The red glow "
     "behind lights one side of him; his face and the heather ahead of him are black",
     GEO_COMMON, "setup", "The stress of blundering against trees and stumbling through heather."),

    ("flight", "insert", [], 0.7, "tilt_up",
     "Insert on the broken ground at night: knee-deep black heather stems and bare sandy earth "
     "between them, a boot print pressed into the sand and filling in at its edge, and the dull "
     "red of the glow behind catching the tops of the stems.",
     "The camera tilts up from the print along the bent track, travelling a hand's breadth, until "
     "the heather that was pushed aside is in the middle of the picture; the stems come back "
     "upright one after another; sand runs back into the print a grain at a time as they do.",
     "on the ground among the heather stems, a 50mm lens, a low angle. The red glow comes from "
     "behind and lights the tops of the stems; the sand reads dull red and the roots are black",
     GEO_COMMON, "setup", "The only record that he came this way at all."),

    ("flight", "wide", ["unnamed_first_person_narrator"], 0.9, "crane_up",
     f"Wide of the roadside at night where the common ends: {NARRATOR} down on his hands and knees "
     "in the grass of the verge with his head hanging, the pale road running away past him, and "
     "the lit gasholders of the gasworks standing beyond.",
     "The camera rises from the verge with small amplitude until the road and the lit gasworks "
     "beyond both stand inside the picture, travelling one short stride; he sinks from his hands "
     "on to his side in the grass; his breath goes on lifting his shoulder where he lies.",
     "at the edge of the verge low to the grass, six paces from him, a 35mm lens. The hard white "
     "lamps of the gasworks come from the RIGHT; the grass reads pale grey and he reads black "
     "against it",
     GEO_CANAL, "setup", "At last he could go no further, and fell by the wayside."),

    # ---- canal: the terror falls off him like a garment --------------------------
    ("canal", "medium", ["unnamed_first_person_narrator"], 0.2, "crane_up",
     f"Medium on {NARRATOR} lying still on the grass verge at night by the canal bridge, on his "
     "side with one arm under his head, his eyes open and fixed on the road past the camera, the "
     "stone parapet of "
     "the bridge behind him and the hard white lamps of the gasworks beyond.",
     "The camera rises off the grass with small amplitude until his whole length and the parapet "
     "behind him are in the picture, travelling one short stride; his open eyes go on staring "
     "past the camera; his breathing goes on lifting his shoulder where he lies.",
     "on the verge level with his face, three paces from him, a 50mm lens. The lamp light comes "
     "from the RIGHT and lights one side of his face; the grass and the road are black",
     GEO_CANAL, "setup", "I fell and lay still. I must have remained there some time."),

    ("canal", "medium_close", ["unnamed_first_person_narrator"], 0.4, "tilt_up",
     f"Medium close on {NARRATOR} sitting up on the verge at night, strangely perplexed, his hair "
     "disordered and his collar burst open at the stud, looking about him at a road he knows "
     "perfectly well, with the white lamps of the gasworks behind him.",
     "The camera tilts up with the movement of his head until his face is in the middle of the "
     "picture, travelling a hand's breadth; he turns his head a hand's breadth from the road to "
     "his own "
     "hands and back; his shoulders come down out of their held-up place.",
     "on the verge level with his face, two paces from him, a 50mm lens. The lamp light comes "
     "from behind him at the RIGHT and rims his hair and his shoulder; his face reads dull and "
     "the road behind is black",
     "The narrator's head and shoulders fill the CENTRE of the frame, the panel cutting him at "
     "the middle of the chest, his head a third the frame's height at the TOP third. The stone "
     "parapet runs across the CENTRE behind him, the hard white lamps burn at the RIGHT edge, and "
     "a black sky fills the TOP third.",
     "turn", "My terror had fallen from me like a garment."),

    ("canal", "insert", [], 0.6, "locked",
     "Insert on a soft felt hat lying crown-down in the grass of the verge at night, well away "
     "from the road, its brim bent where it fell and dew already standing on the felt, with the "
     "hard white lamp light raking across the grass beside it.",
     "The camera holds a static shot close over the grass; the grass stems lean back upright one "
     "at a time around the brim; the dew on the felt goes on catching the lamp light as they move.",
     "in the grass of the verge, a 50mm lens, a low angle. The lamp light comes from the RIGHT "
     "and rakes the grass; the felt reads dull grey and the grass around it is black",
     GEO_CANAL, "setup", "My hat had gone, and my collar had burst away from its fastener."),

    ("canal", "medium", ["unnamed_first_person_narrator"], 0.8, "crane_up",
     f"Medium on {NARRATOR} standing up unsteadily at the foot of the canal bridge at night, one "
     "hand out to the stone parapet to keep himself up, looking at the pale road going up over "
     "the hump of the bridge ahead of him.",
     "The camera rises with him as he comes up with small amplitude until the road over the "
     "bridge is inside the picture, travelling one short stride; he gets his hand on to the "
     "parapet and takes his weight on it; he starts up the incline still holding it.",
     "at the foot of the bridge level with his chest, four paces from him, a 35mm lens. The lamp "
     "light comes from the RIGHT and picks out the parapet and one side of him; the water below "
     "is black",
     GEO_CANAL, "setup", "I rose and walked unsteadily up the steep incline of the bridge."),

    # ---- arch: the world is going about its business -----------------------------
    ("arch", "medium", ["unnamed_first_person_narrator"], 0.2, "follow",
     f"Medium on {NARRATOR} coming over the crown of the bridge at night, walking badly with his "
     "hand still on the parapet, the pale road going away down in front of him toward the brick "
     "railway arch and the lit villas beyond it.",
     "The camera tracks with him over the crown at his own pace, a truck with small amplitude, "
     "keeping him at "
     "the left of the picture, travelling one short stride; he takes his hand off the parapet and "
     "sways a hand's breadth; the road ahead of him goes on opening out.",
     "on the bridge level with his shoulder, three paces behind him, a 35mm lens. The gas lamp "
     "ahead comes from the LEFT and the works lamps from behind; the road reads pale and he reads "
     "black against it",
     GEO_MAYBURY, "friction", "My mind was blank wonder. I dare say I staggered drunkenly."),

    ("arch", "medium", ["unnamed_first_person_narrator"], 0.4, "pan_to",
     "Medium past the near shoulder of the narrator as a workman comes up over the arch of the "
     "bridge at night, a solid man in a cloth cap and a jacket with a covered basket on his arm, "
     "and a small boy walking beside him with his hand in the man's coat pocket, the two of them "
     "going home and easy about it while the narrator stands still in the road.",
     "The camera pans to the right with them until the boy already in the picture is at the "
     "centre, travelling a hand's breadth; the narrator's near shoulder stays where it is as "
     "they pass it; the basket goes on swinging on the arm that carries it.",
     "on the bridge level with their faces, four paces from them, a 50mm lens. The works lamps "
     "come from the RIGHT and light the cap and the boy's face; the narrator's shoulder in the "
     "near left is black",
     GEO_CANAL, "friction", "He passed me, wishing me good night."),

    ("arch", "insert", [], 0.6, "track_lateral",
     "Insert on a train crossing the Maybury arch at night, seen close: a long caterpillar of "
     "lighted carriage windows going hard from left to right above the brickwork, with a billowing "
     "tumult of white firelit smoke rolling up off it into the black.",
     "The camera tracks sideways to the right with the train, a truck with small amplitude, until "
     "the last lighted window already in the picture is at the centre, travelling a hand's "
     "breadth; the lighted windows go on flying past; the white smoke goes on boiling up "
     "through the frame.",
     "under the embankment looking up at the arch, a 35mm lens, a low angle. The carriage windows "
     "are the light and they come from the RIGHT; the smoke reads white and the brickwork is "
     "black",
     GEO_MAYBURY, "friction", "Clatter, clatter, clap, rap, and it had gone."),

    ("arch", "medium_close", ["unnamed_first_person_narrator"], 0.8, "locked",
     f"Medium close on {NARRATOR} standing still in the road under the arch at night, looking up "
     "after the train with his mouth a little open, the light of the passing carriage windows "
     "going across his face in bars.",
     "The camera holds a static shot level with his face; the barred light of the carriages goes "
     "on crossing his face from the left; his eyes go on following it up and over.",
     "in the road level with his face, two paces from him, a 50mm lens. The carriage windows are "
     "the light and they come from above at the LEFT; his face reads warm in bars and the arch "
     "behind him is black",
     "The narrator's head and shoulders fill the CENTRE of the frame, the panel cutting him at "
     "the middle of the chest, his head a third the frame's height at the TOP third. The black "
     "brick of the arch fills the whole frame behind him, and bars of window light cross him from "
     "the LEFT edge to the RIGHT edge.",
     "friction", "It was all so real and so familiar. And that behind me!"),

    # ---- gate: the news is offered, and declined ---------------------------------
    ("gate", "wide", [], 0.1, "crane_up",
     "Wide of Oriental Terrace at night: a pretty row of gabled brick villas along the near side "
     "of the road with lit windows and low front gates, a gas street lamp burning at the kerb, a "
     "strip of garden in front of each, and the hill going up dark beyond them.",
     "The camera rises from the road with small amplitude until the whole row of gables and the "
     "hill beyond stand inside the picture, travelling one short stride; the gas lamp at the kerb "
     "goes on burning steadily; a curtain moves in one of the lit windows and settles.",
     "in the middle of the road at a standing man's eye, a 35mm lens. The gaslight comes from the "
     "LEFT and the lit windows from behind it; the road reads pale, the gables read warm brick "
     "and the hill beyond is black",
     GEO_MAYBURY, "setup", "A dim group of people talked in the gate of one of the houses."),

    ("gate", "medium", ["unnamed_neighbour", "unnamed_neighbours_wife"], 0.4, "track_lateral",
     f"Medium on {NEIGHBOUR} and {NEIGHBOURS_WIFE} standing at their own front gate at night with "
     "a second man beside them, all three standing at their ease in the warm light of their own "
     "window, the woman leaning on the gate itself.",
     "The camera tracks sideways to the left along the railings, a truck with small amplitude, "
     "until the gate already in the picture is at the centre, travelling one short stride; the "
     "neighbour takes the pipe out of his mouth to say something; the woman leans further on to "
     "the gate and goes on listening.",
     "on the pavement level with their faces, four paces from them, a 50mm lens. The window light "
     "comes from the RIGHT behind them and the gas lamp from the LEFT; their faces read warm and "
     "the garden is black",
     GEO_MAYBURY, "friction", "It was all so real and so familiar."),

    ("gate", "medium_close", ["unnamed_first_person_narrator"], 0.6, "locked",
     f"Medium close on {NARRATOR} stopped on the pavement at the gate at night, hatless, his "
     "collar still open, asking them something across the railings with the warm window light on "
     "one side of his face.",
     "The camera holds a static shot level with his face; he asks it and waits with his head a "
     "little forward; his hand goes on to the top of the railings and stays there.",
     "on the pavement level with his face, two paces from him, a 50mm lens. The window light "
     "comes from the LEFT and lights one side of his face; the road behind him is black",
     "The narrator's head and shoulders fill the CENTRE of the frame, the panel cutting him at "
     "the middle of the chest, his head a third the frame's height at the TOP third. The iron "
     "railings cross the BOTTOM third, the lit window shows warm at the LEFT edge, and the black "
     "road fills the RIGHT third behind him.",
     "friction", "What news from the common?"),

    ("gate", "medium_close", ["unnamed_neighbour"], 0.7, "over_shoulder",
     f"Medium close over the shoulder of {NARRATOR} toward {NEIGHBOUR} at the gate at night: the "
     "narrator's dark shoulder near and black at the LEFT, the neighbour square in the right of "
     "the picture in his shirtsleeves and waistcoat, turning with the pipe still in his hand.",
     "The camera holds a static shot over the narrator's shoulder, keeping the neighbour's face "
     "in the right of frame; the neighbour turns his head to answer and keeps turning it; the "
     "pipe comes up toward his mouth again as he speaks.",
     "on the pavement level with their eyes, two paces behind the narrator, a 50mm lens. The "
     "window light comes from the RIGHT and lights the neighbour's face and forearm; the "
     "narrator's shoulder in the near left is black",
     "The narrator's shoulder fills the LEFT third of the frame from the TOP edge to the BOTTOM "
     "edge, black and out of focus. The neighbour stands at the RIGHT third, the panel cutting "
     "him at the middle of the chest, his head a third the frame's height at the TOP third. The "
     "lit window shows warm behind him at the RIGHT edge.",
     "friction", "Ain't yer just been there?"),

    ("gate", "medium_close", ["unnamed_neighbours_wife"], 0.8, "locked",
     f"Medium close on {NEIGHBOURS_WIFE} leaning on the top bar of her own gate at night, her "
     "bonnet strings loose, speaking across it with her chin up and her eyes amused, the warm "
     "light of her own window full on her face.",
     "The camera holds a static shot level with her face; she says it across the gate and her "
     "chin stays up; her hands go on resting flat along the top bar of the gate.",
     "on the pavement level with her face, two paces from her, a 50mm lens. The window light "
     "comes from behind the camera and is full on her face; the garden behind her is black",
     "The neighbour's wife fills the CENTRE of the frame, the panel cutting her at the middle of "
     "the chest, her head a third the frame's height at the TOP third. The top bar of the gate "
     "crosses the BOTTOM third with both her hands on it, and the black garden fills the frame "
     "behind her.",
     "friction", "People seem fair silly about the common. What's it all abart?"),

    ("gate", "medium", ["unnamed_neighbour", "unnamed_neighbours_wife"], 0.9, "pan_to",
     f"Medium on {NEIGHBOUR} and {NEIGHBOURS_WIFE} and the second man at the gate at night, all "
     "three of them laughing together at what has just been said to them, the woman with her head "
     "back and the neighbour with the pipe held away from his mouth.",
     "The camera pans to the left across the three of them until the woman already in the picture "
     "is at the centre, travelling a hand's breadth; the neighbour's shoulders go on shaking; the "
     "woman's head comes forward and she goes on laughing over the gate.",
     "on the pavement level with their faces, three paces from them, a 50mm lens. The window "
     "light comes from the RIGHT and is full on all three; the road and the garden are black",
     GEO_MAYBURY, "spike", "All three of them laughed."),

    ("gate", "medium_close", ["unnamed_first_person_narrator"], 0.95, "locked",
     f"Medium close on {NARRATOR} at the gate at night with the laughter going on in front of "
     "him, his mouth half open on a sentence he has given up, his hand coming down off the "
     "railings.",
     "The camera holds a static shot level with his face; his mouth closes after the words; his "
     "hand comes down off the railings and goes on down to his side; he turns his shoulder "
     "away from the gate and goes on turning until the light leaves his face.",
     "on the pavement level with his face, two paces from him, a 50mm lens. The window light "
     "comes from the LEFT and lights one side of his face; the road behind him is black",
     "The narrator's head and shoulders fill the CENTRE of the frame, the panel cutting him at "
     "the middle of the chest, his head a third the frame's height at the TOP third. The iron "
     "railings cross the BOTTOM third and the black road fills the frame behind him.",
     "reaction", "I tried and found I could not tell them what I had seen."),

    # ---- door: he brings it home -------------------------------------------------
    ("door", "medium", ["narrators_wife"], 0.3, "crane_up",
     f"Medium on {WIFE} standing in her own lit doorway at night with the door held open against "
     "her shoulder, the warm hall light behind her, looking out at something on the step that has "
     "stopped her where she stands.",
     "The camera rises from the step with small amplitude until her face and the lit hall behind "
     "her are both in the picture, travelling one short stride; her hand goes on tightening on "
     "the edge of the door; the hall light goes on falling out across the step past her.",
     "on the doorstep level with her face, three paces from her, a 50mm lens. The hall light "
     "comes from behind her and rims her hair and shoulder; her face reads dim and the garden "
     "behind the camera is black",
     GEO_MAYBURY, "setup", "I startled my wife at the doorway, so haggard was I."),

    ("door", "insert", [], 0.6, "locked",
     "Insert on a burst collar stud and an open shirt collar at night, close: the linen collar "
     "sprung away from its fastener at the throat, the brass stud hanging by its shank, and a "
     "smear of sand and heather dust across the linen, with warm hall light falling across it "
     "from one side.",
     "The camera holds a static shot close on the collar; the loose stud goes on swinging a "
     "little on its shank; the warm light goes on moving across the linen as the door behind "
     "swings.",
     "on the doorstep close to his throat, a 50mm lens. The hall light comes from the LEFT and "
     "rakes the linen; the collar reads warm white and everything behind it is black",
     GEO_MAYBURY, "setup", "A decent ordinary citizen, with the common still on him."),

    # ---- table: the cold dinner, and the true thing --------------------------------
    ("table", "wide", [], 0.1, "crane_up",
     "Wide of the little dining room at night, the two chairs at the table both empty: a mahogany "
     "table laid with a "
     "white cloth, a cold joint and bread and a decanter of wine set out, two chairs drawn up, an "
     "oil lamp burning in the middle of the cloth and the corners of the room black.",
     "The camera rises from the table with small amplitude until the whole laid cloth and the "
     "papered wall behind it stand inside the picture, travelling one short stride; the lamp "
     "flame leans and rights itself as the door behind opens; the light goes on moving on the "
     "cloth.",
     "at the end of the table a little above it, a 35mm lens. The oil lamp on the table is the "
     "only light and it comes from below; the cloth reads warm white and the corners of the room "
     "are black",
     GEO_DINING, "answer", "The dinner, a cold one, had already been served."),

    ("table", "medium", ["unnamed_first_person_narrator"], 0.4, "locked",
     f"Medium on {NARRATOR} sitting at the laid table at night with a glass of wine in his hand, "
     "his collar still open, talking steadily across the cloth with the lamp between him and the "
     "camera.",
     "The camera holds a static shot across the table level with his chest; he sets the glass "
     "down on the cloth and leaves his hand round it; he goes on talking with his eyes on the "
     "lamp between them.",
     "across the table level with his chest, four paces from him, a 50mm lens. The oil lamp is "
     "between them and lights him from below; the wall behind him is black",
     GEO_DINING, "answer", "They may keep the pit and kill people who come near them."),

    ("table", "insert", [], 0.6, "locked",
     "Insert on the cold dinner standing whole on the white cloth at night: a cut joint on its "
     "dish with the fat set hard and grey, a cottage loaf beside it, two clean plates and a "
     "decanter with the light of the lamp standing in the wine, and the knives and forks square "
     "where they were laid.",
     "The camera holds a static shot close over the cloth; the light in the decanter goes on "
     "shifting as the lamp flame moves; a bead of condensation goes on running down the glass.",
     "over the table close to the cloth, a 50mm lens. The oil lamp is beside it and lights it "
     "from the side; the cloth reads warm white and the room beyond is black",
     GEO_DINING, "answer", "It remained neglected on the table while I told my story."),


    ("table", "medium_close", ["unnamed_first_person_narrator"], 0.9, "over_shoulder",
     f"Medium close over the shoulder of {WIFE} toward {NARRATOR} at the table at night: the back "
     "of her head and her pale shoulder near and soft at the LEFT, turned away so only her hair "
     "shows, the narrator square in the right of the picture with "
     "the decanter at his elbow, explaining something reasonable to her across the cloth.",
     "The camera holds a static shot over her shoulder, keeping his face in the right of frame; "
     "he lifts the decanter and goes on pouring for her; his other hand goes on turning over as "
     "he explains.",
     "across the table level with their eyes, two paces behind her, a 50mm lens. The oil lamp "
     "lights his face from below at the LEFT; her shoulder in the near left is soft and dim",
     "The BACK of the wife's head and her shoulder fill the LEFT third of the frame from the TOP "
     "edge to the BOTTOM edge, turned fully away from the camera, soft and out of focus. The "
     "narrator sits at the RIGHT third, the panel cutting him at the "
     "middle of the chest, his head a third the frame's height at the TOP third. The white cloth "
     "crosses the BOTTOM third between them.",
     "runout", "I pressed her to take wine, and tried to reassure her."),

    ("table", "insert", [], 0.95, "locked",
     "Insert on the oil lamp standing on the white cloth at night, close: its brass reservoir and "
     "glass chimney with the flame standing straight up inside, the cloth around its foot bright, "
     "and the black of the room beginning a hand's breadth beyond the light.",
     "The camera holds a static shot close on the chimney; the flame leans over and comes "
     "straight again as something moves in the room; the ring of light on the cloth goes on "
     "breathing in and out with it.",
     "on the table close to the lamp, a 50mm lens. The lamp is the light and it comes from the "
     "CENTRE; the cloth reads warm white and everything a hand's breadth beyond it is black",
     GEO_DINING, "runout", "The last light in the house, and how far it reaches."),
    ("table", "medium_close", ["narrators_wife"], 0.8, "tilt_up",
     f"Medium close on {WIFE} at the table at night, her face deadly white in the lamplight, her "
     "brows knitted and her hand laid flat on the cloth halfway across it toward him, listening "
     "with her plate still square in front of her.",
     "The camera tilts up from the cloth to her face, travelling a hand's breadth, until her eyes "
     "are in the middle of the picture; her hand goes on further across the cloth toward his; "
     "the lamplight goes on moving on her face as the flame works.",
     "across the table level with her face, three paces from her, a 50mm lens. The oil lamp "
     "lights her from below and from the LEFT; her face reads warm white and the room behind her "
     "is black",
     "The wife's head and shoulders fill the CENTRE of the frame, the panel cutting her at the "
     "middle of the chest, her head a third the frame's height at the TOP third. The white cloth "
     "fills the BOTTOM third with her hand laid flat on it. The papered wall of the dining room "
     "stands behind her with its framed engraving at the RIGHT third and the curtained sash "
     "window at the LEFT third, both dim in the lamplight, so the room she is sitting in is "
     "visible all round her.",
     "button", "They may come here. She says it again and again, and she is right."),
]

MOVES = {i: s[4] for i, s in enumerate(S)}

BEATS = {0: (1.0, 0.6), 2: (1.2, 1.5), 3: (1.0, 0.4), 5: (1.2, 0.8),
         6: (1.0, 1.0), 10: (1.0, 0.8), 12: (1.0, 0.6),
         # THE TWO SHORT REPLIES AT THE GATE. Left at the default they
         # projected 3.0 s each and ONE PER TAKE packed them together,
         # which puts two mouths under one lip-sync gate.
         14: (1.2, 1.2), 15: (1.2, 1.2),
         17: (0.8, 0.8),
         18: (0.8, 1.0),
         # The collar insert held 2.2 s and packed into the doorway shot with
         # it; a silent shot has to be long enough to be its own take.
         20: (1.5, 3.0), 21: (1.0, 0.6), 23: (1.2, 1.2),
         24: (0.8, 0.6), 25: (1.0, 0.8), 26: (0.6, 0.8)}

TURNS = {17: "a man carrying the news -> a man carrying a story",
         21: "a house that has not heard -> a house that has",
         26: "a wife being reassured -> a wife who is right"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "Of the running I kept nothing. Trees, and the shock of hitting them.", 0),
    ("narration", "unnamed_first_person_narrator",
     "Everything I could not see was them, and it was all around me.", 1),
    ("narration", "unnamed_first_person_narrator",
     "Somewhere above, I was sure, that blade of heat was still turning.", 2),
    ("narration", "unnamed_first_person_narrator",
     "At last I could go no further, and I fell by the wayside.", 3),
    ("narration", "unnamed_first_person_narrator",
     "Then the ground had me, and I stayed on it a long while.", 4),
    # HIS OWN QUESTION, SAID ALOUD. Wells has it as a thought -- "I asked myself
    # had these latter things indeed happened" -- and the gates want a voice in
    # the first quarter, so the thought is spoken to the empty road. It is his
    # own sentence and nobody hears it.
    ("dialogue", "unnamed_first_person_narrator", "Did that happen? Did any of that happen?", 5),
    ("narration", "unnamed_first_person_narrator",
     "Somewhere behind me was my hat. My collar had torn off its stud.", 6),
    ("narration", "unnamed_first_person_narrator",
     "The fear came off me like a garment, and I was a citizen again.", 7),
    ("narration", "unnamed_first_person_narrator",
     "The heath, the quiet, the flames going up: a dream I had just left.", 8),
    ("narration", "unnamed_first_person_narrator",
     "A head rose over the arch, and a workman with a basket came by.", 9),
    ("narration", "unnamed_first_person_narrator",
     "He wished me good night. I made a noise at him and walked on.", 10),
    ("narration", "unnamed_first_person_narrator",
     "Over the Maybury arch a train went flying south, and it had gone.", 11),
    ("narration", "unnamed_first_person_narrator",
     "All of it ordinary, all of it certain. And two miles back, that.", 12),
    ("narration", "unnamed_first_person_narrator",
     "Three of them stood talking at a front gate, and I stopped there.", 13),
    ("dialogue", "unnamed_first_person_narrator", "What news from the common?", 14),
    ("dialogue", "unnamed_neighbour", "Ain't yer just been there?", 15),
    ("dialogue", "unnamed_neighbours_wife",
     "People seem fair silly about the common. What's it all about?", 16),
    ("narration", "unnamed_first_person_narrator",
     "Haven't you heard of the men from Mars, I said. The creatures from Mars.", 17),
    # THE ONLY THING HE SAYS BACK, so he says it instead of reporting it. A
    # dialogue line opens its own shot.
    ("dialogue", "unnamed_first_person_narrator", "You'll hear more yet.", 18),
    ("narration", "unnamed_first_person_narrator",
     "I felt foolish, and went on home.", 18),
    ("narration", "unnamed_first_person_narrator",
     "My wife opened the door. She stepped back from the look of me.", 19),
    ("narration", "unnamed_first_person_narrator",
     "I went in, sat down, drank some wine, and told her what I had seen.", 22),
    ("narration", "unnamed_first_person_narrator",
     "Nothing alive has ever moved so slowly, I told her. They barely crawl.", 23),
    ("narration", "unnamed_first_person_narrator",
     "They may keep the pit, but they cannot get out of it.", 24),
    ("narration", "unnamed_first_person_narrator",
     "I laid stress on the weight of them here, and overlooked two things.", 25),
    # THE BUTTON IS NEVER THE PROTAGONIST'S (rule 5). Wells gives her this line
    # "again and again", and it is the only true statement anybody makes in the
    # chapter -- he spends the evening arguing against it, and Wells says
    # plainly that he was wrong.
    ("dialogue", "narrators_wife", "They may come here.", 26),
]

BEDS = [{"from_shot": 0, "tone": "grave"}, {"from_shot": 4, "tone": "uneasy"},
        {"from_shot": 9, "tone": "plain"}, {"from_shot": 13, "tone": "plain"},
        {"from_shot": 18, "tone": "uneasy"}, {"from_shot": 22, "tone": "grave"}]

# WHERE EACH SHOT STANDS ALONG ITS SETUP'S ROUTE, 0 at the start and 1 at the
# far end. The route gate refuses a shot that goes BACKWARDS along it.
PATHS = {
    0: 0.1, 1: 0.4, 2: 0.7, 3: 0.9,                            # flight
    4: 0.2, 5: 0.4, 6: 0.6, 7: 0.8,                            # canal
    8: 0.2, 9: 0.4, 10: 0.6, 11: 0.8,                          # arch
    12: 0.1, 13: 0.4, 14: 0.6, 15: 0.7, 16: 0.8, 17: 0.9,      # gate
    18: 0.95,                                                  # gate, the reaction
    19: 0.3, 20: 0.6,                                          # door
    21: 0.1, 22: 0.4, 23: 0.6, 24: 0.8, 25: 0.9, 26: 0.95,     # table
}

SECTIONS = {
    0: "hook",
    1: "setup", 2: "setup", 3: "setup", 4: "setup",
    # THE TURN IS THE LAUGHTER, not the terror falling off him. Shot 5 is a
    # change in HIM and it lands at 18% of the runtime, where the contract
    # wants the turn between 50 and 75%; the laughter is the change in his
    # SITUATION and it lands at 63%. The docstring said so and the sections
    # did not.
    5: "reaction",
    6: "setup", 7: "setup", 8: "friction",
    9: "friction", 10: "friction", 11: "friction", 12: "setup",
    13: "friction", 14: "friction", 15: "friction", 16: "friction",
    17: "turn",
    18: "reaction",
    19: "setup", 20: "setup",
    21: "answer", 22: "answer", 23: "answer",
    24: "runout", 25: "runout",
    26: "button",
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
    return dict(number=7, title="How I Reached Home",
                question="Can he bring what he saw back into his own house?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 21",
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
