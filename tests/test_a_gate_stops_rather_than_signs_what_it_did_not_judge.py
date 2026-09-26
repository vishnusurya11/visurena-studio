"""A gate that did not judge never signs (root cause 2026-09-26, A2 and A3).

ep12's panel gate signed `keep_best` at attempt 0 because the run's budget was
already 2993 s overdrawn, and its note was one measure repeating "landmark at
shot_00" 531 times.  Neither is a verdict: an unaffordable rung DEFERS the run
(resumable, nothing signed), a judge that repeats one fault past a handful is a
broken measure, and a pass is written down so the publish lock can tell a gate
that passed from one that never ran."""
from __future__ import annotations

import pytest

from studio import judged_gate
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung
from studio.run_budget import EPISODE_SHARES, Budget


class Ctx:
    def __init__(self, tmp_path, clock=lambda: 0.0):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.budget = Budget(18000, EPISODE_SHARES, clock=clock)
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


AUTO = Policy(state="auto", judge="panel_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best")
LADDER = Ladder([Rung("seed", 300)], "keep_best")


def verdict(passed, faults=()):
    return Verdict(judge="panel_eye", version="1", passed=passed, confidence=1.0, reads=3,
                   faults=list(faults))


def clear(ctx, judge, signed):
    return judged_gate.clear(ctx, "EYE_PANELS", judge=judge,
                             sign=lambda v: signed.append(v) or ctx.book_dir,
                             ladder=judged_gate.Rungs(LADDER, take=lambda *a: None),
                             terminal=lambda v: v, policy=AUTO)


def test_an_unaffordable_rung_defers_and_signs_nothing(tmp_path):
    ctx, signed = Ctx(tmp_path, clock=lambda: 17_990.0), []
    ctx.budget.t0 = 0.0
    with pytest.raises(SystemExit, match="DEFERRED"):
        clear(ctx, lambda: verdict(False, [Fault(kind="lag", where="T07")]), signed)
    assert signed == []
    assert [(l.gate, l.action, l.terminal) for l in ctx.learned] == [("budget", "defer", False)]


def test_a_pass_is_learned(tmp_path):
    ctx, signed = Ctx(tmp_path), []
    clear(ctx, lambda: verdict(True), signed)
    assert [(l.gate, l.action, l.terminal) for l in ctx.learned] == [("EYE_PANELS", "pass", False)]


def test_one_fault_repeated_past_the_cap_is_an_invalid_verdict(tmp_path):
    ctx, signed = Ctx(tmp_path), []
    same = [Fault(kind="landmark", where="shot_00")] * (judged_gate.MAX_REPEAT + 1)
    with pytest.raises(SystemExit, match="INVALID VERDICT"):
        clear(ctx, lambda: verdict(False, same), signed)
    assert signed == []


def test_repeats_under_the_cap_are_a_verdict(tmp_path):
    faults = [Fault(kind="lag", where="T07")] * judged_gate.MAX_REPEAT
    assert judged_gate.repeated(verdict(False, faults)) is None
