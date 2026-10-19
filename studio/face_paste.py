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
"""A face under this many take pixels is pasted through the soft head mask: its window is floored
at face_track.MIN_SIDE (96 / 2.4 = 40), so it holds more background than its margin, and the H3
redraw repaints that background (round 1: T01's shop panes became brick, T07's railing went;
docs/audit/2026-10-19_face_blur/bench).  The community recipe: a soft feathered mask, no
sharpening before the paste."""
HEAD_RADII = (0.7, 1.0)
"""The head the soft mask keeps whole, in face heights (x, y): face, hair and hat crown."""
HEAD_LIFT = 0.15
"""The head's centre sits this many face heights above the face's (the hat)."""
SOFT_OUT = 1.8
"""The soft mask falls from 1 at the head's edge to 0 at 1.8 head radii (smoothstep)."""


@dataclass(frozen=True)
class Track:
    windows: list            # (x, y, side) per take frame, at take scale
    life: tuple[int, int]    # first and last take frame the face is seen
    start: int               # the take frame the refined crop's frame 0 is
    crop: str                # the refined crop video
    face: float | None = None  # a soft track's face height as a share of its window; None = the feather


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


def to_master(win, guard, width: int, height: int, factor: int) -> tuple[int, int, int]:
    """A take-scale window (x, y, side) in master pixels: through the guard's crop,
    its scale back up to the canvas (centre-cropped), then the upscale."""
    x, y, side = win
    cw, ch, left, top = guard or (width, height, 0, 0)
    s = max(width / cw, height / ch)
    ox, oy = (cw * s - width) / 2, (ch * s - height) / 2
    return round(((x - left) * s - ox) * factor), round(((y - top) * s - oy) * factor), round(side * s * factor)


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
    """A face pasted through the soft head mask (SOFT_PX)."""
    return face_px is not None and face_px < SOFT_PX


def head_shape(side: int, face: float) -> tuple[float, float, float, float]:
    """(cx, cy, rx, ry) of the head in a window of `side` holding a face `face` px high: the face
    sits at 0.55 of the side (studio/face_track.windows), the head's centre HEAD_LIFT above it."""
    return side / 2, 0.55 * side - HEAD_LIFT * face, HEAD_RADII[0] * face, HEAD_RADII[1] * face


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
    return (m * feather(side, max(4, round(side * FEATHER_SHARE)))).astype(np.float32)


def paste_mask(side: int, face: float | None) -> np.ndarray:
    """The mask a crop of `side` px is pasted through: the soft head mask for a soft track's face
    (`face` px high at this side), else the feather."""
    return soft_mask(side, face) if face else feather(side, max(4, round(side * FEATHER_SHARE)))


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
    frame[y0:y1, x0:x1] = (p * m + region * (1 - m)).clip(0, 255).astype(np.uint8)


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
        import cv2
        for track in span.tracks:
            alpha, k = fade(t, track.life), t - track.start
            patch = self.reader(track.crop).frame(k) if alpha > 0 and 0 <= t < len(track.windows) else None
            if patch is None:
                continue
            x, y, s = to_master(track.windows[t], span.guard, *self.size, self.factor)
            patch = cv2.resize(np.ascontiguousarray(patch), (s, s), interpolation=cv2.INTER_AREA)
            blend(out, patch, x, y, paste_mask(s, track.face * s if track.face else None), alpha)

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


def face_share(doc: dict) -> float | None:
    """A soft track's face height over its frozen side; None (the feather) for a hard or old one."""
    return float(doc["face_px"]) / float(doc["side"]) if doc.get("soft") and doc.get("side") else None


def kept_tracks(entry: dict, room: Path) -> tuple:
    """The Track of every person the gate kept in one take's refine entry."""
    out = []
    for p in entry.get("people", []):
        if p.get("kept"):
            doc = json.loads((Path(room) / p["track"]).read_text(encoding="utf-8"))
            out.append(Track([tuple(w) for w in doc["windows"]], tuple(doc["life"]), int(doc["start"]),
                             str(Path(room) / p["crop"]), face_share(doc)))
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
