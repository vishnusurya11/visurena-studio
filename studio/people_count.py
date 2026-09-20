"""Does a take grow people?  Clones, counted per frame.

The owner, 2026-09-19: "some characters duplicates and all".  A character
sheet is a TURNAROUND -- the same man drawn five times -- and a crowd lives in
some location wides, so a take can render the hero twice.

A CLONE is a face big enough to be a staged character (a fraction of frame
height) beyond the number of people the shot planned.  Faces below BIG_FACE are
the crowd painted into the location picture and are never counted.
"""
from __future__ import annotations

BIG_FACE = 0.12
"""A staged character's face fills at least this much of the frame's height.
The pit crowd on the rim measures 0.02-0.06; a planned medium-close face 0.2-0.6."""


def clones(face_heights: list[float], planned: int) -> int:
    """How many big faces this frame has beyond the people the shot planned."""
    big = [h for h in face_heights if h >= BIG_FACE]
    return max(0, len(big) - planned)


def summarise_people(per_frame: list[list[float]], planned: int) -> dict:
    counts = [clones(f, planned) for f in per_frame]
    return {"planned": planned, "frames": len(per_frame),
            "clone_frames": sum(1 for c in counts if c), "worst_extra": max(counts, default=0)}
