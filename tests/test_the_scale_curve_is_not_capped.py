"""The camera record's scale curve reads past 1.25x.

Jekyll ep01 (2026-10-13, MOTION.md cause 5): `camera_dq` measured every frame
against frame 0 on `cell_scale`'s 0.80-1.26 search grid, so T13's 2.5x push and
T14's 4.75x push both read 1.25 and the record could not tell them from a
hand's breadth.  The curve is now the product of quarter-second steps, each
well inside the grid.  And `camera_ok` was a stillness meter wearing a camera
verdict's name: it is `still_ok` now, and the verdict is the camera-move row.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("take_dq_curve", ROOT / "scripts" / "episode" / "take_dq.py")
take_dq = importlib.util.module_from_spec(spec)
sys.modules["take_dq_curve"] = take_dq
spec.loader.exec_module(take_dq)


def test_steps_compound_past_the_grid():
    curve = take_dq.compound_curve([1.2] * 8)
    assert curve[0] == 1.0 and curve[-1] > 4.0


def test_a_pull_compounds_down():
    assert take_dq.compound_curve([0.9] * 10)[-1] < 0.4


def test_a_still_camera_stays_at_one():
    assert take_dq.compound_curve([1.0] * 5) == [1.0] * 6


def test_the_stillness_meter_is_named_for_what_it_is():
    said = (ROOT / "scripts" / "episode" / "take_dq.py").read_text(encoding="utf-8")
    assert '"still_ok"' in said and '"camera_ok"' not in said
