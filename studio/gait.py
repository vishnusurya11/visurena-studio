"""G-GAIT: does a walker's ground travel pay for the steps his feet take?

THE RULE.  A planted foot does not move against the ground, so a walking body
crosses, per step, about the distance between its feet.  Ground travel per
second divided by steps per second is the step length.  A walker whose legs
cycle fast while his body barely crosses the ground is SHUFFLING: the feet that
"step" must slide back over the cobbles each time.

Jekyll HEL ep01 T03 (owner 2026-10-14: "the little walk is weird"): the little
man's legs cycle at 3.9 steps/s while he crosses 0.13 body heights of ground a
second -- 0.03 heights a step, a mince on the spot.  No row of the take gate
reads a body against its own ground: `held` and `pass-through` read a person
against the scenery only where the plan keeps him in place, the stillness rows
read the whole frame, the eyes read three still frames.

MEASURED, CPU only: a person box per frame (YOLOv10m through OpenCV DNN, the
detector ComfyUI already holds), dense flow (Farneback) at 384 px and 12 fps,
the ground from bands beside the feet, the body from the torso, the legs'
motion against the body (`art`).  The step rate is the strongest rhythm of the
legs' articulation (0.7-4.5 Hz); the travel is the torso against the ground.

CALIBRATION (2026-10-14, docs/audit/2026-10-14_jekyll_ep01_hel/gait_replay.jsonl:
91 walker takes, WotW ep01-27, Scarlet ep01-14, Jekyll ep01): 20 measurable, ONE
fires -- Jekyll T03 (3.94 steps/s, 0.027 heights a step).  The owner-liked WotW
ep03 T07 walks 3.1 steps/s at 0.052; the nearest shipped non-fire is WotW ep06
T23 at 4.04 steps/s and 0.048.  One positive: the wall (0.045) sits just under the
nearest shipped walk, not at the midpoint.  71 of 91 are unmeasured (feet out of
the picture 37, no step rhythm 31, toward/away from the camera 3): a walk the
flow cannot read is unmeasured, never passed as a walk.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import numpy as np

FPS = 12
SIZE = 384
MIN_RUN = 24
"""Two seconds of a person with the feet in the picture, else unmeasured."""
PROMINENCE = 2.5
"""The step rhythm's peak over the spectrum's mean; under it there is no rhythm to count."""
BAND = (0.7, 4.5)
"""Steps per second a walk or a run can take."""
SHUFFLE_CADENCE = 3.0
"""Steps per second past which a short step is a mince, not a stroll."""
SHUFFLE_STEP = 0.045
"""Body heights crossed per step under which the feet must slide (liked floor 0.055)."""
DEPTH = 0.15
"""|d ln(height)/dt| per second past which the walk is toward or away from the camera."""
PENALTY = 40.0

CAMERA = re.compile(r"(?:at a (?:\w+ )?walking pace|a walking pace|travelling[^;,]*?strides?|with each stride|"
                    r"walking stick|walking-stick)", re.I)
GAIT = re.compile(r"\b(?:walks?|walked|stumps?|strides? (?:along|across|out|down|up|toward|to|through|off)|"
                  r"limps?|marches|trudges|hurries|steps (?:along|forward|out|down|across|toward)|"
                  r"runs?|ran)\b", re.I)
THINGS = re.compile(r"\b(?:sand|water|fire|flame|light|lamplight|glint|rain|sweat|dust|shadow|wave|wheat|steam|"
                    r"smoke|ink|blood|tears?|crack|line|scree|pencil|shimmer|wind|shiver|thread|drop)\s+(?:\w+\s+)?"
                    r"runs?\b", re.I)


def walks(motion: str) -> bool:
    """Whether the plan asks a subject to walk or run (the camera's own travel is not a walker)."""
    text = THINGS.sub(" ", CAMERA.sub(" ", motion or ""))
    return bool(GAIT.search(text))


def cadence(rows: list[dict]) -> tuple[float, float]:
    """(steps per second, prominence) of the legs' articulation, per body height."""
    a = np.array([r["art"] / r["h"] for r in rows], dtype=float)
    a = a - a.mean()
    spec = np.abs(np.fft.rfft(a * np.hanning(len(a))))
    freq = np.fft.rfftfreq(len(a), 1 / FPS)
    band = (freq >= BAND[0]) & (freq <= BAND[1])
    if not band.any() or spec[1:].mean() <= 0:
        return 0.0, 0.0
    k = int(np.argmax(np.where(band, spec, -1.0)))
    return float(freq[k]), float(spec[k] / spec[1:].mean())


def longest_run(rows: list) -> list[dict]:
    """The longest stretch of consecutive frames with a person and his feet in the picture."""
    best, cur = [], []
    for r in rows:
        if r and r.get("feet"):
            cur.append(r)
            continue
        best, cur = (cur if len(cur) > len(best) else best), []
    return cur if len(cur) > len(best) else best


def judge(rows: list) -> dict:
    """The gait state of the longest feet-in-frame run: walk, shuffle or unmeasured."""
    run = longest_run(rows)
    if len(run) < MIN_RUN:
        return {"state": f"unmeasured: feet in frame {len(run)} frames", "frames": len(run)}
    if abs(float(np.median([r.get("grow", 0.0) for r in run]))) > DEPTH:
        return {"state": "unmeasured: depth", "frames": len(run)}
    freq, prominence = cadence(run)
    if prominence < PROMINENCE or freq <= 0:
        return {"state": "unmeasured: no step rhythm", "frames": len(run), "prominence": round(prominence, 2)}
    travel = float(np.median([r["travel"] / r["h"] * FPS for r in run]))
    step = travel / freq
    state = "shuffle" if freq >= SHUFFLE_CADENCE and step < SHUFFLE_STEP else "walk"
    return {"state": state, "frames": len(run), "freq": round(freq, 2), "prominence": round(prominence, 2),
            "travel_hps": round(travel, 3), "step_h": round(step, 3)}


def row(m: dict | None, motion: str):
    """The take gate's `gait` row: HARD on a shuffle by a walker the plan asked for."""
    from studio.take_verdict import Gate
    if not walks(motion):
        return Gate("gait", None, True, True, "n/a by the plan")
    if not m or m.get("state", "").startswith("unmeasured") or "step_h" not in m:
        return Gate("gait", None, True, True, "not measured" + (f" ({m['state']})" if m else ""))
    note = f"{m['freq']:.1f} steps/s, {m['step_h']:.3f} heights a step over {m['travel_hps']:.2f} heights/s"
    if m["state"] == "shuffle":
        return Gate("gait", m["step_h"], False, True, f"shuffle: {note} HARD: the feet slide", PENALTY)
    return Gate("gait", m["step_h"], True, True, note)


def _median(flow: np.ndarray, y0: float, y1: float, x0: float, x1: float):
    h, w = flow.shape[:2]
    y0, y1, x0, x1 = max(0, int(y0)), min(h, int(y1)), max(0, int(x0)), min(w, int(x1))
    if y1 - y0 < 2 or x1 - x0 < 2:
        return None
    return np.median(flow[y0:y1, x0:x1].reshape(-1, 2), axis=0)


def per_frame(prev: np.ndarray, cur: np.ndarray, box) -> dict:
    """One frame pair: the ground beside the feet, the torso's travel over it, the legs against the torso."""
    import cv2
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    if y2 > cur.shape[0] - 3 or h < 12:
        return {"feet": False}
    a, b = cv2.cvtColor(prev, cv2.COLOR_RGB2GRAY), cv2.cvtColor(cur, cv2.COLOR_RGB2GRAY)
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    bands = [_median(flow, y2 - 0.06 * h, y2 + 0.10 * h, x1 - 0.8 * w, x1 - 0.1 * w),
             _median(flow, y2 - 0.06 * h, y2 + 0.10 * h, x2 + 0.1 * w, x2 + 0.8 * w),
             _median(flow, y2 + 0.04 * h, y2 + 0.20 * h, x1, x2)]
    bands = [g for g in bands if g is not None]
    body = _median(flow, y1 + 0.2 * h, y1 + 0.55 * h, x1 + 0.25 * w, x2 - 0.25 * w)
    if not bands or body is None:
        return {"feet": False}
    ground = np.median(np.stack(bands), axis=0)
    travel = float(np.linalg.norm(body - ground))
    legs = flow[int(y1 + 0.72 * h):int(y2), max(0, int(x1)):int(x2)].reshape(-1, 2)
    moving = legs[np.linalg.norm(legs - ground, axis=1) > 0.35 * max(travel, 0.3)]
    art = float(np.median(np.linalg.norm(moving - body, axis=1))) if len(moving) > 4 else 0.0
    return {"feet": True, "h": float(h), "travel": travel, "art": art}


Detect = Callable[[np.ndarray], list]


def largest(people: list):
    """The person box (x1, y1, x2, y2) of the biggest, surest person, or None."""
    if not people:
        return None
    return max(people, key=lambda p: (p[0][3] - p[0][1]) * p[1])[0]


def measure(frames: list, detect: Detect | None = None, stride: int = 2) -> dict:
    """The gait state of a take's RGB frames (24 fps native; `stride` 2 reads 12)."""
    import cv2
    if detect is None:
        return {"state": "unmeasured: no person detector"}
    small = [cv2.resize(np.asarray(f), (SIZE, SIZE)) for f in frames[::stride]]
    rows, prev_box = [], None
    for i in range(1, len(small)):
        box = largest(detect(small[i]))
        if box is None:
            rows.append(None)
            prev_box = None
            continue
        r = per_frame(small[i - 1], small[i], box)
        if r.get("feet") and prev_box is not None:
            r["grow"] = float(np.log(max(1.0, box[3] - box[1]) / max(1.0, prev_box[3] - prev_box[1])) * FPS)
        rows.append(r)
        prev_box = box
    return judge(rows)


DETECTOR = Path("models") / "detection" / "yolov10m.onnx"
"""Under ComfyUI's root: the person detector already on the machine."""


def yolo(root: Path | None = None) -> Detect | None:
    """A CPU person detector over OpenCV DNN, or None when the model is absent."""
    import cv2
    if root is None:
        from studio import comfy
        root = comfy.COMFY_ROOT
    path = Path(root) / DETECTOR
    if not path.is_file():
        return None
    net = cv2.dnn.readNetFromONNX(str(path))

    def detect(rgb: np.ndarray) -> list:
        net.setInput(cv2.dnn.blobFromImage(rgb, 1 / 255.0, (640, 640), swapRB=False))
        k = rgb.shape[0] / 640
        return [(tuple(float(v) * k for v in o[:4]), float(o[4]))
                for o in net.forward()[0] if int(o[5]) == 0 and o[4] >= 0.35]
    return detect
