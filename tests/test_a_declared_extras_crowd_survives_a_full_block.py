"""A shot that declares extras keeps its crowd sentence when the block is full: the at-rest clause goes.

Jekyll Kawajiri ep01 shot 18 (three extras on the Sunday walk): `life_for` is the first thing a full
block drops, so a declared crowd was cut while the at-rest geometry stayed.  Fixture:
tests/fixtures/ep01_replay/P03/plan.json (copy of ep01's plan.json)."""
import json
from pathlib import Path

from studio import episode_ref_official as ro
from studio.episode_spec import Setup

PLAN = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "plan.json").read_text("utf-8"))
SHOT = next(s for s in PLAN["shots"] if s["index"] == 18)
SETUP = Setup(**{k: v for k, v in PLAN["setups"][SHOT["setup"]].items() if k in Setup.model_fields})
CTX = lambda: {"crowd_at": 0, "names": (), "faces": [], "cast": [], "life": {}}
SEG = {"t": 0.0, "end": 5, "size": "wide", "crowd": SHOT["crowd"], "setup": SETUP, "extras": SHOT["extras"]}


def full_parts() -> list[tuple[str, bool]]:
    core = " ".join(["stone"] * (ro.HIGH_BLOCK - 40))
    return [(core, True), (f"At the first frame {ro.lower_lead(SHOT['at_rest'])}.", False)]


def test_a_full_block_loses_the_crowd_to_the_old_rule():
    assert ro.life_for(1, SEG, CTX(), ro.joined(full_parts())) == ""


def test_the_at_rest_clause_goes_before_a_declared_crowd():
    parts = ro.rest_before_crowd(full_parts(), SEG)
    assert not any(t.startswith("At the first frame") for t, _ in parts)
    assert "walkers" in ro.life_for(1, SEG, CTX(), ro.joined(parts))


def test_a_shot_without_extras_keeps_its_at_rest_clause():
    assert ro.rest_before_crowd(full_parts(), dict(SEG, extras=0)) == full_parts()


def test_a_block_with_no_at_rest_clause_is_left_alone():
    core = full_parts()[:1]
    assert ro.rest_before_crowd(core, SEG) == core
