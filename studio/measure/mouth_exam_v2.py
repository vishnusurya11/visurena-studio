"""The mouth exam, version 2: a reader's LAG is graded against frame-labelled mouths, never
against an estimator's reading of a soundtrack (skeptic 2026-10-21 on v1, findings 1, 2, 4, 7).

v1 (`mouth_exam`) stays as pre-registered and keeps its recorded verdicts.  v2 is what any
FUTURE reader sits, with the same reader contract `fit(series, line, window)`:

1. wrong line -- as v1, on the 10 bench renders, at least 9 of 10;
2. lag -- on every labelled render (line-driven and no-audio alike) the reader's lag is within
   TOL of the labels' own lag (the median offset of the eye-marked open runs' onsets from the
   line's phrase starts) and measured, on SHARE of them and at least LEAST renders; with fewer
   labelled renders the rule is "ungradable" and the exam cannot pass;
3. shift null -- only shifts 2W+1 apart, which can never share a search window; under
   MIN_SHIFTS of them a render's p cannot fall below 0.05, so the rule is "ungradable" and
   reported, never counted.

The window is the production one (`mouth.WINDOW`): a reader is graded as it runs.
"""
from __future__ import annotations

import math

import numpy as np

from studio.measure import mouth, mouth_exam as v1, mouth_motion as mm

WINDOW = mouth.WINDOW
TOL = v1.TOL
SHARE = 0.9
LEAST = 10
MIN_SHIFTS = round(1 / v1.ALPHA) - 1
"""19: with m independent shifts the smallest p is 1 / (1 + m)."""


def onset_offset(start: int, opens, window: int = WINDOW):
    """The labelled onset nearest a phrase start, less that start; None past +-window."""
    near = [a - start for a, _ in opens if abs(a - start) <= window]
    return min(near, key=lambda d: (abs(d), d)) if near else None


def label_lag(opens, line, window: int = WINDOW):
    """The labels' lag: the median onset offset over the line's phrases; None with none."""
    got = [onset_offset(a, opens, window) for a, _ in mm.phrases(np.asarray(line, dtype=float))]
    got = [d for d in got if d is not None]
    return int(round(float(np.median(got)))) if got else None


def independent_shifts(n: int, window: int = WINDOW) -> range:
    """Circular shifts past 2W, each 2W+1 from the next: no two share a search window."""
    return range(2 * window + 1, n - 2 * window, 2 * window + 1)


def shift_p(fit, series, line, window: int = WINDOW) -> float:
    line = v1.cut(line, len(series))
    true = fit(series, line, window)[1]
    return v1.p_value(true, [fit(series, np.roll(line, s), window)[1] for s in independent_shifts(len(line), window)])


def row(fit, lines: dict, render: dict, series, opens, window: int = WINDOW) -> dict:
    """One render: its lag, the labels' lag (None unlabelled), the hit, and on the bench set the
    wrong-line result; a render with no series is unread and fails what it is asked."""
    line = v1.cut(lines[render["take"]], render["frames"])
    truth = label_lag(opens, line, window) if opens else None
    if series is None or len(series) < 4 * window:
        return {"read": False, "truth": truth, "hit": False, "wrong_line": False}
    k, score, measured = fit(series, v1.cut(line, len(series)), window)
    out = {"read": True, "lag": int(k), "score": round(float(score), 3), "truth": truth,
           "hit": truth is not None and bool(measured) and abs(k - truth) <= TOL}
    if render["set"] == "bench":
        out["wrong_line"] = v1.beats_wrong(fit, series, lines, render["take"], window)
    return out


def lag_count(rows: dict):
    """Hits over the labelled renders, or "ungradable" with fewer than LEAST labelled."""
    labelled = [r for r in rows.values() if r["truth"] is not None]
    return sum(r["hit"] for r in labelled) if len(labelled) >= LEAST else "ungradable"


def shift_count(fit, lines: dict, renders: dict, series: dict, window: int):
    """Bench renders at p < ALPHA over independent shifts, or "ungradable" when one cannot reach it."""
    bench = {k: r for k, r in renders.items() if r["set"] == "bench"}
    if any(len(independent_shifts(r["frames"], window)) < MIN_SHIFTS for r in bench.values()):
        return "ungradable"
    return sum(series.get(k) is not None and shift_p(fit, series[k], lines[r["take"]], window) < v1.ALPHA
               for k, r in bench.items())


def grade(fit, lines: dict, renders: dict, series: dict, labels: dict | None = None,
          window: int = WINDOW) -> dict:
    """The whole v2 exam; `labels` maps a render to its eye-marked open runs [[start, end), ...]."""
    labels = labels or {}
    rows = {k: row(fit, lines, r, series.get(k), labels.get(k), window) for k, r in renders.items()}
    wrong = sum(r.get("wrong_line", False) for r in rows.values())
    lag, labelled = lag_count(rows), sum(r["truth"] is not None for r in rows.values())
    ok = wrong >= v1.NEED["wrong_line"] and lag != "ungradable" and lag >= math.ceil(SHARE * labelled)
    return {"wrong_line": wrong, "lag": lag, "labelled": labelled, "pass": bool(ok),
            "shift": shift_count(fit, lines, renders, series, window), "rows": rows}
