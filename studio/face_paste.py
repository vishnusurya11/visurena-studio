"""Paste the kept refined face crops into the cut-scale frames, BEFORE the one upscale
(owner 2026-10-18, commit 24caaeb: the paste runs on the decoded frames, then the denoise and
the 4x; after the upscale only audio is muxed).  Earlier text (owner 2026-10-17) pasted AFTER
the 4x, on the F2 evidence that detail pasted into a 768 take averaged away; that order is
retired and the detail is re-measured by tests/test_face_refine_pastes_at_cut_scale.py.

The geometry follows the cut exactly as assemble made it (`work_r2v/layout.json`):
the take's head trim, a G-DEAD slow-down, the gutter guard's crop and its scale back
to the canvas, then the upscale factor.  `Paster` wraps the upscaler frame by frame
inside `master_upscale.streamed`, so the paste costs no extra encode; a cut with
nothing kept is the upscale untouched, byte for byte.

Only the face core is pasted (face-warp fix, owner 2026-10-19: "the face fix and eye fix is warping
the video around"): outside a brow-to-chin, cheek-to-cheek outline round the tracked face every pixel is
the take's (hat, brim, hair, ears, jaw, collar); each redraw frame is first put back on the take's head
(head_shift: H3's redraw jitters 2-3 px at 384), and in the feather the take's low frequencies replace
the redraw's (docs/calibration/face_refine.md, the replays).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

FADE = 4
"""Frames over which a track's paste fades in and out at the ends of its life."""
FEATHER_SHARE = 0.083
"""Feather width as a share of the pasted side (F2 at master scale: 24 px of 288)."""
SOFT_PX = 40.0
"""A face under this many take pixels has its window floored at face_track.MIN_SIDE (96 / 2.4 = 40):
logged as `soft` on its track.  Since the face-warp fix (2026-10-19) it is pasted by the same face-core
rule as any face, scaled to its size."""
CORE_HALF = (0.35, 0.34, 0.34)
"""The face core pasted from the redraw, in face heights from the face box's centre (across, up, down):
brow to chin, cheek to cheek, never the hat brim, the hair, the ears, the jaw or the collar.  Everything
outside it is the take's own pixels: the square paste let H3's redraw of hat, hair, collar and background
replace the take's, 1-4 px off and wandering (docs/audit/2026-10-19_face_warp/audit_our_paste.md;
ComfyUI-H3-FaceRefine, Carasibana, MIT, pastes `face_only` by default).  Round 1 (722050e) used these
numbers as 0.55 x 0.65 radii, an outline 1.1 x 1.3 face heights across that took in the brim, the hair,
the ears and the jaw (the skeptic's overlay); drawn over all 14 kept ep01 tracks, this one runs under
the brim, inside the hair and above the collar (docs/calibration/face_refine.md, round 2 of the fix)."""
CORE_POWER = (4.0, 2.0)
"""The outline's power above and below the face's centre: square-shouldered over the eyes (a
superellipse; face_yolov8m puts them at -0.23 to -0.15 face heights, out to +-0.22), round under the chin."""
CORE_FEATHER = 0.08
"""The feather, in face heights, lies INSIDE the core's outline: the mask is exactly 0 at and beyond it.
Thin, so the eyes are the redraw's whole and the brim is the take's whole; the edge lock (band_lock)
takes the tone step out of it."""
FACE_Y = 0.55
"""Where face_track.windows puts the face's centre: half the side across, 0.55 of it down."""
LOW_SIGMA = 0.08
"""The edge lock's low-pass, in face heights: where the mask falls, the take's tone below it and the
redraw's ink lines above it (the replay: the outline's low-frequency step 1.1-3.8 -> 0.7-2.6 levels,
the eye band's lines within 0.4 of the plain core paste)."""

