"""The plan ladder is improve x2 -> model_tier -> terminal (C2_verdict #3).

fresh_brief threw the refusal history away and wrote from a new brief.  Over
40 terminal climbs (ep17-27) it produced the kept draft once (ep18 14:21,
[3, 3, 1, 58 -> 58], an anomaly, not a rescue); a battery-refused draft is
deferred, never shipped, so dropping the rung cannot ship a worse plan."""
from __future__ import annotations

import pytest

from studio import plan_ladder
from studio.ladder import _tries
from tests.test_a_refusal_edits_the_previous_plan import Recorder, _desk
from tests.test_step_02_plan import REFUSED_OUT, _wire, conn, ctx, step  # noqa: F401
from studio.deferral import Deferred


def test_the_rungs_are_improve_improve_model_tier():
    assert [rung.name for rung, _ in _tries(plan_ladder.ladder())] == ["improve", "improve", "model_tier"]
    assert not hasattr(plan_ladder, "FRESH_BRIEF")


def test_a_battery_climb_never_builds_a_fresh_brief(ctx, monkeypatch):
    fresh = []
    real = plan_ladder.Desk.brief_
    monkeypatch.setattr(plan_ladder.Desk, "brief_", lambda self, fresh_=False, **kw: fresh.append(kw) or real(self))
    writer, _ = _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    with pytest.raises(Deferred):
        step.run(ctx)
    assert len(writer.calls) == 4                       # round 0, improve, improve, model_tier
    assert all(call is not None for call in writer.calls[1:]), "every rung edits with the history"
    assert not any(kw.get("fresh") for kw in fresh)


def test_a_converged_draft_is_still_edited(tmp_path):
    writer = Recorder()
    desk = _desk(tmp_path, writer)
    model_tier = plan_ladder.ladder().rungs[-1]
    desk.drafts = [("a passed draft", None)]            # model_tier would not write a far draft now
    desk.take(model_tier, 0, plan_ladder.battery_verdict(["G-SCALE shot 4"]))
    assert writer.previous[-1] is not None


def test_model_tier_hears_every_refusal_of_the_climb(tmp_path):
    writer = Recorder()
    desk = _desk(tmp_path, writer)
    rungs = [rung for rung, _ in _tries(plan_ladder.ladder())]
    for rung, line in zip(rungs, ["G-A shot 1", "G-B shot 2", "G-C shot 3"]):
        desk.take(rung, 0, plan_ladder.battery_verdict([line, "G-X far 1", "G-X far 2"]))
    assert {"G-A shot 1", "G-B shot 2", "G-C shot 3"} <= set(writer.refusals[-1])
