r"""Episode 10 — "John Ferrier Talks with the Prophet", Part Two chapter 3.

THE BRICK. One event split by the title card.

  QUESTION  Today, can John Ferrier say no to the Prophet?
  TURN      shot 16, ~50 % in: Young turns on the threshold -- better that you
            and she lay skeletons on the Sierra Blanco than defy the Holy Four.
            prosperous and let alone -> marked.
  BUTTON    shot 30, Lucy, the world's answer and the last line: "But they won't
            let us leave." Then three silent shots: the bar across the door, the
            rusty shotgun cleaned and loaded by one candle.

Written against docs/analysis/ep08_ep09_why_worse.md and the gates built from
it, then read by a director before a cent was spent. What the reader sent back,
all applied here: the turn shot was written with the camera behind the man's
head; the sun was mirrored on every shot facing away from the house; Ferrier
was bare-headed on two outdoor sheets whose WARDROBE block puts his hat on; he
never said no in his own voice; the threat landed on nobody for three shots;
two pairs of closes were the same picture; Lucy's three heads all ended with a
hand at her collar; a push on four horses would clone them; a bar drawn in
mid-air would pass through its brackets. Twenty-four gate refusals before that,
none of which found any of it. Gates prove only the absence of their own fault.

Chapter 10 is the first with three characters in dialogue; MAX_SPEAKING is 4.
"""
import json
from pathlib import Path

OUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio"
           r"\library\20260822113400_a-study-in-scarlet\episodes\ep10\plan.json")

WHERE = "Ferrier's farm, Utah, 1860"
LIGHT = "low side sun, deep black shadow"

SETUPS = {
    "mountain_track_night": dict(
        described=("A mountain trail above the valley of Utah by night, June 1860: a rutted trail along "
                   "a bare rock shoulder, sagebrush and boulders on both sides, the valley a black gulf "
                   "below to the left, the ridge above to the right, the trail itself pale dust between "
                   "dark rocks; a low moon behind the ridge to the right is the only light and it comes "
                   "from behind and the right, throwing long black shadows off every boulder across the "
                   "trail toward the camera and leaving the riders' faces black under their hat brims, "
                   "the sagebrush silver at its edges and black at its heart"),
        cast=[], landmark="the ridge line against the moonlit sky", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the near bend of the trail along the rock shoulder to the far bend under the ridge",
        geometry=("The ridge line runs across the TOP third of the frame with the moon a hard white disc "
                  "behind it at the RIGHT edge. The trail runs from the bottom LEFT corner up toward the "
                  "far bend at the CENTRE of the upper third, pale dust between dark rocks. The valley "
                  "falls away as black along the whole LEFT edge. Every shadow lies from the upper right "
                  "toward the lower left, down the trail toward the camera."),
        crowd="Four masked riders sit their horses in a line on the trail with rifles across the saddle.",
        outdoors=True, props=[]),
    "farm_path_morning": dict(
        described=("The beaten path from the gate to the porch of John Ferrier's log villa on a fine June "
                   "morning, 1860: a five-bar gate at the near end, the shingly path running up between "
                   "cut stubble to the deep porch of the long log house, the sitting-room window beside "
                   "the door, a rail fence running off to the left, the pine hills dark behind the roof; "
                   "the low morning sun comes from the right, low enough to rake across the path and "
                   "throw the porch's black shadow half across it, the stubble on the right bright and "
                   "the stubble on the left in the porch's shadow, every post throwing a long shadow "
                   "to the left"),
        cast=["john_ferrier", "brigham_young"], landmark="the porch of the log house", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the gate up the shingly path to the porch step",
        geometry=("The porch and the open door stand in the TOP CENTRE of the frame under the long "
                  "shingled roof. The shingly path runs from the bottom LEFT corner up to the porch step "
                  "through the middle of the frame. The sitting-room window is a dark square to the RIGHT "
                  "of the door under the porch roof. The black shadow of the porch lies across the LEFT "
                  "half of the path and the sunlit stubble fills the RIGHT half. The rail fence runs off "
                  "the LEFT edge and the pine hills close the TOP edge behind the roof."),
        crowd="", outdoors=True, props=[]),
    "farm_parlour": dict(
        described=("Interior, inside the sitting-room of John Ferrier's log villa on a June morning, 1860, "
                   "the camera within the room with squared white-chinked log walls closed on all four "
                   "sides and a low plank ceiling: one deep window in the left wall is the only source, "
                   "and the light comes from the left window alone, a hard slab of morning sun lying "
                   "across the scrubbed pine table and the board floor and leaving the far corners of the "
                   "room and the cold stone hearth on the far wall in deep shadow; two ladder-back chairs "
                   "at the table, a rag rug on the boards, a riding whip lying on the table in the light, "
                   "the log walls warm where the slab touches them and black beyond it"),
        cast=["john_ferrier", "brigham_young"], landmark="the deep window in the left wall", landmark_at="start",
        landmark_size="is half the height of the frame",
        route="from the window across the pine table to the hearth on the far wall",
        geometry=("The deep window stands along the LEFT edge of the frame with its slab of hard light "
                  "lying across the middle of the frame from left to right. The scrubbed pine table stands "
                  "in the CENTRE of the frame in that light with the riding whip on it. The cold hearth is "
                  "a dark arch in the RIGHT third against the far log wall. The far corners are black "
                  "across the TOP third, and the rag rug lies in the BOTTOM third on the boards."),
        crowd="", outdoors=False, props=[]),
    "farm_doorway": dict(
        described=("The open front door of John Ferrier's log villa on a June morning, 1860: the deep "
                   "porch on its two posts, the plank door standing open between its dark jambs, the "
                   "sitting-room window to its right, the long log wall running off either side, cut "
                   "stubble either side of the shingly path down to the gate; the low sun comes from the "
                   "right and lights the porch posts, the door frame and the right-hand log wall hard, "
                   "throws the posts' shadows long to the left across the boards, and leaves the room "
                   "behind the open door black"),
        cast=["john_ferrier", "brigham_young"], landmark="the open front door", landmark_at="start",
        landmark_size="fills the frame",
        route="from the porch step down the shingly path to the gate",
        geometry=("The open door stands in the CENTRE of the frame with black behind it under the porch "
                  "roof. The two porch posts stand at the LEFT and RIGHT edges, sunlit on their right "
                  "faces. The shingly path runs from the BOTTOM edge up to the porch step in the middle "
                  "of the frame. The sitting-room window is a dark square in the RIGHT third beside the "
                  "door and the porch's shadow lies across the LEFT third of the path."),
        crowd="", outdoors=True, props=[]),
    "parlour_evening": dict(
        described=("Interior, inside the sitting-room of John Ferrier's log villa on the same evening, "
                   "1860, the camera within the room with squared white-chinked log walls closed on all "
                   "four sides: the one oil lamp burning on the scrubbed pine table is the only light and "
                   "it comes from the lamp alone, low and warm, on the two faces at the table and on the "
                   "near log wall, the deep window a blue-black square in the left wall with the lamp's "
                   "flame reflected small in its glass, the cold hearth and the far corners in darkness, "
                   "two ladder-back chairs, the rag rug a dark shape on the boards, the riding whip on "
                   "the table beside the lamp"),
        cast=["john_ferrier", "lucy_ferrier"], landmark="the oil lamp on the pine table", landmark_at="start",
        landmark_size="is the height of a hand",
        route="from the lamp on the table across the rag rug to the dark window",
        geometry=("The oil lamp stands on the pine table in the CENTRE of the frame and throws its light "
                  "outward across the table top to the BOTTOM third. The window is a blue-black square "
                  "along the LEFT edge with one small reflected flame in it. The far log wall and the cold "
                  "hearth are darkness across the TOP third. The near log wall catches the lamp's warmth "
                  "along the RIGHT edge and everything past an arm's length from the lamp is black."),
        crowd="", outdoors=False, props=[]),
    "bedroom_night": dict(
        described=("Interior, inside John Ferrier's small log bedroom that night, 1860, the camera within "
                   "the room with squared log walls closed on all four sides and a low plank ceiling: "
                   "one candle burning on a stool beside the narrow bed is the only light and it comes "
                   "from the candle alone, low and yellow, throwing a man's shadow huge up the log wall; "
                   "a rusty old single-barrelled shotgun hangs on two wooden pegs on the log wall above "
                   "the bed, a heavy plank door in the near wall with a wooden bar seated in its two iron "
                   "brackets, a small tin of oil and a rag on the stool, the corners of the room in "
                   "darkness"),
        cast=["john_ferrier"], landmark="the shotgun on its two pegs", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the plank door across the boards to the bed under the shotgun",
        geometry=("The plank door stands along the LEFT edge of the frame with its bar across it in the "
                  "two iron brackets at the height of a man's chest. The candle on the stool burns in the "
                  "BOTTOM RIGHT corner and is the only light. The narrow bed lies along the RIGHT third. "
                  "The shotgun hangs on its two pegs across the TOP third of the far log wall above the "
                  "bed, and the man's shadow climbs the LEFT wall beside the door."),
        crowd="", outdoors=False, props=[]),
}

