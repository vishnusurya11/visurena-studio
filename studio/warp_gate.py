"""G-WARP: is the take's face redrawn frame to frame?  (main session 2026-10-18,
from measured evidence, for owner veto; docs/audit/2026-10-18_warping/WARPING.md.)

MiniMax-H3 ref2va re-synthesises a 30-40 px face every frame: eyes melt to slits,
the grin and nose wedge reshape, the identity jumps as the face scales (Kawajiri
POC W, f70-98).  Per take, on the CPU:

- faces: MTCNN every 2nd frame at full resolution, prob >= 0.9, linked into tracks
  by IoU > 0.3 between neighbouring detections; a track swap is a new track, never
  a fault (POC M swaps between two men); a frame borrows its nearest detection
  within 6 frames;
- flow: Farneback forward and backward at 384 px; frame t+1 is warped back onto t
  and the residual is counted only where the two flows agree (< 1.5 px), so an
  occlusion is not a warp;
- E(t) = face residual - (2.51 x bg residual + 1.69 x face flow + 1.00), the same
  over the eye mask; S = p90 of E, Se = p90 of the eye's.

FAIL (S > 2.5 only): one seed retake, then the F2 face refine when the face is small
(a tracked median under 60 px), else the take ships flagged.  EYE (S <= 2.5, Se > 3.0):
an advisory, never a fail -- all eight ep01 hard fails were Se-only (Se 3.2-5.0, S
-0.64..1.96) and the seeds cured 0 of 4 (P07, 2026-10-19).  WARN (1.5 < S <= 2.5) and
UNMEASURABLE (face tracked in under 45 % of searched frames): the F2 face refine, a warn
only for a small face or S_held > 1.5 (H3 animates on threes; the step pairs inflate S).
Fitted on 27 clips with no owner labels; every score is logged in the dq record so the
cut can be refit on labelled takes.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

SIDE = 384
EVERY = 2
PROB_MIN = 0.9
MIN_FACE_PX = 24
LINK_IOU = 0.3
NEAREST = 6
FB_MAX = 1.5
LEAST_PX = 20
MASK_PX = 50
BG_K, FLOW_K, BIAS = 2.51, 1.69, 1.00
"""The pooled fit over 27 clips (WARPING.md section 3)."""
FAIL_S, FAIL_SE, WARN_S = 2.5, 3.0, 1.5
TRACKED_MIN = 0.45
RETAKES = 1
SMALL_TRACK_PX = 60.0
"""A face tracked under this many render pixels is the refine's; at or over it F2 adds nothing."""
HELD_WALL = 1.5
FACE_W_SMALL = 0.10
PERIODS = (3, 2, 4)
HELD_RATIO = 0.25
"""A cadence is real when the held pairs move under this share of the step pairs."""
PENALTY = 40.0


# ---- the score ---------------------------------------------------------------------

def excess(rf: np.ndarray, rb: np.ndarray, mf: np.ndarray) -> np.ndarray:
    """What the face residual holds beyond the background's and its own motion's."""
    return rf - (BG_K * rb + FLOW_K * mf + BIAS)


def score(e: np.ndarray) -> float | None:
    """p90 over the frames that were measured; None when none was."""
    finite = np.asarray(e, float)[np.isfinite(e)]
    return float(np.percentile(finite, 90)) if finite.size else None


def verdict(s: float | None, se: float | None, share: float) -> str:
    """pass / warn / eye / fail / unmeasurable.  Only S over its wall fails; an eye-only
    excess (S <= 2.5, Se > 3.0) is the advisory `eye`."""
    if share < TRACKED_MIN or (s is None and (se is None or se <= FAIL_SE)):
        return "unmeasurable"
    if s is not None and s > FAIL_S:
        return "fail"
    if se is not None and se > FAIL_SE:
        return "eye"
    return "warn" if s > WARN_S else "pass"


def cure(state: str, taken: int, track_px_min: float | None = None) -> str:
    """'seed' for a fail not yet retaken, 'refine' (F2) for a small face, '' otherwise:
    a failing take whose smallest tracked face is readable ships flagged."""
    if state == "fail":
        if taken < RETAKES:
            return "seed"
        return "" if track_px_min is not None and track_px_min >= SMALL_TRACK_PX else "refine"
    return "refine" if state in ("warn", "unmeasurable") else ""


