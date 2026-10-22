"""A DWPose answer that is not JSON is a missing measure, never a crash of the panel judge.

Rehearsal window 3 (2026-10-21): step 08 died on `json.decoder.JSONDecodeError` in
`keypoints.parse` when the engine answered the keypoint workflow with plain text, so the whole
judge (and the drive) fell over where `asked` promises "an unreadable answer is a missing
measure".  The keypoint read now raises Unreadable, which `asked` already counts and skips."""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from studio import episode_home
from studio.judges import panel_eye

TEXT = "[rehearsal canned reply: no recording matched this read]"


def test_a_keypoint_answer_that_is_not_json_raises_unreadable():
    with pytest.raises(panel_eye.Unreadable, match="keypoints"):
        panel_eye.keypoint_frames("shot_01", lambda workflow, values, timeout=0.0: TEXT)
    with pytest.raises(panel_eye.Unreadable):
        panel_eye.keypoint_frames("shot_01", lambda workflow, values, timeout=0.0: "")


def test_a_keypoint_answer_that_is_json_is_still_read():
    frames = panel_eye.keypoint_frames("shot_01", lambda workflow, values, timeout=0.0: '[{"people": []}]')
    assert frames == [{"people": []}]


def home_with(tmp_path: Path) -> tuple[Path, dict]:
    board = tmp_path / "storyboard"
    board.mkdir()
    Image.new("RGB", (64, 64), (30, 40, 40)).save(board / "shot_01.png")
    rows = [{"shot": 1, "passed": True, "flags": [], "faults": []}]
    episode_home.write_json(board / "panel_dq.json", rows)
    episode_home.write_json(board / "panel_content.json", rows)
    plan = {"setups": {"s": {"described": "a yard"}},
            "shots": [{"index": 1, "setup": "s", "size": "close", "faces": ["a_man"], "frame": "a man stands"}]}
    return tmp_path, plan


def test_a_judge_whose_every_answer_is_plain_text_ends_with_the_panel_unread(tmp_path):
    home, plan = home_with(tmp_path)
    verdict = panel_eye.judge(home, plan, run=lambda workflow, values, timeout=0.0: TEXT,
                              stage=lambda p: Path(p).stem, reader=lambda p: [],
                              detect=lambda rgb: [], embed=lambda rgb, box: None)
    assert [(f.kind, f.where) for f in verdict.faults] == [("unread", "shot_01")] and not verdict.passed
