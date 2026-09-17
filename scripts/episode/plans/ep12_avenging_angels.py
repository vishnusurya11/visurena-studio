r"""Episode 12 — "The Avenging Angels", Part Two chapter 5.

THE BRICK. One event split by the title card.

  QUESTION  Today, can Jefferson Hope bring the Ferriers through the mountains?
  TURN      shot 13, ~54 % in: the empty camp -- Hope blows a brand from the
            dead ashes and reads the ground by it: hooves, and a low heap of
            red soil with a stick and a paper. "a guide with two lives in his
            hands -> a man with one thing left".
  BUTTON    shot 26, the world's answer and the last line, a wife of Drebber's
            with her candle over the empty finger: "The ring is gone." One
            silent shot after it: his back striding down into the gorge.

Written under the ep11 rules: a close or medium-close takes a PAN, never a
push and never a pull-back; an insert takes a tilt or a pan; the head fraction
is the size; under a sun the shadow has a caster at an edge; every camera
light clause names its frame side and a black; a dialogue line is the first
line on its shot; the lead speaks his own decision on his own face; the last
line lands within six seconds of the end; a name's first hearing carries its
role. The epitaph is read by the narrator over a blank paper -- the drawer
letters nothing. The years of pursuit belong to episode 13, Hope's own account.

Four speakers: the narrator, Hope, Cowper, a wife of Drebber's. Ferrier and
Lucy are on screen and silent; the riders are never seen.
"""
import json
from pathlib import Path

OUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio"
           r"\library\20260822113400_a-study-in-scarlet\episodes\ep12\plan.json")

WHERE = "Utah mountains, 1860"
LIGHT = "low raking light, deep black shadow"

SETUPS = {
    "mountain_defile_dawn": dict(
        described=("A high mountain defile in the Utah ranges at dawn, August 1860: a rock-strewn trail "
                   "along the floor of a narrow valley, steep banks of grey rock on both sides with larch "
                   "and pine hung over them, fallen trees and boulders down the slopes, and above it all "
                   "the great snow-capped peaks hemming the sky; the low sun comes from the right over the "
                   "peaks and lights them one after another red and gold, rims the pines along the right "
                   "bank, and leaves the defile floor and the left bank in deep black shadow, the trail a "
                   "pale thread between black rocks"),
        cast=["jefferson_hope", "john_ferrier", "lucy_ferrier"], landmark="the snow-capped peaks",
        landmark_at="far_end", landmark_size="is half the height of the frame",
        route="from the near bend of the defile along the trail to the torrent at the far bend",
        geometry=("The snow-capped peaks fill the TOP third of the frame lit red and gold from the RIGHT. "
                  "The right bank rises along the RIGHT edge with pines rimmed in sun; the left bank is a "
                  "black wall along the LEFT edge. The trail runs from the BOTTOM CENTRE up the black floor "
                  "of the defile to the far bend at the CENTRE of the frame."),
        crowd="", outdoors=True, props=[]),
    "camp_nook_dusk": dict(
        described=("A sheltered nook among grey boulders on a mountain shoulder at dusk, August 1860: a "
                   "blazing fire of dried branches on the bare ground in the middle, three animals -- two "
                   "horses and a mule -- tethered to a dead larch behind it, the boulders rising on all "
                   "sides, the sky above violet; the fire is the only light and it comes from the "
                   "fire alone, low and orange, on the faces and hands nearest it and on the near sides of "
                   "the boulders, leaving the far rocks, the animals' flanks and the sky black"),
        cast=["john_ferrier", "lucy_ferrier", "jefferson_hope"], landmark="the fire of dried branches",
        landmark_at="start", landmark_size="is the height of a hand",
        route="from the fire past the tethered animals to the gap in the boulders",
        geometry=("The fire burns at the CENTRE of the frame in the BOTTOM third, its light on the ground "
                  "around it. The three animals stand as dark shapes at the RIGHT third behind it against "
                  "the black boulders. The gap in the boulders is a notch of violet sky at the TOP CENTRE "
                  "and the near boulders close the LEFT edge, orange on their fire side."),
        crowd="", outdoors=True, props=[]),
    "camp_night": dict(
        described=("The same nook among grey boulders by night, August 1860, the fire burned down to a "
                   "glowing pile of wood ashes on the bare ground, the ground all round it stamped and "
                   "churned by the hooves of many horses, a low heap of reddish soil newly dug a little to "
                   "one side with a forked stick planted in it and a blank square of paper in the cleft, "
                   "the boulders black on all sides; a brand blown to a flame in a man's hand is the only "
                   "light and it comes from the brand alone, low and red, on the ashes, the stamped ground, "
                   "the heap and the stick, and leaves the boulders and the sky black"),
        cast=["jefferson_hope"], landmark="the low heap of reddish soil with its forked stick",
        landmark_at="far_end", landmark_size="is the height of a hand",
        route="from the dead fire across the stamped ground to the heap of red soil",
        geometry=("The glowing ashes lie at the BOTTOM LEFT of the frame. The stamped ground fills the "
                  "BOTTOM half between them and the heap of red soil at the RIGHT third with its forked "
                  "stick standing up into the middle of the frame. The boulders are black across the TOP "
                  "half and the brand's red light reaches the middle of the frame and dies at the rocks."),
        crowd="", outdoors=True, props=[]),
    "eagle_canyon_day": dict(
        described=("The mouth of the Eagle Canyon above Salt Lake City on a clear day, August 1860: a flat "
                   "shelf of rock at the canyon's mouth, boulders and scree behind it, and below, far off, "
                   "the wide pale valley with the city's streets small in it and small flags in the "
                   "streets; the sun comes from the left, hard and high, lights the rock shelf and the near "
                   "faces of the boulders, and throws every boulder's shadow black to the right across the "
                   "shelf, the far city pale in haze"),
        cast=["jefferson_hope", "cowper"], landmark="the city small in the valley below",
        landmark_at="far_end", landmark_size="is the height of a finger",
        route="from the canyon trail up onto the rock shelf at the canyon's mouth",
        geometry=("The rock shelf crosses the BOTTOM third of the frame with a boulder at the LEFT edge "
                  "and its black shadow across the shelf to the RIGHT. The pale valley fills the middle of "
                  "the frame with the city the height of a finger at its CENTRE and the far hills close "
                  "the TOP third."),
        crowd="", outdoors=True, props=[]),
    "drebber_house_bier": dict(
        described=("Interior, inside a plain plastered room in a house in Salt Lake City in the grey of "
                   "an early morning, 1860, the camera within the room with white plastered walls closed "
                   "on all four sides: a bier in the middle of the room with a white silent figure on it "
                   "under a sheet to the chin, three women in black seated round it, a lit candle in each "
                   "woman's hands, a heavy plank door in the far wall; the candles are the only light and "
                   "the light comes from the candles alone, low and yellow, on the women's faces and the "
                   "white sheet, leaving the walls, the door and the corners black"),
        cast=["lucy_ferrier", "drebber_wife", "jefferson_hope"], landmark="the plank door in the far wall",
        landmark_at="far_end", landmark_size="is half the height of the frame",
        route="from the bier across the room to the plank door",
        geometry=("The bier stands across the middle of the frame with the white sheet lit from the "
                  "candles, the three women seated round it in the BOTTOM half with their candles at the "
                  "height of their faces. The plank door stands in the far wall at the CENTRE of the upper "
                  "third, black. The plastered walls are black along both edges."),
        crowd="", outdoors=False, props=[]),
}

