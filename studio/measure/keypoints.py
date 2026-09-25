"""DWPose keypoints -> posture family, shot size, limb counts, wrists.

A coordinate has no prior.  The VLM read "lying" off the sand under a man who
stood, and a hat as worn whether on a head or in a hand; a torso is a vector
and its angle from the vertical is a number.

Input is the POSE_KEYPOINT json the `image_dwpose_keypoints` workflow prints
through PreviewAny: a list of frames, each `{"people": [{"pose_keypoints_2d":
[x, y, c, ...]}], "canvas_height", "canvas_width"}` in the OpenPose-18 body
layout.  Coordinates come in canvas pixels and are normalised here.  No model
loads in this module: `run=` is the only door to ComfyUI.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

WORKFLOW = "image_dwpose_keypoints"

NOSE, NECK, R_SHOULDER, R_ELBOW, R_WRIST, L_SHOULDER, L_ELBOW, L_WRIST = range(8)
R_HIP, R_KNEE, R_ANKLE, L_HIP, L_KNEE, L_ANKLE, R_EYE, L_EYE, R_EAR, L_EAR = range(8, 18)
HEAD = (NOSE, NECK, R_EYE, L_EYE, R_EAR, L_EAR)
SHOULDERS = (NECK, R_SHOULDER, R_ELBOW, L_SHOULDER, L_ELBOW)
HIPS = (R_HIP, R_KNEE, L_HIP, L_KNEE)
ANKLES = (R_ANKLE, L_ANKLE)
WRISTS = (R_WRIST, L_WRIST)

CONF = 0.3
"""A keypoint below this confidence is not in the picture."""
LYING = 60.0
"""Degrees of the hip-to-neck line from the vertical: past this the body is down."""
BENT = 120.0
"""A knee angle under this is bent: sitting, crouching or kneeling, not standing."""
FOLDED = 0.6
"""With a bent knee, ankles within this many torso lengths below the hips is a
body folded on itself (crouching, kneeling); further and it sits."""
WIDE_SHARE = 0.45
"""A full figure shorter than this share of the canvas is a wide, not a full."""
ORDER = ("insert", "extreme_close", "close", "medium_close", "medium", "full", "wide")
"""Shot sizes, closest first.  One step apart is the drawer's latitude; two is a fault."""


def parse(text) -> list[dict]:
    """The frames in the workflow's text, one dict per frame."""
    data = json.loads(text) if isinstance(text, str) else text
    return [data] if isinstance(data, dict) else list(data)


def people(frame: dict) -> list[np.ndarray]:
    """Each person as an (18, 3) array of x, y in 0-1 and confidence."""
    w, h = frame.get("canvas_width") or 1, frame.get("canvas_height") or 1
    return [_points(p.get("pose_keypoints_2d"), w, h) for p in frame.get("people", [])]


def _points(flat, w: int, h: int) -> np.ndarray:
    pts = np.zeros((18, 3))
    if flat:
        got = np.asarray(flat, dtype=float).reshape(-1, 3)[:18]
        pts[:len(got)] = got
    if pts[:, :2].max() > 1.5:
        pts[:, 0] /= w
        pts[:, 1] /= h
    return pts


def visible(pts: np.ndarray, i: int) -> bool:
    return bool(pts[i, 2] >= CONF)


def point(pts: np.ndarray, i: int):
    return pts[i, :2] if visible(pts, i) else None


def mid(pts: np.ndarray, a: int, b: int):
    """The midpoint of two keypoints, the one seen when only one is, else None."""
    p, q = point(pts, a), point(pts, b)
    if p is not None and q is not None:
        return (p + q) / 2
    return p if p is not None else q


def _torso(pts: np.ndarray):
    """(hips, top) of the torso line, or None without both ends."""
    hips = mid(pts, R_HIP, L_HIP)
    top = point(pts, NECK)
    top = top if top is not None else mid(pts, R_SHOULDER, L_SHOULDER)
    if hips is None or top is None or np.linalg.norm(hips - top) < 1e-6:
        return None
    return hips, top


