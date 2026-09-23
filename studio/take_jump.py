"""A cut inside a take, read as a change of PICTURE rather than of brightness.

`cut` (take_coherence) is the largest mean grey step between two frames, so a
switch between two pictures of similar brightness reads small: ep09 T15's
second attempt opened on the burning lawn, cut to the rubble insert, read
26.5 and passed at 74 (take-gate audit, 2026-09-23). The lowest cosine between
consecutive frame signatures does not care how bright the two pictures are.
"""
from __future__ import annotations

import numpy as np

from studio.take_verdict import Gate

WALL = 0.50
"""Hard below. Calibrated on the pipeline's own signatures (motion_gate
frames): see tests/test_a_cut_is_a_change_of_picture_not_of_brightness.py and
docs/calibration/take_jump.md for the per-take table."""


def min_step(sigs: np.ndarray) -> float:
    """The lowest similarity between one frame's signature and the next."""
    if len(sigs) < 2:
        return 1.0
    return float((sigs[:-1] * sigs[1:]).sum(axis=1).min())


def row(value: float) -> Gate:
    ok = value >= WALL
    return Gate("jump", round(value, 3), ok, True, f"{value:.2f}" + ("" if ok else " HARD: another picture"),
                0.0 if ok else 40.0)
