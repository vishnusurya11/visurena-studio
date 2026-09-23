"""Measure a storyboard panel before calling it good.

OWNER 2026-09-20: "the images are shit in the ones you shared .. you did not do
any dq."

Twenty-eight panels went out with five faults marked BY EYE and nothing
measured. The rule was already written down for prompts -- green tests are not
evidence a fix reached the artefact, so measure the artefact -- and it applies
just as hard to a picture I am about to call good.

Nothing new is invented here. These are the gates the video already uses,
pointed at a still: `face_end.faces` for who is in it, `people_count.clones`
for two of the same man, `motion_quality.sharpness` for a panel that came back
soft. Two more come from what the storyboard itself taught today: lettering
burned into a picture that is going to be a reference, and a panel that is
secretly a tiled sheet of one image.
"""
from __future__ import annotations

import numpy as np

SHARP_FLOOR = 0.5
"""How soft a panel may be AGAINST THE MEDIAN OF ITS OWN SET.

MEASURED 2026-09-20, and it was wrong first: this began as an absolute 0.45
against `motion_quality.sharpness`, which is a raw variance-of-Laplacian and
came back 279 on the first panel. Every panel passed, which is a gate that
cannot fail -- worse than no gate. `motion_quality.blur_dips` never used an
absolute floor either, for the same reason: sharpness has no absolute scale,
only a scale against comparable pictures. So a panel is soft when it is under
half the median of the episode's own panels.""" 

INK = 0.007
"""MEASURED 2026-09-22 over all 127 panels of ep05-ep09: the inkiest clean
panel in the series reads 0.00417, and a caption band struck across one of
them reads 0.01009. The wall sits between, 68% above the worst clean panel
and 31% below real lettering. The old 0.02 was set when `inkiness` was the
share of bright pixels, which only worked because every episode until ep09
was night."""
"""How much of a panel may be hard-edged near-white on near-black before it is
lettering. MEASURED on the ep05 grids that drew WIDE / MEDIUM / INSERT into
their corners."""

TILED = 0.90
"""How equal two halves may be. A panel whose top half repeats its bottom half
is the mosaic the six 1x1 'grids' came back as."""

CAST_FACE = 0.06
"""A face smaller than this is a figure in a crowd, not a member of the cast.
Shot 9's band of people on the skyline names nobody and is correct."""


