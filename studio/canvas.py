"""The episode's delivery canvas: ONE declaration every stage derives from.

The aspect used to be written down in seven places -- `frames.py`,
`storyboard.py`, `shots.py`, `takes_r2v.py`, `assemble.py`, `title.py` and the
sheet prompt's own wording -- each as a literal `W, H = 768, 1344`.  Seven
copies of one fact is six chances to disagree, and the disagreement is silent:
a square take cropped by a vertical assemble loses a third of every frame and
nothing raises.

So the brick is this module, and the SPEC is the plan: `Episode.aspect`.  A
book's episode 1 stays 9:16 because its plan says so, and episode 2 is square
because the owner said 1:1 on 2026-09-12.  Nothing here is a default anybody
edits -- the plan carries it.

The render canvas is not ours to choose: `h3.adapt_canvas` forces the short
edge to 768 and rewrites anything else, so `size()` returns the fixed point of
H3's own transform for the ratio, and `tests/test_canvas.py` asserts that by
calling `h3.check_canvas` on every aspect we ship.
"""
from __future__ import annotations

from studio import h3

RATIOS = {"9:16": (9, 16), "1:1": (1, 1)}
"""Every delivery shape the pipeline knows, as the ratio the owner names it by."""

ASPECTS = tuple(RATIOS)

DEFAULT = "1:1"
"""The shape a NEW episode is written in (owner, 2026-09-12).

Square because one master serves both destinations: it plays in a vertical feed
without the sides being cropped away, and the episodes concatenate into a
long-form cut that is the same shape throughout.  Episode 1 shipped 9:16 and its
plan now says so explicitly, so it keeps its own canvas -- the plan is the spec,
and a default never reaches back into an episode that already declared one."""

COMFY = {"9:16": "9:16 (Portrait Widescreen)", "1:1": "1:1 (Square)"}
"""The `ResolutionSelector` node's own labels.  A string it does not recognise
is not an error there either -- it falls back -- so these are copied from the
workflow, never composed."""

WORDS = {"9:16": "vertical 9:16", "1:1": "square 1:1"}
"""How the aspect is said to gpt-image in the sheet prompt.  The drawer
composes for the shape it is told, and a panel composed tall and then cropped
square has lost the half of the composition that carried the face."""

GRIDS = {
    # cols, rows, sheet canvas -- the cell's own shape follows the delivery shape
    "9:16": ((3, 1, (1536, 1024)), (3, 2, (2048, 2048)), (3, 3, (2048, 3072))),
    "1:1": ((2, 2, (2048, 2048)), (3, 3, (2048, 2048))),
}
"""The storyboard sheets, smallest first.  A square delivery draws square
cells: 2048x2048 gives 1024x1024 cells at four panels and 682x682 at nine,
both of which reach 768x768 with an upscale a face survives -- and at $0.13 a
sheet against the vertical 3x3's $0.20."""


STILLS = {"9:16": "1024x1536", "1:1": "1024x1024"}
"""The gpt-image size for ONE still (the title card).  A square delivery asks
for a square still: drawing 1024x1536 and cropping it square threw away a third
of the paid pixels and pushed the lettering off the card.  It is also cheaper --
`image_spend` prices an unlisted size by area against the nearest listed one, so
1024x1024 costs $0.05 against the portrait's $0.08."""


def still_size(aspect: str) -> str:
    """The `size` argument for a single paid still at this aspect."""
    return STILLS[aspect]


def ratio(aspect: str) -> tuple[int, int]:
    """The declared ratio, as two integers."""
    return RATIOS[aspect]


def size(aspect: str) -> tuple[int, int]:
    """The render canvas: H3's own fixed point for this ratio."""
    return h3.adapt_canvas(*RATIOS[aspect])


DELIVER = 2
"""How much bigger the UPLOAD is than the render, as a whole number.

Every episode so far was rendered, cut and uploaded at H3's native 768x768 --
0.59 megapixels, below every tier YouTube treats as high definition. The upload
is then transcoded at that tier's bitrate and the detail is thrown away between
the master and the viewer. The master itself is not the problem: it is CRF 17
and episode 8's is the highest-bitrate one in the series.

EPISODE 8 IS WHERE IT SHOWED. Measured across the delivered masters -- detail is
the mean absolute Laplacian, the high-frequency energy a codec must spend bits
on:

    ep06 interiors   detail 5.03   mean luma  69.0
    ep07 interiors   detail 5.60   mean luma  55.5
    ep08 desert      detail 6.93   mean luma 100.9

38 % more fine detail than episode 6 and 46 % brighter. Both punish a thin
transcode: fine rock smears, and the banding that hides in a dark parlour is
plain in a pale sky. The first episode that is mostly wide exteriors is the
first where the upload size hurts.

A WHOLE NUMBER, because 768 to 1080 is a factor of 1.406 and rings on every
hard edge; 2x resamples cleanly. This adds NO detail -- Lanczos cannot invent
any. It stops the detail that IS there from being discarded by a tier chosen on
pixel count, which is a different and more modest claim than "better quality".

The render pipeline does not move: cells, takes and cuts stay at H3's fixed
point. Only the last encode scales."""


def deliver(aspect: str) -> tuple[int, int]:
    """The canvas the finished master is ENCODED at, for upload."""
    w, h = size(aspect)
    return w * DELIVER, h * DELIVER


def comfy_ratio(aspect: str) -> str:
    """The label the ResolutionSelector node expects for a local plate."""
    return COMFY[aspect]


def words(aspect: str) -> str:
    """The shape as the drawer is told it, for the sheet prompt."""
    return WORDS[aspect]


def grids(aspect: str) -> tuple[tuple[int, int, tuple[int, int]], ...]:
    return GRIDS[aspect]


def grid(panels: int, aspect: str) -> tuple[int, int, tuple[int, int]]:
    """The smallest sheet that holds `panels` cells at this aspect."""
    for candidate in GRIDS[aspect]:
        if candidate[0] * candidate[1] >= panels:
            return candidate
    biggest = GRIDS[aspect][-1]
    raise ValueError(f"{panels} panels exceeds the largest {aspect} sheet "
                     f"({biggest[0]}x{biggest[1]}); split the setup over two sheets")


def crop_to(width: float, height: float, aspect: str) -> tuple[int, int]:
    """The largest box of this aspect that fits inside `width` x `height`.

    What `conform()` actually takes out of a drawn cell before the upscale, so
    the grid table can be checked against it instead of against a comment."""
    want_w, want_h = RATIOS[aspect]
    if width * want_h > height * want_w:
        return (round(height * want_w / want_h), round(height))
    return (round(width), round(width * want_h / want_w))
