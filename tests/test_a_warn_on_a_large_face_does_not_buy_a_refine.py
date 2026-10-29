"""A WARN buys no refine on a face that already reads: since 2026-10-19 the refine selects by
the tracked face (studio/face_refine.SMALL_FACE_PX, 120 px), not by the warp route.  The warp
gate's truth stays: the state is recomputed from the numbers, and a FAIL waits for its one seed
retake before any refine (ep01 T15/T19: S 1.96/1.88 but 0.96/0.87 on held pairs)."""
from __future__ import annotations

from studio import face_refine as fr

CARD = {"index": 15, "faces": ["a"]}


def dq(**warp):
    base = {"state": "warn", "S": 1.9, "Se": 1.0, "share": 1.0}
    return {"passed": True, "gates": [], "measures": {"warp": base | warp}}


def tracked(px: float) -> list[dict]:
    """A steady face: its smallest (min_px, read by the refine since 2026-10-19) is its median."""
    return [{"median_px": px, "min_px": px, "life": 120}]


def test_a_warn_with_a_face_tracked_readable_is_refined_too():
    """Owner 2026-10-29: every human face is refined, a readable one too (it was declined)."""
    assert fr.eligible(CARD, ["medium_close"], dq(S_held=0.9, face_w=0.2, tracks=tracked(150.0)))


def test_a_warn_with_a_soft_face_is_refined():
    assert fr.eligible(CARD, ["medium_close"], dq(S_held=0.9, face_w=0.2, tracks=tracked(94.0)))


def test_an_old_warn_record_without_tracks_goes_to_the_tracker():
    assert fr.eligible(CARD, ["medium_close"], dq())


def test_the_state_is_recomputed_from_the_numbers_not_read():
    assert fr.warp_state(dq(state="fail", S=0.1, Se=4.0)) == "eye"
    assert fr.warp_state({}) == ""


def test_a_fail_waits_for_its_one_retake_then_a_small_face_goes_to_the_refine():
    d = dq(S=2.7, tracks=tracked(30.0))
    assert not fr.eligible(CARD, ["wide"], d, taken=0) and fr.eligible(CARD, ["wide"], d, taken=1)


def test_a_failed_face_that_reads_is_refined_too():
    """Owner 2026-10-29: every human face is refined, a readable one too (it was declined)."""
    assert fr.eligible(CARD, ["wide"], dq(S=2.7, tracks=tracked(150.0)), taken=1)
