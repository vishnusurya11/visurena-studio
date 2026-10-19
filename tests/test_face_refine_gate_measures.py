"""The gate's measures for one refined crop (studio/face_gate.py): the seam in the
feather band, the face region's frame-to-frame flicker unpasted and pasted, the
faces counted and the identity against the sheet on the 768 crops.  The detector
and the embedder are injected fakes; frames are synthetic arrays."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_gate as fg
from studio import face_refine as fr


def frames(n, level=50, side=32):
    return [np.full((side, side, 3), level + (k % 2), np.uint8) for k in range(n)]


def test_the_take_is_cut_to_its_windows_over_the_life():
    take = [np.full((100, 100, 3), k, np.uint8) for k in range(10)]
    wins = [(10, 20, 30)] * 10
    got = fg.windows_of(take, wins, (2, 5))
    assert len(got) == 4 and got[0].shape == (30, 30, 3) and got[0][0, 0, 0] == 2


def test_windows_that_follow_a_push_in_are_measured_at_one_side():
    """The window grows with its face (studio/face_track.windows): seam and flicker compare
    frames of one size, the track's median side."""
    take = [np.full((200, 200, 3), 9, np.uint8) for _ in range(4)]
    crops = fg.windows_of(take, [(0, 0, 40), (0, 0, 50), (0, 0, 60), (0, 0, 70)], (0, 3))
    got = fg.at_side(crops, 55)
    assert {g.shape for g in got} == {(55, 55, 3)} and got[0][0, 0, 0] == 9


def test_the_refined_crop_is_shrunk_to_the_window_frame_by_frame():
    crop = [np.full((768, 768, 3), k, np.uint8) for k in range(8)]
    got = fg.shrunk(crop, start=2, span=(3, 5), side=30)
    assert [g[0, 0, 0] for g in got] == [1, 2, 3] and got[0].shape == (30, 30, 3)


def test_a_crop_that_ends_early_is_shrunk_to_what_exists():
    crop = [np.zeros((768, 768, 3), np.uint8)] * 2
    assert len(fg.shrunk(crop, start=0, span=(0, 5), side=30)) == 2


def test_identical_crops_have_no_seam_and_the_same_flicker():
    src = frames(6)
    seam, f_src, f_ref = fg.seam_and_flicker(src, src)
    assert seam == 0.0 and f_src == pytest.approx(f_ref)


def test_a_boiling_refine_flickers_more_than_its_take():
    src = frames(6)
    ref = [np.full((32, 32, 3), 50 + 40 * (k % 2), np.uint8) for k in range(6)]
    _, f_src, f_ref = fg.seam_and_flicker(src, ref)
    assert f_ref > f_src * fr.FLICKER_RATIO + fr.FLICKER_SLACK


def fake_detect(found):
    return lambda rgb: [{"box": [10, 10, 60, 60]} for _ in range(found[int(rgb[0, 0, 0])])]


def test_faces_and_identity_are_read_on_the_sampled_crops():
    src = [np.full((64, 64, 3), 0, np.uint8)] * 3
    ref = [np.full((64, 64, 3), 1, np.uint8)] * 3
    detect = fake_detect({0: 1, 1: 1})
    embed = lambda rgb, box: np.array([1.0, 0.0]) if rgb[0, 0, 0] == 1 else np.array([0.6, 0.8])
    cs, cr, ids, idr = fg.faces_and_identity(src, ref, np.array([1.0, 0.0]), detect, embed)
    assert (cs, cr) == (1, 1) and ids == pytest.approx(0.6) and idr == pytest.approx(1.0)


def test_no_sheet_vector_leaves_identity_unread():
    src = [np.zeros((64, 64, 3), np.uint8)]
    cs, cr, ids, idr = fg.faces_and_identity(src, src, None, lambda rgb: [], lambda r, b: np.array([1.0]))
    assert (cs, cr, ids, idr) == (0, 0, None, None)


def test_the_measures_come_together_for_the_decision():
    src = frames(12, side=40)
    m = fg.measure(src, src, src[:3], src[:3], np.array([1.0, 0.0]), lambda rgb: [], lambda r, b: None)
    assert isinstance(m, fr.Measures) and fr.decide(m)[0]
