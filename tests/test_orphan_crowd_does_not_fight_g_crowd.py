"""The orphan cure clears the crowd AND the voices it put in the ambience, and it never
fights G-CROWD: it fires only when no shot of the setup is wide/full or has extras,
so a wide that G-CROWD owns keeps its crowd (Jekyll Kawajiri ep01 night_door)."""
import copy
import json
from pathlib import Path

from studio import episode_spec as spec, plan_cures as pc, plan_gates

PLAN = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02" / "plan.json"


def ep01() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def both(doc: dict) -> list[str]:
    ep = spec.Episode(**doc)
    return plan_gates.crowd_faults(ep) + plan_gates.orphan_crowd_faults(ep)


def test_the_cure_clears_night_door_crowd_and_its_shouting():
    out = pc.clear_orphan_crowds(ep01())
    door = out["setups"]["night_door"]
    assert door["crowd"] == ""
    assert door["ambience"] == "a cold night hush, gas hissing in the kerb lamp"
    assert both(out) == []
    assert out["setups"]["walk_on_day_2"]["crowd"] == ""                  # the lone split copy too


def test_other_setups_are_byte_identical():
    out = pc.clear_orphan_crowds(ep01())
    for name, setup in ep01()["setups"].items():
        if name not in ("night_door", "walk_on_day_2"):
            assert out["setups"][name] == setup
    assert out["shots"] == ep01()["shots"]


def test_the_cure_is_idempotent():
    once = pc.clear_orphan_crowds(ep01())
    assert pc.clear_orphan_crowds(copy.deepcopy(once)) == once


def test_a_wide_with_no_extras_keeps_its_crowd_for_g_crowd_to_judge():
    doc = ep01()
    next(s for s in doc["shots"] if s["index"] == 10)["size"] = "wide"
    out = pc.clear_orphan_crowds(copy.deepcopy(doc))
    assert out["setups"]["night_door"] == doc["setups"]["night_door"]
    assert [r.split(":")[0] for r in both(out) if "night_door" in r or "shot" in r] == ["G-CROWD shot 10"]


def test_either_order_of_the_two_cures_settles():
    doc = ep01()
    next(s for s in doc["shots"] if s["index"] == 10)["size"] = "wide"
    raised = copy.deepcopy(doc)
    next(s for s in raised["shots"] if s["index"] == 10)["extras"] = 1      # what G-CROWD's cure writes
    assert not [r for r in both(pc.clear_orphan_crowds(raised)) if "night_door" in r or "shot 10" in r]
    assert pc.clear_orphan_crowds(raised)["setups"]["night_door"]["crowd"] != ""
