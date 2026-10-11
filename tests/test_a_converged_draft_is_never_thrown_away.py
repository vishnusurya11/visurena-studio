"""ep15 (2026-10-01, eight plan deferrals): the improve rung converged the
draft to ONE battery fault, then the old fresh_brief rung discarded it and wrote from
nothing (39-57 faults), MODEL_TIER repeated the cycle, and keep_best deferred
a 1-fault draft -- eight times, ~3.5 h, all paid calls.  A rung that would
start over now degrades to one more targeted improve while the draft is
within CONVERGED faults of passing; only a genuinely bad draft is thrown
away.  Since C2_verdict #3 there is no fresh_brief rung at all."""
from __future__ import annotations

from studio import plan_ladder
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Rung


def verdict(n: int) -> Verdict:
    return Verdict(judge="plan", version="1", passed=n == 0, confidence=1.0, reads=1,
                   faults=[Fault(kind="battery", where="plan", note=f"fault {k}") for k in range(n)])


class Desk(plan_ladder.Desk):
    def __init__(self):  # noqa: super().__init__ needs ctx/plan/writer; the test drives take() only
        self.refusals, self.pending, self.drafts, self.judged = [], None, [], {}
        self.agent, self.best, self.brief = None, None, {"x": 1}
        self.wrote = []

    def brief_(self):
        return self.brief

    def escalate(self):
        self.agent = "reasoner"

    def refused_plan(self):
        return {"the": "draft"}

    def remember(self, v):
        pass

    def write(self, refusals, agent=None, previous=None):
        self.wrote.append("improve" if previous is not None else "fresh")


def test_a_near_pass_is_edited_by_the_improve_rung():
    desk = Desk()
    desk.take(Rung(plan_ladder.IMPROVE, 1.0), 0, verdict(1))
    assert desk.wrote == ["improve"]          # the converged draft is edited, never discarded


def test_the_model_tier_rung_also_edits_a_near_pass():
    desk = Desk()
    desk.drafts = [1]                          # would normally skip the write entirely
    desk.take(Rung(plan_ladder.MODEL_TIER, 1.0), 0, verdict(2))
    assert desk.wrote == ["improve"]


def test_converged_is_two_faults():
    assert plan_ladder.CONVERGED == 2