def spans(e: np.ndarray, wall: float = FAIL_S) -> list[list[int]]:
    """[first, last] frame runs where E is over the wall: the retake record and F2's window."""
    out: list[list[int]] = []
    for t in np.flatnonzero(np.nan_to_num(np.asarray(e, float), nan=-np.inf) > wall):
        if out and out[-1][1] == t - 1:
            out[-1][1] = int(t)
        else:
            out.append([int(t), int(t)])
    return out


def split_pairs(frames: int, period: int, phase: int) -> tuple[list[int], list[int]]:
    """(held, step) pair indices: with a cadence the picture changes on pair t when
    (t + 1 - phase) is a multiple of the period."""
    pairs = range(max(frames - 1, 0))
    step = [t for t in pairs if period > 1 and (t + 1 - phase) % period == 0]
    return [t for t in pairs if t not in step], step


def cadence(gray: list[np.ndarray]) -> tuple[int, int]:
    """(period, phase) of the frame repeat, (1, 0) when every pair moves."""
    d = np.array([np.abs(a.astype(np.float32) - b.astype(np.float32)).mean() for a, b in zip(gray, gray[1:])])
    best = (HELD_RATIO, 1, 0)
    for p in PERIODS:
        for ph in range(p):
            held, step = split_pairs(len(gray), p, ph)
            if held and step and d[step].mean() > 0:
                best = min(best, (d[held].mean() / d[step].mean(), p, ph))
    return (best[1], best[2]) if best[1] > 1 else (1, 0)


def pick(e: np.ndarray, idx: list[int]) -> float | None:
    """The score over the chosen pairs; None when there are none."""
    return score(e[idx]) if idx else None


def track_stats(tracks: list[list], scale: float) -> list[dict]:
    """Each track's median face height in render px and its life in detections."""
    return [{"median_px": round(float(np.median([(b[3] - b[1]) / scale for _, b in tr])), 1), "life": len(tr)}
            for tr in tracks]


def face_width(tracks: list[list]) -> float | None:
    """The longest track's median face width as a share of the frame."""
    if not tracks:
        return None
    longest = max(tracks, key=len)
    return round(float(np.median([(b[2] - b[0]) / SIDE for _, b in longest])), 3)


def judge(rows: dict, share: float, frames: int, tracks: list[dict] | None = None,
          cad: tuple[int, int] = (1, 0), face_w: float | None = None) -> dict:
    """The measure the dq record keeps, from the per-frame rows rf, rb, mf, re.  Under
    TRACKED_MIN the faces were barely found: S and Se are None, S_raw keeps the number."""
    e = excess(rows["rf"], rows["rb"], rows["mf"])
    ee = excess(rows["re"], rows["rb"], rows["mf"])
    s, se = score(e), score(ee)
    r = lambda v: None if v is None else round(v, 2)
    seen = share >= TRACKED_MIN
    held, step = split_pairs(frames, *cad)
    return {"state": verdict(s, se, share), "S": r(s) if seen else None, "Se": r(se) if seen else None,
            "S_raw": r(s), "share": round(share, 2), "frames": frames, "spans": spans(e),
            "period": cad[0], "phase": cad[1], "S_held": r(pick(e, held)), "S_step": r(pick(e, step)),
            "Se_held": r(pick(ee, held)), "Se_step": r(pick(ee, step)),
            "frames_eye": int((np.nan_to_num(ee, nan=-np.inf) > FAIL_SE).sum()), "face_w": face_w,
            "eye_spans": spans(ee, FAIL_SE), "tracks": tracks or []}


def warn_routes(m: dict) -> bool:
    """A warn goes to F2 only for a small face or a bad held score; no cadence log, the old route."""
    held, width = m.get("S_held"), m.get("face_w")
    if held is None or width is None:
        return True
    return width < FACE_W_SMALL or held > HELD_WALL


def smallest_track(m: dict | None) -> float | None:
    """The smallest tracked median face height (render px) in a warp measure; None unlogged."""
    heights = [t["median_px"] for t in (m or {}).get("tracks") or []]
    return min(heights) if heights else None


