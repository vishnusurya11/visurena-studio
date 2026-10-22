"""The last plan climb keeps the best draft (owner 2026-10-18) -- but when the CONTRACT refused every
draft, no plan.json was ever written and there is nothing to keep.  The first real rehearsal
(2026-10-21 17:44 PDT, S0a, every writer part canned) reached exactly that: climb 2 of 2 ended
keep_best, Desk.sign hashed a plan.json that did not exist, and the drive died on
`FileNotFoundError ... plan.json`, which the autopilot read as `unclassified`.  A real writer that
fails the contract on all six rounds of both climbs ends the same way.

The stop is the closed SAFETY list's `plan_builder` entry (a CONTRACT line is a builder line), raised
as SystemExit so the drive log carries it and autopilot.classify parks it named.  No test spends:
the writer is a fake that raises what the structured gateway raises."""
from __future__ import annotations

import pytest
from strands.types.exceptions import StructuredOutputException

from scripts.episode import step_02_plan as step02
from studio import autopilot, judged_gate, plan_ladder
from studio.gate_policy import Policy
from studio.run_budget import EPISODE_SHARES, Budget

REFUSED = "CONTRACT : an episode with no line has no button"


class ContractWriter:
    def write(self, brief, refusals, **kw):
        raise StructuredOutputException(f"output did not match schema: Value error, {REFUSED}")


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number = "episode", "ep01", 1
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep01"
        self.home.mkdir(parents=True)
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned, self.said = [], []

    def learn(self, learning):
        self.learned.append(learning)

    def log(self, msg, **kw):
        self.said.append(msg)


AUTO = Policy(state="auto", judge="plan@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best", battery_terminal="defer")


def last_climb(ctx) -> plan_ladder.Desk:
    desk = plan_ladder.Desk(ctx, ctx.home / "plan.json", writer=ContractWriter())
    desk.brief, desk.battery_terminal = {}, plan_ladder.KEEP_BEST
    desk.write(None)
    return desk


def clear(ctx, desk):
    rungs = judged_gate.Rungs(plan_ladder.ladder(2), take=desk.take)
    return judged_gate.clear(ctx, "PLAN", judge=lambda: step02.judge(ctx, desk), sign=desk.sign,
                             ladder=rungs, terminal=desk.terminal, policy=AUTO)


def test_keep_best_with_no_plan_on_disk_is_a_named_safety_stop(tmp_path):
    ctx = Ctx(tmp_path)
    desk = last_climb(ctx)
    with pytest.raises(SystemExit) as stop:
        clear(ctx, desk)
    said = str(stop.value)
    assert said.startswith("SAFETY: plan_builder: ") and REFUSED in said
    assert not desk.plan.exists() and not desk.climb_path().exists()


def test_the_autopilot_parks_the_stop_by_its_name():
    kind, reason, _ = autopilot.classify(f"SystemExit: SAFETY: plan_builder: no draft on disk; {REFUSED}", set())
    assert kind == "park" and reason.startswith("safety: ")
