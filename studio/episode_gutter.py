"""The gutter guard: H3 continues the storyboard sheet a panel was cut from.

MEASURED on episode 1 (2026-09-10): the panels were gutter-free, yet four
takes (T12, T13, T18, T19) ended with a paper-white band along the bottom and
the grey top of a "next cell" beneath it, growing over the take; the owner
saw it as a white bar at 28 s and 37 s.  The panel is clean, so the picture
is guarded at the cut: the widest paper-white band on any sampled frame of a
take is cropped off every frame, and the take is scaled back to the frame.
"""
from __future__ import annotations

import numpy as np

WHITE, FLAT = 190.0, 30.0
"""A gutter row is bright AND flat; a lit wall is bright and textured."""
MAX_FRAC = 0.08
MARGIN = 2

EDGES = {"top": (0, 1), "bottom": (0, -1), "left": (1, 1), "right": (1, -1)}


def band(grey: np.ndarray, edge: str) -> int:
    """Pixels to cut from `edge`: up to the outermost paper-white line found
    within MAX_FRAC of the side, plus MARGIN.  Zero when there is none."""
    axis, direction = EDGES[edge]
    lines = grey if axis == 0 else grey.T
    lines = lines[::-1] if direction < 0 else lines
    limit = round(lines.shape[0] * MAX_FRAC)
    found = 0
    for i in range(limit):
        if lines[i].mean() > WHITE and lines[i].std() < FLAT:
            found = i + 1
    # A BRIGHT FLAT REGION THAT FILLS THE WHOLE WINDOW IS THE PICTURE.  Leaked
    # paper is a BAND: it starts at the edge and STOPS, with the picture under
    # it.  A pale sky does not stop -- it runs past the window and on into the
    # frame.  MEASURED on episode 8, whose palette is "bleached high-key ... bone
    # white ... under a white sun": Q13_0E is a wide of the plateau and its top
    # 67 rows are sky at mean 198, std 2.5, so this returned its own limit and
    # called a correct picture a gutter.  The three real residues in the same
    # episode run 11 to 12 rows and stop well inside it.
    #
    # Without this the guard would crop 61 pixels off the top of every wide
    # desert shot in Part Two and scale the rest up, which is a defect in the
    # delivered picture rather than a repair.
    if found >= limit:
        return 0
    return min(found + MARGIN, limit) if found else 0


def box(frames: list[np.ndarray]) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) keeping the widest clean picture on every frame."""
    h, w = frames[0].shape
    cut = {edge: max(band(f, edge) for f in frames) for edge in EDGES}
    return cut["left"], cut["top"], w - cut["right"], h - cut["bottom"]


def crop_filter(box_: tuple[int, int, int, int], w: int, h: int) -> str:
    left, top, right, bottom = box_
    if (left, top, right, bottom) == (0, 0, w, h):
        return ""
    return f"crop={right - left}:{bottom - top}:{left}:{top}"
