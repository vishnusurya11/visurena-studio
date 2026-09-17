"""An ALTERNATE is a real picture or nothing.

MEASURED on episode 9 (`docs/analysis/ep08_ep09_why_worse.md`, cause 4): 14 of
44 panels were template alternates that (a) said "the same moment as panel k"
on a sheet whose ORDER block says every panel is later than the last, (b) were
listed as route panels that must advance, (c) inherited the base panel's
`size`, `path`, `at_rest` and ladder clause -- "FULL SHOT ... a tight insert of
hands", (d) carried "camera The camera stands" in all 14, and (e) named no
object.  The drawer drew the same wide three times per sheet.

So an alternate chooses its own size, writes its own at-rest line, names the
base panel's people AND its hero object, sits outside the ORDER and the route,
and the free gate refuses any sheet that still says "same moment".
"""
import json
from pathlib import Path

import pytest

from studio import episode_seq_board as sq, sheet_gate as gate
from studio.affirm import negations
from studio.episode_spec import Episode, Setup

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"

PARLOUR = Setup(described="The parlour of a log villa by lamplight.",
                cast=["john_ferrier", "lucy_ferrier", "jefferson_hope"], landmark="the stone hearth",
                landmark_at="start", route="from the hearth across the rag rug to the open window",
                crowd="Moths cross the lamp glass in ones and twos and the low fire settles in the hearth.")

UTAH = {
    "john_ferrier": {"physical": "A tall spare man in his middle fifties, iron-grey hair cut square to the collar.",
                     "wardrobe": {"indoor": "is bare-headed in a dark waistcoat over a collarless white linen shirt",
                                  "outdoor": "wears a wide-brimmed brown felt hat and a fawn homespun coat"}},
    "lucy_ferrier": {"physical": "A young woman of about twenty, long chestnut hair worn loose.",
                     "wardrobe": {"indoor": "is bare-headed in a plain grey-blue cotton house dress",
                                  "outdoor": "wears a cream straw hat and a slate-blue divided riding skirt"}},
    "jefferson_hope": {"physical": "A tall young man in his middle twenties with a full black beard.",
                       "wardrobe": {"indoor": "is in a long brownish driving coat buttoned to the chest",
                                    "outdoor": "wears a broad brown felt sombrero and a fringed buckskin shirt"}},
}


def seg(shot, size="full", path=0.3, faces=("lucy_ferrier", "jefferson_hope"),
        frame="Full shot across the pine table: Lucy at the open window, the lamp between them, the hearth behind.",
        camera="at the table end level with a seated man's eye, a 50mm lens",
        at_rest="Lucy stands in the RIGHT third with the pale window behind her."):
    return {"shot": shot, "sub": 0, "size": size, "path": path, "faces": list(faces), "frame": frame,
            "camera": camera, "at_rest": at_rest, "motion": "The camera holds; her hand lifts a finger's breadth.",
            "end_frame": "", "changed": "", "crowd": ""}


def rebuilt(plan: str, name: str, physical: dict) -> list[str]:
    """Every sheet prompt of one setup, built by today's code from the plan on disk."""
    episode = Episode.model_validate_json((FIXTURES / plan).read_text(encoding="utf-8"))
    setup, segs = episode.setups[name], sq.segments(episode.shots, name)
    return [sq.prompt(group, setup, physical, previous=False, first=(k == 0), geography=route,
                      aspect=episode.aspect)
            for k, (group, route, _grid) in enumerate(sq.sheets(segs, setup, episode.aspect))]


def fixture_prompts(name: str) -> dict[str, str]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# ---- the alternate's own picture -------------------------------------------

def test_the_insert_alternate_is_an_insert_and_the_wide_one_is_wide():
    base = seg(0, size="full")
    kinds = {sq.alt_panel(base, k)["size"] for k in range(1, 5)}
    assert kinds == {"full", "wide", "insert"}
    assert sq.alt_panel(base, 3)["size"] == "insert"   # the third template is the tight insert
    assert sq.alt_panel(base, 2)["size"] == "wide"     # the second is the establishing wide


