"""A grid panel draws the setup's crowd only when its shot declares extras > 0.

Jekyll Kawajiri ep01 (2026-10-18): `crowd_clause` and `crowd_block` printed the night door's ring of
townsfolk on every wide panel, so the storyboard drew strangers into extras-0 shots and H3 walked
them in.  Fixture: tests/fixtures/ep01_replay/P03/plan.json (copy of ep01's plan.json)."""
import json
from pathlib import Path

from studio.episode_seq_board import cell, crowd_block, crowd_clause
from studio.episode_spec import Setup, Shot

PLAN = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "plan.json").read_text("utf-8"))
DOOR = Setup(**{k: v for k, v in PLAN["setups"]["night_door"].items() if k in Setup.model_fields})


def seg(extras: int, size: str = "wide", crowd: str = "") -> dict:
    return {"size": size, "crowd": crowd, "extras": extras, "frame": "the door"}


def test_an_extras_0_panel_gets_no_setup_crowd():
    assert crowd_clause(seg(0), DOOR) == ""


def test_a_panel_with_extras_gets_the_setup_crowd():
    assert "townsfolk" in crowd_clause(seg(2), DOOR)


def test_a_panels_own_crowd_needs_no_extras():
    assert "tramp" in crowd_clause(seg(0, crowd="one tramp"), DOOR)


def test_the_sheet_block_is_said_only_when_a_panel_holds_the_crowd():
    assert crowd_block(DOOR, [seg(0), seg(0)]) == ""
    assert "public place" in crowd_block(DOOR, [seg(0), seg(3)])


def test_a_cell_carries_its_shots_extras():
    shot = Shot(**{k: v for k, v in PLAN["shots"][1].items() if k in Shot.model_fields})
    assert cell(shot, 1, 0, None)["extras"] == 2
    assert cell(shot, 1, 1, None, extras=shot.extras)["extras"] == 2


def test_a_crowd_that_is_not_people_needs_no_extras():
    moths = Setup(described="A parlour.", crowd="moths cross the lamp glass")
    assert "moths" in crowd_clause(seg(0), moths)


def test_replay_ep01_crowd_words_survive_only_where_extras_are_declared():
    """R3: the 28 plan shots through the grid's crowd clause, before (no extras key) and after."""
    setups = {n: Setup(**{k: v for k, v in s.items() if k in Setup.model_fields}) for n, s in PLAN["setups"].items()}
    def seg_of(s: dict, keyed: bool) -> dict:
        out = {"size": s["size"], "crowd": s["crowd"], "frame": s["frame"]}
        return out | ({"extras": s["extras"]} if keyed else {})
    before = [s["index"] for s in PLAN["shots"] if crowd_clause(seg_of(s, False), setups[s["setup"]])]
    after = [s["index"] for s in PLAN["shots"] if crowd_clause(seg_of(s, True), setups[s["setup"]])]
    declared = [s["index"] for s in PLAN["shots"] if s["extras"] > 0 or s["crowd"]]
    assert set(after) <= set(declared) and set(after) < set(before)
    assert [i for i in before if i not in after]            # the leaked extras-0 panels are gone


def test_a_mixed_sheet_does_not_promise_people_in_every_panel():
    mixed = crowd_block(DOOR, [seg(0), seg(3)])
    assert "in every panel." not in mixed.split("The people")[0]
    assert "every panel." in crowd_block(DOOR, [seg(2), seg(3)])
    assert crowd_block(DOOR) .startswith("This is a public place")        # no segs given: legacy
