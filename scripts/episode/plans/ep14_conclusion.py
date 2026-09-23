r"""Episode 14 -- "The Conclusion", Part Two chapter 7.  The last episode.

THE BRICK. One event: the evening after Hope's death, when Holmes shows how
simple it was and the newspaper gives the credit away.

  QUESTION  Today, can Watson see that Holmes gets the credit he has earned?
  TURN      shot 17, Watson's own decision, on his own face: "Your merits should
            be known. If you won't publish the case, I will."  "a friend who
            listens -> the man who will write it down".
  BUTTON    shot 22, the world's answer and the last line, not the lead's: Holmes
            laughing over the Echo -- "That's the result of all our Study in
            Scarlet: to get them a testimonial!"  One silent shot after it:
            Watson's pen over his journal by the lamp.

The reasoning is SHOWN in the places it was done -- the ruts in the road, the
two men's prints in the clay, the ring on the boards, the cab rank the street
boys searched -- with the narrator carrying Holmes's chain in his own words,
because a chapter of explanation told as dialogue would put 80 % of the words
in Holmes's mouth against a wall of 20.

Two speakers: the narrator (who speaks his own turn) and Holmes.  Hope is on
screen once, dead with a smile, and silent.  The newspaper is folded with its
print away from the lens, and the journal page is seen edge-on: the owner's
rule is that nothing drawn carries lettering.

Rooms match the episodes that drew them first: the sitting-room's mantelpiece in
the LEFT wall and its two windows in the far wall (ep03); the Lauriston front
room's tall curtainless window in the far wall and its marble mantelpiece at the
LEFT (ep03).
"""
import json
from pathlib import Path

OUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio"
           r"\library\20260822113400_a-study-in-scarlet\episodes\ep14\plan.json")

WHERE = "London, March 1881"
LIGHT = "low raking lamplight, deep black shadow"

