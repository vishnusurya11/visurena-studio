"""Paste the kept refined face crops into the master, AFTER the 4x upscale, at master
scale (owner 2026-10-17; F2, docs/audit/2026-10-16_model_tests: pasted into the 768
take the new detail is averaged away again).

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


@dataclass(frozen=True)
class Track:
    windows: list            # (x, y, side) per take frame, at take scale
    life: tuple[int, int]    # first and last take frame the face is seen
    start: int               # the take frame the refined crop's frame 0 is
    crop: str                # the refined crop video


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
            blend(out, patch, x, y, feather(s, max(4, round(s * FEATHER_SHARE))), alpha)

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


def kept_tracks(entry: dict, room: Path) -> tuple:
    """The Track of every person the gate kept in one take's refine entry."""
    out = []
    for p in entry.get("people", []):
        if p.get("kept"):
            doc = json.loads((Path(room) / p["track"]).read_text(encoding="utf-8"))
            out.append(Track([tuple(w) for w in doc["windows"]], tuple(doc["life"]), int(doc["start"]),
                             str(Path(room) / p["crop"])))
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
