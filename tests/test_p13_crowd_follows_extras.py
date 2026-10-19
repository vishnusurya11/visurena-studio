"""Lint P13 counts the setup's crowd only for a shot that declares extras > 0.

Jekyll Kawajiri ep01 (2026-10-18): the night door's ring of townsfolk covered "the doctor" in the
text of 14 extras-0 shots, so the lint that should have refused the crowd's words let them through.
Fixture: tests/fixtures/ep01_replay/P03/plan.json, a copy of ep01's plan.json."""
import json
from pathlib import Path

from studio import prompt_lint as pl

PLAN = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "plan.json").read_text("utf-8"))
SHOT = next(s for s in PLAN["shots"] if s["index"] == 10)        # night_door, extras 0
TEXT = "The doctor leans in beside the kerb lamp."


def test_a_setup_crowd_is_not_a_cover_for_an_extras_0_shot():
    facts = pl.shot_facts(PLAN, SHOT, {})
    assert facts["crowd"].strip() == ""
    assert any("doctor" in f for f in pl.p13_people(TEXT, facts))


def test_a_setup_crowd_covers_a_shot_that_declares_extras():
    facts = pl.shot_facts(PLAN, dict(SHOT, extras=2), {})
    assert "doctor" in facts["crowd"]
    assert pl.p13_people(TEXT, facts) == []


def test_a_shots_own_crowd_still_counts():
    assert "tramp" in pl.shot_facts(PLAN, dict(SHOT, crowd="one tramp"), {})["crowd"]


def test_the_take_facts_follow_the_same_rule():
    zero = pl.crowd_text(SHOT, PLAN["setups"]["night_door"])
    two = pl.crowd_text(dict(SHOT, extras=2), PLAN["setups"]["night_door"])
    assert zero.strip() == "" and "doctor" in two
