"""G-LOOK on a TAKE: does the picture keep a black in it for its whole length?

look_gate ran on cells only.  Episode 10 shipped one print (T20: a sunlit wide
with p5 43 and one pixel in a hundred near black) and two takes that went
bright and orange over their length (T16, T28: a push that ends on a face
filling the frame, so the black jamb and the dark side of the face leave with
it) -- all three at 100/100.  This row reads SAMPLES frames of the take with
look_gate's own numbers.

Synthetic frames on tmp_path, no ffmpeg, no repo video, nothing paid.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from studio import look_gate as lg, take_look as tl

SIDE = 96


def warm_over_black(black_share: float, orange_share: float, side: int = SIDE) -> np.ndarray:
    """A frame that is `orange_share` orange, `black_share` black, the rest grey."""
    rgb = np.full((side, side, 3), 110.0)
    rows = int(side * orange_share)
    rgb[:rows] = (210.0, 120.0, 30.0)
    rgb[side - int(side * black_share):] = 0.0
    return rgb.astype(np.uint8)


def lifted(mean: float = 120.0, side: int = SIDE) -> np.ndarray:
    """A mid-grey field with no black in it: a print."""
    rng = np.random.default_rng(2)
    return np.clip(mean + rng.normal(0, 10.0, (side, side, 3)), 40, 255).astype(np.uint8)


def write_frames(frames: list[np.ndarray], folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for k, f in enumerate(frames):
        Image.fromarray(f).save(folder / f"f{k:04d}.png")
    return folder


# ---- the numbers of one frame ------------------------------------------------------

def test_one_frame_is_read_with_look_gates_own_numbers():
    got = tl.stats(warm_over_black(0.5, 0.4).astype(float))
    p5, nb = lg.black_floor(lg.luma(warm_over_black(0.5, 0.4).astype(float)))
    assert got["p5"] == p5 and got["near_black"] == nb
    assert 0.35 <= got["share"] <= 0.45 and got["mean"] > 0


def test_eight_frames_are_spread_over_the_take_first_and_last_included():
    assert tl.sample_indices(158, 8)[0] == 0 and tl.sample_indices(158, 8)[-1] == 157
    assert len(tl.sample_indices(158, 8)) == 8
    assert tl.sample_indices(3, 8) == [0, 1, 2]


# ---- the verdict: pure arithmetic over the take's medians and its ends -------------------

def measured(p5, nb, share, mean, nb_first=None, nb_last=None, share_first=None, share_last=None):
    return {"n": 8, "p5": p5, "near_black": nb, "share": share, "mean": mean,
            "near_black_first": nb if nb_first is None else nb_first,
            "near_black_last": nb if nb_last is None else nb_last,
            "share_first": share if share_first is None else share_first,
            "share_last": share if share_last is None else share_last}


class TestTheWalls:
    """CALIBRATION (docs/calibration/take_look.md, 8 frames per ep10 take):
    T20 median p5 43 / near-black .01 is the one print; T31 1.0 / .68 the
    cleanest take; T16 loses its black .45 -> .18 (hue share .31 -> .75) and
    T28 .66 -> .28 (.39 -> .79); T07 / T13 / T15 darken and are clean."""

    def test_t20_has_no_floor_and_is_hard(self):
        g = tl.verdict(measured(43.3, 0.01, 0.40, 117))
        assert g.name == "look" and g.hard and not g.ok and "no floor" in g.note and g.penalty > 0

    def test_t31_is_clean(self):
        g = tl.verdict(measured(1.0, 0.68, 0.41, 31))
        assert g.ok and not g.hard and g.penalty == 0

    def test_t16_loses_its_black_and_is_a_scored_advisory(self):
        g = tl.verdict(measured(3.0, 0.36, 0.42, 87, nb_first=0.45, nb_last=0.18, share_first=0.31, share_last=0.75))
        assert not g.ok and not g.hard and "black lost" in g.note and g.penalty > 0

    def test_t28_loses_its_black(self):
        g = tl.verdict(measured(0.1, 0.56, 0.51, 38, nb_first=0.66, nb_last=0.28, share_first=0.39, share_last=0.79))
        assert not g.ok and not g.hard

    def test_a_hue_rise_alone_fires(self):
        g = tl.verdict(measured(2.0, 0.50, 0.50, 40, share_first=0.32, share_last=0.60))
        assert not g.ok and "hue" in g.note

    def test_darkening_takes_are_clean(self):
        for nb_first, nb_last in ((0.54, 0.70), (0.39, 0.53), (0.36, 0.50)):    # T07, T13, T15
            assert tl.verdict(measured(1.0, 0.5, 0.35, 45, nb_first=nb_first, nb_last=nb_last)).ok

    def test_a_drop_under_the_wall_is_quiet(self):
        assert tl.verdict(measured(2.0, 0.5, 0.4, 45, nb_first=0.50, nb_last=0.35)).ok

    def test_a_bright_take_with_a_lifted_p5_but_a_floor_is_a_level_advisory(self):
        """ep09's class: median mean 95 / p5 17.8 with near-black kept by a shadow."""
        g = tl.verdict(measured(17.8, 0.12, 0.5, 105))
        assert not g.ok and not g.hard and "level" in g.note

    def test_a_bright_take_with_a_low_p5_is_not_a_level_fault(self):
        assert tl.verdict(measured(6.8, 0.20, 0.38, 103)).ok      # T18's second segment: 103 / 9

    def test_the_walls_are_the_calibrated_numbers(self):
        assert (tl.BLACK_DROP, tl.SHARE_RISE, tl.LEVEL_MEAN) == (0.20, 0.25, 100.0)

    def test_too_few_frames_is_not_measured(self):
        g = tl.verdict({"n": 1})
        assert g.value is None and g.ok and not g.hard and g.note == "not measured"


# ---- the row on a frames folder ------------------------------------------------------

def test_a_take_that_keeps_its_black_passes(tmp_path):
    clip = write_frames([warm_over_black(0.5, 0.4)] * 8, tmp_path / "a")
    g = tl.row(clip, 8 / 24)
    assert g.ok and not g.hard and g.value is not None


def test_a_print_is_hard(tmp_path):
    clip = write_frames([lifted()] * 8, tmp_path / "b")
    assert tl.row(clip, 8 / 24).hard


def test_a_take_that_loses_its_black_is_advisory(tmp_path):
    frames = [warm_over_black(0.6 - 0.05 * k, 0.3 + 0.06 * k) for k in range(8)]     # .60 -> .25, .30 -> .72
    g = tl.row(write_frames(frames, tmp_path / "c"), 8 / 24)
    assert not g.ok and not g.hard and "black lost" in g.note


def test_the_row_reports_its_medians(tmp_path):
    clip = write_frames([warm_over_black(0.5, 0.4)] * 8, tmp_path / "d")
    assert "p5" in tl.row(clip, 8 / 24).note
