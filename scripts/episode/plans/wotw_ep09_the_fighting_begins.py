r"""The War of the Worlds, episode 9 -- "The Fighting Begins", chapter 9.

THE BRICK.  A man spends a hot Saturday winning an imaginary war, and loses
his house in ninety seconds.  Every picture before the turn is somebody being
confident about a fight nobody has seen; every picture after it is the same
man doing what the confident people said would not be necessary.

  QUESTION  What did he think a fight with them would look like?
  TURN      shot 16.  He grips his wife's arm and runs her out into the road.
            The man who spent the afternoon defeating the invaders in a dozen
            striking ways takes about twenty seconds to become a refugee, and
            the only thing that changed is that the college is out of the way.
  ANSWER    shot 21: the cart at his own gate with his wife and his servant
            up in it, and behind the house the whole crest of Maybury Hill
            going up in thick streamers of black smoke shot with red fire.
            That is what a fight with them looks like.
  BUTTON    line 21, the hussar: "Crawling out in a thing like a dish cover!"
            The only news anybody gives him all day, bawled over a shoulder
            by a man who is running, and then hidden by smoke.  It is true,
            and it is useless, which is the fourth time this series has ended
            an episode on that exact shape (ep06 untrue, ep07 argued away,
            ep08 sold as a headline, ep09 shouted while running).

THE NARRATOR IS IN THE PICTURE THIS TIME, and that is the point.  ep08 kept
him out because he spent that night indoors and said so.  This chapter is
the first where he ACTS -- he grips an arm, he buys a horse, he packs plate
in a tablecloth -- so he is cast in five shots, and every one of them has him
doing something rather than watching something.

THE CONFIDENT MEN GET THE FIRST THIRD.  The milkman ("they aren't to be
killed, if that can possibly be avoided"), the neighbour with his handful of
strawberries, the sappers arguing about trenches and rushes.  None of them is
wrong about anything they can see.  That is why the turn lands.

THE HOUR COMES FROM THE REFERENCE AND NEVER FROM THE WORDS (measured twice on
ep05, 2026-09-20).  The bridge, the common and Maybury Hill are all drawn
already, and all three are drawn at NIGHT.  This episode is a hot bright
Saturday that ends in a red evening, so all three get their own hour drawn.

THE CAST IS DESCRIBED FROM ITS BOUND ROWS (`refs.json`), never from memory --
ep07 shipped four characters that contradicted their own rows.  The narrator,
his wife and the neighbour are quoted from theirs below.  The milkman, the
sapper, the landlord and the hussar are new, and each is given a silhouette,
a colour and a hairline that none of the other six shares.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds"
OUT = BOOK / "episodes" / "ep09" / "plan.json"

WHERE = "Maybury, Surrey, 1894"
LIGHT = "low raking sun and black shadows"
LOOK = "Angular stylised 3D animation, brush-stroke texture"

# ---- the four new people, each a silhouette the other six do not have -------
MILKMAN = ("the milkman, a stocky short-legged man of forty-four with strong shoulders, a round "
           "ruddy face, a snub nose, cheerful creases at the eyes, bright blue eyes and short "
           "chestnut curly hair, a thick chestnut walrus moustache covering his upper lip, in a "
           "brown felt pork-pie hat with a narrow brim, a buff holland linen dairyman's coat to "
           "the thigh and a long white apron to the shin")
SAPPER = ("Snippy the sapper, a wiry narrow-shouldered man of twenty-six with quick hands, a long "
          "narrow face, a sharp pointed nose, thin lips and a prominent Adam's apple, fair freckled "
          "skin sunburnt at the neck, sandy mouse-brown hair cropped short, a clipped sandy "
          "moustache, pale grey eyes set close together and a small white scar through his right "
          "eyebrow, in a small round dark-blue pillbox cap with a narrow yellow band on a chin "
          "strap and a dirty brick-red serge jacket with garter-blue collar and cuffs hanging "
          "unbuttoned over a blue-grey flannel shirt")
LANDLORD = ("the landlord of the Spotted Dog, a sturdy barrel-chested man of fifty-two with a thick "
            "neck and heavy forearms, a broad red face, a fleshy nose and small shrewd blue eyes, "
            "brown hair flecked with grey and thinning on the crown and brushed flat, heavy "
            "grey-brown mutton-chop whiskers joined to a full moustache with a clean-shaven chin, "
            "bare-headed, in a white cotton shirt with the sleeves rolled to the elbow and black "
            "sleeve garters, a black broadcloth waistcoat with a brass watch chain and a long tan "
            "leather cellarman's apron from chest to shin")
HUSSAR = ("the dismounted hussar, a lean horseman of twenty-two with long thighs and narrow hips, "
          "an oval olive-tanned face, a straight nose, dark brown eyes, brown curly hair cropped "
          "close to the skull, a clean-shaven boyish jaw and a thin pale scar across his left "
          "eyebrow, in a dark green pillbox forage cap with a yellow band on a chin strap and a "
          "dark rifle-green serge hussar jacket with yellow cord frogging and a yellow-edged "
          "collar, its right sleeve torn and blackened with soot")

# ---- the three bound people, quoted from their rows in refs.json ------------
NARRATOR = ("the narrator, a slender narrow-shouldered man of thirty-four with long limbs, a long "
            "oval face, a high forehead, a long straight nose, straight dark brows and grey eyes, "
            "his dark brown hair cut short at the back and sides and parted on the left, a neat "
            "close-trimmed dark brown moustache with shaven cheeks and chin, in a mid-grey "
            "herringbone tweed jacket and waistcoat with a silver watch chain, a white starched "
            "turn-down collar and a dark green knitted tie")
WIFE = ("the narrator's wife, a slim straight-carried woman of twenty-nine with an oval face, wide "
        "hazel eyes, softly arched chestnut brows and light freckles across the nose, her thick "
        "chestnut-auburn hair waved and swept up into a soft pompadour, in a sage-green linen "
        "walking costume with a short fitted jacket over a cream high-collared blouse and a long "
        "sage-green skirt, a small sage-green felt toque with a cream ostrich tip pinned to her "
        "hair")
NEIGHBOUR = ("the neighbour, a tall spare stooping man of forty-eight with long arms, a long "
             "hollow-cheeked face with prominent cheekbones, mild hazel eyes, grey-brown hair "
             "receding at the temples and a short pointed grey goatee with shaved cheeks and lip, "
             "in a wide-brimmed straw gardening hat, a collarless white shirt with the sleeves "
             "rolled and sky-blue sleeve garters, a tan canvas gardening apron and white "
             "flannel trousers")

# ---- the five places, each naming its own light and where it comes from -----
GARDEN_MORNING = (
    "the garden behind a brick villa at Maybury on a hot close summer morning in 1894: a clipped "
    "lawn with a gravel path along it, a low paling fence at the far side with a side gate in it, "
    "standard roses and a bed of stocks against the brick, a dark cedar at one corner and the open "
    "heath rising beyond the fence to a flat horizon of pines; the light is high flat hazy sunlight "
    "the morning sun from the left over the pines, so the lawn reads bleached green, the brick reads pale warm red and the shadows "
    "under the cedar are short and soft")
BRIDGE_DAY = (
    "the road under a brick railway bridge on the Maybury road at midday in 1894: a low round brick "
    "arch with a soot-blackened underside carrying the railway embankment over the road, the pale "
    "dusty road running through it, the canal running flat and green alongside below a towpath, "
    "hedges and elms on the far bank and the open common beyond; the light is hard white midday sun "
    "sun from the far end of the arch, so the road reads bleached and chalky, the brick "
    "reads dark red and the water reads flat green")
PIT_DAY = (
    "the sand-pits on Horsell Common on a hot bright afternoon in 1894: the raw ring of flung yellow "
    "sand round the crater, a single continuous streamer of grey smoke standing straight up out of "
    "it in the still air, knee-deep heather and dark furze running away flat to a horizon of low "
    "pines, and a shallow ditch with spoil thrown up along the near side; the light is a hard high "
    "sun from the right, so the sand ring reads raw pale yellow, the heather reads dusty olive and "
    "every shadow lies short to the LEFT of the thing that throws it")
CREST_BURNING = (
    "the same walled lawn on the crest of Maybury Hill with the valley below it on fire: the broken "
    "roof line of the Oriental College and a half-fallen church tower burning above the garden "
    "wall, thick black smoke driving up off them across the whole sky, a wooden summerhouse and a "
    "white gate on the near lawn, and broken red chimney brick scattered fresh on the grass; the "
    "light is the fire itself, low and raking from beyond the wall, so the lawn reads scorched "
    "orange, the summerhouse and the gate read hot red on their fire side and black on the other")
INN_BAR = (
    "the bar of a small country public house on a summer evening in 1894: a scrubbed wooden counter "
    "along one side with beer engines and their brass handles standing on it, shelves of bottles and "
    "pewter behind, a settle and a plain table against the far wall, a bare board floor, and a small "
    "sash window with the evening outside it; the light is a hanging oil lamp over the counter and "
    "the window, so the counter reads warm yellow, the brass reads bright and the corners are brown "
    "and dark")

# ---- the geometry of each place: WHERE things are, in cells -----------------
GEO_GARDEN = (
    "The gravel path runs from the BOTTOM CENTRE away to the white paling gate at the CENTRE LEFT, "
    "with mown lawn and flower borders on both sides of it in the BOTTOM half. The brick wall of "
    "the house fills the RIGHT third from the BOTTOM to the TOP with its sash windows in it, and a "
    "tall dark cedar stands against it at the CENTRE RIGHT. The low white paling runs across the "
    "CENTRE from the LEFT edge to the CENTRE RIGHT, the open heather of the common lies flat beyond "
    "it, and a line of pines and a pale hazy sky fill the TOP third at the LEFT.")
GEO_BRIDGE = (
    "The dark brick of the bridge fills the LEFT half and the TOP third of the frame, its arch "
    "springing from a pier at the LEFT third and coming down again at the RIGHT edge. The bright "
    "opening of the arch shows at the CENTRE RIGHT with hard white daylight, hedges and elms in it, "
    "and the green canal water lying flat beyond. The pale dusty road runs from the BOTTOM edge up "
    "through the opening, and grass and weeds edge it at the BOTTOM LEFT and the BOTTOM RIGHT.")
GEO_PIT = (
    "Dusty olive heather fills the BOTTOM third of the frame from the LEFT edge to the RIGHT edge, "
    "with the shallow ditch and its thrown-up spoil running across the BOTTOM LEFT. The raw ring of "
    "flung yellow sand runs across the CENTRE, a tenth of the height of the frame, and the single "
    "grey streamer of smoke stands straight up out of it at the CENTRE into the TOP third. Low pines "
    "close the horizon behind the ring and a pale hot sky fills the TOP third.")
GEO_LAWN = (
    "The scorched lawn fills the BOTTOM half of the frame from the LEFT edge to the RIGHT edge with "
    "broken red chimney brick scattered on it at the BOTTOM CENTRE and the BOTTOM RIGHT. The "
    "summerhouse stands at the LEFT third, the low brick garden wall runs across the CENTRE from "
    "the LEFT edge to the RIGHT edge with the white gate in it at the CENTRE RIGHT, the broken "
    "roof line and the burning church tower stand above the wall at the CENTRE, and thick black "
    "smoke fills the TOP third from the CENTRE to the RIGHT edge.")
GEO_BRIDGE_PARAPET = (
    "The brick parapet runs across the BOTTOM third of the frame from the LEFT edge to the RIGHT "
    "edge. The soot-blackened brick of the arch fills the LEFT half from the BOTTOM to the TOP "
    "behind it, and the bright opening of the arch shows at the CENTRE RIGHT with hard white "
    "daylight and green hedges standing in it.")
GEO_INN = (
    "The scrubbed counter runs across the BOTTOM of the frame from the LEFT edge to the CENTRE RIGHT "
    "with the brass beer-engine handles standing up from it at the CENTRE. Shelves of bottles and "
    "pewter fill the LEFT third behind it from the BOTTOM to the TOP, the hanging oil lamp burns at "
    "the TOP CENTRE, and the small sash window with the evening in it shows at the RIGHT third.")

SETUPS = {
    "garden": dict(
        described=GARDEN_MORNING, cast=["unnamed_milkman", "unnamed_neighbour"],
        landmark="the side gate in the low paling fence", landmark_at="far_end",
        landmark_size="is a fifth of the height of the frame",
        route="from the gravel path across the lawn toward the side gate in the fence",
        geometry=GEO_GARDEN,
        crowd="",
        outdoors=True, props=[], location="narrators_garden"),
    "bridge": dict(
        described=BRIDGE_DAY, cast=["snippy"],
        landmark="the bright opening of the arch with the road going away through it",
        landmark_at="far_end",
        landmark_size="is a third of the height of the frame",
        route="from the near mouth of the arch along the road through it toward the daylight beyond",
        geometry=GEO_BRIDGE,
        crowd="sappers in small round caps and dirty brick-red jackets unbuttoned over blue shirts, "
              "sitting on the parapet, standing in the shade of the arch, one squatting over the dust",
        outdoors=True, props=[], location="maybury_canal_bridge"),
    "pit": dict(
        described=PIT_DAY, cast=["unnamed_first_person_narrator"],
        landmark="the raw ring of flung yellow sand round the crater", landmark_at="far_end",
        landmark_size="is a tenth of the height of the frame",
        route="from the heather along the shallow ditch out toward the ring of the pit",
        geometry=GEO_PIT,
        crowd="",
        outdoors=True, props=[], location="horsell_common"),
    "lawn": dict(
        described=CREST_BURNING,
        cast=["unnamed_first_person_narrator", "narrators_wife", "unnamed_hussar"],
        landmark="the burning church tower standing above the garden wall",
        landmark_at="far_end",
        landmark_size="is a quarter of the height of the frame",
        route="from the summerhouse across the scorched lawn to the white gate in the wall",
        geometry=GEO_LAWN,
        crowd="",
        outdoors=True, props=[], location="maybury_hill"),
    "inn": dict(
        described=INN_BAR, cast=["unnamed_landlord", "unnamed_first_person_narrator"],
        landmark="the brass beer-engine handles standing on the counter", landmark_at="far_end",
        landmark_size="is a fifth of the height of the frame",
        route="from the door along the bare boards to the counter and its brass handles",
        geometry=GEO_INN,
        crowd="",
        outdoors=False, props=[], location="spotted_dog"),
}

#  setup   size   faces  path  move   frame / motion / camera / geometry / section / why
S = [
    # ---- garden: three confident men, and none of them wrong ----------------
    ("garden", "wide", [], 0.1, "crane_up",
     "Wide across a bleached lawn behind a brick villa on a hot hazy summer morning, the gravel "
     "path running along it, a low paling fence with a side gate at the far side, a dark cedar at "
     "one corner and the open heath and its pines lying flat and empty beyond the fence.",
     "The camera rises from the lawn with small amplitude until the fence, the gate and the flat "
     "heath beyond them all stand inside the picture, travelling one short stride; a lark goes on "
     "rising over the heath; the leaves of the cedar go on stirring a little in the hot air.",
     "on the lawn at a standing man's eye looking toward the fence, a 35mm lens. The light is high "
     "flat hazy sun from the TOP; the lawn reads bleached, the brick reads pale red and the shadows "
     "are short",
     GEO_GARDEN, "hook", "Saturday lives in my memory as a day of suspense."),

    ("garden", "medium", ["unnamed_milkman"], 0.4, "push_in",
     "Medium on " + MILKMAN + " standing at the side gate in the low paling fence on a hot hazy "
     "morning with a brass milk can hooked on one finger, the gate held half open against his hip "
     "and the flat empty heath running away behind him.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling one short stride; he goes on speaking and lifts the brass "
     "can a little as he does; the gate goes on resting against his hip.",
     "at the fence level with his chest, four paces from him, a 50mm lens. The hazy sun comes from "
     "the TOP and slightly BEHIND him; his canvas coat reads dull brown and the heath reads pale",
     GEO_GARDEN, "setup", "The milkman came as usual, and had the night's news at the gate."),

    ("garden", "medium", ["unnamed_neighbour"], 0.6, "track_lateral",
     "Medium on " + NEIGHBOUR + " leaning over the low paling fence with a handful of strawberries "
     "held out across it, his ash stick hooked over the rail beside him and the hazy heath flat "
     "behind him.",
     "The camera tracks sideways to the right along the fence, a truck with small amplitude, until "
     "the side gate already in the picture is at the centre, travelling one short stride; he goes on "
     "holding the strawberries out across the rail and laughs as he speaks; his free hand goes on "
     "resting on the top of the paling.",
     "at the fence level with his chest, four paces from him, a 50mm lens. The hazy sun comes from "
     "the TOP; his striped blazer reads pale blue and white and the heath behind reads bleached",
     GEO_GARDEN, "setup", "My neighbour was of opinion the troops would destroy them during the day."),

    ("garden", "insert", [], 0.8, "tilt_up",
     "Insert past the paling fence at a flat haze of grey smoke standing over a line of pine woods "
     "far off across the heath on a hot hazy morning, the heather running away bleached and empty "
     "between, and the furze below the smoke standing green and unburnt.",
     "The camera tilts up from the heather to the haze of smoke already in the picture until the "
     "smoke stands in the middle of the frame, travelling a forearm; the haze goes on "
     "drifting sideways above the pines by a thumb’s width; the heather goes on stirring in the hot air.",
     "at the fence looking out across the heath, an 85mm lens. The hazy sun comes from the TOP; the "
     "smoke reads pale grey and the pines read dusty dark green",
     GEO_GARDEN, "setup", "Another of those blessed things had fallen by the Byfleet golf links."),

    # ---- bridge: the army, arguing about a fight it has not seen ------------
    ("bridge", "medium", [], 0.1, "push_in",
     "Wide on the road under a brick railway bridge at midday, the soot-blackened arch overhead, "
     "sappers in small round caps and dirty brick-red jackets unbuttoned over blue shirts sitting "
     "along the parapet and standing in the shade of it, and the pale dusty road running away bright "
     "through the opening beyond them.",
     "The camera pushes in along the road toward the bright opening of the arch with small "
     "amplitude, travelling one short stride; the men go on talking among themselves in the shade; "
     "one of them goes on turning a mess tin over in his hands.",
     "in the road at a standing man's eye, a 35mm lens. Hard white daylight stands in the opening "
     "at the CENTRE and the shade under the arch is cool; the road reads chalky and the brick reads "
     "dark red",
     GEO_BRIDGE, "setup", "Under the railway bridge I found a group of sappers."),

    ("bridge", "medium_close", ["snippy"], 0.35, "push_in",
     "Medium close on " + SAPPER + " sitting on the parapet in the shade of the arch with his "
     "forearms on his knees and his short entrenching spade leaning against the brick beside "
     "him, the dark brick of the arch close behind him.",
     "The camera pushes in toward his face with small amplitude until his head fills the middle of "
     "the picture, travelling a forearm; he goes on speaking and opens one hand flat as he does; he "
     "goes on knocking the back of that hand twice against his own knee.",
     "in the shade level with his eyes, three paces from him, an 85mm lens. The daylight comes out "
     "of the bright arch opening at the LEFT and rakes across him; his red jacket reads dull brick "
     "and the brick behind him reads dark",
     GEO_BRIDGE_PARAPET + " His head is a third of the frame's height.",
     "friction", "Snippy, who wanted a trench, and had thought about it."),

    ("bridge", "medium", [], 0.5, "pan_to",
     "Medium along the pale dusty road beyond the arch at a single soldier standing sentinel in the "
     "middle of it in the hard midday sun, his rifle grounded beside his boot, the hedges and elms "
     "running away on both sides and the empty road going on past him.",
     "The camera pans to the right along the road until the sentinel already in the picture is at "
     "the centre, travelling one short stride; he goes on standing where he is and shifts his weight "
     "once; the dust goes on lifting off the road behind him.",
     "in the road level with his chest, eight paces from him, an 85mm lens. Hard white sun comes "
     "from the CENTRE beyond the arch; the road reads bleached and his shadow lies short and black "
     "under him",
     GEO_BRIDGE, "friction", "No one was allowed over the canal, and a sentinel stood in the road."),

    ("bridge", "insert", [], 0.7, "tilt_down",
     "Medium down at a soldier squatting on his heels in the dust of the road in the shade of the "
     "arch, scratching a long straight line and then a second beside it with the point of a stick, "
     "boots and puttees of other men standing round the edge of the drawing.",
     "The camera tilts down from the standing men to the drawing in the dust already in the picture "
     "until the scratched lines are in the middle of the frame, travelling a forearm; the "
     "stick goes on drawing the second line; the dust goes on lifting where it drags.",
     "over his shoulder looking down at the road, a 50mm lens. The daylight comes from the CENTRE "
     "beyond the arch; the dust reads pale and the scratched lines read dark",
     GEO_BRIDGE, "friction", "You always want trenches; you ought to have been born a rabbit."),

    ("bridge", "close", ["snippy"], 0.85, "push_in",
     "Close on the face of " + SAPPER + " in the shade of the arch, his chin lifted and his cap "
     "pushed back off his forehead, the dark brick soft and out of focus behind him.",
     "The camera pushes in on his face with small amplitude until it fills the middle of the "
     "picture, travelling a forearm; he goes on speaking with his chin up; his head "
     "goes on nodding once toward the common as he says it.",
     "in the shade level with his eyes, two paces from him, an 85mm lens. The daylight out of the "
     "bright arch opening at the LEFT falls on his face, and the brick edge of the arch at the "
     "CENTRE throws its own shadow across the right of it",
     GEO_BRIDGE_PARAPET + " His head is half the frame's height.", "reaction", "Octopuses, said he; fighters of fish it is this time."),

    # ---- pit: the enemy declines to be looked at ----------------------------
    ("pit", "wide", [], 0.15, "crane_up",
     "Wide across dusty olive heather at the raw ring of flung yellow sand round the crater on a "
     "hot bright afternoon, one continuous grey streamer of smoke standing straight up out of it in "
     "the still air, the heath running away flat to low pines, and the raw sand lying still and bare "
     "inside its ring.",
     "The camera rises from the heather with small amplitude until the whole ring of sand and the "
     "standing streamer of smoke are inside the picture, travelling one short stride; the streamer "
     "goes on rising straight up out of the pit; the heather goes on stirring in the hot air.",
     "on the heath at a standing man's eye, a 35mm lens. A hard high sun stands at the RIGHT; the sand ring reads "
     "raw pale yellow, the heather reads dusty olive and every shadow lies short",
     GEO_PIT, "setup", "The Martians did not show an inch of themselves all day."),

    ("pit", "medium", [], 0.4, "track_lateral",
     "Medium along a shallow ditch in the heather at a soldier lying flat in it on his elbows with a "
     "long pole in both hands and a white flag on the end of it held up above the spoil, the raw "
     "sand ring of the pit far off standing quiet and unanswering far beyond him.",
     "The camera tracks sideways to the right along the ditch, a truck with small amplitude, until "
     "the ring of sand already in the picture is at the centre, travelling one short stride; he goes "
     "on swinging the pole from side to side above the spoil through a hand’s breadth; the flag goes on turning over "
     "on itself as it swings.",
     "at the lip of the ditch level with the spoil, five paces from him, a 50mm lens. A hard high sun stands at the "
     "RIGHT; the flag reads bright white and the heather reads dusty olive",
     GEO_PIT, "friction", "It was done by a man in a ditch with a flag on a long pole."),

    ("pit", "medium", ["unnamed_first_person_narrator"], 0.65, "push_in",
     "Medium on " + NARRATOR + " standing in the heather in the hard afternoon sun with his straw "
     "boater in one hand and his hair flat with heat, looking out across the heath toward the raw "
     "ring of sand with his chin up, the flat common running away behind him.",
     "The camera pushes in toward him with small amplitude until his head and shoulders fill the "
     "middle of the picture, travelling one short stride; he goes on looking out across the heath "
     "and turns the boater once right over in his hand; his shoulders go on standing square.",
     "in the heather level with his chest, four paces from him, a 50mm lens. A hard high sun stands at the "
     "RIGHT; his grey tweed reads pale and bleached and the heather behind him reads olive",
     GEO_PIT, "reaction", "My imagination became belligerent and defeated them a dozen ways."),

    # ---- lawn: ninety seconds -----------------------------------------------
    ("garden", "medium", ["unnamed_first_person_narrator", "narrators_wife"], 0.9, "track_lateral",
     "Medium on " + NARRATOR + " and " + WIFE + " sitting facing each other at a small table set "
     "out on their own lawn at six in the evening with a tea tray between them, both of them "
     "leaning in and talking, and the flower borders and the white paling gate behind them.",
     "The camera tracks sideways to the left along the lawn, a truck with small amplitude, until "
     "both of them are in the middle of the picture, travelling one short stride; he goes on "
     "talking with one hand turned up on the table; she goes on holding her cup in both hands "
     "and nods once.",
     "on the lawn level with their shoulders, four paces from them, a 50mm lens. The low evening "
     "sun comes from the LEFT across the lawn; the tea things read white and the borders behind "
     "them read dark",
     GEO_GARDEN, "setup", "We sat at tea in the summerhouse talking about the battle."),

    ("lawn", "wide", [], 0.35, "crane_up",
     "Wide from the lawn across the paling at the tops of the trees about the Oriental College below "
     "and beyond it bursting into smoky red flame, the broken roof line of the college standing "
     "behind them, and black smoke going up off the whole of it into a sky already going dark.",
     "The camera rises from the lawn with small amplitude until the burning treetops and the broken "
     "roof line behind them are both inside the picture, travelling one short stride; the flame goes "
     "on standing up out of the treetops; the smoke goes on rolling up off them into the sky.",
     "on the lawn at a standing man's eye looking over the paling, a 35mm lens. The light is low red "
     "firelight from the CENTRE LEFT and below; the lawn reads scorched gold and the smoke reads "
     "black",
     GEO_LAWN, "spike", "The tops of the trees about the Oriental College burst into flame."),

    ("lawn", "insert", [], 0.45, "tilt_down",
     "Medium across the paling at the tower of a little church beside the burning college, its "
     "masonry going out of line and sliding down into its own ruin, red flame standing up behind it "
     "and a column of dust lifting where it falls.",
     "The camera tilts down from the top of the tower to the ruin already in the picture until the "
     "falling masonry is in the middle of the frame, travelling a forearm; the tower goes on "
     "sliding down into itself; the dust goes on lifting up out of it.",
     "on the lawn looking over the paling, an 85mm lens. The light is red firelight from behind the "
     "tower at the CENTRE, so the tower reads black against it and the dust reads hot red",
     GEO_LAWN, "spike", "The tower of the little church beside it slid down into ruin."),

    ("lawn", "insert", [], 0.55, "tilt_down",
     "Insert down at a flower bed under a study window with a heap of broken red chimney fragments "
     "lying fresh on the turned earth among the crushed stocks, more pieces still lying along the "
     "roof tiles above, and red firelight coming across all of it from below the lawn.",
     "The camera tilts down from the broken tiles to the flower bed already in the picture until the "
     "heap of red fragments is in the middle of the frame, travelling a forearm; dust goes on "
     "sifting down off the brickwork onto the earth; a last fragment goes on rocking where it fell.",
     "at the flower bed looking down, a 50mm lens. The light is low red firelight from the CENTRE "
     "LEFT; the broken brick reads hot red and the turned earth reads dark",
     GEO_LAWN, "spike", "A piece of our chimney came down on the flower bed."),

    ("lawn", "medium_close", ["unnamed_first_person_narrator", "narrators_wife"], 0.6, "push_in",
     "Medium close on " + NARRATOR + " and " + WIFE + " together on their own lawn in the red "
     "evening light, his hand closed hard round her upper arm and her shoulder already turning "
     "under it, both their faces in the picture and the smoke black behind their heads.",
     "The camera pushes in toward the two of them with small amplitude until both faces fill the "
     "middle of the picture, travelling a forearm; the narrator takes his wife by the arm and "
     "draws her round toward the road as he speaks; she goes on turning her shoulder under his "
     "hand and brings her foot round after it.",
     "on the lawn level with their eyes, three paces from them, an 85mm lens. The red firelight "
     "comes from the CENTRE LEFT and rakes across both their faces; the smoke behind them reads "
     "black",
     GEO_LAWN + " Their heads are a third of the frame's height.",
     "turn", "I gripped my wife's arm and ran her out into the road."),

    ("lawn", "medium_close", ["narrators_wife"], 0.7, "push_in",
     "Medium close on " + WIFE + " standing on the gravel drive in the red evening light with her "
     "apron still on and her hands held together in front of her, her face turned downhill and her "
     "pompadour loosened at the temples, the white gate behind her.",
     "The camera pushes in toward her with small amplitude until her head and shoulders fill the "
     "middle of the picture, travelling a forearm; she goes on looking downhill and her hands "
     "go on gripping each other; she goes on turning her head further downhill as she speaks.",
     "on the drive level with her eyes, three paces from her, an 85mm lens. The red firelight comes "
     "from the CENTRE LEFT; her lilac-grey dress reads warm and the gate behind her reads pale",
     GEO_LAWN + " Her head is a third of the frame's height.", "reaction", "But where are we to go? said my wife in terror."),

    ("lawn", "wide", [], 0.8, "pan_to",
     "Wide down the hill from the gate at a bevy of hussars in dark blue riding under the brick "
     "railway bridge below and out along the road, two of them already dismounted and running from "
     "house to house, and the sun standing blood red in the smoke above the trees.",
     "The camera pans to the left along the road until the railway bridge already in the picture is "
     "at the centre, travelling one short stride; the riders go on coming through under the arch at "
     "a canter; the two on foot go on running up to the doors.",
     "at the gate looking downhill, a 35mm lens. The sun stands blood red in the smoke at the TOP "
     "CENTRE and throws a lurid light on everything; the road reads red-brown and the smoke reads "
     "black",
     GEO_LAWN, "friction", "The sun shone blood red through the smoke, on everything."),

    # ---- inn: a man who does not know yet -----------------------------------
    ("inn", "medium", ["unnamed_landlord"], 0.3, "push_in",
     "Medium on " + LANDLORD + " behind the scrubbed counter of his bar under a hanging oil lamp "
     "with both hands spread flat on the wood, the brass beer-engine handles standing up beside him "
     "and the shelves of bottles and pewter behind, his weight settled back on his heels.",
     "The camera pushes in across the counter toward him with small amplitude until his head and "
     "shoulders fill the middle of the picture, travelling one short stride; he goes on speaking and "
     "lifts one hand off the wood to turn it palm up; his moustache goes on moving as he talks.",
     "at the counter level with his chest, four paces from him, a 50mm lens. The oil lamp hangs at "
     "the TOP CENTRE and lights the counter and his face from above; the corners of the room read "
     "brown and dark",
     GEO_INN, "setup", "I must have a pound, said the landlord, and I've no one to drive it."),

    ("inn", "medium", ["unnamed_first_person_narrator"], 0.5, "track_lateral",
     "Medium on " + NARRATOR + " standing at the counter in the lamplight speaking past the shoulder "
     "of another man who stands with his back to the camera, his hat off and held against his chest "
     "and his face wet with the heat, the bottles on the shelves behind them.",
     "The camera tracks sideways to the right along the counter, a truck with small amplitude, until "
     "the brass handles already in the picture are at the centre, travelling one short stride; he "
     "goes on speaking across the other man's shoulder; his hat goes on being turned round and round "
     "against his chest.",
     "at the counter level with his chest, four paces from him, a 50mm lens. The oil lamp hangs at "
     "the TOP CENTRE; his grey tweed reads warm under it and the man in front of him reads dark",
     GEO_INN, "friction", "I'll give you two, said I, over the stranger's shoulder."),

    # ---- lawn again: what a fight with them looks like ----------------------
    ("lawn", "wide", [], 0.9, "crane_up",
     "Wide from the road at a dog cart standing at a white gate in the red evening with a horse in "
     "the shafts and two women already up in it, a bundle tied in a tablecloth and a corded box on "
     "the tail of it, and the whole crest of the hill behind the house going up in thick streamers "
     "of black smoke shot through with threads of red fire.",
     "The camera rises from the road with small amplitude until the cart at the gate and the "
     "streaming smoke over the crest behind it are both inside the picture, travelling one short "
     "stride; the horse goes on shifting in the shafts; the streamers of smoke go on driving up off "
     "the crest.",
     "in the road at a standing man's eye, a 35mm lens. The light is red firelight from the CENTRE "
     "and a red sun in the smoke above; the cart reads black against it and the smoke reads black",
     GEO_LAWN, "answer", "The beeches below the house were burning and the palings glowed red."),

    ("lawn", "close", ["unnamed_hussar"], 0.95, "pan_to",
     "Close on " + HUSSAR + " stopped in the road in the red evening with his head turned back over "
     "his shoulder and his mouth open, shouting, the soot black across one cheek, and a whirl of "
     "black smoke already driving across the road behind him.",
     "The camera pans to the right along the road until his face already in the picture is at the "
     "centre, travelling a forearm; he goes on shouting back over his shoulder as he moves "
     "off; the whirl of black smoke goes on driving across behind him and takes him into it.",
     "in the road level with his eyes, three paces from him, an 85mm lens. The red firelight comes "
     "from the CENTRE LEFT and stands on one side of his face; the smoke behind him reads black",
     GEO_LAWN + " His head is half the frame's height.", "button", "He bawled something about a thing like a dish cover, and ran on."),
]

MOVES = {i: s[4] for i, s in enumerate(S)}

# Beats and codas are COMPUTED, not typed -- `scratchpad/fit_beats.py` gives
# each shot the largest beat and coda that keep its line, its hold and the
# builder's half-second handle inside the 8 s take.
# MEASURED 2026-09-22 on ep08 T16: a coda is the room a move has to finish in.
# Cutting one to 0.4 s to close a gap in the CUT froze the take at 51 %, and a
# fresh seed froze it at 75 %. No moving shot here holds under 0.8 s.
BEATS = {0: (0.9, 1.0), 1: (0.8, 0.9), 2: (0.8, 0.9), 3: (0.9, 1.0),
         4: (0.9, 1.0), 5: (0.9, 1.0), 6: (0.8, 0.9), 7: (0.9, 1.0),
         8: (0.9, 1.0), 9: (0.9, 1.0), 10: (0.8, 0.9), 11: (0.9, 1.0),
         12: (0.8, 0.9), 13: (0.9, 1.0), 14: (0.9, 1.0), 15: (0.8, 0.9),
         16: (1.5, 2.0), 17: (0.9, 1.0), 18: (0.9, 1.0), 19: (0.8, 0.9),
         20: (0.8, 0.9), 21: (1.2, 1.2), 22: (1.0, 1.5)}

TURNS = {16: "a man who has been winning the war in his head -> a man getting his wife "
             "out of the house",
         21: "his own hill as a place he lives -> his own hill as the thing he is running from"}

LINES = [
    ("narration", "unnamed_first_person_narrator",
     "Saturday I remember as a day of suspense, hot and close and still.", 0),
    ("narration", "unnamed_first_person_narrator",
     "The milkman said they were surrounded in the night, and that guns were coming up.", 1),
    ("narration", "unnamed_first_person_narrator",
     "A pity they are so unapproachable, said my neighbour; we might learn something.", 2),
    ("narration", "unnamed_first_person_narrator",
     "A second had come down by the golf links, and the woods still burned.", 3),
    ("narration", "unnamed_first_person_narrator",
     "After breakfast I walked down, and got no further than the bridge.", 4),
    ("dialogue", "snippy",
     "What's cover against this heat? Sticks to cook yer!", 5),
    ("narration", "unnamed_first_person_narrator",
     "Nobody was allowed over the canal. None of these men had seen a Martian.", 6),
    ("narration", "unnamed_first_person_narrator",
     "I told them what I had seen, and they fell to arguing.", 7),
    ("dialogue", "snippy",
     "Octopuses. Talk about fishers of men. Fighters of fish it is this time.", 8),
    ("narration", "unnamed_first_person_narrator",
     "All afternoon they showed not an inch of themselves.", 9),
    ("narration", "unnamed_first_person_narrator",
     "We signalled with a flag on a pole. They took no notice.", 10),
    ("narration", "unnamed_first_person_narrator",
     "All that armament excited me. They seemed very helpless down there.", 11),
    ("narration", "unnamed_first_person_narrator",
     "At six we sat at tea on the lawn, talking about the battle coming.", 12),
    ("narration", "unnamed_first_person_narrator",
     "A muffled detonation, a gust of firing, and a crash that shook the ground.", 13),
    ("narration", "unnamed_first_person_narrator",
     "The college was down. Our own crest was in range now.", 14),
    ("dialogue", "unnamed_first_person_narrator",
     "We can't possibly stay here.", 16),
    ("dialogue", "narrators_wife",
     "But where are we to go?", 17),
    ("narration", "unnamed_first_person_narrator",
     "Leatherhead, I shouted: her cousins' town, twelve miles off and out of this.", 18),
    ("narration", "unnamed_first_person_narrator",
     "The landlord wanted a pound for his horse and cart.", 19),
    ("narration", "unnamed_first_person_narrator",
     "I gave him two, and promised to bring it back by midnight.", 20),
    ("narration", "unnamed_first_person_narrator",
     "I packed our plate in a tablecloth. The palings glowed red.", 21),
    ("dialogue", "unnamed_hussar",
     "Crawling out in a thing like a dish cover!", 22),
]

BEDS = [{"from_shot": 0, "tone": "plain"}, {"from_shot": 4, "tone": "uneasy"},
        {"from_shot": 9, "tone": "plain"}, {"from_shot": 12, "tone": "uneasy"},
        {"from_shot": 13, "tone": "grave"}, {"from_shot": 19, "tone": "plain"},
        {"from_shot": 21, "tone": "grave"}]

PATHS = {
    0: 0.1, 1: 0.4, 2: 0.6, 3: 0.8,                       # garden
    4: 0.1, 5: 0.35, 6: 0.5, 7: 0.7, 8: 0.85,             # bridge
    9: 0.15, 10: 0.4, 11: 0.65,                           # pit
    12: 0.9, 13: 0.35, 14: 0.45, 15: 0.55, 16: 0.6,       # lawn
    17: 0.7, 18: 0.8,
    19: 0.3, 20: 0.5,                                     # inn
    21: 0.9, 22: 0.95,                                    # lawn again
}


SECTIONS = {
    0: "hook",
    1: "setup", 2: "setup", 3: "setup",
    4: "setup", 5: "friction", 6: "friction", 7: "friction", 8: "reaction",
    9: "setup", 10: "friction", 11: "reaction",
    12: "setup", 13: "spike", 14: "spike", 15: "spike",
    16: "turn", 17: "reaction", 18: "friction",
    19: "setup", 20: "friction",
    21: "answer",
    22: "button",
}


def build() -> dict:
    shots = []
    for i, (setup, size, faces, path, move, frame, motion, camera, at_rest, section, why) in enumerate(S):
        beat, coda = BEATS.get(i, (0.8, 0.9))
        shots.append(dict(index=i, section=SECTIONS.get(i, section), setup=setup, size=size,
                          faces=list(faces), view="",
                          path=PATHS.get(i, path), frame=frame, motion=motion, camera=camera,
                          at_rest=at_rest, end="", changed="", beat_s=beat, coda_s=coda,
                          turn=TURNS.get(i, ""), why=why, cuts=[]))
    lines = [dict(index=k, kind=kind, speaker=who, text=text, shot=shot)
             for k, (kind, who, text, shot) in enumerate(LINES)]
    return dict(number=9, title="The Fighting Begins",
                question="What did he think a fight with them would look like?",
                aspect="1:1", where=WHERE, light=LIGHT, look=LOOK,
                protagonist="unnamed_first_person_narrator", answer="shot 21",
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
    sizes = {z: [s["size"] for s in doc["shots"]].count(z)
             for z in {s["size"] for s in doc["shots"]}}
    print(f"{len(doc['shots'])} shots, {len(doc['lines'])} lines, {words} words; "
          f"dialogue {said / words:.1%}; silent shots {silent}")
    print(f"measured projection at 2.62 w/s: "
          f"{words / 2.62 + sum(s['beat_s'] + s['coda_s'] + 0.5 for s in doc['shots']):.0f}s")
    print(f"sizes: {sizes}")
    print(f"moves: {counts}")
    print(OUT)
