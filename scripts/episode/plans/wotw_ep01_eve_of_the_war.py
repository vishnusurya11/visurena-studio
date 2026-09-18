r"""The War of the Worlds, episode 1 -- "The Eve of the War", chapter 1.

THE BRICK. One event: the night of the vigil at Ottershaw, when the narrator
sees the second flame leave Mars and the man beside him explains it away.

  QUESTION  Today, can the narrator see what Mars is sending?
  TURN      shot 11, the narrator's own act on his own face: he sees the red flash
            at the planet's edge and calls Ogilvy to the eyepiece.
            "a quiet vigil -> the first sign seen".
  ANSWER    line 13, Ogilvy: "The chances against anything manlike on Mars are a
            million to one."  The world's answer is no.
  BUTTON    shot 22, the wife's line and the last one, not the lead's: the signal
            lights red, green and yellow over the railway, so safe and tranquil.
            One silent shot after it: the lights themselves from the study window.

REFERENCES-ONLY (owner 2026-09-18).  No storyboard and no composed first frame.
Each take is handed its location VIEW (chosen to match the shot size, named
per shot in `view`) and the one sheet of each person in it, from the book's
reference pack; everything else is in the words.  The wardrobe of chapter 1 is
said in every frame text and in each subject's definition.
"""
import json
from pathlib import Path

OUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio"
           r"\library\20260827135508_the-war-of-the-worlds\episodes\ep01\plan.json")

WHERE = "Surrey, 1894"
LIGHT = "low lantern light, deep black shadow"
LOOK = "Angular stylised 3D animation, painterly brush-stroke texture, cinematic"

NARR = "the Narrator in the grey herringbone tweed suit and straw boater"
OGIL = "Ogilvy in the ochre tweed Inverness cape, black velvet smoking cap and steel spectacles"
WIFE = "the Wife in the cream high-collared blouse, sage-green skirt and paisley shawl"

