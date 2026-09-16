r"""Episode 9 — "The Flower of Utah", Part Two chapter 2.

THE BRICK. One event split by the title card.

  QUESTION  Today, can Lucy Ferrier ride into the city and come back her own?
  TURN      shot 17, 57% in: a stranger's brown hand closes on her bridle.
            alone and sufficient -> seen, and no longer her own.
  BUTTON    shot 29, Jefferson Hope, the world's answer and the last line:
            "In two months you shall see me." The reader knows what two months
            will cost; she does not.

Six setups, none over ~25 s. One line per shot, no sub-shots: 8.0 s take budget
and a 2-segment cap, the shape episodes 4 and 8 passed on.

`end` is written on the shots that travel. Under the owner's rule of 2026-09-16
no END picture is drawn or pinned; `episode_ref_official.arrival_clause` says
the arrival in WORDS instead, and `end` is what it says.
"""
import json
from pathlib import Path

OUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio"
           r"\library\20260822113400_a-study-in-scarlet\episodes\ep09\plan.json")

PALETTE = ("Warm high-summer palette of gold ripe wheat, red road dust and deep green pine, "
           "hard blue shadow under a clear bleached sky; the Utah valley and Salt Lake City, "
           "June 1860; American frontier, sunlight and lamplight only.")

SETUPS = {
    "valley_rim": dict(
        described=("The rim of the pass above the valley of Utah at sunrise, June 1847: a bare "
                   "rock shoulder falling away to a broad green valley floor, a flat silver "
                   "inland sea along its far side, a chain of snow-flecked peaks beyond that, "
                   "sagebrush and red dust underfoot, the sun low behind the near ridge"),
        cast=[], landmark="the flat silver inland sea on the valley floor",
        landmark_at="far_end", landmark_size="is the height of a hand",
        route="from the crest of the pass down the rock shoulder to the first grass",
        geometry=("The silver inland sea lies along the TOP third of the frame at the far side "
                  "of the valley. The snow-flecked peaks stand above it along the skyline. The "
                  "bare rock shoulder fills the BOTTOM third and the near right corner."),
        crowd=("Forty immigrants in dust-grey homespun kneel along the rock shoulder with their "
               "hats off, and beyond them twelve canvas-topped waggons stand in a line with "
               "their oxen still in the yoke."),
        outdoors=True, props=[]),
    "ferrier_land": dict(
        described=("John Ferrier's farm on the valley floor, June 1860: a long low log house "
                   "grown room by room into a rambling villa with a shingled roof and a deep "
                   "porch, a rail fence running out from it, a hundred acres of ripe gold wheat "
                   "beyond the fence, red pine hills behind, hard morning sunlight"),
        cast=["john_ferrier", "lucy_ferrier"], landmark="the log house with its deep porch",
        landmark_at="start", landmark_size="fills the frame",
        route="from the porch steps out along the rail fence into the standing wheat",
        geometry=("The log house stands along the LEFT edge with its porch posts in the near "
                  "ground. The rail fence runs from the bottom left corner to the centre of the "
                  "frame. The gold wheat fills the middle band and the red pine hills the TOP "
                  "third."),
        crowd=("Two farm hands in shirtsleeves pitch cut wheat onto a waggon at the fence line, "
               "and a yoke of oxen stands in the shafts with a boy at their heads."),
        outdoors=True, props=[]),
    "high_road": dict(
        described=("The dusty high road into Salt Lake City on a warm June morning, 1860: a "
                   "broad rutted red-dust road between low adobe walls and cottonwoods, the "
                   "half-built grey stone temple standing over the roofs ahead, the Wahsatch "
                   "mountains blue behind it, hanging dust gold in the low sun"),
        cast=["lucy_ferrier"], landmark="the half-built grey stone temple over the roofs",
        landmark_at="far_end", landmark_size="is half the height of the frame",
        route="from the open country at the farm end of the road in to the city outskirts",
        geometry=("The temple stands in the TOP centre of the frame above the roofline. The "
                  "rutted road runs from the bottom centre away to it. The adobe walls and "
                  "cottonwoods stand along both edges."),
        crowd=("Thirty heavily-laden pack mules file west along the left of the road with six "
               "drivers walking at their heads, a train of eight immigrant waggons rolls the "
               "other way, and four Indians lead ponies loaded with pelts along the right wall."),
        outdoors=True, props=[]),
    "the_drove": dict(
        described=("The road at the city outskirts, packed bank to bank with a great drove of "
                   "cattle on a warm June morning, 1860: long-horned bullocks shoulder to "
                   "shoulder from wall to wall, a standing cloud of red dust to the height of a "
                   "man, adobe walls and a rail corral on either side, hard white sun overhead"),
        cast=["lucy_ferrier", "jefferson_hope"], landmark="the rail corral at the roadside",
        landmark_at="far_end", landmark_size="is the height of a hand",
        route="from the open road behind the herd through the packed drove to its far edge",
        geometry=("The long-horned backs of the bullocks fill the BOTTOM two thirds of the frame "
                  "from edge to edge. The red dust hangs across the middle band. The adobe wall "
                  "and the rail corral stand along the RIGHT edge and the TOP third is bleached "
                  "sky."),
        crowd=("Six wild-looking herdsmen on ponies ride the flanks of the drove swinging coiled "
               "ropes, and two more sit their horses at the corral rail watching the road."),
        outdoors=True, props=[]),
    "farm_parlour": dict(
        described=("The parlour of John Ferrier's log villa on a summer evening, 1860: squared "
                   "log walls chinked white, a stone hearth with a low fire, a scrubbed pine "
                   "table under a hanging oil lamp, ladder-back chairs, a rag rug on boards, a "
                   "deep window open on the blue dusk, warm lamplight"),
        cast=["john_ferrier", "lucy_ferrier", "jefferson_hope"],
        landmark="the stone hearth with its low fire", landmark_at="start",
        landmark_size="is half the height of the frame",
        route="from the hearth across the rag rug to the open window",
        geometry=("The stone hearth stands along the LEFT edge with the fire low in it. The pine "
                  "table stands in the centre under the hanging lamp. The open window is a pale "
                  "blue rectangle in the RIGHT third."),
        crowd=("Moths cross the lamp glass in ones and twos and the low fire settles in the "
               "hearth."),
        outdoors=False, props=[]),
    "farm_gate": dict(
        described=("The gate of Ferrier's farm on a summer evening, 1860: a five-bar rail gate "
                   "in the fence at the head of a beaten path, the porch of the log house behind "
                   "it, gold stubble fields either side, the pine hills black against a burning "
                   "orange west, long level light"),
        cast=["lucy_ferrier", "jefferson_hope"], landmark="the porch of the log house",
        landmark_at="start", landmark_size="is half the height of the frame",
        route="from the gate up the beaten path to the porch steps",
        geometry=("The five-bar gate stands in the near RIGHT of the frame. The beaten path runs "
                  "from the gate to the bottom left corner. The porch of the log house stands in "
                  "the LEFT third and the burning orange west fills the TOP third."),
        crowd=("A roan horse stands at the fence with its bridle over the rail, shifting its "
               "weight and swinging its head at the flies."),
        outdoors=True, props=[]),
}

