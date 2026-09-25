"""The hat and landmark measures need a SCORED open-vocabulary detector.  The
installed box workflow returns a mask for any word (measured: 225 "bridge"
boxes on one panel), so until `SCORED_BOXES` is true the judge must not ask it:
no GPU job, no fault, and the panel still gets its other reads."""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

from studio.judges import panel_eye
from studio.measure import boxes


def test_the_judge_never_asks_the_box_workflow_while_boxes_are_unscored(tmp_path):
    board = tmp_path / "storyboard"
    board.mkdir()
    Image.new("RGB", (64, 64), (120, 120, 120)).save(board / "shot_01.png")
    asked = []

    def run(name, values, timeout=None):
        asked.append(name)
        if name == boxes.WORKFLOW:
            raise AssertionError("the box workflow was asked while SCORED_BOXES is False")
        if name == panel_eye.CAPTION:
            return json.dumps({"size": "wide", "pictures": 1})
        return "[]"                                   # keypoints: nobody found

    plan = {"setups": {"s": {"described": "a field"}},
            "shots": [{"index": 1, "setup": "s", "size": "wide", "faces": ["a"], "frame": "a man stands"}]}
    assert panel_eye.SCORED_BOXES is False
    verdict = panel_eye.judge(tmp_path, plan, run=run, stage=lambda p: str(p), reader=lambda p: [],
                              detect=lambda rgb: [], embed=lambda rgb, box: np.zeros(4))
    assert boxes.WORKFLOW not in asked
    assert not any(f.kind in ("hat", "landmark") for f in verdict.faults)
    assert verdict.reads == 1
