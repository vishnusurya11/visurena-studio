"""Lag between two tracks, from the cross-correlation of their envelopes.

Used as the sync gate on an anchored H3 take: the take's own soundtrack is
the model's regeneration of the anchored wav, so its envelope should sit on
the input's envelope with zero lag.  A lag of one frame (0.042 s) is the
tolerance; anything more means the mouth is not on the wav we play.
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
    return lag_seconds(load_mono(take, sr), load_mono(wav, sr), sr)
