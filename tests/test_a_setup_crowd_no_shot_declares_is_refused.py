"""G-CROWD-ORPHAN: a setup that stages a crowd no shot of it draws.  Jekyll Kawajiri
ep01 night_door staged 'five townsfolk ... shouting' over shots 0, 10, 11, 12 (a medium
close, a medium, a medium close, an insert; extras 0 on all) and the crowd leaked into
14 take prompts and the ambience.  G-CROWD covers the reverse (a wide with no extras)."""
import json
from pathlib import Path

from studio import episode_spec as spec, plan_cures as pc, plan_gates

PLAN = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02" / "plan.json"


def ep01() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def orphans(doc: dict, setup: str = "") -> list[str]:
    rows = plan_gates.orphan_crowd_faults(spec.Episode(**doc))
    return [r for r in rows if setup in r.split(":")[0]]


def test_night_door_and_the_split_copy_walk_on_day_2_are_refused():
    """walk_on_day_2 is the one-shot copy split_setup made of walk_on_day (its wide declares
    the walkers); its single medium shot declares none, so the copy's crowd is orphaned too."""
    rows = orphans(ep01())
    assert [r.split(":")[0] for r in rows] == ["G-CROWD-ORPHAN setup night_door",
                                               "G-CROWD-ORPHAN setup walk_on_day_2"]


def test_a_wide_over_the_crowd_is_g_crowds_row_not_the_orphans():
    doc = ep01()
    next(s for s in doc["shots"] if s["index"] == 10)["size"] = "wide"
    assert orphans(doc, "night_door") == []
    assert any(r.startswith("G-CROWD ") for r in plan_gates.crowd_faults(spec.Episode(**doc)))


def test_one_shot_declaring_extras_keeps_the_crowd():
    doc = ep01()
    next(s for s in doc["shots"] if s["index"] == 11)["extras"] = 2
    assert orphans(doc, "night_door") == []


def test_street_day_and_walk_on_day_pass_because_their_wides_declare_extras():
    assert not any("street_day" in r or "walk_on_day:" in r for r in orphans(ep01()))


def test_a_setup_no_shot_uses_is_not_an_orphan():
    doc = ep01()
    doc["setups"]["unused"] = dict(doc["setups"]["night_door"])
    assert orphans(doc, "unused") == []


def test_the_row_routes_to_the_orphan_cure():
    assert pc.cure_for(orphans(ep01())[0]) == "clear_orphan_crowds"
