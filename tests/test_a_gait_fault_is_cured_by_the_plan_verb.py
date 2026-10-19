"""P08 item 5: a gait shuffle is cured by the plan's verb, not a seed (LESSONS: "in profile, a long
stride, feet in the picture").  Only the pace phrase is rewritten; the camera head stays; one render."""
from __future__ import annotations

from studio import gait, take_ladder as tl
from studio.judges.verdict import Fault

T01 = ("The camera tracks beside the two walkers as they walk at a walking pace east toward the "
       "blistered door across the whole shot; the man about town swings his black walking cane; the "
       "lawyer's long black overcoat swings at his knees with each stride at a walking pace.")


def test_the_pace_phrase_becomes_the_verb_and_the_camera_head_stays():
    out = gait.gait_verb(T01)
    assert out.startswith("The camera tracks beside the two walkers as they walk")
    assert gait.VERB in out and out.count(gait.VERB) == 1
    assert "walking pace" not in out
    assert "swings his black walking cane" in out                # the other clauses are untouched


def test_a_motion_with_no_pace_phrase_gains_the_verb_as_a_clause():
    out = gait.gait_verb("The camera holds a locked-off frame; the man crosses the road.")
    assert out.startswith("The camera holds a locked-off frame; the man crosses the road")
    assert gait.VERB in out


def test_a_gait_fault_routes_to_gait_verb():
    assert tl.cure_of([Fault(kind="gait", where="T01", note="shuffle: 4.1 steps/s HARD")]) == "gait_verb"


def test_an_identical_second_signature_routes_to_nothing():
    again = Fault(kind="gait", where="T01", evidence={"repeated": True})
    assert tl.cure_of([again]) == ""


def test_feet_out_of_frame_is_advisory_and_routes_to_nothing():
    assert tl.cure_of([Fault(kind="gait", where="T01", note="not measured (unmeasured: feet in frame 3 frames)")]) == ""


def test_the_edit_rewrites_the_shots_motion_through_the_ladder():
    doc = {"shots": [{"index": 1, "motion": T01}]}
    out = tl.gait_edit(doc, 1)
    assert "walking pace" not in out["shots"][0]["motion"]


def test_a_gait_take_is_a_render_of_the_batch():
    routed = {"gait_verb": {1: []}, "move_type": {2: []}}
    assert tl.renders_of(routed) == [1, 2]


def test_the_early_lane_edits_a_gait_take_by_the_verb_and_a_moving_one_by_its_move():
    doc = {"shots": [{"index": 1, "motion": T01}, {"index": 2, "motion": "The camera holds a locked-off frame."}]}
    out = tl.plan_cure(doc, 1, [Fault(kind="gait", where="T01")])
    assert gait.VERB in out["shots"][0]["motion"]
    out = tl.plan_cure(out, 2, [Fault(kind="frozen-whole", where="T02")])
    assert "pushes in" in out["shots"][1]["motion"] or "tracks" in out["shots"][1]["motion"]
