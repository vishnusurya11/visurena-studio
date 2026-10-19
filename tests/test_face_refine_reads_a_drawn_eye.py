"""A cel-valid eye measure for the refine's gate log and the bench (face-blur round 2, 2026-10-19).

Round 1 scored every refine 0.6-0.77x the take on the Laplacian variance of the eye band: cel
inking holds less high-frequency energy than the take's smeared noise and wrinkle hatching, so
that measure rewards the smear (docs/audit/2026-10-19_face_blur/bench/BENCH.md).  A drawn eye is a
dark compact pupil or iris inside the eye band; a smeared one is a pale blob.  `eye_score` is the
local contrast of the two strongest compact dark blobs in the eye band of the 128 px face crop
(long ink lines -- wrinkles, lids, brims -- are not compact).  Logged, never a wall.  Pure numpy."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_eye as fe


def face(eyes=True, smear=False, lines=False) -> np.ndarray:
    """A 128 px skin-toned face; drawn eyes are 5 px dark discs in white, smeared ones pale blobs."""
    g = np.full((128, 128), 170.0)
    for cx in (44, 84):
        if eyes:
            g[40:50, cx - 8:cx + 8] = 235
            yy, xx = np.mgrid[0:128, 0:128]
            g[(yy - 45) ** 2 + (xx - cx) ** 2 <= 9] = 25
        if smear:
            g[40:50, cx - 8:cx + 8] = 205
    if lines:
        g[36:38, 20:108] = 30                 # a brow line: long, not compact
        g[55:57, 30:100] = 40
    return g


def test_a_drawn_eye_outscores_a_smear():
    assert fe.eye_score(face()) > 2 * max(fe.eye_score(face(eyes=False, smear=True)), 1.0)


def test_long_ink_lines_are_not_eyes():
    assert fe.eye_score(face(eyes=False, lines=True)) == 0.0


def test_two_eyes_read_more_than_one():
    one = face()
    one[40:50, 76:92] = 170
    assert fe.eye_score(face()) > fe.eye_score(one) > 0


def test_the_face_crop_is_the_square_box_at_128_px():
    rgb = np.zeros((300, 300, 3), np.uint8)
    rgb[100:140, 100:130] = 200
    g = fe.face_gray(rgb, (100, 100, 130, 140))
    assert g.shape == (128, 128) and g[64, 64] == pytest.approx(200, abs=1)


def test_a_track_reads_the_median_over_its_frames():
    crops = [np.dstack([face()] * 3).astype(np.uint8)] * 3 + [np.dstack([face(eyes=False)] * 3).astype(np.uint8)]
    boxes = [(0, 0, 128, 128)] * 4
    assert fe.track_eyes(crops, boxes) == pytest.approx(fe.eye_score(face()), rel=0.05)
