r"""Episode 11 — "A Flight for Life", Part Two chapter 4.

THE BRICK. One event split by the title card.

  QUESTION  Tonight, can John Ferrier get his daughter out of Utah?
  TURN      shot 13, ~52 % in: the scratching at the door, and Ferrier draws the
            bolt himself and throws it open on the night -- hunted behind a bolt
            -> the door opened by his own hand. Then a man flat on the threshold,
            and Jefferson Hope's face in the candle.
  BUTTON    shot 25, the sentinel on the rock, the world's answer and the last
            line: "Pass, and the Lord go with you." One silent shot after it.

Written against docs/analysis/ep10_dq_synthesis.md, the ten-analyst read of
episode 10, and what it measured: H3 obeys the cell and the camera verb's
direction and ignores amounts, angles and absences -- so a close takes a
pull-back or a pan, an insert a tilt or a pan, a walk goes away or across to a
named thing in frame; the head fraction is the size; under a sun the shadow
has a caster at an edge; the lead speaks his own decision on his own face; the
turn shot holds the protagonist; the last line lands within six seconds of the
end; a kept-clause names a sharp static edge object and nothing else.

Four speakers: the narrator, Ferrier, Hope, and the sentinel. The two suitors
are on screen and silent; Lucy is on screen and silent.
"""
import json
from pathlib import Path

OUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio"
           r"\library\20260822113400_a-study-in-scarlet\episodes\ep11\plan.json")

WHERE = "Ferrier's farm, Utah, 1860"
LIGHT = "low sidelong light, deep black shadow"