# (setup, size, faces, path, frame, motion, camera, at_rest, section, beat, coda)
S = [
    # ---- hook: the Avenging Angels --------------------------------------------
    ("mountain_track_night", "wide", [], 0.0,
     "Wide of the mountain trail by night: four masked riders halted in a line across the trail "
     "on the bare rock shoulder, rifles across their saddles, the low moon behind the ridge at the "
     "right throwing their long black shadows across the trail toward the camera, the valley a "
     "black gulf at the left.",
     "The camera pushes in on the four riders across the whole shot, travelling a hand's breadth; "
     "the nearest horse shifts one hoof on the rock; a rider turns his masked head toward the valley.",
     "on the trail at the height of a mounted man's eye, four long strides below the riders, a "
     "35mm lens. The low moon stands behind the ridge at the right and throws every shadow toward "
     "the camera",
     "The ridge line crosses the TOP third of the frame with the moon a hard white disc at the "
     "RIGHT edge. The four riders stand in a row across the CENTRE of the frame, each the height "
     "of a hand, their masked faces black under their hat brims. Their four shadows lie down the "
     "trail across the BOTTOM third to the bottom edge, and the valley is a black wall along the "
     "LEFT edge.",
     "hook", 0.0, 0.0),

    ("mountain_track_night", "medium", [], 0.4,
     "Medium of two masked riders side by side on the trail, dark cloth masks under low hat "
     "brims, long rifles across the saddle bows, the moon behind the ridge rimming the horses' "
     "backs and leaving the men's faces black.",
     "The camera pushes in on the two riders across the whole shot, travelling a forearm; the near "
     "rider lifts his rifle a hand's breadth off the saddle bow; the near horse's ear turns back.",
     "on the trail level with the riders' chests, two long strides from the near horse, a 50mm "
     "lens. The moon rims the men from behind and the right",
     "The two riders fill the CENTRE of the frame from the bottom edge to the TOP third, the near "
     "rider at the RIGHT, the far rider at the LEFT, both masked faces a black oval under the hat "
     "brim. The two rifles lie across the middle of the frame as two lines of moonlit steel. The "
     "ridge and the white moon fill the TOP edge behind their hats.",
     "setup", 0.0, 0.0),

    ("mountain_track_night", "insert", [], 0.6,
     "Insert on a bare brown hand closed on the stock of a long rifle across a saddle bow, the moon "
     "lying as one white line along the barrel, the horse's dark shoulder below.",
     "The camera pushes in on the hand across the whole shot, travelling a hand's breadth; the "
     "bare fingers close tighter on the stock; the horse's shoulder rises under the rifle as it "
     "breathes.",
     "beside the horse at the height of the saddle bow, an arm's length from the hand, a 90mm "
     "lens. The moon lays one line of light along the barrel from the right",
     "The bare hand fills the CENTRE of the frame closed on the dark stock. The rifle barrel runs "
     "from the hand to the RIGHT edge as one white line of moonlight on steel. The horse's dark "
     "shoulder fills the BOTTOM third and the black of the night fills the TOP third.",
     "setup", 0.4, 1.0),

    # ---- the Prophet at the gate ----------------------------------------------
    ("farm_path_morning", "wide", [], 0.0,
     "Wide up the shingly path to the porch of the log villa on a fine June morning, the five-bar "
     "gate in the near ground standing open, the low sun from the right raking the stubble and "
     "throwing the porch's black shadow half across the path, the sitting-room window a dark "
     "square beside the door.",
     "The camera pushes in on the porch across the whole shot, travelling two long strides; John "
     "Ferrier's bearded face comes up pale behind the dark glass of the sitting-room window; a "
     "curtain moves beside it.",
     "on the path just inside the gate at a standing man's eye, a 35mm lens. The low morning sun "
     "comes from the right and throws the porch's shadow toward the left",
     "The porch and the open door stand in the TOP CENTRE of the frame the height of a hand. The "
     "shingly path runs from the bottom LEFT corner up to the porch step through the middle of "
     "the frame. The black shadow of the porch lies across the LEFT half of the path and the sunlit "
     "stubble fills the RIGHT half. The gate's top bar crosses the BOTTOM edge.",
     "setup", 0.0, 0.0),

    ("farm_path_morning", "medium", ["brigham_young"], 0.4,
     "Medium of Brigham Young coming up the shingly path toward the porch, a stout sandy-haired "
     "man in a plain black homespun frock coat buttoned high over a black stock, bare-headed, a "
     "brown-backed volume under one arm, the low sun from the left hard on the side of his face.",
     "The camera pushes in on Brigham Young across the whole shot, travelling a forearm, as he "
     "walks up the path toward it at a normal walking pace; he shifts the brown-backed volume from "
     "one arm to the other; the shingle turns under his boots.",
     "on the path ahead of him at the height of his chest, three long strides up the path from "
     "him, a 50mm lens. The low sun comes from the left and leaves the right side of his face in "
     "shadow",
     "Brigham Young fills the CENTRE of the frame from the bottom edge to the TOP third, his sandy "
     "head at the TOP CENTRE, the black frock coat filling the middle of the frame, the "
     "brown-backed volume under his left arm at the RIGHT of the frame. The sunlit stubble fills "
     "the LEFT edge and the open gate and the pale valley the TOP edge behind him.",
     "setup", 0.0, 0.0),

    ("farm_path_morning", "close", ["brigham_young"], 0.6,
     "Close on Brigham Young's face coming up the path, the full florid clean-shaven face and "
     "heavy jaw, the pale blue eyes under light sandy lashes turned up toward the porch, the sandy "
     "hair going grey combed back, the low sun from the left on one cheek and the other in "
     "shadow.",
     "The camera pushes in on Brigham Young's face across the whole shot, travelling a hand's "
     "breadth; his pale eyes come up from the path to the door ahead; he lifts his head a finger's "
     "breadth toward the door.",
     "on the path at Brigham Young's own eye, an arm's length ahead of him, a 90mm lens. The low "
     "sun comes from the left and splits his face into a lit half and a dark half",
     "Brigham Young's face fills the CENTRE of the frame from the chin at the BOTTOM edge to the "
     "sandy hair at the TOP edge, the LEFT half of the face in hard sun and the RIGHT half in "
     "shadow, the pale eyes on the line of the upper third. The black stock and the top of the "
     "frock coat cross the BOTTOM edge and the sunlit stubble is a blur along the LEFT edge.",
     "setup", 0.0, 0.0),

    ("farm_path_morning", "medium", ["john_ferrier", "brigham_young"], 0.9,
     "Medium at the porch step: John Ferrier in the open doorway in his wide-brimmed brown felt "
     "hat and the fawn homespun coat open over his dark waistcoat, one bare hand held out, Brigham "
     "Young arriving at the step with his back three-quarter to the camera, the black room behind "
     "Ferrier.",
     "The camera pushes in on the two men across the whole shot, travelling one long stride; "
     "Brigham Young walks past Ferrier's held-out hand and into the dark doorway at a normal "
     "walking pace; Ferrier lowers the hand to his side and turns after him into the door.",
     "on the path below the porch, level with Ferrier's chest, two long strides from the step, "
     "a 50mm lens. The low sun comes from the right and lights the porch post and Ferrier's coat",
     "John Ferrier stands in the open doorway in the CENTRE of the frame from the porch step at the "
     "BOTTOM edge to the door lintel at the TOP edge, the hat brim's black across his eyes and his "
     "RIGHT hand held out into the light. Brigham Young's broad black-coated back fills the RIGHT "
     "third of the frame at the step. The room behind Ferrier is black across the middle of the "
     "frame.",
     "setup", 0.0, 0.0),

    # ---- the interview ----------------------------------------------------------
    ("farm_parlour", "medium_close", ["brigham_young"], 0.1,
     "Medium close of Brigham Young seated in a ladder-back chair at the pine table with the slab of "
     "window light lying across the table and his black knees, the brown-backed volume under his "
     "hand on the table, his pale eyes turned up at Ferrier standing off frame at the right, the "
     "far corner of the room in deep shadow.",
     "The camera pushes in on Brigham Young across the whole shot, travelling a forearm; he "
     "lays one heavy hand flat on the brown-backed volume; he turns his sandy head a hand's breadth "
     "toward the right of frame.",
     "at the table end level with a seated man's eye, two long strides from the chair, a 50mm "
     "lens. The window at the left throws a hard slab of sun across the table and his knees",
     "Brigham Young sits in the ladder-back chair in the CENTRE of the frame from the bottom edge to "
     "the TOP third, his sandy head against the deep shadow of the far corner, the slab of window "
     "sun lying across the pine table in the BOTTOM third and across his black knees. The "
     "brown-backed volume lies under his hand at the BOTTOM CENTRE and the window's edge is a bar "
     "of light along the LEFT edge.",
     "friction", 0.0, 0.0),

    ("farm_parlour", "close", ["john_ferrier"], 0.3,
     "Close on John Ferrier standing by the table, the long sun-darkened face and iron-grey beard "
     "lit hard from the window at the left and the right side of the face in shadow, his eyes down "
     "toward the chair below the frame, the top of the pushed-back chair's rail bright in the "
     "bottom left corner, the log wall dark behind him.",
     "The camera pushes in on John Ferrier's face across the whole shot, travelling a hand's "
     "breadth; he draws a breath that lifts the rolled shirt sleeve at the bottom of frame; "
     "he brings his chin down a finger's breadth.",
     "in the room at John Ferrier's own eye, an arm's length from him, a 90mm lens. The window "
     "light comes from the left and leaves the right of his face dark",
     "John Ferrier's face fills the CENTRE of the frame from the beard at the BOTTOM edge to the "
     "iron-grey hair at the TOP edge, the LEFT half of the face carved in window light and the "
     "RIGHT half in shadow, the deep-set eyes on the line of the upper third looking down. The "
     "chair's top rail is a bright bar in the BOTTOM LEFT corner and the dark log wall fills the "
     "RIGHT edge behind him.",
     "friction", 0.0, 0.0),

    ("farm_parlour", "medium_close", ["brigham_young"], 0.4,
     "Medium close on Brigham Young in the chair, head and shoulders, the heavy florid face "
     "turned up, one thick sandy eyebrow raised, the window light on the near cheek, the black "
     "stock at his throat, the far corner black behind him.",
     "The camera pushes in on Brigham Young across the whole shot, travelling a hand's breadth; "
     "he lifts one heavy hand off the table and turns it palm up toward the right of frame; his "
     "head comes forward a finger's breadth on the question.",
     "at the table side level with Brigham Young's eye, an arm's length from him, a 50mm lens. "
     "The window sun comes from the left onto his near cheek",
     "Brigham Young's head and shoulders fill the CENTRE of the frame from the black stock at the "
     "BOTTOM edge to the sandy hair at the TOP edge, the LEFT cheek in hard sun and the RIGHT cheek "
     "in shadow, the pale eyes on the upper third turned up to the right. His raised hand comes "
     "into the BOTTOM RIGHT corner and the deep shadow of the far corner fills the frame behind "
     "him.",
     "friction", 0.0, 0.0),

    ("farm_parlour", "insert", [], 0.5,
     "Insert at the edge of the pine table: the riding whip's leather thong hanging down off the "
     "table's edge into shadow, John Ferrier's bare heavy knuckles closed on the stock above it in "
     "the window sun, the dark board floor and the rag rug far below.",
     "The camera pushes in on the thong across the whole shot, travelling a hand's breadth; the "
     "knuckles turn the whip stock a quarter turn; the thong swings once off the table's edge.",
     "beside the table at the height of its top, an arm's length from the edge, a 90mm lens. The "
     "window sun comes from the left across the table's edge and drops off into shadow below it",
     "The table's edge runs across the frame on the line of the upper third, sunlit along its lip. "
     "The knuckles and the whip stock sit on it at the CENTRE, lit from the LEFT. The leather "
     "thong hangs straight down from the stock through the BOTTOM half of the frame into shadow, "
     "and the rag rug is a dark shape at the BOTTOM edge.",
     "friction", 0.0, 0.0),

    ("farm_parlour", "medium_close", ["brigham_young"], 0.6,
     "Medium close on Brigham Young from above, head and shoulders, leaning a little forward in "
     "the chair with both heavy hands flat on the pine table in the window light, the pale eyes "
     "turned up into the lens, the sandy hair going grey combed back.",
     "The camera pushes in on Brigham Young across the whole shot, travelling a hand's breadth; "
     "he brings both flat hands forward a hand's breadth along the table toward the lens; his "
     "shoulders come forward with them.",
     "at the table end at a standing man's eye looking down at him, an arm's length from him, a "
     "50mm lens. The window sun comes from the left across the table and his hands",
     "Brigham Young's head and shoulders fill the CENTRE of the frame from the TOP edge to the "
     "black coat at the BOTTOM third, the LEFT cheek sunlit, the pale eyes on the upper third "
     "fixed up into the lens. His two heavy hands lie flat on the sunlit table across the BOTTOM "
     "edge of the frame. The far corner is deep shadow behind his RIGHT shoulder.",
     "friction", 0.0, 0.0),

    ("farm_parlour", "close", ["john_ferrier"], 0.7,
     "Close on John Ferrier's face with the brows knitted, the riding whip's stock held up under "
     "his chin in his bare knuckles, the deep-set eyes narrowed under the heavy brows, the "
     "iron-grey beard lit from the window at the left, the right of the face in shadow.",
     "The camera pushes in on John Ferrier's face across the whole shot, travelling a hand's "
     "breadth; his brows draw down a finger's breadth over the eyes; he lifts his bearded chin a "
     "finger's breadth off the whip stock to answer.",
     "in the room at John Ferrier's own eye, an arm's length from him, a 90mm lens. The window "
     "light comes hard from the left",
     "John Ferrier's face fills the CENTRE of the frame from the beard at the BOTTOM third to the "
     "hairline at the TOP edge, the LEFT half of the face in window light and the RIGHT half in "
     "shadow, the knitted brows on the line of the upper third. The whip stock crosses the BOTTOM "
     "edge under his beard in his bare knuckles and the dark log wall fills both edges behind his "
     "head.",
     "friction", 1.0, 1.5),

    ("farm_parlour", "medium", ["brigham_young", "john_ferrier"], 0.9,
     "Medium of Brigham Young on his feet beside the pushed-back ladder-back chair, the "
     "brown-backed volume tucked under his arm, the slab of window light cutting across his black "
     "waistcoat at the chest, his sandy head above the light in shadow, the chair's rungs bright "
     "beside his knee, John Ferrier's dark shoulder at the right edge.",
     "The camera pushes in on Brigham Young across the whole shot, travelling a forearm; "
     "he pushes the chair back a hand's breadth with his knee; he tucks the volume tighter under "
     "his arm and turns toward the door.",
     "at the window end of the room level with a standing man's chest, three long strides from the "
     "table, a 35mm lens. The window beside the camera at the left throws its slab of sun across "
     "the table between the two men",
     "Brigham Young stands on his feet at the LEFT third of the frame from the bottom edge to the "
     "TOP edge, the slab of window light cutting across his chest at the CENTRE line and his head "
     "in shadow above it. The pushed-back chair's bright rungs stand at the BOTTOM LEFT. John "
     "Ferrier's dark shoulder cuts the RIGHT edge and the black hearth arch sits in the TOP RIGHT.",
     "friction", 1.5, 0.0),

    # ---- turn: the threat on the threshold ---------------------------------------
    ("farm_doorway", "medium_close", ["brigham_young"], 0.0,
     "Medium close of Brigham Young turned back on the threshold and facing into the room, head "
     "and shoulders, the flushed heavy face and flashing pale eyes full to the lens, one hand up "
     "on the door frame, the brown-backed volume clamped under his other arm, the sunlit path and "
     "the pale valley bright behind him between the black door jambs.",
     "The camera pushes in on Brigham Young across the whole shot, travelling a forearm; "
     "he throws one heavy hand up and out in a threat toward the lens; his boot comes down "
     "hard on the threshold.",
     "inside the doorway at Brigham Young's own eye, an arm's length from him with the black door "
     "jamb at each edge of the lens, a 50mm lens. The low sun comes from the right along the house "
     "front and lights the path behind him and his right cheek hard",
     "Brigham Young's head and shoulders fill the CENTRE of the frame from the black stock at the "
     "BOTTOM edge to the sandy hair at the TOP edge, the RIGHT half of the flushed face in hard sun "
     "and the LEFT half in shadow, the pale eyes on the upper third full to the lens. The black "
     "door jambs stand at the LEFT and RIGHT edges and the sunlit path and pale valley fill the "
     "frame bright between them behind his head.",
     "turn", 0.0, 0.0),

    ("farm_doorway", "insert", [], 0.1,
     "Insert on Brigham Young's heavy raised hand against the black of the door jamb, the fingers "
     "spread in a threat, the sunlight from the right hard on the knuckles and the black coat "
     "cuff, the white shirt cuff below it.",
     "The camera pushes in on the raised hand across the whole shot, travelling a hand's breadth; "
     "the spread fingers close into a fist; the fist drops out of the bottom of the frame.",
     "at the threshold at the height of a standing man's head, an arm's length from the hand, a "
     "90mm lens. The low sun comes from the right onto the knuckles",
     "The raised hand fills the CENTRE of the frame with the fingers spread across the upper third, "
     "lit hard from the RIGHT, the black coat cuff and the white shirt cuff at the BOTTOM CENTRE. "
     "The black of the door jamb fills the whole frame behind the hand and the sunlit door frame "
     "is a bar of light along the RIGHT edge.",
     "spike", 0.0, 0.0),

    ("farm_doorway", "medium_close", ["john_ferrier"], None,
     "Medium close on John Ferrier inside the doorway, head and shoulders, in the brown felt hat "
     "with the brim's black across his eyes and the fawn coat open, the long sun-darkened face and "
     "iron-grey beard, the low sun from the right on one side of the face, the riding whip in his "
     "hand at the bottom of frame, the black room behind him.",
     "The camera pushes in on John Ferrier across the whole shot, travelling a hand's breadth; "
     "his head turns a hand's breadth to follow the man out of the door; his hand tightens on the "
     "riding whip and draws it up against his chest.",
     "on the threshold level with John Ferrier's eye, an arm's length from him, a 50mm lens. The "
     "low sun comes from the right onto his near cheek under the hat brim",
     "John Ferrier's head and shoulders fill the CENTRE of the frame from the TOP edge to the fawn "
     "coat at the BOTTOM third, the hat brim's black across his eyes and the RIGHT cheek in hard "
     "sun under it, the LEFT cheek in shadow. The riding whip crosses the BOTTOM edge in his hand "
     "and the black of the room fills the frame behind his head.",
     "reaction", 1.5, 1.5),

    ("farm_doorway", "medium", ["brigham_young"], 0.6,
     "Medium of Brigham Young's broad black-coated back going away down the shingly path from "
     "the porch, seen low from the porch boards, the brown-backed volume under one arm, his boots "
     "and the swinging coat skirts big in the frame, the low sun from the left on his sandy head, "
     "the open gate small at the far end of the path.",
     "The camera pushes in on Brigham Young's back across the whole shot, travelling one long "
     "stride as he walks away down the path at a normal walking pace; the shingle turns under his "
     "heavy boots; his black coat skirts swing at the knee.",
     "on the porch boards at the height of a man's knee, three long strides behind him, a 35mm "
     "lens. The low sun comes from the left and lights his head and shoulder",
     "Brigham Young's black back fills the CENTRE of the frame from the boots at the bottom edge to "
     "the sandy head at the TOP third, lit from the LEFT. The shingly path runs from the BOTTOM "
     "edge past his boots to the open gate small at the CENTRE of the upper third. The sunlit "
     "stubble fills the LEFT edge and the porch's black shadow the RIGHT edge.",
     "spike", 0.0, 0.0),

    # ---- payoff: the lamp -------------------------------------------------------
    ("parlour_evening", "medium", ["john_ferrier", "lucy_ferrier"], 0.1,
     "Medium of John Ferrier seated at the pine table with his elbows on his knees and his bearded "
     "head bowed over his hands in the lamplight, Lucy Ferrier standing beside him in the "
     "grey-blue house dress with her small bare hand laid on his, the lamp warm on the two of them "
     "and the room black behind.",
     "The camera pushes in on the two of them across the whole shot, travelling one long stride; "
     "Lucy lays her hand over her father's on his knee; he lifts his bowed head to look up at her.",
     "at the hearth end of the room level with a seated man's eye, three long strides from the "
     "table, a 50mm lens. The one oil lamp on the table lights the two faces from the left and "
     "leaves the room black",
     "John Ferrier sits bowed in the CENTRE of the frame from the bottom edge to the TOP third with "
     "his elbows on his knees, the lamp on the table at the LEFT edge lighting the side of his "
     "beard. Lucy stands at the RIGHT of the frame from the bottom edge to the TOP edge in the "
     "grey-blue dress, her hand on his at the CENTRE. The room is black across the TOP third and "
     "the far RIGHT.",
     "payoff", 0.0, 0.0),

    ("parlour_evening", "close", ["lucy_ferrier"], 0.2,
     "Close on Lucy Ferrier's pale frightened face in the lamplight, the chestnut hair gathered "
     "back, the clear hazel eyes wide and wet, her lips parted, the lamp warm on one side of her "
     "face and the other side dark.",
     "The camera pushes in on Lucy's face across the whole shot, travelling a hand's breadth; her "
     "lips part on the question; she bows her head a finger's breadth toward her father below the "
     "frame.",
     "in the room at Lucy's own eye, an arm's length from her, a 90mm lens. The lamp lights her "
     "from the left and low",
     "Lucy's face fills the CENTRE of the frame from the narrow white collar at the BOTTOM edge to "
     "the chestnut hairline at the TOP edge, the LEFT half warm in lamplight and the RIGHT half in "
     "shadow, the wide hazel eyes on the line of the upper third. The black of the room fills both "
     "edges behind her head.",
     "payoff", 0.0, 0.0),

    ("parlour_evening", "medium_close", ["john_ferrier"], 0.3,
     "Medium close on John Ferrier, head and shoulders, looking up at Lucy from the chair with the "
     "lamplight in his beard, one broad rough hand raised to the height of her hair at the top of "
     "frame, his deep-set eyes soft, the log wall dark behind him.",
     "The camera pushes in on John Ferrier across the whole shot, travelling a hand's breadth; he "
     "passes his broad rough hand once over the chestnut hair at the top of frame; he draws the "
     "hand down along her hair toward her shoulder.",
     "at the table side level with John Ferrier's eye, an arm's length from him, a 50mm lens. The "
     "lamp lights him from the right and below",
     "John Ferrier's head and shoulders fill the CENTRE of the frame from the TOP edge to the dark "
     "waistcoat at the BOTTOM third, the RIGHT side of the beard warm in lamplight. His raised "
     "hand crosses the TOP RIGHT corner at the height of Lucy's hair with a fall of chestnut hair "
     "beside it. The log wall is black behind his LEFT shoulder.",
     "payoff", 0.0, 0.0),

    ("parlour_evening", "insert", [], 0.4,
     "Insert on Lucy's small bare hand closed hard over her father's broad rough hand on his knee "
     "in the lamplight, the grey-blue sleeve and the rolled white shirt sleeve, the rag rug dark "
     "below.",
     "The camera pushes in on the two hands across the whole shot, travelling a hand's breadth; "
     "her fingers tighten over his knuckles; his thumb moves across the backs of her fingers.",
     "beside the chair at the height of a seated man's knee, an arm's length from the hands, a "
     "90mm lens. The lamp lights the hands from above and the left",
     "The two hands fill the CENTRE of the frame, Lucy's small hand over her father's broad one on "
     "the dark cloth of his knee, lit warm from the TOP LEFT. The grey-blue sleeve comes in from "
     "the RIGHT edge and the rolled white shirt sleeve from the LEFT edge. The rag rug is dark "
     "across the BOTTOM third.",
     "payoff", 0.0, 0.0),

    ("parlour_evening", "close", ["john_ferrier"], 0.5,
     "Close on John Ferrier's face in three-quarter profile turned up to Lucy, the lamp behind "
     "him at the left rim-lighting the iron-grey beard and the cheekbone, the near side of the "
     "face black, a hard set to the mouth in the beard, Lucy's grey-blue sleeve at the right edge.",
     "The camera pushes in on John Ferrier's face across the whole shot, travelling a hand's "
     "breadth; he sets his jaw and brings his chin up a finger's breadth; he lifts one hand into "
     "the bottom of frame to count off a finger.",
     "in the room at John Ferrier's own eye, an arm's length from him, a 90mm lens. The lamp is "
     "behind him at the left and rims him; the near side of his face is black",
     "John Ferrier's face in three-quarter profile fills the CENTRE of the frame from the beard at "
     "the BOTTOM edge to the iron-grey hair at the TOP edge, the lamp's rim a line of warm light "
     "along the LEFT edge of the beard and the cheekbone, the near face BLACK across the CENTRE. "
     "Lucy's grey-blue sleeve stands at the RIGHT edge and one hand comes into the BOTTOM RIGHT "
     "corner.",
     "payoff", 0.0, 0.0),

    ("parlour_evening", "medium_close", ["lucy_ferrier"], 0.6,
     "Medium close on Lucy Ferrier, head and shoulders, laughing through her tears in the "
     "lamplight, the wet hazel eyes and the wide mouth, the chestnut hair gathered back, the "
     "narrow white collar of the grey-blue dress, the black room behind her.",
     "The camera pushes in on Lucy across the whole shot, travelling a hand's breadth; she laughs "
     "and brings the back of one bare hand up to wipe her eyes; she lets the hand fall to her "
     "collar.",
     "at the table side level with Lucy's eye, an arm's length from her, a 50mm lens. The lamp "
     "lights her from the left and below",
     "Lucy's head and shoulders fill the CENTRE of the frame from the TOP edge to the narrow white "
     "collar at the BOTTOM third, the LEFT side of her face warm in lamplight and the RIGHT in "
     "shadow, the wet eyes on the upper third. Her raised hand comes up into the RIGHT half of the "
     "frame and the black of the room fills the frame behind her.",
     "payoff", 0.0, 0.0),

    ("parlour_evening", "close", ["john_ferrier"], 0.7,
     "Close on John Ferrier's face in the lamplight with the deep-set eyes hard and steady, "
     "the iron-grey beard, the mouth set, the lamp warm on the right of the face and the left side "
     "black.",
     "The camera pushes in on John Ferrier's face across the whole shot, travelling a hand's "
     "breadth; he brings his bearded chin down a finger's breadth on the last word; he turns his "
     "head a hand's breadth toward the dark window.",
     "in the room at John Ferrier's own eye, an arm's length from him, a 90mm lens. The lamp "
     "lights him from the right",
     "John Ferrier's face fills the CENTRE of the frame from the beard at the BOTTOM edge to the "
     "hairline at the TOP edge, the RIGHT half in lamplight and the LEFT half in shadow, the hard "
     "eyes on the upper third. The blue-black window is a faint square at the LEFT edge and the log "
     "wall is black along the RIGHT edge.",
     "runout", 0.6, 0.0),

    ("parlour_evening", "medium_close", ["lucy_ferrier"], 0.8,
     "Medium close on Lucy Ferrier, head and shoulders, the laugh fallen from her face, the hazel "
     "eyes steady on her father at the left of frame, the chestnut hair gathered back, the lamp on "
     "one cheek, the blue-black window behind her shoulder.",
     "The camera pushes in on Lucy across the whole shot, travelling a hand's breadth; she puts "
     "her chin up a finger's breadth toward her father; she turns her head a hand's breadth to the "
     "blue-black window behind her shoulder.",
     "at the table side level with Lucy's eye, an arm's length from her, a 50mm lens. The lamp "
     "lights her from the left",
     "Lucy's head and shoulders fill the CENTRE of the frame from the TOP edge to the narrow white "
     "collar at the BOTTOM third, the LEFT cheek warm in lamplight, the steady eyes on the upper "
     "third turned toward the LEFT edge. The blue-black window is a square behind her RIGHT "
     "shoulder and the black room fills the TOP edge.",
     "button", 0.0, 0.0),

    # ---- the answer, in pictures: the bar, the gun, the candle ------------------
    ("bedroom_night", "medium", ["john_ferrier"], 0.0,
     "Medium of John Ferrier by one candle with both hands flat on the heavy wooden bar seated in "
     "its two iron brackets across the plank door of the log bedroom, bare-headed, in his dark "
     "waistcoat and rolled sleeves, the candle on the stool behind him throwing his shadow huge "
     "across the door.",
     "The camera pushes in on John Ferrier across the whole shot, travelling one long stride; he "
     "leans his weight onto the bar with both hands; his head bows between his arms.",
     "at the bed end of the small room level with a standing man's chest, three long strides from "
     "the door, a 35mm lens. The one candle on the stool at the right lights him from behind and "
     "below and throws his shadow on the door",
     "John Ferrier stands at the plank door along the LEFT third of the frame from the bottom edge "
     "to the TOP edge with both hands flat on the heavy bar lying in its two brackets across the "
     "middle of the frame, his huge shadow thrown up the door beside him. The candle burns on the "
     "stool in the BOTTOM RIGHT corner as the only light. The log wall and the shotgun's pegs are "
     "dark across the TOP RIGHT.",
     "answer", 1.0, 2.0),

    ("bedroom_night", "insert", [], 0.6,
     "Insert on John Ferrier's two bare heavy-knuckled hands drawing an oily rag down the rusty "
     "barrel of the old single-barrelled shotgun across his knees in candlelight, the rust brown on "
     "the steel, a small tin of oil open on the stool beside the candle.",
     "The camera pushes in on the hands across the whole shot, travelling a hand's breadth; the rag "
     "draws down the barrel toward the bottom of frame; the hands turn the gun over on his knees "
     "to the other side.",
     "beside the bed at the height of a seated man's knee, an arm's length from the gun, a 90mm "
     "lens. The candle lights the hands and the barrel from the left and low",
     "The two hands and the rusty barrel fill the CENTRE of the frame from the LEFT edge to the "
     "RIGHT edge, the rag dark in the near hand, the rust brown on the steel lit warm from the LEFT. "
     "The dark cloth of his knees fills the BOTTOM third and the open oil tin and the candle flame "
     "sit at the LEFT edge. The room is black across the TOP third.",
     "answer", 1.0, 1.5),

    ("bedroom_night", "medium", ["john_ferrier"], 0.8,
     "Medium of John Ferrier seated on the edge of the narrow bed with the shotgun across his knees "
     "in candlelight, bent over the breech, the candle on the stool warm on the right of his face "
     "and the rest of him in shadow, the barred plank door dark at the left, his shadow huge on the "
     "log wall behind him.",
     "The camera pushes in on John Ferrier across the whole shot, travelling one long stride; "
     "his hands close the breech of the gun with a snap; he turns "
     "his head toward the barred door.",
     "in the near corner beside the plank door, level with a seated man's eye, three long strides "
     "from the bed, a 35mm lens. The candle on the stool lights him from the right and below",
     "John Ferrier sits on the bed's edge in the CENTRE of the frame from the boards at the BOTTOM "
     "edge to the TOP third, bent over the shotgun across his knees, the RIGHT side of him warm from "
     "the candle on the stool in the BOTTOM RIGHT corner and the LEFT side black. His shadow climbs "
     "the log wall across the TOP third behind him and the barred plank door stands dark along the "
     "LEFT edge.",
     "answer", 1.0, 3.0),
]

