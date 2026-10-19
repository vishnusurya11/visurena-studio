"""P05 item 2: a wrist in the picture with no shoulder, elbow or head behind it (ep01 shot 27, the floating
hand, passed every check) is an `orphan_limb` fault, ADVISORY until P06's eval calibrates it.  The
DWPose frame the eye already reads gives it; no second VL call.  $0: injected keypoints."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from studio import episode_home
from studio.judges import panel_eye
from studio.measure import keypoints as kp
from test_the_eye_rereads_only_the_rewound_panels import board28, tools


def person(**seen):
    """A (18,3) person with only the named keypoints (name -> x, y) seen."""
    pts = np.zeros((18, 3))
    for name, (x, y) in seen.items():
        pts[getattr(kp, name)] = (x, y, 0.9)
    return pts


def frame_of(*people):
    return {"canvas_width": 100, "canvas_height": 100,
            "people": [{"pose_keypoints_2d": [v for r in p for v in (r[0] * 100, r[1] * 100, r[2])]} for p in people]}


def test_a_lone_wrist_in_frame_is_an_orphan():
    assert kp.orphan_limbs(person(R_WRIST=(0.5, 0.6))) == [kp.R_WRIST]


def test_a_wrist_on_its_arm_is_not():
    assert kp.orphan_limbs(person(R_WRIST=(0.5, 0.6), R_ELBOW=(0.45, 0.5), R_SHOULDER=(0.4, 0.4))) == []


def test_a_wrist_beside_a_head_is_not():
    assert kp.orphan_limbs(person(L_WRIST=(0.5, 0.6), NOSE=(0.5, 0.2))) == []


def test_a_wrist_on_the_border_is_cropped_not_orphaned():
    assert kp.orphan_limbs(person(R_WRIST=(0.995, 0.6))) == []


def pose_tools(frames):
    t = tools({"n": 0})
    inner = t["run"]
    t["run"] = lambda w, v, timeout=0.0: json.dumps(frames) if w == kp.WORKFLOW else inner(w, v, timeout)
    return t


def one_shot(tmp_path, **shot):
    home, board, plan = board28(tmp_path)
    plan["shots"] = [{**plan["shots"][0], **shot}]
    return home, board, plan


def test_an_orphan_wrist_is_an_advisory_panel_fault(tmp_path):
    home, _, plan = one_shot(tmp_path)
    got = panel_eye.judge(home, plan, **pose_tools([frame_of(person(R_WRIST=(0.5, 0.6)))]))
    hit = [f for f in got.faults if f.kind == "orphan_limb"]
    assert len(hit) == 1 and hit[0].severity == "advisory" and hit[0].evidence["calibrated"] is False
    assert got.passed        # advisory: it changes no verdict


def test_a_whole_person_raises_nothing(tmp_path):
    home, _, plan = one_shot(tmp_path)
    whole = person(NOSE=(0.5, 0.2), NECK=(0.5, 0.3), R_SHOULDER=(0.4, 0.3), R_ELBOW=(0.4, 0.5), R_WRIST=(0.4, 0.6))
    got = panel_eye.judge(home, plan, **pose_tools([frame_of(whole)]))
    assert not [f for f in got.faults if f.kind == "orphan_limb"]


def test_extras_declared_and_pose_found_nobody_is_an_orphan(tmp_path):
    home, _, plan = one_shot(tmp_path, extras=2)
    got = panel_eye.judge(home, plan, **pose_tools([frame_of()]))
    assert [f.kind for f in got.faults if f.kind == "orphan_limb"] == ["orphan_limb"]


def test_the_k9_answers_are_advisory_kinds(tmp_path):
    home, board, plan = one_shot(tmp_path)
    rows = [{"shot": 1, "passed": True, "faults": [], "body": "fading", "limb_attached": "floating"}]
    episode_home.write_json(board / "panel_content.json", rows)
    got = panel_eye.judge(home, plan, **tools({"n": 0}))
    kinds = {f.kind: f for f in got.faults}
    assert set(kinds) == {"body", "orphan_limb"} and got.passed
    assert all(f.severity == "advisory" and f.evidence["calibrated"] is False for f in kinds.values())


def test_ok_and_cannot_tell_raise_nothing(tmp_path):
    home, board, plan = one_shot(tmp_path)
    rows = [{"shot": 1, "passed": True, "faults": [], "body": "ok", "limb_attached": "cannot_tell"}]
    episode_home.write_json(board / "panel_content.json", rows)
    assert not panel_eye.judge(home, plan, **tools({"n": 0})).faults


FIXTURE = Path(__file__).parent / "fixtures" / "dq_eval"


def test_the_eval_negatives_raise_no_orphan_when_present():
    import pytest
    pose = sorted(FIXTURE.glob("**/*pose*.json")) if FIXTURE.exists() else []
    if not pose:
        pytest.skip("P06's tests/fixtures/dq_eval has no pose frames yet")
    for path in pose:
        assert kp.orphan_frame(json.loads(path.read_text(encoding="utf-8"))) == [] or "orphan" in path.name
