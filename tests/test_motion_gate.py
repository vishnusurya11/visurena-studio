"""Is the picture alive?  Synthetic frames pin the arithmetic; the calibration
numbers in the assertions come from review8/motion_gate.md (63 H3 takes,
iterations 2-4).  Nothing here decodes a real take, spends, or touches the GPU.
"""
from types import SimpleNamespace

import numpy as np

from studio import motion_gate as mg


def still(n: int, seed: int = 0) -> np.ndarray:
    """n copies of one noisy frame: a pinned still."""
    base = np.random.default_rng(seed).integers(0, 255, (336, 192)).astype(np.float32)
    return np.repeat(base[None], n, axis=0)


def test_identical_frames_have_zero_energy():
    assert mg.block_max(still(10)).max() == 0.0
    assert mg.block_max(still(1)).shape == (0,)


def test_lips_moving_in_one_block_register_while_the_frame_wide_mean_does_not():
    fr = still(25)
    for i in range(1, 25):
        fr[i, 192:216, 96:120] = 255 * (i % 2)                    # one 24x24 block flickers: a mouth
    e = mg.block_max(fr)
    assert e.min() > 100                                          # the block sees it
    assert np.abs(fr[1:] - fr[:-1]).mean(axis=(1, 2)).max() < 3   # the frame-wide mean barely does


def test_the_still_floor_is_the_calibrated_gap():
    """MEASURED on 63 takes: pinned still 0.2-0.7, a drift the eye reads as still
    0.8-1.1, a living hold at rest 1.8-3.0.  STILL sits in the gap."""
    assert mg.STILL == 1.2
    assert mg.START_LIMIT_S == 1.0 and mg.GRACE_S == 0.5


def test_leading_still_counts_bins_until_the_first_that_moves():
    assert mg.leading_still_s([0.3, 0.5, 0.9, 1.1, 5.0, 0.2]) == 1.0
    assert mg.leading_still_s([2.0, 2.0, 2.0, 0.1]) == 0.0       # moved 0.75 s first: not a still start
    assert mg.leading_still_s([0.1] * 8) == 2.0
    assert mg.leading_still_s([]) == 0.0


def test_a_settle_twitch_in_the_first_half_second_does_not_hide_a_still_start():
    """T17 iteration 4, segment 0: one bin at 1.4, then 0.3-0.7 for 4.75 s."""
    assert mg.leading_still_s([1.4] + [0.5] * 19) == 4.75
    assert mg.leading_still_s([1.4, 1.6] + [0.5] * 4) == 1.0


def test_still_share_and_spans():
    bins = [0.1, 0.2, 0.3, 4.0, 4.0, 0.1, 0.1, 0.1, 0.1, 3.0]
    assert mg.still_share(bins) == 0.7
    assert mg.frozen_spans(bins) == [(0.0, 0.75), (1.25, 2.25)]
    assert mg.still_share([]) == 0.0


def test_bins_are_quarter_seconds_and_drop_a_sliver():
    e = np.array([1.0] * 6 + [2.0] * 6 + [9.0] * 2)              # 14 steps: two full bins and a 2-step sliver
    assert mg.bin_means(e) == [1.0, 2.0]
    assert mg.bin_means(np.array([1.0] * 6 + [3.0] * 3)) == [1.0, 3.0]   # a half bin counts


def test_segments_come_from_start_pins_only():
    anchors = [("Q17_0.png", 0), ("Q17_1.png", 121), ("Q17_2.png", 213),
               ("Q17_0.png", 117), ("Q17_1E.png", 209), ("Q17_2.png", 357)]
    assert mg.segments(anchors, 362) == [("Q17_0.png", 0, 121), ("Q17_1.png", 121, 213), ("Q17_2.png", 213, 362)]


def test_kind_of_a_segment():
    lines = [SimpleNamespace(kind="dialogue", shot=15), SimpleNamespace(kind="narration", shot=14)]
    assert mg.kind_of(SimpleNamespace(index=15, size="medium_close", motion="Static shot; he speaks"), lines) == "dialogue"
    assert mg.kind_of(SimpleNamespace(index=9, size="medium", motion="Tracking behind at walking pace"), lines) == "track"
    assert mg.kind_of(SimpleNamespace(index=14, size="insert", motion="Static shot; the collar rises"), lines) == "insert"
    assert mg.kind_of(SimpleNamespace(index=16, size="medium_close", motion="Static shot; lips stay closed"), lines) == "hold"
    assert mg.shot_of("Q17_2.png") == 17


def test_segment_verdict_gates_the_start_and_advises_the_share():
    v = mg.segment_verdict([0.2] * 5 + [4.0] * 3, "hold")
    assert v["leading_still_s"] == 1.25 and not v["start_ok"]
    assert v["still_share"] == 0.625 and not v["share_ok"]
    v = mg.segment_verdict([0.2] * 4 + [4.0] * 12, "hold")
    assert v["start_ok"] and v["share_ok"]


def test_share_ceilings_are_per_kind():
    """MEASURED per-kind over 136 segments (review8/motion_gate/calib.json)."""
    assert mg.SHARE_CEILING == {"dialogue": 0.20, "hold": 0.35, "insert": 0.50, "track": 0.10}
    assert mg.segment_verdict([0.2] * 5 + [4.0] * 15, "track")["share_ok"] is False
    assert mg.segment_verdict([0.2] * 5 + [4.0] * 15, "insert")["share_ok"] is True


def test_report_from_energy_is_the_verdict_without_a_decoder():
    """The same report motion_dq builds, fed the energy directly: no ffmpeg, no take."""
    energy = np.concatenate([np.full(48, 0.3), np.full(48, 6.0)])   # 2 s frozen, then 2 s alive
    r = mg.report(energy, [("Q05_0.png", 0)], {})
    assert not r["motion_ok"] and r["worst_leading_still_s"] == 2.0
    assert r["still_share"] == 0.5 and r["frozen_spans"] == [(0.0, 2.0)]
    alive = mg.report(np.full(96, 6.0), [("Q05_0.png", 0)], {})
    assert alive["motion_ok"] and alive["share_ok"] and alive["frozen_spans"] == []


def test_best_attempt_prefers_a_pass_then_the_shorter_start_freeze():
    a = {"foreign": 0, "audio": {"lag_ok": True, "lag_s": 0.0},
         "motion": {"motion_ok": False, "worst_leading_still_s": 5.0, "still_share": 0.9}}
    b = {"foreign": 0, "audio": {"lag_ok": True, "lag_s": 0.01},
         "motion": {"motion_ok": True, "worst_leading_still_s": 0.5, "still_share": 0.3}}
    c = {"foreign": 1, "audio": {"lag_ok": True, "lag_s": 0.0},
         "motion": {"motion_ok": True, "worst_leading_still_s": 0.0, "still_share": 0.1}}
    assert mg.best_attempt({"T17.mp4": a, "T17_fail1.mp4": b, "x": c}) == "T17_fail1.mp4"
    assert mg.attempt_score(c)[0] == 1                            # a foreign frame fails the hard gates
