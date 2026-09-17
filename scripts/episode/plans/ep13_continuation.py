r"""Episode 13 -- "A Continuation of the Reminiscences of John Watson, M.D.",
Part Two chapter 6.

THE BRICK. One event: the statement at the police station, split by the title
card, with the night at Brixton Road inside it.

  QUESTION  Today, can Jefferson Hope tell his whole story before his heart gives out?
  TURN      shot 15: in the empty house Hope holds the candle up to his own face --
            "Now, Enoch Drebber. Who am I?"  "a cabman in the dark -> Jefferson
            Hope, lit and known".  The lead's own act, on his own face.
  BUTTON    shot 26, the world's answer and the last line: the Inspector at the bell,
            "On Thursday he goes before the magistrates. Until then, he is mine."
            One silent shot after it: Hope walked to the door between two warders.

Written under the ep12 plan_check: closes and MCUs pan, inserts tilt, head
fractions in at_rest, a named light side and a black in every camera, no split
faces, no absences, no facing-away words, a pace on every walk, one shot per
take.  Kept off the picture on purpose: the knife, the blood and the word on the
wall (the image model refuses violence on its OUTPUT, and the owner's rule
forbids lettering), and Stangerson's death, which the narrator says over Hope
on the bench.

Four speakers: the narrator (who also speaks his own line), Hope, Drebber, the
Inspector.  Holmes and Lestrade are on screen and silent; Lucy and Ferrier walk
in the rain beside the horse and say nothing.

Hope has two rows: `jefferson_hope` (indoor: the driving coat, bare-headed) and
`jefferson_hope_cabman` for the one outdoor London setup, because the wardrobe
contract's `outdoor` state for Hope is the Utah sombrero and buckskin.
"""
import json
from pathlib import Path

OUT = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio"
           r"\library\20260822113400_a-study-in-scarlet\episodes\ep13\plan.json")

WHERE = "London, March 1881"
LIGHT = "low raking lamplight, deep black shadow"

