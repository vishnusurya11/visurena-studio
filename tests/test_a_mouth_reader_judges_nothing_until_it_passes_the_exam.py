"""A mouth reader judges nothing until it passes the exam (GAVEL 2026-10-21, step 2).

The exam (studio/measure/mouth_exam.py): on 10 line-driven bench renders the right line must
beat both wrong lines on 9 of 10 and beat its own circular shifts at p < 0.05 on 9 of 10, and on
the two no-audio renders the reader must find the model's own late speech at +12 f and +16 f
within 2 f.  These tests run the grading on synthetic series only; the recorded readers are
graded in test_the_mouth_exam_grades_the_recorded_readers.py.  Nothing decodes video.
"""
import numpy as np
import pytest

from studio.measure import mouth, mouth_exam as exam


def gated(seed: int, n: int = 124) -> np.ndarray:
    """A line's per-frame |sample| mean: phrases of noise over a quiet floor."""
    rng = np.random.default_rng(seed)
    on = np.zeros(n)
    t = 6
    while t < n - 20:
        span = int(rng.integers(8, 30))
        on[t:t + span] = 1.0
        t += span + int(rng.integers(4, 16))
    return 0.002 + on * rng.uniform(0.02, 0.1, n)


def late(x: np.ndarray, k: int) -> np.ndarray:
    """`x` moved k frames later, its quietest value filling the start."""
    out = np.roll(x, k)
    out[:k] = x.min()
    return out


def oracle(series, line, window):
    """A reader that IS the voice: FaceMesh's alignment on the series as given."""
    k, corr = mouth.best_lag(series, mouth.zscore(line), window)
    return k, corr, corr >= mouth.CORR_FLOOR


def test_a_line_is_cut_or_padded_with_its_quietest_frame():
    line = np.array([0.5, 0.1, 0.3])
    assert exam.cut(line, 2).tolist() == [0.5, 0.1]
    assert exam.cut(line, 5).tolist() == [0.5, 0.1, 0.3, 0.1, 0.1]


def test_the_right_line_beats_both_wrong_ones_for_a_mouth_on_it():
    lines = {19: gated(1), 22: gated(2), 25: gated(3)}
    assert exam.beats_wrong(oracle, lines[22], lines, 22, 20) is True
    assert exam.beats_wrong(oracle, lines[19], lines, 22, 20) is False


def test_no_shift_reaches_the_true_alignment():
    s = list(exam.shifts(124, 20))
    assert s[0] == 41 and s[-1] == 83 and all(40 < k < 84 for k in s)


def test_the_shift_p_is_conservative():
    assert exam.p_value(0.5, [0.1, 0.2, 0.3]) == pytest.approx(0.25)
    assert exam.p_value(0.5, [0.6, 0.5, 0.3]) == pytest.approx(0.75)


def test_a_mouth_on_its_line_beats_its_shifts():
    line = gated(4)
    assert exam.shift_p(oracle, line, line, 20) < 0.05


def test_a_known_offset_is_found_within_two_frames():
    line = gated(5)
    assert exam.offset_hit(oracle, late(line, 16), line, 16, 20) is True
    assert exam.offset_hit(oracle, late(line, 16), line, 12, 20) is False


def test_a_window_short_of_the_offset_cannot_find_it():
    line = gated(5)
    assert exam.offset_hit(oracle, late(line, 16), line, 16, 12) is False


def test_the_verdict_needs_nine_nine_and_two():
    assert exam.passes({"wrong_line": 9, "shift": 9, "offset": 2}) is True
    assert exam.passes({"wrong_line": 8, "shift": 10, "offset": 2}) is False
    assert exam.passes({"wrong_line": 10, "shift": 10, "offset": 1}) is False


def test_an_oracle_passes_a_synthetic_exam_and_a_swapped_mouth_fails():
    lines = {19: gated(1), 22: gated(2, 141), 25: gated(3)}
    renders = {f"T{t}_{a}": {"take": t, "set": "bench"} for t in lines for a in ("A_s1", "A_s2", "B_s1")}
    renders |= {"T22_N_s1": {"take": 22, "set": "offset", "truth": 12},
                "T25_N_s1": {"take": 25, "set": "offset", "truth": 16}}
    series = {k: late(exam.cut(lines[r["take"]], len(lines[r["take"]])), r.get("truth", 0)) for k, r in renders.items()}
    good = exam.grade(oracle, lines, renders, series, 20)
    assert good["pass"] is True and good["wrong_line"] == 9 and good["offset"] == 2
    series["T22_A_s1"] = exam.cut(lines[19], 141)
    assert exam.grade(oracle, lines, renders, series, 20)["wrong_line"] == 8


def test_an_unread_render_fails_its_criteria():
    lines = {19: gated(1), 22: gated(2), 25: gated(3)}
    renders = {"T22_A_s1": {"take": 22, "set": "bench"}}
    got = exam.grade(oracle, lines, renders, {}, 20)
    assert got["wrong_line"] == 0 and got["shift"] == 0 and got["rows"]["T22_A_s1"]["read"] is False


def test_the_facemesh_fit_is_the_production_alignment():
    line = gated(6)
    ap = 0.05 + 3.0 * late(line, 5)
    k, corr, measured = exam.facemesh_fit(ap, line, 20)
    assert k == 5 and corr > 0.5 and measured is True     # smoothed over 3 frames: the noise drops it from 1
    assert exam.facemesh_fit(np.full(len(line), np.nan), line, 20)[2] is False
