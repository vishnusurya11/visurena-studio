"""The face refine's gate measures (CPU): one refined crop against the take it came
from.  The walls and the decision live in studio/face_refine.py; this module only
measures.  `detect` / `embed` are facenet's (studio/measure/faces.embedder) in a run
and fakes in a test.

- seam: the mean level change the paste makes to the take OUTSIDE the head, at window scale,
  through the mask the paste uses (round 2, 2026-10-19: the feather or a small face's soft head
  mask; the old feather-band difference read 1.7-2.0x this on round 1's 15 rows);
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


def collateral(src: np.ndarray, ref: np.ndarray, mask: np.ndarray, head: np.ndarray) -> float:
    """The mean level change pasting `ref` through `mask` makes to `src` outside the head."""
    moved = np.abs(ref.astype(np.float32) - src.astype(np.float32)).mean(axis=2) * mask[..., 0]
    return float(moved[~head].mean()) if (~head).any() else 0.0


def seam_and_flicker(src: list[np.ndarray], ref: list[np.ndarray], face: float | None = None,
                     soft: bool = False) -> tuple[float, float, float]:
    """(seam, the take's flicker, the pasted flicker), at window scale; `face` is the face's
    height as a share of the window (None: the margin's 1 / 2.4), `soft` its soft paste."""
    from studio.face_track import MARGIN
    n, side = min(len(src), len(ref)), src[0].shape[0]
    face_px = (face or 1 / MARGIN) * side
    mask, head = face_paste.paste_mask(side, face_px if soft else None), face_paste.head_mask(side, face_px)
    pasted = [(r * mask + s * (1 - mask)).astype(np.uint8) for s, r in zip(src[:n], ref[:n])]
    seam = float(np.mean([collateral(s, r, mask, head) for s, r in zip(src[:n:SEAM_EVERY], ref[:n:SEAM_EVERY])]))
    return seam, face_paste.region_flicker(src[:n]), face_paste.region_flicker(pasted)


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
    share of the window and `soft` its soft paste (seam_and_flicker)."""
    seam, f_src, f_ref = seam_and_flicker(src_w, ref_w, face, soft)
    cs, cr, ids, idr = faces_and_identity(src768, ref768, sheet_vec, detect, embed)
    return face_refine.Measures(id_src=ids, id_ref=idr, seam=round(seam, 2), flick_src=round(f_src, 3),
                                flick_ref=round(f_ref, 3), faces_src=cs, faces_ref=cr,
                                change=None if moved is None else round(moved, 2))


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
