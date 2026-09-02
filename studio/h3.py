"""MiniMax-H3's hard constants, taken from comfy_extras/nodes_minimax_h3.py.

These are not preferences.  The node snaps an off-grid frame count UP and
area-scales an oversized canvas DOWN, both silently, so a job that asked for
something illegal renders something else and never says so.  Checking here
turns a silent substitution into a loud error.
"""
from __future__ import annotations

import math

CANVAS_MULTIPLE = 32
BASE_SHORT_EDGE = 768
MAX_PIXELS = 768 * 1344
FPS = 24
FRAME_MODULUS = 17
FRAME_REMAINDER = 5

NATIVE_W, NATIVE_H = 1344, 768
"""Native canvas and the pixel cap at once -- there is nothing above this."""


def legal_frames(count: int) -> int:
    """Round a frame count up onto H3's grid: frames % 17 == 5."""
    if count < FRAME_REMAINDER:
        return FRAME_REMAINDER
    while count % FRAME_MODULUS != FRAME_REMAINDER:
        count += 1
    return count


def frames_for(seconds: float) -> int:
    """The legal frame count COVERING a duration, at H3's fixed 24 fps.

    Ceil, never round: a clip one frame short of its slot leaves a hole in
    the cut, and the hole is silent until the assemble step.
    """
    if seconds <= 0:
        raise ValueError(f"duration must be positive, got {seconds}")
    return legal_frames(math.ceil(seconds * FPS))


def seconds_for(frames: int) -> float:
    """What a frame count actually plays for.  Always check against the ask."""
    return frames / FPS


def check_canvas(width: int, height: int) -> None:
    """Raise unless the canvas is one H3 will honour rather than rewrite."""
    if width % CANVAS_MULTIPLE or height % CANVAS_MULTIPLE:
        raise ValueError(f"{width}x{height} is not a multiple of {CANVAS_MULTIPLE}")
    if width * height > MAX_PIXELS:
        raise ValueError(
            f"{width}x{height} = {width * height}px exceeds the {MAX_PIXELS}px cap; "
            "H3 would silently area-scale it back"
        )
