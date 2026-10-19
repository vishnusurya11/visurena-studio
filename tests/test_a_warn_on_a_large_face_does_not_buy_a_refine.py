"""A WARN is refined only for a small face (face_w < 0.10) or S_held > 1.5 (ep01 T15/T19: S
1.96/1.88 but 0.96/0.87 on held pairs; F2 costs 100-160 s GPU a face)."""
from __future__ import annotations

from studio import face_refine as fr


def dq(**warp):
    base = {"state": "warn", "S": 1.9, "Se": 1.0, "share": 1.0}
    return {"passed": True, "gates": [], "measures": {"warp": base | warp}}


def test_a_warn_with_a_large_face_and_low_held_score_is_not_routed():
    assert not fr.warp_routed(dq(S_held=0.9, face_w=0.2), 0)


def test_a_warn_with_a_small_face_is_routed():
    assert fr.warp_routed(dq(S_held=0.9, face_w=0.06), 0)


def test_a_warn_with_a_bad_held_score_is_routed():
    assert fr.warp_routed(dq(S_held=1.7, face_w=0.2), 0)


def test_an_old_warn_record_without_the_cadence_log_is_routed_as_before():
    assert fr.warp_routed(dq(), 0)


def test_the_state_is_recomputed_from_the_numbers_not_read():
    assert fr.warp_state(dq(state="fail", S=0.1, Se=4.0)) == "eye"
    assert fr.warp_state({}) == ""


def test_a_fail_waits_for_its_one_retake_then_a_small_face_goes_to_the_refine():
    d = dq(S=2.7, tracks=[{"median_px": 30.0, "life": 40}])
    assert not fr.warp_routed(d, 0) and fr.warp_routed(d, 1)


def test_a_failed_readable_face_ships_flagged_not_refined():
    d = dq(S=2.7, tracks=[{"median_px": 100.0, "life": 40}])
    assert not fr.warp_routed(d, 1)
