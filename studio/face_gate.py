"""The face refine's gate measures (CPU): one refined crop against the take it came
from.  The walls and the decision live in studio/face_refine.py; this module only
measures.  `detect` / `embed` are facenet's (studio/measure/faces.embedder) in a run
and fakes in a test.

- seam: the level change between the refined crop and the take where the paste's mask falls,
  outside the head (|grad m|-weighted, at window scale; the feather's edge band or a small face's
  soft ring).  Through the feather it is round 1's feather-band difference; it reads a change D as
  D at any face size (fix round 2026-10-19: a mean over the whole window outside the head read a
  13 px face 60 levels off as 2.5);
- outside / ring warp (face-warp fix, 2026-10-19): the production paste (the face core, edge-locked)
  must move no pixel outside the core, and the ring round the face must not warp (flow take -> paste);
- drift: the mean |refined - take| inside the face box (PLAN_FINAL 1a, T8mars' parity cap);
- eyes: the drawn-eye score of the take and of the refined crop (studio/face_eye.py), logged;
- flicker: the face region's frame-to-frame change, the take's own against the
  pasted result (F2 0.81-0.95 of the take's, F3's boiling noise 1.15-1.32);
- faces: the most faces any one 768 crop shows -- centre inside the window's core,
  overlapping boxes merged -- unrefined against refined (a clone or a lost face
  changes it; a sharper face found in more frames does not: Kawajiri POC W);
- identity: facenet cosine to the person's sheet at the crop's face -- the detected
  one, else the box the window was cut round, since no detector reads a drawn face;
- change: the refined crop against the crop it was rendered from (0 = no render).
"""
from __future__ import annotations

import numpy as np

from studio import face_paste, face_refine

SEAM_EVERY = 8


def windows_of(take: list[np.ndarray], wins: list, span: tuple[int, int]) -> list[np.ndarray]:
    """The take cut to the track's window, frame by frame over its life."""
    out = []
    for t in range(span[0], min(span[1], len(take) - 1) + 1):
        x, y, s = wins[t]
        out.append(take[t][y:y + s, x:x + s])
    return out


def at_side(crops: list[np.ndarray], side: int) -> list[np.ndarray]:
    """Window crops of a growing window (a push-in) brought to one side, so seam and flicker
    compare frames of one size."""
    import cv2
    return [c if c.shape[0] == side else cv2.resize(np.ascontiguousarray(c), (side, side), interpolation=cv2.INTER_AREA)
            for c in crops]


def shrunk(crop: list[np.ndarray], start: int, span: tuple[int, int], side: int) -> list[np.ndarray]:
    """The refined crop's frames over the life, shrunk to the window's side."""
    import cv2
    ks = [t - start for t in range(span[0], span[1] + 1) if 0 <= t - start < len(crop)]
    return [cv2.resize(np.ascontiguousarray(crop[k]), (side, side), interpolation=cv2.INTER_AREA) for k in ks]


HEAD_RADII = (0.7, 1.0)
"""The head the seam is read outside of, in face heights (x, y): face, hair and hat crown."""
HEAD_LIFT = 0.15
"""The head's centre sits this many face heights above the face's (the hat)."""
SOFT_OUT = 1.8
"""A small face's seam ring falls from 1 at the head's edge to 0 at 1.8 head radii (smoothstep)."""


def head_shape(side: int, face: float) -> tuple[float, float, float, float]:
    """(cx, cy, rx, ry) of the head in a window of `side` holding a face `face` px high: the face
    sits at 0.55 of the side (studio/face_track.windows), the head's centre HEAD_LIFT above it."""
    return side / 2, face_paste.FACE_Y * side - HEAD_LIFT * face, HEAD_RADII[0] * face, HEAD_RADII[1] * face


def head_radius(side: int, face: float) -> np.ndarray:
    """Every pixel's elliptic radius from the head's centre, 1 on the head's edge."""
    cx, cy, rx, ry = head_shape(side, face)
    yy, xx = np.mgrid[0:side, 0:side].astype(np.float32)
    return np.sqrt(((xx - cx) / max(rx, 1e-6)) ** 2 + ((yy - cy) / max(ry, 1e-6)) ** 2)


