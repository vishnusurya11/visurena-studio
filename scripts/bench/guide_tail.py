#!/usr/bin/env python
"""The bench's room-tone guide (C1_verdict #8): the voice guide with its silent
pad AFTER the line filled with seeded brown noise at ROOM_DB, in place of the
digital zero `takes_r2v.composite` pads with (`anullsrc`).  Bench only; the
production composite is untouched until block 4 of the bench rules.

The line's own samples and the guide's length never change: only the trailing
exact-zero run is filled.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

ROOM_DB = -50.0


def line_end(samples: np.ndarray) -> int:
    """The index just past the last non-zero sample: the trailing pad starts here."""
    nz = np.flatnonzero(np.asarray(samples) != 0)
    return int(nz[-1]) + 1 if len(nz) else 0


def brown(n: int, seed: int) -> np.ndarray:
    """Seeded brown noise, mean-free, at unit RMS."""
    walk = np.cumsum(np.random.default_rng(seed).standard_normal(n))
    walk -= np.convolve(walk, np.ones(2401) / 2401, mode="same") if n > 2401 else walk.mean()
    rms = float(np.sqrt(np.mean(walk ** 2))) or 1.0
    return walk / rms


def roomtone(src: Path, out: Path, seed: int = 1, db: float = ROOM_DB) -> Path:
    """`src` with its trailing pad at `db` dBFS RMS of brown noise, written to `out` (int16)."""
    import soundfile as sf

    samples, sr = sf.read(str(src), dtype="int16")
    end = line_end(samples)
    pad = brown(len(samples) - end, seed) * (10 ** (db / 20)) * 32767
    filled = samples.copy()
    filled[end:] = np.clip(np.round(pad), -32768, 32767).astype(np.int16)
    sf.write(str(out), filled, sr, subtype="PCM_16")
    return Path(out)