SETUPS = {
    "cell_dawn": dict(
        described=("Interior, inside a bare stone police cell at dawn in March 1881, the camera within the "
                   "cell with whitewashed stone walls closed on all four sides: a plank bed fixed along the "
                   "right wall, a floor of grey stone flags, a heavy iron-bound door in the left wall, a "
                   "small high barred window near the top of the far wall; the grey dawn through the barred "
                   "window is the only light and it comes from the top left, high and cold, in a pale square "
                   "across the flags and the edge of the plank bed, and leaves the door, the corners and the "
                   "lower walls black"),
        cast=["jefferson_hope"], landmark="the small high barred window", landmark_at="far_end",
        landmark_size="is the height of a hand",
        route="from the iron-bound door across the stone flags to the plank bed under the window",
        geometry=("The small barred window stands high in the far wall at the TOP LEFT of the frame with "
                  "the grey dawn in it. The plank bed runs along the RIGHT edge at the height of a man's knee. "
                  "The stone flags fill the BOTTOM half with the pale square of dawn light across the CENTRE. "
                  "The iron-bound door is black at the LEFT edge and the corners are black."),
        crowd="", outdoors=False, props=[]),
    "sitting_room_evening": dict(
        described=("Interior, inside the hearth end of the first-floor sitting-room of 221B Baker Street on "
                   "a March evening in 1881, the camera within the room with walls closed on all four sides: "
                   "a white marble mantelpiece over a black iron grate with a coal fire burning in the left "
                   "wall, two broad sash windows with their curtains drawn in the far wall, a red patterned "
                   "Turkey carpet, buff striped wallpaper, two worn armchairs facing each other at the hearth, "
                   "a small round table with a lit oil lamp beside the right-hand chair, a writing desk under "
                   "the far windows; the coal fire and the oil lamp are the only light and they come from the "
                   "left, low and warm, on the two faces, the chair backs and the carpet at the hearth, and "
                   "leave the far windows, the writing desk and the corners black"),
        cast=["sherlock_holmes", "john_watson"], landmark="the white marble mantelpiece over the grate",
        landmark_at="start", landmark_size="is half the height of the frame",
        route="from the hearth across the Turkey carpet to the writing desk under the windows",
        geometry=("The white marble mantelpiece and its burning grate hold the LEFT edge of the frame from "
                  "the TOP third to the carpet. The two worn armchairs face each other across the CENTRE of "
                  "the lower half with the lamp on its round table at the RIGHT third. The curtained windows "
                  "stand black in the far wall across the TOP third and the red carpet fills the BOTTOM edge."),
        crowd="", outdoors=False, props=[]),
    "garden_path_morning": dict(
        described=("The front garden of a shut-up brick house off the Brixton Road on a wet grey morning in "
                   "March 1881: a narrow path of yellow clay running from an open iron gate up to the front "
                   "door between two strips of sickly grass, puddles standing in the clay, a low brick wall "
                   "with wooden rails along the street, the muddy roadway beyond it cut with wheel ruts, the "
                   "house front dark with every blind drawn; the grey overcast is the only light and it comes "
                   "low from the left, soft and cold, over the wet clay, the puddles and the ruts, and leaves "
                   "the doorway, the house front and the wall's shadow side black"),
        cast=[], landmark="the dark doorway of the house", landmark_at="far_end",
        landmark_size="is the height of a finger",
        route="from the rutted roadway through the iron gate along the clay path to the doorway",
        geometry=("The muddy roadway with its ruts crosses the BOTTOM third of the frame. The low brick wall "
                  "and its open iron gate stand across the middle with the yellow clay path running from the "
                  "gate up the CENTRE to the dark doorway at the CENTRE of the upper third. The house front "
                  "rises black across the TOP edge and the grey light falls from the LEFT."),
        crowd="", outdoors=True, props=[]),
    "lauriston_front_room": dict(
        described=("Interior, inside the empty front room of the same shut-up house on the grey morning, "
                   "the camera within the room with walls closed on all four sides: bare floorboards thick "
                   "with dust, walls of cheap flaring yellow paper peeling in strips and blotched with "
                   "mildew, a mantelpiece of imitation white marble in the left wall, a single tall curtainless "
                   "window in the centre of the far wall; the grey daylight through the tall window is the "
                   "only light and it comes from the far wall, low and cold, along the dusty boards, and "
                   "leaves the near corners, the ceiling and the wall beside the door black"),
        cast=["sherlock_holmes"], landmark="the tall curtainless window in the far wall", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the doorway across the dusty boards to the tall window",
        geometry=("The tall curtainless window stands in the CENTRE of the far wall across the upper half of "
                  "the frame and gives all the light. The imitation marble mantelpiece holds the LEFT edge. "
                  "The dusty floorboards run from the BOTTOM edge away to the far wall with the window's grey "
                  "light along them. The near corners and the ceiling are black."),
        crowd="", outdoors=False, props=[]),
    "cab_rank_afternoon": dict(
        described=("A London cab rank beside a railed square on a raw grey afternoon in March 1881: a row of "
                   "four-wheeled cabs with their horses standing nose to tail along the kerb, a cabmen's "
                   "shelter hut of green-painted planks at the far end of the rank, cabmen hunched on their "
                   "boxes in caped coats, the cobbles wet, the iron railings of the square along the far "
                   "pavement; the low grey sky is the only light and it comes from the right, cold and flat, "
                   "over the wet cobbles and the horses' backs, and leaves the cabs' undersides and the "
                   "shelter's doorway black"),
        cast=[], landmark="the green cabmen's shelter hut", landmark_at="far_end",
        landmark_size="is half the height of the frame",
        route="from the first cab along the rank to the green cabmen's shelter",
        geometry=("The row of cabs and horses runs along the kerb from the BOTTOM RIGHT to the CENTRE of the "
                  "frame. The green cabmen's shelter stands at the far end of the rank at the CENTRE of the "
                  "upper third. The iron railings run along the LEFT third and the wet cobbles fill the BOTTOM "
                  "edge. The grey light falls from the RIGHT onto the horses' backs."),
        crowd=("Ragged street boys in torn jackets run between the cabs in twos and threes, cabmen sit hunched "
               "on their boxes, and the horses stamp and toss their heads."),
        outdoors=True, props=[]),
}

