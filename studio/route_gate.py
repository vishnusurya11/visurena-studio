"""The far-door gate for a geography storyboard strip.

MEASURED 2026-09-11 (measurement agent, 22 corridor cells): the far
doorway window is the brightest compact blob in the upper-middle band,
blown-out daylight (mean >= 210) while cuffs, cravats and wall patches top
out near 195; its height in pixels grows as the camera nears the door.  A
strip whose from-behind cells shrink the door by more than 25 % between
consecutive cells has let the people arrive early (the failure showed as a
40 % shrink).  Cells with no far window carry no geography and are skipped.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

BAND_Y, BAND_X = (0.15, 0.65), (0.12, 0.88)
THRESH, MIN_MEAN = 170, 210
MIN_H, MAX_H = 12, 400
ASPECT, FILL = (0.45, 1.8), 0.45
REGRESSION = 0.25


def _grey(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L").filter(ImageFilter.GaussianBlur(3)), dtype=np.float32)


def _blobs(grey: np.ndarray) -> list[dict]:
    h, w = grey.shape
    y0, y1, x0, x1 = int(h * BAND_Y[0]), int(h * BAND_Y[1]), int(w * BAND_X[0]), int(w * BAND_X[1])
    band = grey[y0:y1, x0:x1]
    mask = ndimage.binary_closing(band > THRESH, structure=np.ones((9, 9)))
    lab, _ = ndimage.label(mask)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None:
            continue
        ys, xs = sl
        bh, bw = ys.stop - ys.start, xs.stop - xs.start
        area = int((lab[sl] == i).sum())
        touches = ys.start == 0 or xs.start == 0 or ys.stop == band.shape[0] or xs.stop == band.shape[1]
        out.append({"h": bh, "w": bw, "area": area, "fill": area / (bh * bw), "touches": touches,
                    "mean": float(band[sl][lab[sl] == i].mean())})
    return out


def door_height(path: Path) -> int | None:
    """Height in px of the far window, or None when the panel shows no geography."""
    ok = [b for b in _blobs(_grey(path)) if MIN_H <= b["h"] <= MAX_H and ASPECT[0] <= b["h"] / b["w"] <= ASPECT[1]
          and b["fill"] >= FILL and not b["touches"] and b["mean"] >= MIN_MEAN]
    if not ok:
        return None
    best = max(ok, key=lambda b: (round(b["mean"] / 10), b["area"]))
    return int(best["h"])


def regressions(heights: list[int | None], tolerance: float = REGRESSION) -> list[int]:
    """Indices where a geography cell shrinks the door by more than `tolerance`
    against the previous geography cell."""
    bad, last = [], None
    for i, h in enumerate(heights):
        if h is None:
            continue
        if last is not None and h < last * (1 - tolerance):
            bad.append(i)
        last = h
    return bad