EXTRA = {
    8: ("farm_parlour", "insert", [], 0.35,
        "Insert on Brigham Young's heavy hand lying flat on the brown-backed volume on the pine "
        "table in the slab of window sun, the thick fingers spread on the worn leather, the black "
        "coat cuff and the white shirt cuff, the scrubbed boards bright around it.",
        "The camera pushes in on the hand across the whole shot, travelling a hand's breadth; the "
        "thick fingers drum once on the leather; the hand draws the volume a hand's breadth toward "
        "the bottom of frame.",
        "over the table at the height of a seated man's chin, an arm's length from the hand, a 90mm "
        "lens. The window sun comes from the left along the table top",
        "The heavy hand fills the CENTRE of the frame spread on the brown-backed volume, lit hard "
        "from the LEFT. The volume lies in the BOTTOM half of the frame on the sunlit boards with "
        "the table's far edge running along the TOP third into shadow. The black coat cuff comes "
        "in from the RIGHT edge.",
        "friction", 0.0, 0.0),
    10: ("farm_parlour", "medium", ["john_ferrier"], 0.55,
         "Medium of John Ferrier standing beside the pine table with the riding whip in one bare "
         "hand and the other hand thrown out open in expostulation, the window light hard on the "
         "open hand and the rolled shirt sleeve, his bearded face in shadow, the dark hearth "
         "behind him.",
         "The camera pushes in on John Ferrier across the whole shot, travelling one long stride; "
         "he throws the open hand out a forearm's length into the window light; he brings it back "
         "to his chest with the whip.",
         "at the window end of the room level with a standing man's chest, three long strides "
         "from him, a 50mm lens. The window sun comes from the left across his hand and sleeve",
         "John Ferrier stands in the CENTRE of the frame from the bottom edge to the TOP third with "
         "his bearded face in shadow at the TOP CENTRE and his open hand thrown out into the light "
         "at the LEFT third. The riding whip hangs in his RIGHT hand along the RIGHT third. The pine "
         "table crosses the BOTTOM third in the sun and the cold hearth is a dark arch behind his "
         "shoulder at the RIGHT edge.",
         "friction", 0.0, 0.0),
    17: ("farm_doorway", "wide", [], 0.9,
         "Wide down the shingly path from the porch step to the open gate, Brigham Young's small "
         "black figure at the gate with the brown-backed volume under his arm, his long shadow "
         "thrown across the stubble by the low sun from the left, the valley pale beyond the gate.",
         "The camera pushes in on the gate across the whole shot, travelling one short stride as "
         "Brigham Young goes out through it at a normal walking pace; the gate swings a hand's "
         "breadth behind him; the long shadow slides off the stubble with him.",
         "on the porch step at a standing man's eye, a 35mm lens. The low sun comes from the left "
         "and throws every shadow to the right",
         "The shingly path runs from the BOTTOM edge of the frame up to the open gate at the CENTRE "
         "of the upper third. Brigham Young's black figure stands at the gate the height of a "
         "finger with his long shadow lying across the RIGHT half of the stubble. The sunlit stubble "
         "fills the LEFT half and the pale valley and the ridge fill the TOP third.",
         "spike", 0.0, 0.0),
    22: ("parlour_evening", "insert", [], 0.55,
         "Insert on the oil lamp's flame in its glass chimney on the pine table, the brass burner "
         "bright, the dark table top around it, the black of the room beyond the flame.",
         "The camera pushes in on the lamp across the whole shot, travelling a hand's breadth; John "
         "Ferrier's fingers turn the brass wick key a quarter turn at the bottom edge; the flame "
         "rises in the chimney.",
         "over the table at the height of the lamp chimney, an arm's length from the flame, a 90mm "
         "lens. The flame is the light",
         "The lamp's flame burns in its glass chimney at the CENTRE of the frame from the brass "
         "burner at the BOTTOM third to the top of the chimney at the TOP third. The dark table top "
         "fills the BOTTOM edge and the black of the room fills the LEFT third, the RIGHT third and "
         "the TOP edge.",
         "payoff", 0.0, 0.0),
    24: ("parlour_evening", "insert", [], 0.75,
         "Insert on the deep window's blue-black glass beside the table: the lamp's flame reflected "
         "small and sharp in one pane, the dark log frame around it, and beyond the glass the faint "
         "pale line of the path running down to the gate under a sky a shade lighter than the hills.",
         "The camera pushes in on the reflected flame across the whole shot, travelling a hand's "
         "breadth; the reflected flame leans once in the pane; John Ferrier's dark shoulder comes in "
         "across the left of the glass as he turns to the window.",
         "at the table's window end, level with the lamp chimney, an arm's length from the glass, a "
         "90mm lens. The lamp behind the camera is the light and the glass gives back one small flame",
         "The window's dark log frame crosses the frame as two thick bars, one along the TOP edge "
         "and one down the RIGHT third. The blue-black glass fills the CENTRE with the lamp's "
         "reflected flame a small sharp point on the line of the upper third. Below it the faint "
         "pale path runs from the BOTTOM LEFT corner to the black hills across the middle, and the "
         "rest of the frame is black.",
         "runout", 1.2, 0.0),
}
"""Five shots inserted AFTER the named BASE index. The parlour volume and open hand
carry narration the first count had no room for; the wide at the gate follows
the back; the lamp and the window are the evening's two objects."""