# (setup, size, faces, path, frame, motion, camera, at_rest, section, beat, coda)
S = [
    # 0 HOOK -- the peaks light one after another
    ("mountain_defile_dawn", "wide", [], 0.0,
     "Wide up the black defile at dawn, the snow-capped peaks above lit red and gold from the right one "
     "after another, the pines rimmed along the right bank, the trail a pale thread up the black floor.",
     "The camera tilts up across the whole shot, travelling a hand's breadth; the sun's light comes down "
     "the peaks from the right one after another; a thread of mist lifts off the black floor.",
     "on the trail at a standing man's eye, a 35mm lens. The low sun comes from the RIGHT over the peaks "
     "and leaves the defile floor black",
     "The lit peaks fill the TOP third of the frame from edge to edge. The black left bank fills the LEFT "
     "edge and the pines rimmed in sun the RIGHT edge. The pale trail runs from the BOTTOM CENTRE up the "
     "black floor to the far bend at the CENTRE.",
     "hook", 0.6, 0.4),
    # 1
    ("mountain_defile_dawn", "medium", ["jefferson_hope"], 0.2,
     "Medium of Jefferson Hope on foot leading a horse up the trail in the sombrero and buckskin, the "
     "rifle across his back, the mule and the second horse with two riders small behind him, the sun rimming his hat from the left and the brim's shadow black over his face.",
     "The camera pans left across the whole shot, travelling a hand's breadth; the horse's head comes "
     "up; Hope's hand tightens on the lead; his hat brim turns a finger's breadth toward the peaks.",
     "on the trail ahead of him at the height of his chest, three long strides from him, a 50mm lens. "
     "The sun comes from the LEFT and rims his hat, leaving his face black under the brim",
     "Jefferson Hope walks at the CENTRE of the frame from the BOTTOM edge to the TOP third, his face a "
     "quarter of the frame height under the brim. The horse's head fills the RIGHT third beside him. The "
     "mule and the second horse are small at the LEFT third on the trail behind and the black bank fills "
     "the TOP edge.",
     "setup", 0.5, 0.0),
    # 2
    ("mountain_defile_dawn", "insert", [], 0.35,
     "Insert on a great rock the size of a cart coming down the black slope of the left bank in a burst "
     "of dust and smaller stones, the pale trail below it, the sunlit pines above at the right.",
     "The camera tilts down across the whole shot, travelling a hand's breadth; the rock comes down "
     "the slope in its dust and lands on the trail; stones bounce off it; the dust rolls toward the lens.",
     "on the trail below the bank at a standing man's eye, four long strides from the rock's landing, a "
     "35mm lens. The sun comes from the RIGHT and lights the dust, leaving the bank black",
     "The rock fills the CENTRE of the frame the height of the middle third with its dust across the "
     "TOP half. The black bank fills the LEFT edge, the sunlit pines the TOP RIGHT corner, and the pale "
     "trail crosses the BOTTOM third.",
     "setup", 0.5, 0.0),
    # 3 -- dialogue: speed
    ("mountain_defile_dawn", "medium_close", ["jefferson_hope"], 0.5,
     "Medium close of Jefferson Hope at the torrent with the reins in his bare hand, the sombrero pushed "
     "back, the black beard cut close, the sun from the right full on his face, the black bank's shadow across his shoulder, the white water behind him.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the white water keeps "
     "the left edge and the black bank keeps the right edge; his jaw sets on the words; his hand jerks the "
     "reins a hand's breadth.",
     "at the torrent's edge level with his eyes, two long strides from him, a 50mm lens. The sun comes "
     "from the RIGHT onto his face and leaves the bank black",
     "Jefferson Hope's head and shoulders fill the CENTRE of the frame from the TOP third to the "
     "buckskin at the BOTTOM edge, his head a third of the frame's height, in full sun. The white water fills the LEFT edge and the black bank the RIGHT edge.",
     "setup", 1.0, 0.0),
    # 4
    ("camp_nook_dusk", "medium", ["john_ferrier", "lucy_ferrier"], 0.1,
     "Medium of the fire in the nook at dusk, John Ferrier in his brown felt hat and fawn coat and Lucy "
     "Ferrier in the slate-blue riding skirt crouched over the blaze, the three animals dark behind "
     "them, the boulders black.",
     "The camera pushes in on the fire across the whole shot, travelling a hand's breadth; the flames "
     "lean and leap; Lucy's hands spread to the blaze; a horse behind them stamps once.",
     "at the gap in the boulders level with a crouching man's eye, three long strides from the fire, a "
     "35mm lens. The fire is the light, from the CENTRE, and leaves the boulders and the sky black",
     "The fire burns at the CENTRE of the frame in the BOTTOM third with John Ferrier crouched at its "
     "LEFT and Lucy at its RIGHT, their faces orange, the height of the middle third. The three animals "
     "are dark shapes at the TOP RIGHT and the black boulders close the TOP edge.",
     "setup", 0.5, 0.0),
    # 5
    ("camp_nook_dusk", "medium", ["jefferson_hope"], 0.4,
     "Medium of Jefferson Hope at the edge of the firelight with the rifle over his shoulder, the "
     "sombrero on, his head turned back over his shoulder toward the fire, the near side of his face "
     "orange and the far side black against the boulders.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the black boulder "
     "keeps the right edge and the fire's glow keeps the left edge; his chin comes round a finger's "
     "breadth over his shoulder; his hand shifts the rifle's sling.",
     "beside the gap in the boulders level with his eyes, three long strides from him, a 35mm lens. The fire is the light, from the LEFT, and leaves the boulder black",
     "Jefferson Hope stands at the CENTRE of the frame from the BOTTOM edge to the TOP third, his head a quarter of the frame height, the fire's orange on the near side of his face. The rifle's barrel stands up along the RIGHT third, the black boulder fills the RIGHT edge and the fire's glow the LEFT edge.",
     "transition", 0.6, 0.0),
    # 6
    ("camp_nook_dusk", "wide", [], 0.7,
     "Wide from the rocks above the nook at dusk: the fire small below with two figures crouched over "
     "it, the three animals standing motionless behind, the black boulders round them, the violet sky "
     "over the ridge.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the fire's glow flickers "
     "on the two figures; one animal's head comes down; the violet sky darkens a shade.",
     "on the rocks above the nook at a standing man's eye looking down, a 35mm lens. The fire is the "
     "light, from BELOW at the CENTRE, and leaves the boulders and the sky black",
     "The fire is a point of orange at the CENTRE of the lower third with the two figures the height "
     "of a finger crouched at it. The black boulders fill the BOTTOM half round them. The violet sky "
     "fills the TOP third over the ridge line at the CENTRE.",
     "transition", 0.5, 0.3),
    # 7
    ("mountain_defile_dawn", "medium", ["jefferson_hope"], 0.7,
     "Medium of Jefferson Hope lying flat on his belly on a grey rock with the rifle rested before him, "
     "the sombrero off beside him, the black beard along the stock, the sunlit pinnacle high above at "
     "the right, the rock's shadow black beneath him.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the pinnacle keeps the "
     "top right corner and the black rock keeps the bottom edge; his finger comes to the trigger; his cheek comes down along the stock.",
     "beside the rock level with his shoulders, two long strides from him, a 50mm lens. The sun comes "
     "from the RIGHT along the rifle and leaves the rock's underside black",
     "Jefferson Hope lies across the CENTRE of the frame from the LEFT third to the RIGHT third with the "
     "rifle along the CENTRE line, his head a quarter of the frame height. The sunlit pinnacle stands in "
     "the TOP RIGHT corner and the rock's black shadow fills the BOTTOM third.",
     "friction", 0.6, 0.0),
    # 8
    ("mountain_defile_dawn", "insert", [], 0.8,
     "Insert on a bloody haunch of big-horn slung over Jefferson Hope's buckskin shoulder at dusk, the "
     "fringe of the shirt, the rifle's strap, the grey rocks of a gorge behind dim in the dusk.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the haunch swings a "
     "hand's breadth with his stride; the fringe swings with it; a drop falls from it to the rock.",
     "beside him at the height of his shoulder, an arm's length from the haunch, a 90mm lens. The last "
     "light comes from the RIGHT along the fringe and leaves the gorge behind black",
     "The haunch fills the CENTRE of the frame the height of the middle third over the buckskin "
     "shoulder at the LEFT third. The rifle's strap crosses the BOTTOM LEFT corner. The dim grey rocks "
     "fill the RIGHT third and the TOP edge is black.",
     "friction", 0.5, 0.0),
    # 9
    ("mountain_defile_dawn", "medium", ["jefferson_hope"], 0.95,
     "Medium of Jefferson Hope at the mouth of the defile at nightfall with both bare hands cupped "
     "to his mouth, the sombrero back, the black cliffs behind him, the last grey light on his face from "
     "the right.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the black cliff keeps "
     "the right edge; his hands drop from his mouth; his head tilts a finger's breadth to listen.",
     "on the trail level with his eyes, three long strides from him, a 35mm lens. The last light comes from the RIGHT onto his face and leaves the cliffs black",
     "Jefferson Hope stands at the CENTRE of the frame from the BOTTOM edge to the TOP third, his head a quarter of the frame height, his cupped hands at his mouth at the CENTRE. The black cliffs fill both edges and the grey sky the TOP edge.",
     "friction", 0.7, 0.3),
    # 10 -- silent: the dead fire
    ("camp_night", "wide", [], 0.1,
     "Wide of the nook by night, the fire burned down to a glowing pile of ashes on the bare ground, "
     "the bare ground empty round it and stamped and churned, the boulders black on all sides, the "
     "dead larch bare where the animals stood.",
     "The camera pushes in on the ashes across the whole shot, travelling a hand's breadth; one ember "
     "brightens and dies; a thread of smoke lifts off the pile; a stone on the churned ground catches "
     "the glow.",
     "at the gap in the boulders at a standing man's eye, four long strides from the ashes, a 35mm lens. "
     "The ashes are the light, from the CENTRE, and leave the boulders and the sky black",
     "The glowing ashes lie at the CENTRE of the frame in the BOTTOM third. The stamped ground fills the "
     "BOTTOM half round them in their faint red. The black boulders fill the TOP half from edge to edge "
     "with the gap of starry sky at the TOP CENTRE.",
     "spike", 1.2, 0.5),
    # 11
    ("camp_night", "insert", [], 0.3,
     "Insert on a half-burned branch in Jefferson Hope's bare hand held to his lips, its end blown to a "
     "red flame, the flame lighting his knuckles and the buckskin cuff, the black ground below.",
     "The camera tilts up across the whole shot, travelling a finger's breadth; his breath blows the "
     "ember to a flame; the flame stands up a hand's breadth; the knuckles glow red.",
     "beside his hand at the height of his chest, an arm's length from the brand, a 90mm lens. The "
     "brand is the light, from the CENTRE, and leaves everything beyond the hand black",
     "The brand and the hand fill the CENTRE of the frame the height of the middle third with the "
     "flame at the TOP CENTRE. The buckskin cuff comes in from the RIGHT edge and the ground and the "
     "boulders are black across the BOTTOM third and both edges.",
     "spike", 0.6, 0.0),
    # 12
    ("camp_night", "medium", ["jefferson_hope"], 0.5,
     "Medium of Jefferson Hope crouched over the stamped ground with the brand held low, the sombrero "
     "back, the red light on the churned hoof-marks and on his face from below, the heap of red soil "
     "with its forked stick at the right, the boulders black.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the forked stick keeps "
     "the right third; the brand moves a hand's breadth along the hoof-marks; his head comes up toward "
     "the heap.",
     "beside the dead fire at the height of a crouching man's eye, three long strides from him, a 35mm "
     "lens. The brand is the light, from BELOW at the CENTRE, and leaves the boulders black",
     "Jefferson Hope crouches at the LEFT third of the frame from the BOTTOM edge to the CENTRE line "
     "with the brand's red light on the hoof-marks across the BOTTOM half. The heap of red soil with "
     "its forked stick stands at the RIGHT third the height of a hand. The boulders are black across "
     "the TOP half.",
     "spike", 0.8, 0.0),
    # 13 TURN -- the heap, the stick, the paper, by his own light
    ("camp_night", "medium_close", ["jefferson_hope"], 0.6,
     "Medium close of Jefferson Hope on one knee at the heap of red soil with the brand held up beside "
     "his face, the forked stick and its blank square of paper between him and the lens, the red light "
     "on his face and on the paper, the boulders black behind him.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the forked stick keeps "
     "the frame's centre and the black boulders keep the frame behind him; his eyes go down the paper; the brand comes a hand's breadth nearer the paper.",
     "over the heap level with his eyes, two long strides from him, a 50mm lens. The brand is the "
     "light, from the LEFT beside his face, and leaves the right side of his face and the boulders black",
     "Jefferson Hope's head and shoulders fill the CENTRE of the frame from the TOP third to the BOTTOM "
     "edge, his head a third of the frame's height, the LEFT side red in the brand's light and the RIGHT "
     "side black. The forked stick with its blank paper stands at the CENTRE of the lower third and the "
     "brand burns at the LEFT edge.",
     "turn", 1.0, 0.0),
    # 14 -- the lead's decision, in his own mouth, on his own face
    ("camp_night", "close", ["jefferson_hope"], 0.7,
     "Close on Jefferson Hope's face white in the brand's red light, the black beard, the dark eyes "
     "hard, the brand low at the left of frame, the boulders black behind.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the brand keeps the "
     "left edge and the black boulders keep the frame behind him; his jaw sets on the words; his head "
     "lifts a finger's breadth.",
     "at the heap level with his eyes, an arm's length from him, a 90mm lens. The brand is the light, "
     "from the LEFT and below, and leaves the right side of his face black",
     "Jefferson Hope's face fills the CENTRE of the frame, half the frame height, from the beard at "
     "the BOTTOM third to the hair at the TOP edge, the LEFT side red and the RIGHT side black. The "
     "brand's flame is a red point at the LEFT edge and the boulders are black behind.",
     "reaction", 1.0, 0.3),
    # 15
    ("camp_night", "insert", [], 0.9,
     "Insert on Jefferson Hope's bare hands stirring the ashes to a flame with a stick, a bundle of "
     "cooked meat wrapped in a cloth on the ground beside them, the flame's red light on the knuckles "
     "and the cloth, the ground black beyond.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the stick stirs the "
     "ashes; the flame stands up a hand's breadth; the other hand knots the cloth over the bundle.",
     "over the fire at the height of a crouching man's chest, an arm's length from the hands, a 90mm "
     "lens. The flame is the light, from the CENTRE, and leaves the ground beyond the bundle black",
     "The two hands and the stick fill the CENTRE of the frame the height of the middle third over the "
     "ashes at the BOTTOM CENTRE. The bundle in its cloth lies at the RIGHT third. The ground is black "
     "across the TOP third and the LEFT edge.",
     "transition", 0.5, 0.3),
    # 16
    ("eagle_canyon_day", "wide", [], 0.1,
     "Wide from the rock shelf at the canyon's mouth on a clear day: the wide pale valley far below "
     "with the city's streets small in it and small flags in the streets, a boulder at the left with "
     "its shadow black across the shelf in the sun from the left.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the boulder's black "
     "shadow keeps the bottom left corner; the haze over the far city thins; a hawk crosses the "
     "valley below.",
     "on the rock shelf at a standing man's eye, a 35mm lens. The sun comes from the LEFT, hard, and "
     "throws the boulder's shadow black to the right across the shelf",
     "The rock shelf crosses the BOTTOM third of the frame with the boulder at the LEFT edge and its "
     "black shadow across the BOTTOM LEFT. The pale valley fills the middle of the frame with the city "
     "the height of a finger at its CENTRE and the far hills close the TOP third.",
     "transition", 0.6, 0.3),
    # 17
    ("eagle_canyon_day", "medium_close", ["jefferson_hope"], 0.3,
     "Medium close of Jefferson Hope on the shelf leaning on his rifle, the buckskin torn and dusty, "
     "the sombrero battered, the face white and gaunt with the black beard grown ragged, one gaunt "
     "bare hand up shaken at the city below, the sun from the left hard on him and the brim's shadow black across his eyes.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the rifle keeps the "
     "right third and the pale valley keeps the frame behind him; his gaunt hand shakes once at the "
     "city; his head comes forward a finger's breadth.",
     "on the shelf level with his eyes, two long strides from him, a 50mm lens. The sun comes from the LEFT onto his cheek and leaves the boulder behind him black",
     "Jefferson Hope's hat and shoulders fill the CENTRE of the frame from the TOP third to the BOTTOM "
     "edge, his head a third of the frame's height, the brim's shadow black across his eyes. The rifle stands up along the RIGHT third and the pale valley fills the frame behind him.",
     "friction", 0.8, 0.0),
    # 18 -- Cowper's warning
    ("eagle_canyon_day", "medium_close", ["cowper"], 0.5,
     "Medium close of Cowper drawn up on a bay horse on the shelf in the low-crowned black hat and dark "
     "homespun coat, the broad sun-reddened face anxious under the hat's black shadow, the reins in both bare hands, the bay's ears up at the bottom of the frame.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the horse's neck "
     "keeps the bottom edge and the pale valley keeps the frame behind him; his head turns a finger's "
     "breadth to look back down the canyon; his hands shorten the reins.",
     "on the shelf at the height of a mounted man's eye, two long strides from him, a 50mm lens. The sun comes from the LEFT onto his coat and leaves the hat's shadow on his face black",
     "Cowper's hat and shoulders fill the CENTRE of the frame from the TOP third to the BOTTOM edge, his head a third of the frame's height, the hat's shadow black across his eyes. The bay's ears stand up at the BOTTOM edge and the pale valley fills the frame behind him.",
     "friction", 0.8, 0.0),
    # 19
    ("eagle_canyon_day", "close", ["jefferson_hope"], 0.6,
     "Close on Jefferson Hope's gaunt white face tipped up at the rider, the battered brim pushed back off the forehead, the ragged black beard, the wild eyes wide, the sun from the left hard on the forehead and the horse's dark flank filling the frame behind him.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the horse's flank keeps the frame behind him; his lips part on the words; his hand slides up the rifle's barrel.",
     "on the shelf at the height of the rider's knee, a head above Hope's eyes, an arm's length from him, a 90mm lens. The sun comes from the LEFT onto his forehead and leaves the horse's flank behind him black",
     "Jefferson Hope's tipped-up face fills the CENTRE of the frame, half the frame height, from the ragged beard at the BOTTOM third to the pushed-back brim at the TOP edge, the forehead in sun. The horse's dark flank fills the frame behind him from edge to edge.",
     "friction", 0.6, 0.0),
    # 20 -- married yesterday
    ("eagle_canyon_day", "medium_close", ["cowper"], 0.7,
     "Medium close of Cowper leaning down out of the saddle toward Hope, the black hat's brim low, the broad anxious face bent forward, one bare hand out from the reins, Hope's sombrero crown at the bottom of the frame between them, the sun from the left on the homespun shoulder.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the pale valley keeps "
     "the frame behind him; his hand comes out from the reins a hand's breadth toward Hope; his head "
     "bends a finger's breadth.",
     "beside Hope at the height of a standing man's eye looking up, two long strides from Cowper, a 50mm lens. The sun comes from the LEFT onto his shoulder and leaves the brim's shadow on his face black",
     "Cowper's bent head and shoulders fill the CENTRE of the frame from the TOP edge to the middle third, his head a third of the frame's height, the brim's shadow black across his eyes. His hand comes out into the LEFT third, Hope's sombrero crown cuts the BOTTOM edge and the pale sky fills the frame behind him.",
     "friction", 0.6, 0.0),
    # 21 -- silent: white to the lips
    ("eagle_canyon_day", "close", ["jefferson_hope"], 0.8,
     "Close on Jefferson Hope's head fallen back against the grey boulder, the face white to the lips, the eyes shut, the battered sombrero pushed up off the forehead against the rock, the grey stone filling the frame behind him, the sun from the left on the rock.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the boulder keeps the frame behind him; his eyes open; his head rolls a finger's breadth along the rock.",
     "beside the boulder level with his eyes, an arm's length from him, a 90mm lens. The sun comes from the LEFT onto the rock and leaves the crevice behind his head black",
     "Jefferson Hope's fallen-back face fills the CENTRE of the frame, half the frame height, from the beard at the BOTTOM third to the pushed-up brim at the TOP edge, white in the sun. The grey rock fills the frame behind him from edge to edge with a black crevice at the RIGHT edge.",
     "reaction", 1.2, 0.0),
    # 22 -- death in her face
    ("eagle_canyon_day", "medium_close", ["cowper"], 0.9,
     "Medium close of Cowper from behind his shoulder as the bay horse turns to go, the black hat's back and the homespun shoulder nearest the lens, the broad face turned back over the shoulder to Hope, the canyon trail and the boulders' black shadows below him, the sun from the left.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the canyon trail keeps the frame below him; his chin comes round a finger's breadth over his shoulder on the words; the horse's rump swings a hand's breadth.",
     "behind the horse's flank at the height of a mounted man's shoulder, two long strides from him, a 50mm lens. The sun comes from the LEFT onto his turned cheek and leaves the hat's shadow black",
     "Cowper's turned head and near shoulder fill the CENTRE of the frame from the TOP third to the BOTTOM edge, his head a third of the frame's height, the hat's shadow black on the turned cheek. The horse's rump crosses the BOTTOM RIGHT corner and the canyon trail with its black shadows fills the LEFT third below him.",
     "payoff", 1.0, 0.3),
    # 23
    ("drebber_house_bier", "wide", [], 0.1,
     "Wide of the plastered room in the grey of the morning, the bier across the middle with the white "
     "silent figure under a sheet to the chin, three women in black seated round it with lit candles in "
     "their hands, the plank door black in the far wall, the walls black beyond the candles.",
     "The camera pushes in on the bier across the whole shot, travelling a hand's breadth; the three "
     "candle flames lean together; one woman's head bows; the sheet keeps its fold.",
     "at the near wall at a seated woman's eye, four long strides from the bier, a 35mm lens. The "
     "candles are the light, from the CENTRE, and leave the door and the walls black",
     "The bier crosses the CENTRE of the frame with the white sheet lit by the candles, the three women "
     "seated round it in the BOTTOM half with their candles at the height of their faces. The plank "
     "door stands black at the CENTRE of the upper third and the plastered walls are black along both "
     "edges.",
     "payoff", 0.8, 0.0),
    # 24
    ("drebber_house_bier", "medium", ["jefferson_hope"], 0.4,
     "Medium of the plank door flung open with Jefferson Hope in it, savage and weather-beaten in the "
     "torn brown driving coat, the black beard ragged, the candles' light from the bier on his face "
     "from the front, the grey morning behind him in the doorway, a woman's black shoulder at the left "
     "edge.",
     "The camera pushes in on the doorway across the whole shot, travelling a hand's breadth; the door "
     "leaf swings the last hand's breadth back against the wall; Hope's boot comes down over the "
     "threshold; his hat comes off in his hand.",
     "at the bier's foot at a standing man's eye, three long strides from the door, a 35mm lens. The "
     "candles behind the camera are the light, from the FRONT, and leave the walls black",
     "The plank door stands open at the CENTRE of the frame from the BOTTOM edge to the TOP edge with "
     "Jefferson Hope in it from the BOTTOM edge to the TOP third, his face a quarter of the frame "
     "height. The grey morning fills the doorway round him. The woman's black shoulder cuts the LEFT "
     "edge and the black wall fills the RIGHT third.",
     "payoff", 0.8, 0.0),
    # 25
    ("drebber_house_bier", "insert", [], 0.7,
     "Insert on the white silent face on the bier under the sheet's edge, Jefferson Hope's ragged head "
     "bent over it at the left with his lips at the cold forehead, his bare hand lifting the small pale "
     "hand from the sheet, a candle's light from the right on the white face.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; his lips lift from "
     "the forehead; his hand draws the wedding ring off the small finger; the ring catches the candle.",
     "over the bier at the height of the sheet, an arm's length from the two faces, a 90mm lens. A "
     "candle at the RIGHT is the light and leaves the room behind the heads black",
     "The white face lies across the CENTRE of the frame on the sheet, the height of the middle third, "
     "with Jefferson Hope's ragged head bent over it from the LEFT third. The two hands and the ring "
     "are at the BOTTOM CENTRE on the sheet, the candle burns at the RIGHT edge and the room is black "
     "across the TOP third.",
     "payoff", 1.0, 0.0),
    # 26 BUTTON -- the ring is gone
    ("drebber_house_bier", "medium_close", ["drebber_wife"], 0.9,
     "Medium close of a wife of Drebber's on her feet by the bier in the black dress and white cap, "
     "her candle held up in both bare hands, the thin pale face lit from below by it, her eyes down on "
     "the small pale hand on the sheet at the bottom of the frame, the room black behind her.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the black wall keeps "
     "the frame behind her and the white sheet keeps the bottom edge; her lips part on the words; the candle lifts a hand's breadth.",
     "at the bier's side level with her eyes, two long strides from her, a 50mm lens. Her candle is "
     "the light, from BELOW at the CENTRE, and leaves the wall behind her black",
     "The wife's capped head and shoulders fill the CENTRE of the frame from the TOP third to the BOTTOM "
     "edge, her head a third of the frame's height, lit from below by the candle at the BOTTOM CENTRE. "
     "The white sheet and the small pale hand cross the BOTTOM edge and the wall is black behind her.",
     "button", 0.6, 0.0),
    # 27 -- silent runout: down the canyon trail
    ("eagle_canyon_day", "wide", [], 0.95,
     "Wide down the canyon trail from the shelf's edge on a clear day, Jefferson Hope's back on the pale "
     "trail below walking down between the boulders in the buckskin and sombrero with the rifle over his "
     "shoulder, the boulders' shadows black to the right in the sun from the left, the pale valley and "
     "the city small far below.",
     "The camera pushes in on the trail across the whole shot, travelling a hand's breadth; the black "
     "shadows keep the right half of the trail; Hope walks down the trail toward the valley "
     "growing smaller; dust drifts off his boots.",
     "at the shelf's edge at a standing man's eye with the trail below the lens, a 35mm lens. The sun comes "
     "from the LEFT, hard, and throws the boulders' shadows black to the right across the trail",
     "Jefferson Hope's back is at the CENTRE of the frame the height of the middle third on the pale "
     "trail below, walking down toward the valley. The boulders' black shadows fill the RIGHT half of the trail "
     "and their sunlit faces stand along the LEFT edge. The pale valley with the city the height of a "
     "finger fills the TOP third.",
     "runout", 0.8, 1.5),
]

