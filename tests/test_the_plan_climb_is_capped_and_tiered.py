"""The plan climb is capped and its faults are tiered (owner 2026-10-18, Jekyll Kawajiri ep01:
"add the number of loops we can do and what parts to focus on").

The step-02 climb ran 45 min on a draft refused only by rows no writer moves.  Now:
- at most three writer rungs and CLIMB_WALL_S (the cap table's 30 min) of wall for the climb; past the wall a rung
  writes nothing and the terminal takes the best draft;
- tier 1 (a line a downstream builder repeats: contract, cast bound, take length, ...) defers and
  re-authors as before; any other line (tier 2: aim, laid, crowd, react -- one writer round each
  rung gave them) keeps the best draft, signed flagged, never a defer-and-re-author;
- tier 3 never refuses: the voice-measured grammar rows (0314238) and the G-VARIETY insert count
  on a grammar plan are advice.
"""
from __future__ import annotations

from studio import plan_gates, plan_ladder
from studio.episode_spec import Episode
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Rung

from tests.test_the_battery_holds_a_grammar_plan_to_the_grammar import canned_plan


def battery(*lines: str) -> Verdict:
    return plan_ladder.battery_verdict(list(lines))


class Desk(plan_ladder.Desk):
    def __init__(self, began: float | None = None, now: float = 0.0):  # noqa: drives take/terminal only
        self.refusals, self.pending, self.drafts, self.judged = [], None, [], {}
        self.agent, self.best, self.brief, self.rungs_done = None, None, {"x": 1}, 0
        self.over_clock, self.battery_terminal, self.ctx = False, plan_ladder.DEFER, object()
        self.began, self._now, self.wrote = began, now, []

    def now(self) -> float:
        return self._now

    def refused_plan(self):
        return {"the": "draft"}

    def remember(self, v):
        pass

    def checkpoint(self):
        pass

    def write(self, refusals, agent=None, previous=None):
        self.wrote.append("improve")


JUDGED_ONLY = ("CELL GATES   : 2", "    G-AIM shot 10: the camera aims at 'lamp'",
               "    G-LAID shot 7: a medium_close of a person lying down", "VERDICT      : REFUSED")
BUILDER = ("CAST BOUND   : ['poole']", "VERDICT      : REFUSED")


def test_a_draft_refused_only_on_judged_rows_is_kept_flagged_never_deferred():
    desk = Desk()
    assert desk.terminal(battery(*JUDGED_ONLY)).terminal == plan_ladder.KEEP_BEST


def test_a_builder_line_still_defers():
    desk = Desk()
    assert desk.terminal(battery(*BUILDER)).terminal == plan_ladder.DEFER


def test_a_rung_inside_the_wall_writes():
    desk = Desk(began=0.0, now=plan_ladder.CLIMB_WALL_S - 1)
    desk.take(Rung(plan_ladder.IMPROVE, 1.0), 0, battery(*JUDGED_ONLY))
    assert desk.wrote == ["improve"] and desk.rungs_done == 1


def test_a_rung_past_the_wall_writes_nothing():
    desk = Desk(began=0.0, now=plan_ladder.CLIMB_WALL_S + 1)
    desk.take(Rung(plan_ladder.IMPROVE, 1.0), 0, battery(*JUDGED_ONLY))
    assert desk.wrote == [] and desk.rungs_done == 1


def test_the_climb_is_three_writer_rungs_and_the_tables_30_minute_wall():
    # 25 min landed first (ad170a3); the owner's approved cap table says 30 min per climb
    assert sum(r.tries for r in plan_ladder.ladder(2).rungs) == 3
    assert plan_ladder.CLIMB_WALL_S == 30 * 60


def test_the_insert_count_is_advice_on_a_grammar_plan():
    plan = {**canned_plan(), "grammar": "anime_tv"}
    for s in plan["shots"]:
        s["size"] = "close" if s["size"] == "insert" else s["size"]
    ep = Episode.model_validate(plan)
    assert plan_gates.insert_faults(ep) == []
    assert any("insert shots" in a for a in plan_gates.insert_advisories(ep))
