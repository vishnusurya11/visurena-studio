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

INK = 0.02
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


def inkiness(frame: np.ndarray) -> float:
    """The share of the picture that is hard, bright, small-scale marks -- what
    lettering looks like to a histogram and a gradient."""
    grey = frame.mean(axis=2)
    bright = grey > 225
    if not bright.any():
        return 0.0
    edge = np.abs(np.diff(grey, axis=0)).mean() + np.abs(np.diff(grey, axis=1)).mean()
    return float(bright.mean() * min(1.0, edge / 12.0))


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


def verdict(faces: list[float], planned: int, sharp: float, ink: float,
            tiled: float, crowd: bool = False) -> dict:
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