REG_SIDE = 384
"""The head shift is read at most this many pixels across (the replay's scale; Farneback's window 21)."""
REG_RING = (1.0, 1.8)
"""The ring the head shift is read on, in core radii: hat brim, hair, ears, drawn by take and redraw alike."""
SHIFT_MAX = 0.06
"""The most the redraw is moved onto the take's head, in face heights.  The ep01 replay: H3's redraws sit
0.7-2.9 px at 384 off the take's head, std 0.8-3.9 frame to frame (0.005-0.03 face heights); the shift
takes the face-vs-head shear 2.7 -> 0.9 (T18), 2.7 -> 1.1 (T08).  A turned head is not a jitter."""


@dataclass(frozen=True)
class Track:
    windows: list            # (x, y, side) per take frame, at take scale
    life: tuple[int, int]    # first and last take frame the face is seen
    start: int               # the take frame the refined crop's frame 0 is
    crop: str                # the refined crop video
    face: float | None = None  # the face's height as a share of its window (median); None = 1 / MARGIN
    faces: tuple | None = None  # per take frame (x, y, height) of the face as shares of its window, or None


@dataclass(frozen=True)
class Span:
    index: int               # the take
    start: int               # the master frame its segment starts on
    frames: int              # the segment's frames in the master
    head: int                # take frames trimmed from its head
    slow: float              # G-DEAD's stretch (1.0 = none)
    guard: tuple | None      # the gutter guard's crop (w, h, left, top), or None
    tracks: tuple


def parse_guard(said: str | None) -> tuple[int, int, int, int] | None:
    """`crop=w:h:l:t` -> (w, h, l, t); no crop -> None."""
    found = re.search(r"crop=(\d+):(\d+):(\d+):(\d+)", said or "")
    return tuple(int(v) for v in found.groups()) if found else None


def box_at(win, guard, width: int, height: int, factor: int) -> tuple[float, float, float]:
    """A take-scale window (x, y, side) in master pixels, unrounded: through the guard's crop,
    its scale back up to the canvas (centre-cropped), then the upscale."""
    x, y, side = win
    cw, ch, left, top = guard or (width, height, 0, 0)
    s = max(width / cw, height / ch)
    ox, oy = (cw * s - width) / 2, (ch * s - height) / 2
    return ((x - left) * s - ox) * factor, ((y - top) * s - oy) * factor, side * s * factor


def to_master(win, guard, width: int, height: int, factor: int) -> tuple[int, int, int]:
    """The window in whole master pixels: where the crop is resized to and placed."""
    return tuple(round(v) for v in box_at(win, guard, width, height, factor))


def face_in_patch(face: tuple, box: tuple, placed: tuple) -> tuple[float, float, float]:
    """(cx, cy, height) of the face in the placed patch's pixels: the shares of the float box the crop was
    cut by, less the rounding of where it is placed (the mask sits on the face to the sub-pixel)."""
    (fx, fy, fh), (xf, yf, sf), (x, y, _) = face, box, placed
    return fx * sf + (xf - x), fy * sf + (yf - y), fh * sf


def face_at(track: Track, t: int) -> tuple[float, float, float]:
    """The face's (x, y, height) shares of the window on take frame t: the run's record, else the centre
    face_track.windows puts it at with the track's median height."""
    if track.faces and 0 <= t < len(track.faces) and track.faces[t]:
        return tuple(track.faces[t])
    from studio.face_track import MARGIN
    return 0.5, FACE_Y, track.face or 1 / MARGIN


def take_frame(j: int, head: int, slow: float) -> int:
    """The take frame the segment's j-th frame shows."""
    return head + int(j / slow)


def fade(t: int, life: tuple[int, int], n: int = FADE) -> float:
    """1 inside a track's life, ramping over `n` frames at each end, 0 outside."""
    if t < life[0] or t > life[1]:
        return 0.0
    return min(1.0, (t - life[0] + 1) / n, (life[1] - t + 1) / n)