SETUPS = {
    "space": dict(
        described=("The gulf of space between Mars and the Earth in 1894: the ochre-red planet Mars with a white "
                   "polar cap and dark blue-green markings, and far across the black a small blue-white Earth; "
                   "the far sun is the only light and it comes from the right, hard and white, on the planet's "
                   "limb, and leaves the night side of each planet and the whole of space black"),
        cast=[], landmark="the ochre-red planet Mars", landmark_at="start",
        landmark_size="is half the height of the frame",
        route="from the red planet across the black gulf to the small blue Earth",
        geometry=("Mars stands at the LEFT third of the frame, half the frame's height, its lit limb on the RIGHT "
                  "side and its night side black. The small blue Earth hangs at the RIGHT third across the "
                  "black, the height of a thumbnail. Fine stars fill the TOP and the BOTTOM edges, and the "
                  "far sun is off the RIGHT edge of the frame, its hard white light raking across both planets."),
        crowd="", outdoors=True, props=[], location="earth_and_mars"),
    "knoll": dict(
        described=("The garden knoll at Ottershaw on a warm starlit night in 1894: a small round observatory of "
                   "white weatherboard on a red-brick plinth under a green copper dome with its slit open, a "
                   "plank door with iron strap hinges, three brick steps, a gravel path, and below the knoll a "
                   "red-brick house with lit windows and the scattered lamps of Ottershaw; a brass lantern is "
                   "the only near light and it comes from low on one side, warm and yellow, on the steps and "
                   "the gravel, and leaves the dome, the fields and the sky black"),
        cast=["ogilvy", "unnamed_first_person_narrator"], landmark="the white observatory door",
        landmark_at="start", landmark_size="is half the height of the frame",
        route="from the observatory door down the gravel path toward the lit house",
        geometry=("The white observatory wall and its plank door hold the LEFT half of the frame. The brass "
                  "lantern glows at the BOTTOM LEFT on the brick steps, its yellow pool on the gravel. The "
                  "green copper dome with its open slit crosses the TOP LEFT corner. The starry sky is black "
                  "across the TOP edge, the lit red-brick house sits below the knoll at the CENTRE, and the "
                  "village lamps are small at the RIGHT third."),
        crowd="", outdoors=True, props=[], location="ottershaw"),
    "pier": dict(
        described=("Interior, inside the small round private observatory at Ottershaw at midnight in 1894, the "
                   "camera within the room with its curved pine walls closed on all sides: a long brass "
                   "refractor telescope on a black cast-iron pier pointing up through the narrow open slit in "
                   "the black timber dome, a strip of stars in the slit, a mahogany clockwork box on the pier, "
                   "a little deal table with a soda siphon, tumblers and a brass chronometer in its box; a "
                   "shaded lantern on the floor in the corner is the only light and it comes from low at the "
                   "right, a small yellow oval on the pine boards, and leaves the dome, the walls and the "
                   "corners black"),
        cast=["unnamed_first_person_narrator", "ogilvy"], landmark="the brass telescope under the slit",
        landmark_at="far_end", landmark_size="is half the height of the frame",
        route="from the door across the pine boards to the telescope under the slit",
        geometry=("The brass telescope rises from its black pier across the CENTRE of the frame toward the "
                  "starry slit at the TOP RIGHT, the mahogany clockwork box on the pier at the CENTRE. The "
                  "lantern's yellow oval lies on the pine boards at the BOTTOM RIGHT. The star atlases on their "
                  "shelf are dim at the LEFT third, and the curved walls and the black timber dome are black at "
                  "the LEFT edge and across the TOP."),
        crowd="", outdoors=False, props=[], location="ottershaw_observatory"),
    "corner": dict(
        described=("Interior, inside the small round private observatory at Ottershaw at midnight in 1894, the "
                   "camera within the room with its curved pine walls closed on all sides: a long brass "
                   "refractor telescope on a black cast-iron pier pointing up through the narrow open slit in "
                   "the black timber dome, a strip of stars in the slit, a mahogany clockwork box on the pier, "
                   "a little deal table with a soda siphon, tumblers and a brass chronometer in its box; a "
                   "shaded lantern on the floor in the corner is the only light and it comes from low at the "
                   "right, a small yellow oval on the pine boards, and leaves the dome, the walls and the "
                   "corners black"),
        cast=["unnamed_first_person_narrator", "ogilvy"], landmark="the shaded lantern in the corner",
        landmark_at="far_end", landmark_size="is the height of a hand",
        route="from the telescope pier across the boards to the lantern and the little table",
        geometry=("The brass eyepiece and the black pier hold the LEFT third of the frame. The shaded lantern "
                  "glows on the boards at the BOTTOM CENTRE beside the little deal table, which carries the "
                  "soda siphon, two tumblers and the brass chronometer in its open box at the CENTRE. The "
                  "curved pine wall and the plank door with its iron hinges are black at the RIGHT edge, and "
                  "the dome is black across the TOP."),
        crowd="", outdoors=False, props=[], location="ottershaw_observatory"),
    "study": dict(
        described=("Interior, inside the narrator's upstairs study at Maybury at night in 1894, the camera within "
                   "the room with walls closed on all sides: a mahogany writing-table with a green leather top "
                   "and stacked manuscript sheets, a brass inkstand, a green-shaded brass oil lamp, a pair of "
                   "glazed French windows with a low iron rail and a raised cream blind, oak bookcases and a "
                   "globe; the green-shaded lamp is the only light and it comes from low at the right onto the "
                   "table and the pages, and leaves the bookcases, the corners and the night in the windows "
                   "black"),
        cast=["unnamed_first_person_narrator"], landmark="the green-shaded lamp on the writing-table",
        landmark_at="start", landmark_size="is a quarter of the height of the frame",
        route="from the writing-table to the open French windows over the valley",
        geometry=("The writing-table crosses the BOTTOM half of the frame with the green lamp at the RIGHT "
                  "third and the stacked manuscript pages at the CENTRE. The French window and its cream "
                  "curtain stand at the LEFT edge with the night black in the glass and the dark beech tops "
                  "beyond. The oak bookcases are black across the TOP and the terrestrial globe is dim in the "
                  "RIGHT corner."),
        crowd="", outdoors=False, props=[], location="narrators_study"),
    "porch": dict(
        described=("The front of the narrator's red-brick villa at Maybury on a warm starlit night in 1894: a "
                   "black four-panel door with a brass knocker under a small tiled porch on two turned posts, "
                   "a fanlight glowing, a lit bay window at the left, clipped laurels, a gravel path; the "
                   "lamplit fanlight is the only light and it comes from the door behind the couple, warm and "
                   "low, onto the red-and-black tiled step and the gravel, and leaves the laurels, the brick "
                   "and the sky black"),
        cast=["unnamed_first_person_narrator", "narrators_wife"], landmark="the lit fanlight over the door",
        landmark_at="far_end", landmark_size="is the height of a hand",
        route="from the gravel path to the black front door under the porch",
        geometry=("The black front door and its lit fanlight stand at the CENTRE of the upper half of the "
                  "frame under the small tiled porch on its two turned posts. The lit bay window glows at "
                  "the LEFT edge behind its lace. The gravel path fills the BOTTOM edge up to the red-and-black "
                  "tiled step, the clipped laurels are black at the RIGHT, and the starry sky is black above "
                  "the slate roof across the TOP."),
        crowd="", outdoors=True, props=[], location="narrators_home"),
}