SETUPS = {
    "farm_gate_day": dict(
        described=("The road outside the gate of John Ferrier's farm on a warm afternoon, 1860: a five-bar "
                   "gate between two square posts, the rail fence running off both ways, the shingly path "
                   "beyond it up between cut stubble to the long log house and its porch, the pine hills "
                   "dark behind the roof; the low afternoon sun comes from the left, hard and yellow, "
                   "raking across the road and the stubble, and it throws the two posts' shadows long and "
                   "black across the road to the right, leaves the near side of every post black, and puts "
                   "the porch and the house front in the black of their own shadow under the roof"),
        cast=["john_ferrier"], landmark="the two square gate posts", landmark_at="start",
        landmark_size="is half the height of the frame",
        route="from the road at the gate up the shingly path to the porch",
        geometry=("The gate and its two square posts stand in the CENTRE of the frame with the road "
                  "crossing the BOTTOM third. The shingly path runs from the gate up to the porch small at "
                  "the CENTRE of the upper third. The posts' black shadows lie across the RIGHT half of the "
                  "road and the sunlit stubble fills the LEFT third beyond the fence. The pine hills close "
                  "the TOP edge behind the roof."),
        crowd="", outdoors=True, props=[]),
    "farm_parlour_day": dict(
        described=("Interior, inside the sitting-room of John Ferrier's log villa on a warm afternoon, "
                   "1860, the camera within the room with squared white-chinked log walls closed on all "
                   "four sides and a low plank ceiling of pale boards: one deep window in the left wall is "
                   "the only source, and the light comes from the left window alone, a hard slab of "
                   "afternoon sun lying across the scrubbed pine table and the board floor and leaving the "
                   "far corners, the black iron stove on the far wall and the space under the ceiling in "
                   "deep shadow; a wooden rocking-chair beside the stove, two ladder-back chairs at the "
                   "table, a small square looking-glass on the wall beside the window, a rag rug on the "
                   "boards, the log walls warm where the slab touches them and black beyond it"),
        cast=["john_ferrier", "lucy_ferrier", "joseph_stangerson_young", "enoch_drebber_young"],
        landmark="the deep window in the left wall", landmark_at="start",
        landmark_size="is half the height of the frame",
        route="from the window across the pine table to the iron stove on the far wall",
        geometry=("The deep window stands along the LEFT edge of the frame with its slab of hard light "
                  "lying across the middle of the frame from left to right. The scrubbed pine table stands "
                  "in the CENTRE of the frame in that light. The black iron stove and the rocking-chair "
                  "stand in the RIGHT third against the far log wall. The pale ceiling boards close the "
                  "TOP edge in shadow and the rag rug lies in the BOTTOM third on the boards."),
        crowd="", outdoors=False, props=[]),
    "parlour_night": dict(
        described=("Interior, inside the same sitting-room of John Ferrier's log villa late at night, "
                   "1860, the camera within the room with squared white-chinked log walls closed on all "
                   "four sides: the one oil lamp burning low on the scrubbed pine table is the only light "
                   "and it comes from the lamp alone, low and yellow, on the faces at the table and the "
                   "near log wall, the deep window a blue-black square in the left wall, the iron stove "
                   "and the far corners in darkness, a plate of cold meat and bread on the table beside "
                   "the lamp, two ladder-back chairs, the rag rug a dark shape on the boards, everything "
                   "past an arm's length from the lamp black"),
        cast=["john_ferrier", "jefferson_hope", "lucy_ferrier"], landmark="the oil lamp on the pine table",
        landmark_at="start", landmark_size="is the height of a hand",
        route="from the lamp on the table across the rag rug to the dark window",
        geometry=("The oil lamp stands on the pine table in the CENTRE of the frame and throws its light "
                  "outward across the table top to the BOTTOM third. The window is a blue-black square "
                  "along the LEFT edge. The far log wall and the iron stove are darkness across the TOP "
                  "third. The near log wall catches the lamp's warmth along the RIGHT edge and everything "
                  "past an arm's length from the lamp is black."),
        crowd="", outdoors=False, props=[]),
    "farm_door_night": dict(
        described=("Interior, the narrow hall inside the front door of John Ferrier's log villa at night, "
                   "1860, the camera within the hall with squared log walls closed on both sides and the "
                   "heavy plank door ahead with its iron bolt across it at the height of a man's chest: "
                   "one candle burning in a tin holder on a shelf behind the camera is the only light and "
                   "it comes from behind the camera alone, low and yellow, on the door planks, the bolt "
                   "and a man's back, throwing his shadow huge and black up the door; when the door "
                   "stands open, the night beyond is blue-black under bright stars with the pale garden "
                   "path, the fence and the gate faint in it and the threshold boards a pale strip"),
        cast=["john_ferrier", "jefferson_hope"], landmark="the heavy plank door with its iron bolt",
        landmark_at="start", landmark_size="fills the frame",
        route="from the hall to the threshold and the dark garden beyond the open door",
        geometry=("The plank door fills the CENTRE of the frame from the BOTTOM edge to the TOP edge with "
                  "the iron bolt crossing it at the CENTRE line. The log walls of the hall stand at the "
                  "LEFT and RIGHT edges. The candle behind the camera lights the door from the front and "
                  "throws the man's shadow up its middle. When the door is open the starry night fills "
                  "the CENTRE between the black jambs and the threshold boards cross the BOTTOM edge."),
        crowd="", outdoors=False, props=[]),
    "garden_hedge_night": dict(
        described=("The little front garden of John Ferrier's log villa at night, 1860: the side window "
                   "of the house at the near end, a strip of dug earth, the low hedge running away along "
                   "the garden's edge to a gap that opens on the cornfields, the fence and the gate off to "
                   "the left, the fields pale grey beyond under bright stars; the starlight from above and from behind the camera is "
                   "the only light, cold and blue and faint, on the tops of the hedge, the window sill and "
                   "the earth, and it leaves the side of the house, the underside of the hedge and every "
                   "crouching figure black against the pale fields"),
        cast=["john_ferrier", "jefferson_hope", "lucy_ferrier"], landmark="the gap in the hedge",
        landmark_at="far_end", landmark_size="is the height of a hand",
        route="from the side window along the hedge to the gap into the cornfields",
        geometry=("The side window of the house is a dark square at the LEFT edge of the frame with the "
                  "black wall below it. The hedge runs from the BOTTOM LEFT corner away to the gap at the "
                  "CENTRE of the upper third, its top a faint blue line and its side black. The pale fields "
                  "fill the RIGHT third and the TOP third under the stars, and the dug earth of the garden "
                  "lies black across the BOTTOM third."),
        crowd="", outdoors=True, props=[]),
    "eagle_canyon_night": dict(
        described=("The Eagle Canyon in the Utah mountains by night, 1860: a narrow rock trail along the "
                   "bed of a dried watercourse between great boulders, a black crag towering up on the "
                   "left with long basalt ribs down its face, a chaos of boulders and scree on the right, "
                   "the sky a strip of stars above; a low moon behind the crag to the left is the only "
                   "light and it comes from behind and the left, rimming the boulders and the crag's ribs "
                   "in cold silver, throwing every shadow across the trail toward the right, and leaving "
                   "the faces of the riders black under their hat brims and the trail itself pale dust "
                   "between black rocks"),
        cast=["john_ferrier", "jefferson_hope", "lucy_ferrier", "unnamed_sentinel"],
        landmark="the black crag with its basalt ribs", landmark_at="far_end",
        landmark_size="fills the frame",
        route="from the picketed horses along the watercourse trail to the sentinel's rock and beyond",
        geometry=("The black crag fills the LEFT third of the frame from the BOTTOM edge to the TOP edge "
                  "with its basalt ribs rimmed in moonlight. The trail of pale dust runs from the BOTTOM "
                  "CENTRE up between the boulders to the CENTRE of the upper third. The scree and boulders "
                  "fill the RIGHT third. The strip of stars crosses the TOP edge and every shadow lies from "
                  "the upper left toward the lower right across the trail."),
        crowd="", outdoors=True, props=[]),
}

