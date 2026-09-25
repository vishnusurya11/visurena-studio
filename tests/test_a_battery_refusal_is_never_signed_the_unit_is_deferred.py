"""The battery (plan_check) still refusing after improve x2, fresh_brief x1
and model_tier x1: the unit is DEFERRED.  The draft is set aside as
plan.deferred.json with its faults and the pass count, plan.json is gone so
the next pass authors again, no verdict is written, the critic is never
asked, one audit row and one terminal learning are left -- and nobody parks."""
from __future__ import annotations

import json

import pytest

from studio import audit_rows, learnings, plan_verdict
from studio.deferral import Deferred
from tests.test_step_02_plan import (CLEAN_OUT, REFUSED_OUT, Capture, Reader, Writer, _plan,  # noqa: F401
                                     _wire, conn, ctx, step)


def test_the_whole_ladder_is_climbed_then_the_draft_is_deferred(ctx, monkeypatch):
    writer, gate = _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    with pytest.raises(Deferred) as aside:
        step.run(ctx)
    assert aside.value.gate == "PLAN" and aside.value.aside == "episodes/ep03/plan.deferred.json"
    # round 0, improve, improve, fresh_brief, model_tier
    assert len(writer.calls) == 5 and len(gate.commands) == 5
    assert writer.calls[3] is None, "a fresh brief starts without the refusal history"
    assert writer.agents[4] is not None and writer.agents[4].tier == step.plan_ladder.MODEL_TIER_NAME
    assert writer.agents[:4] == [None] * 4


def test_the_deferred_file_holds_the_draft_and_no_verdict_exists(ctx, monkeypatch):
    _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    with pytest.raises(Deferred):
        step.run(ctx)
    plan = _plan(ctx)
    aside = plan.with_name(step.plan_ladder.DEFERRED)
    assert aside.exists() and not plan.exists()
    assert not plan_verdict.verdict_path(plan).exists()
    doc = json.loads(aside.read_text(encoding="utf-8"))
    assert doc["verdict"] == "DEFERRED" and doc["passes"] == 1 and doc["signed_by"] == "judge:plan@1"
    assert doc["draft"]["title"] == "The Yard" and len(doc["plan_sha8"]) == 8
    assert doc["faults"] and doc["faults"][0]["kind"] == "battery"
    assert step.done(ctx) is False


def test_the_critic_is_never_asked_while_the_battery_refuses(ctx, monkeypatch):
    critic = Reader()
    _wire(ctx, monkeypatch, (1, REFUSED_OUT), reader=critic)
    with pytest.raises(Deferred):
        step.run(ctx)
    assert critic.texts == []


def test_a_second_pass_counts_and_the_audit_row_names_the_terminal(ctx, monkeypatch):
    _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    for _ in range(2):
        with pytest.raises(Deferred):
            step.run(ctx)
    aside = _plan(ctx).with_name(step.plan_ladder.DEFERRED)
    assert json.loads(aside.read_text(encoding="utf-8"))["passes"] == 2
    rows = audit_rows.load(ctx.book_dir)
    assert len(rows) == 2 and rows[0].gate == "PLAN" and rows[0].judge == "judge:plan@1"
    assert rows[0].terminal == "defer" and rows[0].artefact == "episodes/ep03/plan.deferred.json"
    terminal = [row for row in learnings.load(ctx.learnings_path) if row.terminal]
    assert terminal and terminal[0].gate == "PLAN" and terminal[0].note.endswith("-> defer")


def test_a_deferred_unit_is_authored_again_and_signs_when_the_battery_passes(ctx, monkeypatch):
    _wire(ctx, monkeypatch, (1, REFUSED_OUT))
    with pytest.raises(Deferred):
        step.run(ctx)
    _wire(ctx, monkeypatch, (0, CLEAN_OUT))
    step.run(ctx)
    assert plan_verdict.current(_plan(ctx))
