"""Stills from a take for the vision model to read.

H3 shows its reference sheet for the first second of every clip (Scarlet run
4), so no sample lands inside that head leak.  Kept apart from any identity
scorer: the trait card (`studio.describe`) is the gate, this only grabs frames.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

HEAD_LEAK_SECONDS = 1.0


def frame_times(seconds: float, count: int = 3, head: float = HEAD_LEAK_SECONDS) -> list[float]:
    """Sample points spread over the clip, none inside the head leak."""
    usable = max(seconds - head, 0.1)
    return [round(head + usable * (i + 0.5) / count, 3) for i in range(count)]


def frame_at(video: Path, seconds: float, dest: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{seconds:.3f}", "-i", str(video),
                    "-frames:v", "1", str(dest)], check=True)
    return dest
