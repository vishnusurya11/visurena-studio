"""A climb that moves no row stops (Jekyll ep01 Kawajiri, 2026-10-18): climb 1's rungs 2 and 3 returned
the rung-1 rows, 10 of 28 minutes bought nothing.  Rows are keyed by (gate id, count), no shot numbers.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import llm, plan_ladder  # noqa: E402
from studio.ladder import Rung  # noqa: E402


class FakeWriter:
    """Records every call; a call that writes nothing is a money refusal, which the desk survives."""

    def __init__(self):
        self.calls = []

    def write(self, brief, refusals, previous=None, **kw):
        self.calls.append({"refusals": refusals, "previous": previous, "kw": kw})
        raise llm.OverBudget("fake writer: no draft")


class Ctx:
    def __init__(self, home: Path):
        self.home, self.book_dir, self.number, self.said = home, home, 1, []

    def log(self, msg, **kw):
        self.said.append(msg)


def desk_with_plan(home: Path):
    writer = FakeWriter()
    desk = plan_ladder.Desk(Ctx(home), home / "plan.json", writer=writer)
    desk.brief = {"x": 1}
    (home / "plan.json").write_text(json.dumps({"draft": 1}), encoding="utf-8")
    return desk, writer


def rows(*gates: str):
    lines = ["GRAMMAR      : %d" % len(gates)] + [f"    {g} shot {i}: a row" for i, g in enumerate(gates)]
    return plan_ladder.battery_verdict(lines + ["VERDICT      : REFUSED"])


IMPROVE = Rung(plan_ladder.IMPROVE, 1.0)
TIER = Rung(plan_ladder.MODEL_TIER, 1.0)


def test_climb_one_twenty_to_six_to_five_still_runs_rung_three(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    twenty = rows(*(["G-PUSH"] * 5 + ["G-TWO"] + ["G-REACT"] * 2 + ["G-SHOTS", "G-CROWD", "G-CROWD", "G-PRESENT"]
                    + ["G-ORDER"] * 2 + ["G-AIM"] * 3 + ["G-LAID"] * 3))
    six = rows("G-TWO", "G-PRESENT", "G-AIM", "G-AIM", "G-AIM", "G-LAID")
    five = rows("G-TWO", "G-PRESENT", "G-AIM", "G-AIM", "G-CROWD")        # the writer moved a row
    desk.take(IMPROVE, 0, twenty)
    desk.take(IMPROVE, 1, six)
    desk.take(TIER, 0, five)
    assert len(writer.calls) == 3 and not desk.stuck


def test_climb_two_one_g_two_twice_writes_nothing_more(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-TWO"))
    desk.take(IMPROVE, 1, rows("G-TWO"))
    desk.take(TIER, 0, rows("G-TWO"))
    assert len(writer.calls) == 1 and desk.stuck
    assert desk.rungs_done == 3
    assert any("moved no row" in line for line in desk.ctx.said)


def test_a_count_that_fell_by_two_is_progress_even_on_the_same_ids(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-AIM", "G-AIM", "G-AIM"))
    desk.take(IMPROVE, 1, rows("G-AIM"))
    assert len(writer.calls) == 2 and not desk.stuck


def test_a_new_id_is_progress_or_regression_never_stuck(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-AIM"))
    desk.take(IMPROVE, 1, rows("G-LAID"))
    assert len(writer.calls) == 2 and not desk.stuck


def test_row_keys_carry_no_shot_numbers():
    assert plan_ladder.row_keys(rows("G-AIM", "G-AIM", "G-TWO")) == {"G-AIM": 2, "G-TWO": 1}
