"""Jekyll ep05 repair (2026-10-28): QC refused the judged cut on `edit` for T11 (mean 2.40) and T14
(1.96) against SEGMENT_MEAN_CUT 1.95, fitted on ep03/ep04 alone. Measured: every frame of T11 sat
2.40-2.52 from its take (spread 0.19, the cut's passing segments 0.07-0.77), offset 0 was best and
one frame either way read 3.18/3.20 (T14: 2.47/2.57). The picture IS the take; the noise follows
the picture's detail and brightness (T11 grey mean 104 against 31-49).

A segment whose offset-0 mean is clearly under both one-frame shifts (CLEAR, ratio) is its take;
the walls that catch a wrong frame -- offset, a frame over SAME_FRAME, a held run -- are unchanged."""
import numpy as np

from studio import edit_gate as eg


def row(mean, shifts, offset=0, frames_off=(), held=()):
    return {"offset": offset, "mean": mean, "frames_off": list(frames_off), "held": list(held),
            "flat": False, "shifts": list(shifts)}


def test_t11_is_its_take():
    assert eg.segment_ok(row(2.40, [3.18, 3.20]), eg.SEGMENT_MEAN_CUT)


def test_t14_is_its_take():
    assert eg.segment_ok(row(1.96, [2.47, 2.57]), eg.SEGMENT_MEAN_CUT)


def test_a_mean_no_better_than_a_shift_still_fails():
    assert not eg.segment_ok(row(2.40, [2.50, 2.60]), eg.SEGMENT_MEAN_CUT)


def test_a_frame_of_another_picture_still_fails():
    assert not eg.segment_ok(row(2.40, [3.18, 3.20], frames_off=[17]), eg.SEGMENT_MEAN_CUT)


def test_an_offset_still_fails():
    assert not eg.segment_ok(row(2.40, [3.18, 3.20], offset=1), eg.SEGMENT_MEAN_CUT)


def test_segment_match_records_the_shifts():
    rng = np.random.default_rng(0)
    take = rng.integers(0, 255, (12, eg.GREY_H, eg.GREY_W)).astype(np.float32)
    got = eg.segment_match(take + 2.0, take, 0, 12, cap=eg.SEGMENT_MEAN_CUT)
    assert len(got["shifts"]) == 2 and min(got["shifts"]) > got["mean"]


def test_a_clear_segment_far_over_the_cap_is_a_regrade_and_fails():
    """CLEAR forgives noise just over the cap (T11 sat 1.23x it), never a picture regraded past it:
    a uniform +3 on every frame beats both shifts and is still not the take's grade."""
    assert not eg.segment_ok(row(eg.SEGMENT_MEAN_CUT * 1.5, [9.0, 9.0]), eg.SEGMENT_MEAN_CUT)
    assert eg.segment_ok(row(eg.SEGMENT_MEAN_CUT * 1.25, [9.0, 9.0]), eg.SEGMENT_MEAN_CUT)
