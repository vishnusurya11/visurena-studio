"""A small face's seam is read on a soft ring round its head, and the seam is measured on what the
redraw does to the take around the head (face-blur round 2, 2026-10-19; face-warp fix the same day).

Round 1 refused T01 Utterson (36 px, seam 21.5), T01 Enfield (30 px, 20.1) and T07's child (38 px,
23.9) on the wall of 18: their 96 px windows are floored (2.6-3.2 faces wide, not 2.4), the H3
redraw repaints that background (a brick wall for shop panes, the railing erased), and the hard
8 % feather pasted all of it.  Round 2 pasted a soft head mask; the face-warp fix (owner: "the face
fix and eye fix is warping the video around") pastes only the face core at every size
(tests/test_the_face_paste_keeps_the_take_outside_the_face.py).  The soft head ring stays the seam's
ruler (studio/face_gate.seam_mask): it reads a level change as itself through either ruler, so round
1's three still read 19.8-25.1 and are refused.  Pure numpy."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_gate as fg
from studio import face_paste as fp
from studio import face_refine as fr
from studio import face_track as ft


def test_a_face_whose_window_is_floored_is_soft():
    assert fp.SOFT_PX == pytest.approx(ft.MIN_SIDE / ft.MARGIN)
    assert fp.soft(38.0) and not fp.soft(41.0) and not fp.soft(None)


def test_the_soft_seam_ring_keeps_the_head_and_fades_to_nothing_at_the_window_edge():
    m = fg.soft_mask(96, 36.0)[..., 0]
    cx, cy, rx, ry = fg.head_shape(96, 36.0)
    assert m[int(cy), int(cx)] == pytest.approx(1.0, abs=1e-3)
    edge = fp.feather(96, 8)[0, :, 0].max()          # the hard feather's own edge, ~0.04
    assert max(m[0, :].max(), m[:, 0].max(), m[-1, :].max(), m[:, -1].max()) <= edge + 1e-6
    assert m[:, 0].max() < 0.01                           # beside the head the soft mask is already gone


def test_the_soft_seam_ring_is_smooth_no_step_anywhere():
    m = fg.soft_mask(96, 36.0)[..., 0]
    assert np.abs(np.diff(m, axis=0)).max() < 0.2 and np.abs(np.diff(m, axis=1)).max() < 0.2


def test_a_big_face_reads_its_seam_on_the_windows_feather_band():
    assert np.array_equal(fg.seam_mask(120, None), fp.feather(120, max(4, round(120 * fp.FEATHER_SHARE))))


def test_the_paste_never_sharpens_a_flat_patch():
    """No halo: a flat patch over a flat frame never leaves the range of the two levels."""
    frame = np.full((200, 200, 3), 40, np.uint8)
    fp.blend(frame, np.full((96, 96, 3), 200, np.uint8), 50, 50, fp.paste_mask(96, 36.0), 1.0)
    assert frame.min() >= 40 and frame.max() <= 200


def take_like(n=8, side=96, seed=0):
    rng = np.random.default_rng(seed)
    base = rng.integers(60, 160, (side, side, 3)).astype(np.uint8)
    return [base.copy() for _ in range(n)]


def test_identical_crops_have_no_seam():
    src = take_like()
    seam, _, _ = fg.seam_and_flicker(src, src, face=36 / 96, soft=True)
    assert seam == 0.0


def test_a_redrawn_background_reads_the_same_through_either_ruler():
    """A level change is a level change: the soft ring spreads the edge, it does not hide it."""
    src = take_like()
    ref = [np.clip(s.astype(int) + 30, 0, 255).astype(np.uint8) for s in src]
    soft, _, _ = fg.seam_and_flicker(src, ref, face=36 / 96, soft=True)
    hard, _, _ = fg.seam_and_flicker(src, ref, face=36 / 96, soft=False)
    assert soft == pytest.approx(hard, abs=2.0) == pytest.approx(30.0, abs=2.0)


def test_a_really_bad_seam_still_fails_the_soft_paste():
    src = take_like()
    ref = [np.clip(s.astype(int) + 60, 0, 255).astype(np.uint8) for s in src]
    seam, _, _ = fg.seam_and_flicker(src, ref, face=36 / 96, soft=True)
    assert seam > fr.SEAM_MAX


def test_the_seam_wall_is_round_ones_wall():
    assert fr.SEAM_MAX == 18.0


def test_a_kept_soft_track_carries_its_face_size(tmp_path):
    import json
    room = tmp_path
    (room / "refine").mkdir()
    (room / "refine" / "T01_p0.json").write_text(json.dumps({"windows": [[0, 0, 96]] * 4, "life": [0, 3], "start": 0,
                                                             "face_px": 36.0, "side": 96, "soft": True}))
    entry = {"people": [{"kept": True, "track": "refine/T01_p0.json", "crop": "refine/T01_p0.mp4"}]}
    track, = fp.kept_tracks(entry, room)
    assert track.face == pytest.approx(36 / 96)


def test_an_old_track_file_has_no_face_size(tmp_path):
    import json
    (tmp_path / "refine").mkdir()
    (tmp_path / "refine" / "T01_p0.json").write_text(json.dumps({"windows": [[0, 0, 96]], "life": [0, 0], "start": 0}))
    entry = {"people": [{"kept": True, "track": "refine/T01_p0.json", "crop": "refine/T01_p0.mp4"}]}
    assert fp.kept_tracks(entry, tmp_path)[0].face is None