SETUPS = {
    "station_desk": dict(
        described=("Interior, inside a small bare charge room at a London police station on a March night "
                   "in 1881, the camera within the room with whitewashed brick walls closed on all four "
                   "sides: a high dark wooden clerk's desk with a sloping top and a ledger open on it, a gas "
                   "jet burning in a brass bracket on the left wall above the desk, a plain wooden bench "
                   "along the right wall, a heavy panelled door in the far wall; the gas jet is the only "
                   "light and it comes from the left, low and yellow, on the desk, the ledger and the faces "
                   "nearest it, and leaves the right wall, the bench and the corners black"),
        cast=["police_inspector", "jefferson_hope", "john_watson"], landmark="the high wooden clerk's desk",
        landmark_at="start", landmark_size="is half the height of the frame",
        route="from the high desk across the bare boards to the panelled door",
        geometry=("The high wooden desk stands at the LEFT third of the frame with the gas jet burning "
                  "above it at the TOP LEFT. The panelled door stands in the far wall at the CENTRE of the "
                  "upper third, black. The bench runs along the RIGHT edge in black shadow and the bare boards fill the BOTTOM third. The gas light reaches the CENTRE of the frame and dies at the RIGHT third."),
        crowd="", outdoors=False, props=[]),
    "euston_platform": dict(
        described=("Interior, inside the great iron-roofed train shed of Euston Station on a March evening "
                   "in 1881, the camera on the platform under the glass roof: a long stone platform beside "
                   "a line of dark railway carriages, iron columns in a row down the platform's edge, a "
                   "porter's barrow stacked with trunks, steam drifting under the roof; the gas lamps hung "
                   "on the columns are the only light and they come from the right, low and yellow, on the "
                   "steam, the trunks and the near faces, and leave the carriages, the roof ironwork and the "
                   "far end of the shed black"),
        cast=["jefferson_hope", "enoch_j_drebber"], landmark="the porter's barrow stacked with trunks",
        landmark_at="start", landmark_size="is half the height of the frame",
        route="from the porter's barrow along the platform to the barrier at the far end",
        geometry=("The line of dark carriages runs along the LEFT edge of the frame into the distance. The "
                  "iron columns stand in a row down the RIGHT third with the gas lamps on them. The porter's "
                  "barrow stands at the BOTTOM RIGHT and the platform runs from the BOTTOM CENTRE to the black far end at the CENTRE of the frame. The glass roof is black across the TOP edge above the steam."),
        crowd=("Travellers in dark coats walk along the platform at a walking pace in twos and threes, a porter in a peaked "
               "cap pushes a barrow of trunks, and steam drifts between the iron columns."),
        outdoors=False, props=[]),
    "cab_night_rain": dict(
        described=("A wet London street of dark brick houses at one in the morning in March 1881, blowing "
                   "hard and raining in torrents: a four-wheeled cab with a dark bay horse standing at the "
                   "kerb, the cabman hunched on the box, the cobbles running with water under a black night sky, a single gas lamp on "
                   "an iron post at the kerb; the gas lamp is the only light and it comes from the right, "
                   "low and yellow, on the wet cobbles, the slanting rain, the horse's streaming flank and "
                   "the cab's wet panels, and leaves the house fronts and the far street black"),
        cast=["jefferson_hope_cabman", "enoch_j_drebber", "john_ferrier", "lucy_ferrier"],
        landmark="the gas lamp on its iron post", landmark_at="start",
        landmark_size="is half the height of the frame",
        route="from the gas lamp at the kerb along the wet street to the garden gate of the empty house",
        geometry=("The gas lamp on its iron post stands at the RIGHT third of the frame with its light on "
                  "the wet cobbles. The cab and the bay horse stand along the kerb across the CENTRE of the "
                  "frame. The dark house fronts fill the LEFT edge and the black street runs to the CENTRE of the upper third. The rain slants across the lamplight from the TOP RIGHT to the BOTTOM LEFT."),
        crowd="", outdoors=True, props=[]),
    "brixton_front_room": dict(
        described=("Interior, inside the empty front room of a shut-up house in the Brixton Road at one in "
                   "the morning, March 1881, the camera within the room with walls closed on all four sides: "
                   "bare floorboards thick with dust, walls of cheap flaring yellow paper peeling in strips "
                   "and blotched with mildew, a mantelpiece of imitation white marble on the left wall, a "
                   "single tall curtainless window in the far wall black with night and streaming with rain, a panelled door in the right wall; "
                   "a single wax candle in a man's hand is the only light and it comes from the candle "
                   "alone, low and yellow, on the faces and hands nearest it and on the peeling paper beside "
                   "it, and leaves the window, the corners and the ceiling black"),
        cast=["jefferson_hope", "enoch_j_drebber"], landmark="the tall rain-streaked window",
        landmark_at="far_end", landmark_size="is half the height of the frame",
        route="from the panelled door across the bare boards to the tall window",
        geometry=("The tall rain-streaked window stands in the far wall at the CENTRE of the upper third, "
                  "grey. The white marble mantelpiece stands along the LEFT wall at the LEFT third. The panelled door is at the RIGHT edge and the bare dusty boards fill the BOTTOM third. The candle's light reaches the middle of the frame and the ceiling is black across the TOP edge."),
        crowd="", outdoors=False, props=[]),
    "station_bench": dict(
        described=("Interior, inside the small bare charge room of the police station on the same March "
                   "night, seen toward its long wall, the camera within the room with whitewashed brick walls "
                   "closed on all four sides: a plain wooden bench along the whitewashed wall, a small deal "
                   "side table beside it with an open note-book and a pencil on it, a second gas jet in a "
                   "brass bracket on the wall above the side table, a heavy panelled door at the left end of "
                   "the wall with a brass bell-pull beside it; the gas jet is the only light and it comes "
                   "from the right, low and yellow, on the table, the note-book and the faces nearest it, and "
                   "leaves the bench's far end, the door and the corners black"),
        cast=["jefferson_hope", "sherlock_holmes", "police_inspector"],
        landmark="the small deal side table with its note-book", landmark_at="start",
        landmark_size="is half the height of the frame",
        route="from the side table along the bench to the panelled door",
        geometry=("The small deal side table stands at the RIGHT third of the frame with the gas jet above "
                  "it at the TOP RIGHT. The wooden bench runs along the whitewashed wall across the middle of "
                  "the frame from the table to the LEFT third. The panelled door stands at the LEFT edge, black, and the bare boards fill the BOTTOM third. The gas light reaches the CENTRE of the frame and dies at the LEFT third."),
        crowd="", outdoors=False, props=[]),
}

