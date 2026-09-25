"""A refusal names rows, so the re-ask carries the previous plan and asks for
those rows changed -- never a rewrite from nothing.  Episode 13 (2026-09-25),
four passes: every rung's from-scratch draft fixed what was named and tripped
a different rule (slowly -> three lines a shot -> twenty words -> a face at
close -> slowly again); the `model_tier` rung escalated to the same model
with reasoning off."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from agents import episode_writer as ew
from studio import llm, plan_ladder
from studio.judges.verdict import Verdict
from tests.test_episode_writer import BRIEF, FakeModel, canned_draft, canned_plan


def test_the_writer_re_asks_with_its_previous_plan_and_the_rows_to_change():
    broken = {**canned_draft(), "lines": []}
    fake = FakeModel(broken, canned_draft())
    episode = ew.write(BRIEF, _agent=fake)
    assert episode.title == "The Yard" and len(fake.prompts) == 2
    first, second = fake.prompts
    assert ew.PREVIOUS not in first
    assert ew.PREVIOUS in second and '"title": "The Yard"' in second
    assert "CONTRACT" in second and "no button" in second
    assert second.index(ew.PREVIOUS) < second.index(ew.REFUSED)


def test_a_plan_refused_on_every_edit_surfaces_the_contract():
    fake = FakeModel({**canned_draft(), "lines": []})
    with pytest.raises(ValidationError, match="no button"):
        ew.write(BRIEF, _agent=fake)
    assert len(fake.prompts) == ew.CONTRACT_RETRIES


def test_the_gates_refusals_and_the_previous_plan_both_reach_the_prompt():
    fake = FakeModel(canned_draft())
    ew.write(BRIEF, refusals=["G-SCALE shot 4: no cell for a close"], previous=canned_plan(),
             _agent=fake)
    prompt = fake.prompts[0]
    assert ew.PREVIOUS in prompt and "G-SCALE shot 4" in prompt
    assert prompt.index("THE BRIEF") < prompt.index(ew.PREVIOUS) < prompt.index(ew.REFUSED)


class Recorder:
    def __init__(self):
        self.previous, self.refusals = [], []

    def write(self, brief, refusals=None, previous=None, **kw):
        self.previous.append(previous)
        self.refusals.append(refusals)
        from studio.episode_spec import Episode
        return Episode.model_validate(canned_plan(3))


def _desk(tmp_path, writer):
    from types import SimpleNamespace
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(canned_plan(3)), encoding="utf-8")
    desk = plan_ladder.Desk(SimpleNamespace(book_dir=tmp_path, number=3), plan, writer=writer)
    desk.brief = {}
    return desk


def test_an_improve_rung_hands_the_refused_plan_back_to_be_edited(tmp_path):
    writer = Recorder()
    desk = _desk(tmp_path, writer)
    rungs = plan_ladder.ladder().rungs
    desk.take(rungs[0], 0, plan_ladder.battery_verdict(["G-SCALE shot 4: no cell for a close"]))
    assert rungs[0].name == plan_ladder.IMPROVE
    assert writer.previous[0]["title"] == "The Yard"
    assert writer.refusals[0] == ["G-SCALE shot 4: no cell for a close"]


def test_a_fresh_brief_starts_from_nothing(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(plan_ladder, "plan_brief", SimpleNamespace(build=lambda b, n, targets=None: {"number": n}))
    writer = Recorder()
    desk = _desk(tmp_path, writer)
    fresh = next(r for r in plan_ladder.ladder().rungs if r.name == plan_ladder.FRESH_BRIEF)
    desk.take(fresh, 0, plan_ladder.battery_verdict(["G-SCALE shot 4"]))
    assert writer.previous == [None] and writer.refusals == [None]


def test_the_model_tier_rung_is_a_tier_that_reasons():
    params = llm.resolve_tier(plan_ladder.MODEL_TIER_NAME).get("params") or {}
    assert params.get("reasoning_effort", "none") != "none"
    assert plan_ladder.MODEL_TIER_NAME != ew.TIER