def with_extra(base: list, extra: dict) -> list:
    out = []
    for i, shot in enumerate(base):
        out.append(shot)
        if i in extra:
            out.append(extra[i])
    return out


# (kind, speaker, text, shot) -- shot numbers are the FINAL numbering, after EXTRA
LINES = [
    ("narration", "john_watson", "There was a thing in Utah that year that nobody named above a whisper.", 0),
    ("narration", "john_watson", "A man who spoke against the Church went out of his door and did not come back.", 1),
    ("narration", "john_watson", "The lonely ranches had a name for the riders. The Avenging Angels.", 2),
    ("narration", "john_watson", "Three weeks after Jefferson Hope rode for Nevada, John Ferrier heard his own gate click.", 3),
    ("narration", "john_watson", "A stout sandy-haired man was coming up the path, and Ferrier knew him at once.", 4),
    ("narration", "john_watson", "It was Brigham Young himself, and a visit from the Prophet boded no man any good.", 5),
    ("narration", "john_watson", "He took Ferrier's greeting coldly and went past him into the house.", 6),
    ("dialogue", "brigham_young", "Brother Ferrier. Where are your wives?", 7),
    ("narration", "john_watson", "Ferrier had never married, and had never said why. He had his daughter.", 8),
    ("narration", "john_watson", "The true believers had fed him in the desert and made him rich, and Young said so.", 9),
    ("narration", "john_watson", "It was of the daughter that the Prophet had come to speak.", 10),
    ("narration", "john_watson", "There were stories, he said, that she was promised to a Gentile.", 11),
    ("narration", "john_watson", "And the thirteenth rule of Joseph Smith let no maiden of the faith wed outside it.", 12),
    ("dialogue", "brigham_young", "Stangerson has a son, and Drebber has a son. Let her choose.", 13),
    ("dialogue", "john_ferrier", "You will give us time. My daughter is very young.", 14),
    ("narration", "john_watson", "She should have a month, he said, and at the end of it her answer.", 15),
    ("dialogue", "brigham_young", "It were better you and she lay bleached skeletons on the Sierra Blanco than defy the Holy Four.", 16),
    ("narration", "john_watson", "His voice rang through the house, and his daughter heard every word of it.", 17),
    # shot 18: silent -- the threat lands on Ferrier's face
    ("narration", "john_watson", "Ferrier heard his heavy step going away down the shingle.", 19),
    ("narration", "john_watson", "The Council of Four had decided it, and the girl had a month.", 20),
    ("narration", "john_watson", "He sat on till the lamp was lit, and then a soft hand was laid on his.", 21),
    ("dialogue", "lucy_ferrier", "Oh, father, what shall we do?", 22),
    ("dialogue", "john_ferrier", "Don't you scare yourself. We'll fix it up somehow.", 23),
    ("narration", "john_watson", "A sob and a squeeze of his hand was her only answer.", 24),
    ("narration", "john_watson", "There was a party leaving for Nevada in the morning. He would send Hope word.", 25),
    ("narration", "john_watson", "If he knew the young man, he would be back at a speed to whip the telegraph.", 26),
    ("narration", "john_watson", "She laughed through her tears, and one heard such stories about those who opposed the Prophet.", 27),
    ("dialogue", "john_ferrier", "I'm a free-born American, and too old to knuckle under.", 28),
    ("narration", "john_watson", "They had a clear month, he said. At the end of it they would leave Utah.", 29),
    ("dialogue", "lucy_ferrier", "But they won't let us leave.", 30),
    # shots 31, 32, 33: silent -- the answer is a picture
]

BEDS = [
    {"from_shot": 0, "tone": "uneasy"},
    {"from_shot": 3, "tone": "plain"},
    {"from_shot": 7, "tone": "grave"},
    {"from_shot": 16, "tone": "thrilling"},
    {"from_shot": 23, "tone": "light"},
    {"from_shot": 28, "tone": "uneasy"},
]

TURNS = {16: "prosperous and let alone -> marked", 30: "a plan to run -> the door already shut"}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, frame, motion, camera, at_rest, section, beat, coda) in enumerate(with_extra(S, EXTRA)):
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces),
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=10, title="John Ferrier Talks with the Prophet",
                question="Today, can John Ferrier say no to the Prophet?",
                aspect="1:1", where=WHERE, light=LIGHT, protagonist="john_ferrier",
                beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words "
          f"-> {words / 3.0:.0f}s projected; dialogue {said / words:.1%}; "
          f"speakers {sorted({l['speaker'] for l in doc['lines']})}")
    print(OUT)
