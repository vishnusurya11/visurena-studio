r"""The War of the Worlds, episode 6 -- "The Heat-Ray in the Chobham Road", chapter 6.

THE BRICK.  One event: a crowd walks out after work to look at a novelty, a
hummock of sand saves every one of them from the ray, and then they kill three
of their own getting away.

  QUESTION  Tonight, does the crowd that came to watch get home?
  TURN      shot 21, and it is a piece of ground and not a person: the beam
            passes OVER them because the mirror sat a few yards too low, so
            nothing they did saved them and nothing they did killed them --
            "a crowd that is being spared" -> "a crowd that does not know it".
  ANSWER    shot 26: the road narrows between high banks and the crowd jams in
            it.  The ray took nobody on this road; the road took three.
  BUTTON    line 23, the count, flat: two women and a little boy.  Wells gives
            them no names and no last words, and inventing either would be the
            episode telling a lie about what it is.

THE NARRATOR IS NOT HERE, and that is the whole shape of the chapter.  He says
so himself -- "The description of their death, as it was seen by the crowd,
tallies very closely with my own impressions" -- so episode 6 keeps HIS VOICE
over OTHER PEOPLE'S PICTURES.  Episodes 1-5 were his eyes; this one is his
account of a thing he did not see, which is what the prose is.  Every line is
narration except the one shriek Wells actually quotes.

NO NEW LOCATION PACK.  The chapter's road is already drawn inside
`horsell_common`: `wide_horsell_bridge.png` is the bridge they walk out over
and `wide_road_high_banks.png` is the narrow black stretch where the crush
happens.  Only the HOUR is new, and the hour comes from the reference, never
from the words (measured 2026-09-20, ep05 shots 25-27 came back in evening
light twice while the prompt said full dark), so the after-dark setups take
`wide_night.png`.

COMPOSITION, everything episode 5 measured:
- FRAMING IS A CUT, NEVER A FRACTION.  "his head a quarter of the frame" bought
  nothing across four renders; "the panel cuts him at mid-thigh" is obeyed.
- THE OPENING CLAUSE LEADS.  A correction appended after the plan's own first
  sentence loses to it -- ep05 shot 14 drew a horse's head three times while a
  whole-horse clause sat further down the prompt.
- A CREATURE IS NEVER CROPPED TO A PART: the frame CONTAINS the body, the
  light and the lens ATTEND to the detail.
- WARDROBE BY SHAPE AND AGAINST THE OTHER MAN'S.  A named hat is replaced by
  the commonest hat in the scene; a hat given a shape and a contrast holds.
- A CROWD SHOT STAGES NO CAST SHEET.  Measured on ep05 `dusk`: a staged person
  is drawn into any panel whose prose calls for unnamed people, however plainly
  that panel forbids him -- and with no sheet staged the crowd came back
  individuated, which is the clone fault that has dogged every crowd since
  Scarlet.  Six of this episode's seven crowd setups name nobody on purpose.

CAMERA (docs/calibration/camera_catalog.md): eight catalog moves over 28 shots,
none on more than a quarter, never the same move twice running, no orbit, no
push-in, no pull-back off a wide, no crane-down, tilt-down or rack.  A MOVING
camera is never told to keep a subject in frame; a static head names what it
frames, a travelling head names where it ARRIVES and how far it goes.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep06" / "plan.json"

WHERE = "The Chobham road, Surrey, 1894"
LIGHT = "firelight and black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

MOUNTED = ("the mounted policeman, a thick-set man of thirty in a dark blue tunic buttoned to the "
           "throat and a black custodian helmet with a chin strap, his side-whiskers dark against "
           "a red face")
STENT = ("Stent, the Astronomer Royal, a heavy upright man of sixty in a black frock coat and a "
         "black silk top hat, clean-shaven with a long jaw")
OGILVY = ("Ogilvy the astronomer, a spare quick man of forty-five in a brown Norfolk jacket and a "
          "soft brown felt hat, a short sandy beard")

PIT_NIGHT = (
    "the sand-pits on Horsell Common at night in 1894: the raw ring of flung yellow sand round the "
    "crater lit red from inside by burning furze, the thin jointed mast standing above it with its "
    "polished mirror turning at the top, knee-deep heather and dark furze standing black to the "
    "horizon, young Scots pines black against a deep blue-black sky, and the roofs of Woking small "
    "and dark beyond; the only light is the low red glow out of the pit and the furze burning in "
    "patches across the heather")
ROAD_GLOAMING = (
    "the road out of Woking onto Horsell Common at dusk in 1894: a pale dry road running away "
    "between cut hedges, tall beech trees standing along its left side, brick cottages with lit "
    "windows at the near end and the open common beyond the far end, the sky deep green-blue and "
    "the ground already under its own shadow; the road reads pale, the hedges and the beeches read "
    "black, and the lit windows are the only warm light")
ROAD_FIRE = (
    "the road out of Woking onto Horsell Common at night in 1894: a pale dry road between cut "
    "hedges with tall beech trees along its left side, the tops of the beeches alight and burning "
    "orange, sparks going up, a brick house at the corner with its window frames on fire and one "
    "gable fallen into the road, and the common black beyond; the light is firelight from the LEFT, "
    "the road reads orange-pale and everything away from the fire is black")
BANKS = (
    "the narrow stretch of the Chobham road at night in 1894, where it runs down between high "
    "sandy banks: the road pinched to a cart's width, raw sandy banks rising steeply on both sides "
    "above head height with heather and gorse roots along their tops, the way ahead black, and a "
    "red glow in the sky behind; the only light is that glow, the banks read dull red at their "
    "tops and the road between them is nearly black")

GEO_PIT = (
    "Black heather fills the BOTTOM third of the frame from the LEFT edge to the RIGHT edge. The "
    "raw ring of flung yellow sand runs across the CENTRE, lit red from within, a tenth of the "
    "height of the frame, with the thin jointed mast standing above it at the CENTRE RIGHT and its "
    "mirror at the TOP third. Furze burns in low red patches at the LEFT third and the RIGHT "
    "third, and a deep blue-black sky fills the TOP.")
GEO_ROAD = (
    "The pale road runs from the BOTTOM edge away into the CENTRE, narrowing as it goes. Cut "
    "hedges run along both sides, black, and tall beech trees stand along the LEFT from the BOTTOM "
    "LEFT to the CENTRE. Brick cottages with lit windows stand at the RIGHT edge at the near end, "
    "the open common lies dark beyond the CENTRE, and a deep green-blue sky fills the TOP third.")
GEO_FIRE = (
    "The pale road runs from the BOTTOM edge away into the CENTRE. The beech tops burn orange "
    "across the TOP LEFT and the CENTRE, sparks going up into a black sky at the TOP. The brick "
    "house stands at the RIGHT third with its window frames alight and a fallen gable heaped in "
    "the road below it, and the common lies black beyond the CENTRE.")
GEO_BANKS = (
    "The high sandy banks rise from the BOTTOM LEFT and the BOTTOM RIGHT to above the TOP third on "
    "both sides, leaving a black gap of road running away up the CENTRE. The tops of both banks "
    "read dull red against a red glow that fills the TOP CENTRE, and the road between them is "
    "nearly black from the BOTTOM edge to the CENTRE.")

SETUPS = {
    "ray": dict(
        described=PIT_NIGHT, cast=[],
        landmark="the polished mirror turning at the top of its mast", landmark_at="far_end",
        landmark_size="is a twelfth of the height of the frame",
        route="from the black heather across to the red ring of sand round the pit",
        geometry=GEO_PIT, crowd="", outdoors=True, props=["pit_mast_mirror"],
        location="horsell_common"),
    "road": dict(
        described=ROAD_GLOAMING, cast=[],
        landmark="the lit windows of the brick cottages at the near end of the road",
        landmark_at="start", landmark_size="is a sixth of the height of the frame",
        route="from the lit cottages at the Woking end along the road toward the open common",
        geometry=GEO_ROAD, crowd="young shop people walking out in twos and threes after the "
                                 "shops have shut, talking and laughing",
        outdoors=True, props=[], location="horsell_common"),
    "knots": dict(
        described=PIT_NIGHT, cast=["stent", "ogilvy"],
        landmark="the polished mirror turning at the top of its mast", landmark_at="far_end",
        landmark_size="is a twelfth of the height of the frame",
        route="from the end of the road out across the open toward the ring of sand",
        geometry=GEO_PIT, crowd="three hundred people in loose knots across the open, all of them "
                                "facing the pit, with three policemen keeping them back",
        outdoors=True, props=["pit_mast_mirror"], location="horsell_common"),
    "beam": dict(
        described=ROAD_FIRE, cast=[],
        landmark="the burning tops of the beech trees along the road",
        landmark_at="far_end", landmark_size="fills the top third of the frame",
        route="from the open common back along the road to the brick house at the corner",
        geometry=GEO_FIRE, crowd="", outdoors=True, props=[], location="horsell_common"),
    "panic": dict(
        described=ROAD_FIRE, cast=["unnamed_mounted_policeman"],
        landmark="the brick house at the corner with its window frames alight",
        landmark_at="far_end", landmark_size="is a third of the height of the frame",
        route="from under the burning beeches back down the road toward Woking",
        geometry=GEO_FIRE, crowd="a crowd of three hundred turning all at once and pushing back "
                                 "the way they came",
        outdoors=True, props=[], location="horsell_common"),
    "banks": dict(
        described=BANKS, cast=[],
        landmark="the black gap of road running away between the banks", landmark_at="far_end",
        landmark_size="is a quarter of the width of the frame",
        route="down the road to where it pinches between the high sandy banks",
        geometry=GEO_BANKS, crowd="a crowd jammed shoulder to shoulder in a road too narrow to "
                                  "hold it, every one of them pushing the same way",
        outdoors=True, props=[], location="horsell_common"),
}

#  setup      size            faces   path  move            frame / motion / camera / at_rest
S = [
    # ---- ray: what the thing does, and what it did tonight ----------------------
    ("ray", "wide", [], 0.2, "crane_up",
     "Wide of the sand-pits at night from out on the black heather: the raw ring of flung sand lit "
     "red from inside, the thin jointed mast standing above it with its polished mirror turning at "
     "the top, low red patches of burning furze scattered across the heather between, and the "
     "roofs of Woking small and dark on the horizon.",
     "The camera rises above the heather with small amplitude until the whole red ring and the "
     "mast above it stand inside the picture, travelling one short stride; the mirror turns a "
     "quarter turn on its mast; one low patch of furze at the left flares and settles.",
     "out on the heather a hundred yards from the pit, low, a 35mm lens. The only light is the red "
     "glow out of the pit and the burning furze; the sand ring reads dull red and the heather, the "
     "pines and the mast are black",
     GEO_PIT, "setup", "The instrument, and the ground it has already cleared."),

    ("ray", "insert", [], 0.6, "locked",
     "Insert on the polished mirror at the top of the mast: a shallow parabolic dish of unknown "
     "metal, its face bright and smooth as a lighthouse reflector, turning a quarter turn at a time on its joint "
     "against a deep blue-black sky, with the red glow of the pit catching its lower rim.",
     "The camera holds a static shot on the mirror, keeping the dish in the centre of frame; the "
     "dish turns one quarter turn on its joint at a walking pace; the red glow runs along its lower rim and off "
     "again as it comes round.",
     "level with the mirror from a hundred yards off, a 300mm lens. The red glow of the pit comes "
     "from BELOW and catches the lower rim; the dish reads pale against a black sky",
     "The mirror fills the CENTRE of the frame, its bright dish a third of the height of the "
     "frame, its joint and the top of the mast below it at the BOTTOM third. A deep blue-black sky "
     "fills the whole frame behind it and a dull red glow shows at the BOTTOM edge.",
     "setup", "A parabolic mirror, of the kind a lighthouse uses, pointed the other way."),

    ("ray", "medium", [], 0.6, "pan_to",
     "Medium on a stand of dark furze out on the heather at night, dry and black and shoulder "
     "high, with the red glow of the pit behind it and a line of untouched heather running away "
     "to the right.",
     "The camera pans to the right across the black furze until the untouched heather beyond it is "
     "in the picture, travelling a hand's breadth; the near stand of furze takes fire all at once "
     "along its whole height of its own accord; the flame runs up it and the light "
     "jumps onto the heather beyond.",
     "out on the heather, low at the height of the furze, four paces from it, a 50mm lens. Before "
     "the fire the only light is the red glow from the LEFT; after it the furze itself is the "
     "brightest thing in the frame",
     "The stand of dark furze fills the CENTRE and the LEFT of the frame from the TOP third down "
     "to the BOTTOM edge. Untouched black heather runs away at the RIGHT third to a dull red "
     "horizon, and a deep blue-black sky fills the TOP third.",
     "setup", "Whatever is combustible flashes into flame at its touch."),

    ("ray", "wide", [], 0.8, "track_lateral",
     "Wide of the common at night from high on the heather: the open ground running from Horsell "
     "away to Maybury with fires burning in patches all across it, a dozen low red glows in the "
     "black, the red ring of the pit at the centre with its mast above it, and smoke lying flat "
     "and lit along the ground between them.",
     "The camera tracks sideways to the right, a truck with large amplitude across the heather "
     "until the furthest fires toward Maybury are inside the picture, travelling two long strides; "
     "the flat smoke drifts left to right across the fires; two of the far glows brighten and "
     "steady.",
     "high on the heather looking out across the common, a 35mm lens. Every light in the frame is "
     "a fire on the ground; the sky is black and the smoke is lit from below",
     "Burning patches run across the CENTRE of the frame from the LEFT edge to the RIGHT edge, a "
     "dozen low red glows in black ground. The red ring of the pit sits at the CENTRE with its "
     "mast above it, flat lit smoke lies along the CENTRE between the fires, black heather fills "
     "the BOTTOM third and a black sky fills the TOP third.",
     "setup", "Forty people under the starlight, and nobody yet who knows it."),

    # ---- road: the town walks out after work ------------------------------------
    ("road", "wide", [], 0.2, "follow",
     "Wide down the pale road out of Woking at dusk, looking away from the town toward the open "
     "common: the road running away between cut black hedges with tall beech trees along its left "
     "side, brick cottages with lit windows at the near right, and young shop people walking out "
     "along it in twos and threes with their backs to the camera.",
     "The camera tracks behind the walkers at a walking pace with large amplitude, coming on down "
     "the road until the open common at the end of it is inside the picture, travelling two long "
     "strides; the nearest pair walk on "
     "with their heads together; a third figure comes out of a cottage gate at the right and falls "
     "in behind them.",
     "in the middle of the road at a standing man's eye, six paces behind the nearest walkers, a "
     "35mm lens. The lit cottage windows at the RIGHT are the only warm light "
     "in the frame; the road reads pale and the hedges and beeches are black",
     GEO_ROAD, "setup", "A novelty, and the excuse it gives for walking together."),

    ("road", "medium", [], 0.6, "track_lateral",
     "Medium alongside two young shop people walking out on the road at dusk: a girl of twenty in "
     "a pale cotton blouse and a dark skirt with her hat pushed back, and a young man beside her "
     "in a cheap dark suit and a bowler, both of them brushed up after the day's work, walking at "
     "an easy pace with the black hedge running past behind them.",
     "The camera tracks sideways to the left alongside them at their own pace until the hedge "
     "behind them gives way to the open common, travelling one long stride; the girl turns her "
     "face to him and laughs; he shifts his hat back off his forehead with one thumb.",
     "at the roadside level with their shoulders, three paces from them, a 50mm lens. The last "
     "green light is behind them; their faces read pale and the hedge behind them is black",
     "The girl and the young man fill the CENTRE of the frame side by side, the panel cutting them "
     "at mid-thigh, their heads at the TOP third. The black hedge runs across the whole frame "
     "behind them at the CENTRE, the pale road shows at the BOTTOM edge, and a deep green-blue sky "
     "fills the TOP third.",
     "setup", "The hum of voices along the road in the gloaming."),

    ("road", "wide", [], 0.4, "crane_up",
     "Wide of the Horsell bridge at dusk from the Woking side: the low brick parapet crossing the "
     "frame, the pale road going over it and away toward the common beyond, a straggling line of "
     "people crossing it in ones and twos, and the black water of the canal below the near side.",
     "The camera rises from the road with small amplitude until the whole span of the bridge and "
     "the common beyond it stand inside the picture, travelling one short stride; the line of "
     "people goes on across the bridge in one unbroken file; two of them stop at the parapet and look "
     "over toward the common.",
     "on the road at the near end of the bridge, low, a 35mm lens. The sky over the common is "
     "still green; the road and the parapet read pale grey and the people crossing are black",
     "The brick parapet runs across the CENTRE of the frame from the LEFT edge to the RIGHT edge. "
     "The pale road crosses it at the CENTRE and runs away to the open common at the CENTRE "
     "beyond, a straggling line of black figures along it. Black canal water shows at the BOTTOM "
     "LEFT and a deep green-blue sky fills the TOP third.",
     "setup", "Nobody on this bridge knows the cylinder has opened."),

    # ---- knots: three hundred people, and three policemen -----------------------
    ("knots", "wide", [], 0.4, "pan_to",
     "Wide of the open common at night from the end of the road: loose knots of people standing "
     "out across the black heather in twos and fives and tens, every one of them turned the same "
     "way toward the red ring of sand a hundred yards off, with the thin mast and its turning "
     "mirror standing above it.",
     "The camera pans to the left across the standing knots until the red ring of sand and the "
     "mast above it are inside the picture, travelling a hand's breadth; the nearest knot shifts "
     "and closes up; arms go up along the near knot and point toward the pit.",
     "at the end of the road looking out over the heather, a 35mm lens. The red glow out of the "
     "pit comes from the CENTRE; the standing people read black against it and the heather is "
     "black",
     "Loose knots of black figures stand across the CENTRE of the frame from the LEFT edge to the "
     "RIGHT edge, the nearest of them cut at the knee by the heather. The red ring of sand lies "
     "beyond them at the CENTRE, a tenth of the height of the frame, with the mast above it. Black "
     "heather fills the BOTTOM third and a blue-black sky fills the TOP third.",
     "setup", "Three hundred people, and a novelty to look at."),

    ("knots", "medium", [], 0.6, "locked",
     "Medium on one knot of people out on the heather at night: five of them standing close in a "
     "ring, a heavy carter in a moleskin waistcoat, a thin clerk in a bowler, a stout woman with a "
     "shawl over her head, an old man with a stick and a boy of sixteen, all of them talking at "
     "once with their faces turned half toward the pit.",
     "The camera holds a static shot on the knot, keeping the five of them in the centre of frame; "
     "arms go out toward the pit across the knot and drop again; heads shake and turn; the five of them close up shoulder to shoulder.",
     "out on the heather at a standing man's eye, four paces from them, a 50mm lens. The red glow "
     "from the pit comes from BEHIND them at the CENTRE; their faces read dull red down one side "
     "and black down the other",
     "The five of them fill the CENTRE of the frame side by side, the panel cutting them at "
     "mid-thigh, their heads across the TOP third. Black heather fills the BOTTOM third from the "
     "LEFT edge to the RIGHT edge, the red glow of the pit shows between their shoulders at the "
     "CENTRE, and a blue-black sky fills the TOP.",
     "setup", "Everyone with a theory, and none of them worth anything."),

    ("knots", "medium", [], 0.4, "low_angle",
     "Low medium from the heather looking up at a mounted policeman on the open common at night: a "
     "thick-set man of thirty on a dark horse, in a dark blue tunic buttoned to the throat and a "
     "black custodian helmet with a chin strap, one arm held straight out sideways to hold the "
     "people back, the horse standing broadside across the frame.",
     "The camera keeps low in the heather, a static shot from the height of the heather with the "
     "horse broadside; the policeman swings his held-out arm across at a walking pace from the left to the "
     "right; the horse shifts its forefeet and swings its head down and away; a figure at the "
     "right edge gives back from the arm.",
     "in the heather below him looking up, five paces from the horse, a 35mm lens, a low angle. "
     "The red glow of the pit comes from BEHIND him; the helmet and the horse read black and their "
     "edges are red",
     "The mounted policeman and his horse fill the CENTRE and the RIGHT of the frame, broadside, "
     "the horse's legs down to the heather at the BOTTOM edge and the helmet at the TOP third. His "
     "held-out arm runs across the CENTRE toward the LEFT third. Black heather fills the BOTTOM "
     "quarter, the red glow of the pit shows at the LEFT third, and a blue-black sky fills the "
     "TOP.",
     "setup", "Three policemen against three hundred people, under Stent's instructions."),

    ("knots", "medium_close", [], 0.4, "pan_to",
     "Medium close on three young men at the back of the crowd at night, shoulder to shoulder and "
     "grinning, hands cupped round their mouths, in cheap dark suits and bowlers with their "
     "collars loose, shouting toward the pit for the pleasure of the noise.",
     "The camera pans to the right across their faces until the third of them is at the centre of "
     "frame, travelling a hand's breadth; the first two shout with their hands cupped and drop "
     "them again; the third puts two fingers in his mouth and whistles.",
     "at the back of the crowd level with their faces, two paces from them, a 50mm lens. The red "
     "glow of the pit comes from the LEFT and lights one side of each face; the other side is "
     "black",
     "The three of them fill the CENTRE of the frame from the LEFT third to the RIGHT third, the "
     "panel cutting them at the middle of the chest, their heads across the TOP third. Black heads "
     "and shoulders of the crowd in front of them cross the BOTTOM edge, the red glow shows at the "
     "LEFT edge, and a blue-black sky fills the TOP third.",
     "friction", "A crowd is always an occasion for noise and horse-play."),

    # ---- deputation: the two who go out ------------------------------------------
    ("knots", "medium_close", ["stent", "ogilvy"], 0.6, "over_shoulder",
     f"Medium close over the shoulder of {OGILVY} toward {STENT}, the two of them halted at the front of "
     "the crowd at night with the red ring of sand beyond them: Ogilvy's brown Norfolk shoulder "
     "and soft felt brim dark and near at the LEFT, Stent square in the right of the picture in "
     "his black frock coat and tall silk hat, with the red glow on one side of his long jaw.",
     "The camera holds a static shot over Ogilvy's shoulder, keeping Stent's face in the right of "
     "frame; Stent looks out at the pit and then back at Ogilvy and gives one short nod; Ogilvy's "
     "near shoulder turns a hand's breadth toward the pit.",
     "at the front of the crowd level with their eyes, two paces behind Ogilvy, a 50mm lens. The "
     "red glow of the pit comes from the RIGHT and lights Stent's jaw and hat brim; Ogilvy's "
     "shoulder in the near left is black",
     "Ogilvy's shoulder and hat brim fill the LEFT third of the frame from the TOP edge to the "
     "BOTTOM edge, black and out of focus. Stent stands at the RIGHT third, the panel cutting him "
     "at the middle of the chest, his head at the TOP third with the red glow along his jaw. The "
     "red ring of sand shows small between them at the CENTRE and a blue-black sky fills the TOP.",
     "friction", "Two men who have already sent for soldiers, going out themselves first."),

    ("knots", "wide", [], 0.8, "track_lateral",
     "Wide of the open sand at night from the front of the crowd: a small party of dark figures "
     "walking away from the camera across the flat sand toward the red ring, one of them carrying "
     "a white sheet on a pole that hangs slack, the ring of sand low beyond them with the mast "
     "above it, and the black heads and shoulders of the crowd across the bottom of the frame.",
     "The camera tracks sideways to the right, a truck with small amplitude behind the crowd's "
     "heads until the whole walking party is clear of them, travelling one long stride; the party "
     "walks on across the sand away from the camera and the gap between them and the crowd opens; "
     "the night wind lifts the slack white sheet once and drops it.",
     "at the front of the crowd looking out over their heads, a 35mm lens. The red glow comes from "
     "the CENTRE beyond them; the walking figures and the crowd read black and the white sheet is "
     "the only pale thing in the frame",
     "Black heads and shoulders of the crowd run across the BOTTOM third of the frame from the "
     "LEFT edge to the RIGHT edge. The small party walks away at the CENTRE, their whole figures "
     "inside the frame and a sixth of its height, with the pale sheet above them at the CENTRE. "
     "The red ring of sand lies beyond at the CENTRE, a tenth of the height of the frame, and a "
     "blue-black sky fills the TOP third.",
     "friction", "The same walk the narrator watched from the other side."),

    ("knots", "insert", [], 0.4, "tilt_up",
     "Insert on the red ring of sand at night: three separate puffs of thick green smoke going up "
     "one after another from behind the rim, each of them rolling and climbing, lit green from "
     "within, against a blue-black sky with the thin mast standing beside them.",
     "The camera tilts up from the rim of the sand with small amplitude until all three puffs of "
     "green smoke are inside the picture, travelling a hand's breadth; the first puff climbs and "
     "spreads, the second goes up through it, the third follows; the mast stands unmoved beside "
     "them.",
     "a hundred yards from the pit, low, a 135mm lens. The green smoke is lit from INSIDE and is "
     "the brightest thing in the frame; the sand rim below it reads dull red and the sky is black",
     "The three puffs of green smoke climb up the CENTRE of the frame from the CENTRE to the TOP "
     "edge, each a sixth of the width of the frame. The dull red rim of the sand runs across the "
     "BOTTOM third from the LEFT edge to the RIGHT edge, the thin mast stands at the RIGHT third, "
     "and a blue-black sky fills the rest.",
     "friction", "The signal the whole common can see and nobody can read."),

    ("knots", "wide", [], 0.4, "locked",
     "Wide of the flat sand at night: the small party of dark figures out in the open with white "
     "flame standing up around them, three of them already down and dark on the sand, the pole and "
     "its white sheet fallen sideways, and the red ring of sand beyond with the mast above it.",
     "The camera holds a static shot on the open sand, keeping the fallen party in the centre of "
     "frame; the white flame stands up around them and drops away; the pole with its sheet goes "
     "over sideways and lies still; smoke crosses the frame from the left.",
     "at the front of the crowd looking out over the sand, a 35mm lens. The white flame is the "
     "brightest thing in the frame and lights the sand around it; everything outside it is black",
     "The fallen party lies at the CENTRE of the frame, their whole figures inside it, a sixth of "
     "its height, with white flame standing up around them from the CENTRE to the TOP third. The "
     "fallen pole and its white sheet lie at the CENTRE RIGHT. The red ring of sand shows beyond "
     "at the CENTRE, black sand fills the BOTTOM third and a black sky fills the TOP third.",
     "turn", "The description tallies very closely with my own impressions."),

    # ---- beam: the hummock, and the road ----------------------------------------
    ("beam", "medium", [], 0.6, "low_angle",
     "Low medium on a hummock of heathery sand out on the common at night, a long low swell of "
     "ground with heather growing over its top, standing between the camera and the red glow "
     "beyond, its whole crest lit hard along one edge and the ground behind it dark.",
     "The camera keeps low against the hummock, a static shot from the height of the heather with "
     "the crest across the frame; a hard line of light runs along the crest from the left to the "
     "right and goes out; the heather along the top takes fire in a thin line and burns low.",
     "on the ground below the hummock looking up along it, three paces from its foot, a 50mm lens, "
     "a low angle. The light that runs along the crest comes from the LEFT and is the brightest "
     "thing in the frame; the ground behind the hummock is black",
     "The hummock of sand fills the BOTTOM half of the frame from the LEFT edge to the RIGHT edge, "
     "its crest running across the CENTRE. The hard line of light lies along that crest at the "
     "CENTRE, thin heather standing black along it, and a black sky fills the TOP half with a red "
     "glow low at the LEFT edge.",
     "turn", "A few yards of sand, and nothing else, between three hundred people and it."),

    ("beam", "wide", [], 0.8, "track_lateral",
     "Wide across the black common at night: a line of low bushes running away toward the road, "
     "each one taking fire in turn along the line as though a hand were touching them one after "
     "another, the fires small and separate and bright, and the dark line of beech trees along the "
     "road standing at the far end.",
     "The camera tracks sideways to the left, a truck with large amplitude along the line of "
     "bushes until the beech trees at the road are inside the picture, travelling two long "
     "strides; the bushes take fire one after another along the line away from the camera; the "
     "light reaches the foot of the beeches.",
     "out on the common level with the bushes, a 35mm lens. Each bush lights itself as it takes "
     "fire and lights the ground around it; the sky and the far trees are black",
     "The line of burning bushes runs from the BOTTOM LEFT away to the CENTRE RIGHT, each fire a "
     "twelfth of the height of the frame. The dark line of beech trees stands across the CENTRE "
     "at the far end, black ground fills the BOTTOM third, and a black sky fills the TOP third.",
     "turn", "An invisible hand, as it were, lighting the bushes as it hurried."),

    ("beam", "medium", [], 0.6, "tilt_up",
     "Medium on the tops of the beech trees along the road at night, seen from the road below: the "
     "high crowns of three beeches black against a black sky, their upper leaves catching light "
     "along one side, with the pale road and the black hedge showing at the bottom of the frame.",
     "The camera tilts up from the road with small amplitude until the crowns of all three beeches "
     "are inside the picture, travelling a hand's breadth; the upper leaves of the nearest crown "
     "take fire and the fire runs along the tops of the other two; burning leaves begin to come "
     "away and fall.",
     "in the road below the trees looking up, a 35mm lens. The fire in the crowns is the only "
     "light and it comes from ABOVE; the road below reads dull orange and the hedges are black",
     "The three burning crowns fill the TOP half of the frame from the LEFT edge to the RIGHT "
     "edge, orange against black. Their trunks run down through the CENTRE to the BOTTOM third, "
     "the pale road shows at the BOTTOM edge lit dull orange, and the black hedge crosses the "
     "BOTTOM RIGHT.",
     "turn", "The beam swung close over their heads, with a whistling note."),

    ("beam", "insert", [], 0.4, "locked",
     "Insert on the brickwork and a window of the corner house at night: red brick with its "
     "mortar courses showing, a sash window in a painted wooden frame, the glass whole and dark, "
     "and the fire from the trees lighting the wall from one side.",
     "The camera holds a static shot on the brickwork, keeping the window in the centre of frame; "
     "a crack opens across the bricks beside the window and runs down; the glass goes out of the "
     "sash all at once; the painted frame takes fire along its top edge and burns.",
     "in the road two paces from the wall, level with the window, a 50mm lens. The firelight comes "
     "from the LEFT and rakes across the brick; the window itself is black until the frame burns",
     "The brick wall fills the whole frame. The sash window sits at the CENTRE, a third of the "
     "height of the frame, its dark glass at the CENTRE and its painted frame around it. The "
     "mortar courses run across the frame from the LEFT edge to the RIGHT edge and the firelight "
     "rakes them from the LEFT.",
     "turn", "It splits the bricks, smashes the windows, fires the frames."),

    ("beam", "wide", [], 0.8, "crane_up",
     "Wide of the brick house at the corner of the road at night: its upper gable broken open and "
     "coming down in loose brick, a heap of rubble spreading into the pale road below it, the "
     "burning beech crowns standing over the road at the left, and the black common beyond.",
     "The camera rises from the road with large amplitude until the broken gable and the burning "
     "crowns above it both stand inside the picture, travelling one long stride; the gable sheds "
     "another course of brick into the road; dust goes up through the firelight and drifts left.",
     "in the road forty paces from the house, a 35mm lens. The burning crowns at the LEFT are the "
     "light; the house reads orange on its left face and black on its right",
     GEO_FIRE, "turn", "A portion of the gable of the house nearest the corner."),

    # ---- panic: the crowd turns --------------------------------------------------
    ("panic", "medium", [], 0.6, "pan_to",
     "Medium on the pale road under the burning beeches at night: sparks and burning twigs coming "
     "down into the road, single leaves falling still alight like drifting flakes of flame, the road "
     "surface lit orange and pitted with small bright fires where they have landed.",
     "The camera pans to the left across the road until the foot of the nearest beech is inside "
     "the picture, travelling a hand's breadth; sparks and burning twigs come down through the "
     "frame; two lit leaves land in the road and go on burning where they lie.",
     "in the road looking down at it, a 50mm lens. The light comes from ABOVE out of the burning "
     "crowns; the road reads orange and the hedges at the edges are black",
     "The pale road fills the BOTTOM two thirds of the frame from the LEFT edge to the RIGHT edge, "
     "lit orange, with small bright fires scattered across it. Falling sparks and lit leaves cross "
     "the CENTRE, the black foot of a beech stands at the LEFT third, and the black hedge runs "
     "across the TOP third.",
     "friction", "Sparks and burning twigs began to fall into the road."),

    ("panic", "medium_close", ["unnamed_neighbours_wife"], 0.4, "locked",
     "Medium close on the woman in the crowd at night, a woman of thirty in a dark cotton dress "
     "and a straw bonnet tied under her chin, her face turned up toward the burning trees, with "
     "the crowd packed dark and close on both sides of her.",
     "The camera holds a static shot on the woman, keeping her face in the centre of frame; a lit "
     "leaf comes down and catches in the straw of her bonnet and the straw takes fire at its brim; "
     "she claws the bonnet off her head with both hands and it goes down out of the frame still "
     "burning.",
     "in the crowd level with her face, two paces from her, a 50mm lens. The burning trees light "
     "her from ABOVE and from the LEFT; the crowd around her is black",
     "The woman's head and shoulders fill the CENTRE of the frame, the panel cutting her at the "
     "middle of the chest, her face at the CENTRE lit orange from above. Black heads and shoulders "
     "of the crowd press in from the LEFT edge and the RIGHT edge, and the burning crowns show "
     "orange at the TOP third.",
     "friction", "Hats and dresses caught fire."),

    ("panic", "medium", ["unnamed_mounted_policeman"], 0.6, "follow",
     f"Medium on {MOUNTED} coming down the road at a gallop through the crowd at night, both his "
     "hands clasped over the top of his helmet and his mouth wide open, his reins loose on the "
     "horse's neck, the horse running flat out with its ears back and people breaking away from it "
     "on both sides.",
     "The camera tracks beside him at a galloping pace with large amplitude, coming on down the "
     "road until the crowd closes in behind the horse, travelling two long strides; he keeps both hands clasped over his helmet the whole way "
     "past; his mouth stays open; the horse runs on past the camera and the crowd closes in "
     "behind it.",
     "at the roadside level with the horse's shoulder, four paces out, a 50mm lens. The burning "
     "trees light him from ABOVE and from behind; his face reads orange and the crowd is black",
     "The policeman and his horse fill the CENTRE and the RIGHT of the frame, the panel cutting "
     "the horse at the knee, his clasped hands and helmet at the TOP third. Black figures of the "
     "crowd break away at the LEFT third and the RIGHT edge, the pale road runs along the BOTTOM "
     "third, and orange burning crowns show at the TOP.",
     "friction", "The man whose job was to keep them back, going the other way first."),

    ("panic", "wide", [], 0.8, "crane_up",
     "Wide of the road under the burning beeches at night from above the crowd: three hundred "
     "people packed across the whole width of the road and every one of them turned the same way, "
     "back toward Woking, the front of them already pressing into the backs of those behind, and "
     "the fire in the crowns lighting the tops of their heads.",
     "The camera rises above the crowd with large amplitude until the whole width of the road and "
     "the turn of the crowd are inside the picture, travelling one long stride; the crowd turns "
     "all together and begins to move back down the road; the movement runs from the front of them "
     "to the back like a wave.",
     "above the crowd at the roadside, a 35mm lens. The burning crowns light them from ABOVE; "
     "their hats and shoulders read orange on top and the road between them is black",
     "The packed crowd fills the CENTRE and the BOTTOM two thirds of the frame from the LEFT edge "
     "to the RIGHT edge, their hats lit orange along the top. The pale road shows between them in "
     "the BOTTOM third, the burning beech crowns run across the TOP third, and black hedges stand "
     "at the LEFT edge and the RIGHT edge.",
     "friction", "They must have bolted as blindly as a flock of sheep."),

    # ---- banks: the road that is too narrow --------------------------------------
    ("banks", "wide", [], 0.8, "track_lateral",
     "Wide of the Chobham road at night where it runs down between high sandy banks: the road "
     "pinched to a cart's width, raw banks rising steeply above head height on both sides, the way "
     "between them nearly black, and the crowd jammed into that gap shoulder to shoulder with a "
     "red glow in the sky behind them.",
     "The camera tracks sideways to the right, a truck with small amplitude along the top of the "
     "bank until the full length of the pinched road is inside the picture, travelling one long "
     "stride; the crowd in the gap presses forward and stops and presses again; the gap holds them "
     "exactly where they stand.",
     "on the top of the bank looking down into the road, a 35mm lens. The only light is the red "
     "glow behind them in the sky; the tops of the banks read dull red and the road between them "
     "is nearly black",
     GEO_BANKS, "answer", "Where the road grows narrow and black between the high banks."),

    # THE BUTTON SHOT, and it has to carry a face: a dialogue line drives lips,
    # so the plan gate refuses one laid over an insert. The shriek was written
    # over the trampled boot and had to come back to a mouth.
    ("banks", "medium_close", ["unnamed_neighbours_wife"], 0.6, "low_angle",
     "Medium close on a woman jammed in the road between the banks at night, a woman of thirty in "
     "a dark shawl over a pale blouse with her hair coming down, her head turned back over her "
     "shoulder toward the red glow behind, her mouth wide open, packed black coats pressing "
     "against her on both sides.",
     "The camera keeps low in the road, a static shot at the height of her face with the packed "
     "coats all round; she looks back over her shoulder at the red sky and shouts; her free hand "
     "comes up against the coat of the person in front of her and pushes.",
     "down in the road among them, level with her face, two paces from her, a 50mm lens, a low "
     "angle. The red glow behind her is the only light; her face reads dull red down one side and "
     "the crowd around her is black",
     "The woman's head and shoulders fill the CENTRE of the frame, the panel cutting her at the "
     "middle of the chest, her face at the CENTRE turned back over her right shoulder. Packed "
     "black coats fill the LEFT edge and the RIGHT edge, the raw sandy bank rises black at the "
     "RIGHT third, and a strip of red sky shows at the TOP CENTRE.",
     "button", "The only thing said aloud in the chapter, and it is not true."),

    ("banks", "medium", [], 0.6, "track_lateral",
     "Low medium in the road between the banks at night, in among the crowd: dark coats and skirts "
     "packed close on every side of the camera, arms up, hats knocked sideways, the raw sandy bank "
     "rising steeply above them on the right, and a narrow strip of red sky showing between the "
     "bank tops.",
     "The camera keeps low in the road, a static shot from the height of a child with the packed "
     "coats all round; the crowd surges forward against itself and the packed coats swing together "
     "and back; one arm comes up out of the press and stays up.",
     "down in the road among them, low at a child's height, a 35mm lens, a low angle. The red sky "
     "between the bank tops is the only light; the people around the camera are black and their "
     "edges are dull red",
     "Packed black coats and skirts fill the LEFT edge, the RIGHT edge and the BOTTOM half of the "
     "frame. The raw sandy bank rises at the RIGHT third from the BOTTOM to the TOP third, a "
     "narrow strip of red sky shows between the bank tops at the TOP CENTRE, and one raised arm "
     "stands black at the CENTRE.",
     "answer", "A desperate struggle, at the bottom of a sandpit of their own."),

    ("banks", "insert", [], 1.0, "locked",
     "Insert on the road surface at night between the banks: trodden sand and loose grit, a small "
     "child's boot lying on its side where it has come off, a woman's straw hat crushed flat "
     "beside it, and the marks of many boots pressed over both of them.",
     "The camera holds a static shot on the ground, keeping the small boot in the centre of frame; "
     "a last pair of boots comes through the top of the frame and goes on past; grit is kicked "
     "across the small boot and settles; the boot and the hat lie still.",
     "down at the road surface, a 50mm lens. The red glow comes from ABOVE and behind; the ground "
     "reads dull red and the boot and the hat are black",
     "The trodden road surface fills the whole frame. The small child's boot lies at the CENTRE on "
     "its side, a fifth of the width of the frame, and the crushed straw hat lies beside it at the "
     "CENTRE RIGHT. Boot marks run across the ground from the LEFT edge to the RIGHT edge and a "
     "dull red light falls across all of it from the TOP.",
     "answer", "Three persons at least, and Wells gives them no names."),
]

BEATS = {0: (1.0, 0.4), 1: (0.8, 0.0), 3: (1.0, 0.6), 4: (1.2, 0.6), 7: (0.8, 0.4),
         11: (0.6, 0.0), 12: (1.0, 0.4), 14: (1.2, 1.4), 15: (1.0, 0.4),
         # THE SILENT SHOTS CARRY THEIR OWN TIME. A shot with no line is only
         # its beat and its coda, and at 1.6 s two of them pack into one take --
         # which is what `groups` does with anything under the 8 s budget, and
         # what ONE PER TAKE refuses. A picture worth cutting to is worth four
         # seconds.
         19: (1.5, 3.0), 21: (1.5, 3.0), 22: (1.5, 3.2), 26: (1.5, 4.0), 27: (1.5, 3.5),
         18: (0.8, 0.4), 20: (0.8, 0.8), 23: (1.2, 0.8), 24: (1.2, 0.6), 25: (1.2, 0.8)}

TURNS = {14: "a deputation going out to be answered -> a common that has answered",
         15: "a crowd that is being spared -> a crowd that does not know it",
         19: "a road people walked out along -> a road coming down on them",
         24: "a crowd running from the ray -> a crowd that is its own disaster"}

LINES = [
    # ONE LINE A SHOT, and short. The take budget is 8 s and the builder
    # projects words at 2.58 a second: shots 1, 3 and 4 carried two lines each
    # and projected 12-13 s, which is not a take, it is two.
    ("narration", "unnamed_first_person_narrator",
     "It is still a matter of wonder how they kill so swiftly and so silently.", 0),
    ("narration", "unnamed_first_person_narrator",
     "A chamber of heat, and a mirror to throw it in a parallel beam.", 1),
    ("narration", "unnamed_first_person_narrator",
     "Whatever will burn burns at its touch.", 2),
    ("narration", "unnamed_first_person_narrator",
     "That night forty people lay about the pit, and the common burned till morning.", 3),
    ("narration", "unnamed_first_person_narrator",
     "In Woking the shops had shut when it happened.", 4),
    ("narration", "unnamed_first_person_narrator",
     "So the shop people walked out to see it, brushed up after the day.", 5),
    ("narration", "unnamed_first_person_narrator",
     "Few of them even knew the cylinder had opened.", 6),
    ("narration", "unnamed_first_person_narrator",
     "They found knots of people already there, watching the mirror turn.", 7),
    ("narration", "unnamed_first_person_narrator",
     "By half past eight there were three hundred of them.", 8),
    ("narration", "unnamed_first_person_narrator",
     "Three policemen, with Stent's instructions: keep them back.", 9),
    ("narration", "unnamed_first_person_narrator",
     "And booing, from the sort to whom a crowd is an occasion for noise.", 10),
    # Wells quotes one line in the whole chapter. He does state the rest
    # happened -- the wire to the barracks, the decision to go out again -- so
    # the deputation says what the chapter says it did, on the one shot close
    # enough to drive a mouth.
    ("dialogue", "stent", "Nine is two hours. They are out there now.", 11),
    ("dialogue", "ogilvy", "Then we go out to them ourselves.", 11),
    ("narration", "unnamed_first_person_narrator",
     "They had wired the barracks. Soldiers by nine, and it was half past eight.", 12),
    ("narration", "unnamed_first_person_narrator",
     "Then they went back to lead the advance themselves.", 13),
    ("narration", "unnamed_first_person_narrator",
     "Three puffs of green smoke. A humming note. The flashes of flame.", 14),
    ("narration", "unnamed_first_person_narrator",
     "That crowd had a far narrower escape than mine.", 15),
    ("narration", "unnamed_first_person_narrator",
     "A hummock of heathery sand took the lower part of the ray.", 16),
    ("narration", "unnamed_first_person_narrator",
     "A few yards higher, and none of them could have lived to tell it.", 17),
    ("narration", "unnamed_first_person_narrator",
     "The beam swung over their heads and lit the tops of the beeches.", 18),
    ("narration", "unnamed_first_person_narrator",
     "It split the bricks, brought down a gable, and the road began to burn.", 20),
    ("narration", "unnamed_first_person_narrator",
     "Where the road grows narrow between the banks, the crowd jammed.", 23),
    ("narration", "unnamed_first_person_narrator",
     "Three at least did not get out. Two women, and a little boy.", 24),
    # THE BUTTON IS NEVER THE PROTAGONIST'S (rule 5), and it is the only thing
    # said aloud in the chapter -- and the only thing in it that is untrue.
    # Nothing was coming down that road. The words killed three people; the ray
    # killed none of them.
    ("dialogue", "unnamed_neighbours_wife", "They're coming!", 25),
]

BEDS = [{"from_shot": 0, "tone": "grave"}, {"from_shot": 4, "tone": "plain"},
        {"from_shot": 8, "tone": "uneasy"}, {"from_shot": 12, "tone": "thrilling"},
        {"from_shot": 20, "tone": "thrilling"}, {"from_shot": 25, "tone": "grave"}]

# The dramatic spine, one shot at a time. Exactly one hook, one turn, one
# answer and one button -- the plan gate counts them, and it counted the
# sections I had typed into the shot tuples and found none of the four.
# WHERE EACH SHOT STANDS ALONG ITS SETUP'S ROUTE, 0 at the start and 1 at the
# far end. The route gate refuses a shot that goes BACKWARDS along it, which
# the hand-typed values did at shot 6: a camera that walks back up the road it
# just came down is a camera the audience cannot follow.
PATHS = {
    0: 0.1, 1: 0.3, 2: 0.5, 3: 0.8,                            # ray
    4: 0.2, 5: 0.5, 6: 0.9,                                    # road
    7: 0.1, 8: 0.2, 9: 0.3, 10: 0.4,                           # knots
    11: 0.5, 12: 0.6, 13: 0.8, 14: 0.9,                        # knots, the deputation
    15: 0.1, 16: 0.3, 17: 0.5, 18: 0.7, 19: 0.9,               # beam
    20: 0.2, 21: 0.4, 22: 0.6, 23: 0.9,                        # panic
    24: 0.2, 25: 0.5, 26: 0.7, 27: 0.9,                        # banks
}

SECTIONS = {
    0: "hook",
    1: "setup", 2: "setup", 3: "setup",
    4: "transition", 5: "setup", 6: "transition", 7: "setup",
    8: "friction", 9: "friction", 10: "friction", 11: "friction",
    12: "friction", 13: "friction",
    14: "spike",
    15: "turn",
    16: "spike", 17: "spike", 18: "spike", 19: "spike", 20: "spike",
    21: "reaction",
    22: "spike",
    23: "reaction",
    24: "answer",
    25: "button",
    26: "runout", 27: "runout",
}

MOVES = {i: s[4] for i, s in enumerate(S)}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.6, 0.0))
        shots.append(dict(index=i, section=SECTIONS.get(i, section), setup=setup, size=size, faces=list(faces), view="",
                          path=PATHS.get(i, path), frame=frame, motion=motion, camera=camera, at_rest=at_rest,
                          end="", changed="", beat_s=beat, coda_s=coda, turn=TURNS.get(i, ""), why=why,
                          cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=6, title="The Heat-Ray in the Chobham Road",
                question="Tonight, does the crowd that came to watch get home?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 24",
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
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words; "
          f"dialogue {said / words:.1%}; silent shots {silent}")
    print(f"measured projection at 2.72 w/s: "
          f"{words / 2.72 + sum(s['beat_s'] + s['coda_s'] + 0.5 for s in doc['shots']):.0f}s")
    print(f"moves: {counts}")
    print(OUT)
