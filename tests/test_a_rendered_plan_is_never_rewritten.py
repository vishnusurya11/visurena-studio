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
    assert writer.calls == [] and gate.commands == []
    assert _plan(ctx).read_bytes() == before


def test_a_rendered_plan_is_done(ctx, monkeypatch):
    _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    rendered(ctx)
    assert step.done(ctx)