# (setup, size, faces, path, frame, motion, camera, at_rest, section)
S = [
    # 0 HOOK -- the cell at dawn
    ("cell_dawn", "wide", [], 0.2,
     "Wide of the bare stone cell at dawn: Jefferson Hope in the long brownish driving coat lying stretched "
     "on his back on the grey stone flags beside the plank bed, his hands open at his sides, the grey dawn "
     "falling from the small barred window high in the far wall in a pale square across him.",
     # A PUSH IS THE ONE MOVE THAT CHANGES THE SHOT'S SIZE, and the size is what
     # the cut is built from.  Measured on this reel: the push ran until an
     # eight-second WIDE of the whole cell ended as a close-up of the dead face,
     # which is shot 1's framing, so shot 0 cut into shot 1 on the same picture.
     # A pan holds the wide for its whole length.
     "The camera pans right across the cell over the whole shot, travelling a hand's breadth; the grey "
     "square of dawn widens across the stones; dust turns in the window's light; the light climbs the edge "
     "of the plank bed a hand's breadth.",
     "at the iron-bound door at a standing man's eye, four long strides from him, a 35mm lens. The dawn "
     "comes from the TOP LEFT through the barred window and leaves the corners and the lower walls black",
     "Jefferson Hope lies across the CENTRE of the lower half of the frame on the flags, the height of a "
     "hand, in the pale square of dawn. The barred window stands at the TOP LEFT, the plank bed runs along "
     "the RIGHT edge and the corners are black.",
     "hook"),
    # 1 -- the placid smile
    ("cell_dawn", "close", ["jefferson_hope"], 0.5,
     "Close on Jefferson Hope's face lying on the grey stone flags, the eyes closed, the full black beard, a "
     "placid smile on the lips, the grey dawn from the top left across the brow.",
     # NOTHING ON THE DEAD MAN MOVES.  This clause was "a strand of black hair
     # stirs on the stone", which the owner caught in the reference reel as the
     # corpse moving, and which L4 refuses anyway because `stir` is not a
     # body-scale act.  The light is the only mover a dead face can have, and
     # `crosses` is in ACTS, so the block carries an action without animating him.
     "The camera tilts down across the whole shot, travelling a finger's breadth; the grey flags keep the "
     "frame behind his head; the dawn light crosses his brow from the top left and lowers down his cheek.",
     "over him at the height of a kneeling man's eye, an arm's length from his face, a 90mm lens. The dawn "
     "comes from the TOP LEFT onto his brow and leaves the flags beyond his head black",
     "Jefferson Hope's face fills the CENTRE of the frame, half the frame height, from the beard at the "
     "BOTTOM third to the black hair at the TOP edge, lit from the TOP LEFT. The grey flags lie behind his "
     "head and are black at the RIGHT edge.",
     "setup"),
    # 2 -- the open hand
    ("cell_dawn", "insert", [], 0.8,
     "Insert on Jefferson Hope's bare brown hand lying open on the grey stone flags, the cuff of the brownish "
     "driving coat, the square of grey dawn light falling across the fingers.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the open hand keeps the "
     "frame's centre; dust settles on the stone; the dawn light spreads a finger's breadth across the fingers.",
     "beside the plank bed at the height of the flags, an arm's length from the hand, a 90mm lens. The dawn "
     "comes from the TOP LEFT onto the fingers and leaves the flags beyond black",
     "The open hand lies at the CENTRE of the frame on the flags, the height of a hand, in the square of "
     "light. The coat's cuff comes in from the LEFT edge and the flags are black across the TOP third.",
     "setup"),
    # 3 -- the sitting-room
    ("sitting_room_evening", "wide", [], 0.1,
     "Wide of the sitting-room at 221B Baker Street in the evening: Sherlock Holmes in the bottle-green "
     "velvet jacket in the worn armchair at the right of the hearth, John Watson in his tweed waistcoat in "
     "the armchair at the left, the coal fire in the marble grate, the oil lamp on the round table, the "
     "curtained windows black.",
     "The camera pushes in on the hearth across the whole shot, travelling a hand's breadth; the coal fire "
     "flares in the grate; the lamp flame steadies; Holmes's long hand lifts off the chair arm.",
     "at the writing desk at a seated man's eye, four long strides from the hearth, a 35mm lens. The fire "
     "and the lamp come from the LEFT onto the two men and leave the windows and the corners black",
     "The two armchairs face each other across the CENTRE of the lower half, Holmes at the RIGHT third and "
     "Watson at the LEFT third, each from the BOTTOM edge to the TOP third, heads a fifth of the frame "
     "height. The marble mantelpiece holds the LEFT edge and the windows are black across the TOP third.",
     "setup"),
    # 4 -- what people believe
    ("sitting_room_evening", "medium_close", ["sherlock_holmes"], 0.2,
     "Medium close of Sherlock Holmes in the worn armchair, the lean pale face and high forehead in the "
     "firelight from the left, a bitter half smile, the bottle-green velvet jacket, one long hand raised.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the black window keeps the "
     "frame behind him; his mouth tightens on the words; his raised hand turns over a hand's breadth.",
     "across the hearth level with his eyes, two long strides from him, a 50mm lens. The fire comes from "
     "the LEFT onto his face and leaves the curtained window behind him black",
     "Sherlock Holmes's head and shoulders fill the CENTRE of the frame from the TOP third to the green "
     "velvet at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The curtained "
     "window is black behind him.",
     "friction"),
    # 5 -- Watson: simple!
    ("sitting_room_evening", "medium_close", ["john_watson"], 0.3,
     "Medium close of John Watson sitting bolt upright in the worn armchair in his tweed waistcoat with the "
     "watch chain across it, both bare hands gripping the chair arms, astonishment on him, the coal fire "
     "glowing at the left edge of frame.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the fire keeps the left "
     "edge; his brows come up on the words; his hands push him up a finger's breadth off the cushion.",
     "from Holmes's chair across the hearth at a seated man's eye, two long strides from him, a 50mm lens. "
     "The fire comes from the LEFT onto his waistcoat and leaves the chair back behind him black",
     "John Watson's head, shoulders and waistcoat fill the CENTRE of the frame from the TOP third to his "
     "hands on the chair arms at the BOTTOM edge, his head a third of the frame's height. The fire glows at "
     "the LEFT edge and the chair back is black behind him.",
     "friction"),
    # 6 -- reason backwards
    ("sitting_room_evening", "medium_close", ["sherlock_holmes"], 0.4,
     "Medium close of Sherlock Holmes leaning forward in the armchair with his long fingertips pressed "
     "together before his chin, the pale face intent in the firelight from the left, the lamp at the right "
     "of frame.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the lamp keeps the right "
     "third; his fingertips part on the words; his hands open a hand's breadth toward Watson.",
     "beside the lamp table level with his eyes, two long strides from him, a 50mm lens. The fire comes "
     "from the LEFT onto his face and leaves the wall behind him black",
     "Sherlock Holmes's head and shoulders fill the CENTRE of the frame from the TOP third to his hands at "
     "the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The lamp glows at the "
     "RIGHT third and the wall is black behind him.",
     "friction"),
    # 7 -- the ruts
    ("garden_path_morning", "insert", [], 0.1,
     "Insert on two narrow wheel ruts pressed deep in the mud of the roadway at the kerb, grey water "
     "standing in them, the edge of the brick kerbstone at the top of frame.",
     # A PAN, BECAUSE THE DIRECTION IS THE ONLY PART OF A MOVE THAT IS OBEYED.
     # This read "tilts up ... travelling a finger's breadth", and the take
     # travelled until it was looking at the skyline -- where the cell holds
     # nothing, so the model invented a house, and the house it invented was a
     # tidy occupied terrace that contradicts shot 9's boarded-up one in the
     # same setup.  A camera pointed down at the roadway can overrun as far as
     # it likes and still only find more roadway.
     "The camera pans right along the kerb across the whole shot, travelling a finger's breadth; the two "
     "ruts keep the frame's centre; a drop falls into the water in one rut; the ripple spreads a finger's "
     "breadth.",
     "over the roadway at the height of a stooping man's eye, an arm's length from the ruts, a 90mm lens. "
     "The grey light comes from the LEFT along the ruts and leaves their far walls black",
     "The two narrow ruts run from the BOTTOM edge up the CENTRE of the frame a hand's width apart with grey "
     "water in them. The kerbstone crosses the TOP third and the ruts' far walls are black.",
     "transition"),
    # 8 -- the two men's prints
    ("garden_path_morning", "insert", [], 0.4,
     "Insert on the yellow clay path with two lines of bootprints side by side: large deep prints set a "
     "long stride apart, and beside them small narrow prints of a well-made pointed boot, puddles in the "
     "clay.",
     # The same fault and the same fix as shot 7: tilting UP off a ground-level
     # insert aims the overrun at the skyline.  Panning across the prints keeps
     # the clay filling the frame however far the move runs, and the house is
     # shot 9's to reveal.
     "The camera pans left across the line of prints over the whole shot, travelling a finger's breadth; "
     "the two lines of prints keep the frame's centre; water seeps into the deepest print; a drop falls "
     "into a puddle.",
     # STRAIGHT DOWN, because the pan alone did not save this one.  At a
     # stooping man's eye the lens still looks ALONG the path, so a sideways
     # overrun swept across the grass and arrived at the house anyway -- and
     # invented the wrong house, an occupied terrace against shot 9's boarded-up
     # one.  Pointed at the ground, every direction of overrun finds more clay.
     "directly above the path looking straight down at the clay, an arm's length from the prints, a 90mm "
     "lens. "
     "The grey light comes from the LEFT across the prints and leaves their heels black",
     "The two lines of prints run from the BOTTOM edge up the CENTRE of the frame, the large ones at the "
     "LEFT third a stride apart and the small ones at the RIGHT third, each print the height of a finger. "
     "The yellow clay fills the frame and the heels of the prints are black.",
     "transition"),
    # 9 -- the path to the door
    ("garden_path_morning", "wide", [], 0.7,
     "Wide up the yellow clay path through the open iron gate to the dark doorway of the shut-up brick "
     "house, the two lines of prints along the path, the sickly grass, the puddles grey under the "
     "overcast, every blind drawn.",
     "The camera pushes in up the path across the whole shot, travelling a hand's breadth; the rain dimples "
     "the puddles; the iron gate swings a finger's breadth on its hinge; the grey sky brightens a shade.",
     "at the gate at a standing man's eye, a 35mm lens. The grey light comes from the LEFT over the clay "
     "and leaves the doorway and the house front black",
     "The yellow clay path runs from the open gate at the BOTTOM CENTRE up to the dark doorway at the "
     "CENTRE of the upper third, the height of a finger. The house front rises black across the TOP edge "
     "and the sickly grass lines both sides of the path.",
     "transition"),
    # 10 -- Holmes on his knees
    ("lauriston_front_room", "medium", ["sherlock_holmes"], 0.3,
     "Medium of Sherlock Holmes on his knees on the dusty floorboards in the bottle-green velvet jacket, a "
     "round brass-rimmed magnifying lens in his hand held close over the boards, the lean face bent to it, "
     "the tall window grey behind him.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the tall window keeps the "
     "frame behind him; the lens travels a hand's breadth along the boards; his head bends lower after it.",
     "on the boards at the height of a kneeling man's eye, three long strides from him, a 35mm lens. The "
     "grey daylight comes from the far window behind him at the CENTRE and leaves the near corners and the "
     "ceiling black",
     "Sherlock Holmes kneels at the CENTRE of the frame from the BOTTOM edge to the middle, his head a "
     "quarter of the frame height, the lens over the boards. The tall window stands grey behind him across "
     "the upper half and the near corners are black.",
     "friction"),
    # 11 -- the ring on the boards
    ("lauriston_front_room", "insert", [], 0.5,
     "Insert on a small plain gold wedding ring lying on the dusty floorboards in the grey light from the "
     "window, a long pale forefinger with a white sticking plaster round its middle joint reaching toward "
     "it from the right.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the ring keeps the "
     "frame's centre; the forefinger comes a finger's breadth nearer; the ring rocks on the board.",
     "over the boards at the height of a kneeling man's chest, an arm's length from the ring, a 90mm lens. "
     "The grey daylight comes from the far window at the TOP of the frame and leaves the gaps between the "
     "boards black",
     "The gold ring lies at the CENTRE of the frame on the dusty board, the height of a thumbnail. The pale "
     "forefinger with its plaster comes in from the RIGHT edge and the gaps between the boards are black "
     "lines across the frame.",
     "friction"),
    # 12 -- the lens at the marks
    ("lauriston_front_room", "medium_close", ["sherlock_holmes"], 0.7,
     "Medium close of Sherlock Holmes stooped by the tall window with the brass-rimmed lens held up to one "
     "eye, the other eye narrowed, the lean pale face intent, the grey window light on his cheek.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the grey window keeps the "
     "frame behind him; his narrowed eye closes; his hand brings the lens down a hand's breadth to his chest.",
     "beside the window level with his eyes, two long strides from him, a 50mm lens. The grey daylight "
     "comes from the window at the RIGHT onto his cheek and leaves the wall behind him at the LEFT black",
     "Sherlock Holmes's head and shoulders fill the CENTRE of the frame from the TOP third to the green "
     "velvet at the BOTTOM edge, his head a third of the frame's height, the lens at his eye, lit from the "
     "RIGHT. The yellow paper is black behind him at the LEFT.",
     "friction"),
    # 13 -- the cab rank
    ("cab_rank_afternoon", "wide", [], 0.2,
     "Wide down a London cab rank on a raw grey afternoon: four-wheeled cabs and their horses standing nose "
     "to tail along the kerb, cabmen hunched on the boxes in caped coats, ragged street boys running "
     "between the cabs, the green cabmen's shelter at the far end, the iron railings of the square along "
     "the left.",
     "The camera pushes in along the rank across the whole shot, travelling a hand's breadth; a horse "
     "tosses its head; the ragged boys run between the cabs at a running pace; a cabman turns on his box.",
     "on the kerb at the head of the rank at a standing man's eye, a 35mm lens. The grey light comes from "
     "the RIGHT onto the horses' backs and leaves the cabs' undersides black",
     "The row of cabs and horses runs from the BOTTOM RIGHT to the CENTRE of the frame. The green shelter "
     "stands at the CENTRE of the upper third, half the frame height. The railings run along the LEFT "
     "third and the ragged boys are each the height of a finger between the cabs.",
     "transition"),
    # 14 -- a boy asks a cabman
    ("cab_rank_afternoon", "medium", [], 0.5,
     "Medium of a ragged street boy in a torn jacket standing at the wheel of a four-wheeled cab with his "
     "face turned up to the cabman on the box, the cabman in a caped coat bending down to him, the horse's "
     "wet flank at the right.",
     "The camera pans left across the whole shot, travelling a hand's breadth; the horse's flank keeps the "
     "right third; the boy's hand points up the rank; the cabman leans down a hand's breadth.",
     "on the kerb at a standing man's eye, three long strides from the boy, a 35mm lens. The grey light "
     "comes from the RIGHT onto the boy's face and leaves the cab's wheel and underside black",
     "The ragged boy stands at the LEFT third of the frame from the BOTTOM edge to the middle, his head a "
     "fifth of the frame height, the cabman on the box above him at the CENTRE of the upper third. The "
     "horse's wet flank fills the RIGHT third and the cab's underside is black.",
     "transition"),
    # 15 -- the shilling
    ("cab_rank_afternoon", "insert", [], 0.8,
     "Insert on a ragged boy's bare grimy hand closing over a silver shilling in its palm, the frayed cuff "
     "of a torn jacket, the wet cobbles below.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the shilling keeps the "
     "frame's centre; the grimy fingers close over the coin; the hand pulls back a hand's breadth.",
     "beside the boy at the height of his chest, an arm's length from the hand, a 90mm lens. The grey light "
     "comes from the RIGHT onto the coin and leaves the cobbles below black",
     "The grimy hand fills the CENTRE of the frame, the height of the middle third, with the silver "
     "shilling bright in the palm. The frayed cuff comes in from the LEFT edge and the cobbles are black "
     "across the BOTTOM third.",
     "friction"),
    # 16 -- the chain
    ("sitting_room_evening", "medium", ["sherlock_holmes"], 0.5,
     "Medium of Sherlock Holmes standing at the white marble mantelpiece with one elbow on it, filling a "
     "black clay pipe from a Persian slipper, the pale face in profile toward the room, the coal fire "
     "below him at the left.",
     "The camera pushes in on the mantelpiece across the whole shot, travelling a hand's breadth; the fire flares in the grate; his thumb presses the tobacco into the bowl; his hand brings the pipe up a hand's breadth.",
     "on the carpet at a standing man's eye, three long strides from him, a 35mm lens. The fire comes from the LEFT below him onto his face and leaves the bookshelves at the RIGHT black",
     "Sherlock Holmes stands at the LEFT third of the frame from the BOTTOM edge to the TOP third, his head a quarter of the frame height, his elbow on the marble mantelpiece at the LEFT edge. The fire glows below him and the bookshelves are black at the RIGHT third.",
     "friction"),
    # 17 TURN -- Watson decides
    ("sitting_room_evening", "close", ["john_watson"], 0.6,
     "Close on John Watson on his feet by the armchair in profile facing the right edge of frame, the sunburnt face set and eager, the thin waxed moustache, the curtained window black beyond him, the firelight from the left on the back of his head and his ear.",
     # `his jaw sets` and `his head comes forward` are both under L4's floor --
     # a jaw is named in ACTS' docstring as not counting, and `comes forward` is
     # not `come up`.  Watson is on his feet and indignant, so the shoulders are
     # the honest scale for it.
     "The camera pans left across the whole shot, travelling a finger's breadth; the black window keeps the frame beyond him; his shoulders turn toward the right edge and his chin lifts a finger's breadth.",
     "across the hearth level with his eyes, an arm's length from him, a 90mm lens. The fire comes from the "
     "LEFT onto his face and leaves the bookshelves behind him black",
     "John Watson's face fills the CENTRE of the frame, half the frame height, from the moustache at the "
     "BOTTOM third to the swept-back hair at the TOP edge, lit from the LEFT. The bookshelves are black "
     "behind him.",
     "turn"),
    # 18 -- the paper handed over
    ("sitting_room_evening", "medium", ["sherlock_holmes"], 0.65,
     "Medium of Sherlock Holmes leaning across the hearth from his armchair holding out a folded newspaper "
     "to Watson, the folded side toward the lens, the pale face amused in the firelight from the left, "
     "the lamp at the right.",
     "The camera pushes in on the folded paper across the whole shot, travelling a hand's breadth; the fire "
     "flares; the paper comes across the hearth a hand's breadth; his long fingers tap its fold.",
     "at the side of the hearth at a seated man's eye, three long strides from him, a 35mm lens. The fire "
     "comes from the LEFT onto his face and leaves the curtained windows black",
     "Sherlock Holmes leans out of the armchair at the RIGHT third of the frame from the BOTTOM edge to the "
     "TOP third, his head a quarter of the frame height, the folded paper held out at the CENTRE. The lamp "
     "glows at the RIGHT edge and the windows are black across the TOP third.",
     "payoff"),
    # 19 -- the folded paper
    ("sitting_room_evening", "insert", [], 0.7,
     "Insert on a folded newspaper in John Watson's bare sunburnt hands on his knee, the fold toward the "
     "lens, the tweed waistcoat and watch chain behind it, the firelight from the left on the paper's edge.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the folded paper keeps "
     "the frame's centre; the paper's corner lifts in the fire's draught; his thumb presses the fold flat.",
     "beside the armchair at the height of his chest, an arm's length from the paper, a 90mm lens. The fire "
     "comes from the LEFT onto the paper's edge and leaves the waistcoat behind it black",
     "The folded paper lies across the CENTRE of the frame in the two bare hands, the height of the middle "
     "third. The tweed waistcoat and its watch chain fill the TOP third and are black beyond the firelight.",
     "payoff"),
    # 20 -- Watson reading
    ("sitting_room_evening", "medium_close", ["john_watson"], 0.75,
     "Medium close of John Watson in the armchair reading the folded paper held up before his chest, the "
     "sunburnt face darkening, the brows drawn down, the firelight from the left.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the black bookshelves keep "
     "the frame behind him; his brows draw down; the paper comes down a hand's breadth from his face.",
     "across the hearth level with his eyes, two long strides from him, a 50mm lens. The fire comes from the "
     "LEFT onto his face and leaves the bookshelves behind him black",
     "John Watson's head and shoulders fill the CENTRE of the frame from the TOP third to the folded paper "
     "at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The bookshelves are "
     "black behind him.",
     "payoff"),
    # 21 -- the crumpled edge
    ("sitting_room_evening", "insert", [], 0.8,
     "Insert on John Watson's bare sunburnt fist crumpling the edge of the folded newspaper on the arm of "
     "the worn chair, the firelight from the left on the knuckles.",
     # `crumples` and `tightens` are finger work, which ACTS excludes by name.
     # The whole fist leaving the chair arm is the same beat at body scale, and
     # `lifts` is in ACTS.
     # THE ACTION LEADS, because this take came back frozen for its first 1.75 s
     # (DQ frozen-at-start HARD).  The lift was the last clause of four, so the
     # model had three clauses' worth of nothing to do before it began.
     "The camera tilts up across the whole shot, travelling a finger's breadth, and the fist lifts off the "
     "chair arm a hand's breadth from the first frame; the paper's edge crumples in the fingers; the fist "
     "keeps the frame's centre.",
     "beside the chair arm at the height of his chest, an arm's length from the fist, a 90mm lens. The fire "
     "comes from the LEFT onto the knuckles and leaves the chair's far side black",
     "The fist and the crumpled paper fill the CENTRE of the frame, the height of the middle third, on the "
     "worn chair arm. The chair's far side is black at the RIGHT edge.",
     "payoff"),
    # 22 BUTTON -- a testimonial
    ("sitting_room_evening", "medium_close", ["sherlock_holmes"], 0.9,
     "Medium close of Sherlock Holmes laughing in the worn armchair, the lean pale face creased with it, "
     "the head thrown back against the chair, the bottle-green velvet jacket, the firelight from the left.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the black window keeps the "
     "frame behind him; his mouth opens on the words; his head comes forward off the chair back a hand's "
     "breadth.",
     "across the hearth level with his eyes, two long strides from him, a 50mm lens. The fire comes from the "
     "LEFT onto his face and leaves the curtained window behind him black",
     "Sherlock Holmes's head and shoulders fill the CENTRE of the frame from the TOP third to the green "
     "velvet at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The curtained "
     "window is black behind him.",
     "button"),
    # 23 -- silent runout: the journal
    ("sitting_room_evening", "medium", ["john_watson"], 1.0,
     "Medium of John Watson at the writing desk under the curtained windows, a steel pen in his bare "
     "sunburnt hand over a thick leather journal lying open with its pages edge-on to the lens, the oil "
     "lamp beside him lighting his face from the left.",
     "The camera pushes in on the desk across the whole shot, travelling a hand's breadth; the lamp flame "
     "steadies; the pen dips to the inkwell; his hand brings the pen down to the page.",
     "beside the hearth at a seated man's eye, three long strides from the desk, a 35mm lens. The lamp "
     "comes from the LEFT onto his face and leaves the curtains behind him black",
     "John Watson sits at the CENTRE of the frame from the BOTTOM edge to the TOP third, his head a quarter "
     "of the frame height, lit from the LEFT by the lamp at the LEFT third. The open journal lies edge-on "
     "on the desk at the CENTRE of the lower third and the curtains are black behind him.",
     "runout"),
]

