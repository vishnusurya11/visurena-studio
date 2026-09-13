"""Which storyboard cell does a rendered frame look like?  A crude, honest
judge: both images to a 48x84 grey thumbnail, zero-mean, cosine similarity.
It cannot tell faces apart, but it tells a frontal close-up from two backs
in a corridor, which is the question of the day (2026-09-10).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

SIZE = (48, 84)


def signature(image: Image.Image) -> np.ndarray:
    a = np.asarray(image.convert("L").resize(SIZE), dtype=float)
    a = a - a.mean()
    return a / (np.linalg.norm(a) + 1e-9)


def similarity(a: Image.Image, b: Image.Image) -> float:
    return float((signature(a) * signature(b)).sum())


def closest(frame: Image.Image, cells: dict[str, Image.Image]) -> tuple[str, float]:
    scored = {name: similarity(frame, cell) for name, cell in cells.items()}
    best = max(scored, key=scored.get)
    return best, round(scored[best], 3)


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")