def head_mask(side: int, face: float) -> np.ndarray:
    """(side, side) bool: inside the head."""
    return head_radius(side, face) <= 1.0


def soft_mask(side: int, face: float) -> np.ndarray:
    """(side, side, 1) float: 1 on the head, a smoothstep down to 0 at SOFT_OUT head radii, held
    to the window's own feather so its edge is always 0."""
    t = np.clip((head_radius(side, face) - 1.0) / (SOFT_OUT - 1.0), 0.0, 1.0)
    m = (1.0 - t * t * (3.0 - 2.0 * t))[..., None]
    return (m * face_paste.feather(side, max(4, round(side * face_paste.FEATHER_SHARE)))).astype(np.float32)


def seam_mask(side: int, face: float | None) -> np.ndarray:
    """Where the seam is read (round 1-2's paste masks, kept as the seam's ruler when the paste became the
    face core, 2026-10-19): a small face's soft head ring (`face` px high), else the window's feather band.
    It reads how far the redraw strays from the take round the head, on the walls calibrated there."""
    return soft_mask(side, face) if face else face_paste.feather(side, max(4, round(side * face_paste.FEATHER_SHARE)))


def edge_weight(mask: np.ndarray, head: np.ndarray) -> np.ndarray:
    """(side, side) weights a seam is read by: the seam mask's slope |grad m| outside the head --
    a ring in head radii for a small face, the window's edge band for a big one."""
    gy, gx = np.gradient(np.asarray(mask, np.float32).reshape(head.shape))
    return np.hypot(gx, gy) * ~head


def edge_change(src: np.ndarray, ref: np.ndarray, weight: np.ndarray) -> float:
    """The mean level change between `ref` and `src`, weighted by `weight` (0 when it is all 0)."""
    total = float(weight.sum())
    if total <= 0:
        return 0.0
    moved = np.abs(ref.astype(np.float32) - src.astype(np.float32)).mean(axis=2)
    return float((moved * weight).sum() / total)


def face_px_of(face: float | None, side: int) -> float:
    """The face's height in window pixels: its share of the window, else the margin's 1 / 2.4."""
    from studio.face_track import MARGIN
    return (face or 1 / MARGIN) * side


def pasted_of(src: list[np.ndarray], ref: list[np.ndarray], face: float | None) -> tuple[list, list, np.ndarray]:
    """(the edge-locked crops, the pasted windows, the mask) as the production paste makes them."""
    n, side = min(len(src), len(ref)), src[0].shape[0]
    face_px = face_px_of(face, side)
    mask = face_paste.paste_mask(side, face_px)
    locked = [face_paste.band_lock(r, s, mask, face_px) for s, r in zip(src[:n], ref[:n])]
    pasted = [np.rint(r * mask + s * (1 - mask)).astype(np.uint8) for s, r in zip(src[:n], locked)]
    return locked, pasted, mask


def seam_and_flicker(src: list[np.ndarray], ref: list[np.ndarray], face: float | None = None,
                     soft: bool = False) -> tuple[float, float, float]:
    """(seam, the take's flicker, the pasted flicker), at window scale; `face` is the face's height as a
    share of the window (None: the margin's 1 / 2.4), `soft` its floored window.  The seam is read where
    the seam mask falls outside the head (edge_weight), so it reads a change D as D at any face size;
    the flicker is the production paste's (the face core, edge-locked)."""
    side = src[0].shape[0]
    face_px = face_px_of(face, side)
    weight = edge_weight(seam_mask(side, face_px if soft else None), head_mask(side, face_px))
    _, pasted, _ = pasted_of(src, ref, face)
    n = len(pasted)
    seam = float(np.mean([edge_change(s, r, weight) for s, r in zip(src[:n:SEAM_EVERY], ref[:n:SEAM_EVERY])]))
    return seam, face_paste.region_flicker(src[:n]), face_paste.region_flicker(pasted)


