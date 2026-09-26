"""Is the WHOLE picture still?  Whole-frame optical flow, split into the
camera's move and the subject's.

`motion_gate` scores a frame step by its BLOCK-MAX |diff|: one puff of smoke,
a glint or a mouth makes the frame "alive", and every ep12 take read 0 %
frozen while five shots were 70-100 % static by whole-frame flow (the h2
analysis of all twelve masters, Farneback at 256 px).  Here every step is the
MEAN Farneback magnitude over the frame at 256 px on its long side, and a
similarity fit (studio.measure.flow's model) says how much of it the camera
explains: a push on a still scene is camera motion, a locked camera on an
acting subject is subject motion, and a step under STATIC is neither.

HARD: a take whose placed seconds are >= MIN_SECONDS and whose static share is
>= WALL is still.  A shot the plan declares still (`Framed.still`) is exempt.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from studio.measure import flow as fl

SIZE = 256
FPS = 24
KIND = "frozen-whole"
"""The fault kind: take_ladder.FROZEN already routes it to the frozen cure."""
STATIC = 0.15
"""CALIBRATION (2026-09-26, 290 r2v takes of WotW ep01-ep12 over their placed
seconds, from the head the cut skips): px per step at 256 px.  0.12 lets 3 of
the 5 owner-dead ep12 takes through at any wall; 0.20 fails 3 of the 28
known-good (ep09, ep12 T04/T09/T12/T17/T19) at any wall.  The h2 master
analysis used the same 0.15 and a take's share matches its master row to 0.03."""
WALL = 0.65
"""CALIBRATION: known-good max 0.60 (ep09 T13, a slow push); owner-dead min 0.69
(ep12 T18, the tripod's legs moving slowly in the river).  0.65 fails 5/5
owner-dead, 0/28 known-good, 56/56 of the h2 master-dead shots, and 5 more at
0.66-0.71 (ep04 T13, ep06 T22, ep07 T11/T17/T24): 61 of 290 takes."""
ADVISORY = 0.50
"""No length floor: ep12 T07 (4.2 s, 0.71) and T16 (3.0 s, 0.60), the owner's
'nearly frozen', are named; ep09 T13 (0.60) is named and passes.  ep12 T23
(0.31, 'nearly') is out of this instrument's reach."""
MIN_SECONDS = 5.0
"""The h2 dead-shot rule: under 5 s a still reads as a beat, not a dead shot."""
TRIM = 0.7
"""The camera is refitted on the TRIM share of grid points it explains best,
so an actor filling a third of the frame does not drag the fit."""


def fit_size(w: int, h: int, size: int = SIZE) -> tuple[int, int]:
    """(w, h) with the long side at `size`, the short side even, aspect kept."""
    if w >= h:
        return size, max(2, int(round(size * h / w / 2)) * 2)
    return max(2, int(round(size * w / h / 2)) * 2), size


def probe(video) -> tuple[int, int]:
    """The clip's (width, height)."""
    import cv2

    cap = cv2.VideoCapture(str(video))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if not w or not h:
        raise ValueError(f"cannot read the size of {video}")
    return w, h


