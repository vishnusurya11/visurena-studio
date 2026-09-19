"""Smoothness of an H3 take: blur dips and warping, measured frame to frame.

DQ's churn row measures HOW MUCH moves; it cannot tell a clean pan from a
smear.  Two measures here, both on grey frames:
- sharpness: variance of the Laplacian.  A take that softens mid-move shows a
  dip well below its own median (a blur dip).
- flow incoherence: dense optical flow between consecutive frames; the spread
  of the flow field relative to its mean magnitude.  A camera move or a
  walking figure gives a coherent field; a warp (a face melting, a wall
  sliding through itself) gives a field that disagrees with itself.
"""
from __future__ import annotations

import numpy as np


def sharpness(frame: np.ndarray) -> float:
    import cv2
    return float(cv2.Laplacian(frame, cv2.CV_64F).var())


def blur_dips(series: list[float], floor: float = 0.5) -> list[int]:
    """Frames whose sharpness is under `floor` x the take's median."""
    if not series:
        return []
    wall = float(np.median(series)) * floor
    return [i for i, s in enumerate(series) if s < wall]


def flow_incoherence(a: np.ndarray, b: np.ndarray) -> float:
    """Spread of the flow field over its mean magnitude, 0 = every pixel moved alike."""
    import cv2
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag = np.linalg.norm(flow, axis=2)
    mean = float(mag.mean())
    if mean < 1e-6:
        return 0.0
    return float(np.sqrt(((flow - flow.mean(axis=(0, 1))) ** 2).sum(axis=2)).mean() / mean)


def summarise(sharp: list[float], warp: list[float]) -> dict:
    median = float(np.median(sharp)) if sharp else 0.0
    return {"sharp_median": round(median, 1),
            "sharp_min_ratio": round(min(sharp) / median, 2) if median else 0.0,
            "blur_dips": len(blur_dips(sharp)),
            "warp_mean": round(float(np.mean(warp)), 2) if warp else 0.0,
            "warp_max": round(float(max(warp)), 2) if warp else 0.0}


BLUR_DIPS = 3
BLUR_FLOOR = 0.5
REFRAME_WARP = 1.4
"""CALIBRATED on WotW ep02 (2026-09-19): T16's push-in (6 dips, min 0.45) was
the one visibly soft take; T12 (warp max 1.58) and T21 jumped to a new framing
in their last second; every locked shot sat at warp max 1.2-1.4 with the
actor's own motion and looked fine."""


def flags(row: dict) -> list[str]:
    out = []
    if row["blur_dips"] >= BLUR_DIPS or row["sharp_min_ratio"] < BLUR_FLOOR:
        out.append("BLUR")
    if row["warp_max"] >= REFRAME_WARP:
        out.append("REFRAME")
    return out