# (setup, size, faces, view, path, frame, motion, camera, at_rest, section, why)
S = [
    # 0 HOOK -- the gulf of space
    ("space", "wide", [], "wide_space", 0.1,
     "Wide of the gulf of space: the ochre-red planet Mars with its white polar cap at the left, lit hard "
     "from the right, and far across the black the small blue-white Earth with its drifting cloud.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the red planet keeps the left "
     "third; the red planet turns a finger's breadth on its axis toward the far sun.",
     "far off the plane of the orbits, a 35mm lens. The sun comes from the RIGHT onto the planet's limb and "
     "leaves its night side and all of space black",
     "The red planet Mars fills the LEFT third of the frame, half the frame's height, its lit limb on the "
     "RIGHT side and its night side black. The small blue Earth hangs at the RIGHT third, the height of a "
     "thumbnail. Fine stars scatter across the TOP and the BOTTOM edges and the rest of space is black.",
     "hook", "Opens on the watchers' own view: the world as the Martians see it."),
    # 1 -- the gun pit on Mars
    ("space", "wide", [], "wide_mars_gun_pit", 0.4,
     "Wide of the rust-red desert plain of Mars under a thin salmon sky: the terraced rim of a vast round "
     "pit, and from its centre a colossal dark gun barrel slanting up toward the low small sun.",
     "The camera pans left across the whole shot, travelling a hand's breadth; the gun barrel keeps the "
     "centre of the frame; a jet of green-white gas rises from its mouth and travels up the salmon sky.",
     "on the rim of the pit at a standing man's eye, a 35mm lens. The low sun comes from the RIGHT across the "
     "plain and throws the pit's terraces into black shadow",
     "The terraced rim of the round pit crosses the BOTTOM third of the frame. The dark gun barrel rises from "
     "the CENTRE of the pit to the TOP RIGHT third, slanting toward the small sun at the RIGHT edge. The "
     "salmon sky fills the TOP half and the terraces lie black in their own shadow.",
     "setup", "Where the Thing comes from: a made thing, a gun, before anyone on Earth knows it."),
    # 2 -- the flash at the limb
    ("space", "insert", [], "insert_mars_limb_jet", 0.8,
     "Insert on the bright curved limb of Mars against black space: a reddish flash at its edge and a thin "
     "streamer of green-white flaming gas projecting out into the dark.",
     "The camera pushes in on the reddish flash across the whole shot, travelling a finger's breadth; the "
     "curved limb keeps the bottom half; the streamer of flaming gas travels out a finger's breadth into "
     "the black.",
     "in space close over the planet, a 50mm lens. The sun comes from the RIGHT along the limb and leaves "
     "the space above it black",
     "The curved bright limb of Mars crosses the BOTTOM half of the frame from the LEFT edge to the RIGHT "
     "edge. The reddish flash sits at the CENTRE of the limb and the green-white streamer rises from it to "
     "the TOP third. Space is black across the TOP edge with fine stars.",
     "setup", "The shot itself: what Lavelle of Java saw, before the narrator hears of it."),
    # 3 -- the little affairs of men
    ("study", "medium_close", ["unnamed_first_person_narrator"], "medium_writing_table", 0.2,
     f"Medium close of {NARR}, the boater set on the table, leaning back from the writing-table under the "
     "green-shaded lamp with the steel pen in his hand, the long oval face lit from the right, a faint smile.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the green lamp keeps the "
     "right third; he sets the pen down on the page and his head lifts from it.",
     "across the writing-table level with his eyes, an arm's length from him, a 50mm lens. The lamp comes "
     "from LOW at the RIGHT onto his face and leaves the bookcases behind him black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his dark parted hair at the TOP "
     "third to the grey tweed at the BOTTOM edge, his head a third of the frame's height, lit from the "
     "RIGHT. The green lamp glows at the RIGHT third and the bookcases are black at the LEFT edge.",
     "setup", "The lead is one of the complacent men of the first paragraph, and says so."),
    # 4 -- up the steps to the observatory
    ("knoll", "medium", ["unnamed_first_person_narrator"], "medium_observatory_door", 0.1,
     f"Medium of {NARR} at the foot of the three brick steps of the white observatory at night, one boot on "
     "the first step, the plank door ajar on the dark above him and the brass lantern glowing on the top step.",
     "The camera pans right across the whole shot, travelling a forearm; the plank door keeps the centre; the "
     "Narrator climbs the brick steps toward the door at a normal walking pace and his hand lifts to the "
     "door's edge.",
     "on the gravel path at a standing man's eye, three long strides from him, a 35mm lens. The lantern comes "
     "from LOW at the LEFT onto his boots and knees and leaves the dome and the sky black",
     "The white weatherboard wall of the observatory fills the CENTRE of the frame with the plank door ajar "
     "above the brick steps. The Narrator stands at the RIGHT third, his head a quarter of the frame's "
     "height. The lantern glows on the top step at the BOTTOM LEFT and the sky is black at the TOP edge.",
     "setup", "How he came to be there at all: chance, and a friend's excitement."),
    # 3 -- Ogilvy at the door, first dialogue
    ("knoll", "medium_close", ["ogilvy"], "medium_observatory_door", 0.3,
     f"Medium close of {OGIL} standing at the plank door of the white observatory on the knoll at night, "
     "the broad ruddy face and full auburn beard lit from below by the brass lantern on the step, one hand "
     "raised toward the dome.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the plank door keeps the "
     "left edge; his raised hand lifts toward the open slit in the dome; his head turns up after it.",
     "on the gravel path at the foot of the steps level with his eyes, two long strides from him, a 50mm "
     "lens. The lantern comes from LOW at the LEFT onto his face and leaves the dome and the sky black",
     "Ogilvy's head and shoulders fill the CENTRE of the frame from the TOP third to the ochre cape at the "
     "BOTTOM edge, his head a third of the frame's height, lit from LOW at the LEFT. The white plank door "
     "stands at the LEFT edge and the starry sky is black at the TOP RIGHT.",
     "setup", "The invitation: a man delighted by a puzzle, which is how the danger arrives."),
    # 4 -- the observatory, wide
    ("pier", "wide", [], "wide_establishing", 0.2,
     f"Wide of the dark round observatory at midnight: the long brass telescope on its black iron pier "
     f"pointing up through the open slit full of stars, {NARR} bending to its eyepiece, the lantern's "
     "yellow oval on the boards in the right-hand corner.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the brass telescope keeps "
     "the centre; the Narrator bends to the eyepiece and his hand turns the brass focusing wheel.",
     "just inside the door at a standing man's eye, four long strides from the pier, a 35mm lens. The "
     "lantern comes from LOW at the RIGHT onto the boards and leaves the dome and the walls black",
     "The brass telescope rises from its black pier across the CENTRE of the frame to the starry slit at "
     "the TOP RIGHT. The Narrator stands at the eyepiece at the LEFT third, his head a fifth of the frame's "
     "height. The lantern's yellow oval lies at the BOTTOM RIGHT and the dome is black across the TOP.",
     "setup", "The place of the vigil, remembered in its detail: the black, the lantern, the clockwork."),
    # 5 -- the eyepiece field
    ("pier", "insert", [], "insert_eyepiece_field", 0.4,
     "Insert through the telescope eyepiece: a perfect circle of deep blue inside a black surround, and at "
     "its centre the small bright round planet, faintly striped, three faint stars near it.",
     "The camera pushes in on the little planet across the whole shot, travelling a finger's breadth; the "
     "circle of blue keeps the frame; the little planet travels a finger's breadth across the blue with the "
     "clockwork drive.",
     "at the eyepiece, the lens to the glass, a 90mm lens. The blue field comes from the CENTRE and leaves "
     "the surround black",
     "The circle of deep blue fills the CENTRE of the frame from the TOP third to the BOTTOM third. The "
     "small bright planet sits at the CENTRE, the height of a fingernail, with three faint stars at the "
     "RIGHT. The surround is black at the LEFT edge, the RIGHT edge and every corner.",
     "setup", "What the man sees: a little thing, bright and small, which is the whole irony."),
    # 6 -- the narrator at the eyepiece
    ("corner", "medium_close", ["unnamed_first_person_narrator"], "reverse", 0.2,
     f"Medium close of {NARR} with one eye to the brass eyepiece of the telescope, the long oval face and "
     "neat dark moustache lit from below by the lantern, the other eye narrowed.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the brass eyepiece keeps "
     "the left third; his hand lifts to the focusing wheel; his shoulders lower toward the glass.",
     "beside the pier level with his eyes, an arm's length from him, a 50mm lens. The lantern comes from "
     "LOW at the RIGHT onto his cheek and leaves the dome behind him black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from the straw boater at the TOP third "
     "to the grey tweed at the BOTTOM edge, his head a third of the frame's height. The brass eyepiece "
     "comes in from the LEFT edge and the dome is black at the TOP RIGHT.",
     "setup", "The lead's own face before the turn: patient, curious, safe."),
    # 9 -- the chronometer toward midnight
    ("corner", "insert", [], "medium_little_table", 0.3,
     "Insert on the brass chronometer with its white enamel dial in its open mahogany box on the little deal "
     "table, the glass soda siphon behind it, the lantern's low yellow glow across the dial and the boards.",
     "The camera pushes in on the white dial across the whole shot, travelling a finger's breadth; the "
     "mahogany box keeps the frame's centre; Ogilvy's ink-stained hand reaches in from the left and lifts the "
     "brass lid of the box.",
     "low over the table at a seated man's eye, an arm's length from the box, a 90mm lens. The lantern comes "
     "from LOW at the LEFT onto the dial and leaves the curved wall behind black",
     "The open mahogany box sits at the CENTRE of the frame with the white dial the height of the middle "
     "third, its hands near twelve. The glass siphon stands at the RIGHT third behind it, the lantern glow "
     "lies along the BOTTOM edge and the curved wall is black across the TOP.",
     "setup", "The clock running toward the second shot: the audience knows what midnight brings."),
    # 8 -- the reddish flash, silent
    ("pier", "insert", [], "insert_eyepiece_field", 0.7,
     "Insert through the telescope eyepiece: the circle of deep blue with the small bright planet at its "
     "centre, a reddish flash blooming at the planet's edge and a hair-thin projection of its outline.",
     "The camera pushes in on the planet's edge across the whole shot, travelling a finger's breadth; the "
     "circle of blue keeps the frame; the reddish flash swells at the edge and a thin streamer travels out "
     "from it.",
     "at the eyepiece, the lens to the glass, a 90mm lens. The flash comes from the planet's RIGHT edge and "
     "leaves the surround black",
     "The circle of deep blue fills the CENTRE of the frame from the TOP third to the BOTTOM third. The small "
     "planet sits at the CENTRE, the height of a fingernail, the reddish flash at its RIGHT edge. The "
     "surround is black at the LEFT edge, the RIGHT edge and every corner.",
     "spike", "The picture speaks: the second shot fired, seen by one man, silent."),
    # 8 TURN -- he calls Ogilvy
    ("corner", "medium_close", ["unnamed_first_person_narrator"], "reverse", 0.4,
     f"Medium close of {NARR} lifting his face from the brass eyepiece and turning it toward the dark, the "
     "grey eyes wide, the lantern low at the right on his cheek.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the brass eyepiece keeps "
     "the left edge; his head turns off the eyepiece toward the dark; his hand lifts and points back at the "
     "glass.",
     "beside the pier level with his eyes, an arm's length from him, a 50mm lens. The lantern comes from "
     "LOW at the RIGHT onto his face and leaves the dome behind him black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from the straw boater at the TOP third "
     "to the grey tweed at the BOTTOM edge, his head a third of the frame's height, his face turned toward "
     "the RIGHT. The brass eyepiece comes in from the LEFT edge and the dome is black behind him.",
     "turn", "The turn is his own act: he sees it and says so. Nobody else on Earth is looking."),
    # 9 -- Ogilvy takes his place
    ("corner", "medium", ["ogilvy"], "reverse", 0.6,
     f"Medium of {OGIL} bending to the brass eyepiece of the telescope beside its black iron pier, one hand "
     "on the brass tube, the lantern on the boards behind him in the corner.",
     "The camera pans right across the whole shot, travelling a forearm; the black iron pier keeps the "
     "left third; Ogilvy bends to the eyepiece and his hand turns the brass wheel on the tube.",
     "beside the table at a standing man's eye, three long strides from him, a 35mm lens. The lantern comes "
     "from LOW at the RIGHT onto his cape and leaves the dome and the walls black",
     "Ogilvy stands at the CENTRE of the frame from the BOTTOM edge to the TOP third, his head a quarter of "
     "the frame's height, bent to the eyepiece. The black iron pier stands at the LEFT third, the lantern "
     "glows at the BOTTOM RIGHT and the curved wall is black at the RIGHT edge.",
     "reaction", "The expert takes over and is thrilled: the danger handed to a man who will explain it."),
    # 10 -- the little table in the dark
    ("corner", "medium", ["unnamed_first_person_narrator"], "medium_little_table", 0.9,
     f"Medium of {NARR} at the little deal table in the dark corner, his hand reaching for the glass soda "
     "siphon beside the tumblers and the brass chronometer in its open box, the lantern low on the floor "
     "beside the table leg.",
     "The camera pans left across the whole shot, travelling a forearm; the brass chronometer keeps the "
     "right third; his hand reaches to the siphon and he pours into a tumbler.",
     "low beside the table at a seated man's eye, three long strides from him, a 35mm lens. The lantern "
     "comes from LOW at the BOTTOM LEFT onto the table and leaves the curved wall behind black",
     "The little deal table stands at the CENTRE of the lower half of the frame with the siphon, the tumblers "
     "and the chronometer on it. The Narrator leans in from the LEFT third, his head a quarter of the "
     "frame's height. The lantern glows at the BOTTOM LEFT and the curved wall is black across the TOP.",
     "friction", "The lead turns his back on the thing he has just seen: thirst, a smoke. Ordinary life."),
    # 11 -- the second missile
    ("space", "wide", [], "wide_space", 0.9,
     "Wide of the black gulf of space between the ochre-red planet Mars at the left and the small blue Earth "
     "at the right, a small glowing grey cylinder crossing the black between them toward the Earth.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the small Earth keeps the "
     "right third; the glowing grey cylinder travels across the black toward the Earth.",
     "far off the plane of the orbits, a 35mm lens. The sun comes from the RIGHT onto both planets and "
     "leaves their night sides and all of space black",
     "The red planet fills the LEFT third of the frame, half the frame's height, lit on its RIGHT side. The "
     "small blue Earth hangs at the RIGHT third. A small glowing cylinder crosses the CENTRE between them and "
     "the rest of space is black with fine stars at the TOP and BOTTOM edges.",
     "friction", "What he did not see: the Thing on its way. The audience knows more than he does."),
    # 16 -- the lantern lit at one
    ("knoll", "insert", [], "medium_observatory_door", 0.5,
     "Insert on the shaded brass lantern on the top brick step of the observatory at night, Ogilvy's broad "
     "ink-stained hand turning up its wick, the flame rising behind the glass and the gravel below.",
     "The camera tilts down on the lantern across the whole shot, travelling a finger's breadth; the brass "
     "lantern keeps the frame's centre; his hand turns the wick up and lifts the lantern by its ring.",
     "beside the steps at the height of a crouching man's eye, an arm's length from the lantern, a 90mm "
     "lens. The flame comes from the CENTRE onto his fingers and leaves the plank door behind black",
     "The brass lantern stands at the CENTRE of the frame on the red brick step, the height of the middle "
     "third, its flame bright behind the glass. His hand comes in from the LEFT edge, the gravel lies across "
     "the BOTTOM edge and the plank door is black across the TOP.",
     "transition", "The vigil ends by his hand: the light they carry down among the sleepers."),
    # 13 ANSWER -- a million to one
    ("knoll", "medium_close", ["ogilvy"], "medium_observatory_door", 0.7,
     f"Medium close of {OGIL} on the brick steps of the observatory at night with the brass lantern raised "
     "in one hand, the broad ruddy face amused and sure, the full auburn beard, the plank door dark behind.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the plank door keeps the "
     "left edge; his free hand lifts and waves the thought away; the lantern swings a hand's breadth.",
     "on the gravel path level with his eyes, two long strides from him, a 50mm lens. The lantern comes from "
     "LOW at the RIGHT onto his face and leaves the dome and the sky black",
     "Ogilvy's head and shoulders fill the CENTRE of the frame from the TOP third to the ochre cape at the "
     "BOTTOM edge, his head a third of the frame's height, lit from LOW at the RIGHT. The plank door is dark "
     "at the LEFT edge and the starry sky is black across the TOP.",
     "answer", "The world answers the question: no. The man best placed to see it laughs it off."),
    # 12 -- walking down from the knoll
    ("knoll", "wide", [], "reverse", 0.9,
     f"Wide from the knoll at night: {OGIL} and {NARR} walking down the grass beside the white observatory "
     "wall, the brass lantern swinging from Ogilvy's hand, the lit house below and the scattered lamps of "
     "Ottershaw beyond.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the white observatory wall "
     "keeps the left edge; the two men walk down the grass at a normal walking pace toward the lit house.",
     "at the observatory door on the knoll at a standing man's eye, four long strides from them, a 35mm "
     "lens. The lantern comes from LOW in Ogilvy's hand onto the grass and leaves the fields and the sky "
     "black",
     "The white observatory wall holds the LEFT edge of the frame. The two men walk at the CENTRE of the "
     "lower half, each the height of a finger, the lantern between them. The lit house sits at the CENTRE "
     "of the frame and the village lamps are small across the RIGHT third under a black sky.",
     "transition", "Down among the sleepers: the village that will be in the path."),
    # 14 -- the petty concerns
    ("study", "medium", ["unnamed_first_person_narrator"], "medium_writing_table", 0.3,
     f"Medium of {NARR}, the boater set on the table, at the mahogany writing-table under the green-shaded "
     "lamp, a steel pen moving across a manuscript page, the French window dark beside him.",
     "The camera pans left across the whole shot, travelling a forearm; the green lamp keeps the right "
     "third; he writes a line across the page and lifts the pen to the inkwell.",
     "at the side of the table at a seated man's eye, three long strides from him, a 35mm lens. The lamp "
     "comes from LOW at the RIGHT onto the page and his face and leaves the bookcases black",
     "The writing-table crosses the BOTTOM half of the frame with the green-shaded lamp at the RIGHT third. "
     "The Narrator sits at the CENTRE, his head a quarter of the frame's height, bent to the page. The "
     "French window is black at the LEFT edge and the bookcases are black across the TOP.",
     "transition", "Men going about their petty concerns: the lead among them, busy with moral progress."),
    # 19 -- her hand on his arm
    ("porch", "insert", [], "medium_front_door_porch", 0.3,
     "Insert on the Wife's slim hand with its plain gold wedding band slipping into the crook of the "
     "Narrator's grey herringbone tweed sleeve on the gravel path at night, the paisley shawl over her wrist.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the grey tweed sleeve keeps "
     "the frame's centre; her hand slides into the crook of his arm and his arm draws it in.",
     "beside them at the height of a standing man's elbow, an arm's length from the hands, a 90mm lens. The "
     "fanlight comes from BEHIND at the LEFT onto the gold band and leaves the laurels beyond black",
     "The grey tweed sleeve crosses the CENTRE of the frame from the LEFT edge with her slim hand at the "
     "CENTRE, the gold band catching the light. The paisley shawl hangs at the BOTTOM RIGHT and the laurels "
     "are black across the TOP.",
     "runout", "The marriage in one gesture: what the war will separate."),
    # 15 -- the walk home
    ("porch", "medium", ["unnamed_first_person_narrator", "narrators_wife"], "medium_front_door_porch", 0.4,
     f"Medium of {NARR} and {WIFE} arm in arm on the gravel path before the black front door under the "
     "porch, the fanlight glowing behind them, his free hand pointing up at the stars.",
     "The camera pans right across the whole shot, travelling a forearm; the lit fanlight keeps the centre; "
     "his hand lifts and points up at the sky and she turns her face up after it.",
     "on the gravel path at a standing man's eye, three long strides from them, a 35mm lens. The fanlight "
     "comes from BEHIND them onto their shoulders and leaves the laurels and the sky black",
     "The Narrator stands at the LEFT third and the Wife at the RIGHT third of the frame, each from the "
     "BOTTOM edge to the TOP third, heads a quarter of the frame's height. The black door and its glowing "
     "fanlight stand at the CENTRE behind them and the laurels are black at both edges.",
     "runout", "Home, domestic, safe: a husband explaining the sky to his wife."),
    # 18 -- the trains in the distance
    ("porch", "medium_close", ["unnamed_first_person_narrator"], "medium_front_door_porch", 0.6,
     f"Medium close of {NARR} on the gravel path at night with his face turned up to the stars, the grey "
     "eyes on the sky, the lit fanlight of the porch glowing behind his shoulder.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the glowing fanlight keeps "
     "the left third; his raised hand points up at the red dot overhead; his head turns to her.",
     "on the gravel path level with his eyes, two long strides from him, a 50mm lens. The fanlight comes "
     "from BEHIND at the LEFT onto his shoulder and leaves the laurels and the sky black",
     "The Narrator's head and shoulders fill the CENTRE of the frame from the straw boater at the TOP third "
     "to the grey tweed at the BOTTOM edge, his head a third of the frame's height, his face turned up. The "
     "glowing fanlight sits at the LEFT third and the laurels are black at the RIGHT edge.",
     "runout", "The last calm: the sounds of a sleeping suburb."),
    # 16 BUTTON -- the signal lights
    ("porch", "medium_close", ["narrators_wife"], "medium_front_door_porch", 0.8,
     f"Medium close of {WIFE} on the gravel path at night, her face turned up and toward the right, wide "
     "hazel eyes bright, one slim hand with its gold band raised toward the railway beyond the laurels.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the glowing fanlight keeps "
     "the left third; her raised hand points toward the railway; her face turns to him with a smile.",
     "on the gravel path level with her eyes, two long strides from her, a 50mm lens. The fanlight comes "
     "from BEHIND at the LEFT onto her hair and cheek and leaves the laurels behind her black",
     "The Wife's head and shoulders fill the CENTRE of the frame from her chestnut hair at the TOP third to "
     "the paisley shawl at the BOTTOM edge, her head a third of the frame's height. The glowing fanlight "
     "sits at the LEFT third and the laurels are black at the RIGHT edge.",
     "button", "The world's last word: beauty, safety -- the lights she admires sit on the line the "
     "Martians will come down."),
    # 17 -- silent: the signal lights over the valley
    ("study", "wide", [], "window_view_panorama", 1.0,
     "Wide through the open French windows of the study over the valley at night: the iron rail in the "
     "foreground, the dark beech tops, and beyond them the railway cutting with its brick arch and the red, "
     "green and yellow signal lamps on their gantry, the lamps of Woking and the dark heath under the stars.",
     "The camera pushes in on the signal gantry across the whole shot, travelling a hand's breadth; the "
     "open window frames keep both edges; a train's lamps travel along the cutting past the signals.",
     "at the writing-table looking out through the open windows at a standing man's eye, a 35mm lens. The "
     "signal lamps and the town lamps come from the valley below and leave the heath and the sky black",
     "The open window frames stand at the LEFT edge and the RIGHT edge of the frame with the iron rail "
     "across the BOTTOM third. The red, green and yellow signals sit at the RIGHT third over the brick arch. "
     "The town lamps glow at the LEFT third and the heath and the sky are black across the TOP.",
     "runout", "Silent. The same view will burn in chapter 11; tonight it is safe and tranquil."),
]

