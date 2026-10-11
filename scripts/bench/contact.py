#!/usr/bin/env python
"""Same-shot contact sheet: one row per arm, frames at fixed shares of the take, labelled.

    uv run --no-sync python scripts/bench/contact.py <out.png> <label>=<video> ...
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.bench.rulers import frames  # noqa: E402

SHARES = (0.08, 0.5, 0.92)
CELL = 384
LABEL_W = 200


def sheet(rows: list[tuple[str, Path]], shares=SHARES) -> Image.Image:
    out = Image.new("RGB", (LABEL_W + CELL * len(shares), CELL * len(rows)), (15, 16, 18))
    d = ImageDraw.Draw(out)
    for r, (label, video) in enumerate(rows):
        d.text((8, r * CELL + 8), label, fill=(230, 230, 230))
        for c, rgb in enumerate(frames(video, shares)):
            out.paste(Image.fromarray(rgb).resize((CELL, CELL)), (LABEL_W + c * CELL, r * CELL))
    return out


if __name__ == "__main__":
    pairs = [a.split("=", 1) for a in sys.argv[2:]]
    sheet([(l, Path(v)) for l, v in pairs]).save(sys.argv[1])
