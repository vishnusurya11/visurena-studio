"""G-FRAME: a measurement only, advisory (C2_verdict #8).

85 planned medium-close panels over 16 WotW episodes have a median face_h of
0.207 against about 0.30 the cut words ask for: a tight size is drawn a size
wide.  panel_dq records the drawn face height against the planned size for every
faced, non-back panel, and flags an MCU < 0.22 or a close < 0.32.  The floors
are UNCALIBRATED and the MCU floor sits ABOVE today's median, so the flag can
never refuse a panel, climb a ladder or reach a terminal."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from studio import panel_dq

ROOT = Path(__file__).resolve().parents[1]


def face(h: float, score: float = 0.9) -> dict:
    return {"h": h, "score": score}


def test_an_mcu_drawn_wide_is_flagged_and_a_close_at_its_size_is_not():
    got = panel_dq.frame_record([face(0.18)], planned=1, size="medium_close", prose="")
    assert got["face_h"] == 0.18 and got["planned_size"] == "medium_close" and got["frame_advisory"]
    assert "uncalibrated" in got["frame_note"]
    assert not panel_dq.frame_record([face(0.35)], 1, "close", "")["frame_advisory"]
    assert panel_dq.frame_record([face(0.30)], 1, "close", "")["frame_advisory"]


def test_the_tallest_present_face_is_the_measure():
    got = panel_dq.frame_record([face(0.31), face(0.12), face(0.5, score=0.5)], 1, "medium_close", "")
    assert got["face_h"] == 0.31 and not got["frame_advisory"]


def test_no_record_for_a_back_view_an_uncast_panel_or_a_wide():
    assert panel_dq.frame_record([face(0.1)], 1, "medium_close", "Medium close from behind the narrator") == {}
    assert panel_dq.frame_record([face(0.1)], 0, "medium_close", "") == {}
    assert panel_dq.frame_record([face(0.05)], 1, "medium", "") == {"face_h": 0.05, "planned_size": "medium",
                                                                      "frame_advisory": False}


def test_a_faced_panel_with_no_face_found_records_none_and_flags_nothing():
    assert panel_dq.frame_record([], 1, "close", "") == {"face_h": None, "planned_size": "close",
                                                         "frame_advisory": False}


def test_an_advisory_cannot_fail_a_panel_or_climb_its_ladder(monkeypatch):
    spec = importlib.util.spec_from_file_location("panel_check_gframe", ROOT / "scripts" / "episode" / "panel_check.py")
    pc = importlib.util.module_from_spec(spec)
    sys.modules["panel_check_gframe"] = pc
    spec.loader.exec_module(pc)
    monkeypatch.setattr(pc.face_end, "faces", lambda frame: [face(0.15)])
    shot = SimpleNamespace(index=4, faces=["narrator"], size="medium_close", extras=0,
                           frame="Medium close of the narrator", at_rest="")
    setup = SimpleNamespace(described="a study by day", crowd="")
    frame = np.full((256, 256, 3), 128, np.uint8)
    frame[::8] = 0                                                     # some edges, so it is not soft
    row = pc.judge(shot, setup, frame, {"day": 1e-6, "night": 1e-6})
    assert row["frame_advisory"] is True
    assert "frame" not in " ".join(row["flags"]) and row["passed"] == (not row["flags"])
