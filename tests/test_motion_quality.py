"""Is an H3 take smooth -- neither blurred nor warping -- frame to frame?"""
import numpy as np

from studio.motion_quality import (blur_dips, flow_incoherence, sharpness,
                                   summarise)


def _checker(shift=0):
    y, x = np.mgrid[0:64, 0:64]
    return (((x + shift) // 8 + y // 8) % 2 * 255).astype(np.uint8)


def test_a_sharp_frame_scores_higher_than_its_blur():
    import cv2
    sharp = _checker()
    assert sharpness(sharp) > 4 * sharpness(cv2.GaussianBlur(sharp, (9, 9), 3))


def test_blur_dips_names_frames_far_below_the_takes_own_median():
    series = [100.0] * 20
    series[7] = 20.0
    series[8] = 25.0
    assert blur_dips(series, floor=0.5) == [7, 8]
    assert blur_dips([100.0] * 20, floor=0.5) == []


def test_a_uniform_shift_is_coherent_and_a_scramble_is_not():
    a = _checker()
    shifted = flow_incoherence(a, _checker(shift=2))
    rng = np.random.default_rng(0)
    scrambled = flow_incoherence(a, rng.integers(0, 256, a.shape, dtype=np.uint8))
    assert shifted < scrambled


def test_summarise_reports_the_dip_count_and_the_worst_warp():
    out = summarise(sharp=[100.0, 100.0, 30.0, 100.0], warp=[0.1, 0.9, 0.2])
    assert out["blur_dips"] == 1 and out["warp_max"] == 0.9
    assert out["sharp_min_ratio"] == 0.3


def test_flags_name_blur_and_a_late_reframe_and_nothing_else():
    from studio.motion_quality import flags
    assert flags({"blur_dips": 6, "sharp_min_ratio": 0.45, "warp_max": 1.0}) == ["BLUR"]
    assert flags({"blur_dips": 0, "sharp_min_ratio": 0.9, "warp_max": 1.58}) == ["REFRAME"]
    assert flags({"blur_dips": 0, "sharp_min_ratio": 0.9, "warp_max": 1.2}) == []
