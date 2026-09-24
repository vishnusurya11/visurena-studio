r"""The War of the Worlds, episode 11 -- "At the Window", chapter 11.

THE BRICK.  A man who has run out of feeling watches his world burn from a
window, and it takes a stranger in worse case to bring him back to himself.

  QUESTION  What happened in the last seven hours? "What had happened in the
            last seven hours I still did not know."
  TURN      shot 14. He lets the soldier in: the lead acting on another person
            by his own choice ("Come into the house") -- and from there he is
            the one who pours the whisky and stands beside the man who weeps,
            "with a curious forgetfulness of my own recent despair".
  ANSWER    shot 17: the artilleryman's face in the dark, "They wiped us out.
            Simply wiped us out." The army on the common is gone.
  BUTTON    shot 21, the artilleryman at the window at dawn: "Just like parade
            it had been, a minute before." The book's own words (he says them
            in the dining room); moved to the window so a non-lead line closes
            the chapter on camera, and said so.

ONE NAMED PERSON IN A FRAME. Two different cast sheets in one take merge into
one man (camera catalog, ep05 T08). The two of them never share a frame: the
window talk is cut shot for shot, the dining room is one face at a time, and
the dawn is his face alone.

THE MACHINES ARE AS THE BOOK SEES THEM FROM THE WINDOW: "huge black shapes,
grotesque and strange", far off across the red light, and at dawn "three of
the metallic giants stood about the pit, their cowls rotating". "Tripod" is
said only in the shots that should stage the sheet (3 and 22).

THE LIGHT IS THE FIRE. At night nothing in the house is lit ("We lit no lamp
for fear of attracting the Martians"), so every interior reads by the red
glare through the window, from one side, and never 'like daylight'.

WHAT TODAY'S GATES ASK OF THIS PLAN (2026-09-24): every move aims at a noun its
own at_rest holds (G-AIM); no sideways truck across a person anchored to the
set (G-ANCHOR); a person lying down is seen from above or level (G-LAID; none
lies here); rows say "Hatless", never "Bareheaded"; tags carry chapter=11.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep11" / "plan.json"

WHERE = "Surrey, 1894"
LIGHT = "red firelight from the valley, deep black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

from studio import cast_refs  # noqa: E402

NARRATOR = cast_refs.tag(BOOK, "unnamed_first_person_narrator", "the narrator", [
    "Neat close-trimmed dark brown moustache",
    "Hatless, his dark brown hair combed smooth and parted on the left",
    "A dry second suit in the same mid-grey herringbone tweed"], chapter=11)
GUNNER = cast_refs.tag(BOOK, "artilleryman", "the artilleryman", [
    "Full black moustache",
    "Thick straight black hair cut short at the sides and falling forward over the brow and eyes",
    "Royal Horse Artillery driver's dark blue serge frock jacket with scarlet stand collar and brass "
    "buttons, hanging unbuttoned",
    "Uniform and face blackened with ash and soot"], chapter=11)

# ---- the five places, each naming its hour, its light and where it comes from ----
STUDY_NIGHT = (
    "a tall open sash window glowing red with fire, seen across the narrator's dark study at Maybury "
    "at night in 1894: the window frame full of flat country burning orange and red far below, "
    "out to a low flat dark horizon under "
    "rolling red smoke, a writing desk and a turned desk chair black against it, bookshelves along "
    "the left wall lost in shadow, and the red reflections of a nearer fire dancing on the wall and "
    "the ceiling; the light is the red glare through the open window AHEAD, so the window reads red, "
    "the desk and chair read as black shapes against it and the room reads black")
VALLEY_NIGHT = (
    "flat Surrey country on fire at night in 1894, seen from a hillside window at Maybury: a long "
    "low slope and the level fields beyond set thick with tongues of orange flame out to a low "
    "flat dark horizon, a wrecked train burning with a vivid glare on "
    "the railway near an arch at the centre, the houses about Woking station glowing as red ruins at "
    "the left, the far common about the sand-pits lit blood red, black smoke rolling up red-lit into "
    "the sky, and the dark tops of trees and the railway line in the foreground; the light is the "
    "red glare of the fires AHEAD and below, so the smoke reads red, the country reads black and "
    "the sky reads dark red")
GARDEN_NIGHT = (
    "the narrator's back garden at Maybury at night in 1894 after a storm, seen from an upstairs "
    "window: a small dark lawn trampled and wet, broken rose trees along its edge, a weathered "
    "paling fence at the far end with dark shrubs beyond it, and the pale corner of the house at "
    "the near right; the light is the faint red glare of the fires in the sky BEHIND the fence, so "
    "the palings read black against it, the lawn reads dark grey and the house corner reads pale")
DINING_NIGHT = (
    "the narrator's dining room at Maybury at night in 1894, dark, every lamp cold: a mahogany table "
    "with a whisky decanter and glasses on it, two dining chairs pulled out, a sideboard against the "
    "far wall, dark patterned wallpaper, and a curtained window at the left edge where a faint red "
    "glare comes in; the light is that red glare through the gap in the curtains from the LEFT, so "
    "the glass and the edge of the table read red and the rest of the room reads black")
DAWN_WINDOW = (
    "the view from a hillside study window at Maybury at dawn in 1894 over a valley of ashes: grey "
    "streamers of smoke rising from the countless ruins of gutted houses and blackened trees, a "
    "white railway signal standing untouched amid the wreckage, the blackened common beyond with "
    "the pit at the centre, three tall metallic tripods standing about it with their hooded heads "
    "turned, puffs of green vapour rising out of the pit, and pillars of red smoke far off; the "
    "light is the grey dawn in the east AHEAD at the RIGHT, so the smoke reads grey, the country "
    "reads black and the sky reads pale and cold")

# ---- the geometry of each place: WHERE things are, in cells --------------------------
GEO_STUDY = (
    "The open sash window fills the CENTRE from the TOP third to the BOTTOM third, the burning "
    "valley glowing red inside its frame. The desk and the turned chair stand black against it at "
    "the BOTTOM CENTRE, the dark bookshelves fill the LEFT third, and red reflections dance on the "
    "wall at the RIGHT third. The dark floorboards run from the BOTTOM edge to the window, and the "
    "black ceiling crosses the TOP edge with the red light flickering on it.")
GEO_VALLEY = (
    "The dark tree tops cross the BOTTOM third from the LEFT edge to the RIGHT edge. The burning "
    "level fields fill the CENTRE with its small tongues of flame, the glowing ruins about the station "
    "stand at the LEFT third, the burning train lies at the CENTRE on the railway, the red-lit "
    "common lies far off at the RIGHT third, and red smoke fills the TOP third.")
GEO_GARDEN = (
    "The dark trampled lawn fills the BOTTOM half, the black paling fence runs across the CENTRE "
    "from the LEFT edge to the RIGHT edge with the faint red glare above it, the broken rose trees "
    "stand at the LEFT third, and the pale corner of the house stands at the RIGHT edge. Dark shrubs "
    "stand beyond the fence at the TOP third, and wet footprints cross the lawn from the fence to "
    "the BOTTOM RIGHT.")
GEO_DINING = (
    "The dark table runs across the BOTTOM half with the decanter and glasses at the CENTRE, the "
    "sideboard stands against the far wall at the TOP third, the chairs stand at the LEFT third "
    "and the RIGHT third, and the curtained window with its thin red glare stands at the LEFT edge. "
    "The dark patterned wallpaper fills the RIGHT edge, and the red light lies in a thin line along "
    "the edge of the table from the LEFT third to the CENTRE.")
GEO_DAWN = (
    "The blackened country fills the BOTTOM half with grey streamers of smoke rising from its "
    "ruins, the pit lies at the CENTRE with three tall tripods standing about it, green vapour "
    "rising between them, the white railway signal stands at the LEFT third, and the pale dawn sky "
    "fills the TOP third with red pillars of smoke at the RIGHT edge. The gutted shells of houses "
    "stand along the BOTTOM third, and the end of a white greenhouse stands at the BOTTOM RIGHT.")

# ---- the cells of every tighter shot: where ITS subject sits (G-SCALE) ---------------
GEO_DOORWAY = (
    "The narrator stands at the CENTRE LEFT in the dark doorway of the study, one hand on the door "
    "frame, the red glare of the open window falling across his face from the RIGHT. The dark "
    "passage fills the LEFT edge. His head is a third of the frame's height.")
GEO_SHAPES = (
    "Three huge black tripods stand far off across the red light at the CENTRE, each a sixth of the "
    "height of the frame, their legs black against the glare. The burning hillside fills the "
    "BOTTOM half with its small flames and red smoke drifts across the TOP third.")
GEO_TRAIN = (
    "The wrecked train lies along the railway at the CENTRE, its fore part a black heap in a vivid "
    "orange glare at the LEFT third and its hinder carriages a row of lit yellow windows at the "
    "RIGHT third. The black embankment crosses the BOTTOM third and red smoke fills the TOP third.")
GEO_FIGURES = (
    "A line of small black figures hurries across the railway at the CENTRE against the red glow "
    "of the station ruins behind them, which fill the TOP half. The dark embankment crosses the "
    "BOTTOM third from the LEFT edge to the RIGHT edge.")
GEO_CHAIR = (
    "The narrator sits at the CENTRE in the desk chair turned to the open window, seen from the "
    "side, his elbows on his knees, the red glare of the window at the RIGHT third lighting his "
    "face and the dark bookshelves behind him at the LEFT third. His head is a fifth of the frame's height.")
GEO_HANDS = (
    "Two hands grip the dark wooden arms of the desk chair at the CENTRE, lit red from the RIGHT "
    "by the window, a grey herringbone tweed cuff at the LEFT third and the dark floor across the "
    "BOTTOM third. The red glare of the open window falls across the RIGHT third, and the dark "
    "legs of the desk stand behind the chair at the TOP third.")
GEO_MARS = (
    "A single small red point of light stands low in the clear dark sky at the CENTRE LEFT. The red "
    "smoke of the burning land crosses the BOTTOM third and the dark clear sky fills the TOP half. "
    "A few faint stars stand at the TOP RIGHT, and the red glow of the fires lights the underside "
    "of the smoke from the BOTTOM edge.")
GEO_FENCE = (
    "The artilleryman sits astride the black paling fence at the CENTRE, seen from above, one leg "
    "over, his open jacket hanging, the dark lawn below him across the BOTTOM half and the faint "
    "red glare above the fence at the TOP third. His head is a sixth of the frame's height.")
GEO_LEAN = (
    "The narrator leans out of the open window at the CENTRE, seen from the lawn below, his head "
    "and shoulders over the sill, the pale wall of the house around him and the dark sky with a "
    "faint red glare at the TOP third. His head is a third of the frame's height.")
GEO_UNDER = (
    "The artilleryman stands at the CENTRE under the window, seen from above, his blackened face "
    "turned up, the dark lawn around him and the broken rose trees at the LEFT third. His head is a "
    "third of the frame's height.")
GEO_POUR = (
    "The narrator stands at the CENTRE RIGHT at the dark table, pouring whisky from the decanter "
    "into a glass at the CENTRE, the red glare through the curtains at the LEFT edge lighting the "
    "glass and his hands. His head is a third of the frame's height.")
GEO_WEEP = (
    "The artilleryman sits at the CENTRE at the dark table with his head down on his folded arms, "
    "his shoulders shaking, a glass beside his elbow at the RIGHT third, the thin red glare from "
    "the curtains at the LEFT edge. His head is a quarter of the frame's height.")
GEO_GUNNER_FACE = (
    "The artilleryman's blackened face fills the CENTRE, lit red from the LEFT by the curtain gap, "
    "his black hair falling over his brow, the dark room behind him. His head is half the frame's height.")
GEO_LISTEN = (
    "The narrator stands at the CENTRE in the dark dining room, his face turned down and to the "
    "LEFT, lit red from the LEFT by the curtain gap, the dark sideboard behind him at the RIGHT "
    "third. His head is a third of the frame's height.")
GEO_BREAD = (
    "A plate of cold mutton and a loaf of bread lie at the CENTRE on the dark table, two hands "
    "reaching into the frame from the LEFT edge and the RIGHT edge, the glasses at the TOP third "
    "catching a thin red light from the LEFT.")
GEO_SILL = (
    "The narrator stands at the CENTRE LEFT at the open study window at dawn, seen from behind "
    "over his shoulder, his hands on the sill, the valley of ashes filling the window at the "
    "CENTRE RIGHT with grey smoke rising from it. His head is a quarter of the frame's height.")
GEO_GUNNER_DAWN = (
    "The artilleryman's streaked face fills the CENTRE, lit pale from the RIGHT by the dawn "
    "through the window, his black hair falling over his brow, the pale window at the RIGHT third. "
    "His head is half the frame's height.")

SETUPS = {
    "study": dict(
        described=STUDY_NIGHT, cast=["unnamed_first_person_narrator"],
        landmark="the open window with the burning valley in it", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the dark doorway across the study to the open window",
        geometry=GEO_STUDY, crowd="",
        outdoors=False, props=[], location="narrators_study", view="interior_window_fire_night"),
    "valley": dict(
        described=VALLEY_NIGHT, cast=[],
        landmark="the burning train on the railway", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the tree tops below the window out over the burning valley to the common",
        geometry=GEO_VALLEY, crowd="a line of small black figures running across the railway",
        outdoors=True, props=["fighting_machine"], location="narrators_study",
        view="window_view_valley_fire_night"),
    "garden": dict(
        described=GARDEN_NIGHT, cast=["unnamed_first_person_narrator", "artilleryman"],
        landmark="the black paling fence at the end of the lawn", landmark_at="far_end",
        landmark_size="is a fifth of the height of the frame",
        route="from the paling fence across the dark lawn to the corner of the house",
        geometry=GEO_GARDEN, crowd="",
        outdoors=True, props=[], location="narrators_garden", view="wide_lawn_palings_night"),
    "dining": dict(
        described=DINING_NIGHT, cast=["unnamed_first_person_narrator", "artilleryman"],
        landmark="the curtained window with its thin red glare", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the door along the dark table to the curtained window",
        geometry=GEO_DINING, crowd="",
        outdoors=False, props=[], location="narrators_home", view="dining_room_unlit_night"),
    "dawn": dict(
        described=DAWN_WINDOW, cast=["unnamed_first_person_narrator", "artilleryman"],
        landmark="the pit with the three tripods about it", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the window sill out over the valley of ashes to the pit",
        geometry=GEO_DAWN, crowd="",
        outdoors=True, props=["fighting_machine"], location="narrators_study",
        view="window_view_ashes_dawn"),
}

#  setup   size   faces  path  move   frame / motion / camera / cells / section / why
S = [
    # ---- study: the window, and the burning valley in it -------------------------------
    ("study", "wide", [], 0.1, "push_in",
     "Wide on the narrator's dark study at night, its tall window standing wide open in the far wall "
     "and a whole valley burning red far below inside the frame of it, the desk and turned chair "
     "black against the glare.",
     "The camera pushes in toward the open window already in the picture with small amplitude, "
     "travelling one short stride; the red glare goes on flickering on the wall; the smoke goes on "
     "drifting across the window.",
     "in the dark doorway at a standing man's eye, a 35mm lens. The red glare comes through the "
     "window AHEAD at the CENTRE; the window reads red and the room reads black",
     GEO_STUDY, "hook", "The passage was dark, and the side of the room seemed impenetrably dark."),

    ("study", "medium_close", ["unnamed_first_person_narrator"], 0.4, "locked",
     "Medium close on " + NARRATOR + " stopped short in the dark doorway of his study at night, one "
     "hand on the door frame, the red glare of the window falling across his face.",
     "The camera holds a locked-off frame; he stares at the window and his breath catches; his "
     "hand goes on gripping the door frame.",
     "in the passage level with his eyes, three paces from him, an 85mm lens. The red glare comes "
     "from the window at the RIGHT; his face reads red and the passage reads black",
     GEO_DOORWAY, "setup", "I stopped short in the doorway."),

    # ---- valley: what the window holds -------------------------------------------------
    ("valley", "wide", [], 0.2, "pan_to",
     "Wide from a hillside window at night over flat country on fire, the level fields set with "
     "small tongues of flame out to a low flat horizon, the station ruins glowing and red smoke "
     "rolling over it all.",
     "The camera pans from the burning fields across to the station ruins already in the "
     "picture until the ruins are at the centre, travelling a hand's breadth; the small flames go "
     "on swaying; the red smoke goes on rolling across the sky.",
     "at the open window at a standing man's eye, a 35mm lens. The red glare comes from the fires "
     "BELOW; the smoke reads red and the country reads black",
     GEO_VALLEY, "setup", "It seemed indeed as if the whole country in that direction was on fire."),

    ("valley", "medium", [], 0.4, "track_lateral",
     "Medium across the red glare at night on three huge black tripods far off on the common, "
     "moving busily to and fro across the light like grotesque shapes.",
     "The camera tracks sideways to the right past the dark tree tops, a truck with small "
     "amplitude, until the three tripods already in the picture stand at the centre, travelling "
     "one short stride; the three tripods go on striding to and fro across the glare; the flames "
     "go on leaping below them.",
     "at the open window looking out over the valley, a 135mm lens. The red glare comes from the "
     "fires BEHIND them; the tripods read black and the glare reads red",
     GEO_SHAPES, "spike", "Across the light huge black shapes, grotesque and strange, moved busily to and fro."),

    ("valley", "insert", [], 0.55, "tilt_up",
     "Insert at night on a wrecked train on the railway below the hill, its fore part a black heap "
     "in a vivid glare and its hinder carriages a row of lit yellow windows.",
     "The camera tilts up from the black embankment to the burning train already in the picture "
     "until the train stands in the middle of the frame, travelling a forearm; the glare goes on "
     "flaring; the red smoke goes on rising.",
     "at the window looking down the hill, a 135mm lens. The glare comes from the burning engine at "
     "the LEFT; the carriages read yellow and the embankment reads black",
     GEO_TRAIN, "spike", "Then I perceived this was a wrecked train, the fore part smashed and on fire."),

    ("valley", "wide", [], 0.7, "crane_up",
     "Wide at night over the railway below the hill, where a line of small black figures hurries "
     "one after another across the line against the red glow of the station ruins.",
     "The camera rises above the embankment with small amplitude until the line of black figures "
     "already in the picture stands at the centre, travelling one short stride; the figures go on "
     "hurrying across the line; the station ruins go on glowing.",
     "at the window looking down over the railway, a 85mm lens. The red glow comes from the station "
     "ruins BEHIND the figures; the figures read black and the glow reads red",
     GEO_FIGURES, "friction", "I saw against the light of Woking station a number of black figures hurrying across the line."),

    # ---- study: the chair, and the question ---------------------------------------------
    ("study", "medium", ["unnamed_first_person_narrator"], 0.6, "push_in",
     "Medium on " + NARRATOR + " sitting in his desk chair turned to the open window at night, "
     "staring out at the blackened country, his elbows on his knees.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; he goes on staring out at the valley; "
     "his head goes on turning after the far shapes.",
     "in the study level with his chest, four paces from him, a 50mm lens. The red glare comes from "
     "the window at the RIGHT; his face reads red and the shelves read black",
     GEO_CHAIR, "friction", "I turned my desk chair to the window, sat down, and stared at the blackened country."),

    ("study", "insert", [], 0.75, "push_in",
     "Insert at night on a man's two hands gripping the wooden arms of a desk chair, lit red by "
     "the window, the knuckles pale.",
     "The camera pushes in on the hands at the centre of the picture, travelling a hand's breadth; "
     "the fingers go on tightening on the chair arms; the red light goes on flickering over them.",
     "beside the chair looking down, a 50mm lens. The red glare comes from the window at the "
     "RIGHT; the knuckles read pale and the wood reads black",
     GEO_HANDS, "friction", "Did a Martian sit within each, ruling, directing, using?"),

    ("valley", "insert", [], 0.9, "tilt_up",
     "Insert at night on the little red pinpoint of Mars dropping into the west, low in a clear dark "
     "sky over the smoke of the burning land.",
     "The camera tilts up from the red smoke to the red point of Mars already in the picture "
     "until the point stands in the middle of the frame, travelling a forearm; the red smoke goes "
     "on rolling up below it; the flames go on flickering along the bottom of the smoke.",
     "at the window looking up into the west, a 135mm lens. The only light is the red glow of the "
     "fires from BELOW; the sky reads black and the point reads red",
     GEO_MARS, "reaction", "Over the smoke the little fading pinpoint of Mars was dropping into the west."),

    # ---- garden: a soldier in the garden ------------------------------------------------
    ("garden", "medium", ["artilleryman"], 0.2, "high_angle",
     "Medium seen from an upstairs window at night on " + GUNNER + " clambering over the black "
     "paling fence into the dark garden, one leg over the top.",
     "The camera tilts down from the faint red glare to the fence already in the picture until the "
     "fence stands in the middle of the frame, travelling a hand's breadth; he goes on swinging "
     "his leg over the palings; his open jacket goes on flapping.",
     "a high angle from the upstairs window looking down on the lawn, a 50mm lens. The faint red "
     "glare comes from BEHIND the fence; the palings read black and the lawn reads dark grey",
     GEO_FENCE, "friction", "A soldier came into my garden, clambering over the palings."),

    ("garden", "medium_close", ["unnamed_first_person_narrator"], 0.4, "low_angle",
     "Medium close seen from the lawn at night on " + NARRATOR + " leaning out of the open window "
     "above, eager, whispering down into the dark.",
     "The camera holds a locked-off frame from below; he leans out over the sill and whispers; his "
     "hand goes on gripping the window frame.",
     "a low angle from the lawn looking up at the window, three paces from the wall, an 85mm lens. "
     "The faint red glare comes from BEHIND the camera; his face reads pale and the wall reads grey",
     GEO_LEAN, "friction", "At the sight of another human being my torpor passed, and I leaned out."),

    ("garden", "medium_close", ["artilleryman"], 0.55, "push_in",
     "Medium close seen from the window above at night on " + GUNNER + " standing under the window, "
     "his blackened face turned up, peering and whispering.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; he whispers up at the window; his head goes "
     "on turning along the dark wall.",
     "above him looking down from the window, three paces up, an 85mm lens. The faint red glare "
     "comes from BEHIND him at the TOP; his face reads grey and the lawn reads black",
     GEO_UNDER, "friction", "'Who's there?' he said, also whispering, standing under the window and peering up."),

    ("garden", "medium_close", ["unnamed_first_person_narrator"], 0.7, "push_in",
     "Medium close seen from the lawn at night on " + NARRATOR + " at the open window above, "
     "whispering down, his hands on the sill.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; he asks his question in a whisper; his "
     "hand goes on gripping the sill.",
     "a low angle from the lawn looking up, three paces from the wall, an 85mm lens. The faint red "
     "glare comes from BEHIND the camera; his face reads pale and the wall reads grey",
     GEO_LEAN, "friction", "'Where are you going?' I asked. 'Are you trying to hide?'"),

    ("garden", "close", ["artilleryman"], 0.85, "locked",
     "Close seen from above at night on the blackened face of " + GUNNER + " under the window, "
     "turned up, exhausted, whispering his answer.",
     "The camera holds a locked-off frame; he whispers and nods; his head goes on turning to the "
     "fence behind him.",
     "above him looking down from the window, two paces up, an 85mm lens. The faint red glare "
     "comes from BEHIND him at the TOP; his face reads grey and his hair reads black",
     GEO_UNDER, "friction", "'God knows.' ... 'That's it.'"),

    ("garden", "close", ["unnamed_first_person_narrator"], 0.95, "push_in",
     "Close seen from the lawn at night on the face of " + NARRATOR + " at the open window, "
     "deciding, then beckoning him in.",
     "The camera pushes in toward his face with small amplitude until it fills the middle of the "
     "picture, travelling a hand's breadth; he whispers and beckons; his hand goes on waving "
     "toward the door below.",
     "a low angle from the lawn looking up, two paces from the wall, an 85mm lens. The faint red "
     "glare comes from BEHIND the camera; his face reads pale and the window reads black",
     GEO_LEAN, "turn", "'Come into the house,' I said."),

    # ---- dining: whisky, and the story in the dark --------------------------------------
    ("dining", "medium_close", ["unnamed_first_person_narrator"], 0.3, "push_in",
     "Medium close in the dark dining room at night on " + NARRATOR + " pouring a stiff dose of "
     "whisky from the decanter into a glass, lit only by a thin red glare from the curtains.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; he speaks as he goes on pouring the "
     "whisky; the red glare goes on glinting in the glass.",
     "at the table level with his eyes, three paces from him, an 85mm lens. The thin red glare comes "
     "through the curtains from the LEFT; his face reads red and the room reads black",
     GEO_POUR, "reaction", "'Take some whisky,' I said, pouring out a stiff dose."),

    ("dining", "medium", ["artilleryman"], 0.5, "crane_up",
     "Medium in the dark dining room at night on " + GUNNER + " sitting at the table with his head "
     "down on his folded arms, his shoulders shaking, a glass beside his elbow.",
     "The camera rises above the table with small amplitude until the artilleryman already in the "
     "picture sits at the centre, travelling a hand's breadth; he goes on sobbing into his arms; his "
     "shoulders go on shaking.",
     "at the table level with his head, four paces from him, a 50mm lens. The thin red glare comes "
     "through the curtains from the LEFT; his jacket reads dark blue and the room reads black",
     GEO_WEEP, "reaction", "He put his head on his arms, and began to sob and weep like a little boy."),

    ("dining", "close", ["artilleryman"], 0.7, "push_in",
     "Close in the dark dining room at night on the blackened, haggard face of " + GUNNER + ", "
     "lifted from his arms, his eyes wet, telling it.",
     "The camera pushes in toward his face with small amplitude until it fills the middle of the "
     "picture, travelling a hand's breadth; he speaks; his head goes on shaking from side "
     "to side.",
     "at the table level with his eyes, two paces from him, an 85mm lens. The thin red glare comes "
     "from the curtain gap at the LEFT; his face reads black and red and the room reads black",
     GEO_GUNNER_FACE, "answer", "'They wiped us out -- simply wiped us out,' he repeated again and again."),

    ("dining", "medium_close", ["unnamed_first_person_narrator"], 0.8, "push_in",
     "Medium close in the dark dining room at night on " + NARRATOR + " standing and listening, his "
     "face turned down toward the table, lit red from one side.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling a hand's breadth; he goes on listening; his hand goes on "
     "gripping the back of a chair.",
     "in the dining room level with his eyes, three paces from him, an 85mm lens. The thin red "
     "glare comes from the curtain gap at the LEFT; his face reads red and the sideboard reads black",
     GEO_LISTEN, "reaction", "He was a driver in the artillery, and had only come into action about seven."),

    ("dining", "insert", [], 0.9, "push_in",
     "Insert at night on a plate of cold mutton and a loaf of bread on the dark table, two hands "
     "reaching in from either side and touching over it in the dark.",
     "The camera pushes in on the bread at the centre of the picture, travelling a hand's breadth; "
     "the two hands go on tearing at the bread; the red glint goes on shining in the glasses.",
     "above the table looking down, a 50mm lens. The thin red glare comes from the LEFT; the bread "
     "reads pale and the table reads black",
     GEO_BREAD, "reaction", "We lit no lamp, and ever and again our hands would touch upon bread or meat."),

    # ---- dawn: the valley of ashes ---------------------------------------------------------
    ("dawn", "medium", ["unnamed_first_person_narrator"], 0.3, "push_in",
     "Medium over the shoulder of " + NARRATOR + " at the open study window at dawn, seen from "
     "behind with his hands on the sill, the valley of ashes beyond him smoking grey.",
     "The camera pushes in past his shoulder toward the valley already in the picture with small "
     "amplitude, travelling one short stride; the grey smoke goes on rising from the ruins; he "
     "goes on gripping the sill.",
     "behind him in the study at a standing man's eye, three paces from him, a 35mm lens. The grey "
     "dawn comes from AHEAD at the RIGHT; the smoke reads grey and his back reads dark",
     GEO_SILL, "runout", "In one night the valley had become a valley of ashes."),

    ("dawn", "close", ["artilleryman"], 0.6, "locked",
     "Close at dawn on the streaked face of " + GUNNER + " turned from the study window toward the "
     "camera, looking straight ahead, the valley of ashes over his shoulder, dawn light on his face.",
     "The camera holds a locked-off frame; he speaks quietly, facing the camera; his head goes on "
     "lowering toward his chest.",
     "in the study level with his eyes, two paces from him, an 85mm lens. The grey dawn comes from "
     "the window at the RIGHT onto his face; his skin reads pale through streaks of soot and his hair reads black",
     GEO_GUNNER_DAWN, "button", "'Just like parade it had been a minute before -- then stumble, bang, swish!'"),

    ("dawn", "wide", [], 0.9, "crane_up",
     "Wide at dawn over the valley of ashes to the pit, where three tall tripods stand about it with "
     "their hooded heads turning and puffs of green vapour rise out of it into the grey sky.",
     "The camera rises above the ruins with small amplitude until the three tripods already in the "
     "picture stand at the centre, travelling one short stride; their hooded heads go on turning; "
     "the green vapour goes on rising from the pit.",
     "at the window at a standing man's eye, a 50mm lens. The grey dawn comes from the RIGHT; the "
     "smoke reads grey, the tripods read metal and the country reads black",
     GEO_DAWN, "runout", "Three of the metallic giants stood about the pit, their cowls rotating."),
]

MOVES = {i: s[4] for i, s in enumerate(S)}

BEATS = {10: (1.5, 1.5), 11: (1.5, 1.5), 13: (1.5, 1.5), 20: (1.0, 1.4), 21: (1.0, 1.0), 22: (1.5, 1.5)}
"""Everything else takes the default (0.8, 0.9). The shot before the button
holds a beat of 1.0 s or more (the contract); the silent last shot takes the
longest coda the 6.0 s silence wall allows."""

TURNS = {14: "a man watching his world burn -> a man taking a stranger in"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "Then, why I do not know, I went up to my study.", 0),
    ("dialogue", "unnamed_first_person_narrator", "It is all on fire.", 1),
    ("narration", "unnamed_first_person_narrator",
     "The storm had passed. The whole country toward the common was on fire.", 2),
    ("narration", "unnamed_first_person_narrator",
     "Across the red light, huge black shapes, grotesque and strange, went busily to and fro.", 3),
    ("narration", "unnamed_first_person_narrator",
     "A glare on the railway. A wrecked train, its fore part burning.", 4),
    ("narration", "unnamed_first_person_narrator",
     "Later, against the light of the station, black figures hurried across the line.", 5),
    ("narration", "unnamed_first_person_narrator",
     "I turned my chair to the window, and sat, and stared at the blackened country.", 6),
    ("narration", "unnamed_first_person_narrator",
     "Did a Martian sit within each, ruling it as a brain rules a body?", 7),
    ("narration", "unnamed_first_person_narrator",
     "Over the smoke, the small red point of Mars was sinking west.", 8),
    ("narration", "unnamed_first_person_narrator",
     "Then, near dawn, a soldier came clambering into my garden, over the palings.", 9),
    ("dialogue", "unnamed_first_person_narrator", "You there, in the garden! Up here!", 10),
    ("dialogue", "artilleryman", "Who is that? Who is there?", 11),
    ("dialogue", "unnamed_first_person_narrator", "Are you trying to hide?", 12),
    ("dialogue", "artilleryman", "God knows. That is it.", 13),
    ("dialogue", "unnamed_first_person_narrator", "Come into the house.", 14),
    ("narration", "unnamed_first_person_narrator", "I poured him out a stiff dose of whisky, and he drank it down.", 15),
    ("narration", "unnamed_first_person_narrator",
     "He sat down, put his head on his arms, and wept like a little boy.", 16),
    ("dialogue", "artilleryman", "They wiped us out. Simply wiped us out.", 17),
    ("narration", "unnamed_first_person_narrator",
     "He was a driver in the artillery. Nothing living was left upon the common.", 18),
    ("narration", "unnamed_first_person_narrator",
     "We lit no lamp. Our hands would touch upon bread, or meat.", 19),
    ("narration", "unnamed_first_person_narrator",
     "At dawn we went up again. The valley was a valley of ashes.", 20),
    ("dialogue", "artilleryman", "Just like parade, a minute before.", 21),
]

BEDS = [{"from_shot": 0, "tone": "grave"}, {"from_shot": 9, "tone": "uneasy"},
        {"from_shot": 15, "tone": "grave"}]

EXTRAS = {}

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
    return dict(number=11, title="At the Window",
                question="What happened in the last seven hours?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 17",
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
