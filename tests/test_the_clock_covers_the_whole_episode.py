"""Five-hour plan fix 1 (2026-09-30): the ceiling covers the EPISODE, not the
process.  `Budget.t0` was set at process start and `EpisodeContext` built a
fresh Budget every run, so ep14's 31 driver runs each got a fresh 5 h -- 34
logged hours under a 5 h ceiling.  Now the budget is charged with the seconds
timing.jsonl already holds, a spent ceiling makes a rung TERMINAL instead of
deferred (a deferral can never be paid for any more), and the driver refuses
to auto-resume a spent episode."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import episode_drive, judged_gate, run_budget, take_ladder
from studio.ladder import Rung
from studio.run_budget import EPISODE_SHARES, Budget


def room(tmp_path: Path, seconds: list[float]) -> Path:
    rows = [{"stage": "takes", "seconds": s, "note": ""} for s in seconds]
    (tmp_path / "timing.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return tmp_path


def test_the_spent_seconds_are_read_off_the_timing_log(tmp_path):
    assert run_budget.spent_before(room(tmp_path, [100.0, 250.5])) == 350.5
    assert run_budget.spent_before(tmp_path / "nowhere") == 0.0


def test_a_charged_budget_remembers_what_earlier_runs_spent():
    b = Budget(18000, EPISODE_SHARES, clock=lambda: 1000.0)
    assert not b.ceiling_spent()
    b.charge(17500.0)                      # earlier runs' timing.jsonl
    assert b.pool_left() <= 500.0          # the ceiling binds across runs now
    b.charge(600.0)
    assert b.ceiling_spent()


class Ctx:
    def __init__(self, spent: float):
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.budget.charge(spent)
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


def test_a_spent_ceiling_is_terminal_not_deferred():
    """A deferral exists so a later run can pay; with one episode-wide clock a
    spent ceiling can never be paid again -- the terminal answers."""
    rung = Rung("batched_cures", 565.0)
    poor = Ctx(spent=18001.0)
    assert judged_gate.affordable(poor, "EYE_TAKES", rung, taken=1) is False
    assert poor.learned and poor.learned[-1].action == "terminal"
    assert take_ladder.can_afford(poor, take_ladder.BATCH, 3) is False
    rich = Ctx(spent=0.0)
    assert judged_gate.affordable(rich, "EYE_TAKES", rung, taken=1) is True


def test_an_unaffordable_rung_with_ceiling_left_is_still_terminal():
    """The deferral is gone: a rung even the whole remaining ceiling cannot
    pay is terminal in the same run, never 'run again to resume'."""
    mid = Ctx(spent=0.0)
    dear = Rung("batched_cures", 10 ** 9)
    assert judged_gate.affordable(mid, "EYE_TAKES", dear, taken=1) is False
    assert mid.learned[-1].action == "terminal"


def test_the_driver_never_resumes_a_spent_episode():
    ran, said = [], []
    code = episode_drive.drive(lambda: ran.append(1) or "DEFERRED: EYE_TAKES needs 565 s for its rung",
                               said.append, over_budget=lambda: True)
    assert len(ran) == 1                   # one run may finish terminals; no resume
    assert code == 1 and any("ceiling" in s for s in said)
