"""The refine tracks only faces under 60 px (ep01: 6 of 8 picks ended no_faces, 579 s of CPU).
The warp measure now keeps `tracks: [{median_px, life}]` in render px; a take whose every
planned face is tracked, mostly, at 60 px or more is declined.  Never face-at-end (T08's is 0.31
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


def test_a_148_px_face_is_declined_though_the_shot_is_wide():
    assert not fr.eligible(card(), ["wide"], dq([{"median_px": 148.0, "life": 60}]), H)


def test_a_34_px_face_is_selected():
    assert fr.eligible(card(), ["wide"], dq([{"median_px": 34.0, "life": 60}]), H)


def test_the_t08_shape_is_selected_whatever_its_face_at_end():
    """A big adult track and a small child track: 2 tracks, the smallest 40 px, face-at-end 0.31."""
    tracks = [{"median_px": 150.0, "life": 60}, {"median_px": 40.0, "life": 55}]
    assert fr.eligible(card(2), ["wide"], dq(tracks, face=0.31), H)


def test_fewer_tracks_than_planned_faces_keeps_todays_rule():
    """MTCNN misses small faces: one 148 px track for two planned faces proves nothing."""
    assert fr.eligible(card(2), ["wide"], dq([{"median_px": 148.0, "life": 60}]), H)


def test_a_low_tracked_share_keeps_todays_rule():
    assert fr.eligible(card(), ["wide"], dq([{"median_px": 148.0, "life": 9}], share=0.5), H)


def test_a_record_without_tracks_keeps_todays_rule():
    assert fr.eligible(card(), ["wide"], dq([]), H)


def test_the_smallest_median_decides():
    tracks = [{"median_px": 148.0, "life": 60}, {"median_px": 59.9, "life": 50}]
    assert fr.eligible(card(2), ["wide"], dq(tracks), H)


def test_the_t01_shape_is_eligible_with_a_gait_hard_fail_and_an_unmeasurable_warp():
    gait = [{"name": "gait", "value": 1.0, "ok": False, "hard": True}]
    d = dq([], share=0.39, state="unmeasurable", passed=False, gates=gait)
    assert fr.eligible({"index": 1, "faces": ["a"]}, ["medium_close"], d, H)


def test_an_identity_hard_fail_still_bars_the_take():
    ident = [{"name": "identity", "value": 0.1, "ok": False, "hard": True}]
    assert not fr.eligible(card(), ["wide"], dq([], passed=False, state="unmeasurable", gates=ident), H)


def test_the_ep01_refine_json_replay_keeps_t08_and_t18_and_drops_the_no_faces_picks():
    """refine.json: only T08 and T18 refined.  With the stored warp measures (no tracks logged yet),
    the Se-only fails T21 and T24 are no longer warp-routed."""
    dqs = json.loads((FIX / "dq_warp.json").read_text("utf-8"))
    refine = json.loads((FIX / "refine.json").read_text("utf-8"))
    routed = {t for t, v in dqs.items() if v["warp"] and fr.warp_routed({"measures": {"warp": v["warp"]}}, 1)}
    assert {"T21", "T24"}.isdisjoint(routed)
    assert {t for t, v in refine.items() if v["status"] == "refined"} == {"T08", "T18"}
