"""A plan whose takes are rendered is never sent back to the writer.

ep13 (2026-09-27): the take ladder's move_type edits made plan.json newer than
its signature; step 02 re-judged it, the battery (with the new pre-render gate
G-STILL, and G-MOVES counting the ladder's own substitutes) refused, and the
`improve` rung had the writer REWRITE the plan -- 25 lines for 24, no shot
matching its rendered take.  The battery guards spend BEFORE a render; after
it, the takes are judged by the take gates.  A --rewrite was already refused
once the plan ran downstream; the ladder now is too.
"""
import json

from tests.test_step_02_plan import REFUSED_OUT, _plan, _wire, conn, ctx, step  # noqa: F401
from tests.test_episode_writer import canned_plan


def rendered(ctx):
    _plan(ctx).write_text(json.dumps(canned_plan(3)), encoding="utf-8")
    takes = ctx.home / "takes" / "r2v"
    takes.mkdir(parents=True)
    (takes / "T00.mp4").write_bytes(b"take")


def test_a_rendered_plan_is_not_rejudged_or_rewritten(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    rendered(ctx)
    before = _plan(ctx).read_bytes()
    step.run(ctx)
    assert writer.calls == []
    assert _plan(ctx).read_bytes() == before


def test_a_rendered_plan_is_done(ctx, monkeypatch):
    _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    rendered(ctx)
    assert step.done(ctx)


def test_a_rendered_plan_is_still_judged_in_report_mode(ctx, monkeypatch):
    """Ten-agent debate 2026-09-27: 971485e was right to bar the rewrite and
    wrong to stop judging -- G-STILL would have named shots 9, 18 and 19, all
    three visible on ep13's master.  The battery runs; its refusals are logged."""
    writer, gate = _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    logged = []
    monkeypatch.setattr(ctx, "log", lambda msg, **k: logged.append(msg), raising=False)
    rendered(ctx)
    step.run(ctx)
    assert writer.calls == [] and len(gate.commands) == 1
    assert any("G-SCALE shot 4" in m for m in logged)
