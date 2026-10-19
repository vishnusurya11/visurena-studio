"""Cadence: H3 often animates on threes, so S over all pairs is inflated by the step pairs
(ep01 T15 S 1.96 but 0.96 on held pairs).  cadence(gray) -> (period, phase); S_held and S_step
are logged; a WARN routes to the face refine only if the face is small or S_held > 1.5."""
from __future__ import annotations

import numpy as np
import pytest

from studio import warp_gate as wg


def threes(n=30, size=16, seed=0):
    rng = np.random.default_rng(seed)
    base = [rng.integers(0, 255, (size, size)).astype(np.uint8) for _ in range(n // 3 + 1)]
    return [base[i // 3] for i in range(n)]


def test_frames_held_for_three_report_period_three_phase_zero():
    assert wg.cadence(threes()) == (3, 0)


def test_frames_that_all_move_report_no_cadence():
    rng = np.random.default_rng(1)
    gray = [rng.integers(0, 255, (16, 16)).astype(np.uint8) for _ in range(30)]
    assert wg.cadence(gray)[0] == 1


def test_the_pairs_split_into_held_and_step_by_phase():
    held, step = wg.split_pairs(9, 3, 0)
    assert step == [2, 5] and held == [0, 1, 3, 4, 6, 7]


def test_a_cadence_of_one_has_no_step_pairs():
    assert wg.split_pairs(5, 1, 0) == ([0, 1, 2, 3], [])


@pytest.mark.parametrize("s_held, face_w, routed", [(0.9, 0.2, False), (1.6, 0.2, True), (0.9, 0.05, True)])
def test_a_warn_is_refined_only_for_a_small_face_or_a_bad_held_score(s_held, face_w, routed):
    assert wg.warn_routes({"S_held": s_held, "face_w": face_w}) is routed


def test_a_warn_without_the_cadence_log_keeps_the_old_route():
    assert wg.warn_routes({}) is True
