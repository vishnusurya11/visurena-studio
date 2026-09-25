"""The stored machine rows (panel_dq.json, panel_content.json) are the judge's
first reads: every failed row becomes a Fault with a kind and a WHERE that
names the panel, never a bare flag."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from studio import episode_home
from studio.judges import panel_eye

FIX = Path(__file__).resolve().parent / "fixtures" / "vlm"
DQ = [{"shot": 1, "passed": True, "flags": []},
      {"shot": 2, "passed": False, "flags": ["clone", "text"], "sharp": 0.9, "ink": 0.012},
      {"shot": 3, "passed": True, "flags": []}]


def _board(tmp_path) -> Path:
    board = tmp_path / "storyboard"
    board.mkdir()
    episode_home.write_json(board / "panel_dq.json", DQ)
    shutil.copy(FIX / "panel_content_rows.json", board / "panel_content.json")
    return board


def test_every_failed_row_is_a_fault_at_its_panel(tmp_path):
    faults = panel_eye.stored_faults(_board(tmp_path))
    assert [(f.kind, f.where) for f in faults] == [
        ("clone", "shot_02"), ("text", "shot_02"),
        ("clones", "shot_02"), ("lettering", "shot_03"), ("unread", "shot_04"),
        ("missing", "shot_05"), ("posture", "shot_05")]
    assert all(re.fullmatch(r"shot_\d\d", f.where) for f in faults)


def test_a_fault_keeps_the_row_it_came_from_as_evidence(tmp_path):
    faults = panel_eye.stored_faults(_board(tmp_path))
    text = next(f for f in faults if f.kind == "text")
    assert text.evidence["ink"] == 0.012 and text.evidence["source"] == "panel_dq"
    unread = next(f for f in faults if f.kind == "unread")
    assert unread.evidence["source"] == "panel_content" and "no JSON" in unread.note


def test_calibrated_rows_refuse_and_thin_rows_say_so(tmp_path):
    faults = {f.kind: f for f in panel_eye.stored_faults(_board(tmp_path))}
    assert faults["clone"].evidence["calibrated"] is True
    assert faults["posture"].evidence["calibrated"] is False


def test_missing_rows_are_no_faults(tmp_path):
    board = tmp_path / "storyboard"
    board.mkdir()
    assert panel_eye.stored_faults(board) == []
    episode_home.write_json(board / "panel_dq.json", json.loads("[]"))
    assert panel_eye.stored_faults(board) == []
