"""G-PLACE and G-LOOK: gates whose cure is code (verdict S).  A place owns its
member ids; a lookalike new id is the member; a member with nothing drawn
whose room a sibling has drawn moves there (WotW ep26's third dining room);
a framing or state view of a recurring place is its master, the state kept
for step 03 (ep27's fresh 'reverse'); a view naming a new subject is a new
side, drawn once."""
from __future__ import annotations

import json
from types import SimpleNamespace

from studio import continuity_place as cp
from studio.continuity_spec import CharacterLooks, LookBook
from tests import continuity_fixtures as fx

ROWS = [{"id": "narrators_home", "name": "the narrator's house at Maybury", "aliases": ["the house"]},
        {"id": "narrators_dining_room", "name": "the dining room of the narrator's house",
         "aliases": ["the dining room, the house"]},
        {"id": "narrators_study", "name": "the narrator's study", "aliases": ["the study, the house"]},
        {"id": "horsell_common", "name": "Horsell Common", "aliases": []}]


def book(tmp_path):
    root = tmp_path / "book"
    for loc in ("narrators_home", "narrators_study"):
        (root / "refs" / "locations" / loc).mkdir(parents=True)
        (root / "refs" / "locations" / loc / "wide_establishing.png").write_bytes(fx.PNG)
    (root / "refs" / "locations" / "narrators_home" / "dining_room_unlit_night.png").write_bytes(fx.PNG)
    (root / "analysis" / "locations").mkdir(parents=True)
    for row in ROWS:
        (root / "analysis" / "locations" / f"{row['id']}.json").write_text(json.dumps(row), encoding="utf-8")
    earlier = {"setups": {"a": {"location": "narrators_study", "view": ""}}}
    (root / "episodes" / "ep01").mkdir(parents=True)
    (root / "episodes" / "ep01" / "plan.json").write_text(json.dumps(earlier), encoding="utf-8")
    return root


def test_rooms_join_the_house_they_name():
    groups = cp.groups(ROWS)
    assert sorted(groups["narrators_home"]) == ["narrators_dining_room", "narrators_home", "narrators_study"]
    assert groups["horsell_common"] == ["horsell_common"]


def test_a_lookalike_new_id_is_the_member(tmp_path):
    b = book(tmp_path)
    assert cp.place_fix(b, cp.groups(ROWS), ROWS, "narrator_study", "") == ("narrators_study", "")


def test_a_room_a_sibling_has_drawn_is_reused_not_drawn(tmp_path):
    b = book(tmp_path)
    assert cp.place_fix(b, cp.groups(ROWS), ROWS, "narrators_dining_room", "medium_french_window") == \
        ("narrators_home", "dining_room_unlit_night")


def test_a_framing_view_of_a_recurring_place_is_its_master_with_its_state(tmp_path):
    b = book(tmp_path)
    doc = {"number": 2, "setups": {"rev": {"location": "narrators_study", "view": "reverse"},
                                   "late": {"location": "narrators_study", "view": "wide_ruined_dusk"}}}
    cured = cp.cure_places(doc, b, cp.groups(ROWS), ROWS)["setups"]
    assert cured["rev"]["view"] == "" and cured["rev"]["place_state"] == ""
    assert cured["late"]["view"] == "" and cured["late"]["place_state"] == "ruined dusk"


def test_a_new_side_and_a_first_visit_are_left_to_be_drawn_once(tmp_path):
    b, places = book(tmp_path), cp.groups(ROWS)
    assert cp.place_fix(b, places, ROWS, "narrators_study", "medium_writing_table") == \
        ("narrators_study", "medium_writing_table")
    assert cp.place_fix(b, places, ROWS, "narrators_study", "reverse", recurring=False) == \
        ("narrators_study", "reverse")


def test_the_gate_names_the_rewrite(tmp_path):
    b = book(tmp_path)
    ep = SimpleNamespace(number=2, setups={"rev": SimpleNamespace(location="narrators_study", view="reverse")})
    got = cp.place_gate(b, ep, cp.groups(ROWS), ROWS)
    assert got and "G-PLACE setup rev" in got[0] and "narrators_study/wide_establishing" in got[0]
    assert cp.history(b, 2, ["narrators_study"]) == ["ep01 narrators_study/wide_establishing"]


def test_g_look_drops_a_pick_the_chapter_does_not_allow():
    table = LookBook(characters={"narrator": CharacterLooks.model_validate(fx.CARD)})
    setup = SimpleNamespace(looks=[SimpleNamespace(who="narrator", look="borrowed")])
    ep = SimpleNamespace(number=24, setups={"s": setup})
    assert cp.look_gate(table, ep) and cp.look_gate(None, ep) == []
    doc = {"setups": {"s": {"looks": [{"who": "narrator", "look": "borrowed"},
                                      {"who": "narrator", "look": "ragged"}]}}}
    assert cp.cure_looks(doc, table, 24)["setups"]["s"]["looks"] == [{"who": "narrator", "look": "ragged"}]
