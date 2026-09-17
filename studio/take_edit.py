"""G-EDIT -- two things the cut detector surfaced on episode 10 that no row saw.

Both read the same free series: the mean |difference| between consecutive
frames of the take on a 64x64 grey (dq10/G `framediff.py`), the number whose
spikes are cuts and whose baseline is motion.

post-cut   The edit trims 6-22 frames off every take (HANDLE + the token grid),
           so a take's last rendered frames are never in the cut.  T28
           collapsed two frames past its cut -- placed tail mean 4.06, trimmed
           remainder 8.55 with every frame over 8 -- and T29 went 1.45 -> 5.07:
           a take at its edge INSIDE the cut, where the viewer sees the run-up
           (T28's crown already out, motion 5x its first quarter) and not the
           fall.  ep05 and ep07 under the same rule: none.  Fires when the
           trimmed frames' mean step is over POST_CUT_RATIO times the last
           TAIL placed steps' mean AND their peak is over POST_CUT_MAX.
           ep10, all 30 kept takes: T28 (4.07 -> 8.48, max 14.5) and T29
           (1.44 -> 5.06, max 8.6) fire; T04 (2.21 -> 2.60, max 6.7) and T06
           (4.86 -> 5.84) do not.

pulse      T05 breathes: a ~22-frame period in motion over six cycles, peaks
           10-14 on a baseline of 1-3.  Churn averaged it to 3.5, zoom netted
           it to 0.99x, score 100.  The series is detrended by a DETREND-frame
           moving mean (so an accelerating push, which is a trend, cannot
           correlate with itself) and its autocorrelation read at every lag
           from PULSE_LAGS[0] to PULSE_LAGS[1]; a lag whose correlation stays
           over PULSE_R at one, two and three multiples (three cycles) with a
           residual at least PULSE_AMP of the median step is a pulse.  The
           period named is the FUNDAMENTAL (the first autocorrelation peak):
           ep10's current T04 fires at lag 24 because every fourth frame step
           is 0 and the next 2x -- a 4-frame stutter, named "4f", not a breath.
           ep10, all 30 kept takes: T05 (23f, 4 cycles, r 0.85, amp 0.65) and
           T04 (4f, r 0.83, amp 0.69) fire; T20 (r 0.53 at 34f), T21 (0.73 at
           12f) and T01/T03/T33 (0.50-0.51) sit under the amplitude floor at
           0.11-0.18, so the correlation there is on grain.

Both ADVISORY, scored.  Free: ffmpeg + numpy, no GPU, no credit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

FPS = 24
DOWN = 64
TAIL = 10
POST_CUT_RATIO, POST_CUT_MAX = 2.0, 8.0
PULSE_LAGS = (12, 36)
PULSE_R, PULSE_CYCLES, PULSE_AMP = 0.5, 3, 0.5
DETREND = 73
"""Odd; two of the longest lag plus one, so no trend slower than a pulse survives."""
MARGIN = 8
"""Pairs a lag must leave to be read: a correlation over fewer is a coincidence."""
PENALTY = 5.0
FRAME_EXT = (".png", ".jpg", ".jpeg")


# ---- the series -----------------------------------------------------------------

def frames(video: Path, seconds: float) -> np.ndarray:
    """Grey frames (n, DOWN, DOWN) float32 of the take.  A folder of images serves the same."""
    video = Path(video)
    if video.is_dir():
        names = sorted(p for p in video.iterdir() if p.suffix.lower() in FRAME_EXT)
        return np.stack([np.asarray(Image.open(p).convert("L").resize((DOWN, DOWN), Image.BILINEAR)) for p in names]).astype(np.float32)
    cut = ["-t", f"{seconds:.3f}"] if seconds else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), *cut, "-vf", f"scale={DOWN}:{DOWN}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, DOWN, DOWN).astype(np.float32)


def diff_series(fr: np.ndarray) -> np.ndarray:
    """Mean |difference| per frame step; d[i] is between frame i and i + 1."""
    if len(fr) < 2:
        return np.zeros(0, dtype=np.float32)
    return np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))


# ---- post-cut -------------------------------------------------------------------

def post_cut(d: np.ndarray, placed_frames: int) -> dict:
    """The trimmed tail against the last TAIL placed steps; {} when nothing is trimmed."""
    p = placed_frames
    if len(d) <= p - 1 or p < 2:
        return {}
    last = float(d[max(0, p - TAIL - 1):p - 1].mean())
    rest = d[p - 1:]
    fires = float(rest.mean()) > POST_CUT_RATIO * last and float(rest.max()) > POST_CUT_MAX
    return {"fires": fires, "last": round(last, 2), "rest": round(float(rest.mean()), 2),
            "rest_max": round(float(rest.max()), 2), "trim": int(len(rest))}


def post_cut_row(pc: dict):
    """ADVISORY, scored: the take collapsed in the frames the edit trims."""
    from studio.take_verdict import Gate
    if not pc:
        return Gate("post-cut", None, True, False, "not measured")
    note = f"{pc['last']:.2f}->{pc['rest']:.2f} max {pc['rest_max']:.1f}"
    return Gate("post-cut", pc["rest"], not pc["fires"], False, note, PENALTY if pc["fires"] else 0.0)


# ---- pulse ----------------------------------------------------------------------

def detrended(d: np.ndarray) -> np.ndarray:
    """The series less its DETREND-frame centred moving mean (edges held)."""
    pad = DETREND // 2
    return d - np.convolve(np.pad(d, pad, mode="edge"), np.ones(DETREND) / DETREND, mode="valid")


def autocorr(r: np.ndarray, lag: int) -> float:
    """Pearson correlation of the series with itself `lag` steps on."""
    a, b = r[:-lag], r[lag:]
    if len(a) < MARGIN or a.std() < 1e-6 or b.std() < 1e-6:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def cycles(acf: dict[int, float], lag: int) -> int:
    """How many multiples of `lag` in a row the correlation stays over PULSE_R."""
    k = 0
    while (k + 1) * lag in acf and acf[(k + 1) * lag] > PULSE_R:
        k += 1
    return k


def fundamental(acf: dict[int, float]) -> int | None:
    """The first peak of the autocorrelation over PULSE_R: the period itself,
    which a lag search may only see a multiple of (T04's 4-frame stutter at 24)."""
    for lag in range(3, PULSE_LAGS[1] + 1):
        if acf.get(lag, 0.0) > PULSE_R and acf[lag] > acf.get(lag - 1, 0.0) and acf[lag] >= acf.get(lag + 1, -1.0):
            return lag
    return None


def pulse(d: np.ndarray) -> dict:
    """The best lag in PULSE_LAGS, its cycles and correlation, and whether it is a pulse."""
    quiet = {"fires": False, "period": 0, "lag": 0, "cycles": 0, "r": 0.0, "amp": 0.0}
    if len(d) < PULSE_LAGS[0] * PULSE_CYCLES + MARGIN:
        return quiet
    r = detrended(d)
    acf = {lag: autocorr(r, lag) for lag in range(2, len(d) - MARGIN)}
    lag = max(range(PULSE_LAGS[0], PULSE_LAGS[1] + 1), key=lambda L: (cycles(acf, L), acf.get(L, 0.0)))
    amp = float(r.std()) / max(float(np.median(d)), 0.1)
    n = cycles(acf, lag)
    return {"fires": n >= PULSE_CYCLES and amp >= PULSE_AMP, "period": fundamental(acf) or lag, "lag": lag,
            "cycles": n, "r": round(acf.get(lag, 0.0), 2), "amp": round(amp, 2)}


def pulse_row(p: dict):
    """ADVISORY, scored: the take breathes (or stutters) with a period."""
    from studio.take_verdict import Gate
    note = f"{p['period']}f x{p['cycles']} r {p['r']:.2f}" if p["fires"] else f"r {p['r']:.2f}"
    return Gate("pulse", p["r"], not p["fires"], False, note, PENALTY if p["fires"] else 0.0)


# ---- the rows -------------------------------------------------------------------

def rows(video: Path, seconds: float, placed_seconds: float) -> list:
    """The post-cut and pulse rows for one take, off one decode."""
    d = diff_series(frames(video, seconds))
    return [post_cut_row(post_cut(d, int(round(placed_seconds * FPS)))), pulse_row(pulse(d))]
