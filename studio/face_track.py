"""One crop track per face in a take, for the face refine (studio/face_refine.py).

Detections (the anime-trained face_yolov8m.pt every few frames, studio/face_detect.py;
MTCNN when its worker fails) are linked frame to frame by nearness; a track ends when
its face is gone too long, so a person who walks out never hands his window to the man
beside him (F2 T22 drifted from Utterson to Enfield), and it is cut at a hard cut.
A track's boxes are interpolated over its life and held at its ends; the centre is
median-smoothed over 21 frames and the size over 51 (ComfyUI-H3-FaceRefine, Carasibana,
MIT: the ideas ported, nothing installed), so the window sits still and follows a
push-in slowly without ever pumping.
"""
from __future__ import annotations

import numpy as np

from studio import h3

EVERY = 3
"""Detect on every 3rd frame and interpolate between (YOLO on CPU: about a third of a take's
frames; MTCNN read every 4th, 18 s of CPU for a 192-frame take)."""
GAP = 12
MIN_HITS = 4
JUMP_FACES = 2.0
JUMP_FLOOR = 48.0
SMOOTH = 9
CENTRE_SMOOTH = 21
SIZE_SMOOTH = 51
"""Running-median windows in frames (ComfyUI-H3-FaceRefine: centre over 21, size over 51)."""
MARGIN = 2.4
MIN_SIDE = 96

Box = tuple[float, float, float, float]


def centre(b: Box) -> tuple[float, float]:
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2


def height(b: Box) -> float:
    return b[3] - b[1]


def near(a: Box, b: Box) -> float:
    """Centre distance, in pixels."""
    (ax, ay), (bx, by) = centre(a), centre(b)
    return float(np.hypot(ax - bx, ay - by))


def iou(a: Box, b: Box) -> float:
    """Intersection over union of two boxes, 0..1."""
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - w * h
    return w * h / union if union > 0 else 0.0


def reach(b: Box) -> float:
    """How far a face may move between detections and stay the same face."""
    return max(JUMP_FLOOR, JUMP_FACES * height(b))


def extend(tracks: list[list], live: list[int], t: int, found: list[Box]) -> list[int]:
    """Give each detection at frame `t` to its nearest live track in reach, else a new track."""
    taken: set[int] = set()
    for b in sorted(found, key=height, reverse=True):
        options = [k for k in live if k not in taken and near(tracks[k][-1][1], b) <= reach(tracks[k][-1][1])]
        k = min(options, key=lambda k: near(tracks[k][-1][1], b)) if options else None
        if k is None:
            tracks.append([])
            k = len(tracks) - 1
        tracks[k].append((t, b))
        taken.add(k)
    return sorted(taken)


def link(dets: dict[int, list[Box]], gap: int = GAP) -> list[list[tuple[int, Box]]]:
    """Detections by frame -> tracks of (frame, box); a track unseen for `gap` frames ends."""
    tracks: list[list] = []
    for t in sorted(dets):
        live = [k for k, tr in enumerate(tracks) if t - tr[-1][0] <= gap]
        extend(tracks, live, t, list(dets[t]))
    return tracks


def keep(tracks: list[list], hits: int = MIN_HITS) -> list[list]:
    """Tracks seen often enough to be a face, not a flicker of the detector."""
    return [tr for tr in tracks if len(tr) >= hits]


def life(track: list) -> tuple[int, int]:
    return track[0][0], track[-1][0]


STITCH_GAP = 48
STITCH_FACES = 3.0
STITCH_FLOOR = 80.0


def joins(a: list, b: list) -> bool:
    """`b` picks up where `a` lost its face: after it, soon, and near where it was."""
    gap = b[0][0] - a[-1][0]
    room = max(STITCH_FLOOR, STITCH_FACES * height(a[-1][1]))
    return 0 < gap <= STITCH_GAP and near(a[-1][1], b[0][1]) <= room


def stitch(tracks: list[list]) -> list[list]:
    """Pieces of one face split by a stretch the detector missed, joined in time
    order (Jekyll ep01 T07: Hyde came back as two pieces 20 frames apart)."""
    out: list[list] = []
    for b in sorted(tracks, key=lambda tr: tr[0][0]):
        options = [a for a in out if joins(a, b)]
        if options:
            a = min(options, key=lambda a: near(a[-1][1], b[0][1]))
            a.extend(b)
        else:
            out.append(list(b))
    return out


def split(tracks: list[list], cuts: list[int]) -> list[list]:
    """Each track cut at every hard cut (the first frame of a new shot): a face on both
    sides of a cut is two faces to the crop, never one window swimming across."""
    out: list[list] = []
    for tr in tracks:
        piece: list = []
        for t, b in tr:
            if piece and any(piece[-1][0] < c <= t for c in cuts):
                out.append(piece)
                piece = []
            piece.append((t, b))
        out.append(piece)
    return out