# (setup, size, faces, path, frame, motion, camera, at_rest, end, changed, section, beat, coda)
S = [
    # ---- hook: the promised land, and the man who prospered in it -----------
    ("valley_rim", "wide", [], 0.0,
     "Wide from the rim of the pass: the broad green valley of Utah opening below, the flat "
     "silver inland sea along its far side under a chain of snow-flecked peaks, kneeling "
     "immigrants in dust-grey homespun ranked along the bare rock shoulder in the near ground.",
     "The camera pulls back off the valley across the whole shot, travelling three long strides; "
     "the low sun lifts along the far peaks and the shadow slides down the valley wall; the "
     "kneeling men bow their heads together in the near ground.",
     "on the crest of the pass at a standing man's eye, two long strides behind the kneeling "
     "rank, a 35mm lens. The low sun stands behind the near ridge and rakes across the valley",
     "The silver inland sea lies along the TOP third and the kneeling rank fills the BOTTOM edge.",
     "The valley stands a hand's height smaller in the frame with the whole rock shoulder and "
     "both ends of the kneeling rank inside the bottom edge.",
     "the valley has fallen to half its size", "hook", 0.0, 0.0),

    ("valley_rim", "medium", [], 0.35,
     "Medium along the kneeling rank on the rock shoulder: bowed heads and clasped brown hands, "
     "hats held against chests, the green valley floor small and bright beyond their shoulders.",
     "The camera pans right along the rank across the whole shot, travelling two long strides; a "
     "man near the centre raises his face to the valley; his neighbour turns a hat brim through "
     "his fingers.",
     "on the rock shoulder at the height of a kneeling man's head, an arm's length from the "
     "nearest shoulder, a 50mm lens. The low sun comes across the rank from the left",
     "The bowed heads run in a line across the middle band of the frame.",
     "The far end of the kneeling rank has arrived at the right edge and the near man has left "
     "the frame on the left.",
     "the rank has travelled the frame's width", "hook", 0.0, 0.0),

    ("valley_rim", "full", [], 0.7,
     "Full of the waggon line on the flat below the rock shoulder: twelve canvas tops in a row, "
     "oxen standing in the yoke, a woman lifting a child down from a tailgate, red dust on "
     "every wheel.",
     "The camera tilts down off the peaks onto the waggons across the whole shot, travelling a "
     "head's height; the woman swings the child down onto the grass; an ox swings its head "
     "against the yoke.",
     "on the rock shoulder above the flat, a head's height over the waggon tops, a 35mm lens. "
     "The early sun comes from behind the camera",
     "The twelve canvas tops stand in a row across the middle band of the frame.",
     "The snow peaks have left the top of the frame and the waggon line fills it from edge to "
     "edge.",
     "the waggon tops have risen to fill the frame", "hook", 0.4, 0.0),

    ("ferrier_land", "wide", [], 0.0,
     "Wide of Ferrier's farm on the valley floor: the long log house with its deep porch and "
     "shingled roof on the left, a rail fence running out from it, a hundred acres of ripe gold "
     "wheat beyond, red pine hills behind under a bleached sky.",
     "The camera pushes in on the log house across the whole shot, travelling two long strides; "
     "the wheat runs in a long wave where the wind crosses it; a farm hand pitches a forkful up "
     "onto the waggon at the fence.",
     "on the beaten track in front of the farm at a standing man's eye, four long strides out "
     "from the rail fence, a 35mm lens. The hard morning sun stands high behind the camera",
     "The log house stands along the LEFT edge and the gold wheat fills the middle band.",
     "The log house stands twice its size along the left edge with the porch posts at the bottom "
     "corner and the wheat reduced to a gold strip.",
     "the house has doubled in the frame", "hook", 0.0, 0.0),

    # ---- rise: the girl in the wheat --------------------------------------
    ("ferrier_land", "medium", ["john_ferrier"], 0.3,
     "Medium of John Ferrier at the rail fence, the wide-brimmed brown felt hat level over his "
     "brows, the fawn homespun coat open on his dark waistcoat, one bare heavy-knuckled hand "
     "closed on the top rail, the gold wheat standing to his shoulder behind him.",
     "The camera pushes in on Ferrier across the whole shot, travelling one long stride; he runs "
     "his bare hand along the top rail toward the post; he turns his beard toward the wheat.",
     "on the track side of the rail fence, level with Ferrier's eye, two long strides from him, "
     "a 50mm lens. The high sun comes over his right shoulder",
     "Ferrier stands in the LEFT half with his hand on the top rail and the wheat behind him.",
     "Ferrier's head and shoulders fill the left half of the frame with the fence rail cut off "
     "at the bottom edge.",
     "Ferrier has grown by half in frame", "rise", 0.0, 0.0),

    ("ferrier_land", "full", ["lucy_ferrier"], 0.6,
     "Full of Lucy Ferrier walking a path through the standing wheat, the cream straw hat hanging "
     "back off her shoulders on its ribbon, chestnut hair loose, the white blouse and the "
     "slate-blue riding skirt bright against the gold, the pine hills behind.",
     "The camera tracks beside Lucy across the whole shot, travelling four long strides; she "
     "puts her bare hand out along the wheat heads as she walks at a normal walking pace; the "
     "ears bend under her palm and spring up behind her.",
     "in the standing wheat at the height of Lucy's shoulder, three long strides to her left, "
     "a 35mm lens. The high sun stands behind her and rims her hair",
     "Lucy stands in the RIGHT half of the frame with the wheat to her waist.",
     "Lucy has crossed to the left half of the frame with four fresh strides of wheat path open "
     "behind her.",
     "Lucy has crossed the frame", "rise", 0.0, 0.0),

    ("ferrier_land", "close", ["lucy_ferrier"], 0.75,
     "Close on Lucy's face against the gold wheat, the straw hat brim behind her head, her "
     "chestnut hair blown across her cheek, her eyes on something far down the valley.",
     "The camera pushes in on Lucy's face across the whole shot, travelling a head's height; she "
     "lifts her chin a finger's breadth toward the valley; she draws the blown hair off her "
     "cheek with one bare hand.",
     "in the wheat at Lucy's own eye, an arm's length in front of her, a 90mm lens. The high sun "
     "comes from behind her left shoulder",
     "Lucy's face fills the middle of the frame with the wheat behind her.",
     "Lucy's face stands a hand taller in the frame with her hair and the wheat carried out past "
     "both edges.",
     "her face has risen a hand taller", "rise", 0.3, 0.0),

    ("ferrier_land", "medium_close", ["lucy_ferrier", "john_ferrier"], 0.85,
     "Medium two-shot on the porch steps: Lucy on the lower step with the straw hat back on her "
     "shoulders, Ferrier above her in the brown felt hat with a folded paper held out in his "
     "bare hand, the open house door dark behind them.",
     "The camera pushes in on the two of them across the whole shot, travelling one long stride; "
     "Ferrier puts the folded paper down into Lucy's bare hand; she closes her fingers on it and "
     "turns her face up to him.",
     "on the beaten path below the porch, level with Lucy's eye, two long strides from the steps, "
     "a 50mm lens. The high sun comes over the roof and leaves the doorway dark",
     "Lucy stands on the LEFT of the steps and Ferrier on the RIGHT above her.",
     "Both stand half again as large with the porch posts carried out past both edges and the "
     "paper in Lucy's closed hand.",
     "the two have grown by half", "rise", 0.0, 0.0),

    # ---- the ride in ------------------------------------------------------
    ("high_road", "wide", [], 0.0,
     "Wide down the dusty high road into the city: the broad rutted red-dust road between adobe "
     "walls and cottonwoods, the half-built grey stone temple standing over the roofs ahead, the "
     "blue Wahsatch behind it, hanging dust gold in the low sun.",
     "The camera pushes in on the temple across the whole shot, travelling three long strides; a "
     "file of pack mules crosses the road from the left with their drivers walking at their "
     "heads; the hanging dust rolls up through the low sun.",
     "in the middle of the rutted road at a standing man's eye, a 35mm lens. The low morning sun "
     "comes from the right along the road",
     "The temple stands in the TOP centre above the roofline and the road runs from the bottom "
     "centre away to it.",
     "The temple stands twice its height over the roofs with the near adobe walls carried out "
     "past both edges of the frame.",
     "the temple has doubled in height", "rise", 0.0, 0.0),

    ("high_road", "medium", [], 0.25,
     "Medium along the left of the road: thirty heavily-laden pack mules filing west, six "
     "drivers walking at their heads with lead ropes over their shoulders, packs roped high, red "
     "dust to the mules' knees.",
     "The camera pans left along the mule train across the whole shot, travelling two long "
     "strides; the lead driver shifts the rope from one shoulder to the other; a mule swings its "
     "packed load against its neighbour.",
     "at the roadside at the height of a mule's back, two long strides from the file, a 50mm "
     "lens. The low sun comes down the road from behind the file",
     "The mule file runs across the middle band of the frame from edge to edge.",
     "The head of the mule train has arrived at the left edge and four fresh mules have come in "
     "at the right.",
     "the file has travelled the frame's width", "rise", 0.0, 0.0),

    ("high_road", "full", ["lucy_ferrier"], 0.45,
     "Full of Lucy galloping down the middle of the road on the mustang, the straw hat flat back "
     "on her shoulders, chestnut hair streaming, the blue riding skirt against the horse's "
     "shoulder, immigrant waggons rolling the other way behind her.",
     "The camera tracks beside Lucy across the whole shot, travelling four long strides; the "
     "mustang reaches into its gallop under her; she leans down along its neck with both bare "
     "hands low on the reins.",
     "beside the road at the height of the horse's shoulder, three long strides from it, a 35mm "
     "lens. The low sun comes from behind the camera and throws horse and rider forward",
     "Lucy and the mustang fill the RIGHT half of the frame.",
     "Lucy and the mustang have crossed to the left half with four waggons carried in behind "
     "them at the right edge.",
     "horse and rider have crossed the frame", "rise", 0.0, 0.0),

    ("high_road", "close", ["lucy_ferrier"], 0.6,
     "Close on Lucy's face in the gallop, the cream straw hat flat behind her head on its ribbon, "
     "her chestnut hair blown straight back, her cheek flushed, her eyes ahead down the road.",
     "The camera pushes in on Lucy's face across the whole shot, travelling a head's height; her "
     "hair lifts and streams back off her temple; she narrows her eyes against the hanging dust.",
     "beside the road at Lucy's own eye, an arm's length from her, a 90mm lens. The low sun comes "
     "across her face from the right",
     "Lucy's face fills the middle of the frame with the road behind her.",
     "Lucy's face stands a hand taller with her streaming hair carried out past the left edge.",
     "her face has risen a hand taller", "rise", 0.0, 0.0),

    ("high_road", "medium", [], 0.8,
     "Medium along the right wall: four Indians in worked hide leading laden ponies in toward the "
     "city, bundles of pelts roped over the ponies' backs, their faces turned up the road after "
     "something passing.",
     "The camera pans right off the road onto the pony train across the whole shot, travelling "
     "two long strides; the leading man turns his head to follow the road; a pony swings its "
     "roped pelts against the adobe.",
     "at the right roadside at a standing man's eye, two long strides from the wall, a 50mm lens. "
     "The low sun comes over the wall from behind them",
     "The pony train stands along the RIGHT half against the adobe wall.",
     "The pony train fills the frame from edge to edge with the adobe wall along the left.",
     "the road has left the frame", "rise", 0.3, 0.0),

    # ---- turn: the drove --------------------------------------------------
    ("the_drove", "wide", [], 0.0,
     "Wide of the road packed bank to bank with long-horned cattle, a standing cloud of red dust "
     "to the height of a man over their backs, the adobe wall and the rail corral along the "
     "right, herdsmen on ponies riding the flanks.",
     "The camera pulls back off the drove across the whole shot, travelling three long strides; "
     "the packed backs roll forward together up the road; a herdsman swings a coiled rope over "
     "the flank.",
     "on the road above the herd at the height of a mounted man's eye, a 35mm lens. The hard "
     "white sun stands overhead",
     "The bullocks fill the BOTTOM two thirds from edge to edge and the dust hangs in the middle "
     "band.",
     "The whole width of the drove and both roadside walls stand inside the frame with the herd "
     "reduced to half its size.",
     "the drove has fallen to half its size", "turn", 0.0, 0.0),

    ("the_drove", "medium", ["lucy_ferrier"], 0.3,
     "Medium of Lucy on the mustang pushing into a gap in the herd, the straw hat back on her "
     "shoulders, both bare hands low on the reins, long horns crowding in on either side of the "
     "horse's shoulder.",
     "The camera pushes in on Lucy across the whole shot, travelling two long strides; she puts "
     "the mustang forward into the gap at a walking pace; the bullocks close their backs in "
     "behind its tail.",
     "on the road behind the horse at the height of Lucy's shoulder, three long strides back, a "
     "50mm lens. The overhead sun drops her hat shadow onto her collar",
     "Lucy and the mustang stand in the centre of the frame with the herd to either side.",
     "Lucy and the mustang stand twice their size with the crowding horns carried out past both "
     "edges and packed backs filling both corners.",
     "the gap has closed behind her", "turn", 0.0, 0.0),

    ("the_drove", "close", [], 0.45,
     "Close insert at the mustang's flank in the press: the horse's dusty shoulder and barrel, a "
     "long polished horn swinging in across it, dust in the hair of the hide, a boot and stirrup "
     "at the top of the frame.",
     "The camera pushes in on the flank across the whole shot, travelling a hand's breadth; the "
     "long horn comes across and knocks against the horse's barrel; the hide flinches away under "
     "it.",
     "low at the height of the horse's belly, an arm's length from the flank, a 90mm lens. The "
     "overhead sun stripes the flank through the dust",
     "The horse's flank fills the LEFT two thirds and the horn crosses the middle band.",
     "The flank and the horn fill the frame edge to edge with the top edge across the stirrup leather.",
     "the stirrup has risen to the top edge", "turn", 0.0, 0.0),

    ("the_drove", "full", ["lucy_ferrier"], 0.55,
     "Full of the mustang up on its hind legs in the packed drove, Lucy thrown back along its "
     "neck with the straw hat swung back on its ribbon, her hair loose, the horns of the bullocks "
     "crowded round its forelegs, red dust to her stirrup.",
     "The camera tilts up with the rearing horse across the whole shot, travelling a head's "
     "height; the mustang goes up and tosses its head against the bit; Lucy comes forward along "
     "its neck and takes a fresh grip on the reins.",
     "on the road beside the herd at the height of a mounted man's eye, four long strides from "
     "the horse, a 35mm lens. The overhead sun stands behind the dust",
     "The rearing mustang fills the RIGHT half of the frame from the bottom edge upward.",
     "The mustang's head and Lucy's shoulders stand at the top of the frame with the crowded "
     "horns carried out below the bottom edge.",
     "the horse has risen to the top of frame", "turn", 0.0, 0.0),

    ("the_drove", "medium_close", ["lucy_ferrier", "jefferson_hope"], 0.7,
     "Medium two-shot at the mustang's head: a sinewy brown hand closed on the curb below the "
     "horse's jaw, Jefferson Hope beside it on the powerful roan in the broad brown sombrero and "
     "the fringed buckskin, Lucy above on the mustang with her hair over her face.",
     "The camera pushes in on the two of them across the whole shot, travelling two long strides; "
     "Hope draws the mustang's head down and round toward his knee; Lucy lifts her face out of "
     "her hair and looks down at his hand.",
     "on the road level with the horses' heads, three long strides from the curb, a 50mm lens. "
     "The overhead sun stands behind the hanging dust",
     "Hope stands in the LEFT half on the roan and Lucy above in the RIGHT half.",
     "Both riders stand half again as large with the horses' heads filling the bottom of the "
     "frame and the herd carried out past both edges.",
     "the two riders have grown by half", "turn", 0.0, 0.0),

    ("the_drove", "close", ["jefferson_hope"], 0.85,
     "Close on Jefferson Hope under the broad brown sombrero, the dark fierce sunburnt face and "
     "the close black beard, his eyes up at Lucy, the rifle strap across his buckskin shoulder, "
     "dust hanging behind him.",
     "The camera pushes in on Hope's face across the whole shot, travelling a head's height; he "
     "puts his chin up a finger's breadth toward her; his jaw works once under the beard.",
     "on the road at Hope's own eye, an arm's length from him, a 90mm lens. The overhead sun "
     "comes past his hat brim onto his beard",
     "Hope's face fills the middle of the frame with the dust behind him.",
     "Hope's face stands a hand taller with the sombrero brim carried out past both edges.",
     "his face has risen a hand taller", "turn", 0.0, 0.0),

    ("the_drove", "medium_close", ["lucy_ferrier"], 0.95,
     "Medium close on Lucy at the edge of the drove, the straw hat back on its ribbon, her "
     "chestnut hair off her face, the flush high on her cheek, the rail corral and the open road "
     "behind her shoulder.",
     "The camera pulls back off Lucy across the whole shot, travelling one long stride; she "
     "gathers the loose hair back off her cheek with one bare hand; she puts her chin round "
     "toward Hope at the frame edge.",
     "at the edge of the drove level with Lucy's eye, two long strides from her, a 50mm lens. "
     "The overhead sun stands behind her and lights the dust",
     "Lucy fills the middle of the frame with the corral rail behind her right shoulder.",
     "Lucy stands a third smaller with the whole corral rail and Hope's shoulder inside the "
     "right edge.",
     "Lucy has fallen a third in size", "turn", 0.0, 0.0),

    ("the_drove", "close", ["lucy_ferrier"], 1.0,
     "Close on Lucy's face turned down to Hope at the frame edge, her hair off her cheek, her "
     "mouth open on a laugh, the bright road behind her.",
     "The camera holds a static shot as Lucy laughs down at him; she tips her head over toward "
     "her shoulder; she draws one bare hand down the mustang's neck.",
     "at the edge of the drove at Lucy's own eye, an arm's length from her, a 90mm lens. The "
     "overhead sun comes across her cheek",
     "Lucy's face fills the middle of the frame.",
     "", "", "turn", 0.4, 0.0),

    # ---- fall: the visits -------------------------------------------------
    ("farm_parlour", "wide", [], 0.0,
     "Wide of the Ferrier parlour by lamplight: squared white-chinked log walls, the stone hearth "
     "with a low fire on the left, the scrubbed pine table under the hanging oil lamp, "
     "ladder-back chairs, the deep window open on the blue dusk.",
     "The camera pushes in on the table across the whole shot, travelling two long strides; the "
     "low fire settles and drops in the hearth; a moth crosses the lamp glass and goes out into "
     "the dark.",
     "at the parlour door at a standing man's eye, four long strides from the table, a 35mm lens. "
     "The hanging oil lamp is the light in the room",
     "The hearth stands along the LEFT edge and the table in the centre under the lamp.",
     "The table fills the middle of the frame with the hearth carried out past the left edge.",
     "the hearth has left the frame", "reaction", 0.0, 0.0),

    ("farm_parlour", "medium", ["jefferson_hope", "john_ferrier"], 0.3,
     "Medium two-shot across the pine table: Jefferson Hope leaning in on his forearms with his "
     "hat off and the black hair flat, Ferrier opposite him bare-headed in his dark waistcoat "
     "with the iron-grey hair combed back, the lamp hanging between them.",
     "The camera pushes in on the two men across the whole shot, travelling one long stride; Hope "
     "opens one brown hand flat on the boards toward Ferrier; Ferrier puts his chin down and "
     "draws his beard through his fingers.",
     "at the table end level with a seated man's eye, two long strides from the near chair, a "
     "50mm lens. The hanging lamp is over the table between them",
     "Hope sits in the LEFT half and Ferrier in the RIGHT half across the table.",
     "Both men stand half again as large with the lamp carried out above the top edge.",
     "the lamp rim has risen to the top edge", "reaction", 0.0, 0.0),

    ("farm_parlour", "close", ["lucy_ferrier"], 0.45,
     "Close on Lucy at the open window in the plain grey-blue house dress with the narrow white "
     "collar, her chestnut hair gathered back, the blue dusk in the window behind her, the "
     "lamplight warm on the near side of her face.",
     "The camera pushes in on Lucy across the whole shot, travelling a head's height; she turns "
     "her face a finger's breadth toward the table; the colour comes up along her cheekbone.",
     "in the room at Lucy's own eye, an arm's length from her, a 90mm lens. The lamp is behind "
     "the camera and the open window behind her",
     "Lucy's face fills the middle of the frame with the pale window behind her.",
     "Lucy's face stands a hand taller with the window carried out past the right edge.",
     "her face has risen a hand taller", "reaction", 0.0, 0.0),

    ("farm_parlour", "medium_close", ["jefferson_hope"], 0.6,
     "Medium close on Hope in the lamplight, the dark fierce face and close black beard turned "
     "across the table, the buckskin shoulder catching the lamp, the white-chinked logs behind "
     "him.",
     "The camera pushes in on Hope across the whole shot, travelling one long stride; he turns "
     "his head from the table toward the window; his eyes come up and hold on Lucy at the frame "
     "edge.",
     "at the table side level with Hope's eye, two long strides from him, a 50mm lens. The "
     "hanging lamp comes down on his shoulder from the left",
     "Hope fills the LEFT half of the frame with the log wall behind him.",
     "Hope's head and shoulders fill the frame with the log wall carried out past both edges.",
     "Hope has grown to fill the frame", "reaction", 0.0, 0.0),

    ("farm_parlour", "close", [], 0.75,
     "Close insert on the pine boards under the lamp: Hope's brown open hand flat on the scrubbed "
     "wood, a tin cup beside it, Lucy's smaller bare hand at the edge of the table in the "
     "lamplight.",
     "The camera pushes in on the two hands across the whole shot, travelling a hand's breadth; "
     "Hope's fingers draw in along the boards toward the cup; Lucy's hand turns over on the table "
     "edge.",
     "over the table at the height of a seated man's chin, an arm's length from the boards, a "
     "90mm lens. The hanging lamp is straight above the hands",
     "Hope's hand lies in the LEFT half and Lucy's at the RIGHT edge.",
     "Both hands fill the frame with the tin cup carried out past the top edge.",
     "the cup rim has risen to the top edge", "reaction", 0.4, 0.0),

    # ---- button: the gate -------------------------------------------------
    ("farm_gate", "wide", [], 0.0,
     "Wide of the farm gate at sundown: the five-bar rail gate in the near right, the beaten path "
     "running to the porch of the log house on the left, gold stubble either side, the pine hills "
     "black against a burning orange west.",
     "The camera pushes in on the gate across the whole shot, travelling two long strides; the "
     "roan at the fence swings its head at the flies; the long light slides up the stubble as the "
     "sun drops behind the hills.",
     "on the path below the gate at a standing man's eye, four long strides out, a 35mm lens. The "
     "low sun burns orange behind the pine hills",
     "The five-bar gate stands in the near RIGHT and the porch in the LEFT third.",
     "The gate fills the right half of the frame with the porch carried out past the left edge.",
     "the porch has left the frame", "button", 0.0, 0.0),

    ("farm_gate", "medium_close", ["jefferson_hope", "lucy_ferrier"], 0.4,
     "Medium two-shot at the gate: Hope facing Lucy with her two bare hands taken in his brown "
     "ones between them, the sombrero pushed back off his forehead, Lucy in the grey-blue house "
     "dress with her chestnut hair loose, the burning west behind their heads.",
     "The camera pushes in on the two of them across the whole shot, travelling one long stride; "
     "Hope closes his brown hands over Lucy's; she puts her face up to him and her fingers turn "
     "in his.",
     "on the path beside the gate level with Lucy's eye, two long strides from them, a 50mm lens. "
     "The low orange sun stands behind their heads",
     "Hope stands in the RIGHT half and Lucy in the LEFT half facing him.",
     "Both stand half again as large with the gate rail carried out past the right edge.",
     "the two have grown by half", "button", 0.0, 0.0),

    ("farm_gate", "close", ["lucy_ferrier"], 0.55,
     "Close on Lucy's face turned up to Hope at the frame edge, her chestnut hair loose on her "
     "shoulder, the orange west burning behind her, her eyes on his.",
     "The camera pushes in on Lucy's face across the whole shot, travelling a head's height; she "
     "brings her chin up a finger's breadth to him; her mouth comes open on the question.",
     "beside the gate at Lucy's own eye, an arm's length from her, a 90mm lens. The low orange "
     "sun comes past her cheek from behind",
     "Lucy's face fills the middle of the frame against the burning sky.",
     "Lucy's face stands a hand taller with her loose hair carried out past the left edge.",
     "her face has risen a hand taller", "button", 1.2, 0.0),

    ("farm_gate", "close", ["jefferson_hope"], 0.7,
     "Close on Hope's face against the burning west, the sombrero pushed back, the dark fierce "
     "eyes down on Lucy at the frame edge, the black beard close along his jaw.",
     "The camera pushes in on Hope's face across the whole shot, travelling a head's height; he "
     "brings his head down toward her a finger's breadth; his eyes hold and his jaw sets under "
     "the beard.",
     "beside the gate at Hope's own eye, an arm's length from him, a 90mm lens. The low orange "
     "sun burns behind his shoulder",
     "Hope's face fills the middle of the frame against the burning sky.",
     "Hope's face stands a hand taller with the sombrero brim carried out past both edges.",
     "his face has risen a hand taller", "button", 0.0, 3.0),
]

