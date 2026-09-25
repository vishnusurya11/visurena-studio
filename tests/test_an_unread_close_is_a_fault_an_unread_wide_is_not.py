"""The one short VLM read per panel (size, pictures) is parsed into a closed
vocabulary and a malformed answer raises Unreadable -- never a default.  A
panel the reader could not read is a fault when the face IS the picture (a
close) and not when it is a wide; either way it counts against confidence."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from studio import episode_home
from studio.judges import panel_eye

FIX = Path(__file__).resolve().parent / "fixtures" / "vlm"
READS = json.loads((FIX / "size_reads.json").read_text(encoding="utf-8"))


def test_a_malformed_answer_raises_unreadable():
    with pytest.raises(panel_eye.Unreadable):
        panel_eye.parse_size(READS["shot_03"])
    with pytest.raises(panel_eye.Unreadable, match="size"):
        panel_eye.parse_size(READS["shot_05"])


def test_a_wrapped_answer_is_unwrapped_and_a_plain_one_read():
    assert panel_eye.parse_size(READS["shot_01"]) == {"size": "close", "pictures": 1}
    assert panel_eye.parse_size(READS["shot_02"]) == {"size": "wide", "pictures": 1}
    assert panel_eye.parse_size(READS["shot_04"]) == {"size": "medium", "pictures": 2}


def home_with(tmp_path, sizes: dict[int, str]) -> tuple[Path, dict]:
    board = tmp_path / "storyboard"
    board.mkdir()
    for i in sizes:
        Image.new("RGB", (64, 64), (i * 30, 40, 40)).save(board / f"shot_{i:02d}.png")
    rows = [{"shot": i, "passed": True, "flags": [], "faults": []} for i in sizes]
    episode_home.write_json(board / "panel_dq.json", rows)
    episode_home.write_json(board / "panel_content.json", rows)
    plan = {"setups": {"s": {"described": "a yard"}},
            "shots": [{"index": i, "setup": "s", "size": size, "faces": ["a_man"], "frame": "a man stands"}
                      for i, size in sizes.items()]}
    return tmp_path, plan


def fake_run(answers: dict[str, str]):
    def run(workflow, values, timeout=0.0):
        if workflow == panel_eye.CAPTION:
            return answers[values["image_1"]]
        return "[]"
    return run


def tools(answers):
    return dict(run=fake_run(answers), stage=lambda p: Path(p).stem, reader=lambda p: [],
                detect=lambda rgb: [], embed=lambda rgb, box: None)


def test_an_unread_close_is_a_fault_an_unread_wide_is_not(tmp_path):
    home, plan = home_with(tmp_path, {1: "close", 2: "wide"})
    bad = {"shot_01": READS["shot_03"], "shot_02": READS["shot_03"]}
    verdict = panel_eye.judge(home, plan, **tools(bad))
    assert [(f.kind, f.where) for f in verdict.faults] == [("unread", "shot_01")]
    assert not verdict.passed and verdict.reads == 2 and verdict.confidence == 0.0


def test_a_read_wide_and_an_unread_wide_pass_with_half_confidence(tmp_path):
    home, plan = home_with(tmp_path, {1: "wide", 2: "wide"})
    verdict = panel_eye.judge(home, plan, **tools({"shot_01": READS["shot_02"], "shot_02": READS["shot_03"]}))
    assert verdict.passed and verdict.faults == []
    assert verdict.reads == 2 and verdict.confidence == 0.5
