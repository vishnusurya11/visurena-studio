"""A keypoint read that fails is on the verdict's record, never a silent pass.

Window 3 review (2026-10-21): after 55588d7 a non-JSON DWPose answer left `frames` empty, so the
posture, keypoint-framing and orphan rows were dropped without a word -- a wide or full panel
signed `passed=True, faults=[]`, the `failed` count never reached the evidence, and confidence
counted only the short read.  A broken DWPose workflow would sign EYE_PANELS on every non-close
panel.  JSON of the wrong shape (`["text"]`, a 2-number keypoint list) still crashed the judge."""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from studio import episode_home, panel_ladder
from studio.judges import panel_eye
from studio.measure import keypoints

TEXT = "[rehearsal canned reply: no recording matched this read]"
SIZE = '{"size": "wide", "pictures": 1}'


def answers(keypoint_answer: str):
    """A run whose keypoint ask answers `keypoint_answer` and whose short read answers a wide."""
    return lambda workflow, values, timeout=0.0: keypoint_answer if workflow == keypoints.WORKFLOW else SIZE


def home_with(tmp_path: Path, size: str, frame: str) -> tuple[Path, dict]:
    board = tmp_path / "storyboard"
    board.mkdir()
    Image.new("RGB", (64, 64), (30, 40, 40)).save(board / "shot_01.png")
    rows = [{"shot": 1, "passed": True, "flags": [], "faults": []}]
    episode_home.write_json(board / "panel_dq.json", rows)
    episode_home.write_json(board / "panel_content.json", rows)
    plan = {"setups": {"s": {"described": "a yard"}},
            "shots": [{"index": 1, "setup": "s", "size": size, "faces": ["a_man"], "frame": frame}]}
    return tmp_path, plan


def judged(tmp_path: Path, size: str, frame: str, keypoint_answer: str = TEXT):
    home, plan = home_with(tmp_path, size, frame)
    return panel_eye.judge(home, plan, run=answers(keypoint_answer), stage=lambda p: Path(p).stem,
                           reader=lambda p: [], detect=lambda rgb: [], embed=lambda rgb, box: None)


@pytest.mark.parametrize("size,frame", [("wide", "a man lies on the ground"), ("full", "a man sits on a bench")])
def test_a_panel_whose_keypoints_went_unread_carries_an_advisory_that_says_so(tmp_path, size, frame):
    verdict = judged(tmp_path, size, frame)
    hit = [f for f in verdict.faults if f.kind == panel_eye.KEYPOINTS_UNREAD]
    assert [(f.where, f.severity) for f in hit] == [("shot_01", "advisory")]
    assert "posture" in hit[0].note and "framing" in hit[0].note


def test_the_failed_asks_reach_the_evidence_and_count_against_confidence(tmp_path):
    verdict = judged(tmp_path, "wide", "a man lies on the ground")
    assert verdict.evidence["failed"] == 1 and verdict.confidence == 0.0


def test_a_panel_whose_keypoints_were_read_has_no_unread_advisory(tmp_path):
    verdict = judged(tmp_path, "wide", "a man lies on the ground", keypoint_answer='[{"people": []}]')
    assert not [f for f in verdict.faults if f.kind == panel_eye.KEYPOINTS_UNREAD]
    assert verdict.evidence["failed"] == 0 and verdict.confidence == 1.0


@pytest.mark.parametrize("said", ['["text"]', '{"people": [{"pose_keypoints_2d": [1, 2]}]}', '[{"people": "x"}]'])
def test_json_of_the_wrong_shape_is_unreadable_never_a_crash(said):
    with pytest.raises(panel_eye.Unreadable, match="keypoints"):
        panel_eye.keypoint_frames("shot_01", lambda workflow, values, timeout=0.0: said)


def test_a_redraw_cannot_cure_a_measure_that_went_unread():
    assert panel_eye.KEYPOINTS_UNREAD in panel_ladder.REDRAW_CANNOT_CURE
