"""A cel-valid eye measure for the face refine (face-blur round 2, 2026-10-19).

Round 1 read eye sharpness as the Laplacian variance of the eye band and scored every refine
0.6-0.77x the take, the owner-liked old F2 crops too: cel inking holds less high-frequency
energy than a take's smeared noise and wrinkle hatching (docs/audit/2026-10-19_face_blur/bench/
BENCH.md).  What the strips show instead is a drawn eye -- a dark compact pupil or iris -- where
the take had a pale smudge.  So the measure finds compact dark blobs in the eye band of the
128 px face crop (darker than the face's skin by max(40, 35 %)) and sums the local contrast of
the two strongest; a long ink line (a wrinkle, a lid, a hat brim) is not compact and never
counts.  Pre-registered on round 1 before its numbers were read, never tuned on them.
Logged on the gate and the bench; never a wall.  A character drawn with blank eyes (Hyde's
glare) reads near 0 either way.
"""
from __future__ import annotations

import numpy as np

SIDE = 128
EYE_BAND = (0.18, 0.50)
"""Rows of the face box the eyes sit in (face_yolov8m boxes put them at 0.27-0.35, round 1's
band_check.png), with room for a tilt."""
SKIN_ROWS, SKIN_COLS = (0.45, 0.80), (0.30, 0.70)
DARK_SHARE, DARK_MIN = 0.35, 40.0
AREA = (6, 150)
SPAN_MAX = 22
ASPECT_MAX = 3.0
FILL_MIN = 0.35


def face_gray(rgb: np.ndarray, box) -> np.ndarray:
    """The square face box (side = its larger side, kept inside the picture) at 128 px, grey."""
    import cv2
    x1, y1, x2, y2 = box
    h, w = rgb.shape[:2]
    s = min(int(round(max(y2 - y1, x2 - x1, 4))), h, w)
    x0 = int(np.clip(round((x1 + x2) / 2 - s / 2), 0, w - s))
    y0 = int(np.clip(round((y1 + y2) / 2 - s / 2), 0, h - s))
    crop = np.ascontiguousarray(rgb[y0:y0 + s, x0:x0 + s])
    small = cv2.resize(crop, (SIDE, SIDE), interpolation=cv2.INTER_AREA if s > SIDE else cv2.INTER_CUBIC)
    return cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)


def part(g: np.ndarray, rows, cols) -> np.ndarray:
    return g[int(rows[0] * SIDE):int(rows[1] * SIDE), int(cols[0] * SIDE):int(cols[1] * SIDE)]


def compact(stats) -> bool:
    """A blob the size and shape of a pupil, not an ink line."""
    _, _, w, h, area = stats
    return (AREA[0] <= area <= AREA[1] and max(w, h) <= SPAN_MAX
            and max(w, h) <= ASPECT_MAX * min(w, h) and area / (w * h) >= FILL_MIN)


def pupils(g: np.ndarray) -> list[float]:
    """The local contrast of every compact dark blob in the eye band, strongest first."""
    import cv2
    skin = float(np.median(part(g, SKIN_ROWS, SKIN_COLS)))
    band = part(g, EYE_BAND, (0.10, 0.90))
    dark = (band < skin - max(DARK_MIN, DARK_SHARE * skin)).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
    out = []
    for j in (j for j in range(1, n) if compact(stats[j])):
        blob = labels == j
        ring = cv2.dilate(blob.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2).astype(bool) & ~blob
        out.append(float(band[ring].mean() - band[blob].mean()))
    return sorted(out, reverse=True)


def eye_score(g: np.ndarray) -> float:
    """The two strongest pupils' contrast, summed (grey levels): 0 is no drawn eye."""
    return float(sum(pupils(g)[:2]))


def track_eyes(crops: list[np.ndarray], boxes: list) -> float | None:
    """The median eye score over a track's crops, each read at its own face box."""
    scores = [eye_score(face_gray(c, b)) for c, b in zip(crops, boxes)]
    return float(np.median(scores)) if scores else None