# (setup, size, faces, path, frame, motion, camera, at_rest, section)
S = [
    # 0 HOOK -- the prisoner before the desk
    ("station_desk", "wide", [], 0.0,
     "Wide of the small charge room at night: the white-faced Inspector behind the high wooden desk with a "
     "steel pen over the open ledger, Jefferson Hope in the long brownish driving coat standing before the "
     "desk with his wrists manacled in front of him, the gas jet burning above the desk at the left, the "
     "bench along the right wall black.",
     "The camera pushes in on the desk across the whole shot, travelling a hand's breadth; the gas flame flutters in its bracket; a steel pen dips to the ledger; the manacles' chain swings a finger's breadth.",
     "at the panelled door at a standing man's eye, four long strides from the desk, a 35mm lens. The gas "
     "jet comes from the LEFT above the desk and leaves the bench and the right wall black",
     "The high wooden desk stands at the LEFT third of the frame the height of the middle third with the "
     "Inspector behind it and the gas jet at the TOP LEFT. Jefferson Hope stands before the desk at the "
     "CENTRE of the frame, his head a fifth of the frame height. The bench is black along the RIGHT edge "
     "and the bare boards fill the BOTTOM third.",
     "hook"),
    # 1 -- the caution
    ("station_desk", "medium_close", ["police_inspector"], 0.1,
     "Medium close of the police Inspector behind the high desk, the long white bloodless face under the "
     "gas jet, the iron-grey mutton-chop whiskers, the dark blue frock coat buttoned to the throat, a steel "
     "pen held over the open ledger.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the gas jet keeps the top "
     "left corner and the black wall keeps the frame behind him; his heavy lids lift on the words; the pen "
     "comes up a finger's breadth off the ledger.",
     "across the desk level with his eyes, two long strides from him, a 50mm lens. The gas jet comes from "
     "the LEFT onto his face and leaves the wall behind him black",
     "The Inspector's head and shoulders fill the CENTRE of the frame from the TOP third to the desk at the "
     "BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The gas jet burns at the TOP "
     "LEFT corner and the wall behind him is black.",
     "setup"),
    # 2 -- I may never be tried
    ("station_desk", "medium_close", ["jefferson_hope"], 0.2,
     "Medium close of Jefferson Hope before the desk in the long brownish driving coat, the dark fierce face "
     "and full black beard lit from the left, a faint smile, the manacled wrists raised to his chest.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the black wall keeps the "
     "frame behind him; his mouth sets in a smile on the words; his manacled hands lift a hand's breadth "
     "toward his chest.",
     "beside the desk level with his eyes, two long strides from him, a 50mm lens. The gas jet comes from "
     "the LEFT onto his face and leaves the wall behind him black",
     "Jefferson Hope's head and shoulders fill the CENTRE of the frame from the TOP third to the manacled "
     "wrists at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The whitewashed "
     "wall is black behind him at the RIGHT.",
     "setup"),
    # 3 -- the hand on the chest
    ("station_desk", "insert", [], 0.3,
     "Insert on John Watson's bare sunburnt hand laid flat on the breast of Jefferson Hope's brownish "
     "driving coat, the manacled wrists below it, the gas light from the left on the knuckles.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the coat's buttons keep "
     "the frame's centre; the chest under the hand lifts and falls; the hand presses a finger's breadth "
     "into the cloth.",
     "beside the two men at the height of a man's chest, an arm's length from the hand, a 90mm lens. The "
     "gas jet comes from the LEFT onto the knuckles and leaves the coat's far side black",
     "Watson's bare sunburnt hand lies flat across the CENTRE of the frame on the brownish cloth, the height "
     "of the middle third. The manacled wrists cross the BOTTOM third and the coat's far side is black at "
     "the RIGHT edge.",
     "friction"),
    # 4 -- the narrator's own line
    ("station_desk", "close", ["john_watson"], 0.4,
     "Close on John Watson's sunburnt face, the thin waxed moustache, the dark hair swept back, the eyes "
     "wide on the man before him, the gas light from the left.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the black wall keeps the "
     "frame behind him; his brows come up on the words; his head draws back a finger's breadth.",
     "beside Hope's shoulder level with Watson's eyes, an arm's length from him, a 90mm lens. The gas jet "
     "comes from the LEFT onto his face and leaves the wall behind him black",
     "John Watson's face fills the CENTRE of the frame, half the frame height, from the moustache at the "
     "BOTTOM third to the swept-back hair at the TOP edge, lit from the LEFT. The whitewashed wall is black "
     "behind him.",
     "friction"),
    # 5 -- Euston
    ("euston_platform", "wide", [], 0.0,
     "Wide down the long platform under the iron roof of Euston Station at evening, the dark carriages "
     "along the left, steam drifting between the iron columns, the gas lamps on the columns at the right, "
     "travellers in dark coats walking in twos and threes, a porter's barrow of trunks in the foreground.",
     "The camera pushes in along the platform across the whole shot, travelling a hand's breadth; steam "
     "rolls between the columns; the travellers walk on at a walking pace; a porter pushes the barrow a "
     "hand's breadth.",
     "on the platform beside the barrow at a standing man's eye, a 35mm lens. The gas lamps come from the "
     "RIGHT onto the steam and leave the carriages and the far end of the shed black",
     "The porter's barrow of trunks stands at the BOTTOM RIGHT of the frame the height of the middle third. "
     "The dark carriages run along the LEFT edge into the distance and the iron columns with their lamps "
     "stand down the RIGHT third. The platform runs to the black far end at the CENTRE.",
     "transition"),
    # 6 -- Hope at the column
    ("euston_platform", "medium", ["jefferson_hope"], 0.4,
     "Medium of Jefferson Hope bare-headed in the long brownish driving coat standing against an iron "
     "column on the platform, the black beard, the dark eyes fixed along the platform, steam drifting past "
     "him, the gas lamp above him at the right.",
     "The camera pans left across the whole shot, travelling a hand's breadth; the iron column keeps the "
     "right third; steam drifts across his chest; his head turns a finger's breadth along the platform.",
     "on the platform level with his eyes, three long strides from him, a 35mm lens. The gas lamp comes "
     "from the RIGHT onto his face and leaves the carriages behind him black",
     "Jefferson Hope stands at the CENTRE of the frame from the BOTTOM edge to the TOP third, his head a "
     "quarter of the frame height, lit from the RIGHT. The iron column stands up the RIGHT third and the "
     "dark carriages fill the LEFT edge.",
     "transition"),
    # 7 -- Drebber goes off alone
    ("euston_platform", "medium", ["enoch_j_drebber"], 0.8,
     "Medium of Enoch Drebber bare-headed in the heavy black broadcloth frock coat walking up the platform "
     "through the steam at a walking pace, the coarse florid face flushed and scowling, the gold watch chain "
     "across the waistcoat, the gas lamps at the right.",
     "The camera pans right across the whole shot, travelling a hand's breadth; the iron columns keep the "
     "right third; Drebber walks along the platform to the barrier at a walking pace; his thick hand swings a hand's breadth.",
     "on the platform at a standing man's eye, three long strides from him, a 35mm lens. The gas lamps "
     "come from the RIGHT onto his face and leave the carriages behind him black",
     "Enoch Drebber stands at the CENTRE of the frame from the BOTTOM edge to the TOP third, his head a "
     "quarter of the frame height, lit from the RIGHT, the steam round his coat. The iron columns stand "
     "down the RIGHT third and the dark carriages fill the LEFT edge.",
     "friction"),
    # 8 -- the cab in the rain
    ("cab_night_rain", "wide", [], 0.1,
     "Wide of the wet street at night in driving rain: the four-wheeled cab and its dark bay horse standing "
     "at the kerb under the gas lamp, Jefferson Hope in the low black cap hunched on the box with "
     "the reins, the brick house fronts black, the cobbles running with water.",
     "The camera pushes in on the cab across the whole shot, travelling a hand's breadth; the rain slants "
     "through the lamplight; water runs off the cab's roof; the horse's head comes down a hand's breadth.",
     "across the street at a standing man's eye, five long strides from the cab, a 35mm lens. The gas lamp "
     "comes from the RIGHT onto the wet cobbles and leaves the house fronts black",
     "The cab and the bay horse stand along the kerb across the CENTRE of the frame the height of the middle "
     "third, the cabman hunched on the box. The gas lamp on its post stands at the RIGHT third with the rain "
     "slanting through its light. The house fronts are black along the LEFT edge and the wet cobbles fill "
     "the BOTTOM third.",
     "transition"),
    # 9 -- the two pills
    ("cab_night_rain", "insert", [], 0.3,
     "Insert on a small round wooden pill box open in Jefferson Hope's bare brown palm on the cab box, two "
     "small white pills inside it, raindrops on the open lid, the wet coat sleeve at the edge.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the open box keeps the "
     "frame's centre; a raindrop lands on the lid; the thumb closes the lid a finger's breadth.",
     "over his lap at the height of his chest, an arm's length from the palm, a 90mm lens. The gas lamp "
     "comes from the RIGHT onto the palm and leaves the street below black",
     "The open pill box sits in the bare palm at the CENTRE of the frame, the height of a hand, the two "
     "white pills plain in it. The wet brownish sleeve comes in from the LEFT edge and the street is black "
     "across the TOP third.",
     "friction"),
    # 10 -- the two who walk beside the horse
    ("cab_night_rain", "medium", [], 0.5,
     "Medium over Jefferson Hope's shoulder and low black cap on the box, the reins in his bare "
     "hands, the bay horse's wet back and ears in the rain, and walking in the rain one on each side of the "
     "horse's head the pale figures of an old grey-bearded man in a brown felt hat and a young woman with "
     "long chestnut hair, both with their faces toward the cab, smiling.",
     "The camera pushes in over his shoulder across the whole shot, travelling a hand's breadth; the rain "
     "slants across the lamplight; the horse walks on at a walking pace; the two pale figures walk beside "
     "its head at a walking pace.",
     "on the cab's roof behind the box at the height of his shoulder, an arm's length from his hat, a 35mm "
     "lens. The gas lamp comes from the RIGHT onto the wet horse and leaves the street beyond black",
     "Jefferson Hope's hat and shoulder fill the BOTTOM LEFT corner of the frame, the reins running to the "
     "horse's wet back at the CENTRE of the lower third. The pale old man walks at the LEFT third and the "
     "pale young woman at the RIGHT third, each the height of a finger, one on each side of the horse's "
     "head. The street is black across the TOP third.",
     "friction"),
    # 11 -- silent: his face on the box
    ("cab_night_rain", "close", ["jefferson_hope_cabman"], 0.6,
     "Close on Jefferson Hope's face on the box in the rain under the low black cap, the full black "
     "beard wet, the dark eyes fixed on the road, the lamplight from the right on the wet cheek.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the black street keeps the "
     "frame behind him; rain runs off the hat's brim; his chin lifts a finger's breadth.",
     "beside the box level with his eyes, an arm's length from him, a 90mm lens. The gas lamp comes from "
     "the RIGHT onto his wet cheek and leaves the street behind him black",
     "Jefferson Hope's face fills the CENTRE of the frame, half the frame height, from the wet beard at the "
     "BOTTOM third to the hat's brim at the TOP edge, lit from the RIGHT. The rain slants across the black "
     "street behind him.",
     "spike"),
    # 12 -- waking the passenger
    ("cab_night_rain", "medium", ["enoch_j_drebber"], 0.9,
     "Medium of the open door of the four-wheeled cab in the rain, Enoch Drebber slumped asleep inside on "
     "the seat in his tall black hat and broadcloth coat, the florid face slack, and Jefferson Hope's "
     "bare brown hand on his arm in the doorway at the left.",
     "The camera pushes in on the doorway across the whole shot, travelling a hand's breadth; rain drips "
     "off the door's edge; Hope's hand shakes Drebber's arm; Drebber's head lifts off the cushion.",
     "at the kerb beside the cab door at the height of a seated man's eye, two long strides from him, a "
     "50mm lens. The gas lamp comes from the RIGHT into the cab and leaves the cab's far corner black",
     "Enoch Drebber sits slumped at the CENTRE of the frame inside the cab door, his head a quarter of the "
     "frame height under the top hat, lit from the RIGHT. Hope's bare hand and wet sleeve come in from the "
     "LEFT edge onto his arm and the cab's far corner is black.",
     "transition"),
    # 13 -- the match
    ("brixton_front_room", "insert", [], 0.1,
     "Insert on a struck match flaring in Jefferson Hope's bare brown fingers as it touches the wick of a "
     "white wax candle in his other hand, the dark driving coat behind.",
     "The camera tilts up across the whole shot, travelling a finger's breadth; the candle keeps the "
     "frame's centre; the wick catches and the flame stands up a finger's breadth; the match comes away "
     "from the wick.",
     "beside his hands at the height of his chest, an arm's length from the candle, a 90mm lens. The match "
     "is the light, from the CENTRE, and leaves everything beyond the hands black",
     "The white candle and the flaring match fill the CENTRE of the frame, the height of the middle third, "
     "with the two bare hands round them. The dark coat is black across the BOTTOM third and both edges.",
     "transition"),
    # 14 -- the empty room
    ("brixton_front_room", "wide", [], 0.3,
     "Wide of the empty front room by the light of one wax candle: Jefferson Hope bare-headed in the long "
     "driving coat holding the lit candle up at the left, Enoch Drebber bare-headed and swaying in his "
     "broadcloth coat at the centre, the peeling yellow paper, the tall window streaming with rain in the "
     "far wall, the bare boards thick with dust.",
     "The camera pushes in on the two men across the whole shot, travelling a hand's breadth; the candle "
     "flame leans and steadies; Drebber sways on his heels; Hope's candle lifts a hand's breadth.",
     "at the white marble mantelpiece at a standing man's eye, four long strides from the men, a 35mm "
     "lens. The candle is the light, from the LEFT, and leaves the window, the corners and the ceiling black",
     "Jefferson Hope stands at the LEFT third of the frame holding the candle at the height of his "
     "shoulder, Enoch Drebber at the CENTRE, each from the BOTTOM edge to the TOP third. The tall "
     "rain-streaked window stands grey at the CENTRE of the upper third and the peeling paper is black "
     "beyond the candle's reach.",
     "spike"),
    # 15 TURN -- the candle to his own face
    ("brixton_front_room", "medium_close", ["jefferson_hope"], 0.5,
     "Medium close of Jefferson Hope holding the lit wax candle up beside his own face, the flame lighting "
     "the dark fierce face, the full black beard and the deep-set eyes from the left, the peeling yellow "
     "paper black behind him.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the candle keeps the "
     "left third and the black wall keeps the frame behind him; his lips part on the words; the candle "
     "comes a hand's breadth nearer his face.",
     "across the bare boards level with his eyes, two long strides from him, a 50mm lens. The candle is "
     "the light, from the LEFT beside his face, and leaves the wall behind him black",
     "Jefferson Hope's head and shoulders fill the CENTRE of the frame from the TOP third to the BOTTOM "
     "edge, his head a third of the frame's height, lit from the LEFT by the candle at the LEFT third. The "
     "peeling paper is black behind him.",
     "turn"),
    # 16 -- the horror comes
    ("brixton_front_room", "close", ["enoch_j_drebber"], 0.6,
     "Close on Enoch Drebber's coarse florid face in the candlelight, the small bleared eyes wide with "
     "horror, sweat standing on the low forehead, the jowls slack, the curly hair damp.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the black window keeps "
     "the frame behind him; sweat runs down his brow; his head pulls back a hand's breadth.",
     "facing him level with his eyes, an arm's length from him, a 90mm lens. The candle is the light, from "
     "the LEFT, and leaves the window behind him black",
     "Enoch Drebber's face fills the CENTRE of the frame, half the frame height, from the stubbly beard at the BOTTOM third to the curly hair at the TOP edge, lit from the LEFT. The window is black "
     "behind him.",
     "reaction"),
    # 17 -- would you murder me
    ("brixton_front_room", "medium_close", ["enoch_j_drebber"], 0.7,
     "Medium close of Enoch Drebber backed against the rain-streaked window, both thick bare hands up "
     "before his chest, the florid face livid, the lips trembling, the candle's light from the left.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the grey window keeps "
     "the frame behind him; his lips tremble on the words; his thick hands lift a hand's breadth before his "
     "chest.",
     "across the room level with his eyes, two long strides from him, a 50mm lens. The candle is the "
     "light, from the LEFT, and leaves the window frame behind him black",
     "Enoch Drebber's head and shoulders fill the CENTRE of the frame from the TOP third to his raised "
     "hands at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. The "
     "rain-streaked window stands grey behind him.",
     "friction"),
    # 18 -- the box held out
    ("brixton_front_room", "insert", [], 0.75,
     "Insert on the small round wooden pill box held out open in Jefferson Hope's bare brown hand toward "
     "the lens, the two small white pills inside, the candle flame behind the hand at the left, the dark "
     "room beyond.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the candle keeps the "
     "left third; the box comes forward a finger's breadth; the fingers tip the box a finger's breadth "
     "toward the lens.",
     "facing the hand at the height of a man's chest, an arm's length from the box, a 90mm lens. The "
     "candle is the light, from the LEFT behind the hand, and leaves the room beyond black",
     "The open pill box sits in the bare hand at the CENTRE of the frame, the height of a hand, the two "
     "white pills plain in it. The candle flame burns at the LEFT third and the room is black beyond.",
     "payoff"),
    # 19 -- justice upon the earth
    ("brixton_front_room", "close", ["jefferson_hope"], 0.8,
     "Close on Jefferson Hope's face in profile turned toward the right of frame, the candle held low under his chin lighting the full black beard and the jaw from beneath, the deep-set eye blazing, the rain-streaked window grey behind him.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the grey window keeps the frame behind him; his jaw sets on the words; his head comes forward a finger's breadth toward the right edge.",
     "at his shoulder level with his cheek, an arm's length from him, a 90mm lens. The candle is the light, from BELOW at the CENTRE, and leaves the room above him black",
     "Jefferson Hope's profile fills the CENTRE of the frame, half the frame height, facing the RIGHT edge, from the beard at the BOTTOM third to the black hair at the TOP edge, lit from below. The candle flame is a yellow point at the BOTTOM CENTRE and the grey window stands behind him.",
     "payoff"),
    # 20 -- the ring
    ("brixton_front_room", "insert", [], 0.9,
     "Insert on a small plain gold wedding ring held up between Jefferson Hope's bare brown finger and "
     "thumb in the candlelight, Drebber's dark coat shoulder at the right edge of frame, the room black "
     "beyond.",
     "The camera tilts up across the whole shot, travelling a finger's breadth; the ring keeps the frame's "
     "centre; the ring turns a finger's breadth and catches the flame; the fingers lift it a finger's "
     "breadth.",
     "beside Drebber's shoulder at the height of his eyes, an arm's length from the ring, a 90mm lens. The "
     "candle is the light, from the LEFT, and leaves the room beyond the fingers black",
     "The gold ring stands at the CENTRE of the frame between finger and thumb, the height of a finger, "
     "catching the flame. Drebber's dark shoulder fills the RIGHT edge and the room is black across the TOP "
     "third.",
     "payoff"),
    # 21 -- it was quick
    ("brixton_front_room", "wide", [], 1.0,
     "Wide of the empty front room by candlelight: Enoch Drebber's heavy body in the black broadcloth coat "
     "lying on its back on the dusty boards before the rain-streaked window, the thick hands flung out, "
     "Jefferson Hope standing over it at the left with the candle held low.",
     "The camera pushes in on the window across the whole shot, travelling a hand's breadth; the candle "
     "flame leans; rain runs down the window's panes; Hope's candle comes down a hand's breadth toward the "
     "boards.",
     "at the panelled door at a standing man's eye, four long strides from the window, a 35mm lens. The "
     "candle is the light, from the LEFT, and leaves the corners and the ceiling black",
     "Enoch Drebber's body lies across the CENTRE of the lower third on the dusty boards, the height of a "
     "hand. Jefferson Hope stands at the LEFT third from the BOTTOM edge to the TOP third with the candle "
     "held low. The rain-streaked window stands grey at the CENTRE of the upper third.",
     "payoff"),
    # 22 -- back on the bench
    ("station_bench", "medium", ["jefferson_hope"], 0.2,
     "Medium of Jefferson Hope sitting back on the wooden bench against the whitewashed wall in the long "
     "brownish driving coat, the manacled wrists in his lap, the dark face tired and sweating under the gas "
     "light from the right.",
     "The camera pushes in on the bench across the whole shot, travelling a hand's breadth; the gas flame "
     "flutters; his head goes back against the wall; his manacled hands turn over in his lap.",
     "across the room at a seated man's eye, three long strides from him, a 35mm lens. The gas jet comes "
     "from the RIGHT onto his face and leaves the far end of the bench black",
     "Jefferson Hope sits at the CENTRE of the frame from the BOTTOM edge to the TOP third, his head a "
     "quarter of the frame height, lit from the RIGHT. The bench runs to the LEFT third into black and the "
     "whitewashed wall stands behind him.",
     "payoff"),
    # 23 -- the pencil
    ("station_bench", "insert", [], 0.4,
     "Insert on a sallow hand moving a pencil across an open note-book on the small deal side table under "
     "the gas jet, the page grey with close pencil strokes.",
     "The camera tilts down across the whole shot, travelling a finger's breadth; the note-book keeps the "
     "frame's centre; the pencil runs along the page a finger's breadth; the hand turns the page's corner "
     "up.",
     "over the side table at the height of a seated man's eye, an arm's length from the note-book, a 90mm "
     "lens. The gas jet comes from the RIGHT onto the page and leaves the table's far edge black",
     "The open note-book lies at the CENTRE of the frame the height of the middle third with the sallow "
     "hand and the pencil on it. The gas light falls from the RIGHT and the table's far edge is black "
     "across the TOP third.",
     "payoff"),
    # 24 -- Holmes's one question
    ("station_bench", "medium_close", ["sherlock_holmes"], 0.6,
     "Medium close of Sherlock Holmes standing by the side table in the bottle-green velvet jacket, the lean "
     "pale face and the high forehead under the gas light from the right, the eyes keen on the man on the "
     "bench.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the gas jet keeps the top "
     "right corner and the whitewashed wall keeps the frame behind him; his brows lift a finger's breadth; "
     "his right hand comes up to his chin.",
     "beside the bench level with his eyes, two long strides from him, a 50mm lens. The gas jet comes from "
     "the RIGHT onto his face and leaves the wall behind him black",
     "Sherlock Holmes's head and shoulders fill the CENTRE of the frame from the TOP third to the green "
     "velvet at the BOTTOM edge, his head a third of the frame's height, lit from the RIGHT. The gas jet "
     "burns at the TOP RIGHT and the wall is black behind him at the LEFT.",
     "payoff"),
    # 25 -- my own secrets
    ("station_bench", "medium_close", ["jefferson_hope"], 0.7,
     "Medium close of Jefferson Hope on the bench, the dark fierce face turned up toward Holmes with a "
     "smile in the full black beard, the manacled wrists at the bottom of the frame, the gas light from the "
     "right.",
     "The camera pans right across the whole shot, travelling a finger's breadth; the whitewashed wall "
     "keeps the frame behind him; one eye closes in a wink on the words; his manacled hands lift a finger's "
     "breadth off his knees.",
     "across from the bench level with his eyes, two long strides from him, a 50mm lens. The gas jet comes "
     "from the RIGHT onto his face and leaves the far end of the bench black",
     "Jefferson Hope's head and shoulders fill the CENTRE of the frame from the TOP third to the manacled "
     "wrists at the BOTTOM edge, his head a third of the frame's height, lit from the RIGHT. The bench's "
     "far end is black at the LEFT.",
     "payoff"),
    # 26 BUTTON -- Thursday
    ("station_bench", "medium_close", ["police_inspector"], 0.8,
     "Medium close of the police Inspector standing by the panelled door with one bare hand on the brass "
     "bell-pull, the long white face grave, the iron-grey mutton-chop whiskers, the dark blue frock coat "
     "buttoned to the throat, the gas light from the right.",
     "The camera pans left across the whole shot, travelling a finger's breadth; the black door keeps the "
     "frame behind him; his thin lips move on the words; his hand pulls the bell-pull down a hand's breadth.",
     "beside the side table level with his eyes, two long strides from him, a 50mm lens. The gas jet comes "
     "from the RIGHT onto his face and leaves the door behind him black",
     "The Inspector's head and shoulders fill the CENTRE of the frame from the TOP third to the BOTTOM "
     "edge, his head a third of the frame's height, lit from the RIGHT, his hand on the bell-pull at the "
     "LEFT third. The panelled door is black behind him.",
     "button"),
    # 27 -- silent runout: to the door between two warders
    ("station_bench", "wide", [], 1.0,
     "Wide of the charge room by gas light: Jefferson Hope in the long brownish driving coat walking at a "
     "walking pace between two warders in dark blue coats toward the open panelled door at the left, the "
     "manacled wrists in front of him, the side table and the bench at the right.",
     "The camera pushes in on the doorway across the whole shot, travelling a hand's breadth; the gas "
     "flame flutters; the three men walk to the open door at a walking pace; the door swings a hand's "
     "breadth wider.",
     "beside the side table at a standing man's eye, four long strides from the door, a 35mm lens. The gas "
     "jet comes from the RIGHT onto the three men and leaves the doorway black",
     "Jefferson Hope walks at the CENTRE of the frame between the two warders from the BOTTOM edge to the "
     "TOP third, his head a fifth of the frame height. The open panelled door is black at the LEFT third, "
     "and the side table stands at the RIGHT edge under the gas jet.",
     "runout"),
]

