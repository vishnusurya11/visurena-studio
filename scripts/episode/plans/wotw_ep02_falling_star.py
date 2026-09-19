r"""The War of the Worlds, episode 2 -- "The Falling Star", chapter 2.

THE BRICK. One event: the morning the Thing is found, and the one man who
saw it open has to make somebody believe him.

  QUESTION  Today, can Ogilvy make anyone believe what lies in the pit?
  TURN      shot 16, Ogilvy's own act on his own face: over Henderson's palings
            he names it -- "an artificial cylinder, man!"
            "a madman nobody hears -> believed".
  ANSWER    line 20, the newspaper boy: the whole town believes, in its own
            form -- "Dead men from Mars, sir!"
  BUTTON    shot 22, the boy's line, the last one, and not the lead's.

REFERENCES-ONLY (owner 2026-09-18). Each take gets the one wide of its place,
the one sheet of each person in it and, in the pit, the one sheet of the
cylinder; everything else is words. Chapter 2's wardrobe is said in every frame.

CAMERA (owner 2026-09-19, docs/calibration/camera_catalog.md). ep01 was 18 pans
of 23, each an orbit request. Here: thirteen move ids, none on more than four
shots, no move twice in a row, no orbit; a pan names where it ARRIVES and no
pan or track "keeps" anything. The move id of each shot is in MOVES.

THE CYLINDER'S SIZE (owner undecided; Wells followed): about thirty yards
across, lying half-buried, its circular end a wall of crusted metal taller than
a house beside a man at its foot.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep02" / "plan.json"

WHERE = "Surrey, 1894"
LIGHT = "low raking sunlight, long black shadow"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

NARR = "the Narrator in the grey herringbone tweed suit, bare-headed, his dark hair parted on the left"
NARR_OUT = "the Narrator in the grey herringbone tweed suit and straw boater with a black band"
OGIL = ("Ogilvy, bare-headed with his auburn hair blown wild, in the mustard-ochre tweed suit and round "
        "steel spectacles, his trousers dark with dew to the knee")
HEND = ("Henderson in white shirtsleeves rolled to the elbow and the black-and-grey striped waistcoat, "
        "bare-headed, his brown hair oiled flat")
WAGG = ("the waggoner in the wide-brimmed black felt hat and the oatmeal linen smock frock, the long "
        "whip over his shoulder")
BOY = ("the newspaper boy in the grey flat cap and the ginger corduroy jacket with patched elbows, the "
       "canvas bag on its strap across his chest")
CYL = "the huge crusted cylinder"

PIT_DESCRIBED = (
    "A great raw crater on Horsell Common at sunrise in 1894: sloping walls of loose yellow sand and grey "
    "gravel, a charred rim ringed with flung heaps of spoil, splintered fir wood on the gravel floor, and "
    "lying half-buried across the pit a colossal cylinder thirty yards across, its huge circular end tilted "
    "up out of the sand, its whole skin caked in a scaly dun-grey crust of clinker; pines and purple heather "
    "stand on the far rim under a pale sky; the low sun comes from the LEFT over the far rim, hard and "
    "yellow on the crust, and leaves the pit's near wall and the underside of the cylinder black")
PIT_GEOMETRY = (
    "The circular end of the cylinder fills the CENTRE of the frame, its crusted face turned toward the "
    "camera, the height of half the frame. The yellow sand walls slope down from the LEFT edge and the "
    "RIGHT edge to the grey gravel floor at the BOTTOM. Splintered fir wood lies on the gravel at the "
    "BOTTOM LEFT. Purple heather and dark pines line the far rim across the TOP third under a pale sky.")

SETUPS = {
    "study": dict(
        described=("Interior, inside the narrator's upstairs study at Maybury at night in 1894, the camera "
                   "within the room with walls closed on all sides: a mahogany writing-table with a green "
                   "leather top and stacked manuscript sheets, a brass inkstand, a green-shaded brass oil "
                   "lamp, a pair of glazed French windows with a low iron rail and a raised cream blind "
                   "showing the starry night sky and dark beech tops, oak bookcases and a globe; the "
                   "green-shaded lamp is the only light and it comes from low at the right onto the table "
                   "and the pages, and leaves the bookcases, the corners and the night in the windows black"),
        cast=["unnamed_first_person_narrator"], landmark="the French windows over the night",
        landmark_at="start", landmark_size="is half the height of the frame",
        route="from the green lamp on the writing-table to the French windows",
        geometry=("The glazed French windows stand across the LEFT half of the frame with the starry sky "
                  "and the dark beech tops in the glass. The writing-table crosses the BOTTOM half with "
                  "the stacked pages at the CENTRE and the green-shaded lamp at the RIGHT third. The oak "
                  "bookcase is dark at the RIGHT edge and the ceiling is black across the TOP."),
        crowd="", outdoors=False, props=[], location="narrators_study"),
    "heath": dict(
        described=("Horsell Common at sunrise in 1894: knee-deep purple-brown heather and dark furze, two "
                   "young Scots pines in the foreground, low raw mounds of flung yellow sand and grey "
                   "gravel ringing a crater a hundred yards off, a thin blue smoke rising from burning "
                   "heather to the east, the old sand-pits with yellow digging faces, a pale sandy road "
                   "crossing the heath at the left, and on the horizon the black roofs and church tower "
                   "of Woking among scattered pines under a lemon-yellow sky; the low sun comes from "
                   "BEHIND the far pines, gold on the sand heaps, and leaves the near heather black"),
        cast=["ogilvy", "unnamed_waggoner"], landmark="the raw mound of flung sand",
        landmark_at="far_end", landmark_size="is a quarter of the height of the frame",
        route="from the near heather across the heath to the sand mound and the road to Woking",
        geometry=("The low raw mound of flung yellow sand lies across the CENTRE of the frame a hundred "
                  "yards off, the height of a fingernail. Knee-deep heather fills the BOTTOM half, the "
                  "two young Scots pines stand at the LEFT third and the RIGHT third, the pale sandy road "
                  "crosses at the LEFT edge, and the church tower of Woking rises small on the horizon "
                  "at the CENTRE under the lemon sky across the TOP."),
        crowd="", outdoors=True, props=[], location="horsell_common"),
    "pit": dict(
        described=PIT_DESCRIBED, cast=["ogilvy"], landmark="the crusted circular end of the cylinder",
        landmark_at="far_end", landmark_size="is half the height of the frame",
        route="from the charred rim down the sand wall to the crusted end of the cylinder",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "floor": dict(
        described=PIT_DESCRIBED, cast=["ogilvy", "henderson"],
        landmark="the bright seam at the rim of the lid", landmark_at="far_end",
        landmark_size="is the height of a hand",
        route="from the foot of the crusted end back up the sand wall to the rim",
        geometry=PIT_GEOMETRY, crowd="", outdoors=True, props=["martian_cylinder"],
        location="horsell_pit"),
    "garden": dict(
        described=("A quiet street in Woking at half past six on an early summer morning in 1894: a "
                   "waist-high fence of white-painted pointed palings with a wicket gate fronting a small "
                   "vegetable garden of peas on sticks, lettuces and runner beans on canes, the dug soil "
                   "dark, a semi-detached yellow-brick villa with a slate roof, a gabled wooden porch over "
                   "a green door and a bay window, a cast-iron gas lamp at the kerb and flagstones on the "
                   "pavement; the low sun comes from the RIGHT, raking across the palings and the rows, "
                   "and leaves the porch, the bay window and the shadows of the palings black"),
        cast=["ogilvy", "henderson"], landmark="the white palings and the wicket gate",
        landmark_at="start", landmark_size="is a third of the height of the frame",
        route="from the pavement over the white palings into the rows of peas",
        geometry=("The white pointed palings cross the BOTTOM third of the frame from the LEFT edge to "
                  "the wicket gate at the CENTRE. The rows of peas and runner beans on canes fill the "
                  "CENTRE behind them. The yellow-brick villa with its gabled porch and green door stands "
                  "at the LEFT half across the TOP, and the cast-iron gas lamp rises at the RIGHT edge."),
        crowd="", outdoors=True, props=[], location="hendersons_garden_woking"),
    "home": dict(
        described=("The front of the narrator's red-brick villa at Maybury at a quarter to nine on a clear "
                   "summer morning in 1894: a black front door under a small red-tiled porch, a canted bay "
                   "window with white sashes, a knee-high red-brick wall with a black wrought-iron gate, "
                   "clipped laurels and a privet hedge, a gravel road climbing to the right, tall beech "
                   "trees downhill at the left and a green boarded side gate; the morning sun comes from "
                   "the LEFT, warm on the brick, and leaves the porch, the laurels and the shade under the "
                   "beeches black"),
        cast=["unnamed_first_person_narrator", "unnamed_newspaper_boy"],
        landmark="the black wrought-iron gate in the brick wall", landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the gravel road to the iron gate and the black front door",
        geometry=("The red-brick villa fills the CENTRE of the frame with the black front door under its "
                  "red-tiled porch at the CENTRE. The black wrought-iron gate stands in the brick wall at "
                  "the LEFT third, the gravel road crosses the BOTTOM edge climbing to the RIGHT, the tall "
                  "beeches are dark at the LEFT edge and the blue sky runs across the TOP."),
        crowd="", outdoors=True, props=[], location="narrators_home"),
}

# (setup, size, faces, path, move_id, frame, motion, camera, at_rest, section, why)
S = [
    ("study", "wide", [], 0.2, "pan_to",
     f"Wide of the dark study at night: {NARR} bent over the writing-table in the green lamplight with his "
     "back to the tall French windows, his pen already moving across the page, and through the glass behind "
     "him a green-white streak of flame crossing the starry sky from the right toward the left.",
     "The camera pans from the green lamp across to the French windows; the green-white streak of flame "
     "races across the starry sky beyond the glass and leaves a glowing green trail; the Narrator's hand "
     "drives the pen along the line of writing.",
     "inside the study by the bookcase at a standing man's eye, four long strides from the table, a 35mm "
     "lens. The lamp comes from LOW at the RIGHT onto his page and leaves the corners black",
     f"The tall French windows fill the LEFT half of the frame, the starry sky and the dark beech tops in "
     "the glass and the green-white streak crossing it at the TOP. The Narrator sits bent at the "
     "writing-table at the CENTRE, his back three-quarters to the windows, his head a fifth of the frame's "
     "height. The green lamp glows at the RIGHT third and the bookcase is black at the RIGHT edge.",
     "hook", "The strangest thing ever to reach the earth falls past the one man telling us about it."),
    ("study", "medium_close", ["unnamed_first_person_narrator"], 0.5, "locked",
     f"Medium close of {NARR} at the writing-table under the green-shaded lamp, the long oval face bent to "
     "the manuscript, the steel pen already moving along a line, a green flicker of light on the window "
     "glass behind his shoulder.",
     "The camera holds a locked-off frame; he dips the pen in the brass inkstand and writes on along the "
     "line; a green glow washes across the window glass behind him and fades.",
     "across the writing-table level with his eyes, an arm's length from him, a 50mm lens. The lamp comes "
     "from LOW at the RIGHT onto his face and leaves the window behind him dark",
     "The Narrator's head and shoulders fill the CENTRE of the frame from his dark parted hair at the TOP "
     "third to the grey tweed at the BOTTOM edge, his head a third of the frame's height, bent to the page. "
     "The dark window glass stands behind his LEFT shoulder and the green lamp glows at the RIGHT edge.",
     "setup", "The lead is the man who did not look up: the chapter's irony is his own."),
    ("heath", "wide", [], 0.2, "crane_down",
     f"Wide of Horsell Common at sunrise: {OGIL} small among the knee-deep heather, already wading toward "
     "the raw mound of flung yellow sand a hundred yards off, a thin blue smoke rising from burning heather "
     "beyond it and the church tower of Woking on the horizon under the lemon sky.",
     "The camera descends from the lemon sky over the far pines to the heather; Ogilvy wades on through "
     "the heather toward the sand mound; the thin blue smoke rises and drifts to the right.",
     "on the heath at a standing man's eye, far behind him, a 35mm lens. The low sun comes from BEHIND "
     "the far pines onto the sand heaps and leaves the near heather black",
     "The raw mound of flung yellow sand lies across the CENTRE of the frame, the height of a fingernail, "
     "the blue smoke rising behind it. Ogilvy wades in the heather at the LEFT third, the height of a "
     "finger, his back to the camera. The two young pines stand at the LEFT edge and the RIGHT third, and "
     "the lemon sky fills the TOP half.",
     "setup", "Ogilvy saw it fall and went to look: the one man who acts on what he saw."),
    ("heath", "medium", ["ogilvy"], 0.5, "follow",
     f"Medium of {OGIL} striding through the knee-deep heather at dawn, turned three-quarters toward the "
     "camera, one hand pushing a furze bush aside, his eyes on the heaps of flung sand ahead.",
     "The camera tracks beside Ogilvy as he strides at a normal walking pace through the heather toward the flung sand; the "
     "furze springs back behind his hand; his head lifts toward the smoke.",
     "beside him in the heather at his shoulder height, three long strides from him, a 35mm lens. The "
     "low sun comes from BEHIND him onto his hair and shoulders and leaves the heather at his knees black",
     "Ogilvy strides at the CENTRE of the frame from the heather at the BOTTOM edge to his wild auburn "
     "hair at the TOP third, his head a quarter of the frame's height, turned three-quarters toward the "
     "camera. The flung yellow sand heaps rise at the RIGHT third and the lemon sky fills the TOP edge.",
     "setup", "What he finds: the ground itself thrown about, the heather burning."),
    ("pit", "wide", [], 0.2, "high_angle",
     f"High wide looking down into the raw pit at sunrise: {CYL} lying half-buried across it, its huge "
     "circular end tilted up out of the sand, splintered fir wood on the gravel, and at the charred rim "
     f"at the bottom left the small figure of {OGIL} standing and staring, the curved crusted hull towering "
     "many times his height and running out of the frame at both sides.",
     "The camera tilts down from the pines on the far rim to the crusted circular end of the cylinder; "
     "a thin haze of heat shimmers off the crust; Ogilvy leans forward over the rim.",
     "high on the rim of the pit looking down into it, a 35mm lens, a high angle. The low sun comes from "
     "the LEFT over the far rim onto the crust and leaves the near sand wall black",
     "The crusted circular end of the cylinder fills the CENTRE of the frame, half the frame's height, "
     "tilted up out of the sand. The yellow sand walls slope in from the LEFT edge and the RIGHT edge, "
     "splintered fir lies on the gravel at the BOTTOM, and Ogilvy stands small on the rim at the BOTTOM "
     "LEFT, the height of a finger, the crusted hull many times his height. The heather and pines line the "
     "TOP edge.",
     "setup", "The size of it: a man is a finger beside a thing thirty yards across."),
    ("pit", "medium_close", ["ogilvy"], 0.4, "locked",
     f"Medium close of {OGIL} at the edge of the pit, sweat on his broad ruddy face, the full auburn beard, "
     "his spectacles pushed up on his forehead, the crusted curve of the cylinder filling the pit behind him.",
     "The camera holds a locked-off frame; he draws his spectacles down onto his nose and stares at the "
     "cylinder; he shakes his head and drags the back of his hand across his forehead.",
     "on the rim of the pit level with his eyes, an arm's length from him, a 50mm lens. The low sun comes "
     "from the LEFT onto his face and leaves the pit behind him in shadow",
     "Ogilvy's head and shoulders fill the CENTRE of the frame from his wild auburn hair at the TOP third "
     "to the mustard-ochre tweed at the BOTTOM edge, his head a third of the frame's height, lit from the "
     "LEFT. The crusted grey curve of the cylinder fills the frame behind him to the RIGHT edge.",
     "setup", "He sees design before he can name it: the shape, not the size, is what troubles him."),
    ("pit", "insert", [], 0.7, "tilt_down",
     "Insert on the crusted rim of the cylinder's circular end in the low sun: the thick dun-grey clinker "
     "already cracking and flaking off the curved edge, grey flakes dropping onto the yellow sand below.",
     "The camera tilts down from the crusted rim of the circular end to the yellow sand below; grey "
     "clinker flakes rain off the rim in a steady shower; the flakes pile into a grey drift on the sand.",
     "at the foot of the circular end looking up at its rim, an arm's length from the crust, a 90mm lens. "
     "The low sun comes from the LEFT along the rim and leaves the crust's underside black",
     "The curved crusted rim of the circular end crosses the frame from the LEFT edge to the RIGHT edge "
     "across the TOP half, thick dun-grey clinker cracked along it. Grey flakes hang in the air at the "
     "CENTRE and the yellow sand lies across the BOTTOM third with fallen flakes on it.",
     "setup", "The picture speaks: the Thing is shedding its skin, and he is alone with it."),
    ("pit", "medium", ["ogilvy"], 0.9, "low_angle",
     f"Low medium from the pit floor of {OGIL} already half-way down the sand wall, upright on his feet "
     "and stepping down it sideways, one arm out for balance, the crusted curve of the cylinder rising at "
     "the right.",
     "The camera tilts up from the grey gravel of the pit floor to Ogilvy on the sand wall; he steps down "
     "the sand sideways at a normal walking pace; a shower of sand runs down beside his boots.",
     "on the gravel floor of the pit at knee height looking up the sand wall, three long strides from him, "
     "a 35mm lens, a low angle. The low sun comes from the LEFT onto his back and the sand and leaves the "
     "cylinder's flank black",
     "Ogilvy stands upright on the yellow sand wall at the LEFT third of the frame, his head a quarter of the "
     "frame's height, the pale sky above the rim at the TOP. The crusted curve of the cylinder rises at the "
     "RIGHT half and the grey gravel lies across the BOTTOM edge.",
     "setup", "He goes toward it: curiosity is still bigger than fear."),
    ("floor", "insert", [], 0.1, "locked",
     "Insert on the edge of the cylinder's crusted circular lid with a black scorch mark the size of a hand "
     "on its rim, the thin seam between the lid and the body cutting across the crust.",
     "The camera holds a locked-off frame; dust trickles off the rim as the whole crusted lid turns on its "
     "body, carrying the black mark along the rim from the right toward the left; dust spurts from the seam "
     "as the lid jerks and the black mark jumps forward.",
     "at the foot of the cylinder, an arm's length from the rim, a 90mm lens. The low sun comes from the "
     "LEFT along the seam and leaves the crust below it black",
     "The crusted rim of the lid crosses the frame from the LEFT edge to the RIGHT edge through the CENTRE, "
     "the thin dark seam running under it. The black scorch mark sits at the RIGHT third of the rim, the "
     "size of a hand, and grey clinker lies on the sand at the BOTTOM edge.",
     "setup", "The shape becomes a mechanism: the lid is turning, so something turns it."),
    ("floor", "medium_close", ["ogilvy"], 0.3, "push_slow",
     f"Medium close of {OGIL} at the foot of the cylinder, the broad ruddy face streaming with sweat and the small "
     "hazel eyes wide behind the steel spectacles, the crusted metal filling the frame behind him.",
     "The camera pushes in toward Ogilvy's face; his eyes go wide; his mouth opens on the words and "
     "his hand rises to his spectacles.",
     "at the foot of the cylinder level with his eyes, an arm's length from him, a 50mm lens. The low sun "
     "comes from the LEFT onto his face and leaves the metal behind him in shadow",
     "Ogilvy's head and shoulders fill the CENTRE of the frame from his wild auburn hair at the TOP third to "
     "the mustard-ochre tweed at the BOTTOM edge, his head a third of the frame's height, lit from the LEFT. "
     "The grey crust of the cylinder fills the frame behind him from the LEFT edge to the RIGHT edge.",
     "reaction", "The thought arrives whole and wrong: men, trapped, dying."),
    ("floor", "medium", ["ogilvy"], 0.5, "pull_reveal",
     f"Medium of {OGIL} at the foot of the huge crusted lid, both hands already reaching out toward the "
     "glowing metal, heat haze rising off it around his fingers, the curved crusted hull towering many "
     "times his height and running out of the frame at both sides.",
     "The camera pulls back from Ogilvy's outstretched hands, widening to show the whole crusted end of "
     "the cylinder above him; he snatches his hands back from the heat and shakes them; he turns and "
     "scrambles up the sand wall.",
     "on the pit floor at a standing man's eye, three long strides from him, a 35mm lens. The low sun "
     "comes from the LEFT onto the crust and leaves the sand wall behind him black",
     "Ogilvy stands at the CENTRE of the frame from the gravel at the BOTTOM edge to the TOP third, his head "
     "a quarter of the frame's height, his hands reaching toward the crust. The crusted circular end rises "
     "behind him across the frame from the LEFT edge to the RIGHT edge, heat haze over it.",
     "reaction", "His goodness nearly burns him: he would help the thing that has come to kill him."),
    ("heath", "medium", ["ogilvy"], 0.8, "pan_to",
     f"Medium of {OGIL} already running hatless through the knee-deep heather toward the pale sandy road, "
     f"both arms flung up, and behind him on the road {WAGG} on the seat of a horse-drawn cart, the church "
     "tower of Woking on the horizon.",
     "The camera pans from the smoking sand heaps across to Ogilvy running onto the pale sandy road; he "
     "waves both arms at the cart; the horse pulls the cart on along the road.",
     "on the heath at his shoulder height, three long strides from him, a 35mm lens. The low sun comes "
     "from BEHIND the far pines onto his hair and shoulders and leaves the near heather black",
     "Ogilvy runs through the heather at the CENTRE of the frame from the BOTTOM edge to the TOP third, his "
     "head a quarter of the frame's height, both arms up. The pale sandy road crosses behind him from the "
     "LEFT edge to the RIGHT third with the horse-drawn cart on it at the LEFT third, and the lemon sky "
     "fills the TOP edge.",
     "friction", "The first person he meets does not stop: the news is too wild to be heard."),
    ("heath", "medium_close", ["unnamed_waggoner"], 0.9, "over_shoulder",
     f"Medium close over Ogilvy's shoulder toward {WAGG} on the seat of his cart, the weathered brick-red "
     "face and squinting pale blue eyes turned down at Ogilvy, the reins already in his fist.",
     "The camera holds a locked-off frame over Ogilvy's shoulder toward the waggoner; the waggoner looks "
     "him up and down and shakes his head; he flicks the reins and the horse pulls the cart on along the road.",
     "behind Ogilvy's shoulder on the road, looking up at the cart seat, two long strides from the "
     "waggoner, a 50mm lens. The low sun comes from BEHIND the waggoner onto his hat brim and leaves his "
     "face in soft shadow",
     "The waggoner's head and shoulders fill the RIGHT half of the frame from his black hat at the TOP "
     "edge to the smock frock at the BOTTOM edge, his head a third of the frame's height. Ogilvy's shoulder "
     "and wild auburn hair fill the LEFT edge, dark against the lemon sky at the TOP LEFT.",
     "friction", "Ordinary England answers the end of the world with a flick of the reins."),
    ("garden", "medium", ["henderson"], 0.2, "track_lateral",
     f"Medium of {HEND} bent over his spade among the rows of peas behind the white palings, already "
     "turning the dark soil, the gabled porch of the yellow-brick villa behind him.",
     "The camera tracks sideways to the right along the white palings, past the wicket gate, with "
     "Henderson digging behind it; he drives the spade into the soil and turns it over; a clod of dark "
     "soil tumbles off the blade of his spade.",
     "on the pavement at a standing man's eye, three long strides from the palings, a 35mm lens. The low "
     "sun comes from the RIGHT across the palings and leaves the porch behind him black",
     "The white pointed palings cross the BOTTOM third of the frame from the LEFT edge to the RIGHT edge. "
     "Henderson digs behind them at the CENTRE among the peas on sticks, his head a quarter of the frame's "
     "height. The gabled porch and green door stand at the LEFT third and the villa's brick fills the TOP.",
     "friction", "The one listener, and he is deaf in one ear and busy with his peas."),
    ("garden", "medium_close", ["ogilvy"], 0.3, "locked",
     f"Medium close of {OGIL} on the pavement outside the white palings, turned three-quarters toward the "
     "camera, both hands gripping the pointed tops, leaning over them into the garden, breathless, sand on "
     "his tweed and in his beard.",
     "The camera holds a locked-off frame; he leans over the palings and calls out; his hand shakes the "
     "pointed tops.",
     "on the pavement beside him level with his eyes, an arm's length from him, looking along the palings, "
     "a 50mm lens. The low sun comes from the RIGHT onto his face and leaves the porch across the garden black",
     "Ogilvy's head and shoulders fill the LEFT half of the frame from his wild auburn hair at the TOP third "
     "to his gripping hands on the palings at the BOTTOM edge, his head a third of the frame's height, lit "
     "from the RIGHT. The white palings run away from him along the BOTTOM edge, and the rows of peas and "
     "the gabled porch of the villa stand across the garden at the RIGHT half.",
     "friction", "He has learned: this time he starts with what the other man saw."),
    ("garden", "medium_close", ["henderson"], 0.5, "tilt_up",
     f"Medium close of {HEND} straightening up among the peas, the narrow sharp face with its pointed nose "
     "turning toward the palings, the spade still upright in his hand.",
     "The camera tilts up from the spade blade in the dark soil to Henderson's face; he straightens with a "
     "quick grin; he plants the spade in the soil.",
     "among the peas at the height of his chest, an arm's length from him, a 50mm lens. The low sun comes "
     "from the RIGHT onto his face and leaves the villa behind him in shade",
     "Henderson's head and shoulders fill the CENTRE of the frame from his oiled brown hair at the TOP "
     "third to the striped waistcoat at the BOTTOM edge, his head a third of the frame's height, lit from "
     "the RIGHT. The spade handle rises at the LEFT third and the green porch door is dark at the TOP LEFT.",
     "friction", "He hears the word he wanted: a story. He has not heard the rest."),
    ("garden", "medium_close", ["ogilvy"], 0.7, "push_slow",
     f"Medium close of {OGIL} on the pavement leaning hard over the white palings into the garden, turned "
     "three-quarters toward the camera, one hand chopping the air, the low sun full on his broad ruddy face.",
     "The camera pushes in toward Ogilvy's face; he slaps the palings with his open hand; he leans "
     "in over the palings and jabs his arm back toward the common.",
     "on the pavement beside him level with his eyes, an arm's length from him, looking along the palings, "
     "a 50mm lens. The low sun comes from the RIGHT onto his face and leaves the porch across the garden black",
     "Ogilvy's head and shoulders fill the LEFT half of the frame from his wild auburn hair at the TOP third "
     "to his hand on the palings at the BOTTOM edge, his head a third of the frame's height, lit from the "
     "RIGHT. The white palings run away from him along the BOTTOM edge, and the peas and the gabled porch "
     "stand across the garden at the RIGHT half.",
     "turn", "The turn is his own act: he says the true word, artificial, and makes it land."),
    ("garden", "medium_close", ["henderson"], 0.9, "low_angle",
     f"Low medium close of {HEND} among the peas, one hand already cupped behind his ear, his narrow face "
     "turned toward the palings, the spade loose in his other hand.",
     "The camera holds a locked-off frame; he cups his hand to his ear and leans in over the peas; he lets "
     "the spade fall into the peas.",
     "among the peas at knee height looking up at him, an arm's length from him, a 50mm lens, a low angle. "
     "The low sun comes from the RIGHT onto his face and leaves the porch behind him black",
     "Henderson's head and shoulders fill the CENTRE of the frame from his oiled brown hair at the TOP "
     "third to the striped waistcoat at the BOTTOM edge, his head a third of the frame's height, his hand "
     "cupped at his ear. The gabled porch is dark at the TOP LEFT and the blue sky fills the TOP RIGHT.",
     "reaction", "The deaf ear: one more obstacle, comic, before belief."),
    ("floor", "medium", [], 0.8, "follow",
     f"Medium of {OGIL} and Henderson, now in his black-and-white shepherd's-check jacket, hurrying down "
     "the sand wall side by side toward the crusted cylinder, Henderson with a walking stick in his hand, "
     "the curved crusted hull towering many times their height and running out of the frame at both sides.",
     "The camera tracks behind Ogilvy and Henderson as they walk down the sand at a normal walking pace toward the cylinder; "
     "Henderson raps the crust with his stick; both men lean their heads toward the metal to listen.",
     "behind them on the sand wall at a standing man's eye, three long strides from them, a 35mm lens. "
     "The low sun comes from the LEFT onto their backs and leaves the pit floor in shadow",
     "Ogilvy walks at the LEFT third and Henderson at the RIGHT third of the frame, their backs to the "
     "camera, heads a quarter of the frame's height. The crusted circular end of the cylinder fills the TOP "
     "half ahead of them from the LEFT edge to the RIGHT edge and the yellow sand runs across the BOTTOM.",
     "answer", "Two men now, and the thing is silent: belief arrives just as the sound stops."),
    ("floor", "insert", [], 0.95, "crane_up",
     "Insert on the thin circle of bright yellowish-white metal showing in the seam between the crusted lid "
     "and the body of the cylinder, a faint shimmer of hissing air along it, the tip of a walking stick "
     "resting against the crust.",
     "The camera rises above the bright seam, looking down over the crusted lid and the sand around "
     "it; a thin wisp of air shimmers out of the seam; the stick taps the crust twice.",
     "close over the rim of the lid looking down, an arm's length from the seam, a 90mm lens. The low sun "
     "comes from the LEFT along the bright seam and leaves the crust around it dark",
     "The bright ring of pale metal curves across the CENTRE of the frame from the LEFT edge to the RIGHT "
     "edge, the thickness of a finger. The dun-grey crust fills the TOP half above it and the BOTTOM third "
     "below it, and the stick's tip rests on the crust at the BOTTOM RIGHT.",
     "answer", "The seam is the future: the lid is coming off, and nobody is there to see it."),
    ("home", "wide", ["unnamed_newspaper_boy", "unnamed_first_person_narrator"], 0.3, "pan_to",
     f"Wide of the narrator's red-brick villa at a quarter to nine in bright morning sun: {BOY} already "
     "running up the gravel road toward the iron gate, and at the open gate "
     f"{NARR_OUT} waiting with one hand on the gatepost.",
     "The camera pans from the tall beeches at the left across to the iron gate; the newspaper boy runs up "
     "the gravel to the iron gate; the Narrator at the gate raises his hand to him.",
     "on the gravel road at a standing man's eye, far down the hill, a 35mm lens. The morning sun comes "
     "from the LEFT onto the brick and leaves the laurels and the porch black",
     "The red-brick villa fills the CENTRE of the frame with the black front door under its red-tiled porch. "
     "The newspaper boy runs on the gravel road at the LEFT third toward the iron gate, the height of a "
     "finger. The beeches are dark at the LEFT edge and the blue sky runs across the TOP.",
     "runout", "The news has become a spectacle: the town goes to look before it goes to fear."),
    ("home", "insert", [], 0.6, "track_lateral",
     "Insert across the top of the black wrought-iron gate: the newspaper boy's inky fingers passing a "
     "newspaper folded tight in quarters, its plain grey folded edge toward the camera, over the gate into "
     "the Narrator's hand in its grey tweed cuff.",
     "The camera tracks sideways to the left along the top of the iron gate, past the passing newspaper; "
     "a grey tweed cuff reaches in and takes the folded paper; inky fingers point away down the road.",
     "beside the gate at the height of the gate top, an arm's length from the paper, a 90mm lens. The "
     "morning sun comes from the LEFT onto the paper and leaves the laurels behind black",
     "The black iron gate top crosses the BOTTOM third of the frame from the LEFT edge to the RIGHT edge. "
     "The tight-folded newspaper passes over it edge-on at the CENTRE, the boy's hand at the LEFT third and the Narrator's "
     "grey tweed cuff at the RIGHT third. The dark laurels fill the TOP half behind.",
     "runout", "The lead's own entrance into the story: the news is handed to him over his own gate."),
    ("home", "medium_close", ["unnamed_newspaper_boy"], 0.8, "locked",
     f"Medium close of {BOY} at the black iron gate in the morning sun, the narrow freckled face flushed "
     "from running, gap-toothed and grinning, one hand pointing away down the road toward the common.",
     "The camera holds a locked-off frame; he points down the road toward the common; he bounces on his "
     "toes as he tells it.",
     "on the garden path level with his eyes, an arm's length from him, a 50mm lens. The morning sun comes "
     "from the LEFT onto his face and leaves the laurels behind him black",
     "The newspaper boy's head and shoulders fill the CENTRE of the frame from his grey flat cap at the TOP "
     "third to the canvas bag strap at the BOTTOM edge, his head a third of the frame's height, lit from "
     "the LEFT. The black iron gate crosses the BOTTOM edge and the dark laurels fill the RIGHT edge.",
     "button", "The world's answer: not believed as a cylinder, but believed -- as dead men from Mars."),
]

BEATS = {0: (0.8, 0.0), 6: (1.5, 2.5), 8: (0.8, 0.0), 9: (0.8, 0.0), 16: (1.0, 0.0),
         17: (0.6, 0.3), 19: (0.8, 0.0), 21: (1.0, 0.0), 22: (0.6, 1.5)}
TURNS = {16: "a madman nobody hears -> believed", 9: "a fallen stone -> a made thing with men in it",
         22: "one man's secret -> the whole town's spectacle"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "Then came the first falling star, a line of flame rushing east over Winchester.", 0),
    ("narration", "unnamed_first_person_narrator",
     "I was writing in my study, the blind up, and I never once looked up.", 1),
    ("narration", "unnamed_first_person_narrator",
     "Ogilvy had seen it fall. At dawn he went hunting it on Horsell Common.", 2),
    ("narration", "unnamed_first_person_narrator",
     "Sand was flung over the heath in heaps, and eastward the heather burned.", 3),
    ("narration", "unnamed_first_person_narrator",
     "The Thing lay half-buried in a great pit: a cylinder thirty yards across.", 4),
    ("dialogue", "ogilvy", "Good Lord. No meteorite was ever that shape.", 5),
    ("narration", "unnamed_first_person_narrator",
     "He clambered down into the heat. The ash was falling from the end alone.", 7),
    ("narration", "unnamed_first_person_narrator",
     "Very slowly, the circular top was turning. Something inside was unscrewing it.", 8),
    ("dialogue", "ogilvy", "Good heavens! A man in it, half roasted!", 9),
    ("narration", "unnamed_first_person_narrator",
     "He forgot the heat and went to help turn it. The glowing metal drove him back.", 10),
    ("narration", "unnamed_first_person_narrator",
     "He ran for Woking, hatless and wild. It was six o'clock.", 11),
    ("narration", "unnamed_first_person_narrator",
     "A waggoner simply drove on. At Horsell Bridge, a potman tried to lock him in.", 12),
    ("narration", "unnamed_first_person_narrator",
     "Then he saw Henderson, the London journalist, digging in his garden.", 13),
    ("dialogue", "ogilvy", "Henderson! That shooting star: it is out on Horsell Common!", 14),
    ("dialogue", "henderson", "Good Lord! A fallen meteorite! That is good.", 15),
    ("dialogue", "ogilvy", "It is an artificial cylinder, man!", 16),
    ("dialogue", "henderson", "What is that?", 17),
    ("narration", "unnamed_first_person_narrator", "He was deaf in one ear.", 17),
    ("narration", "unnamed_first_person_narrator",
     "The two hurried back. The sounds inside had stopped. They rapped the crust with a stick.", 18),
    ("narration", "unnamed_first_person_narrator",
     "A thin ring of bright metal showed at the rim, and air hissed through it.", 19),
    ("narration", "unnamed_first_person_narrator",
     "By eight, boys and idle men were off to see the dead men from Mars.", 20),
    ("narration", "unnamed_first_person_narrator",
     "My newspaper boy told me at a quarter to nine. I lost no time.", 21),
    ("dialogue", "unnamed_newspaper_boy", "Dead men from Mars, sir! Out at the sand-pits!", 22),
]

BEDS = [{"from_shot": 0, "tone": "uneasy"}, {"from_shot": 2, "tone": "plain"},
        {"from_shot": 6, "tone": "grave"}, {"from_shot": 13, "tone": "light"},
        {"from_shot": 18, "tone": "grave"}, {"from_shot": 20, "tone": "plain"}]

MOVES = {i: s[4] for i, s in enumerate(S)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.5, 0.0))
        shots.append(dict(index=i, section=section, setup=setup, size=size, faces=list(faces), view="",
                          path=path, frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), why=why,
                          cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=2, title="The Falling Star",
                question="Today, can Ogilvy make anyone believe what lies in the pit?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="ogilvy", answer="line 22",
                beds=BEDS, setups=SETUPS, shots=shots, lines=lines)


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT.parent / "moves.json").write_text(json.dumps(MOVES, indent=1), encoding="utf-8")
    words = sum(len(l["text"].split()) for l in doc["lines"])
    said = sum(len(l["text"].split()) for l in doc["lines"] if l["kind"] == "dialogue")
    counts = {m: list(MOVES.values()).count(m) for m in set(MOVES.values())}
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words "
          f"-> {words / 2.3:.0f}s at 2.3 w/s; dialogue {said / words:.1%}; moves {counts}")
    print(OUT)
