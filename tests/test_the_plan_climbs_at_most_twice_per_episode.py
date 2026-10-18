"""The plan's defer-and-re-author loop is capped (owner 2026-10-18, STEP_CAPS.md finding 2:
wotw/ep15 ran 24 plan climbs, 301 min, because `passes` (plan_ladder.defer) was counted and
never read).

At most `climbs` (2) climbs per EPISODE, counted in attempts.json so a drive run, a relaunch
or an autopilot cure reads the same count.  The last climb never defers: it keeps the best
draft, signed flagged.  A climb past the count takes no writer round at all.  When a tier-1
line (a downstream builder repeats it: contract, cast bound) is still on the kept draft, the
unit parks ONCE with the line; the next launch goes on with the signed draft.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.episode import step_02_plan as s02  # noqa: E402
from studio import plan_ladder, plan_verdict, step_attempts, step_caps  # noqa: E402
from studio.deferral import Deferred  # noqa: E402


class Ctx:
    def __init__(self, home: Path):
        self.home, self.book_dir, self.said = home, home, []

    def log(self, msg, **kw):
        self.said.append(msg)


def desk(home: Path) -> plan_ladder.Desk:
    d = plan_ladder.Desk(Ctx(home), home / "plan.json", writer=None)
    d.battery_terminal = plan_ladder.DEFER
    return d


def test_the_climb_wall_is_the_tables():
    assert plan_ladder.CLIMB_WALL_S == step_caps.wall_s("plan") == 30 * 60


def test_the_first_climb_may_defer_the_last_keeps_best_and_one_past_takes_no_round(tmp_path):
    ctx = Ctx(tmp_path)
    first = desk(tmp_path)
    assert sum(r.tries for r in s02.climb_ladder(ctx, first).rungs) == 3
    assert first.battery_terminal == plan_ladder.DEFER
    last = desk(tmp_path)
    assert sum(r.tries for r in s02.climb_ladder(ctx, last).rungs) == 3
    assert last.battery_terminal == plan_ladder.KEEP_BEST
    past = desk(tmp_path)
    assert s02.climb_ladder(ctx, past).rungs == []
    assert past.battery_terminal == plan_ladder.KEEP_BEST
    assert step_attempts.count(tmp_path, s02.CLIMBS) == 3
    assert any(line.startswith("CAP plan: 2/2 climbs") for line in ctx.said)


def signed(home: Path, notes: list[str]) -> Path:
    plan = home / "plan.json"
    plan.write_text(json.dumps({"x": 1}), encoding="utf-8")
    plan_verdict.sign(plan, "kept", signed_by="judge:plan@1", flagged=True,
                      faults=[{"kind": "battery", "where": "plan", "note": n} for n in notes])
    return plan


def test_a_tier_one_line_left_at_the_last_climb_parks_once(tmp_path):
    plan = signed(tmp_path, ["CAST BOUND   : ['poole']", "VERDICT      : REFUSED"])
    step_attempts.spend(tmp_path, s02.CLIMBS)
    step_attempts.spend(tmp_path, s02.CLIMBS)
    with pytest.raises(Deferred, match="poole"):
        s02.park_once(Ctx(tmp_path), plan)
    s02.park_once(Ctx(tmp_path), plan)                  # the second launch goes on


def test_judged_rows_alone_never_park(tmp_path):
    plan = signed(tmp_path, ["CELL GATES   : 1", "    G-AIM shot 10: the camera aims at 'lamp'"])
    step_attempts.spend(tmp_path, s02.CLIMBS)
    step_attempts.spend(tmp_path, s02.CLIMBS)
    s02.park_once(Ctx(tmp_path), plan)


def test_a_climb_with_climbs_left_never_parks(tmp_path):
    plan = signed(tmp_path, ["CAST BOUND   : ['poole']", "VERDICT      : REFUSED"])
    step_attempts.spend(tmp_path, s02.CLIMBS)
    s02.park_once(Ctx(tmp_path), plan)


def test_past_the_climbs_the_asides_draft_is_judged_as_it_is_no_writer_round(tmp_path):
    from tests.test_episode_writer import canned_plan
    (tmp_path / plan_ladder.DEFERRED).write_text(json.dumps({"draft": canned_plan(), "passes": 2}),
                                                 encoding="utf-8")
    step_attempts.spend(tmp_path, s02.CLIMBS)
    step_attempts.spend(tmp_path, s02.CLIMBS)
    d = desk(tmp_path)                                  # writer=None: a writer round would raise
    s02.first_draft(Ctx(tmp_path), d)
    assert json.loads((tmp_path / "plan.json").read_text(encoding="utf-8")) == canned_plan()


def test_a_climb_resumed_from_its_checkpoint_is_not_a_new_climb(tmp_path):
    ctx = Ctx(tmp_path)
    s02.climb_ladder(ctx, desk(tmp_path))
    resumed = desk(tmp_path)
    resumed.rungs_done = 1
    s02.climb_ladder(ctx, resumed)
    assert step_attempts.count(tmp_path, s02.CLIMBS) == 1
    assert resumed.battery_terminal == plan_ladder.DEFER
