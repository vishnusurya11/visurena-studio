"""G-WARP's cure matrix (contract K6): one seed retake, then the refine only for a small
face; a readable face ships flagged.  `track_px_min` is the smallest tracked median height."""
from __future__ import annotations

import pytest

from studio import warp_gate as wg


@pytest.mark.parametrize("state, taken, px, cure", [
    ("fail", 0, 30.0, "seed"), ("fail", 0, 200.0, "seed"), ("fail", 0, None, "seed"),
    ("fail", 1, 34.0, "refine"), ("fail", 1, None, "refine"), ("fail", 1, 148.0, ""),
    ("fail", 2, 60.0, ""),
    ("warn", 0, 30.0, "refine"), ("unmeasurable", 0, None, "refine"),
    ("pass", 0, 30.0, ""), ("eye", 1, 30.0, ""),
])
def test_the_cure_matrix(state, taken, px, cure):
    assert wg.cure(state, taken, px) == cure


def test_one_retake_is_the_cap():
    assert wg.RETAKES == 1


def test_a_cure_without_track_heights_still_works():
    assert wg.cure("fail", 0) == "seed" and wg.cure("fail", 1) == "refine"
