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


def adapt_canvas(width: int, height: int) -> tuple[int, int]:
    """A port of the node's own `adapt_canvas`, value for value.

    Read the source, not the documentation: this takes only the ASPECT RATIO.
    The short edge is forced to 768 and the result is area-capped and rounded
    to 32, so a canvas is never honoured -- it is rewritten, and a request
    smaller than native is scaled UP rather than refused.
    """
    ratio = width / height
    if ratio >= 1.0:
        nominal_w, nominal_h = BASE_SHORT_EDGE * ratio, float(BASE_SHORT_EDGE)
    else:
        nominal_w, nominal_h = float(BASE_SHORT_EDGE), BASE_SHORT_EDGE / ratio
    if nominal_w * nominal_h > MAX_PIXELS:
        scale = math.sqrt(MAX_PIXELS / (nominal_w * nominal_h))
        nominal_w, nominal_h = nominal_w * scale, nominal_h * scale
    return (max(CANVAS_MULTIPLE, round(nominal_w / CANVAS_MULTIPLE) * CANVAS_MULTIPLE),
            max(CANVAS_MULTIPLE, round(nominal_h / CANVAS_MULTIPLE) * CANVAS_MULTIPLE))


def check_canvas(width: int, height: int) -> None:
    """Raise unless the canvas is a FIXED POINT of the node's own transform.

    The previous guard asserted a hand-derived property -- "a multiple of 32,
    under the pixel cap" -- and the node validates nothing of the sort.  It
    rewrites.  `check_canvas(640, 384)` passed clean and rendered 1280x768,
    because 640x384 satisfies both hand-derived conditions and is still not
    what H3 will draw.

    Asking whether the node would change the canvas cannot be wrong about what
    the node does, because it asks the node's own function.
    """
    adapted = adapt_canvas(width, height)
    if adapted != (width, height):
        raise ValueError(
            f"H3 would render {adapted[0]}x{adapted[1]}, not {width}x{height}; "
            "the short edge is always 768 and only the ratio is yours"
        )