# (kind, speaker, text, shot)
LINES = [
    ("narration", "john_watson", "We drove him to the station in his own cab, and he came as quiet as a lamb.", 0),
    ("dialogue", "police_inspector", "Have you anything to say? It will be taken down.", 1),
    ("dialogue", "jefferson_hope", "I may never be tried.", 2),
    ("narration", "john_watson", "I put my hand on his chest. Inside, something throbbed like an engine in a shed.", 3),
    ("dialogue", "john_watson", "You have an aortic aneurism!", 4),
    ("narration", "john_watson", "He sat down, and told us the whole of it as calmly as a man reading a timetable.", 5),
    ("narration", "john_watson", "For two weeks he had driven behind Drebber and Stangerson, and never once found them apart.", 6),
    ("narration", "john_watson", "Then at Euston they missed the Liverpool train, and Drebber went off alone into the night.", 7),
    ("narration", "john_watson", "Hope drove him from one gin palace to the next, until the man could barely stand.", 8),
    ("narration", "john_watson", "In his pocket was a little box with two pills in it, and only one was poisoned.", 9),
    ("narration", "john_watson", "All the way, John Ferrier and Lucy walked ahead of the horse in the rain, one each side.", 10),
    # shot 11: silent -- his face on the box
    ("narration", "john_watson", "At Brixton Road he woke his passenger, and walked him up the garden to the empty house.", 12),
    ("narration", "john_watson", "It was black inside. Hope struck a match, and lit a wax candle he had brought.", 13),
    ("narration", "john_watson", "Drebber stamped about the dust, grumbling at the dark, and waiting to be shown his room.", 14),
    ("dialogue", "jefferson_hope", "Now then, Enoch Drebber. Look at my face, and tell me who I am.", 15),
    ("narration", "john_watson", "The drink went out of his eyes, and the horror came into them. He knew.", 16),
    ("dialogue", "enoch_j_drebber", "Would you murder me?", 17),
    ("narration", "john_watson", "Hope held out the box. Drebber was to choose, and Hope would swallow the pill that was left.", 18),
    ("dialogue", "jefferson_hope", "Let us see if there is justice upon the earth.", 19),
    ("narration", "john_watson", "When the poison took hold, Hope held Lucy's wedding ring up before his eyes.", 20),
    ("narration", "john_watson", "It was quick. He threw out his hands, and fell, and never moved again.", 21),
    ("narration", "john_watson", "Stangerson he found two days later, and gave the same choice. The man flew at his throat.", 22),
    ("narration", "john_watson", "When he stopped, nobody spoke. There was only the scratch of Lestrade's pencil.", 23),
    ("narration", "john_watson", "Holmes had one question left: who had come to our rooms for the ring?", 24),
    ("dialogue", "jefferson_hope", "I can tell my own secrets, but not other people's.", 25),
    ("dialogue", "police_inspector", "On Thursday he goes before the magistrates. Until then, he is mine.", 26),
    # shot 27: silent -- to the door between two warders
]