# (setup, size, faces, path, frame, motion, camera, at_rest, section, beat, coda)
S = [
    # 0 HOOK -- two strange horses at his own gate
    ("farm_gate_day", "wide", [], 0.0,
     "Wide of the gate of Ferrier's farm on a warm afternoon, a farm gate of five rough grey split-rail timbers, weathered wood pegged to two square timber posts, two saddled horses hitched one to each post, the shingly path beyond running up to the log house, the posts' shadows black across "
     "the road.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the posts' black shadows keep the road's right half and the gate keeps the frame's centre; the near horse tosses its head; the reins swing against the post.",
     "on the road at a standing man's eye, three long strides from the gate, a 35mm lens. The low afternoon sun comes from the LEFT, lays the posts' shadows BLACK across the road and leaves each post's near face black",
     "The two square gate posts stand in the CENTRE of the frame the height of half the frame with a "
     "saddled horse hitched to each. The road crosses the BOTTOM third. The posts' black shadows lie "
     "across the RIGHT half of the road and the sunlit stubble fills the LEFT third. The log house is "
     "small at the CENTRE of the upper third.",
     "hook", 0.6, 0.4),
    # 1
    ("farm_gate_day", "medium", ["john_ferrier"], 0.3,
     "Medium of John Ferrier drawing rein at his own gate on a bay horse, in his brown felt hat and fawn "
     "coat, the two strange horses at the posts beyond him, the low sun from the left hard on his face.",
     "The camera pushes in on John Ferrier across the whole shot, travelling a hand's breadth; his horse's "
     "head comes up; his bare hand tightens on the rein; his head turns a finger's breadth to the horses "
     "at the posts.",
     "on the road beside the gate at the height of a mounted man's chest, two long strides from him, a "
     "50mm lens. The low sun comes from the LEFT and leaves the right side of his face under the hat "
     "brim's black",
     "John Ferrier sits his horse in the CENTRE of the frame from the horse's shoulder at the BOTTOM edge "
     "to the hat at the TOP third, his face a quarter of the frame height under the brim. The two hitched "
     "horses stand at the RIGHT third by the posts and the sunlit stubble fills the LEFT edge.",
     "setup", 0.5, 0.0),
    # 2
    ("farm_parlour_day", "medium", ["joseph_stangerson_young", "enoch_drebber_young"], 0.1,
     "Medium of the sitting-room with two young men in possession of it: a long pale fair-haired young "
     "man leaning back in the rocking-chair with his boots up on the black stove, and a bull-necked "
     "sandy-haired youth standing at the window with his hands in his pockets, the window sun across "
     "the table.",
     "The camera pushes in on the two men across the whole shot, travelling a hand's breadth; the "
     "rocking-chair rocks back a hand's breadth under the pale young man; the youth's fingers drum the "
     "window sill.",
     "at the door end of the room level with a standing man's chest, three long strides from the table, "
     "a 35mm lens. The window sun comes from the LEFT across the table and leaves the stove corner black",
     "The pale young man in the rocking-chair fills the RIGHT third of the frame with his boots on the "
     "black stove at the RIGHT edge. The bull-necked youth stands at the LEFT third against the bright "
     "window. The sunlit pine table crosses the BOTTOM third between them and the ceiling boards close "
     "the TOP edge in shadow.",
     "setup", 0.5, 0.0),
    # 3
    ("farm_parlour_day", "close", ["enoch_drebber_young"], 0.3,
     "Close on the bull-necked youth's broad florid face smirking at his own reflection in the small "
     "looking-glass on the wall beside the window, the window sun hard on the near cheek, the far cheek "
     "in the black of the log wall.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the looking-glass keeps the right edge and the log wall keeps the left edge; the smirk widens; his hand lifts to smooth the sandy curls.",
     "at the wall beside the looking-glass level with his eyes, an arm's length from him, a 90mm lens. The window sun comes from the RIGHT, past the looking-glass, onto his near cheek and leaves the far side of his face black",
     "The youth's florid face fills the CENTRE of the frame, half the frame height, from the loose black "
     "tie at the BOTTOM edge to the sandy curls at the TOP edge, the RIGHT cheek in hard sun and the LEFT cheek black. The small looking-glass is a bright square at the RIGHT edge with the edge of his "
     "reflection in it.",
     "setup", 0.5, 0.0),
    # 4
    ("farm_parlour_day", "medium_close", ["john_ferrier"], 0.35,
     "Medium close of John Ferrier bare-headed in the open doorway of the sitting-room, the riding whip "
     "in his bare hand, his long sun-darkened face and iron-grey beard hard in the window light, the "
     "room's black behind him.",
     "The camera pans left across the whole shot, travelling a hand's breadth; the whip's stock comes up "
     "to his chest; his jaw sets; his head comes forward a finger's breadth.",
     "at the table end of the room level with a standing man's eye, two long strides from the door, a "
     "50mm lens. The window sun comes from the LEFT onto the left side of his face and leaves the "
     "doorway black behind him",
     "John Ferrier's head and shoulders fill the CENTRE of the frame from the TOP third to the rolled sleeves at the BOTTOM edge, his head a third of the frame's height, the LEFT side of his face lit "
     "and the RIGHT side dark. The whip stands up along the RIGHT third and the black of the doorway "
     "fills the frame behind him.",
     "friction", 1.0, 0.0),
    # 5
    ("farm_parlour_day", "close", ["john_ferrier"], 0.4,
     "Close on John Ferrier's savage brown face, the iron-grey beard, the deep-set eyes narrowed, the "
     "whip's stock across the bottom of the frame in his knuckles, the window light hard on the left "
     "side of the face and the right side black.",
     "The camera pulls back from John Ferrier's face across the whole shot, travelling a hand's breadth; "
     "his brows draw down; his mouth sets hard after the words; the whip's stock lifts a finger's "
     "breadth.",
     "at the table end of the room level with his eyes, an arm's length from him, a 90mm lens. The "
     "window sun comes from the LEFT onto the left side of his face and leaves the right side black",
     "John Ferrier's face fills the CENTRE of the frame, half the frame height, from the beard at the "
     "BOTTOM third to the iron-grey hair at the TOP edge, the LEFT half in window light and the RIGHT "
     "half black. The whip's stock crosses the BOTTOM edge in his knuckles and the dark log wall fills "
     "both edges.",
     "friction", 1.0, 0.0),
    # 6
    ("farm_parlour_day", "medium", [], 0.5,
     "Medium of the open door from inside the room with the two young men going out through it, their backs to the camera, hats in their hands, the tall pale one ducking under the lintel and the bull-necked one a step behind, the black of the hall beyond them.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the door jambs keep the frame's centre and the sunlit log wall keeps the left edge; the pale one's hat comes off in his hand; the door leaf swings a hand's breadth toward the jamb behind them.",
     "at the window end of the room level with a standing man's chest, three long strides from the "
     "door, a 35mm lens. The window sun comes from the LEFT across the table and leaves the doorway "
     "black",
     "The open door fills the CENTRE of the frame from the BOTTOM edge to the TOP edge with the two men's backs in it, the pale one ahead at the CENTRE and the bull-necked one at the RIGHT third. The black hall fills the doorway behind them and the sunlit log wall stands at the LEFT edge.",
     "reaction", 0.5, 0.0),
    # 8
    ("farm_parlour_day", "insert", [], 0.6,
     "Insert on a small square of paper held in John Ferrier's bare fingers over the sunlit pine table, "
     "its blank back to the lens, a pin still through one corner, the window sun hard on the paper.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the fingers turn the "
     "paper a hand's breadth; the thumb presses its corner flat; the pin glints once.",
     "over the table at the height of a seated man's chest, an arm's length from the paper, a 90mm "
     "lens. The window sun comes from the LEFT onto the paper and leaves the table's far edge black",
     "The square of paper fills the CENTRE of the frame the height of a hand with the bare fingers holding its LEFT edge, the window's light on it from the LEFT edge and the paper's shadow lying to the RIGHT on the table. The sunlit pine table fills the BOTTOM half and the black of the room fills the TOP third.",
     "friction", 0.6, 0.0),
    # 9
    ("farm_parlour_day", "medium_close", ["john_ferrier"], 0.65,
     "Medium close of John Ferrier at the pine table reading the small square of paper, bare-headed, "
     "his brows drawn together, the window sun from the left on the paper and on one side of his face.",
     "The camera pans left across the whole shot, travelling a hand's breadth; the window keeps the left edge and the paper keeps his two hands at the bottom centre; his eyes go down the paper; his fist closes on it; his head bows a finger's breadth.",
     "at the table's far end level with his eyes, two long strides from him, a 50mm lens. The window "
     "sun comes from the LEFT onto the left side of his face and leaves the right side and the wall "
     "behind him black",
     "John Ferrier's head and shoulders fill the CENTRE of the frame from the TOP third to the sunlit table at the BOTTOM edge, his head a third of the frame's height, the LEFT side of his face lit "
     "and the RIGHT side dark. The square of paper is a bright point in his hands at the BOTTOM CENTRE.",
     "friction", 0.8, 0.0),
    # 10
    ("farm_parlour_day", "close", ["lucy_ferrier"], 0.7,
     "Close on Lucy Ferrier at breakfast in the grey-blue house dress, her chestnut hair gathered back, "
     "her face turned up to the ceiling and her bare hand coming up to point, the window sun on one "
     "cheek and the other in shadow.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the log wall keeps the frame behind her and the table's edge keeps the bottom edge; her eyes widen; her lips part; her pointing finger rises a hand's breadth.",
     "across the table level with her eyes, an arm's length from her, a 90mm lens. The window sun comes "
     "from the LEFT onto her left cheek and leaves the right cheek and the wall behind black",
     "Lucy's face fills the CENTRE of the frame, half the frame height, from the white collar at the "
     "BOTTOM edge to the chestnut hair at the TOP edge, the LEFT cheek in sun and the RIGHT cheek dark. "
     "Her raised hand comes into the RIGHT third with one finger up.",
     "friction", 0.8, 0.0),
    # 12 -> insert: the placard on the gate rail
    ("farm_gate_day", "insert", [], 0.9,
     "Insert on a small square placard nailed to the top rail of the gate in the low sun, its face blank "
     "to the lens, John Ferrier's bare hand flat on the rail beside it, a rider's dust drifting on the "
     "road beyond.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the placard keeps its nails in the top rail at the frame's centre and the post keeps the right edge; dust drifts across the empty road behind the gate; the bare hand pulls along the rail a hand's breadth and closes on the placard's corner; the corner tears a finger's breadth.",
     "at the gate at the height of the top rail, an arm's length from the placard, a 90mm lens. The low "
     "sun comes from the LEFT onto the placard and leaves the post's near face black",
     "The placard is a pale square in the CENTRE of the frame the height of a hand on the gate's top rail, "
     "which crosses the frame at the CENTRE line. The bare hand rests on the rail at the LEFT third. The "
     "road and the drifting dust fill the TOP third and the post's black face stands at the RIGHT edge.",
     "friction", 0.8, 0.0),
    # 13
    ("parlour_night", "medium_close", ["john_ferrier"], 0.1,
     "Medium close of John Ferrier alone at the pine table by the low lamp late at night, bare-headed, "
     "his head sinking toward his folded arms on the table, the lamp warm on one side of the face and "
     "the room black.",
     "The camera pushes in on John Ferrier across the whole shot, travelling a hand's breadth; his head "
     "sinks the last hand's breadth onto his arms; his shoulders shake once; the lamp flame leans.",
     "at the table's far end level with the lamp chimney, two long strides from him, a 50mm lens. The "
     "lamp is the light, from the LEFT, and leaves the right side of his face and the room black",
     "John Ferrier's bowed head and shoulders fill the CENTRE of the frame from the TOP third to the "
     "table at the BOTTOM edge, his head a third of the frame's height, warm on the LEFT and black on "
     "the RIGHT. The lamp stands at the LEFT edge and the room is black across the TOP third.",
     "spike", 1.0, 0.5),
    # 14
    ("farm_door_night", "medium", [], 0.1,
     "Medium of John Ferrier standing in the narrow hall facing the heavy plank door with its iron bolt, "
     "his back to the camera, the candle behind the camera on his shoulders and on the door, his shadow "
     "huge and black up the planks.",
     "The camera pushes in on the door across the whole shot, travelling a hand's breadth; Ferrier's "
     "head tilts a finger's breadth to listen; his hand comes up toward the bolt; his shadow climbs the "
     "planks with it.",
     "in the hall behind him at the height of his shoulders, two long strides from the door, a 35mm "
     "lens. The candle behind the camera is the light, from the FRONT, and leaves the hall's log walls "
     "black at both edges",
     "The plank door fills the CENTRE of the frame from the BOTTOM edge to the TOP edge with the iron "
     "bolt across it at the CENTRE line. John Ferrier's back stands at the LEFT third from the BOTTOM "
     "edge to the TOP third with his shadow huge up the RIGHT half of the door.",
     "spike", 1.0, 0.0),
    # 17 TURN -- his own hand opened it; now he looks down
    ("farm_door_night", "medium_close", ["john_ferrier"], 0.55,
     "Medium close of John Ferrier in the thrown-open doorway, bare-headed, the candle from behind the "
     "camera hard on his face, his iron-grey beard, his eyes level on the empty night beyond the fence, the starry black behind him.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; both black jambs keep the frame edges and the starry blue-black keeps the frame behind his head; his eyes drop to the threshold; his bare hand goes to his throat; his mouth opens a finger's breadth.",
     "in the hall level with his eyes, two long strides from him, a 50mm lens. The candle behind the "
     "camera is the light, from the FRONT, and the night behind him is blue-black under stars",
     "John Ferrier's head sits at the CENTRE of the frame a third of the frame's height, his collar at the BOTTOM third, lit from the front, with the starry night black behind him and the black jambs at the LEFT and RIGHT edges.",
     "turn", 1.0, 0.0),
    # 18 -> insert: the prone man's hand on the sill
    ("farm_door_night", "insert", [], 0.6,
     "Insert looking down at a man's bare brown hand flat on the threshold boards beside the sprawled sleeve of a brown driving coat, the candle from the hall hard on the knuckles, the starlit garden path pale beyond "
     "the fingers.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the fingers spread and "
     "grip the board's edge; the coat sleeve drags forward a hand's breadth over the sill; the "
     "knuckles whiten.",
     "in the hall at the height of a standing man's knee looking down, an arm's length from the "
     "threshold, a 90mm lens. The candle behind the camera is the light, from the FRONT, and the garden "
     "beyond is blue-black",
     "The bare hand fills the CENTRE of the frame the width of a third of the frame with the fingers "
     "toward the BOTTOM edge. The threshold board crosses the frame at the CENTRE line. The brown coat sleeve comes in from the RIGHT edge and the pale path fills the TOP third.",
     "reaction", 1.0, 0.0),
    # 19
    ("farm_door_night", "close", ["jefferson_hope"], 0.8,
     "Close on Jefferson Hope's fierce sun-browned face come up into the candlelight inside the shut "
     "door, the black beard cut close, the deep-set dark eyes on Ferrier, the hair damp and flat, the "
     "planks of the door black behind his head.",
     "The camera pulls back from Jefferson Hope's face across the whole shot, travelling a hand's "
     "breadth; his jaw sets; his hand comes up to wipe his mouth; his chin lifts a finger's breadth.",
     "in the hall level with his eyes, an arm's length from him, a 90mm lens. The candle behind the "
     "camera is the light, from the FRONT, and leaves the door planks behind him black",
     "Jefferson Hope's face fills the CENTRE of the frame, half the frame height, from the black beard "
     "at the BOTTOM third to the damp hair at the TOP edge, lit from the front. The plank door fills the "
     "frame black behind him and the shut bolt crosses the BOTTOM edge.",
     "reaction", 1.0, 0.5),
    # 20 -> insert: Hope's hands at the bread
    ("parlour_night", "insert", [], 0.3,
     "Insert on Jefferson Hope's two brown hands tearing a loaf over a plate of cold meat on the pine "
     "table beside the low lamp, the brown wool cuffs of his driving coat, the lamp's light hard on the knuckles and the "
     "table's far edge black.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the plate keeps the bottom centre and the lamp's foot keeps the left edge; one hand carries the torn half up out of the TOP edge; the other hand holds the plate; a crumb falls to the table.",
     "over the table at the height of the lamp chimney, an arm's length from the plate, a 90mm lens. "
     "The lamp is the light, from the LEFT, and leaves the far edge of the table black",
     "The two hands and the loaf fill the CENTRE of the frame the height of the middle third over the "
     "plate at the BOTTOM CENTRE. The lamp's foot is a bright column at the LEFT edge. The pine table "
     "fills the BOTTOM half and the black of the room fills the TOP third.",
     "payoff", 0.5, 0.0),
    # 21
    ("parlour_night", "close", ["jefferson_hope"], 0.4,
     "Close on Jefferson Hope's face over the plate, the black beard, the dark eyes off to the left of the lens, the lamp warm on the near side of the face and the far side black, a crust in "
     "his fist.",
     "The camera pulls back from Jefferson Hope's face across the whole shot, travelling a hand's "
     "breadth; his eyes come round into the lens on the words; his chin comes up a finger's breadth; the crust lifts to his mouth.",
     "across the table level with his eyes, an arm's length from him, a 90mm lens. The lamp is the "
     "light, from the LEFT, and leaves the right side of his face black",
     "Jefferson Hope's face fills the CENTRE of the frame, half the frame height, from the beard at the "
     "BOTTOM third to the hair at the TOP edge, the LEFT side warm in lamplight and the RIGHT side black. "
     "The crust in his fist comes into the BOTTOM RIGHT corner.",
     "payoff", 1.0, 0.0),
    # 23
    ("parlour_night", "medium_close", ["jefferson_hope"], 0.7,
     "Medium close of Jefferson Hope on his feet by the table, the brown driving coat open over the revolver butt at the front of his belt, his fierce face turned to Ferrier at the right of frame, the lamp warm on "
     "one side and the room black.",
     "The camera pans right across the whole shot, travelling a hand's breadth; his eyes hold the lens; his hand slaps the revolver butt once; his head comes forward a finger's breadth on the words.",
     "at the window end of the room level with his eyes, two long strides from him, a 50mm lens. The "
     "lamp is the light, from the LEFT, and leaves the right side of his face and the wall black",
     "Jefferson Hope's head and shoulders fill the CENTRE of the frame from the TOP edge to the belt at "
     "the BOTTOM edge, his head a third of the frame's height, the LEFT side warm and the RIGHT side "
     "black. The revolver butt is at the BOTTOM CENTRE and the lamp's glow reaches from the LEFT edge.",
     "payoff", 1.0, 0.0),
    # 24 -- the lead's decision, in his own mouth, on his own face
    ("parlour_night", "close", ["john_ferrier"], 0.9,
     "Close on John Ferrier's face at the blue-black window glass, bare-headed, the iron-grey beard, "
     "his eyes on the dark fields beyond the glass, the lamp's low light from the left on one cheek and "
     "the near side of the face black against the glass.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the blue-black glass keeps the right third and the sill keeps the bottom edge; his eyes come round from the glass to the lens; his jaw sets on the words; his hand lifts off the sill and closes.",
     "at the window level with his eyes, an arm's length from him, a 90mm lens. The lamp is the light, "
     "from the LEFT, and leaves the right side of his face black against the blue-black glass",
     "John Ferrier's face fills the CENTRE of the frame, half the frame height, from the beard at the "
     "BOTTOM third to the iron-grey hair at the TOP edge, the LEFT cheek in low lamplight and the RIGHT "
     "cheek black. The blue-black glass fills the RIGHT third behind him with one faint star in it.",
     "payoff", 1.2, 0.0),
    # 25 -> insert: boots down from the sill
    ("garden_hedge_night", "insert", [], 0.1,
     "Insert by starlight on the side window's sill with a woman's small boot coming down over it onto the dug earth, Jefferson Hope's two bare hands under the boot, the hem of her skirt, the house wall black.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the sill keeps the top third and the black house wall keeps the right edge; the boot comes down the last hand's breadth onto the earth; the hands let go; the skirt's hem falls over the boot.",
     "in the garden at the height of the sill, an arm's length from it, a 90mm lens. The starlight comes "
     "from ABOVE and behind the camera, cold and faint, and leaves the house wall black",
     "The sill crosses the frame at the TOP third with the boot and the two hands at the CENTRE of the "
     "frame the height of the middle third. The dug earth fills the BOTTOM third and the house wall is "
     "black across the TOP edge and the RIGHT edge.",
     "spike", 0.8, 0.0),
    # 26
    ("garden_hedge_night", "medium_close", ["jefferson_hope"], 0.5,
     "Medium close of Jefferson Hope flat against the black side of the hedge, the sombrero's brim over "
     "his eyes, one bare hand pressing Lucy's bowed head down beside him, her loose chestnut hair over her collar, his face turned to the gap "
     "in the hedge at the right of frame where two shadowy figures stand against the pale field.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the two shadowy figures "
     "at the gap part and go their ways left and right; Hope's hand stays flat on her hair; his chin lifts a finger's breadth.",
     "at the foot of the hedge at the height of a crouching man's eye, two long strides from him, a "
     "50mm lens. The starlight from ABOVE is the light and leaves his face black under the brim against "
     "the pale field",
     "Jefferson Hope's hat and shoulders fill the LEFT third of the frame from the BOTTOM edge to the "
     "CENTRE line, his head a third of the frame's height, black under the brim with her bowed head beside him at the BOTTOM CENTRE. The hedge's black side runs from the BOTTOM LEFT to the gap at the "
     "RIGHT third where the two shadowy figures stand against the pale field.",
     "spike", 1.0, 0.5),
    # 29
    ("eagle_canyon_night", "wide", [], 0.6,
     "Wide up the canyon trail: the file small on the pale dust below, and above them on a rock that "
     "overhangs the trail a solitary sentinel standing dark and plain against the strip of stars, a "
     "rifle upright in his hands, the moon behind the crag rimming the rock's edge.",
     "The camera tilts up across the whole shot, travelling a hand's breadth; the sentinel on the rock "
     "raises the rifle a hand's breadth; the file below halts; a horse's head comes up.",
     "on the trail behind the file at a standing man's eye, a 35mm lens. The moon comes from behind "
     "and the LEFT and rims the sentinel's rock in silver, leaving the trail below black between the "
     "boulders",
     "The sentinel stands on his rock at the CENTRE of the upper third against the strip of stars, "
     "the height of a finger, the rifle upright beside him. The black crag fills the LEFT third to the "
     "TOP edge. The three riders' backs fill the BOTTOM half of the frame on the pale dust between black boulders.",
     "friction", 0.8, 0.0),
    # 30
    ("eagle_canyon_night", "medium_close", ["unnamed_sentinel"], 0.7,
     "Medium close of the sentinel on his rock from below, a lean weathered bearded man in a battered "
     "black slouch hat and a long dark coat, the rifle upright in both bare hands, the moon behind the "
     "crag rimming his hat and shoulders and leaving his face black but for the eyes.",
     "The camera pans left across the whole shot, travelling a hand's breadth; the rifle's muzzle comes "
     "down a hand's breadth toward the trail; his head bends a finger's breadth to peer down; his mouth "
     "opens on the words.",
     "on the trail below the rock at the height of a mounted man's eye looking up, three long strides "
     "from him, a 50mm lens. The moon comes from behind and the LEFT and rims his hat and shoulders, "
     "leaving his face black but for the eyes",
     "The sentinel's hat and shoulders fill the CENTRE of the frame from the BOTTOM third to the TOP "
     "edge, his head a third of the frame's height, black under the brim with a silver rim along the "
     "LEFT side. The rifle stands up along the RIGHT third and the strip of stars fills the TOP edge.",
     "friction", 0.6, 0.0),
    # 31
    ("eagle_canyon_night", "close", ["jefferson_hope"], 0.75,
     "Close on Jefferson Hope's face under the sombrero's brim looking up at the rock, the black beard, "
     "his bare hand on the rifle at his saddle at the bottom of the frame, the moon from behind and the "
     "left rimming the brim and the cheekbone and leaving the face black but for the eyes.",
     "The camera pulls back from Jefferson Hope's face across the whole shot, travelling a hand's "
     "breadth; his eyes stay up on the rock; his hand slides a hand's breadth up the rifle's stock; his chin lifts a finger's breadth on the words.",
     "beside the horse level with his eyes, an arm's length from him, a 90mm lens. The moon comes from "
     "behind and the LEFT and rims the brim and the cheekbone, leaving the face black but for the eyes",
     "Jefferson Hope's face fills the CENTRE of the frame, half the frame height, from the beard at the "
     "BOTTOM third to the brim at the TOP edge, black with a silver rim along the LEFT side. His hand on "
     "the rifle's stock crosses the BOTTOM edge and the black crag fills the RIGHT edge.",
     "friction", 0.6, 0.0),
    # 34 BUTTON -- the world lets them by
    ("eagle_canyon_night", "close", ["unnamed_sentinel"], 0.9,
     "Close on the sentinel's bearded face under the slouch hat's brim from below, his chin on his two bare hands folded over the rifle's muzzle, the moon's silver rim along the brim and the cheekbone from behind and the left, the rest of the face black, the stars behind.",
     "The camera pulls back from the sentinel across the whole shot, travelling a hand's breadth; his "
     "hand lifts off the muzzle and waves once down the trail, a hand's breadth; his head nods once; the coat skirt stirs.",
     "on the trail below the rock at the height of a mounted man's eye looking up, three long strides "
     "from him, a 50mm lens. The moon comes from behind and the LEFT and rims his hat and shoulders, "
     "leaving his face black under the brim",
     "The sentinel's face fills the CENTRE of the frame, half the frame height, from the folded hands at the BOTTOM third to the brim at the TOP edge, black with the silver rim along the LEFT side. The rifle's muzzle stands up into the BOTTOM CENTRE under his hands and the stars fill the TOP edge.",
     "button", 0.6, 0.0),
    # 35 -- silent runout: the trot, the watcher small behind
    ("eagle_canyon_night", "wide", [], 1.0,
     "Wide from the sentinel's rock looking down into the canyon: the three riders going away from the camera at a trot down the pale dust between the black boulders, small and black, the rifle's muzzle and the sentinel's coat sleeve in the near left corner, the moon rimming the far crag.",
     "The camera tilts down across the whole shot, travelling a hand's breadth; the three riders go away down the trail at a trot growing smaller; the coat sleeve in the near corner lifts a hand's breadth; dust drifts off the trail to the right.",
     "on the sentinel's rock HIGH ABOVE the trail, looking steeply DOWN so the riders' hat crowns and the horses' backs are seen from above, a 35mm lens. The moon comes from behind and the LEFT and rims every rider in silver, leaving the trail black between the boulders",
     "The three riders are small at the CENTRE of the lower third going away down the pale trail, seen from above. The rock's edge crosses the BOTTOM LEFT corner under the rifle's muzzle and the coat sleeve, and the trail falls away below it. The black crag fills the RIGHT third to the TOP edge and the trail runs from the BOTTOM CENTRE up to the far bend at the CENTRE of the upper third.",
     "runout", 1.0, 3.0),
]

