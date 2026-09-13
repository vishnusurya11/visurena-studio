"""Camera scale of storyboard cells, and which cells may be pinned.

MEASURED 2026-09-10: MiniMax-H3 reproduces every pinned cell at its frame;
where consecutive pinned cells differ in camera distance (55 % between cells
4 and 5 of take 3's sheet) the take snaps and wobbles.  So a cell is pinned
only when the drawer kept the camera: its scale against the last pinned cell
within TOL, or, for a shot whose motion names a push/pull, a monotonic ramp
travelling at most TRAVEL in all.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

W, H = 192, 336
CROP = 0.6
SCALES = np.round(np.arange(0.80, 1.26, 0.02), 2)
TOL = 0.05
TRAVEL = 0.15


def _norm(a: np.ndarray) -> np.ndarray:
    a = a - a.mean()
    return a / (np.linalg.norm(a) + 1e-9)


def _centre(a: np.ndarray, w: int, h: int) -> np.ndarray:
    cx, cy = a.shape[1] // 2, a.shape[0] // 2
    return a[cy - h // 2:cy + h // 2, cx - w // 2:cx + w // 2]


def scale_between(ref: Image.Image, other: Image.Image) -> float:
    """How much larger `other` shows the scene than `ref` (1.2 = a fifth closer)."""
    r = np.asarray(ref.convert("L").resize((W, H)), dtype=float)
    o = Image.fromarray(np.asarray(other.convert("L").resize((W, H)), dtype=np.uint8))
    cw, ch = int(W * CROP), int(H * CROP)
    ref_c = _norm(_centre(r, cw, ch))
    best, best_s = -2.0, 1.0
    for s in SCALES:
        z = np.asarray(o.resize((int(W * s), int(H * s)), Image.BILINEAR), dtype=float)
        crop = _centre(z, cw, ch)
        if crop.shape != ref_c.shape:
            continue
        c = float((_norm(crop) * ref_c).sum())
        if c > best:
            best, best_s = c, float(s)
    return round(1.0 / best_s, 2)  # `other` had to be shrunk by best_s to match: it is 1/best_s larger


def scales_of(cells: list[Image.Image]) -> list[float]:
    return [scale_between(cells[0], c) for c in cells]


def pins(scales: list[float], candidates: tuple[int, ...], tol: float = TOL) -> list[int]:
    """Frame 0 always; each later candidate only if within `tol` of the last pin."""
    kept, last = [0], scales[0]
    for k in candidates:
        if k == 0:
            continue
        if abs(scales[k] - last) <= tol:
            kept.append(k)
            last = scales[k]
    return kept


def consistent(scales: list[float], push: bool, tol: float = TOL, travel: float = TRAVEL) -> bool:
    """A sheet keeps its camera: all cells within `tol` of cell 0, or, for a
    named push/pull, a monotonic ramp travelling at most `travel`."""
    if not push:
        return all(abs(s - scales[0]) <= tol for s in scales)
    steps = [b - a for a, b in zip(scales, scales[1:])]
    monotonic = all(s <= 1e-9 for s in steps) or all(s >= -1e-9 for s in steps)
    return monotonic and abs(scales[-1] - scales[0]) <= travel
