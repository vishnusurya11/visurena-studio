"""One crop track per face in a take, for the face refine (studio/face_refine.py).

Detections (the anime-trained face_yolov8m.pt every few frames, studio/face_detect.py;
MTCNN when its worker fails) are linked frame to frame by nearness; a track ends when
its face is gone too long, so a person who walks out never hands his window to the man
beside him (F2 T22 drifted from Utterson to Enfield), and it is cut at a hard cut.
A track's boxes are interpolated over its life and held at its ends; the centre is
median-smoothed over 21 frames and the size over 51 (ComfyUI-H3-FaceRefine, Carasibana,
MIT: the ideas ported, nothing installed), so the window sits still and follows a
push-in slowly without ever pumping.

Round 2 (2026-10-19, docs/audit/2026-10-19_face_blur/PLAN_FINAL.md section 1a): a track never
jumps to another person -- a detection joins it only at its own size, and once it has LOST its
face it re-acquires only a head `same` reads as its own (Lab colour of the head and hat); a weak
detection only continues a face (`rescue`); the refine runs where the face is soft, with
hysteresis (`soft_span`; VideoFaceDetailer's idea); the crop side is frozen per run
(`frozen_side`); the crop stays inside its shot and on H3's 17k+5 grid (`crop_span`).  Fix round
(the same day): detections go to tracks by least total cost (`assign`: motion, size, head likeness),
since nearest-first swapped two faces of near size crossing; a face within a sample still answers the
head check (`steady`); the stitch never counts a piece as its own rival (`rivals_of`).
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


SIZE_JUMP = 1.5
"""A face at more than 1.5x (or under 1/1.5) the track's last height is another person's
(ep01 T01: Utterson 36 px beside Enfield's top hat; a push-in grows a few % per sample)."""


def same_size(a: Box, b: Box) -> bool:
    ha, hb = max(height(a), 1e-6), max(height(b), 1e-6)
    return max(ha, hb) / min(ha, hb) <= SIZE_JUMP


def steady(same, track: list, b: Box, t: int) -> bool:
    """A face found within a sample of the track's last still reads as its head, when the check can
    say (`same.continues`): someone stepping in front of a face is never its next sample."""
    check = getattr(same, "continues", None)
    return check is None or bool(check(track, b, t))


def fits(track: list, b: Box, t: int, same=None, others=()) -> bool:
    """`b` at frame `t` can be this track's face: in reach, at its size, its head still (`steady`)
    and -- once the track has lost its face for a sample or more -- its own head by
    `same(track, b, t, others)`, the other tracks being the other people it might be."""
    last_t, last = track[-1]
    if near(last, b) > reach(last) or not same_size(last, b):
        return False
    if t - last_t <= EVERY:
        return steady(same, track, b, t)
    return same is None or bool(same(track, b, t, others))


def predicted(track: list, t: int) -> Box:
    """The track's last box carried to frame `t` at its last velocity, at most one sample's step
    ahead (SORT's constant-velocity idea): two faces crossing keep their own ways."""
    last_t, last = track[-1]
    if len(track) < 2 or t <= last_t:
        return last
    prev_t, prev = track[-2]
    k = min(t - last_t, last_t - prev_t) / max(last_t - prev_t, 1)
    (cx, cy), (px, py) = centre(last), centre(prev)
    dx, dy = (cx - px) * k, (cy - py) * k
    return last[0] + dx, last[1] + dy, last[2] + dx, last[3] + dy


def cost(track: list, b: Box, t: int, same=None) -> float:
    """How unlike the track's face `b` at `t` is: its distance from where the track's motion carries
    it, in reaches; its size step, in SIZE_JUMPs; and, when the head check offers `like`, 1 less how
    much its head reads like the track's."""
    last = track[-1][1]
    step = abs(np.log(max(height(b), 1e-6) / max(height(last), 1e-6))) / np.log(SIZE_JUMP)
    like = getattr(same, "like", None)
    return near(predicted(track, t), b) / reach(last) + step + (1.0 - like(track, b, t) if like else 0.0)


UNFIT = 1e6


def costs(tracks: list[list], live: list[int], t: int, found: list[Box], same=None) -> np.ndarray:
    """(detections, live tracks) costs; UNFIT where the detection cannot be the track's face (fits)."""
    m = np.full((len(found), len(live)), UNFIT)
    for i, b in enumerate(found):
        for j, k in enumerate(live):
            if fits(tracks[k], b, t, same, [tracks[o] for o in live if o != k]):
                m[i, j] = cost(tracks[k], b, t, same)
    return m


def assign(tracks: list[list], live: list[int], t: int, found: list[Box], same=None) -> dict[int, int]:
    """detection index -> live track, by least total cost over the pairs that fit (the Hungarian
    assignment): a nearest-first greedy swapped two faces of near size crossing."""
    from scipy.optimize import linear_sum_assignment
    if not found or not live:
        return {}
    m = costs(tracks, live, t, found, same)
    rows, cols = linear_sum_assignment(m)
    return {int(i): live[j] for i, j in zip(rows, cols) if m[i, j] < UNFIT}


def extend(tracks: list[list], live: list[int], t: int, found: list[Box], same=None) -> list[int]:
    """Give the detections at frame `t` to the live tracks they fit (assign), the rest new tracks."""
    found = sorted(found, key=height, reverse=True)
    got, taken = assign(tracks, live, t, found, same), set()
    for i, b in enumerate(found):
        k = got.get(i)
        if k is None:
            tracks.append([])
            k = len(tracks) - 1
        tracks[k].append((t, b))
        taken.add(k)
    return sorted(taken)


def link(dets: dict[int, list[Box]], gap: int = GAP, same=None) -> list[list[tuple[int, Box]]]:
    """Detections by frame -> tracks of (frame, box); a track unseen for `gap` frames ends."""
    tracks: list[list] = []
    for t in sorted(dets):
        live = [k for k, tr in enumerate(tracks) if t - tr[-1][0] <= gap]
        extend(tracks, live, t, list(dets[t]), same)
    return tracks


def lost(track: list, every: int = EVERY) -> int:
    """Sampled frames inside the track's life where its face was not found."""
    a, b = life(track)
    return max((b - a) // every + 1 - len({t for t, _ in track}), 0)


def by_strength(found: dict, line: float) -> tuple[dict, dict]:
    """{frame: [{"box", "score"}]} -> (strong face boxes by frame, weak face boxes by frame);
    a person row (`kind: person`) is no face."""
    strong, weak = {}, {}
    for t, rows in found.items():
        faces = [r for r in rows if r.get("kind", "face") == "face"]
        strong[int(t)] = [tuple(r["box"]) for r in faces if float(r.get("score", 1.0)) >= line]
        if low := [tuple(r["box"]) for r in faces if float(r.get("score", 1.0)) < line]:
            weak[int(t)] = low
    return strong, weak


def persons_of(found: dict) -> dict[int, list[Box]]:
    """The person boxes of each frame that has any (the detector worker's `kind: person` rows)."""
    out = {int(t): [tuple(r["box"]) for r in rows if r.get("kind") == "person"] for t, rows in found.items()}
    return {t: boxes for t, boxes in out.items() if boxes}


def nearest(track: list, t: int) -> Box:
    """The track's detection nearest in time to frame `t`."""
    return min(track, key=lambda d: abs(d[0] - t))[1]


RESCUE_REACH = 1.0
RESCUE_FLOOR = 12.0
"""A weak or body face may sit at most one face height (12 px at least) from the track's nearest
face: weaker evidence, a shorter reach than a detection's 2x (ep01 T01: Enfield's body face, 70 px
below Utterson's last 46 px one, joined Utterson's track under the 2x reach)."""


def holds(track: list, b: Box, t: int, gap: int, same=None, others=()) -> bool:
    """A weak `b` at `t` continues the track: within `gap` of its life, within a face of its nearest
    face, at its size, and -- more than a sample from that face -- its own head by `same`."""
    a, z = life(track)
    t0, ref = min(track, key=lambda d: abs(d[0] - t))
    if not (a - gap <= t <= z + gap and near(ref, b) <= max(RESCUE_FLOOR, RESCUE_REACH * height(ref))
            and same_size(ref, b)):
        return False
    if abs(t - t0) <= EVERY:
        return steady(same, track, b, t)
    return same is None or bool(same(track, b, t, others))


def claimed(tracks: list[list], b: Box, t: int) -> bool:
    """Some track already holds a face at frame `t` in reach of `b`: `b` is that face."""
    return any(u == t and near(c, b) <= reach(c) for tr in tracks for u, c in tr)


def rescue(tracks: list[list], weak: dict[int, list[Box]], gap: int = GAP, same=None) -> list[list]:
    """A weak detection continues a track it fits (ByteTrack's idea): in the track's life or
    within `gap` of its ends, never a new face, never a face another track holds at that frame
    (ep01 T07: the child's two pieces); read forward, then back, so a track grows both ways."""
    for t in sorted(weak) + sorted(weak, reverse=True):
        for b in (b for b in weak[t] if not claimed(tracks, b, t)):
            options = [tr for tr in tracks if holds(sorted(tr), b, t, gap, same, [o for o in tracks if o is not tr])]
            if options:
                min(options, key=lambda tr: near(nearest(tr, t), b)).append((t, b))
    return [sorted(tr, key=lambda d: d[0]) for tr in tracks]


def keep(tracks: list[list], hits: int = MIN_HITS) -> list[list]:
    """Tracks seen often enough to be a face, not a flicker of the detector."""
    return [tr for tr in tracks if len(tr) >= hits]


def life(track: list) -> tuple[int, int]:
    return track[0][0], track[-1][0]


STITCH_GAP = 48
STITCH_FACES = 3.0
STITCH_FLOOR = 80.0


BODY_FACE = 0.100
BODY_FACE_Y = 0.125
"""A person's face from its box, by ep01's own geometry (9 round-1 takes, 509 people holding one
detected face): height 0.100 of the person's (p10-p90 0.086-0.164), centre 0.125 down from its
top, centred across it."""
BODY_ONLY_PX = 24.0
"""A track from bodies alone is a face only when it is this small: the face model reads ep01's
cel faces from about 13 px, so a bigger faceless person is turned away or cropped (T15, T18)."""
BODY_MIN_FRAMES = 24
"""...and only when it lives a second or more: ep01's two 13-frame body tracks (T07 and T08,
frames 0-12) were T07's child seen from behind and an unnamed figure."""
EDGE_PX = 2.0


def body_face(p: Box) -> Box:
    """The face box a person's box holds."""
    h = p[3] - p[1]
    cx, cy, f = (p[0] + p[2]) / 2, p[1] + BODY_FACE_Y * h, BODY_FACE * h
    return cx - f / 2, cy - f / 2, cx + f / 2, cy + f / 2


def body_faces(persons: dict[int, list[Box]], width: int, height_: int) -> dict[int, list[Box]]:
    """Each frame's people as face boxes; a person cut by the frame's top or foot gives none."""
    out = {t: [body_face(p) for p in boxes if p[1] > EDGE_PX and p[3] < height_ - EDGE_PX]
           for t, boxes in persons.items()}
    return {t: faces for t, faces in out.items() if faces}


def meets(body: list, face: list, gap: int = GAP) -> bool:
    """A face track comes near the body track somewhere in their shared time."""
    a, z = life(face)
    return any(a - gap <= t <= z + gap and near(nearest(face, t), b) <= reach(b) for t, b in body)


def body_only(bodies: dict[int, list[Box]], faces: list[list]) -> list[list]:
    """Tracks of body faces no face track ever comes near, seen MIN_HITS times, under BODY_ONLY_PX."""
    tracks = [tr for tr in keep(link(bodies)) if life(tr)[1] - life(tr)[0] + 1 >= BODY_MIN_FRAMES]
    return [tr for tr in tracks if track_px(tr) < BODY_ONLY_PX and not any(meets(tr, f) for f in faces)]


def joins(a: list, b: list, same=None, others=()) -> bool:
    """`b` picks up where `a` lost its face: after it, soon, near where it was, at its size,
    and (when `same` is given) `a`'s own head."""
    gap = b[0][0] - a[-1][0]
    room = max(STITCH_FLOOR, STITCH_FACES * height(a[-1][1]))
    if not (0 < gap <= STITCH_GAP and near(a[-1][1], b[0][1]) <= room and same_size(a[-1][1], b[0][1])):
        return False
    return same is None or bool(same(a, b[0][1], b[0][0], others))


def rivals_of(a: list, b: list, pieces: list[list]) -> list[list]:
    """The pieces that are neither `b` nor already part of `a`: the other people `b` might be."""
    held = set(a)
    return [o for o in pieces if o is not b and not set(o) <= held]


def stitch(tracks: list[list], same=None) -> list[list]:
    """Pieces of one face split by a stretch the detector missed, joined in time
    order (Jekyll ep01 T07: Hyde came back as two pieces 20 frames apart)."""
    out: list[list] = []
    for b in sorted(tracks, key=lambda tr: tr[0][0]):
        options = [a for a in out if joins(a, b, same, rivals_of(a, b, tracks))]
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


HYSTERESIS = 1.25
"""The refine switches on under SMALL_FACE_PX and off only over 1.25x it (150 px for 120):
a face that zooms past the wall never toggles the refine (VideoFaceDetailer's size gate)."""


def heights_over(track: list, frames: int) -> np.ndarray:
    """The track's face height on every frame: detections through track_px's running median,
    interpolated over the life, held at its ends."""
    at = [t for t, _ in track]
    h = running_median(np.array([height(b) for _, b in track], float), max(SIZE_SMOOTH // EVERY, 1))
    return np.interp(range(frames), at, h)


def soft_span(track: list, frames: int, on: float = 120.0, off: float | None = None) -> tuple[int, int] | None:
    """(first, last) frame of the life where the face is soft: on under `on`, off over `off`
    (on x HYSTERESIS); None when it never reads soft."""
    off, h, state, soft = off or on * HYSTERESIS, heights_over(track, frames), False, []
    a, b = life(track)
    for t in range(a, min(b, frames - 1) + 1):
        state = h[t] < on if not state else h[t] <= off
        if state:
            soft.append(t)
    return (soft[0], soft[-1]) if soft else None


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


def frozen_side(boxes: np.ndarray, span: tuple[int, int], width: int, height_: int) -> int:
    """One crop side for the run (VideoFaceDetailer's frozen crop size): the biggest smoothed
    face over the span times the margin, at least MIN_SIDE, inside the frame."""
    h = boxes[span[0]:span[1] + 1, 3] - boxes[span[0]:span[1] + 1, 1]
    return int(min(max(MIN_SIDE, float(h.max()) * MARGIN), width, height_))


def windows(boxes: np.ndarray, width: int, height_: int, side: int | None = None) -> list[tuple[int, int, int]]:
    """A square (x, y, side) per frame round the face: `side` frozen for the run, else the
    smoothed height times the margin (a push-in grows its window slowly)."""
    out = []
    for x1, y1, x2, y2 in boxes:
        s = side or min(int(max(MIN_SIDE, (y2 - y1) * MARGIN)), width, height_)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2 - 0.05 * s
        out.append((int(np.clip(cx - s / 2, 0, width - s)), int(np.clip(cy - s / 2, 0, height_ - s)), s))
    return out


def side_of(wins: list) -> int:
    """The track's common window side (the median): the gate measures every frame at it."""
    return int(np.median([s for _, _, s in wins]))


TRIM_MAX = 8
"""Frames of a life the grid may trim rather than render 17 more (two fades of face_paste.FADE),
and never more than a quarter of the life (ep01 T07's child lived 10 frames)."""


def grid_frames(count: int) -> int:
    """H3's 17k+5 count for a life of `count` frames: the one just over it, or the one under
    it when that trims at most TRIM_MAX frames and a quarter of the life (the paste's fades)."""
    up = h3.legal_frames(count)
    down = up - h3.FRAME_MODULUS
    return down if down >= h3.FRAME_REMAINDER and count - down <= min(TRIM_MAX, count // 4) else up


def shot_of(span: tuple[int, int], frames: int, cuts) -> tuple[int, int]:
    """[first, end) frames of the shot holding the span: the take cut at its hard cuts."""
    lo = max([c for c in cuts if c <= span[0]], default=0)
    hi = min([c for c in cuts if c > span[1]], default=frames)
    return lo, min(hi, frames)


def crop_span(span: tuple[int, int], frames: int, cuts=()) -> tuple[int, int]:
    """(first frame, count) of the crop clip: the life on H3's frame grid, inside its shot,
    a trim split between both ends of the life."""
    lo, hi = shot_of(span, frames, cuts)
    n = grid_frames(span[1] - span[0] + 1)
    while n > hi - lo and n > h3.FRAME_REMAINDER:
        n -= h3.FRAME_MODULUS
    first = span[0] + max(0, (span[1] - span[0] + 1 - n) // 2)
    return max(lo, min(first, hi - n)), n


def head_box(b: Box, width: int, height_: int) -> Box:
    """The face box widened to the head and hat: what tells two people apart at 30 px."""
    h = height(b)
    x1, x2 = b[0] - 0.25 * h, b[2] + 0.25 * h
    y1, y2 = b[1] - 0.8 * h, b[3] + 0.1 * h
    return max(0.0, x1), max(0.0, y1), min(float(width), x2), min(float(height_), y2)


def lab_hist(img: np.ndarray) -> np.ndarray:
    """An RGB crop's normalised Lab colour histogram (8 x 6 x 6 bins), flattened."""
    import cv2
    lab = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_RGB2LAB)
    h = cv2.calcHist([lab], [0, 1, 2], None, [8, 6, 6], [0, 256, 0, 256, 0, 256])
    return cv2.normalize(h, h).flatten()


def hist_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation of two lab_hist histograms, -1..1."""
    import cv2
    return float(cv2.compareHist(a, b, cv2.HISTCMP_CORREL))


def hist_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Lab colour histogram correlation of two RGB crops, -1..1.  Lab, not hue: a
    black hat has no hue, and Hyde's black wideawake is what tells him from
    Enfield's light-brown top hat at 30 px (Jekyll ep01 T07: 0.77 against 0.08).  An empty crop (a big
    face's head box past the frame edge) is no evidence: 0.0, never an OpenCV refusal (2026-10-29)."""
    if not np.asarray(a).size or not np.asarray(b).size:
        return 0.0
    return hist_correlation(lab_hist(a), lab_hist(b))


def loose_detector(device: str = "cpu"):
    """MTCNN loosened for 25-40 px faces (F2's tracker): rgb -> [{"box", "score"}]."""
    from facenet_pytorch import MTCNN
    from PIL import Image
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=12, thresholds=[0.5, 0.6, 0.6])

    def detect(rgb: np.ndarray) -> list[dict]:
        boxes, probs = mtcnn.detect(Image.fromarray(rgb))
        return [] if boxes is None else [{"box": [float(v) for v in b], "score": float(p)} for b, p in zip(boxes, probs)]
    return detect
