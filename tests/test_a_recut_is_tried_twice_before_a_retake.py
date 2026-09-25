"""The master's ladder under judged_gate.clear: a fault on a measured field
takes recut, recut, then one retake of the shot the evidence names (followed
by its recut), and the terminal signs the rubric flagged with an audit row.  A
story-only fault has no rung: it is flagged straight away, at no cost."""
from __future__ import annotations

import json

from studio import audit_rows, judged_gate, master_ladder as ml
from studio.gate_policy import Policy
from studio.judges import master_eye as me
from studio.judges.verdict import Fault, Verdict
from studio.run_budget import EPISODE_SHARES, Budget

AUTO = Policy(state="auto", judge="master_eye@1", decision="2026-09-24-automate-the-taste-gates", terminal="flag")


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep01"
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


def off_board() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="board", where="master",
                                 evidence={"off": {3: 0.1, 5: 0.2}, "share": 0.5, "wall": {"cell": 0.5}}),
                           Fault(kind="faces", where="master", evidence={"under": [3], "wall": 0.25})])


def story_only() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="story", where="master", evidence={"matched": []})])


def climb(tmp_path, verdict: Verdict):
    ctx, taken = Ctx(tmp_path), []
    ladder = ml.rungs(verdict, recut=lambda: taken.append("recut"), retake=lambda shot, v: taken.append(("retake", shot)))
    signed = judged_gate.clear(ctx, "MASTER", judge=ml.once(verdict, lambda: verdict),
                               sign=lambda v: me.write_rubric(ctx.home, "abc12345", v),
                               ladder=ladder, terminal=ml.flag, policy=AUTO)
    return ctx, taken, json.loads(signed.read_text(encoding="utf-8"))


def test_recut_twice_then_one_retake_of_the_named_shot_then_flag(tmp_path):
    ctx, taken, doc = climb(tmp_path, off_board())
    assert taken == ["recut", "recut", ("retake", 3), "recut"]
    assert doc["terminal"] == "flag" and doc["rubric"]["board"]["answer"] == "n"
    assert doc["rubric"]["board"]["flagged_by"] == "judge:master_eye@1"
    actions = [(l.action, l.terminal) for l in ctx.learned]
    assert actions == [("recut", False), ("recut", False), ("retake_shot", False), ("flag", True)]
    rows = audit_rows.load(ctx.book_dir)
    assert len(rows) == 1 and rows[0].gate == "MASTER" and rows[0].terminal == "flag"
    assert rows[0].artefact == "episodes/ep01/review/eye_abc12345.json" and rows[0].sha8 == "abc12345"


def test_a_story_fault_takes_no_rung_and_is_flagged_at_no_cost(tmp_path):
    ctx, taken, doc = climb(tmp_path, story_only())
    assert taken == [] and doc["terminal"] == "flag" and doc["rubric"]["story"]["answer"] == "n"
    assert [(l.action, l.terminal) for l in ctx.learned] == [("flag", True)]
    assert not ml.recuttable(story_only()) and ml.recuttable(off_board())


def test_the_worst_shot_is_the_one_the_measures_name_most():
    assert ml.worst_shot(off_board()) == 3
    assert ml.worst_shot(story_only()) is None


def test_once_serves_the_first_read_then_fresh_ones():
    served = []
    judge = ml.once(story_only(), lambda: served.append(1) or off_board())
    assert judge().faults[0].kind == "story" and served == []
    assert judge().faults[0].kind == "board" and served == [1]