def feather(side: int, f: int) -> np.ndarray:
    """(side, side, 1) float mask: 1 inside, falling to 0 over `f` px at the edge."""
    import cv2
    m = np.zeros((side, side), np.float32)
    if side > 2 * f:
        m[f:-f, f:-f] = 1.0
    return cv2.GaussianBlur(m, (0, 0), max(f / 2, 0.5))[..., None]


def soft(face_px: float | None) -> bool:
    """A face whose window is floored (SOFT_PX); logged on its track."""
    return face_px is not None and face_px < SOFT_PX


def core_radius(side: int, face: float, centre: tuple | None = None) -> np.ndarray:
    """Every pixel's radius from the face's centre, 1 on the face core's outline (CORE_HALF face heights,
    CORE_POWER above and below); `centre` (cx, cy) in pixels, else where face_track.windows puts the face."""
    cx, cy = centre or (side / 2, FACE_Y * side)
    yy, xx = np.mgrid[0:side, 0:side].astype(np.float32) + 0.5
    up = yy < cy
    f = max(face, 1e-6)
    n = np.where(up, *CORE_POWER).astype(np.float32)
    dy = np.abs(yy - cy) / (np.where(up, CORE_HALF[1], CORE_HALF[2]) * f)
    return ((np.abs(xx - cx) / (CORE_HALF[0] * f)) ** n + dy ** n) ** (1.0 / n)


def core_mask(side: int, face: float, centre: tuple | None = None) -> np.ndarray:
    """(side, side, 1) float: 1 on the face, a smoothstep down to exactly 0 at the core's outline;
    the feather (CORE_FEATHER face heights) lies inside it."""
    width = CORE_FEATHER / float(np.mean(CORE_HALF))
    t = np.clip((1.0 - core_radius(side, face, centre)) / width, 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t))[..., None].astype(np.float32)


def paste_mask(side: int, face: float | None = None, centre: tuple | None = None) -> np.ndarray:
    """The mask a crop of `side` px is pasted through: the face core round a face `face` px high
    (an old track with no face size: the margin's, side / 2.4), for a small face and a big one alike."""
    from studio.face_track import MARGIN
    return core_mask(side, face or side / MARGIN, centre)


def band_lock(patch: np.ndarray, take: np.ndarray, mask: np.ndarray, face: float) -> np.ndarray:
    """The redraw with the take's low frequencies where the mask falls (weight 1 - m): no tone step at
    the face's outline, the redraw's ink lines kept.  No registration, no global tone shift: replayed,
    a similarity warp blurred the drawn eyes and a per-frame Lab match flickered."""
    import cv2
    p, t = patch.astype(np.float32), take.astype(np.float32)
    sigma = max(1.0, LOW_SIGMA * face)
    low = cv2.GaussianBlur(t, (0, 0), sigma) - cv2.GaussianBlur(p, (0, 0), sigma)
    return np.clip(p + (1.0 - mask) * low, 0, 255).astype(np.uint8)


def under(frame: np.ndarray, x: int, y: int, patch: np.ndarray) -> np.ndarray:
    """The frame's pixels under a patch placed at (x, y); where it hangs off the frame, the patch's own."""
    h, w = frame.shape[:2]
    s = patch.shape[0]
    out = patch.copy()
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + s, w), min(y + s, h)
    if x0 < x1 and y0 < y1:
        out[y0 - y:y1 - y, x0 - x:x1 - x] = frame[y0:y1, x0:x1]
    return out


