"""The warp measure keeps `tracks: [{median_px, min_px, life}]` in render px (P07; min_px since
2026-10-19); a take whose every planned face is tracked, mostly, at SMALL_FACE_PX or more AT ITS
SMALLEST is declined before the refine's own tracker runs (a median-only record goes to the tracker).  The wall was 60 px (ep01: 6 of 8 picks ended no_faces, 579 s of CPU) and is 120
since 2026-10-19 (a 60-110 px face draws a 5-10 px eye).  Never face-at-end (T08's is 0.31
while its child track is under 60 px)."""
from __future__ import annotations

import json
from pathlib import Path

from studio import face_refine as fr

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P07"
H = 768


def dq(tracks, share=1.0, state="pass", face=0.3, passed=True, gates=()):
    g = [{"name": "face-at-end", "value": face, "ok": True, "hard": False}, *gates]
    return {"passed": passed, "gates": g, "measures": {"warp": {"state": state, "S": 0.1, "Se": 0.1,
                                                               "share": share, "tracks": tracks}}}


def card(n=1):
    return {"index": 3, "shots": [3], "faces": ["a", "b"][:n]}


def test_a_148_px_face_is_refined_too():
    """Owner 2026-10-29: every human face is refined, a readable one too (it was declined)."""
    assert fr.eligible(card(), ["wide"], dq([{"median_px": 148.0, "min_px": 140.0, "life": 60}]))


def test_a_34_px_face_is_selected():
    assert fr.eligible(card(), ["wide"], dq([{"median_px": 34.0, "life": 60}]))


def test_a_100_px_face_is_selected_since_the_wall_is_120():
    assert fr.eligible(card(), ["medium_close"], dq([{"median_px": 100.0, "life": 60}]))


def test_the_t08_shape_is_selected_whatever_its_face_at_end():
    """A big adult track and a small child track: 2 tracks, the smallest 40 px, face-at-end 0.31."""
    tracks = [{"median_px": 150.0, "life": 60}, {"median_px": 40.0, "life": 55}]
    assert fr.eligible(card(2), ["wide"], dq(tracks, face=0.31))


def test_fewer_tracks_than_planned_faces_keeps_todays_rule():
    """MTCNN misses small faces: one 148 px track for two planned faces proves nothing."""
    assert fr.eligible(card(2), ["wide"], dq([{"median_px": 148.0, "life": 60}]))


def test_a_low_tracked_share_keeps_todays_rule():
    assert fr.eligible(card(), ["wide"], dq([{"median_px": 148.0, "life": 9}], share=0.5))


def test_a_record_without_tracks_keeps_todays_rule():
    assert fr.eligible(card(), ["wide"], dq([]))


def test_the_smallest_median_decides():
    tracks = [{"median_px": 148.0, "life": 60}, {"median_px": 59.9, "life": 50}]
    assert fr.eligible(card(2), ["wide"], dq(tracks))


def test_the_t01_shape_is_eligible_with_a_gait_hard_fail_and_an_unmeasurable_warp():
    gait = [{"name": "gait", "value": 1.0, "ok": False, "hard": True}]
    d = dq([], share=0.39, state="unmeasurable", passed=False, gates=gait)
    assert fr.eligible({"index": 1, "faces": ["a"]}, ["medium_close"], d)


def test_an_identity_hard_fail_still_bars_the_take():
    ident = [{"name": "identity", "value": 0.1, "ok": False, "hard": True}]
    assert not fr.eligible(card(), ["wide"], dq([], passed=False, state="unmeasurable", gates=ident))


def test_the_ep01_refine_json_replay_keeps_t08_and_t18_and_owes_no_seed_on_the_se_only_fails():
    """refine.json: only T08 and T18 refined.  The Se-only fails T21 and T24 owe no seed retake
    (the eye is an advisory), so the refine's tracker reads them like any other take."""
    dqs = json.loads((FIX / "dq_warp.json").read_text("utf-8"))
    refine = json.loads((FIX / "refine.json").read_text("utf-8"))
    owed = {t for t, v in dqs.items() if v["warp"] and fr.retake_owed({"measures": {"warp": v["warp"]}}, 0)}
    assert {"T21", "T24"}.isdisjoint(owed)
    assert {t for t, v in refine.items() if v["status"] == "refined"} == {"T08", "T18"}