def row(m: dict | None):
    """The take gate's `warp` row: HARD on S over its wall only.  The state is recomputed
    from the numbers (a stored `fail` of an older gate does not stand); `eye` is advisory."""
    from studio.take_verdict import Gate
    if not m:
        return Gate("warp", None, True, True, "not measured")
    state = verdict(m.get("S"), m.get("Se"), m["share"])
    show = lambda v: "no score" if v is None or m["share"] < TRACKED_MIN else v
    note = f"{state}: S {show(m.get('S'))} Se {show(m.get('Se'))} over {m['share']:.0%} tracked; over the wall {m['spans']}"
    if state == "fail":
        return Gate("warp", m["S"], False, True, f"{note} HARD: the face is redrawn frame to frame", PENALTY)
    if state == "eye":
        return Gate("warp", m["S"], True, False, f"{note} advisory: the eye alone moves (owner label wanted)")
    return Gate("warp", m.get("S"), True, True, note)


# ---- the flow --------------------------------------------------------------------------

def grid(shape) -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    return xx, yy


def residual(g0: np.ndarray, g1: np.ndarray, fwd: np.ndarray) -> np.ndarray:
    """|frame t+1 warped back onto t - frame t|."""
    import cv2
    xx, yy = grid(g0.shape)
    warped = cv2.remap(g1.astype(np.float32), xx + fwd[..., 0], yy + fwd[..., 1], cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_REPLICATE)
    return np.abs(warped - g0.astype(np.float32))


