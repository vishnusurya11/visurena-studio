"""F6 (ep10 synthesis): a cut the model places lands on the token grid; the
ledger reads it at that frame and says how late it is, never "missing".

Episode 10 cut 22: planned 120.667 (take frame 74), the pin snapped forward to
grid_frame(74) = 77, the model obeyed it to the frame, and the 3-frame snap is
0.125 s -- 5 ms past CUT_TOLERANCE -- so qc reported "missing 1/33" on a hard
cut of ordinary strength. Also the speech-gap wall: ep09 3.25 s passes, ep10's
11.25 s wordless tail fails.
"""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "ep_qc_grid", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "qc.py")
qc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qc)

GOOD = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [{"passed": True}],
        "edit": {"ok": True, "measured": True}}


def test_a_cut_on_the_grid_is_late_not_missing():
    row = qc.grid_cut(planned=120.667, take_frame=74, seen=[120.792])
    assert row["on_grid"] is True and row["late_frames"] == 3
    assert row["grid_frame"] == 77 and row["missing"] is False


def test_a_cut_the_picture_does_not_show_at_its_grid_frame_is_still_missing():
    row = qc.grid_cut(planned=120.667, take_frame=74, seen=[125.0])
    assert row["missing"] is True and row["on_grid"] is False and row["late_frames"] is None


def test_a_cut_exactly_at_its_planned_frame_is_on_the_grid_with_no_lateness():
    # take frame 85 = grid_frame(85): block 5, k 0
    row = qc.grid_cut(planned=103.292, take_frame=85, seen=[103.292])
    assert row["on_grid"] is True and row["late_frames"] == 0


def test_the_tolerance_for_edit_made_cuts_is_unchanged():
    assert qc.CUT_TOLERANCE == 0.12
    assert qc.missing_cuts([120.667], [120.792]) == [120.667], "an edit-made cut 0.125 s off IS off"


def test_internal_rows_take_the_take_frame_from_the_runs_first_shot():
    placed = {"shots": [{"index": 21, "t_start": 117.583333}, {"index": 22, "t_start": 120.666667},
                        {"index": 23, "t_start": 125.125}]}
    records = [{"index": 21, "shots": [21, 22]}, {"index": 23, "shots": [23]}]
    (row,) = qc.internal_cut_rows(placed, records, seen=[120.792, 125.125])
    assert row["at"] == pytest.approx(120.666667) and row["take_frame"] == 74
    assert row["on_grid"] is True and row["late_frames"] == 3


def test_a_cut_on_the_grid_leaves_the_missing_list():
    rows = [{"at": 120.666667, "on_grid": True}, {"at": 158.083333, "on_grid": False}]
    assert qc.drop_on_grid([120.666667, 158.083333], rows) == [158.083333]


def test_the_speech_gap_wall_is_six_seconds():
    assert qc.MAX_GAP_S == 6.0
    assert qc.verdict({**GOOD, "longest_gap_s": 3.25}), "ep09"
    assert not qc.verdict({**GOOD, "longest_gap_s": 11.25}), "ep10"
    assert qc.verdict({**GOOD, "longest_gap_s": 6.0})
