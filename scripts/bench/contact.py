#!/usr/bin/env python
"""Same-shot contact sheet: one row per arm, frames at fixed shares of the take, labelled.

    uv run --no-sync python scripts/bench/contact.py <out.png> <label>=<video> ...
    uv run --no-sync python scripts/bench/contact.py faces <out.jpg> <label>=<video> ...   (first = control)

The FACE sheet (R2_verdict §2.4) is the owner's deliverable: every readable face
of the control at 8/50/92 %, cut from every arm by the same share-of-frame box
and shown at one size, arms side by side.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.bench.rulers import frames  # noqa: E402

SHARES = (0.08, 0.5, 0.92)
CELL = 384
LABEL_W = 200
FACE = 256
MIN_FACE = 0.06
"""A face box under 6 % of the frame height is unreadable at any arm: not shown."""
PAD = 1.6


def sheet(rows: list[tuple[str, Path]], shares=SHARES) -> Image.Image:
    out = Image.new("RGB", (LABEL_W + CELL * len(shares), CELL * len(rows)), (15, 16, 18))
    d = ImageDraw.Draw(out)
    for r, (label, video) in enumerate(rows):
        d.text((8, r * CELL + 8), label, fill=(230, 230, 230))
        for c, rgb in enumerate(frames(video, shares)):
            out.paste(Image.fromarray(rgb).resize((CELL, CELL)), (LABEL_W + c * CELL, r * CELL))
    return out


def face_boxes(rgb: np.ndarray, detect) -> list[tuple[float, float, float, float]]:
    """Each readable face as a square box in shares of the frame, padded, clipped."""
    h, w = rgb.shape[:2]
    out = []
    for f in detect(rgb) or []:
        x1, y1, x2, y2 = f["box"]
        if (y2 - y1) / h < MIN_FACE:
            continue
        half = PAD * max(x2 - x1, y2 - y1) / 2 / h
        cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
        half = min(half, cy, 1 - cy, cx * w / h, (1 - cx) * w / h)
        out.append((cx - half * h / w, cy - half, cx + half * h / w, cy + half))
    return out


def crop(rgb: np.ndarray, box) -> np.ndarray:
    h, w = rgb.shape[:2]
    x1, y1, x2, y2 = box
    return rgb[int(round(y1 * h)):int(round(y2 * h)), int(round(x1 * w)):int(round(x2 * w))]


def face_columns(control: list[np.ndarray], detect) -> list[tuple[int, tuple]]:
    """(frame index, box) for every readable face of the control take."""
    return [(k, b) for k, rgb in enumerate(control) for b in face_boxes(rgb, detect)]


def face_sheet(rows: list[tuple[str, Path]], detect, read=frames, shares=SHARES):
    """Rows = arms (the first is the control), columns = its faces; None when it shows none."""
    takes = [read(v, shares) for _, v in rows]
    cols = face_columns(takes[0], detect)
    if not cols:
        return None
    out = Image.new("RGB", (LABEL_W + FACE * len(cols), FACE * len(rows)), (15, 16, 18))
    d = ImageDraw.Draw(out)
    for r, ((label, _), got) in enumerate(zip(rows, takes)):
        d.text((8, r * FACE + 8), label, fill=(230, 230, 230))
        for c, (k, box) in enumerate(cols):
            if k < len(got):
                out.paste(Image.fromarray(crop(got[k], box)).resize((FACE, FACE), Image.LANCZOS),
                          (LABEL_W + c * FACE, r * FACE))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "faces":
        from scripts.bench.rulers import detector
        pairs = [a.split("=", 1) for a in sys.argv[3:]]
        img = face_sheet([(l, Path(v)) for l, v in pairs], detector())
        print("no readable face" if img is None else img.save(sys.argv[2], quality=92) or sys.argv[2])
    else:
        pairs = [a.split("=", 1) for a in sys.argv[2:]]
        sheet([(l, Path(v)) for l, v in pairs]).save(sys.argv[1])