def consistent(fwd: np.ndarray, bwd: np.ndarray) -> np.ndarray:
    """Pixels whose forward flow, followed back, returns within FB_MAX px."""
    import cv2
    xx, yy = grid(fwd.shape[:2])
    back = cv2.remap(bwd, xx + fwd[..., 0], yy + fwd[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.linalg.norm(fwd + back, axis=2) < FB_MAX


def region(res: np.ndarray, mask: np.ndarray, ok: np.ndarray, least: int = LEAST_PX) -> float:
    """Mean residual over the masked, agreeing pixels; NaN when too few."""
    sel = mask & ok
    return float(res[sel].mean()) if sel.sum() >= least else float("nan")


def flows(g0: np.ndarray, g1: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Farneback forward and backward (the prototype's parameters)."""
    import cv2
    args = (None, 0.5, 4, 21, 3, 5, 1.1, 0)
    return cv2.calcOpticalFlowFarneback(g0, g1, *args), cv2.calcOpticalFlowFarneback(g1, g0, *args)


# ---- the faces -------------------------------------------------------------------------

def link(dets: dict[int, list]) -> list[list]:
    """Tracks of (frame, box): a detection joins the track whose last box it overlaps."""
    from studio.face_track import iou
    tracks: list[list] = []
    for t in sorted(dets):
        for b in dets[t]:
            live = [tr for tr in tracks if tr[-1][0] < t and iou(tr[-1][1], b) > LINK_IOU]
            if live:
                max(live, key=lambda tr: iou(tr[-1][1], b)).append((t, tuple(b)))
            else:
                tracks.append([(t, tuple(b))])
    return tracks


def boxes_at(t: int, tracks: list[list]) -> list:
    """Each track's detection nearest to frame t, within NEAREST frames."""
    out = []
    for tr in tracks:
        k, b = min(tr, key=lambda d: abs(d[0] - t))
        if abs(k - t) <= NEAREST:
            out.append(b)
    return out


def tracked_share(tracks: list[list], frames: int) -> float:
    """Searched frames on which some track holds a face."""
    searched = len(range(0, frames, EVERY))
    found = {t for tr in tracks for t, _ in tr}
    return len(found) / searched if searched else 0.0


def box_mask(boxes: list, side: int) -> np.ndarray:
    m = np.zeros((side, side), bool)
    for x1, y1, x2, y2 in boxes:
        m[max(0, int(y1)):max(0, int(y2)), max(0, int(x1)):max(0, int(x2))] = True
    return m


def body_mask(boxes: list, side: int) -> np.ndarray:
    """Each face box widened 1.2 widths a side and carried 4 heights down: the body,
    which the background residual must not count (its motion is not the camera's)."""
    grown = [(x1 - 1.2 * (x2 - x1), y1, x2 + 1.2 * (x2 - x1), y2 + 4 * (y2 - y1)) for x1, y1, x2, y2 in boxes]
    return box_mask(grown, side)


def eye_mask(landmarks: list, side: int) -> np.ndarray:
    """A square patch round each eye, 0.35 of the eye distance."""
    m = np.zeros((side, side), bool)
    for pts in landmarks:
        (lx, ly), (rx, ry) = pts[0], pts[1]
        r = max(3, int(0.35 * abs(rx - lx)))
        for ex, ey in ((int(lx), int(ly)), (int(rx), int(ry))):
            m[max(0, ey - r):ey + r, max(0, ex - r):ex + r] = True
    return m


# ---- the take ----------------------------------------------------------------------------

def detector(device: str = "cpu"):
    """The calibration's MTCNN (min face 24 px, thresholds 0.5/0.6/0.6) with
    landmarks, CPU: rgb -> [{"box", "landmarks", "score"}].  facenet's default
    thresholds lose the approaching drawn face: POC W read S 2.32, not 2.65."""
    from facenet_pytorch import MTCNN
    from PIL import Image
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=MIN_FACE_PX, thresholds=[0.5, 0.6, 0.6])

    def detect(rgb: np.ndarray) -> list[dict]:
        boxes, probs, points = mtcnn.detect(Image.fromarray(rgb), landmarks=True)
        if boxes is None:
            return []
        return [{"box": [float(v) for v in b], "landmarks": p.tolist(), "score": float(s)}
                for b, s, p in zip(boxes, probs, points)]
    return detect


def gray_frames(video: Path) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """(full-resolution RGB, gray SIDE x SIDE) frames of the take."""
    import cv2
    cap, rgb, gray = cv2.VideoCapture(str(video)), [], []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        rgb.append(bgr[:, :, ::-1].copy())
        gray.append(cv2.cvtColor(cv2.resize(bgr, (SIDE, SIDE), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY))
    cap.release()
    return rgb, gray


def faces_of(rgb: list[np.ndarray], detect) -> tuple[dict, dict]:
    """(frame -> boxes, box -> landmarks) at SIDE scale, every EVERY frames."""
    dets, marks = {}, {}
    for t in range(0, len(rgb), EVERY):
        sc = SIDE / rgb[t].shape[1]
        found = [f for f in detect(rgb[t]) if f.get("score", 1.0) >= PROB_MIN
                 ]
        dets[t] = [tuple(v * sc for v in f["box"]) for f in found]
        marks.update({b: [(x * sc, y * sc) for x, y in f.get("landmarks") or []] for b, f in zip(dets[t], found)})
    return {t: b for t, b in dets.items() if b}, marks


def frame_rows(gray: list[np.ndarray], tracks: list[list], marks: dict) -> dict:
    """Per frame pair: face, background and eye residual, and the face's mean flow."""
    rows = {k: [] for k in ("rf", "rb", "mf", "re")}
    for t in range(len(gray) - 1):
        fwd, bwd = flows(gray[t], gray[t + 1])
        res, ok, boxes = residual(gray[t], gray[t + 1], fwd), consistent(fwd, bwd), boxes_at(t, tracks)
        face = box_mask(boxes, SIDE)
        eyes = eye_mask([marks[b] for b in boxes if len(marks.get(b) or []) >= 2], SIDE)
        has = face.sum() >= MASK_PX
        rows["rf"].append(region(res, face, ok) if has else np.nan)
        rows["rb"].append(region(res, ~(face | body_mask(boxes, SIDE)), ok))
        rows["mf"].append(float(np.linalg.norm(fwd, axis=2)[face].mean()) if has else np.nan)
        rows["re"].append(region(res, eyes, ok) if eyes.any() else np.nan)
    return {k: np.array(v, float) for k, v in rows.items()}


def measure(video: Path, detect=None) -> dict:
    """G-WARP's measure of one take file (about 5 s per 124 frames at 384 px)."""
    rgb, gray = gray_frames(video)
    if len(gray) < 2:
        return {"state": "unmeasurable", "S": None, "Se": None, "share": 0.0, "frames": len(gray), "spans": []}
    dets, marks = faces_of(rgb, detect or detector())
    tracks = link(dets)
    stats = track_stats(tracks, SIDE / rgb[0].shape[1])
    return judge(frame_rows(gray, tracks, marks), tracked_share(tracks, len(gray)), len(gray),
                 stats, cadence(gray), face_width(tracks))