# (kind, speaker, text, shot)
N, O, W = "unnamed_first_person_narrator", "ogilvy", "narrators_wife"
LINES = [
    ("narration", N, "No one would have believed it, in those last years of the century. Our world was being watched.", 0),
    ("narration", N, "Across the gulf of space, minds vast and cool looked on our green Earth with envy, and planned.", 1),
    ("narration", N, "Then, one summer night, Lavelle of Java wired the news of a huge flame bursting out of Mars.", 2),
    ("narration", N, "Men went about their little affairs, serene and sure. I was busy writing essays on moral progress.", 3),
    ("narration", N, "I might never have heard of it, but for Ogilvy, the astronomer at Ottershaw. He was wild.", 4),
    ("dialogue", O, "Come and look. It came out of Mars like a shot from a gun.", 5),
    ("narration", N, "I still remember that vigil: the black dome, the lantern low in the corner, the clockwork ticking.", 6),
    ("narration", N, "Through the glass: deep blue, and in the middle of it the little planet, swimming.", 7),
    ("narration", N, "It seemed so small, so bright and silvery. Forty million miles of darkness lay between us.", 8),
    ("narration", N, "Ogilvy moved about in the dark behind me, unseen but heard, as the chronometer ran toward midnight.", 9),
    # shot 10: silent -- the flash
    ("dialogue", N, "Ogilvy! A red flash, just now, at the edge of it!", 11),
    ("narration", N, "He took the eyepiece at once, and cried out at the plume of gas.", 12),
    ("narration", N, "I felt my way to the siphon, green and crimson swimming before my eyes.", 13),
    ("narration", N, "I never dreamed of it then. That night, a second missile left Mars, flying straight for us.", 14),
    ("narration", N, "At one o'clock he gave up the watch, and we lit the lantern.", 15),
    ("dialogue", O, "The chances against anything manlike on Mars are a million to one.", 16),
    ("narration", N, "We walked down to his house. Below us, Ottershaw and Chertsey slept in peace.", 17),
    ("narration", N, "For ten nights the flames came, and the papers joked about volcanoes on Mars.", 18),
    ("narration", N, "One warm night, I took my wife out walking under the stars.", 19),
    ("narration", N, "I showed her the Zodiac, and Mars, a bright dot creeping overhead.", 20),
    ("narration", N, "Lights burned in upper windows. Far off, the shunting trains rang, softened into music.", 21),
    ("dialogue", W, "Look, dear, the signal lights. Red and green and yellow. So bright.", 22),
    # shot 23: silent -- the lights over the valley
]