def tiledness(frame: np.ndarray) -> float:
    """How nearly the picture repeats itself, vertically or horizontally."""
    def same(a: np.ndarray, b: np.ndarray) -> float:
        if a.shape != b.shape or a.size == 0:
            return 0.0
        gap = np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()
        return float(max(0.0, 1.0 - gap / 32.0))
    h, w = frame.shape[:2]
    return max(same(frame[:h // 2], frame[h // 2:h // 2 * 2]),
               same(frame[:, :w // 2], frame[:, w // 2:w // 2 * 2]))


BRIGHT, BLOCK, RELIEF = 225.0, 32, 40.0
"""A mark is brighter than `BRIGHT`, and stands `RELIEF` above the mean of the
`BLOCK`-sized patch it sits in. The patch is what makes it LOCAL, and it is
wide enough that a stroke of type cannot pull up its own mean: at BLOCK 8 a
four-pixel stroke filled half its patch and vanished into it."""


def inkiness(frame: np.ndarray) -> float:
    """The share of the picture that is small, bright marks standing clear of
    their own surroundings -- which is what lettering is.

    This used to be the share of pixels over 225 times the picture's mean
    gradient. That works while every episode is gaslight and night, where
    nothing is that bright except letters. ep09 is the first DAYLIGHT episode
    and eleven of its twenty-three panels failed with no text on them: a hazy
    white sky and a pale gravel path are bright pixels, and a garden full of
    leaves supplies the gradient. The same arithmetic also MISSED white
    lettering on a dark picture, because the bright share there is tiny.

    What separates a letter from a sky is locality. A sky is a large bright
    region with nothing inside it; a letter stands well above the patch of
    picture it is struck onto. So the relief is measured against a local mean
    and the marks are counted, rather than the brightness being weighed.
    """
    grey = frame.mean(axis=2)
    local = _block_mean(grey, BLOCK)
    marks = (grey > BRIGHT) & (grey - local > RELIEF)
    return float(_rim(marks).mean())


def _rim(marks: np.ndarray) -> np.ndarray:
    """The marks' outer skin: every true pixel with a false pixel beside it.

    A stroke of type is nearly all rim; a bright opening in a dark wall -- an
    arch, a lit window -- is nearly all middle. ep09 shot 4's archway read
    0.01836 against synthetic lettering at 0.01880 before this, a two per cent
    margin that is a coincidence rather than a measurement.
    """
    inner = marks.copy()
    inner[1:, :] &= marks[:-1, :]
    inner[:-1, :] &= marks[1:, :]
    inner[:, 1:] &= marks[:, :-1]
    inner[:, :-1] &= marks[:, 1:]
    return marks & ~inner


def _block_mean(grey: np.ndarray, block: int) -> np.ndarray:
    """The mean of each `block` x `block` patch, spread back over the picture."""
    h, w = grey.shape
    ph, pw = -h % block, -w % block
    padded = np.pad(grey, ((0, ph), (0, pw)), mode="edge")
    tiles = padded.reshape(padded.shape[0] // block, block,
                           padded.shape[1] // block, block).mean(axis=(1, 3))
    return np.repeat(np.repeat(tiles, block, axis=0), block, axis=1)[:h, :w]


def cast_faces(faces: list[float], floor: float = CAST_FACE) -> list[float]:
    """The faces big enough to be somebody, rather than a head in a crowd."""
    return [f for f in faces if f >= floor]


def softness(sharps: list[float]) -> float:
    """The median sharpness of a set of panels, the yardstick for all of them."""
    ordered = sorted(s for s in sharps if s > 0)
    if not ordered:
        return 0.0
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2


def by_setup(sharps: dict) -> dict:
    """Each panel's sharpness over the median OF ITS OWN SETUP.

    MEASURED 2026-09-20 against a control, which is what made it provable.
    Nine ep05 panels failed `blur` and every one was a night panel. So I
    measured a picture known to be good: `wide_night.png`, drawn in the house
    style an hour before and perfectly sharp, scores 37 where the sunset wide
    scores 253. It would fail its own gate.

    Laplacian variance falls with darkness and with emptiness, and neither is
    softness -- shot 20 is green smoke on a bare sky, bright and nearly
    detailless. An episode-wide median is dominated by whichever hour has the
    most panels. A panel can only be compared with panels of its own hour, for
    the same reason the grid unit is the setup."""
    groups = {}
    for key, (setup, value) in sharps.items():
        groups.setdefault(setup, []).append(value)
    medians = {setup: softness(values) for setup, values in groups.items()}
    return {key: (value / medians[setup] if medians.get(setup) else 1.0)
            for key, (setup, value) in sharps.items()}


FACE_IS_THE_PICTURE = ("close", "extreme_close", "medium_close")
"""The sizes at which a missing face is a fault. At a wide or a medium a face
can be too small for a detector to find and the panel still be right."""


def verdict(faces: list[float], planned: int, sharp: float, ink: float,
            tiled: float, crowd: bool = False, size: str = "") -> dict:
    """Every fault this panel carries, named. An empty list is a clean panel."""
    from studio import people_count

    near = cast_faces(faces)
    flags = []
    # A CROWD IS NOT A CAST OVERFLOW. ep05's shots 10, 12 and 19 name no
    # character and are full of onlookers by design -- the stout washerwoman,
    # the thin governess, the deputation -- so counting detected faces against
    # NAMED characters calls every crowd shot a fault. Where the shot's own
    # prose asks for unnamed people, only the clone check applies.
    if not crowd and len(near) > max(planned, 0):
        flags.append("people")
    if not crowd and planned >= 0 and people_count.clones(near, planned):
        flags.append("clone")
    # AND GOING UNDER, which nobody ever asked it about. ep09's button was a
    # big close-up of the hussar shouting; it came back an empty garden and
    # this printed `faces 0/1` and passed.
    if planned > 0 and not near and size in FACE_IS_THE_PICTURE:
        flags.append("missing")
    if sharp < SHARP_FLOOR:   # `sharp` is the panel OVER the set median
        flags.append("blur")
    if ink > INK:
        flags.append("text")
    if tiled > TILED:
        flags.append("tiled")
    return {"faces": len(faces), "cast_faces": len(near), "planned": planned,
            "sharp": round(sharp, 3), "ink": round(ink, 4), "tiled": round(tiled, 3),
            "flags": flags, "passed": not flags}


def edge_strength(frame) -> float:
    """How sharp the sharpest edges are -- not how many edges there are.

    MEASURED 2026-09-20, the SECOND time this check was wrong. Variance of the
    Laplacian averages the whole frame, so it falls with darkness (fixed by
    judging inside a setup) and again with EMPTINESS, which judging inside a
    setup does not fix: ep05 shots 3, 11, 20 and 25 are a mast on bare sky, a
    mirror on bare sky, green smoke on bare sky and a dark wide. All four are
    crisp and nearly detailless, and all four read as blur.

    A blurred picture has NO hard edge anywhere; an empty picture has few hard
    edges that are still hard. So take the 99th percentile of the edge
    magnitude and ignore how much of the frame is flat."""
    import cv2
    import numpy as np

    grey = np.asarray(frame).mean(axis=2)
    lap = np.abs(cv2.Laplacian(grey, cv2.CV_64F))
    return float(np.percentile(lap, 99))
