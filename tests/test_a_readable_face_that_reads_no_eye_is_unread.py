"""A zero eye score on a face big enough to draw a pupil is the reader's miss, never a score of 0.

FastH3 bench, 2026-10-21 (docs/audit/2026-10-21_fasth3_faces/REPEATABILITY.md): T26 Enfield, A seed 3,
a clearly drawn 63 px face, read eye 0.0 and was averaged into A's mean as a real score (the change
read -1.5 where the other seeds say about -17.8).  `face_eye.track_eyes` now says None ("unread") for
a track whose median is 0 at READABLE_PX or more; under it (Hyde's 11 px far figure) 0 stays 0.
Pure numpy."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_eye as fe
from studio import face_gate


def crops(eyes: bool, n: int = 4) -> list[np.ndarray]:
    g = np.full((128, 128), 170.0)
    if eyes:
        yy, xx = np.mgrid[0:128, 0:128]
        for cx in (44, 84):
            g[40:50, cx - 8:cx + 8] = 235
            g[(yy - 45) ** 2 + (xx - cx) ** 2 <= 9] = 25
    return [np.dstack([g] * 3).astype(np.uint8)] * n


BOXES = [(0, 0, 128, 128)] * 4


def test_a_readable_face_with_no_eye_found_is_unread():
    assert fe.track_eyes(crops(eyes=False), BOXES, px=fe.READABLE_PX) is None


def test_a_face_under_the_readable_size_reads_zero():
    assert fe.track_eyes(crops(eyes=False), BOXES, px=fe.READABLE_PX - 1) == 0.0


def test_a_drawn_eye_is_read_at_any_size():
    assert fe.track_eyes(crops(eyes=True), BOXES, px=fe.READABLE_PX) == pytest.approx(fe.eye_score(crops(True)[0][:, :, 0].astype(np.float32)), rel=0.05)


def test_without_a_size_the_score_is_as_before():
    assert fe.track_eyes(crops(eyes=False), BOXES) == 0.0


def test_unread_is_a_rule_on_the_score_and_the_face_size():
    assert fe.unread_zero(0.0, 63.0) is None and fe.unread_zero(0.0, 11.0) == 0.0 and fe.unread_zero(41.5, 63.0) == 41.5
    assert fe.unread_zero(None, 63.0) is None


def test_the_gate_log_says_unread_for_a_readable_face_with_no_eye():
    out = face_gate.extras(crops(False), crops(False), BOXES, px=60.0)
    assert out["eye_src"] is None and out["eye_ref"] is None
