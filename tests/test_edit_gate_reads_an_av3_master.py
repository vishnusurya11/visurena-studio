"""The edit gate reads a denoised, upscaled (av3) master as its takes.

MEASURED on Jekyll ep01 (qc_r2v.json, copied to the fixture): hqdn3d temporal
denoise plus x4 upscale lifted T01/T11/T12 to 2.02-2.10 against the 2.0 cap and
made 3-frame near-repeats the take does not have (T13/T15/T19/T23).  Cuts were
27/27 exact, no pts holes, offset 0 on all 28: no wrong edit.  A real hold or a
swapped take still fails."""
import json
from pathlib import Path

import numpy as np

from studio import edit_gate as eg

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "C1-qc-edit-gate-av3" / "edit_segments.json"


def test_av3_has_its_own_cap_and_hold_run():
    assert eg.segment_cap("av3") == eg.SEGMENT_MEAN_AV3 > 2.102
    assert eg.hold_least("av3") == eg.HOLD_FRAMES_DENOISED > 3
    assert eg.hold_least("rtx4x") == eg.hold_least("") == eg.HOLD_FRAMES


def test_ep01_replay_has_no_off_segment_under_av3():
    rows = json.loads(FIX.read_text(encoding="utf-8"))["segments"]
    assert sum(not r["ok"] for r in rows) == 7
    off = [r["take"] for r in rows if not eg.segment_ok(r, eg.segment_cap("av3"), eg.hold_least("av3"))]
    assert off == []


def test_the_same_rows_still_fail_under_the_old_rule():
    rows = json.loads(FIX.read_text(encoding="utf-8"))["segments"]
    assert [r for r in rows if not eg.segment_ok(r, eg.SEGMENT_MEAN_RTX, eg.HOLD_FRAMES)]


def test_a_swapped_take_row_fails_under_av3():
    row = {"offset": 0, "mean": 40.0, "frames_off": list(range(50)), "held": [], "flat": False}
    assert not eg.segment_ok(row, eg.segment_cap("av3"), eg.hold_least("av3"))


def test_a_real_hold_fails_under_av3_and_a_denoise_pair_does_not():
    take = np.stack([np.full((8, 8), 60 + 8 * k, np.uint8) for k in range(20)])
    held = np.concatenate([take[:6], np.repeat(take[5:6], 8, axis=0), take[6:10]])
    assert not eg.segment_match(held, take, 0, 18, cap=2.5, hold=eg.hold_least("av3"))["ok"]
    pair = np.concatenate([take[:6], np.repeat(take[5:6], 3, axis=0), take[6:10]])
    assert eg.segment_match(pair, take, 0, 13, cap=eg.SEGMENT_MEAN_AV3, hold=eg.hold_least("av3"))["held"] == []
