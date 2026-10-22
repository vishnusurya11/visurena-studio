"""An `end` is the drawer's last picture as nouns in places, never a camera sentence (craft ruling A19, G-END-NOUNS).

ep01 plan shot 6 wrote its `end` as "The camera tilts up from the wet cobbles to the corner gas lamp ... and
continues to the last frame of the shot": a move, not a picture, and the arrival builder read "the camera tilts
up" as the noun now in frame.  The plan gate refuses such an end at sign and its free cure clears it (an empty
end lets the camera's own move say the arrival); `end_noun` lends no noun from a clause that moves the camera.
The arrival sentence's template (the verb said three times) is shot-framework D-d, held for bench R2-3.
Fixtures: tests/fixtures/craft/episodes/ep01/plan.json, tests/fixtures/shot_framework/."""
from __future__ import annotations

import json
from pathlib import Path

import shot_framework_fixtures as sf
from studio import episode_ref_official as ro, plan_cures, plan_gates
from studio.episode_spec import Episode

PLAN = Path(__file__).parent / "fixtures" / "craft" / "episodes" / "ep01" / "plan.json"


def doc() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def test_end_noun_lends_nothing_from_a_camera_sentence():
    assert ro.end_noun(doc()["shots"][6]["end"]) == ""
    assert ro.end_noun("The lamp glow fills the TOP edge as the camera pushes in") == ""


def test_end_noun_still_lends_a_layouts_noun():
    assert ro.end_noun("The two walkers stand at the CENTRE of the far pavement") == "the two walkers"


def test_ep01_shot_6_faults_g_end_nouns():
    rows = plan_gates.end_noun_faults(Episode.model_validate(doc()))
    assert [r.split(":")[0] for r in rows] == ["G-END-NOUNS shot 6"]


def test_the_fault_routes_to_its_free_cure():
    row = plan_gates.end_noun_faults(Episode.model_validate(doc()))[0]
    assert plan_cures.cure_for(row) == "camera_ends"


def test_the_cure_clears_the_camera_end_and_its_change_only():
    cured = plan_cures.camera_ends(doc(), [6])
    assert cured["shots"][6]["end"] == "" and cured["shots"][6]["changed"] == ""
    assert cured["shots"][1]["end"] == doc()["shots"][1]["end"]
    assert plan_gates.end_noun_faults(Episode.model_validate(cured)) == []


def test_t06_rebuilt_arrival_says_no_camera_noun():
    assert "with the camera" not in sf.detailed(sf.take_prompt(6))
