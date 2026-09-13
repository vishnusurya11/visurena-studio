"""G4.3-4.4 -- the cut-landing gate: synthetic signatures only, no ffmpeg, no
take on disk, no money.  Every threshold asserted here is the calibration from
review8/transitions.md (24 cuts of iteration 4, plus iteration 3's failures).
"""
from __future__ import annotations

import numpy as np

from studio import cut_landing as cl


def unit(seed: int) -> np.ndarray:
    v = np.random.default_rng(seed).normal(size=64)
    return v / np.linalg.norm(v)


A, B, C, PLATE = unit(1), unit(2), unit(3), unit(4)
OWN = {"Q01_0.png": A, "Q01_1.png": B}
OTHER = {"Q05_0.png": C, "plate_x.png": PLATE}
ANCHORS = [["Q01_0.png", 0], ["Q01_1.png", 77]]


def take(sequence: list[tuple[np.ndarray, int]]) -> list[dict]:
    sig = np.concatenate([np.repeat(v[None], n, axis=0) for v, n in sequence])
    return cl.classify(sig, OWN, OTHER)


def test_the_thresholds_are_the_measured_gap():
    """Honoured cuts landed -3..+1; the failures +34, +51, -11, -24.  Foreign runs
    were 25-57 frames against a 7-frame matcher flicker; ping-pongs 36 and 92."""
    assert (cl.MAX_EARLY, cl.MAX_LATE) == (4, 6)
    assert cl.MAX_FOREIGN_RUN == 12 and cl.MAX_PINGPONG == 12
    assert cl.LAND == 0.60 and cl.FOREIGN_MARGIN == 0.05 and cl.FOREIGN_MIN == 0.60


def test_a_frame_that_matches_nothing_is_not_a_foreign_picture():
    """Iteration 4 T03, the cab mid-crossing: own 0.39, other 0.45.  Without the
    floor that reads FOREIGN; it is a frame off its own composition, which is
    drift's business, not a foreign picture's."""
    basis, _ = np.linalg.qr(np.random.default_rng(11).normal(size=(64, 3)))
    mine, theirs, rest = basis[:, 0], basis[:, 1], basis[:, 2]

    def frame(own_s, other_s):
        v = own_s * mine + other_s * theirs
        return v + np.sqrt(max(0.0, 1 - v @ v)) * rest

    weak = cl.classify(frame(0.39, 0.45)[None], {"Q01_0.png": mine}, {"Q05_0.png": theirs})[0]
    assert round(weak["own_s"], 2) == 0.39 and round(weak["other_s"], 2) == 0.45
    assert weak["other_s"] > weak["own_s"] + cl.FOREIGN_MARGIN and not weak["foreign"]
    real = cl.classify(frame(0.30, 0.72)[None], {"Q01_0.png": mine}, {"plate_x.png": theirs})[0]
    assert real["foreign"] and real["other"] == "plate_x.png"


def test_classify_names_the_closest_own_cell_and_flags_foreign():
    rows = take([(A, 2), (PLATE, 1)])
    assert [r["own"] for r in rows[:2]] == ["Q01_0.png", "Q01_0.png"]
    assert rows[2]["foreign"] and rows[2]["other"] == "plate_x.png"
    assert not rows[0]["foreign"]


def test_every_value_classify_returns_is_json_writable():
    """episode_home.write_json has no `default=`: a numpy bool in the row would raise
    TypeError at the end of the DQ, after the whole take had been decoded."""
    import json
    rows = take([(A, 1), (PLATE, 1)])
    assert json.dumps(rows)
    assert all(type(r["foreign"]) is bool and type(r["own_s"]) is float for r in rows)


def test_start_pins_keeps_first_pin_per_cell_and_drops_end_cells():
    anchors = [["Q02_0.png", 0], ["Q02_1.png", 97], ["Q02_0E.png", 93], ["Q02_1.png", 205]]
    assert cl.start_pins(anchors) == [("Q02_0.png", 0), ("Q02_1.png", 97)]


def test_cut_on_the_pin_passes():
    rows = cl.landing(take([(A, 77), (B, 98)]), ANCHORS)
    assert rows[0]["landed"] == 77 and rows[0]["delta"] == 0
    assert cl.verdict(rows)["passed"]