def read_frames(video, seconds: float | None = None, fps: int | None = None, start: float = 0.0) -> np.ndarray:
    """Grey uint8 frames (n, h, w), long side SIZE, at `fps` (FPS), from
    `start` for `seconds` (the whole clip when None)."""
    w, h = fit_size(*probe(video))
    head = ["-ss", f"{start:.3f}"] if start > 0 else []
    cut = ["-t", f"{seconds:.3f}"] if seconds else []
    raw = subprocess.run(["ffmpeg", "-v", "error", *head, "-i", str(video), *cut,
                          "-vf", f"fps={fps or FPS},scale={w}:{h}:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w)


def farneback(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Dense flow a -> b, (h, w, 2) as (dx, dy); the h2 analysis's parameters."""
    import cv2

    return cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)


def flow_mags(frames: np.ndarray) -> np.ndarray:
    """Per frame step, the mean flow magnitude in px at the frames' size."""
    return np.array([float(np.linalg.norm(farneback(frames[i], frames[i + 1]), axis=-1).mean())
                     for i in range(len(frames) - 1)], dtype=np.float32)


def camera_fit(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray) -> np.ndarray:
    """(A, B, ty, tx) of the similarity, refitted on the TRIM best-explained points."""
    sol = fl.fit4(pts, disp, centre)
    res = fl.residuals4(pts, disp, centre, sol)
    keep = res <= np.quantile(res, TRIM)
    return fl.fit4(pts[keep], disp[keep], centre) if keep.sum() >= 4 else sol


def split_step(flow: np.ndarray) -> tuple[float, float]:
    """(camera, residual): the mean px the fitted camera move explains, and the
    mean px it leaves over, on the flow's sample grid."""
    pts = fl.grid_points(flow.shape, step=max(2, min(flow.shape[:2]) // 32))
    disp, centre = fl.sample(flow, pts), np.array(flow.shape[:2], float) / 2
    sol = camera_fit(pts, disp, centre)
    pred = (fl.design(pts, centre) @ sol).reshape(-1, 2)
    return float(np.linalg.norm(pred, axis=1).mean()), float(np.linalg.norm(disp - pred, axis=1).mean())


def global_and_residual(frames: np.ndarray) -> dict[str, np.ndarray]:
    """Per frame step: total mean flow, the camera's share, the subject's residual."""
    total, cam, res = [], [], []
    for i in range(len(frames) - 1):
        flow = farneback(frames[i], frames[i + 1])
        c, r = split_step(flow)
        total.append(float(np.linalg.norm(flow, axis=-1).mean())); cam.append(c); res.append(r)
    return {k: np.array(v, dtype=np.float32) for k, v in (("total", total), ("camera", cam), ("residual", res))}


def step_kinds(total: np.ndarray, camera: np.ndarray, residual: np.ndarray, static: float = STATIC) -> np.ndarray:
    """'static' under `static`, else whichever of camera and subject is larger."""
    moving = np.where(camera >= residual, "camera", "subject")
    return np.where(total < static, "static", moving)


def longest_run_s(mask: np.ndarray, fps: float = FPS) -> float:
    """Seconds of the longest run of True steps."""
    best = run = 0
    for m in mask:
        run = run + 1 if m else 0
        best = max(best, run)
    return round(best / fps, 2)


def summarize(parts: dict[str, np.ndarray], fps: float = FPS, static: float = STATIC) -> dict:
    """Shares of static, camera and subject steps, the longest still run, the mean flow."""
    kinds = step_kinds(parts["total"], parts["camera"], parts["residual"], static)
    n = len(kinds)
    share = (lambda k: round(float(np.mean(kinds == k)), 3)) if n else (lambda k: 0.0)
    return {"steps": n, "static_share": share("static"), "camera_share": share("camera"),
            "subject_share": share("subject"), "longest_static_run_s": longest_run_s(kinds == "static", fps),
            "mean_flow": round(float(parts["total"].mean()), 3) if n else 0.0,
            "mean_camera": round(float(parts["camera"].mean()), 3) if n else 0.0,
            "mean_subject": round(float(parts["residual"].mean()), 3) if n else 0.0}


def is_still(m: dict, seconds: float, exempt: bool = False) -> bool:
    """HARD: long enough to be seen and static for WALL of it, unless planned still."""
    return not exempt and seconds >= MIN_SECONDS and m["static_share"] >= WALL


def is_advisory(m: dict, seconds: float, exempt: bool = False) -> bool:
    """ADVISORY: static for ADVISORY of it at any length, unless planned still."""
    return not exempt and m["static_share"] >= ADVISORY


def measure(video, seconds: float | None = None, start: float = 0.0, exempt: bool = False) -> dict:
    """The take's stillness over its placed `seconds` from `start` (the head the
    cut skips); `exempt` for a shot the plan declares still."""
    frames = read_frames(Path(video), seconds, start=start)
    m = summarize(global_and_residual(frames))
    placed = round(float(seconds) if seconds else len(frames) / FPS, 2)
    return m | {"seconds": placed, "exempt": exempt, "still": is_still(m, placed, exempt),
                "advisory": is_advisory(m, placed, exempt)}


def note(m: dict) -> str:
    """The row's note: the static share, its longest run, and why it fails."""
    text = f"{int(round(m['static_share'] * 100))}% static, run {m['longest_static_run_s']}s"
    if m.get("exempt"):
        return text + " (planned still)"
    return text + (" HARD: the whole frame stands still" if m.get("still") else "")


def gate_args(m: dict) -> dict:
    """The keyword arguments of a take_verdict.Gate: `Gate(**gate_args(m))`."""
    penalty = 60.0 * m["static_share"] if m["still"] else (20.0 * m["static_share"] if m.get("advisory") else 0.0)
    return {"name": KIND, "value": m["static_share"], "ok": not m["still"], "hard": True,
            "note": note(m), "penalty": round(penalty, 1)}


def fault(index: int, m: dict) -> dict | None:
    """A judges.verdict.Fault-shaped dict for a still take; None when it moves."""
    if not m.get("still"):
        return None
    keys = ("static_share", "longest_static_run_s", "seconds", "camera_share", "subject_share", "mean_flow")
    return {"kind": KIND, "where": f"T{index:02d}", "severity": "normal", "note": note(m),
            "evidence": {k: m[k] for k in keys if k in m} | {"wall": WALL, "static": STATIC}}