def test_the_reverse_and_low_alternates_keep_the_base_size():
    base = seg(0, size="medium_close")
    assert sq.alt_panel(base, 1)["size"] == "medium_close"
    assert sq.alt_panel(base, 4)["size"] == "medium_close"


def test_an_alternate_writes_its_own_at_rest_line():
    base = seg(0)
    for k in range(1, 5):
        alt = sq.alt_panel(base, k)
        assert alt["at_rest"] and alt["at_rest"] != base["at_rest"]
        assert len(alt["at_rest"].split(". ")) == 1  # one line


def test_an_alternate_names_the_base_panels_people_and_its_hero_object():
    alt = sq.alt_panel(seg(0), 1)
    assert "Lucy Ferrier" in alt["frame"] and "Jefferson Hope" in alt["frame"]
    assert "the pine table" in alt["frame"]


def test_the_hero_object_is_the_first_concrete_noun_of_the_frame():
    assert sq.hero("Wide of the Ferrier parlour by lamplight: squared log walls.") == "the Ferrier parlour"
    assert sq.hero("Medium two-shot across the pine table: Hope leaning in.") == "the pine table"
    assert sq.hero("Close on Lucy at the open window in the house dress.") == "the open window"
    assert sq.hero("Medium close on Hope in the lamplight, the log wall behind him.") == "the log wall"
    assert sq.hero("Medium close on Hope, the dark fierce face turned, the lamp above.") == "the lamp"


def test_a_panel_with_no_face_is_of_its_own_two_nouns():
    """An empty wide has no people to stand in `{who}`: its first noun does,
    and the hero object is its second."""
    empty = seg(0, faces=(), frame="Wide of the Ferrier parlour by lamplight: the stone hearth on the left.")
    alt = sq.alt_panel(empty, 1)
    assert "the Ferrier parlour and the stone hearth" in alt["frame"]
    assert "the people" not in alt["frame"] and "hands of the" not in sq.alt_panel(empty, 3)["frame"]


def test_no_alternate_says_the_same_moment_or_doubles_the_camera_word():
    text = sq.prompt(sq.with_ends([seg(0), seg(1)], spare=4), PARLOUR, UTAH, previous=False,
                     first=True, geography=True)
    assert "same moment" not in text and "moment of panel" not in text
    assert "camera The camera" not in text
    assert negations(text) == []


def test_an_alternate_is_labelled_as_another_angle_of_its_panel():
    text = sq.prompt(sq.with_ends([seg(0)], spare=1), PARLOUR, UTAH, previous=False, first=True,
                     geography=True)
    assert "ALTERNATE ANGLE OF PANEL 1" in text


# ---- outside the ORDER and the route ---------------------------------------

def test_an_alternate_is_never_a_route_panel():
    alt = sq.alt_panel(seg(0, size="wide", path=0.3), 1)
    assert alt["path"] == 0.3 and not sq.on_route(alt, PARLOUR)
    panels, route, _grid = sq.sheets([seg(0, size="wide"), seg(1, size="full", path=0.6)], PARLOUR, "1:1")[0]
    assert [k for k, p in enumerate(panels, start=1) if p.get("alt")] == [3, 4]
    assert route == [1, 2]


def test_the_order_block_puts_alternates_outside_the_sequence():
    text = sq.prompt(sq.with_ends([seg(0), seg(1)], spare=2), PARLOUR, UTAH, previous=False,
                     first=True, geography=True)
    order = text.split("ORDER\n")[1].split("\n\n")[0]
    assert "panel 2 happens last" in order
    assert "Panels 3 and 4 are alternates" in order and "outside the sequence" in order
    assert "Panels 1 and 2 look along that path" in order


