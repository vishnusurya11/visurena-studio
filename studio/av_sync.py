"""Lag between two tracks, from the cross-correlation of their envelopes.

WHAT THIS MEASURES IS THE MUX, NOT THE MOUTH.  The take's own soundtrack IS
the wav that drove it, re-encoded: MEASURED on episode 10's seven dialogue
takes, sample-level normalised correlation 0.86-0.95 at exactly HANDLE on
every one, and every lag read +0.000 or -0.010.  The number says whether the
sound was laid where we put it.  It cannot say whether the lips are on the
words -- by eye all seven were, and this gate would have read the same if
they were not.  Hence `mux_lag_s` everywhere the number is written or printed,
until a measurement of the mouth exists.

A lag of one frame (0.042 s) is the tolerance for the mux.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

HOP = 0.010
"""Envelope hop in seconds: 10 ms gives a lag resolution well under a frame."""


def envelope(x: np.ndarray, sr: int, hop: float = HOP) -> np.ndarray:
    step = max(int(sr * hop), 1)
    frames = len(x) // step
    e = np.abs(x[:frames * step]).reshape(frames, step).mean(axis=1)
    return (e - e.mean()) / (e.std() + 1e-9)


def lag_seconds(track: np.ndarray, reference: np.ndarray, sr: int, hop: float = HOP) -> float:
    """Positive when `track` is LATE against `reference`."""
    a, b = envelope(track, sr, hop), envelope(reference, sr, hop)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    corr = np.correlate(a, b, mode="full")
    return float((int(np.argmax(corr)) - (n - 1)) * hop)


def load_mono(path: Path, sr: int = 24000) -> np.ndarray:
    """Any audio or video file as mono float samples at `sr`, through ffmpeg."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def take_lag(take: Path, wav: Path, sr: int = 24000) -> float:
    """The MUX lag of a take against the wav that drove it: where the sound was
    laid, not where the mouth is.  Written as `mux_lag_s`."""
    return lag_seconds(load_mono(take, sr), load_mono(wav, sr), sr)


mux_lag = take_lag
"""The honest name; `take_lag` stays for the callers that have it."""