LINES = [
    # (kind, speaker, text, shot)
    ("narration", "john_watson", "They had crossed a continent on foot, and the last of them came over the pass at dawn.", 0),
    ("narration", "john_watson", "Every man there went down on his knees when he saw the valley.", 1),
    ("narration", "john_watson", "Their leader told them it was the promised land, and that it was theirs.", 2),
    ("narration", "john_watson", "Among them was John Ferrier, who had walked out of the desert carrying a child.", 3),
    ("narration", "john_watson", "In three years he was comfortable, in nine he was rich, in twelve he had no equal.", 4),
    ("narration", "john_watson", "The child grew up in the log house and worked beside him at everything.", 5),
    ("narration", "john_watson", "The mountain air and the pines did for her what a mother would have done.", 6),
    ("narration", "john_watson", "So the bud opened into a flower, in the year her father became the richest of them.", 7),

    ("narration", "john_watson", "It was a warm June morning, and the whole valley was at work.", 8),
    ("narration", "john_watson", "The gold fever had broken out west, and the road to it ran through the city.", 9),
    ("narration", "john_watson", "Through the middle of it all Lucy Ferrier came galloping in on her father's errand.", 10),
    ("narration", "john_watson", "She was nineteen, and she had ridden that road a hundred times alone.", 11),
    ("narration", "john_watson", "Strangers turned in the dust to watch her go by.", 12),

    ("narration", "john_watson", "At the edge of the city the road was stopped by a drove of cattle.", 13),
    ("narration", "john_watson", "She saw a gap and put her horse into it, and the beasts closed up behind her.", 14),
    ("narration", "john_watson", "A horn came round and struck the mustang in the flank.", 15),
    ("narration", "john_watson", "It went up, and a slip would have put her under four hundred hooves.", 16),
    ("dialogue", "jefferson_hope", "You're not hurt, I hope, miss.", 17),
    ("dialogue", "jefferson_hope", "I guess you are the daughter of John Ferrier.", 18),
    ("dialogue", "lucy_ferrier", "Hadn't you better come and ask him yourself?", 19),
    ("narration", "john_watson", "She rode on. He sat his horse in the road and watched the dust take her.", 20),

    ("narration", "john_watson", "He came to the house that night, and a great many nights after it.", 21),
    ("narration", "john_watson", "He had been a scout, a trapper and a miner, and he could tell it.", 22),
    ("narration", "john_watson", "Her father heard him gladly. Lucy said very little at all.", 23),
    ("narration", "john_watson", "What she felt was plain enough to the one man it was meant for.", 24),
    ("narration", "john_watson", "By midsummer her heart was no longer her own, and she knew it.", 25),

    ("narration", "john_watson", "He came down the road one evening at a gallop and pulled up at the gate.", 26),
    ("dialogue", "jefferson_hope", "I am off, Lucy. Will you be ready to come when I am here again?", 27),
    ("dialogue", "lucy_ferrier", "And when will that be?", 28),
    ("dialogue", "jefferson_hope", "In two months you shall see me.", 29),
]