# (kind, speaker, text, shot)
LINES = [
    ("narration", "john_watson", "We were all to stand before the magistrates on Thursday. A higher Judge took the case first.", 0),
    ("narration", "john_watson", "The aneurism burst the night after we caught him. They found him on the floor at dawn.", 1),
    ("narration", "john_watson", "He was smiling, like a man who looks back on a useful life and his work well done.", 2),
    ("narration", "john_watson", "Next evening Holmes and I talked it over by our fire. He was bitter, then amused.", 3),
    ("dialogue", "sherlock_holmes", "The question is what you can make people believe that you have done.", 4),
    ("dialogue", "john_watson", "Simple? I call it anything but simple.", 5),
    ("dialogue", "sherlock_holmes", "The grand thing is to be able to reason backwards.", 6),
    ("narration", "john_watson", "He had begun in the road. The wheels were narrow: a cab, and no gentleman's carriage.", 7),
    ("narration", "john_watson", "On the clay path, two men: one very tall by his stride, and one in small, elegant boots.", 8),
    ("narration", "john_watson", "The tall one walked in beside the well-dressed one, and only the tall one walked out.", 9),
    ("narration", "john_watson", "There was no wound, but hatred and fear were on the dead face. Poison, then, forced on him.", 10),
    ("narration", "john_watson", "Then the ring. A murder done so slowly was a private wrong, and a woman was in it.", 11),
    ("narration", "john_watson", "A telegram to Cleveland named an old rival in love. His name was Jefferson Hope.", 12),
    ("narration", "john_watson", "And who follows a man through London best? The man who drives him. The cabman.", 13),
    ("narration", "john_watson", "So his street boys went round every cab rank in London until they found the one.", 14),
    ("narration", "john_watson", "A shilling a boy, and three days in all. He called it the simplest case he knew.", 15),
    ("narration", "john_watson", "From the road to the cab rank, every link held. There was not one break in the chain.", 16),
    ("dialogue", "john_watson", "Your merits should be known. If you won't publish the case, I will.", 17),
    ("narration", "john_watson", "He only smiled at that, and handed me the evening paper across the hearth.", 18),
    ("narration", "john_watson", "The public, it said, had lost a sensational treat now that the man Hope was dead.", 19),
    ("narration", "john_watson", "The credit for his capture went to the Scotland Yard officials, Lestrade and Gregson.", 20),
    ("narration", "john_watson", "And Mr. Sherlock Holmes, an amateur, might learn something in time from such teachers.", 21),
    ("dialogue", "sherlock_holmes", "That's the result of all our Study in Scarlet: to get them a testimonial!", 22),
    # shot 23: silent -- the journal
]