# (kind, speaker, text, shot)
LINES = [
    ("narration", "john_watson", "All night their road lay through the defiles, and at dawn the peaks lit up one after another.", 0),
    ("narration", "john_watson", "They were a day ahead of the Avenging Angels, and Hope drove them on without mercy.", 1),
    ("narration", "john_watson", "A great rock came thundering down and woke the echoes, and the weary horses broke into a gallop.", 2),
    ("dialogue", "jefferson_hope", "They will be upon our track by now. Everything depends on speed.", 3),
    ("narration", "john_watson", "On the second day the food ran out, so Hope made a fire in a sheltered nook.", 4),
    ("narration", "john_watson", "He shouldered his rifle, and went off after whatever the mountains might give him.", 5),
    ("narration", "john_watson", "Looking back, he saw the old man and the girl crouched over the blaze, the animals behind them.", 6),
    ("narration", "john_watson", "Three hours brought him a big-horn on a pinnacle, and one long steady shot brought it down.", 7),
    ("narration", "john_watson", "With a haunch over his shoulder he turned back, and lost his way among the gorges till dark.", 8),
    ("narration", "john_watson", "At the mouth of the defile he put his hands to his mouth and hallooed. Nothing came back.", 9),
    # shot 10: silent -- the dead fire
    ("narration", "john_watson", "The fire had burned to a pile of ashes, and no one had tended it since he left.", 11),
    ("narration", "john_watson", "The ground was stamped by hooves, and to one side lay a heap of red soil, fresh dug.", 12),
    ("narration", "john_watson", "A stick stood in it, with a paper: John Ferrier, of Salt Lake City. Died August the fourth.", 13),
    ("dialogue", "jefferson_hope", "Then I have one thing left.", 14),
    ("narration", "john_watson", "He cooked what would last him, and walked back through the mountains on the track of the Angels.", 15),
    ("narration", "john_watson", "On the sixth day he stood above the city again, and there were flags in the streets.", 16),
    ("narration", "john_watson", "A rider came up the canyon, a Mormon named Cowper, who owed him a kindness or two.", 17),
    ("dialogue", "cowper", "You are mad to come here. There is a warrant against you from the Holy Four.", 18),
    ("dialogue", "jefferson_hope", "What has become of Lucy Ferrier?", 19),
    ("dialogue", "cowper", "Married yesterday, to young Drebber. Hold up, man, hold up.", 20),
    # shot 21: silent -- white to the lips
    ("dialogue", "cowper", "Stangerson shot her father. And I saw death in her face yesterday.", 22),
    ("narration", "john_watson", "She never held up her head again, and died within the month; the wives sat up with her.", 23),
    ("narration", "john_watson", "In the grey of the morning the door was flung open on a wild weather-beaten man.", 24),
    ("narration", "john_watson", "He kissed the cold forehead, and took the wedding ring from her finger.", 25),
    ("dialogue", "drebber_wife", "The ring is gone.", 26),
    # shot 27: silent -- down into the gorge
]

