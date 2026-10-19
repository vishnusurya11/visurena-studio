"""The crop track, ported from ComfyUI-H3-FaceRefine (Carasibana, MIT; ideas only, nothing
installed): the crop centre is median-smoothed over 21 frames and its size over 51, so the box
sits still and never pumps; a gap is interpolated; a track never crosses a hard cut; the window
follows the face's smoothed size, so a push-in (Jekyll ep01 T06, 60 -> 233 px) stays inside its
crop.  A take is judged by its SMALLEST tracked face after the running median, so one detector
dip is not the face.  Pure numpy: no detector, no video."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_track as ft


def box(cx, cy, h=30.0):
    return (cx - h / 2, cy - h / 2, cx + h / 2, cy + h / 2)


def test_the_windows_are_the_ported_ones():
    assert (ft.CENTRE_SMOOTH, ft.SIZE_SMOOTH) == (21, 51)


def test_a_running_median_drops_a_one_frame_spike():
    a = np.array([10.0] * 10 + [90.0] + [10.0] * 10)
    assert ft.running_median(a, 5).max() == pytest.approx(10.0)


def test_the_running_median_shrinks_its_window_at_the_ends():
    assert list(ft.running_median(np.array([255.0, 162.0, 119.0]), 17)) == [162.0, 162.0, 162.0]


def test_a_jittering_centre_is_held_still():
    rng = np.random.default_rng(1)
    track = [(t, box(300 + rng.normal(0, 6), 300, 40)) for t in range(0, 120, 3)]
    raw = ft.fill(track, 120, smooth=1)
    held = ft.fill(track, 120)
    step = lambda b: np.abs(np.diff((b[:, 0] + b[:, 2]) / 2)).mean()
    assert step(held) < 0.25 * step(raw)


def test_a_steady_walk_is_not_dragged_behind():
    track = [(t, box(100 + 2 * t, 300, 40)) for t in range(0, 120, 3)]
    held = ft.fill(track, 120)
    assert (held[60][0] + held[60][2]) / 2 == pytest.approx(220.0, abs=1.0)


def test_the_window_follows_a_push_in():
    track = [(t, box(384, 384, 60 + t)) for t in range(0, 174, 3)]
    wins = ft.windows(ft.fill(track, 174), 768, 768)
    assert wins[20][2] < wins[150][2]
    assert all(s >= (60 + t) * 0.9 * ft.MARGIN for t, (_, _, s) in enumerate(wins) if 30 <= t <= 140)


def test_the_common_side_is_the_median_window():
    assert ft.side_of([(0, 0, 96), (0, 0, 100), (0, 0, 300)]) == 100


def test_a_track_is_cut_at_a_hard_cut():
    track = [(t, box(300, 300)) for t in range(0, 60, 3)]
    pieces = ft.split([track], [30])
    assert [ft.life(p) for p in pieces] == [(0, 27), (30, 57)]


def test_no_cut_leaves_the_track_whole():
    track = [(t, box(300, 300)) for t in range(0, 60, 3)]
    assert ft.split([track], []) == [track]


def test_the_smallest_face_reads_through_the_running_median():
    track = [(t, box(300, 300, 150.0)) for t in range(0, 90, 3)]
    track[10] = (30, box(300, 300, 50.0))
    assert ft.track_px(track) == pytest.approx(150.0)


def test_a_push_in_is_judged_by_its_small_start():
    track = [(t, box(384, 384, 60 + t)) for t in range(0, 174, 3)]
    assert ft.track_px(track) < 90.0


def test_a_track_soft_anywhere_is_kept_for_the_refine():
    push = [(t, box(384, 384, 60 + t)) for t in range(0, 174, 3)]
    close = [(t, box(200, 300, 200)) for t in range(0, 174, 3)]
    assert ft.small([push, close], 120.0) == [push]
