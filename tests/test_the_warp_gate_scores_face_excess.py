"""G-WARP (studio/warp_gate.py; docs/audit/2026-10-18_warping/WARPING.md, main session
2026-10-18, for owner veto): a take's face is redrawn frame to frame when the face
residual -- the warp error of frame t+1 flowed back onto t, counted only where the
forward and backward flow agree -- runs above what the background residual and the
face's own motion explain.

    E(t) = face residual - (2.51 x bg residual + 1.69 x face flow + 1.00)
    S = p90 of E, Se = p90 over the eye mask

FAIL (S > 2.5 or Se > 3.0): a new seed, at most 2, then the F2 face refine.  WARN
(1.5 < S <= 2.5) and UNMEASURABLE (the face tracked in under 45 % of frames): F2.
Tests use synthetic arrays; no video, no detector, no GPU.
"""
from __future__ import annotations

import numpy as np
import pytest

from studio import warp_gate as wg


def test_the_excess_subtracts_what_background_and_motion_explain():
    assert wg.excess(np.array([6.0]), np.array([1.0]), np.array([1.0]))[0] == pytest.approx(6 - 2.51 - 1.69 - 1.0)


def test_the_score_is_the_p90_of_the_finite_frames():
    e = np.array([np.nan] + list(range(10)), float)
    assert wg.score(e) == pytest.approx(np.percentile(np.arange(10.0), 90))
    assert wg.score(np.array([np.nan, np.nan])) is None


@pytest.mark.parametrize("s, se, share, state", [
    (2.65, 3.12, 1.0, "fail"),      # kaw W
    (1.30, 3.20, 1.0, "fail"),      # an eye alone over its wall
    (1.95, 2.0, 1.0, "warn"),       # T22 baseline s1
    (1.30, 1.64, 1.0, "pass"),      # kaw M
    (0.98, -0.9, 1.0, "pass"),      # kaw C
    (3.5, 4.0, 0.40, "unmeasurable"),
    (None, None, 0.9, "unmeasurable"),
])
def test_the_verdict_follows_the_measured_cut(s, se, share, state):
    assert wg.verdict(s, se, share) == state


@pytest.mark.parametrize("state, taken, cure", [
    ("fail", 0, "seed"), ("fail", 1, "seed"), ("fail", 2, "refine"),
    ("warn", 0, "refine"), ("unmeasurable", 0, "refine"), ("pass", 0, ""),
])
def test_a_fail_retakes_twice_then_goes_to_the_face_refine(state, taken, cure):
    assert wg.cure(state, taken) == cure


def test_the_frames_over_the_wall_are_logged_as_spans():
    e = np.array([0, 3, 3, 0, 0, 4, np.nan, 2.6, 0], float)
    assert wg.spans(e) == [[1, 2], [5, 5], [7, 7]]


def test_flow_agreement_keeps_only_consistent_pixels():
    fwd = np.zeros((4, 4, 2), np.float32)
    bwd = np.zeros((4, 4, 2), np.float32)
    bwd[0, 0] = (3.0, 0.0)
    ok = wg.consistent(fwd, bwd)
    assert not ok[0, 0] and ok[1:, :].all()


def test_a_still_frame_flowed_onto_itself_has_no_residual():
    g = np.tile(np.arange(16, dtype=np.uint8) * 10, (16, 1))
    assert wg.residual(g, g, np.zeros((16, 16, 2), np.float32)).max() == 0.0


def test_the_region_mean_reads_only_masked_agreeing_pixels():
    res = np.arange(16, dtype=np.float32).reshape(4, 4)
    mask = np.zeros((4, 4), bool)
    mask[:2, :2] = True
    ok = np.ones((4, 4), bool)
    ok[0, 0] = False
    assert wg.region(res, mask, ok, least=1) == pytest.approx(np.mean([1, 4, 5]))
    assert np.isnan(wg.region(res, np.zeros((4, 4), bool), ok))


def test_faces_link_into_tracks_by_overlap_and_a_swap_starts_a_new_track():
    dets = {0: [(10, 10, 30, 30)], 2: [(12, 10, 32, 30)], 4: [(60, 60, 80, 80)], 6: [(61, 60, 81, 80)]}
    tracks = wg.link(dets)
    assert [[t for t, _ in tr] for tr in tracks] == [[0, 2], [4, 6]]


def test_a_frame_borrows_its_nearest_detection_within_six_frames():
    tracks = [[(0, (10, 10, 30, 30)), (8, (12, 10, 32, 30))]]
    assert wg.boxes_at(3, tracks) == [(10, 10, 30, 30)]
    assert wg.boxes_at(5, tracks) == [(12, 10, 32, 30)]
    assert wg.boxes_at(20, tracks) == []