BEDS = [
    {"from_shot": 0, "tone": "thrilling"},
    {"from_shot": 4, "tone": "plain"},
    {"from_shot": 9, "tone": "uneasy"},
    {"from_shot": 13, "tone": "grave"},
    {"from_shot": 16, "tone": "plain"},
    {"from_shot": 23, "tone": "grave"},
]

TURNS = {13: "a guide with two lives in his hands -> a man with one thing left",
         26: "a bride in the ground -> her ring in his fist and the years ahead"}

# (beat_s, coda_s) by shot; every other shot is 0.5 / 0.0
BEATS = {0: (0.6, 0.4), 3: (1.0, 0.0), 6: (0.5, 0.3), 9: (0.7, 0.3), 10: (1.2, 0.5), 13: (1.0, 0.0),
         14: (1.0, 0.3), 15: (0.5, 0.3), 16: (0.6, 0.3), 21: (1.2, 0.0), 22: (1.0, 0.3), 25: (1.0, 0.0),
         26: (0.6, 0.0), 27: (0.8, 1.5)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, frame, motion, camera, at_rest, section, beat, coda) in enumerate(S):
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces),
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=BEATS.get(i, (0.5, 0.0))[0],
                          coda_s=BEATS.get(i, (0.5, 0.0))[1], turn=TURNS.get(i, ""), cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=12, title="The Avenging Angels",
                question="Today, can Jefferson Hope bring the Ferriers through the mountains?",
                aspect="1:1", where=WHERE, light=LIGHT, protagonist="jefferson_hope", answer="line 12",
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
