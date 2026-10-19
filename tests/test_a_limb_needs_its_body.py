"""G-LIMB (advisory): a sleeve, hand, arm or leg that ENTERS FROM AN EDGE with no body word in
the cell is drawn as a floating part (Jekyll Kawajiri ep01 shot 27: 'The tramp's ragged sleeve
reaches in from the RIGHT edge' -> a torn green sleeve and hand ending in a hard cut mid-wall,
no body; it passed every check).  insert and extreme_close are exempt (the hand IS the subject).
The deterministic cure appends a body clause before the contract; no writer retry."""
import copy
import json
import sys
from pathlib import Path

from studio import cell_gates, episode_spec as spec, grammar_battery, plan_cures as pc, plan_gates

PLAN = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02" / "plan.json"
OLD_27 = ("THE FOCUS OF THE PICTURE IS the match flaring at the CENTRE. The tramp's ragged sleeve reaches in "
          "from the RIGHT edge, a hand striking the match on the stained door panel. Three worn stone steps "
          "fill the BOTTOM third; the blind plaster wall fills the TOP third above the door.")


def ep01() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


OLD_FRAME = "Medium on the blistered door in its recess as a match is struck on its stained panel."
OLD_MOTION = "The camera pulls back, widening to show the door and its blind wall across the whole shot; the match drags along the panel; the flame flares."


def with_27(at_rest: str, old_words: bool = True) -> dict:
    """ep01 with shot 27's cell put back to the superseded wording (no body word anywhere in it)."""
    doc = ep01()
    shot = next(s for s in doc["shots"] if s["index"] == 27)
    shot["at_rest"] = at_rest
    if old_words:
        shot["frame"], shot["motion"] = OLD_FRAME, OLD_MOTION
    return doc


def limbs(doc: dict) -> list[str]:
    return plan_gates.limb_faults(spec.Episode(**doc))


def test_the_real_ep01_plan_is_clean():
    assert limbs(ep01()) == []


def test_the_insert_cuff_of_shot_12_stays_clean_because_an_insert_is_exempt():
    doc = ep01()
    shot = next(s for s in doc["shots"] if s["index"] == 12)
    assert shot["size"] == "insert" and "reaches in from the RIGHT edge" in shot["at_rest"]
    assert limbs(doc) == []
    shot["size"] = "medium"                                  # not an insert: the same words are a fault
    assert [r.split(":")[0] for r in limbs(doc)] == ["G-LIMB shot 12"]


def test_the_old_shot_27_words_are_a_fault():
    rows = limbs(with_27(OLD_27))
    assert len(rows) == 1 and rows[0].startswith("G-LIMB shot 27")


def test_a_body_word_in_the_cell_clears_it():
    whole = OLD_27.replace("The tramp's ragged sleeve", "The tramp crouched whole on the step, his ragged sleeve")
    assert limbs(with_27(whole)) == []


def test_the_owner_order_wording_is_clean():
    fixed = next(s for s in ep01()["shots"] if s["index"] == 27)["at_rest"]
    assert "crouched whole" in fixed and limbs(with_27(fixed, old_words=False)) == []


def test_the_cure_adds_a_body_and_the_row_goes():
    out = pc.body_clause(with_27(OLD_27))
    assert limbs(out) == []
    assert next(s for s in out["shots"] if s["index"] == 27)["at_rest"].startswith(OLD_27)


def test_the_cure_is_idempotent_and_leaves_clean_shots_alone():
    once = pc.body_clause(with_27(OLD_27))
    assert pc.body_clause(copy.deepcopy(once)) == once
    other = [s for s in once["shots"] if s["index"] != 27]
    assert other == [s for s in ep01()["shots"] if s["index"] != 27]


def test_the_cures_output_passes_the_full_contract_and_adds_no_row():
    def battery(doc: dict) -> list[str]:
        ep = spec.Episode(**doc)                              # the contract
        return (plan_gates.faults(ep) + grammar_battery.faults(ep, 2.45) + cell_gates.aim_faults(ep)
                + plan_gates.moves_faults(ep) + plan_gates.still_faults(ep))
    before, after = battery(with_27(OLD_27)), battery(pc.body_clause(with_27(OLD_27)))
    assert set(after) <= set(before)


def test_plan_check_prints_it_as_an_advisory_not_a_hard_row():
    sys.path.insert(0, "scripts/episode")
    import inspect

    import plan_check
    src = inspect.getsource(plan_check)
    assert "limb_faults" in src and "advisory" in src.split("limb_faults")[1][:200]


def test_the_free_pre_contract_restore_runs_the_cure():
    sys.path.insert(0, "scripts/episode")
    import plan_repair
    assert limbs(plan_repair.restored(with_27(OLD_27))) == []
