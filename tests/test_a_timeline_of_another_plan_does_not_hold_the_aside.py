"""ep21, 2026-10-08 08:55Z: the aside (the 32-shot draft whose voices and
timeline were on disk) could not be cured first on the relaunch, because the
guard read 'a timeline exists' as 'this plan ran downstream' -- while plan.json
held an unsigned 29-shot stray the ladder had left mid-climb.  A timeline is
a run of the plan it was built FROM; one built from another plan is no run of
the draft on disk and must not keep the aside from its cure."""
from __future__ import annotations

import json

import tests.test_step_02_plan as t2
from scripts.episode import step_02_plan as step
from studio import episode_home, plan_ladder, timeline_fresh
from tests.test_episode_writer import canned_plan

conn = t2.conn
ctx = t2.ctx
OTHER = "04a2975ac577433c"


def _plan(ctx):
    path = episode_home.plan_path(ctx.book_dir, 3)
    episode_home.write_plan(path, canned_plan())
    return path


def _placed(ctx, fingerprint: str) -> None:
    (ctx.home / "placed.json").write_text(json.dumps({"plan": fingerprint, "shots": [], "lines": []}),
                                           encoding="utf-8")


def test_a_timeline_built_from_this_plan_is_its_run(ctx):
    _plan(ctx)
    _placed(ctx, timeline_fresh.fingerprint(episode_home.load_plan(ctx.book_dir, 3), None))
    assert step.timeline_of_plan(ctx) is True


def test_a_timeline_of_another_plan_is_not(ctx):
    _plan(ctx)
    _placed(ctx, OTHER)
    assert step.timeline_of_plan(ctx) is False


def test_no_timeline_is_no_run(ctx):
    _plan(ctx)
    assert step.timeline_of_plan(ctx) is False


def test_the_aside_is_cured_first_over_another_plans_timeline(ctx, monkeypatch):
    plan = _plan(ctx)
    (ctx.home / plan_ladder.DEFERRED).write_text(json.dumps({"draft": canned_plan()}), encoding="utf-8")
    _placed(ctx, OTHER)
    calls = []

    def capture(script, *args):
        calls.append((script, args))
        return 0, "BATTERY CLEAN"
    monkeypatch.setattr(ctx, "capture_script", capture)
    step.cure_aside_first(ctx, plan)
    assert calls and "--from-aside" in calls[0][1]


def test_the_aside_waits_behind_this_plans_own_timeline(ctx, monkeypatch):
    plan = _plan(ctx)
    (ctx.home / plan_ladder.DEFERRED).write_text(json.dumps({"draft": canned_plan()}), encoding="utf-8")
    _placed(ctx, timeline_fresh.fingerprint(episode_home.load_plan(ctx.book_dir, 3), None))
    monkeypatch.setattr(ctx, "capture_script", lambda *a: (_ for _ in ()).throw(AssertionError("cured over a run")))
    step.cure_aside_first(ctx, plan)