def torso_angle(pts: np.ndarray) -> float | None:
    """Degrees of the hip-to-neck line from the vertical, 0 upright, 90 flat."""
    ends = _torso(pts)
    if ends is None:
        return None
    dx, dy = ends[1] - ends[0]
    return round(math.degrees(math.atan2(abs(dx), abs(dy))), 1)


def _angle_at(b: np.ndarray, a: np.ndarray, c: np.ndarray) -> float:
    """The angle at b between a and c, in degrees."""
    u, v = a - b, c - b
    cos = float(u @ v / ((np.linalg.norm(u) * np.linalg.norm(v)) or 1e-9))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def knee_angle(pts: np.ndarray) -> float | None:
    """The angle at the first knee whose hip and ankle are both seen."""
    for hip, knee, ankle in ((R_HIP, R_KNEE, R_ANKLE), (L_HIP, L_KNEE, L_ANKLE)):
        if all(visible(pts, i) for i in (hip, knee, ankle)):
            return round(_angle_at(pts[knee, :2], pts[hip, :2], pts[ankle, :2]), 1)
    return None


def _folded(pts: np.ndarray) -> bool:
    ends = _torso(pts)
    ankles = mid(pts, R_ANKLE, L_ANKLE)
    if ends is None or ankles is None:
        return False
    return float(ankles[1] - ends[0][1]) < FOLDED * float(np.linalg.norm(ends[0] - ends[1]))


def posture(pts: np.ndarray) -> str:
    """lying | low | sitting | standing | unread -- the families panel_content judges."""
    angle = torso_angle(pts)
    if angle is None:
        return "unread"
    if angle > LYING:
        return "lying"
    bend = knee_angle(pts)
    if bend is None or bend >= BENT:
        return "standing"
    return "low" if _folded(pts) else "sitting"


def _height(pts: np.ndarray) -> float:
    top = min(pts[i, 1] for i in HEAD if visible(pts, i)) if any(visible(pts, i) for i in HEAD) else 0.0
    return float(max(pts[i, 1] for i in ANKLES if visible(pts, i)) - top)


def shot_size(pts: np.ndarray) -> str:
    """The lowest body part in frame names the size: ankles a full (a wide when
    the figure is small), hips or knees a medium, shoulders a medium close, a
    head alone a close."""
    if any(visible(pts, i) for i in ANKLES):
        return "wide" if _height(pts) < WIDE_SHARE else "full"
    if any(visible(pts, i) for i in HIPS):
        return "medium"
    if any(visible(pts, i) for i in SHOULDERS):
        return "medium_close"
    return "close" if any(visible(pts, i) for i in HEAD) else "unread"


def size_fault(measured: str, planned: str) -> str | None:
    """Two steps or more between the drawn size and the planned one."""
    if measured not in ORDER or planned not in ORDER:
        return None
    if abs(ORDER.index(measured) - ORDER.index(planned)) < 2:
        return None
    return f"framing {measured!r}: the shot asks for {planned!r}"


def wrists(pts: np.ndarray) -> list[tuple[float, float]]:
    return [(float(pts[i, 0]), float(pts[i, 1])) for i in WRISTS if visible(pts, i)]


def limbs(frame: dict) -> dict:
    """Heads, wrists and ankles counted over every person the model returned;
    a stray limb comes back as a headless extra person."""
    heads = wrists_n = ankles = 0
    for pts in people(frame):
        heads += any(visible(pts, i) for i in HEAD)
        wrists_n += sum(visible(pts, i) for i in WRISTS)
        ankles += sum(visible(pts, i) for i in ANKLES)
    return {"heads": heads, "wrists": wrists_n, "ankles": ankles}


def extra_limbs(frame: dict) -> list[str]:
    """More than two wrists or two ankles per head."""
    n = limbs(frame)
    unit = "head" if n["heads"] == 1 else "heads"
    return [f"{n[limb]} {limb} for {n['heads']} {unit}" for limb in ("wrists", "ankles")
            if n[limb] > 2 * n["heads"]]


def estimate(image: Path, run=None, timeout: float = 120.0) -> list[dict]:
    """The frames of one picture, read through ComfyUI (or the injected `run`)."""
    from studio import comfy
    staged = comfy.stage_image(Path(image))
    return parse((run or comfy.run_text)(WORKFLOW, {"image_1": staged}, timeout))
