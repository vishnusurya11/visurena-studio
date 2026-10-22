"""The exam a mouth reader passes before it judges anything (GAVEL 2026-10-21, step 2).

A reader is one `fit(series, line, window) -> (lag_frames, score, measured)`: its best alignment
of a render's mouth series against a line's per-frame |sample| mean within +-window frames.
Three criteria, pre-registered in docs/audit/2026-10-21_lipsync_audio_ref/exam/PREREG_exam.md:

1. wrong line -- on the line-driven bench renders, the right line scores above both wrong lines
   on at least 9 of 10;
2. shift null -- the right line beats its own circular shifts (each shift past twice the window,
   so its search never reaches the true alignment) at p < 0.05 on at least 9 of 10;
3. known offset -- on the no-audio renders, where the model spoke the line itself late
   (+12 f on T22, +16 f on T25), the reader finds that offset within 2 f, measured, on 2 of 2.

A render the reader has no series for fails criteria 1 and 2.
"""
from __future__ import annotations

import numpy as np

from studio.measure import mouth

WINDOW = 20
"""Frames each way for every criterion: the largest known offset (16 f), its 2 f, and 2 to spare."""
TOL = 2
NEED = {"wrong_line": 9, "shift": 9, "offset": 2}
ALPHA = 0.05


def cut(line: np.ndarray, n: int) -> np.ndarray:
    """The line over n frames: cut, or padded with its quietest frame (its own silence)."""
    line = np.asarray(line, dtype=float)
    if len(line) >= n:
        return line[:n].copy()
    return np.concatenate([line, np.full(n - len(line), line.min())])


def beats_wrong(fit, series, lines: dict, own, window: int = WINDOW) -> bool:
    """The right line's score is above every wrong line's, each over the series' frames."""
    n = len(series)
    score = {k: fit(series, cut(v, n), window)[1] for k, v in lines.items()}
    return all(score[own] > s for k, s in score.items() if k != own)


def shifts(n: int, window: int = WINDOW) -> range:
    """Circular shifts whose +-window search can never reach the true alignment."""
    return range(2 * window + 1, n - 2 * window)


def p_value(true: float, null: list[float]) -> float:
    """(1 + shifts scoring at or above the truth) / (1 + shifts): never 0."""
    return (1 + sum(s >= true for s in null)) / (1 + len(null))


def shift_p(fit, series, line, window: int = WINDOW) -> float:
    line = cut(line, len(series))
    true = fit(series, line, window)[1]
    return p_value(true, [fit(series, np.roll(line, s), window)[1] for s in shifts(len(line), window)])


def offset_hit(fit, series, line, truth: int, window: int = WINDOW, tol: int = TOL) -> bool:
    """The reader finds the known offset within tol frames, and stands behind the reading."""
    k, _, measured = fit(series, cut(line, len(series)), window)
    return bool(measured) and abs(k - truth) <= tol


def row(fit, lines: dict, render: dict, series, window: int) -> dict:
    """One render's results; a render with no series is unread and fails what it is asked."""
    if series is None or len(series) < 4 * window:
        return {"read": False, "wrong_line": False, "shift_p": 1.0, "offset": False}
    line = lines[render["take"]]
    k, score, measured = fit(series, cut(line, len(series)), window)
    out = {"read": True, "lag": int(k), "score": round(float(score), 3), "measured": bool(measured)}
    if render["set"] == "offset":
        return out | {"offset": offset_hit(fit, series, line, render["truth"], window)}
    return out | {"wrong_line": beats_wrong(fit, series, lines, render["take"], window),
                  "shift_p": round(shift_p(fit, series, line, window), 3)}


def tally(rows: dict, renders: dict, which: str = "bench") -> dict:
    """Counts per criterion over one set of renders ('bench', or 'driven' = bench + extra)."""
    keep = ("bench", "extra") if which == "driven" else (which,)
    asked = [k for k, r in renders.items() if r["set"] in keep]
    return {"n": len(asked), "wrong_line": sum(rows[k].get("wrong_line", False) for k in asked),
            "shift": sum(rows[k].get("shift_p", 1.0) < ALPHA for k in asked)}


def passes(counts: dict) -> bool:
    return all(counts.get(k, 0) >= need for k, need in NEED.items())


def grade(fit, lines: dict, renders: dict, series: dict, window: int = WINDOW) -> dict:
    """The whole exam: per-render rows, the bench tallies, the offsets found, and the verdict."""
    rows = {k: row(fit, lines, r, series.get(k), window) for k, r in renders.items()}
    counts = tally(rows, renders) | {"offset": sum(rows[k].get("offset", False) for k, r in renders.items()
                                                   if r["set"] == "offset")}
    return counts | {"pass": passes(counts), "driven": tally(rows, renders, "driven"), "rows": rows}


def facemesh_fit(ap, line, window: int = WINDOW):
    """Reader 1, the production FaceMesh ruler (b5e9cff): the aperture filled and smoothed, the
    line z-scored once; measured when the face is readable and the peak clears CORR_FLOOR."""
    ap = np.asarray(ap, dtype=float)
    k, corr = mouth.best_lag(mouth.smooth(mouth.fill(ap)), mouth.zscore(line), window)
    return k, corr, mouth.readable(ap) >= mouth.READABLE and corr >= mouth.CORR_FLOOR
