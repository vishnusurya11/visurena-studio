"""Panel face size predicts take face size (2026-10-21_ep02_proof DESIGN 4.4, P6).

The panel's tallest face at the 768 render (panel_dq.tiny_face_record, A28) against the take's
smallest tracked size of its tallest face (the dq's warp tracks), over EVERY pair of an episode, not
only the refined rows.  Pre-registered kill: R^2 < 0.8, or any static single-face take whose take
size the fit misses by more than 20 %."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio.rehearsal import panel_take_size as pts


def panel(shot: int, face_h, faces=1, cast=1) -> dict:
    return {"shot": shot, "faces": faces, "cast_faces": cast, "face_h": face_h}


def dq(tracks: list[tuple[float, float]], still=True) -> dict:
    return {"camera": {"still_ok": still},
            "measures": {"warp": {"tracks": [{"median_px": m, "min_px": n} for m, n in tracks]}}}


def test_a_pair_reads_the_panel_px_from_the_a28_column_and_the_tallest_take_track():
    p = pts.pair_of(3, panel(3, 0.173), dq([(50.0, 45.0), (123.4, 121.7)], still=True))
    assert p == {"take": 3, "panel_px": 133, "take_px": 121.7, "static": True, "single": False}


def test_no_pair_without_a_panel_face_a_cast_face_or_a_take_track():
    assert pts.pair_of(1, panel(1, None), dq([(60.0, 50.0)])) is None
    assert pts.pair_of(1, panel(1, 0.1, cast=0), dq([(60.0, 50.0)])) is None
    assert pts.pair_of(1, panel(1, 0.1), dq([])) is None
    assert pts.pair_of(1, panel(1, 0.1), None) is None


def test_a_perfect_line_has_r2_one():
    pairs = [{"panel_px": x, "take_px": 2 * x + 3} for x in (10, 20, 40, 80)]
    slope, intercept, r2 = pts.fit(pairs)
    assert slope == pytest.approx(2.0) and intercept == pytest.approx(3.0) and r2 == pytest.approx(1.0)


def test_the_kill_fires_on_a_low_r2():
    pairs = [{"take": k, "panel_px": x, "take_px": y, "static": False, "single": False}
             for k, (x, y) in enumerate([(10, 90), (20, 10), (40, 70), (80, 20)])]
    said = pts.verdict(pairs)
    assert not said["passed"] and "R^2" in said["kill"][0]


def test_the_kill_fires_on_one_static_single_face_missed_by_more_than_20_percent():
    pairs = [{"take": k, "panel_px": x, "take_px": x, "static": True, "single": True} for k, x in
             enumerate([20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0])]
    pairs.append({"take": 9, "panel_px": 50.0, "take_px": 80.0, "static": True, "single": True})
    said = pts.verdict(pairs)
    assert not said["passed"] and any("T09" in k for k in said["kill"])


def test_a_tight_line_passes():
    pairs = [{"take": k, "panel_px": x, "take_px": 1.05 * x, "static": True, "single": True}
             for k, x in enumerate([30.0, 60.0, 90.0, 150.0, 220.0])]
    said = pts.verdict(pairs)
    assert said["passed"] and said["n"] == 5 and said["kill"] == []


def test_fewer_than_three_pairs_cannot_pass():
    said = pts.verdict([{"take": 0, "panel_px": 10.0, "take_px": 10.0, "static": True, "single": True}])
    assert not said["passed"] and "pairs" in said["kill"][0]


def test_an_episode_is_read_from_its_named_records(tmp_path):
    home = tmp_path / "ep01"
    (home / "storyboard").mkdir(parents=True)
    (home / "takes" / "r2v").mkdir(parents=True)
    (home / "storyboard" / "panel_dq.json").write_text(json.dumps([panel(0, 0.1), panel(1, 0.2)]))
    (home / "takes" / "r2v" / "prompts.json").write_text(json.dumps([{"index": 0, "shots": [0]},
                                                                     {"index": 1, "shots": [1]}]))
    (home / "takes" / "r2v" / "T00.dq.json").write_text(json.dumps(dq([(80.0, 77.0)])))
    pairs = pts.episode_pairs(home)
    assert [p["take"] for p in pairs] == [0] and pairs[0]["panel_px"] == 77
