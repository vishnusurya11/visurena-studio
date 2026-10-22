"""Exam v2: a mouth reader's LAG is graded against frame-labelled mouths, on every labelled render.

Skeptic 2026-10-21 on exam v1 (studio/measure/mouth_exam.py, pre-registered, kept as it was):
- finding 1: v1's known offsets (+12, +16 f) are `best_lag` of each no-audio render's own
  soundtrack, so the oracle's 2 of 2 is built in, and T22 N's curve is a plateau, not a peak;
- finding 2: v1 grades a lag on 2 renders only, so a reader that always says +14 passes;
- finding 4: v1's ~43-60 overlapping shifts hold one or two independent windows;
- finding 7: v1 grades at 20 f, production reads at 12 f.
v2 takes its truth only from labels (eye-marked open runs), grades at the production window, and
counts only shifts that cannot share a window.  No labels exist yet, so no reader can pass v2.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from studio.measure import mouth, mouth_exam as v1, mouth_exam_v2 as v2, mouth_motion as mm

FIX = Path(__file__).resolve().parent / "fixtures" / "mouth"
LATE = [0, 3, -2, 5, 1, -4, 7, 2, -1, 4, 6, -3, 0, 8, 2, 5, -2]


def exam() -> tuple[dict, dict]:
    d = json.loads((FIX / "exam_lines.json").read_text(encoding="utf-8"))
    return {int(k): np.array(v) for k, v in d["lines"].items()}, d["renders"]


def own() -> dict:
    return {k: np.array(v["own"]) for k, v in exam()[1].items()}


def constant_14(series, line, window):
    """No alignment at all: the soundtrack's score, a lag of +14 whatever the mouth does."""
    _, corr = mouth.best_lag(series, line, window)
    return 14, corr, corr >= mouth.CORR_FLOOR


def moved(x: np.ndarray, k: int) -> np.ndarray:
    """`x` k frames later (earlier when k < 0), zeros where it moved away from."""
    if k >= 0:
        return np.concatenate([np.zeros(k), x[:len(x) - k]])
    return np.concatenate([x[-k:], np.zeros(-k)])


def drawn(lines: dict, renders: dict) -> tuple[dict, dict]:
    """A mouth-shaped self-check: each render's mouth open on its line's phrases, a known number
    of frames late, with jitter; its labels are those open runs, as an eye would mark them."""
    series, labels = {}, {}
    for (k, r), late in zip(renders.items(), LATE):
        on = moved(mm.gate(lines[r["take"]], r["frames"]), late)
        series[k] = 0.05 + 0.3 * on + np.random.default_rng(late + 40).normal(0, 0.02, len(on))
        labels[k] = mm.runs(on > 0.5)
    return series, labels


def test_a_reader_that_ignores_alignment_passes_exam_v1():
    lines, renders = exam()
    assert v1.grade(constant_14, lines, renders, own())["pass"] is True


def test_the_soundtrack_truth_of_t22_n_is_a_plateau_not_a_peak():
    lines, renders = exam()
    s, line = own()["T22_N_s1"], lines[22]
    assert mouth.best_lag(s, line, 20)[0] == 12 and mouth.best_lag(s, mm.gate(line, len(line)), 20)[0] == 6
    za, zb = mouth.zscore(s), mouth.zscore(line)
    assert mouth.xcorr_at(za, zb, 12) - mouth.xcorr_at(za, zb, 4) < 0.03


def test_exam_v1s_shifts_hold_too_few_independent_windows():
    assert all(len(v2.independent_shifts(n, w)) < v2.MIN_SHIFTS for n in (124, 141) for w in (12, 20))
    assert list(v2.independent_shifts(141, 12)) == [25, 50, 75, 100]


def test_v2_grades_at_the_production_window():
    assert v2.WINDOW == mouth.WINDOW


def test_label_lag_is_the_median_onset_offset_of_the_marked_runs():
    line = np.zeros(80)
    line[[*range(6, 20), *range(40, 52), *range(66, 74)]] = 1.0
    assert v2.label_lag([[9, 22], [43, 50], [68, 75]], line) == 3
    assert v2.label_lag([[9, 22], [90, 91]], line) == 3
    assert v2.label_lag([], line) is None


def test_without_labels_the_lag_is_ungradable_and_nothing_passes():
    lines, renders = exam()
    got = v2.grade(constant_14, lines, renders, own())
    assert got["lag"] == "ungradable" and got["pass"] is False and got["shift"] == "ungradable"


def test_too_few_labelled_renders_are_ungradable():
    lines, renders = exam()
    series, labels = drawn(lines, renders)
    got = v2.grade(mm.fit, lines, renders, series, dict(list(labels.items())[:v2.LEAST - 1]))
    assert got["lag"] == "ungradable" and got["pass"] is False


def test_a_mouth_shaped_self_check_passes_v2_and_a_constant_lag_fails_it():
    lines, renders = exam()
    series, labels = drawn(lines, renders)
    good = v2.grade(mm.fit, lines, renders, series, labels)
    assert good["pass"] is True and good["lag"] == len(renders), {k: v for k, v in good.items() if k != "rows"}
    assert [good["rows"][k]["truth"] for k in renders] == LATE

    def constant_2(s, line, window):
        return 2, *mm.fit(s, line, window)[1:]
    assert v2.grade(constant_2, lines, renders, series, labels)["pass"] is False


@pytest.mark.parametrize("name, fit", [("exam_facemesh.json", v1.facemesh_fit), ("exam_motion.json", mm.fit)])
def test_the_recorded_readers_cannot_pass_v2_until_mouths_are_labelled(name, fit):
    lines, renders = exam()
    got = v2.grade(fit, lines, renders, mm.load_series(FIX / name))
    assert got["lag"] == "ungradable" and got["pass"] is False
