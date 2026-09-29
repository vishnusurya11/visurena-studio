"""Place constancy, measured: is this panel the staged room, or its mirror?

Prototyped by the stager agent on ep06 and ep14 (2026-09-28, the five-agent
debate).  Three cheap signatures of a picture's BACKGROUND -- the column light
profile of its upper half, the grey structure of its left and right wings with
the centre 40 % (the figure) dropped, and which side the light falls -- compared
to the staged reference and to the reference mirrored.  Measured on ep14:
Waterloo s05 prof_same -0.56 with the light on the opposite side to the plate
(a MIRROR), s07 -0.36; ep06's pit wides copy their plate at +0.63..+0.84.  It
does not see re-dressing (a cabinet that appears on the same wall): that is the
VLM content rung's, judged against the plate's list.  Advisory until calibrated
over five episodes (docs/calibration/panel_place.md).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

SIDE = 256
COLS = 32
WING = 0.3
MIRROR_SAME = 0.0
"""A profile that agrees better with the mirror than with the reference."""
SIDE_FLOOR = 0.08
"""How lit one side must be over the other before "the light is on the left" is said."""


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB").resize((SIDE, SIDE), Image.LANCZOS)


def unit(a) -> np.ndarray:
    a = np.asarray(a, dtype=float).ravel()
    a = a - a.mean()
    return a / (np.linalg.norm(a) + 1e-9)


def profile(im: Image.Image, cols: int = COLS) -> np.ndarray:
    """Column light profile of the upper half (the room, above the figure)."""
    g = np.asarray(im.convert("L"), dtype=float)
    return unit(g[: g.shape[0] // 2].mean(axis=0).reshape(cols, -1).mean(axis=1))


def wings(im: Image.Image, side: int = 8) -> np.ndarray:
    """8x8 grey structure of the left and right wings; the centre is the figure."""
    a = np.asarray(im.convert("L"), dtype=float)
    w = a.shape[1]
    both = np.concatenate([a[:, : int(w * WING)], a[:, int(w * (1 - WING)):]], axis=1)
    return unit(np.asarray(Image.fromarray(both.astype(np.uint8)).resize((side, side), Image.BOX), dtype=float))


def light_side(im: Image.Image) -> float:
    """(R - L) / (R + L) of the upper half's outer bands: +1 lit on the right."""
    g = np.asarray(im.convert("L"), dtype=float)
    h, w = g.shape[0] // 2, g.shape[1]
    left, right = g[:h, : int(w * WING)].mean(), g[:h, int(w * (1 - WING)):].mean()
    return round(float((right - left) / (right + left + 1e-9)), 3)


def signature(im: Image.Image) -> dict:
    return {"prof": profile(im), "wings": wings(im), "side": light_side(im)}


def versus(panel: Image.Image, reference: Image.Image) -> dict:
    """The panel against the reference and against its mirror."""
    p, r, rf = signature(panel), signature(reference), signature(ImageOps.mirror(reference))
    out = {"side_panel": p["side"], "side_ref": r["side"]}
    for k in ("prof", "wings"):
        same, flip = float(p[k] @ r[k]), float(p[k] @ rf[k])
        out[f"{k}_same"], out[f"{k}_flip"] = round(same, 3), round(flip, 3)
    return out


def mirrored(read: dict) -> bool:
    """The rule the ep14 numbers support: the profile agrees with the mirror
    and the light sits on opposite sides, each side lit by more than SIDE_FLOOR."""
    opposite = (read["side_panel"] * read["side_ref"] < 0
                and abs(read["side_panel"]) > SIDE_FLOOR and abs(read["side_ref"]) > SIDE_FLOOR)
    return read["prof_same"] < MIRROR_SAME and opposite
