"""A speed arm is judged against the control's own seed spread, not a pixel wall
(C1_verdict #2, C1_G §2.3).

MEASURED in BENCH_r2: a fixed 28 dB PSNR floor would refuse A1 -- the 8-step that
ships today -- on all six shots, because a chaotic sampler carries an int8 rounding
error to a new draw. PSNR is kept only as a same-draw guard (did the arm change the
numerics or the draw?). Identity is held to -2 sigma of the seed-to-seed spread per
shot and -0.02 on the dialogue mean; clones to the production take's own count;
invented speech to the control's own tail on that seed, with a prompt-asked mouth
action (the D1 laugh) exempt. The fixture is derived from the BENCH_r2 measures.
"""
import json
from pathlib import Path

import pytest

from scripts.bench import rulers

R2 = json.loads((Path(__file__).parent / "fixtures" / "bench" / "r2_rulers.json").read_text())
SHOTS = R2["shots"]
DIALOGUE = ("S4", "S6", "D1", "D2")


def verdict(arm: str) -> dict:
    return rulers.judge_arm(arm, SHOTS, control="A3", production="A0",
                            asked=set(R2["asked_mouth"]), dialogue=DIALOGUE)


def test_the_seed_spread_is_the_pooled_rms_of_the_seed_pairs():
    assert rulers.sigma_seed([(0.8, 0.798), (0.762, 0.756), (0.834, 0.849), (0.879, 0.912)]) == pytest.approx(0.0184, abs=1e-4)


def test_a_margin_under_three_db_is_a_new_draw_not_a_fault():
    assert rulers.same_draw(30.7, 16.0) is True
    assert rulers.same_draw(18.3, 17.1) is False


def test_ck_passes_identity_banding_clones_and_the_same_draw_guard():
    v = verdict("B3ck")
    assert v["same_draw"] is True
    assert v["faults"]["identity"] == [] and v["faults"]["banding"] == [] and v["faults"]["clones"] == []


def test_ck_fails_invented_speech_on_s4_only():
    assert verdict("B3ck")["faults"]["speech"] == ["S4"]


def test_shift6_beta_fails_invented_speech_on_its_heed():
    assert verdict("B4beta")["faults"]["speech"] == ["S4"]


def test_a1_the_shipped_8_step_is_never_refused_by_a_pixel_rule():
    v = verdict("A1")
    assert v["same_draw"] is False
    assert "psnr" not in v["faults"]


def test_the_production_take_is_not_a_clone_fault_against_itself():
    assert rulers.clone_faults("A0", SHOTS, production="A0") == []


def test_more_clones_than_the_production_take_is_a_fault():
    assert rulers.clone_faults("A1", SHOTS, production="A0") == ["D1"]


def test_a_word_the_control_also_speaks_on_that_seed_is_not_invented():
    shots = {"X": {"words": {"ctl": ["indeed"], "arm": ["indeed"]}}}
    assert rulers.speech_faults("arm", shots, control="ctl", asked=set()) == []
