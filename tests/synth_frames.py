"""Frame sequences drawn in numpy for the take measures: no video, no asset.

A `picture` has structure (hard-edged rectangles and discs plus grain) so every
window of it has something to match on; the block-noise `pan` is what the lock
tests have used since the held row was built.  Everything is deterministic.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

SIZE = 256


def picture(seed: int, size: int = SIZE) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    img = np.full((size, size), rng.uniform(40, 200))
    for _ in range(60):
        cx, cy = rng.uniform(0, size, 2)
        w, h, tone = rng.uniform(size / 20, size / 4), rng.uniform(size / 20, size / 4), rng.uniform(0, 255)
        if rng.uniform() < 0.5:
            img[(np.abs(x - cx) < w / 2) & (np.abs(y - cy) < h / 2)] = tone
        else:
            img[((x - cx) ** 2 + (y - cy) ** 2) < (w / 2) ** 2] = tone
    return np.clip(img + rng.normal(0, 3, img.shape), 0, 255).astype(np.uint8)


def rgb(grey: np.ndarray) -> np.ndarray:
    return np.repeat(grey[:, :, None], 3, axis=2)


def pan(n: int = 24, shift: int = 5, size: int = SIZE, seed: int = 3) -> list[np.ndarray]:
    """RGB frames of a block-textured set sliding left `shift` px per frame."""
    rng = np.random.default_rng(seed)
    wide = (rng.random((size, size + n * shift)) * 255).astype(np.uint8)
    wide = np.repeat(np.repeat(wide[::8, ::8], 8, 0), 8, 1)[:size, :size + n * shift]
    return [rgb(wide[:, i * shift:i * shift + size].copy()) for i in range(n)]


def patch(seed: int = 9, size: int = 40) -> np.ndarray:
    face = (np.random.default_rng(seed).random((size, size)) * 255).astype(np.uint8)
    return np.repeat(np.repeat(face[::4, ::4], 4, 0), 4, 1)


def pin_person(frames: list[np.ndarray], y0: int = 82, x0: int = 108) -> list[np.ndarray]:
    """A textured face held at one screen place while the set runs on under
    it: the fault as rendered, the rails drawn through the man's body."""
    face = patch(9, 40)
    for f in frames:
        f[y0:y0 + 40, x0:x0 + 40] = face[:, :, None]
    return frames


def fixed_face(frames) -> dict[int, dict]:
    return {i: {"cx": 0.5, "cy": 0.4, "h": 0.12} for i in range(0, len(frames), 6)}


def rotate(pic: np.ndarray, n: int, step_deg: float) -> np.ndarray:
    """Grey frames of `pic` turning `step_deg` a frame about its centre."""
    im = Image.fromarray(pic)
    return np.stack([np.asarray(im.rotate(k * step_deg, resample=Image.BILINEAR)) for k in range(n)])


def hold(pic: np.ndarray, n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.clip(pic[None].astype(np.int16) + rng.integers(-2, 3, (n, *pic.shape)), 0, 255).astype(np.uint8)


def thumb_embed(image: np.ndarray, size: int = 16) -> np.ndarray:
    """A stand-in for a patch embedder: a zero-mean 16x16 grey thumbnail, unit norm."""
    im = Image.fromarray(image if image.ndim == 2 else image[..., 0]).convert("L").resize((size, size))
    a = np.asarray(im, dtype=float).ravel()
    a = a - a.mean()
    return a / (np.linalg.norm(a) + 1e-9)
