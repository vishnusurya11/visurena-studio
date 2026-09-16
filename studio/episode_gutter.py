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

WHITE, FLAT = 190.0, 8.0
"""A gutter row is bright AND flat; a lit wall is bright and textured.

FLAT WAS 30.0 AND THAT WAS A NUMBER FROM A DARKER BOOK. Episodes 1 to 7 are
soot-black gaslit London, where nothing bright is ever also smooth, so a loose
floor cost nothing. Part Two is a bleached desert under a white sun, and 30.0
then admits the sky.

MEASURED, episode 9: `Q00_0` and `Q01_0` are wides of the valley of Utah at
sunrise. Their top 50 and 16 rows read mean 203 and 200 at **std 16.9 and 13.5**
-- bright, and smooth enough for 30.0. Both were called leaked paper, and the
cost of that one false positive ran the whole length of the pipeline: the sheet
DQ failed a setup whose four pictures were correct, a $0.13 STRICT redraw was
bought and read the same, the take guard cropped 52 and 51 px of real picture off
T00 and T01, and the EDIT gate then failed the master because a cropped segment
no longer matches the take it was cut from.

Calibrated against every band this function finds across every cell of every
episode on disk -- there are exactly two, and they are those two skies:

    real leaked paper       std 2-5      (episode 3's residues)
    episode 9's pale sky    std 13.5, 16.9

The two populations do not overlap and the gap is empty, so the floor sits in the
middle of it. `found >= limit` below covers the OTHER sky -- the one that fills
the window and runs on (episode 8's Q13_0E, 67 rows at std 2.5). This one STOPS,
where the mountains begin, so by shape it is a band; only flatness tells them
apart."""
MAX_FRAC = 0.08
MARGIN = 2
DROP = 25.0
"""How much darker the picture under a leaked gutter is than the gutter itself.

Paper is the brightest thing in the frame; the scene beneath it is the scene. A
run that ends at something no darker than itself is sky ending in more sky. The
two cases on disk are 100+ grey levels apart, so this is nowhere near either:

    episode 1's white bar    paper ~250 over a night street
    episode 9's T06 / T09    run at ~196, and what follows is 214 and 206
"""

EDGES = {"top": (0, 1), "bottom": (0, -1), "left": (1, 1), "right": (1, -1)}


def band(grey: np.ndarray, edge: str) -> int:
    """Pixels to cut from `edge`: up to the outermost paper-white line found
    within MAX_FRAC of the side, plus MARGIN.  Zero when there is none."""
    axis, direction = EDGES[edge]
    lines = grey if axis == 0 else grey.T
    lines = lines[::-1] if direction < 0 else lines
    limit = round(lines.shape[0] * MAX_FRAC)
    # THE OUTERMOST qualifying line is the depth, not a contiguous run from the
    # edge. A LEAK IS LAYERED and it need not touch the edge: episode 1's is
    # "a paper-white band along the bottom AND THE GREY TOP OF A NEXT CELL
    # BENEATH IT", so paper, then cell, then paper again; and episode 8's Q17_0
    # and Q18_0 carry theirs at rows 8 to 19 FROM the bottom with picture
    # outside them. A contiguous-run rule was tried here and broke both.
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
    if not found:
        return 0
    # AND PAPER HAS PICTURE UNDER IT. Contiguity is not enough either: episode
    # 9's T06 and T09 carry a SOLID bright flat run of 46 and 60 rows, inside
    # the window and unbroken, so they are a band by depth and by shape. What
    # gives them away is where the run STOPS -- row 46 reads mean 214 and row 60
    # reads mean 206. It ends at BRIGHTER sky. Leaked paper is the brightest
    # thing in the frame and the scene beneath it is darker by a wide margin,
    # so a run that ends at something no darker than itself was never paper.
    if lines[found].mean() > lines[:found].mean() - DROP:
        return 0
    return min(found + MARGIN, limit)


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