BEDS = [
    {"from_shot": 0, "tone": "grave"},
    {"from_shot": 3, "tone": "plain"},
    {"from_shot": 7, "tone": "uneasy"},
    {"from_shot": 13, "tone": "thrilling"},
    {"from_shot": 16, "tone": "plain"},
]

TURNS = {17: "a friend who listens -> the man who will write it down",
         22: "a case solved -> the credit given away"}

# (beat_s, coda_s) by shot; every other shot is 0.5 / 0.0
BEATS = {0: (0.6, 0.3), 2: (0.8, 0.3), 3: (0.6, 0.0), 5: (0.8, 0.0), 6: (0.8, 0.3), 9: (0.6, 0.3),
         12: (0.6, 0.0), 15: (0.6, 0.3), 16: (0.6, 0.0), 17: (1.0, 0.0), 21: (1.0, 0.0), 22: (0.6, 0.0),
         23: (0.8, 1.5)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, frame, motion, camera, at_rest, section) in enumerate(S):
        beat, coda = BEATS.get(i, (0.5, 0.0))
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces),
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=14, title="The Conclusion",
                question="Today, can Watson see that Holmes gets the credit he has earned?",
                aspect="1:1", where=WHERE, light=LIGHT, protagonist="john_watson", answer="line 20",
                beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


from studio import episode_home  # noqa: E402


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    episode_home.write_plan(OUT, doc)
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words "
          f"-> {words / 3.0:.0f}s projected; dialogue {said / words:.1%}; "
          f"speakers {sorted({l['speaker'] for l in doc['lines']})}")
    print(OUT)
