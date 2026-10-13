"""What pitch a voice clip actually came out at, and whether that is what was asked.

Jekyll ep01 review (docs/audit/2026-10-13_jekyll_ep01_review/SOUND.md): across
the men, the asked register and the rendered pitch were barely correlated --
Hyde asked 92 Hz and rendered ~179, Poole asked 158 and rendered ~99 -- and the
sheet recorded the ask as if it were the measure.  The measure here is the one
that review used: librosa pYIN over 55-400 Hz, median of the voiced frames.
Three estimators agreed with it on the clip that started this.
"""
from __future__ import annotations

from pathlib import Path

FMIN, FMAX = 55.0, 400.0
"""pYIN's search range: under the lowest man (WotW narrator ~100 Hz, the band
floor 75) and over the highest woman (265).  SOUND.md's range."""

TOLERANCE = 0.15
"""How far a design may sit from its asked register, as a share of it.

15 % is ~2.4 semitones: Enfield (asked 108, measured 103) and the policeman
(125 / 121) land inside it; Hyde (92 / 179) and the narrator (191 / 203 after a
175 ask) do not.  Tighter than this refuses voices that read as asked."""


def f0_hz(wav: Path) -> float:
    """The median voiced F0 of a clip in hertz (pYIN, 55-400); 0 when unvoiced."""
    import librosa
    import numpy as np
    audio, rate = librosa.load(str(wav), sr=16000, mono=True)
    f0, voiced, _ = librosa.pyin(audio, fmin=FMIN, fmax=FMAX, sr=rate)
    got = f0[voiced & ~np.isnan(f0)] if f0 is not None else []
    return float(np.median(got)) if len(got) else 0.0


def pitch_error(measured: float, asked: int) -> float:
    """How far the measure sits from the ask, as a share of the ask; 1.0 unvoiced."""
    if measured <= 0 or asked <= 0:
        return 1.0
    return abs(measured - asked) / asked


def pitch_fault(measured: float, asked: int, tolerance: float = TOLERANCE) -> str:
    """Why a design is not the register it was asked for, or "" when it is."""
    if asked <= 0 or pitch_error(measured, asked) <= tolerance + 1e-9:
        return ""
    return (f"renders at {measured:.0f} Hz against an asked {asked} Hz "
            f"(more than {tolerance:.0%} off)")


def steer(measured: float, asked: int, step: int) -> int:
    """Which way the written register moves next: against the miss, never by default."""
    if measured <= 0 or asked <= 0 or measured == asked:
        return 0
    return -step if measured > asked else step