# (kind, speaker, text, shot)
LINES = [
    ("narration", "john_watson", "On the morning after the Prophet's visit, John Ferrier rode into the city with a letter for Nevada.", 0),
    ("narration", "john_watson", "He came home to find two strange horses hitched to his own gate posts.", 1),
    ("narration", "john_watson", "In his sitting-room sat two young men with their boots up: the sons of Elders Drebber and Stangerson.", 2),
    ("narration", "john_watson", "Stangerson had four wives, and Drebber seven, and each thought that settled it.", 3),
    ("dialogue", "john_ferrier", "This room has two ways out. The door, or the window.", 4),
    ("narration", "john_watson", "They went, and the door banged.", 6),
    ("narration", "john_watson", "Next morning there was a paper pinned to his coverlet, printed in bold straggling letters.", 7),
    ("narration", "john_watson", "Twenty-nine days are given you for amendment, it said, and then a dash.", 8),
    ("narration", "john_watson", "At breakfast his daughter pointed at the ceiling: scrawled there with a burnt stick, twenty-eight.", 9),
    ("narration", "john_watson", "Day by day the count came down, on his door and his gate, and no rider was Hope.", 10),
    ("narration", "john_watson", "The night the figure two went up, with every door bolted, he sank his head on the table.", 11),
    ("narration", "john_watson", "Then, in the silence, a scratching at a panel of the door; assassin, or the last day's number.", 12),
    ("narration", "john_watson", "He drew the bolt and threw the door wide on nothing. Then he looked down.", 13),
    ("narration", "john_watson", "It writhed over the sill like a snake, sprang up, shut the door, and was Hope the hunter.", 14),
    ("dialogue", "jefferson_hope", "Food first. Nothing for two days.", 15),
    ("narration", "john_watson", "It was Hope, come the last mile on his belly.", 15),
    ("narration", "john_watson", "He ate like a starving man, and two thousand dollars in gold went into a bag.", 16),
    ("dialogue", "jefferson_hope", "The house is watched. So I came in on my belly.", 17),
    ("dialogue", "jefferson_hope", "Tomorrow is your last day. We ride tonight.", 18),
    ("dialogue", "john_ferrier", "Then we ride tonight. Every acre of it can stay.", 19),
    ("narration", "john_watson", "Through the side window, one by one, into the garden.", 20),
    ("narration", "john_watson", "At the gap Hope dragged them down; nine to seven, said a voice, and seven to five, another.", 21),
    ("narration", "john_watson", "The horses waited in the Eagle Canyon; high in the pass, a voice rang out above them.", 22),
    ("dialogue", "unnamed_sentinel", "Who goes there? Nine from seven.", 23),
    ("dialogue", "jefferson_hope", "Travellers for Nevada. Seven from five.", 24),
    ("dialogue", "unnamed_sentinel", "Pass on, then, and the Lord go with you.", 25),
    # shot 26: silent -- the trot, the watcher small behind them
]

