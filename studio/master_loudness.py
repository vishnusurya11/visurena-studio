"""The master's integrated loudness, lifted into the band before the name goes on it.

ep20 (2026-10-08 03:30Z): QC refused a finished master at -17.49 LUFS against
the (-15.5, -12.5) band after four hours of pictures.  The lines were levelled
exactly as ep19's (-20.3 LUFS each), the picture was clean; the 3.3 dB gap was
the BED -- a quiet chapter mixes quieter tones (light, plain) than a thrilling
one, so the master's integrated loudness swings with the mood while the wall
stands still (`feedback_constants_outlive_their_world`).  The platform
normalises to -14 LUFS anyway; the master is lifted to it through a true-peak
limiter, video copied, and QC measures the lifted file.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

LUFS_BAND = (-15.5, -12.5)
"""The master's integrated loudness band (QC's wall; YouTube normalises to -14)."""
TARGET_LUFS = -14.0
TRUE_PEAK_DBTP = -1.5


def gain_for(lufs: float, band: tuple[float, float] = LUFS_BAND, target: float = TARGET_LUFS) -> float:
    """dB to add: 0.0 inside the band, else the step to the target."""
    if band[0] <= lufs <= band[1]:
        return 0.0
    return round(target - lufs, 2)


def lift_argv(src: Path, out: Path, gain_db: float, tp: float = TRUE_PEAK_DBTP) -> list[str]:
    """ffmpeg: the audio through a gain and a true-peak limiter, the video copied."""
    limit = round(10 ** (tp / 20.0), 4)
    return ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c:v", "copy",
            "-af", f"volume={gain_db:+.2f}dB,alimiter=limit={limit}:attack=5:release=50:level=false",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]


def into_band(path: Path, work: Path, measure: Callable[[Path], float],
              run: Callable[..., object] = subprocess.run) -> Path:
    """The master itself when its loudness is in the band; else the lifted copy
    in `work`, re-measured and printed.  Never raises on the measure: the
    lift is a courtesy to the wall, QC still judges the file."""
    lufs = measure(Path(path))
    gain = gain_for(lufs)
    if gain == 0.0:
        return Path(path)
    out = Path(work) / f"{Path(path).stem}.lifted{Path(path).suffix}"
    run(lift_argv(Path(path), out, gain), check=True)
    print(f"  loudness: {lufs:.2f} LUFS outside {LUFS_BAND}; lifted {gain:+.2f} dB -> {measure(out):.2f} LUFS")
    return out
