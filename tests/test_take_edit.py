"""G-EDIT: two things the cut detector surfaced on episode 10 that no row saw.

post-cut  The edit trims 6-22 frames off every take (HANDLE + the token grid).
          T28 collapsed two frames past its cut (placed tail mean 4.06, the
          trimmed remainder 8.55 with every frame over 8) and T29 1.45 -> 5.07:
          a take at its edge inside the cut.  ep05 and ep07: none.
pulse     T05 breathes: a ~22-frame period in luminance and motion over six
          cycles, peaks 10-14 against a baseline of 1-3.  Churn averaged it
          to 3.5, zoom netted it to 0.99x, score 100.

Both advisory.  Everything here is synthetic on tmp_path: no ffmpeg, no repo
video, nothing paid.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from studio import take_edit as te


def textured(seed: int, side: int = 64) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, 255, (side, side)).astype(np.uint8)


def write_frames(frames: np.ndarray, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for k, f in enumerate(frames):
        Image.fromarray(f).save(folder / f"f{k:04d}.png")
    return folder


def drifting(n: int, step: float, seed: int = 1) -> np.ndarray:
    """n frames of a textured picture drifting by `step` levels of noise per frame."""
    rng = np.random.default_rng(seed)
    out, cur = [], textured(seed).astype(float)
    for _ in range(n):
        cur = np.clip(cur + rng.normal(0, step, cur.shape), 0, 255)
        out.append(cur.astype(np.uint8))
    return np.stack(out)


# ---- the series ----------------------------------------------------------------------

def test_the_series_is_the_mean_absolute_frame_step():
    fr = np.stack([np.zeros((4, 4)), np.full((4, 4), 3.0), np.full((4, 4), 3.0)]).astype(np.float32)
    assert te.diff_series(fr).tolist() == [3.0, 0.0]


def test_one_frame_has_no_series():
    assert te.diff_series(np.zeros((1, 4, 4), np.float32)).size == 0


# ---- post-cut ------------------------------------------------------------------------

class TestPostCut:
    def test_t28_fires(self):
        d = np.concatenate([np.full(136, 4.06), np.full(22, 8.55)])
        pc = te.post_cut(d, 137)
        assert pc["fires"] and pc["last"] == 4.06 and pc["rest"] == 8.55

    def test_t29_fires(self):
        d = np.concatenate([np.full(191, 1.45), np.full(17, 5.07), [8.59]])
        assert te.post_cut(d, 192)["fires"]

    def test_a_flat_tail_does_not(self):
        d = np.full(158, 2.0)
        assert not te.post_cut(d, 149)["fires"]

    def test_twice_the_tail_but_never_over_eight_does_not(self):
        """T04: 2.21 -> 2.6 with a max of 6.69 -- motion, not a collapse."""
        d = np.concatenate([np.full(144, 2.21), np.full(13, 3.0), [6.69]])
        assert not te.post_cut(d, 144)["fires"]

    def test_over_eight_once_but_not_twice_the_tail_does_not(self):
        d = np.concatenate([np.full(120, 5.0), np.full(20, 7.0), [9.0]])
        assert not te.post_cut(d, 120)["fires"]

    def test_no_trim_is_nothing_to_read(self):
        assert te.post_cut(np.full(100, 2.0), 101) == {}

    def test_the_row_is_advisory_and_names_both_numbers(self):
        g = te.post_cut_row({"fires": True, "last": 4.06, "rest": 8.55, "rest_max": 14.5})
        assert g.name == "post-cut" and not g.ok and not g.hard and g.penalty > 0
        assert "4.06" in g.note and "8.55" in g.note

    def test_an_unread_tail_is_not_measured(self):
        g = te.post_cut_row({})
        assert g.value is None and g.ok and g.note == "not measured"


# ---- pulse ---------------------------------------------------------------------------

def sine_pulse(n: int = 157, period: float = 22.0, seed: int = 4) -> np.ndarray:
    """T05's shape: troughs of 1 rising to peaks of 11 every `period` frames
    (T05's series runs 1-2 to 10-14; its residual is 0.65 of its median step)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    return 6.0 + 5.0 * np.sin(2 * np.pi * t / period) + rng.normal(0, 0.6, n)


def monotone_push(n: int = 157, seed: int = 5) -> np.ndarray:
    """A push that accelerates into its cut: the diff climbs 1 -> 6, with grain."""
    t = np.arange(n) / n
    return 1.0 + 5.0 * t ** 2 + np.random.default_rng(seed).normal(0, 0.3, n)


class TestPulse:
    def test_t05s_pulse_fires(self):
        p = te.pulse(sine_pulse())
        assert p["fires"] and 20 <= p["period"] <= 24 and p["cycles"] >= 3 and p["r"] > 0.5

    def test_a_monotone_push_does_not(self):
        assert not te.pulse(monotone_push())["fires"]

    def test_white_noise_does_not(self):
        assert not te.pulse(np.random.default_rng(9).normal(3, 1, 157))["fires"]

    def test_a_still_take_does_not(self):
        assert not te.pulse(np.full(157, 1.0))["fires"]

    def test_fewer_than_three_cycles_do_not(self):
        assert not te.pulse(sine_pulse(n=50, period=22.0))["fires"]

    def test_a_faint_ripple_under_the_amplitude_floor_does_not(self):
        """T20: r 0.64 at 17 frames, but the ripple is a sixth of the median step."""
        t = np.arange(157)
        assert not te.pulse(1.0 + 0.08 * np.sin(2 * np.pi * t / 17))["fires"]

    def test_a_period_outside_the_window_does_not(self):
        assert not te.pulse(sine_pulse(period=60.0))["fires"]

    def test_the_row_is_advisory_and_names_the_period(self):
        g = te.pulse_row({"fires": True, "period": 22, "cycles": 6, "r": 0.83, "amp": 0.6})
        assert g.name == "pulse" and not g.ok and not g.hard and g.penalty > 0 and "22f" in g.note

    def test_a_quiet_pulse_row_is_ok(self):
        g = te.pulse_row({"fires": False, "period": 0, "cycles": 0, "r": 0.1, "amp": 0.1})
        assert g.ok and g.value == 0.1


# ---- the rows on a frames folder -----------------------------------------------------

def test_a_take_that_collapses_after_its_cut_fires_post_cut(tmp_path):
    frames = np.concatenate([drifting(30, 1.0), np.stack([textured(k) for k in range(12)])])
    rows = te.rows(write_frames(frames, tmp_path / "a"), 42 / 24, 30 / 24)
    assert [g.name for g in rows] == ["post-cut", "pulse"]
    assert not rows[0].ok and rows[1].ok


def test_a_take_with_a_flat_tail_is_quiet(tmp_path):
    rows = te.rows(write_frames(drifting(42, 1.0), tmp_path / "b"), 42 / 24, 30 / 24)
    assert all(g.ok for g in rows)