def test_cut_three_frames_early_passes_and_late_fails():
    early = cl.landing(take([(A, 74), (B, 101)]), ANCHORS)
    assert early[0]["delta"] == -3 and cl.verdict(early)["passed"]
    late = cl.landing(take([(A, 111), (B, 64)]), ANCHORS)          # T09: pin ignored, cut at 111
    assert late[0]["delta"] == 34 and not cl.verdict(late)["passed"]
    assert "landed 34" in cl.verdict(late)["reason"]


def test_cut_a_second_early_fails():
    rows = cl.landing(take([(A, 66), (B, 109)]), ANCHORS)          # iteration-3 T01: -11
    assert rows[0]["delta"] == -11 and not cl.verdict(rows)["passed"]


def test_plate_at_the_cut_fails_and_names_it():
    """T01 iteration 4: 40 frames of plate_criterion pulled in across the cut."""
    rows = cl.landing(take([(A, 74), (PLATE, 40), (B, 61)]), ANCHORS)
    assert rows[0]["foreign_run"] == 40 and rows[0]["foreign_cell"] == "plate_x.png"
    v = cl.verdict(rows)
    assert not v["passed"] and "plate_x.png" in v["reason"]


def test_pingpong_back_to_the_earlier_cell_fails():
    rows = cl.landing(take([(A, 77), (B, 10), (A, 36), (B, 52)]), ANCHORS)   # T02: 36 frames back
    assert rows[0]["delta"] == 0 and rows[0]["pingpong"] == 36 and rows[0]["pingpong_to"] == "Q01_0.png"
    assert not cl.verdict(rows)["passed"]


def test_brief_flicker_within_thresholds_passes():
    rows = cl.landing(take([(A, 77), (B, 20), (A, 6), (B, 72)]), ANCHORS)
    assert rows[0]["pingpong"] == 6 and cl.verdict(rows)["passed"]


def test_never_landing_fails():
    rows = cl.landing(take([(A, 175)]), ANCHORS)
    assert rows[0]["landed"] is None and not cl.verdict(rows)["passed"]


def test_a_take_with_no_internal_cut_has_nothing_to_land():
    rows = cl.landing(take([(A, 120)]), [["Q00_0.png", 0]])
    assert rows == [] and cl.verdict(rows)["passed"]


def test_token_start_follows_the_1_4_4_4_4_cycle():
    assert all(cl.token_start(f) for f in (0, 1, 5, 9, 13, 17, 18, 22, 69, 73, 77, 85, 86))
    assert not any(cl.token_start(f) for f in (49, 89, 97, 121, 189))


def test_the_foreign_set_carries_the_location_plates(tmp_path):
    """The plates were missing from the foreign set, which is why T01's 40 frames of
    plate_criterion were logged as 'Q21_0 0.444' instead of a foreign picture."""
    for name in ("Q01_0.png", "Q01_1.png", "Q05_0.png", "Q05_0E.png", "plate_criterion.png", "ref_take_01.png"):
        (tmp_path / name).write_bytes(b"")
    assert cl.foreign_names(tmp_path, {"Q01_0.png", "Q01_1.png"}) == \
        ["Q05_0.png", "Q05_0E.png", "plate_criterion.png"]


def test_a_cells_own_end_picture_is_not_foreign_to_that_cell(tmp_path):
    """A segment is SENT from its cell toward that cell's END picture, so arriving
    there is the take doing as it was told.  Once the END pins were removed the END
    cell stopped being an anchor, and every successful arrival read as somebody
    else's shot: on iteration 5 T02 matched its own Q02_0E at 0.988 and T03 matched
    Q03_0E at 0.978, and both were failed and queued for a retake for it."""
    for name in ("Q02_0.png", "Q02_0E.png", "Q02_1.png", "Q10_1.png", "Q10_1E.png"):
        (tmp_path / name).write_bytes(b"")
    assert cl.foreign_names(tmp_path, {"Q02_0.png", "Q02_1.png"}) == ["Q10_1.png", "Q10_1E.png"]