FLOW_SIDE = 384
"""The ring warp is read at the audit's scale (docs/audit/2026-10-19_face_warp: 1 px there ~0.7 take px)."""
RING = (1.2, 1.8)
"""The ring round the face core the warp is read on, in core radii: hat brim, hair, ears, collar, and
clear of the flow's own reach into the redrawn face."""


def ring_mask(side: int, face: float | None) -> np.ndarray:
    """(side, side) bool: the RING round the face core in a window of `side`."""
    r = face_paste.core_radius(side, face_px_of(face, side))
    return (r >= RING[0]) & (r <= RING[1])


def ring_warp(src: list[np.ndarray], pasted: list[np.ndarray], face: float | None) -> float:
    """Mean optical-flow shift (px at FLOW_SIDE) from the take to the pasted window on the ring round the
    face: the head-area warp the owner saw (square paste 0.9-3.1, the take against itself 0)."""
    import cv2
    ring, out = ring_mask(FLOW_SIDE, face), []
    for s, p in zip(src[::SEAM_EVERY], pasted[::SEAM_EVERY]):
        a, b = (cv2.cvtColor(cv2.resize(np.ascontiguousarray(f), (FLOW_SIDE, FLOW_SIDE), interpolation=cv2.INTER_AREA),
                             cv2.COLOR_RGB2GRAY) for f in (s, p))
        flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 4, 21, 3, 5, 1.1, 0)
        out.append(float(np.hypot(flow[..., 0], flow[..., 1])[ring].mean()))
    return float(np.mean(out)) if out else 0.0


def paste_check(src: list[np.ndarray], ref: list[np.ndarray], face: float | None) -> tuple[float, float]:
    """(the most any pixel outside the mask moved, the ring warp) of the production paste: outside the
    face core the pasted window must be the take."""
    _, pasted, mask = pasted_of(src, ref, face)
    out = mask[..., 0] == 0
    moved = max((float(np.abs(p.astype(np.int16) - s.astype(np.int16))[out].max(initial=0)) for s, p in zip(src, pasted)),
                default=0.0)
    return moved, ring_warp(src, pasted, face)


DRIFT_EVERY = 4


def drift(src: list[np.ndarray], ref: list[np.ndarray], boxes: list) -> float | None:
    """Mean |refined - take| per pixel inside each frame's face box (window coordinates)."""
    vals = []
    for s, r, b in list(zip(src, ref, boxes))[::DRIFT_EVERY]:
        x1, y1, x2, y2 = (int(round(v)) for v in b)
        x1, y1 = max(x1, 0), max(y1, 0)
        a, c = s[y1:y2, x1:x2].astype(np.float32), r[y1:y2, x1:x2].astype(np.float32)
        if a.size and a.shape == c.shape:
            vals.append(float(np.abs(c - a).mean()))
    return float(np.mean(vals)) if vals else None


EDGE = 0.15
"""A face whose centre falls in this outer share of the window is a neighbour."""
OVERLAP = 0.3


def inside(b, side: int) -> bool:
    """The box's centre lies in the window's core, not its outer EDGE band."""
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    lo, hi = EDGE * side, (1 - EDGE) * side
    return lo <= cx <= hi and lo <= cy <= hi


def dedupe(found: list[dict]) -> list[dict]:
    """Overlapping boxes merged into the best-scored one."""
    from studio.face_track import iou
    kept: list[dict] = []
    for f in sorted(found, key=lambda f: -float(f.get("score", 1.0))):
        if all(iou(f["box"], k["box"]) <= OVERLAP for k in kept):
            kept.append(f)
    return kept


def count(found: list[dict], side: int) -> int:
    """Faces in one crop: inside the window, overlaps merged."""
    return len(dedupe([f for f in found if inside(f["box"], side)]))


