"""lock_two_shot: G-TWO's only wrong word is the VERB (Jekyll Kawajiri ep01 shot 26,
medium/pan_to against medium/locked; it survived five writer rounds over two climbs
because CURES had no pattern for it).  The cure locks the head and drops the aim.

The fixture is the signed ep01 plan; shot 26's head is put back to the drafts' pan
(the fault row names it: 'medium/pan_to'), so the real cell, setups and lines judge it."""
import copy
import json
import re
from pathlib import Path

from studio import cell_gates, episode_spec as spec, framing_grammar as fg, grammar_battery, plan_cures as pc
from studio import episode_ref_official as ro, plan_gates

PLAN = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02" / "plan.json"
PAN = ("The camera pans from the lawyer to the man about town across the whole shot; "
       "the lawyer's hand clasps the man about town's black-gloved hand; their joined hands pump up and down.")
PAN_UNDRAWN = PAN.replace("to the man about town", "to the shaking stranger")


def draft(motion: str = PAN) -> dict:
    doc = json.loads(PLAN.read_text(encoding="utf-8"))
    next(s for s in doc["shots"] if s["index"] == 26)["motion"] = motion
    return doc


def battery(doc: dict) -> list[str]:
    ep = spec.Episode(**doc)
    rows = grammar_battery.faults(ep, 2.9) + cell_gates.aim_faults(ep)
    rows += plan_gates.moves_faults(ep) + plan_gates.still_faults(ep)
    rows += [m.group(0) for s in doc["shots"] for m in ro.GLUED_PACE.finditer(s["motion"])]
    return rows


def test_the_draft_trips_g_two_and_the_cure_table_names_the_cure():
    row = next(r for r in fg.two_shot_faults(spec.Episode(**draft())))
    assert "medium/pan_to" in row
    assert pc.cure_for(row) == "lock_two_shot"


def test_a_wrong_size_row_stays_creative_so_it_is_never_counted_cured_for_nothing():
    row = ("G-TWO shot 7: a two-person reaction is a locked medium two-shot, "
           "measured full/follow against medium/locked")
    assert pc.cure_for(row) is None


def test_shot_26_goes_medium_pan_to_medium_locked():
    out = pc.lock_two_shot(draft(), [26])
    shot = spec.Episode(**out).shots[26]
    assert (shot.size, fg.verb(shot)) == ("medium", "locked")
    assert shot.motion.split(";")[1:] == PAN.split(";")[1:]          # the actor clauses stay


def test_the_battery_is_clean_on_g_two_and_g_aim_before_and_after():
    assert not [r for r in battery(pc.lock_two_shot(draft(), [26])) if r.startswith(("G-TWO", "G-AIM"))]
    assert any(r.startswith("G-TWO") for r in battery(draft()))
    undrawn = battery(draft(PAN_UNDRAWN))
    assert any(r.startswith("G-AIM") for r in undrawn)               # the aim clause was a G-AIM row too
    assert not [r for r in battery(pc.lock_two_shot(draft(PAN_UNDRAWN), [26])) if r.startswith("G-AIM")]


def test_the_cure_adds_no_row_to_the_whole_battery():
    before = battery(draft())
    after = battery(pc.lock_two_shot(draft(), [26]))
    assert set(after) <= set(before) and len(after) < len(before)


def test_the_cure_is_idempotent_and_touches_only_the_named_shot():
    once = pc.lock_two_shot(draft(), [26])
    assert pc.lock_two_shot(copy.deepcopy(once), [26]) == once
    other = [s for s in draft()["shots"] if s["index"] != 26]
    assert [s for s in once["shots"] if s["index"] != 26] == other


def test_a_wrong_size_is_left_to_the_writer():
    doc = draft()
    next(s for s in doc["shots"] if s["index"] == 26)["size"] = "close"
    assert pc.lock_two_shot(copy.deepcopy(doc), [26]) == doc


def test_plan_repair_applies_the_cure_from_the_fault_row(tmp_path):
    import sys
    sys.path.insert(0, "scripts/episode")
    import plan_repair
    rows = fg.two_shot_faults(spec.Episode(**draft()))
    out, uncured, names = plan_repair.apply(draft(), rows, tmp_path, 1, 2.9, llm=False)
    assert "lock_two_shot" in names and not uncured
    assert not fg.two_shot_faults(spec.Episode(**out))