BEDS = [
    {"from_shot": 0, "tone": "uneasy"},
    {"from_shot": 2, "tone": "plain"},
    {"from_shot": 7, "tone": "grave"},
    {"from_shot": 12, "tone": "thrilling"},
    {"from_shot": 16, "tone": "plain"},
    {"from_shot": 20, "tone": "thrilling"},
    {"from_shot": 25, "tone": "uneasy"},
]

TURNS = {13: "hunted behind a bolt -> the door thrown open by his own hand",
         25: "the last post of the chosen people -> the road to Nevada open"}

# (beat_s, coda_s) by FINAL shot number; every other shot is 0.5 / 0.0
BEATS = {0: (0.6, 0.4), 6: (0.0, 0.0), 7: (0.6, 0.0), 8: (0.6, 0.0), 9: (0.6, 0.0), 10: (0.6, 0.0), 11: (1.0, 0.0), 12: (0.8, 0.0), 13: (1.0, 0.0),
         15: (0.5, 0.0), 19: (0.8, 0.0), 21: (0.5, 0.0), 24: (1.0, 0.0), 25: (0.6, 0.0), 26: (0.8, 1.0)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, frame, motion, camera, at_rest, section, beat, coda) in enumerate(S):
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces),
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=BEATS.get(i, (0.5, 0.0))[0],
                          coda_s=BEATS.get(i, (0.5, 0.0))[1], turn=TURNS.get(i, ""), cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=11, title="A Flight for Life",
                question="Tonight, can John Ferrier get his daughter out of Utah?",
                aspect="1:1", where=WHERE, light=LIGHT, protagonist="john_ferrier", answer="line 24",
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
