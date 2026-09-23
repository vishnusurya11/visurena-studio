"""A cut inside a take is a change of PICTURE, read off the frame signatures.

Take-gate audit, 2026-09-23: `cut` is the largest mean grey step between two
frames, so it measures brightness. ep09 T15 opened 0.5 s on the burning lawn
and hard-cut to a rubble insert: attempt 1 read cut 38.9 (fail), attempt 2 read
26.5 and PASSED at 74. The lowest similarity between consecutive frame
signatures reads 0.07 and 0.15 on the two, and 0.83 or more on every other take
of ep08 and ep09.
"""
import numpy as np

from studio.take_jump import min_step, row


def unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def test_a_steady_take_reads_near_one():
    a = unit([1, 2, 3, 4])
    assert min_step(np.stack([a, a, unit([1, 2, 3, 4.1])])) > 0.99


def test_a_switch_to_another_picture_reads_low():
    assert min_step(np.stack([unit([1, 0, 0, 0]), unit([1, 0, 0, 0]), unit([0, 1, 0, 0])])) < 0.1


def test_the_row_is_hard_below_the_wall():
    assert row(0.15).hard and not row(0.15).ok
    assert row(0.83).ok
