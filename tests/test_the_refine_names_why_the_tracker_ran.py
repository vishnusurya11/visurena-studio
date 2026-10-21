"""A26 (face debate 2026-10-21, LEDGER_round4): `readable()` is five clauses and ep01 could not say which
one sent T19 (120.3 px, tracked anyway) to the tracker.  The refine names the failed clause on every
row, beside the warp gate's smallest face and the tracker's own; the 120 px wall does not move."""
from __future__ import annotations

from studio import face_refine as fr

CARD = {"index": 21, "faces": ["richard_enfield"]}


def dq(tracks, share=0.95):
    return {"passed": True, "gates": [], "measures": {"warp": {"S": 0.2, "Se": 0.3, "share": share, "tracks": tracks}}}


def test_a_readable_take_names_no_clause():
    assert fr.readable_clause(CARD, dq([{"median_px": 130.0, "min_px": 125.0}])) == ""


def test_t21_like_record_fails_on_its_smallest_face():
    assert fr.readable_clause(CARD, dq([{"median_px": 131.0, "min_px": 117.1}])) == "min_px<120"


def test_t19_like_record_with_fewer_tracks_than_faces_names_that_clause():
    card = {"index": 19, "faces": ["a", "b"]}
    assert fr.readable_clause(card, dq([{"median_px": 144.0, "min_px": 120.3}])) == "fewer_tracks_than_faces"


def test_a_thin_share_and_a_median_only_record_are_named():
    assert fr.readable_clause(CARD, dq([{"median_px": 150.0, "min_px": 150.0}], share=0.5)) == "share<0.8"
    assert fr.readable_clause(CARD, dq([{"median_px": 150.0}])) == "no_min_px"


def test_no_tracks_and_no_record_are_named():
    assert fr.readable_clause(CARD, dq([])) == "no_tracks"
    assert fr.readable_clause(CARD, None) == "no_tracks"


def test_the_clause_agrees_with_readable():
    for record in (dq([{"median_px": 130.0, "min_px": 125.0}]), dq([{"median_px": 131.0, "min_px": 117.1}]), None):
        assert (fr.readable_clause(CARD, record) == "") == fr.readable(CARD, record)