def running_median(a: np.ndarray, n: int) -> np.ndarray:
    """Each value the median of the `n` around it, the window shrinking at the ends (never padded)."""
    a, k = np.asarray(a, float), max(int(n), 1) // 2
    return np.array([np.median(a[max(0, i - k):i + k + 1]) for i in range(len(a))])


def track_px(track: list) -> float:
    """The track's smallest face height after a running median over SIZE_SMOOTH frames of
    detections: a push-in is judged by its small start, a one-frame detector dip is not the
    face (ep01 T09 sampled 255, 162 and 119 px: a 162 px close-up)."""
    heights = np.array([height(b) for _, b in track], float)
    return float(running_median(heights, max(SIZE_SMOOTH // EVERY, 1)).min())


def small(tracks: list[list], px: float) -> list[list]:
    """The tracks whose smallest face (track_px) is under `px`: a readable face is left alone."""
    return [tr for tr in tracks if track_px(tr) < px]


def box_mean(a: np.ndarray, n: int) -> np.ndarray:
    """A centred moving average over `n` frames, the ends held."""
    pad = np.pad(np.asarray(a, float), (n // 2, n // 2), mode="edge")
    return np.convolve(pad, np.ones(n) / n, mode="valid")


def fill(track: list, frames: int, smooth: int = SMOOTH) -> np.ndarray:
    """(frames, 4) boxes: interpolated inside the life, held outside; then (smooth > 1) the
    centre median-smoothed over CENTRE_SMOOTH, the size over SIZE_SMOOTH, both box-filtered."""
    at = [t for t, _ in track]
    arr = np.array([b for _, b in track], float)
    full = np.stack([np.interp(range(frames), at, arr[:, k]) for k in range(4)], 1)
    if smooth <= 1:
        return full
    cx, cy = (box_mean(running_median((full[:, k] + full[:, k + 2]) / 2, CENTRE_SMOOTH), smooth) for k in (0, 1))
    w, h = (box_mean(running_median(full[:, k + 2] - full[:, k], SIZE_SMOOTH), smooth) for k in (0, 1))
    return np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 1)


def windows(boxes: np.ndarray, width: int, height_: int) -> list[tuple[int, int, int]]:
    """A square (x, y, side) per frame round the face, the side its smoothed height times
    the margin: a steady face keeps one side, a push-in grows its window slowly."""
    out = []
    for x1, y1, x2, y2 in boxes:
        side = min(int(max(MIN_SIDE, (y2 - y1) * MARGIN)), width, height_)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2 - 0.05 * side
        out.append((int(np.clip(cx - side / 2, 0, width - side)), int(np.clip(cy - side / 2, 0, height_ - side)), side))
    return out


def side_of(wins: list) -> int:
    """The track's common window side (the median): the gate measures every frame at it."""
    return int(np.median([s for _, _, s in wins]))


def crop_span(span: tuple[int, int], frames: int) -> tuple[int, int]:
    """(first frame, count) of the crop clip: the life on H3's frame grid, inside the take."""
    n = h3.legal_frames(span[1] - span[0] + 1)
    while n > frames:
        n -= h3.FRAME_MODULUS
    return max(0, min(span[0], frames - n)), n


def head_box(b: Box, width: int, height_: int) -> Box:
    """The face box widened to the head and hat: what tells two people apart at 30 px."""
    h = height(b)
    x1, x2 = b[0] - 0.25 * h, b[2] + 0.25 * h
    y1, y2 = b[1] - 0.8 * h, b[3] + 0.1 * h
    return max(0.0, x1), max(0.0, y1), min(float(width), x2), min(float(height_), y2)


def hist_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Lab colour histogram correlation of two RGB crops, -1..1.  Lab, not hue: a
    black hat has no hue, and Hyde's black wideawake is what tells him from
    Enfield's light-brown top hat at 30 px (Jekyll ep01 T07: 0.77 against 0.08)."""
    import cv2
    hists = []
    for img in (a, b):
        lab = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_RGB2LAB)
        h = cv2.calcHist([lab], [0, 1, 2], None, [8, 6, 6], [0, 256, 0, 256, 0, 256])
        hists.append(cv2.normalize(h, h).flatten())
    return float(cv2.compareHist(hists[0], hists[1], cv2.HISTCMP_CORREL))


def loose_detector(device: str = "cpu"):
    """MTCNN loosened for 25-40 px faces (F2's tracker): rgb -> [{"box", "score"}]."""
    from facenet_pytorch import MTCNN
    from PIL import Image
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=12, thresholds=[0.5, 0.6, 0.6])

    def detect(rgb: np.ndarray) -> list[dict]:
        boxes, probs = mtcnn.detect(Image.fromarray(rgb))
        return [] if boxes is None else [{"box": [float(v) for v in b], "score": float(p)} for b, p in zip(boxes, probs)]
    return detect
