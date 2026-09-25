"""Framing has no owner-labelled positive yet, so the VLM's size read is a
second vote and never the wall: alone it refuses nothing; with the keypoint
measure two steps off as well, the pair is a framing fault; the keypoint
measure alone is advisory (listed, never a refusal)."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from studio import episode_home
from studio.judges import panel_eye
from studio.measure import keypoints

FIX = Path(__file__).resolve().parent / "fixtures"
DWPOSE = {name: (FIX / "measures" / f"dwpose_{name}.json").read_text(encoding="utf-8")
          for name in ("standing", "medium_close")}


def home_with(tmp_path, planned: str = "close"):
    board = tmp_path / "storyboard"
    board.mkdir()
    Image.new("RGB", (64, 64), (60, 60, 60)).save(board / "shot_01.png")
    rows = [{"shot": 1, "passed": True, "flags": [], "faults": []}]
    episode_home.write_json(board / "panel_dq.json", rows)
    episode_home.write_json(board / "panel_content.json", rows)
    return tmp_path, {"setups": {"s": {"described": "a room"}},
                      "shots": [{"index": 1, "setup": "s", "size": planned, "faces": ["a_man"], "frame": "a man"}]}


def tools(read_size: str, pose: str):
    def run(workflow, values, timeout=0.0):
        if workflow == panel_eye.CAPTION:
            return json.dumps({"size": read_size, "pictures": 1})
        if workflow == keypoints.WORKFLOW:
            return DWPOSE[pose]
        return "[]"
    return dict(run=run, stage=lambda p: Path(p).stem, reader=lambda p: [],
                detect=lambda rgb: [], embed=lambda rgb, box: None)


def framing(verdict):
    return [f for f in verdict.faults if f.kind == "framing"]


def test_the_read_alone_is_never_the_wall(tmp_path):
    home, plan = home_with(tmp_path, "close")
    verdict = panel_eye.judge(home, plan, **tools("wide", "medium_close"))
    assert verdict.passed and framing(verdict) == []


def test_two_votes_two_steps_off_are_a_framing_fault(tmp_path):
    home, plan = home_with(tmp_path, "close")
    verdict = panel_eye.judge(home, plan, **tools("wide", "standing"))
    assert not verdict.passed
    fault = framing(verdict)[0]
    assert fault.where == "shot_01" and fault.severity == "normal"
    assert fault.evidence == {"planned": "close", "keypoints": "full", "read": "wide", "calibrated": False}


def test_the_keypoint_vote_alone_is_advisory(tmp_path):
    home, plan = home_with(tmp_path, "close")
    verdict = panel_eye.judge(home, plan, **tools("close", "standing"))
    assert verdict.passed
    assert [f.severity for f in framing(verdict)] == ["advisory"]
