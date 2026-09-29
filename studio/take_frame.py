"""G-FRAME: a take fills its square frame.

ep14 T26 (2026-09-29): the video model drew a silent insert as a widescreen
picture inside the square -- 54 of 256 rows black at the top and as many at the
bottom -- from a full-frame panel, and every take row passed it.  The frame is
read with the plate gate's own measure (flat bands at the top AND the bottom),
on a few frames past the head.  HARD: a letterbox is never the picture planned.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from studio import plate_gate
from studio.take_verdict import Gate

SAMPLES = 3
PENALTY = 60.0


def row_of(frames: list[Image.Image]) -> Gate:
    """The letterbox row over these frames: how many are letterboxed."""
    boxed = sum(1 for im in frames if plate_gate.letterboxed(im))
    return Gate("letterbox", boxed, boxed == 0, True, f"{boxed}/{len(frames)} frames letterboxed",
                PENALTY if boxed else 0.0)


def row(video: Path, seconds: float, work: Path) -> Gate:
    """The row for one take file: SAMPLES frames past the head, read alone."""
    from studio import frames
    Path(work).mkdir(parents=True, exist_ok=True)
    shots = [frames.frame_at(video, at, Path(work) / f"{Path(video).stem}_box{i}.png")
             for i, at in enumerate(frames.frame_times(seconds, SAMPLES))]
    return row_of([Image.open(p).convert("RGB") for p in shots])