BEDS = [
    {"from_shot": 0, "tone": "grave"},
    {"from_shot": 5, "tone": "uneasy"},
    {"from_shot": 8, "tone": "thrilling"},
    {"from_shot": 15, "tone": "grave"},
    {"from_shot": 22, "tone": "plain"},
]

TURNS = {15: "a cabman in the dark -> Jefferson Hope, lit and known",
         26: "a whole confession -> the law's Thursday"}

# (beat_s, coda_s) by shot; every other shot is 0.5 / 0.0
BEATS = {0: (0.6, 0.3), 1: (0.8, 0.4), 2: (1.0, 0.0), 4: (1.0, 0.3), 5: (0.6, 0.3), 10: (0.6, 0.2), 11: (1.2, 0.3),
         14: (1.0, 0.3), 15: (1.0, 0.0), 16: (0.8, 0.0), 17: (0.6, 0.0), 19: (0.8, 0.0), 20: (0.6, 0.0),
         21: (0.8, 0.5), 23: (0.6, 0.0), 25: (1.0, 0.0), 26: (0.6, 0.0), 27: (0.8, 1.5)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, frame, motion, camera, at_rest, section) in enumerate(S):
        beat, coda = BEATS.get(i, (0.5, 0.0))
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces),
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=13, title="A Continuation of the Reminiscences of John Watson, M.D.",
                question="Today, can Jefferson Hope tell his whole story before his heart gives out?",
                aspect="1:1", where=WHERE, light=LIGHT, protagonist="jefferson_hope", answer="line 22",
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