def test_an_alternate_carries_no_ladder_clause():
    text = sq.prompt(sq.with_ends([seg(0, size="wide")], spare=1), PARLOUR, UTAH, previous=False,
                     first=True, geography=True)
    panels = text.split("PANELS\n")[1].split("\n\nSTYLE")[0].split("\n\n")
    assert "height of" in panels[0] or "fills the frame" in panels[0]
    assert "height of" not in panels[1] and "fills the frame" not in panels[1]


# ---- the gate ---------------------------------------------------------------

def test_the_gate_refuses_a_panel_that_says_the_same_moment():
    prompt = ("PANELS\nPanel 1 - WIDE. In frame: the room.\n\n"
              "Panel 2 - WIDE. In frame: Reverse angle on the place, the same moment as panel 1.")
    found = gate.alternates([], prompt)
    assert [(f.check, f.hard) for f in found] == [("ALTERNATE", True)]
    assert found[0].panel == "panel 2"


def test_the_gate_refuses_an_alternate_that_overlaps_its_base():
    base = seg(0, size="wide")
    twin = dict(base, shot=0, alt=True, of=1)
    found = gate.alternates([base, twin], "")
    assert [(f.check, f.hard) for f in found] == [("ALTERNATE", True)]
    assert "overlap" in found[0].note


def test_the_gate_refuses_an_alternate_listed_as_a_route_panel():
    prompt = ("ORDER\nPanels 1, 2 and 3 look along that path.\n\nPANELS\nPanel 1 - WIDE. x\n\n"
              "Panel 2 - WIDE. y\n\nPanel 3 - WIDE, ALTERNATE ANGLE OF PANEL 1, camera well back. z")
    found = gate.alternates([], prompt)
    assert [(f.panel, f.hard) for f in found] == [("panel 3", True)]
    assert "route" in found[0].note


def test_a_good_alternate_passes_the_gate():
    panels = sq.with_ends([seg(0), seg(1, frame="Close on Hope's beard in the lamp, the log wall behind.",
                                        size="close", path=None)], spare=2)
    text = sq.prompt(panels, PARLOUR, UTAH, previous=False, first=True, geography=True)
    assert gate.alternates(panels, text) == []


def test_the_whole_sheet_runs_the_alternate_check():
    prompt = ("SHEET\nA film storyboard sheet: a 3 by 1 grid of 3 equal square 1:1 panels\n\n"
              "PANELS\nPanel 1 - WIDE. x\n\nPanel 2 - WIDE. the same moment as panel 1\n\nPanel 3 - WIDE. z")
    found = gate.sheet_findings([seg(0), seg(1), seg(2)], PARLOUR, prompt, (3, 1, (1536, 512)))
    assert "ALTERNATE" in {f.check for f in found}


# ---- the fixtures ------------------------------------------------------------

def test_the_ep09_sheets_as_drawn_fail_on_all_fourteen_alternates():
    found = [f for text in fixture_prompts("ep09_sheet_prompts.json").values()
             for f in gate.alternates([], text)]
    assert len(found) == 14 and all(f.hard for f in found)


@pytest.mark.parametrize("name", ["ep05_sheet_prompts.json", "ep07_sheet_prompts.json"])
def test_the_sheets_the_owner_liked_pass(name):
    for text in fixture_prompts(name).values():
        assert gate.alternates([], text) == []


def test_ep09_rebuilt_today_passes_the_alternate_check_on_every_sheet():
    episode = Episode.model_validate_json((FIXTURES / "ep09_plan.json").read_text(encoding="utf-8"))
    for name, setup in episode.setups.items():
        segs = sq.segments(episode.shots, name)
        for k, (group, route, _grid) in enumerate(sq.sheets(segs, setup, episode.aspect)):
            text = sq.prompt(group, setup, UTAH, previous=False, first=(k == 0), geography=route,
                             aspect=episode.aspect)
            assert gate.alternates(group, text) == [], name
            assert "same moment" not in text and "camera The camera" not in text