def window_face(side: int) -> tuple[float, float, float, float]:
    """The face box the crop window was cut round (studio/face_track.windows)."""
    from studio.face_track import MARGIN
    h, cx, cy = side / MARGIN, side / 2, side / 2 + 0.05 * side
    return cx - h / 2, cy - h / 2, cx + h / 2, cy + h / 2


def crop_face(found: list[dict], side: int):
    """The largest face inside the window, else the box the window was cut round:
    a drawn face no detector reads is still where the track put it."""
    core = [f for f in found if inside(f["box"], side)]
    if not core:
        return window_face(side)
    return max(core, key=lambda f: f["box"][3] - f["box"][1])["box"]


def read_faces(crops: list[np.ndarray], sheet_vec, detect, embed) -> tuple[int, float | None]:
    """(the most faces any one crop shows, mean cosine of each crop's face to the sheet)."""
    from studio.measure import faces
    most, cos = 0, []
    for rgb in crops:
        found = detect(rgb)
        most = max(most, count(found, rgb.shape[0]))
        vec = embed(rgb, crop_face(found, rgb.shape[0])) if sheet_vec is not None else None
        if vec is not None:
            cos.append(faces.cosine(vec, sheet_vec))
    return most, (float(np.mean(cos)) if cos else None)


def change(src: list[np.ndarray], ref: list[np.ndarray]) -> float:
    """Mean |refined - source| per pixel over the paired frames: 0 is no render."""
    n = min(len(src), len(ref))
    if n == 0:
        return 0.0
    return float(np.mean([np.abs(a.astype(np.float32) - b.astype(np.float32)).mean() for a, b in zip(src[:n], ref[:n])]))


def faces_and_identity(src768, ref768, sheet_vec, detect, embed):
    """(faces unrefined, faces refined, identity unrefined, identity refined)."""
    cs, ids = read_faces(src768, sheet_vec, detect, embed)
    cr, idr = read_faces(ref768, sheet_vec, detect, embed)
    return cs, cr, ids, idr


def measure(src_w, ref_w, src768, ref768, sheet_vec, detect, embed, moved: float | None = None,
            face: float | None = None, soft: bool = False) -> face_refine.Measures:
    """Every measure the decision reads, for one person's refined crop; `moved` is
    the refined crop's change from the crop it was rendered from; `face` the face's
    share of the window and `soft` its floored window (seam_and_flicker, paste_check)."""
    seam, f_src, f_ref = seam_and_flicker(src_w, ref_w, face, soft)
    outside, ring = paste_check(src_w, ref_w, face)
    cs, cr, ids, idr = faces_and_identity(src768, ref768, sheet_vec, detect, embed)
    return face_refine.Measures(id_src=ids, id_ref=idr, seam=round(seam, 2), flick_src=round(f_src, 3),
                                flick_ref=round(f_ref, 3), faces_src=cs, faces_ref=cr,
                                change=None if moved is None else round(moved, 2),
                                outside=round(outside, 2), ring_warp=round(ring, 3))


def face_boxes(boxes, wins: list, life: tuple[int, int], side: int) -> list:
    """The track's smoothed face box on each frame of its life, in its window's coordinates at `side`."""
    out = []
    for t in range(life[0], life[1] + 1):
        x, y, s = wins[t]
        k = side / s
        b = boxes[t]
        out.append(((b[0] - x) * k, (b[1] - y) * k, (b[2] - x) * k, (b[3] - y) * k))
    return out


def extras(src_w: list, ref_w: list, boxes: list) -> dict:
    """The logged measures beside the walls: drift inside the face box, the drawn-eye scores."""
    from studio import face_eye
    n = min(len(src_w), len(ref_w), len(boxes))
    d = drift(src_w[:n], ref_w[:n], boxes[:n])
    e_src, e_ref = face_eye.track_eyes(src_w[:n:2], boxes[:n:2]), face_eye.track_eyes(ref_w[:n:2], boxes[:n:2])
    r = lambda v: None if v is None else round(v, 2)
    return {"drift": r(d), "eye_src": r(e_src), "eye_ref": r(e_ref)}