def blend(frame: np.ndarray, patch: np.ndarray, x: int, y: int, mask: np.ndarray, alpha: float) -> None:
    """Patch over frame at (x, y) through mask x alpha, in place, clipped to the frame."""
    h, w = frame.shape[:2]
    s = patch.shape[0]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + s, w), min(y + s, h)
    if x0 >= x1 or y0 >= y1:
        return
    p = patch[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    m = mask[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
    region = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = np.rint(p * m + region * (1 - m)).clip(0, 255).astype(np.uint8)   # rounded, not cut


def head_shift(patch: np.ndarray, take: np.ndarray, face: float, centre: tuple | None) -> tuple[float, float]:
    """Where the redraw's head sits against the take's on this frame (patch pixels): the median flow take ->
    redraw on the REG_RING round the face core, held to SHIFT_MAX face heights."""
    import cv2
    s = patch.shape[0]
    n = min(s, REG_SIDE)
    k = n / s
    g = [cv2.cvtColor(cv2.resize(np.ascontiguousarray(f), (n, n), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
         for f in (take, patch)]
    flow = cv2.calcOpticalFlowFarneback(g[0], g[1], None, 0.5, 4, 21, 3, 5, 1.1, 0)
    r = core_radius(n, face * k, None if centre is None else (centre[0] * k, centre[1] * k))
    ring = (r >= REG_RING[0]) & (r <= REG_RING[1])
    d = np.median(flow[ring], axis=0) / k if ring.any() else np.zeros(2)
    most, size = SHIFT_MAX * face, float(np.hypot(*d))
    return tuple(float(v) for v in (d * most / size if size > most else d))


def shifted(patch: np.ndarray, d: tuple[float, float]) -> np.ndarray:
    """The patch moved back by `d` (its content at x + d now at x), cubic, edges reflected."""
    import cv2
    m = np.float32([[1, 0, -d[0]], [0, 1, -d[1]]])
    return cv2.warpAffine(np.ascontiguousarray(patch), m, patch.shape[1::-1], flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REFLECT)


def paste_patch(out: np.ndarray, patch: np.ndarray, x: int, y: int, face: float, centre: tuple | None,
                alpha: float = 1.0) -> None:
    """A redrawn patch over `out` at (x, y), in place: put back on the take's head (head_shift), the face
    core only, edge-locked.  The Paster and the gate (studio/face_gate.pasted_of) both paste through it,
    so the gate reads the paste that ships."""
    take = under(out, x, y, patch)
    patch = shifted(patch, head_shift(patch, take, face, centre))
    mask = paste_mask(patch.shape[0], face, centre)
    blend(out, band_lock(patch, take, mask, face), x, y, mask, alpha)


def ring_diff(src: np.ndarray, ref: np.ndarray, f: int) -> float:
    """Mean level difference in the outer band of width `f`: where a seam would show."""
    band = np.ones(src.shape[:2], bool)
    band[f:-f, f:-f] = False
    return float(np.abs(src.astype(np.float32) - ref.astype(np.float32))[band].mean())


def region_flicker(frames: list[np.ndarray]) -> float:
    """Mean frame-to-frame level change of the central half (the face)."""
    if len(frames) < 2:
        return 0.0
    h, w = frames[0].shape[:2]
    core = [f[h // 4:h - h // 4, w // 4:w - w // 4].astype(np.float32) for f in frames]
    return float(np.mean([np.abs(b - a).mean() for a, b in zip(core, core[1:])]))


class CropReader:
    """A refined crop's frames, read forward (the cut plays a take forward)."""

    def __init__(self, path):
        import cv2
        self.cap, self.at, self.last = cv2.VideoCapture(str(path)), -1, None

    def frame(self, k: int) -> np.ndarray | None:
        while self.at < k:
            ok, bgr = self.cap.read()
            if not ok:
                return self.last
            self.at, self.last = self.at + 1, bgr[:, :, ::-1]
        return self.last


class Paster:
    """upscaler(frame) then every kept crop of the master frame pasted at master scale."""

    def __init__(self, upscaler: Callable, spans: list[Span], width: int, height: int, factor: int,
                 open_crop: Callable = CropReader):
        self.up, self.spans, self.size, self.factor = upscaler, spans, (width, height), factor
        self.open_crop, self.readers, self.n = open_crop, {}, 0

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        out = self.up(frame)
        span = next((s for s in self.spans if s.start <= self.n < s.start + s.frames), None)
        if span is not None:
            out = np.array(out, copy=True)
            self.paste(out, span, take_frame(self.n - span.start, span.head, span.slow))
        self.n += 1
        return out

    def paste(self, out: np.ndarray, span: Span, t: int) -> None:
        for track in span.tracks:
            alpha, k = fade(t, track.life), t - track.start
            patch = self.reader(track.crop).frame(k) if alpha > 0 and 0 <= t < len(track.windows) else None
            if patch is not None:
                self.paste_one(out, span, track, t, patch, alpha)

    def paste_one(self, out: np.ndarray, span: Span, track: Track, t: int, patch: np.ndarray, alpha: float) -> None:
        """One crop frame: resized to the window the crop was cut by, the face core only, edge-locked."""
        import cv2
        box = box_at(track.windows[t], span.guard, *self.size, self.factor)
        x, y, s = placed = to_master(track.windows[t], span.guard, *self.size, self.factor)
        patch = cv2.resize(np.ascontiguousarray(patch), (s, s), interpolation=cv2.INTER_AREA)
        cx, cy, face = face_in_patch(face_at(track, t), box, placed)
        paste_patch(out, patch, x, y, face, (cx, cy), alpha)

    def reader(self, crop: str):
        if crop not in self.readers:
            self.readers[crop] = self.open_crop(crop)
        return self.readers[crop]

    def close(self) -> None:
        closer = getattr(self.up, "close", None)
        if closer:
            closer()


def sha8(path: Path) -> str:
    """A take's identity: the first eight hex digits of its sha256 (step 09's rule)."""
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8] if Path(path).exists() else ""


def face_share(doc: dict, row: dict | None = None) -> float | None:
    """A track's median face height over its frozen side; a track file written without them reads its
    refine.json row's face_px over the window's side (ep01: T06's 13.5 px Hyde in a 96 window read as the
    margin's 1 / 2.4 was pasted through a core three times his face); None when neither kept it."""
    if doc.get("face_px") and doc.get("side"):
        return float(doc["face_px"]) / float(doc["side"])
    if (row or {}).get("face_px") and doc.get("windows"):
        return float(row["face_px"]) / float(doc["windows"][int((doc.get("life") or [0])[0])][2])
    return None


def faces_of(doc: dict) -> tuple | None:
    """The run's per-frame face (x, y, height) shares, or None for a track written before they were kept."""
    rows = doc.get("faces")
    return tuple(tuple(float(v) for v in r) if r else None for r in rows) if rows else None


def kept_tracks(entry: dict, room: Path) -> tuple:
    """The Track of every person the gate kept in one take's refine entry."""
    out = []
    for p in entry.get("people", []):
        if p.get("kept"):
            doc = json.loads((Path(room) / p["track"]).read_text(encoding="utf-8"))
            out.append(Track([tuple(w) for w in doc["windows"]], tuple(doc["life"]), int(doc["start"]),
                             str(Path(room) / p["crop"]), face_share(doc, p), faces_of(doc)))
    return tuple(out)


def spans_from(rows: list[dict], seg_frames: dict[int, int], guards: dict, room: Path,
               sha_of: Callable[[int], str], fps: int) -> list[Span]:
    """Where each kept, CURRENT refine sits in the cut: `rows` is layout.json in cut
    order, `seg_frames` each segment's measured frames, `guards` gutter.json."""
    path = Path(room) / "refine.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    out, at = [], 0
    for r in rows:
        i, entry = int(r["index"]), doc.get(f"T{int(r['index']):02d}") or {}
        if not r.get("still") and entry.get("take_sha8") == sha_of(i) and (tracks := kept_tracks(entry, room)):
            out.append(Span(i, at, seg_frames[i], round(float(r.get("head") or 0) * fps), float(r.get("slow") or 1.0),
                            parse_guard(guards.get(i) or guards.get(str(i))), tracks))
        at += seg_frames[i]
    return out