BEDS = [
    {"from_shot": 0, "tone": "grave"},
    {"from_shot": 3, "tone": "plain"},
    {"from_shot": 5, "tone": "light"},
    {"from_shot": 8, "tone": "plain"},
    {"from_shot": 13, "tone": "thrilling"},
    {"from_shot": 20, "tone": "light"},
    {"from_shot": 25, "tone": "uneasy"},
]

TURNS = {
    17: "alone and sufficient -> held by a stranger's hand",
    29: "a promise given -> a clock started",
}


SECTIONS = (
    ["hook"]                     # 0   the valley
    + ["setup"] * 7              # 1-7   the settlement, the farm, the girl
    + ["transition"] * 5         # 8-12  the ride in
    + ["friction"] * 4           # 13-16 the drove closes, the mustang rears
    + ["turn"]                   # 17    the brown hand on the bridle -- 57% in
    + ["spike"] * 2              # 18-19 the exchange
    + ["payoff"] * 6             # 20-25 the visits
    + ["runout"] * 3             # 26-28
    + ["button"]                 # 29    "In two months you shall see me."
)
"""Exactly one hook, one turn and one button: `Episode._the_shape_is_present`.
The turn sits at 17 of 30, 57 % in, inside the 50-75 % band."""
assert len(SECTIONS) == 30


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, frame, motion, camera, at_rest, end, changed,
            section, beat, coda) in enumerate(S):
        shots.append(dict(
            index=i, section=SECTIONS[i], setup=setup, size=size, faces=list(faces), path=path,
            frame=frame, motion=motion, camera=camera, at_rest=at_rest,
            end=end, changed=changed, beat_s=beat, coda_s=coda,
            turn=TURNS.get(i, ""), cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(
        number=9, title="The Flower of Utah",
        question="Today, can Lucy Ferrier ride into the city and come back her own?",
        aspect="1:1", palette=PALETTE, protagonist="lucy_ferrier",
        narrator="john_watson", beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words "
          f"-> {words / 3.0:.0f}s projected; dialogue {said / words:.1%}")
    print(OUT)
