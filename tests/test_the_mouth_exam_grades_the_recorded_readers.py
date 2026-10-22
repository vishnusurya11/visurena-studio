"""The mouth exam on its recorded fixture: 17 renders of the 2026-10-21 lip-sync bench (Jekyll
ep01 T19, T22, T25), the three staged lines and each render's own soundtrack as per-frame
|sample| means (tests/fixtures/mouth/exam_lines.json), and each reader's per-frame series
(exam_facemesh.json, ...).  Rules: docs/audit/2026-10-21_lipsync_audio_ref/exam/PREREG_exam.md.

The exam is first checked against itself: a "mouth" that is the render's own soundtrack must
pass, and a mouth from the other long line must lose the wrong-line test.  Then each reader's
recorded verdict is pinned, so a reader that fails cannot be promoted from advisory by accident.
Nothing decodes video or opens a model.
"""
import json
from pathlib import Path

import numpy as np

from studio.measure import mouth, mouth_exam as exam

FIX = Path(__file__).resolve().parent / "fixtures" / "mouth"


def load(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def lines() -> dict:
    return {int(k): np.array(v) for k, v in load("exam_lines.json")["lines"].items()}


def renders() -> dict:
    return load("exam_lines.json")["renders"]


def soundtrack_fit(series, line, window):
    k, corr = mouth.best_lag(series, line, window)
    return k, corr, corr >= mouth.CORR_FLOOR


def test_the_fixture_holds_the_preregistered_items():
    r = renders()
    assert sum(v["set"] == "bench" for v in r.values()) == 10 and len(r) == 17
    assert {k: v["truth"] for k, v in r.items() if v["set"] == "offset"} == {"T22_N_s1": 12, "T25_N_s1": 16}
    assert all(len(v["own"]) == v["frames"] for v in r.values())


def test_a_mouth_that_is_its_own_soundtrack_passes_the_exam():
    """The exam can be passed: the bench soundtracks sit on their lines, the N soundtracks are late."""
    own = {k: np.array(v["own"]) for k, v in renders().items()}
    got = exam.grade(soundtrack_fit, lines(), renders(), own)
    assert got["pass"] is True, {k: v for k, v in got.items() if k != "rows"}


def test_a_mouth_from_the_other_long_line_loses_the_wrong_line_test():
    r = renders()
    swapped = np.array(r["T19_A_s1"]["own"])
    assert exam.beats_wrong(soundtrack_fit, exam.cut(swapped, 141), lines(), 22) is False


def facemesh() -> dict:
    got = load("exam_facemesh.json")["series"]
    return {k: np.array([np.nan if v is None else v for v in a]) for k, a in got.items()}


def test_the_facemesh_reader_fails_the_exam_so_its_lag_row_stays_advisory():
    """Recorded 2026-10-21 on b5e9cff: a wrong line wins on T19 A_s2, T22 A_s2 and T22 B_s1
    (7 of 10, bar 9); it reads T22 N_s1 at +8 f for +12 and has no correlation on T25 N_s1."""
    got = exam.grade(exam.facemesh_fit, lines(), renders(), facemesh())
    assert (got["wrong_line"], got["shift"], got["offset"], got["pass"]) == (7, 10, 0, False)
    assert got["rows"]["T22_N_s1"]["lag"] == 8
    assert mouth.row({"measured": True, "lag_frames": 8, "lag_s": 0.333, "corr": 0.41}).hard is False


def test_the_facemesh_reader_also_fails_at_its_production_window():
    got = exam.grade(exam.facemesh_fit, lines(), renders(), facemesh(), mouth.WINDOW)
    assert (got["wrong_line"], got["shift"], got["offset"], got["pass"]) == (7, 9, 0, False)