BEDS = [
    {"from_shot": 0, "tone": "grave"},
    {"from_shot": 3, "tone": "plain"},
    {"from_shot": 7, "tone": "uneasy"},
    {"from_shot": 15, "tone": "plain"},
    {"from_shot": 19, "tone": "light"},
]

TURNS = {11: "a quiet vigil -> the first sign seen",
         16: "a sign seen -> explained away",
         22: "danger in the sky -> safe and tranquil at home"}

# (beat_s, coda_s) by shot; every other shot is 0.5 / 0.0
BEATS = {0: (0.8, 0.3), 1: (0.8, 0.0), 2: (0.8, 0.0), 4: (0.8, 0.0), 6: (0.8, 0.3), 7: (0.8, 0.0), 8: (0.6, 0.0), 10: (1.5, 3.0), 11: (1.0, 0.0), 14: (0.8, 0.3),
         16: (1.0, 0.0), 21: (1.0, 0.0), 22: (1.0, 0.6), 23: (1.0, 2.0)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, view, path, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.5, 0.0))
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces), view=view,
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), why=why,
                          cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=1, title="The Eve of the War",
                question="Today, can the narrator see what Mars is sending?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="line 15",
                beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words "
          f"-> {words / 3.0:.0f}s projected; dialogue {said / words:.1%}")
    print(OUT)
