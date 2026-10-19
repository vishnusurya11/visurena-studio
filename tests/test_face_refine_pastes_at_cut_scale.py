"""The paste order is cut scale first, then the one upscale (owner 2026-10-18, 24caaeb).  The
detail a refined crop adds must survive that 4x: after paste-then-upscale the face region keeps
most of the crop's own sharpness and far more than the unrefined take.  Synthetic frames, CPU;
the real T18 before/after A/B (sharpness and facenet identity) is the idle-GPU job, recorded
in docs/audit, never auto-reverted."""
from __future__ import annotations

import cv2
import numpy as np

from studio import face_paste as fp

SIDE, X, Y, UP = 96, 200, 150, 4


def sharp(img: np.ndarray) -> float:
    return float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var())


def up(img: np.ndarray) -> np.ndarray:
    return cv2.resize(img, None, fx=UP, fy=UP, interpolation=cv2.INTER_LANCZOS4)


def scene():
    frame = np.full((384, 384, 3), 120, np.uint8)
    frame[Y:Y + SIDE, X:X + SIDE] = cv2.GaussianBlur(frame[Y:Y + SIDE, X:X + SIDE], (0, 0), 6)
    rng = np.random.default_rng(3)
    crop = cv2.GaussianBlur(rng.integers(40, 220, (SIDE, SIDE, 3)).astype(np.uint8), (0, 0), 0.8)
    return frame, crop


def pasted_at_cut_scale():
    frame, crop = scene()
    fp.blend(frame, crop, X, Y, fp.feather(SIDE, round(SIDE * fp.FEATHER_SHARE)), 1.0)
    return up(frame)


def face_of(master: np.ndarray) -> np.ndarray:
    pad = UP * 14
    return master[Y * UP + pad:(Y + SIDE) * UP - pad, X * UP + pad:(X + SIDE) * UP - pad]


def test_the_pasted_face_keeps_most_of_the_crops_detail_through_the_one_upscale():
    _, crop = scene()
    assert sharp(face_of(pasted_at_cut_scale())) > 0.5 * sharp(face_of(np.pad(up(crop), ((Y * UP, 0), (X * UP, 0), (0, 0)))))


def test_the_pasted_face_is_far_sharper_than_the_unrefined_take():
    frame, _ = scene()
    assert sharp(face_of(pasted_at_cut_scale())) > 20 * sharp(face_of(up(frame)))


def test_the_geometry_at_factor_one_is_the_window_itself():
    assert fp.to_master((100, 200, 96), None, 768, 768, 1) == (100, 200, 96)