def test_the_tracked_share_counts_detected_frames_among_those_searched():
    """Detection runs every 2nd frame: 10 frames are 5 searched, 2 found a face."""
    assert wg.tracked_share([[(0, (0, 0, 1, 1)), (2, (0, 0, 1, 1))]], 10) == pytest.approx(0.4)


def test_the_body_below_a_face_is_kept_out_of_the_background():
    m = wg.body_mask([(20, 10, 30, 20)], 96)
    assert m[15, 25] and m[55, 25] and m[15, 9] and not m[15, 5] and not m[70, 25]


def test_the_eye_mask_is_a_patch_round_each_eye():
    m = wg.eye_mask([[(20, 20), (40, 20), (30, 30), (22, 40), (38, 40)]], 64)
    assert m[20, 20] and m[20, 40] and not m[40, 30]


def frames_of(e_face, n=8):
    return {"rf": np.full(n, e_face + 1.0), "rb": np.zeros(n), "mf": np.zeros(n), "re": np.full(n, e_face + 1.0)}


def test_the_measure_comes_together_from_per_frame_rows():
    m = wg.judge(frames_of(2.8), share=1.0, frames=9)
    assert m["state"] == "fail" and m["S"] == pytest.approx(2.8) and m["spans"] == [[0, 7]]


def test_a_failing_take_is_a_hard_warp_row_the_ladder_cures_with_a_seed():
    from studio import take_ladder
    from studio.judges.verdict import Fault
    g = wg.row({"state": "fail", "S": 2.65, "Se": 3.12, "share": 1.0, "spans": [[70, 98]]})
    assert g.name == "warp" and g.hard and not g.ok
    assert take_ladder.cure_of([Fault(kind="warp", where="T03")]) == "seed"


@pytest.mark.parametrize("state", ["warn", "unmeasurable", "pass"])
def test_anything_short_of_a_fail_never_refuses_the_take(state):
    assert wg.row({"state": state, "S": 1.9 if state == "warn" else None, "Se": None, "share": 0.3, "spans": []}).ok


def test_an_unmeasured_take_says_so():
    g = wg.row(None)
    assert g.ok and g.value is None and "not measured" in g.note


# ---- routing to the F2 face refine (studio/face_refine.eligible) -----------------------------

def dq_with(state, passed=True, hard_warp=False):
    gates = [{"name": "face-at-end", "value": 0.3, "ok": True, "hard": False}]
    if hard_warp:
        gates.append({"name": "warp", "value": 2.7, "ok": False, "hard": True})
    return {"passed": passed, "gates": gates, "measures": {"warp": {"state": state}}}


CARD = {"index": 3, "faces": ["hyde"]}


@pytest.mark.parametrize("state", ["warn", "unmeasurable"])
def test_a_warned_or_unreadable_close_take_goes_to_the_face_refine(state):
    from studio import face_refine as fr
    assert fr.eligible(CARD, ["medium_close"], dq_with(state), 768)
    assert not fr.eligible(CARD, ["medium_close"], dq_with("pass"), 768)


def test_a_warp_fail_goes_to_the_face_refine_only_after_its_two_retakes():
    from studio import face_refine as fr
    dq = dq_with("fail", passed=False, hard_warp=True)
    assert not fr.eligible(CARD, ["medium_close"], dq, 768, taken=1)
    assert fr.eligible(CARD, ["medium_close"], dq, 768, taken=2)


def test_a_take_failing_anything_besides_warp_is_still_never_refined():
    from studio import face_refine as fr
    dq = dq_with("fail", passed=False, hard_warp=True)
    dq["gates"].append({"name": "leak", "value": 1.0, "ok": False, "hard": True})
    assert not fr.eligible(CARD, ["wide"], dq, 768, taken=2)


def test_an_insert_is_never_refined_whatever_its_warp():
    from studio import face_refine as fr
    assert not fr.eligible(CARD, ["insert"], dq_with("warn"), 768)


# ---- the take gate's row (scripts/episode/take_dq.py) -------------------------------------

def test_the_take_gate_judges_the_warp_row():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import take_dq
    rows = take_dq.judge_rows({"warp": {"state": "fail", "S": 2.65, "Se": 3.12, "share": 1.0, "spans": []}},
                              {"lane": "narration", "motion": "", "motions": [""]})
    warp = next(r for r in rows if r.name == "warp")
    assert warp.hard and not warp.ok and "studio/warp_gate.py" in take_dq.MEASURES


def test_a_take_with_no_staged_face_is_never_decoded_for_warp():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import take_dq
    assert take_dq.warp_measure(Path("nowhere.mp4"), {"faces": []}, lambda rgb: []) == {"warp": None}
