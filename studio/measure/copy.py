"""Is this picture a staged input handed back?  pHash first, SSIM to corroborate.

A place reference returned unchanged as an insert passed every gate, because no
gate compared an output with the bytes that were staged; `take_currency`
knows the staged names, and this reads their pixels.  pHash: grey, 32x32, DCT,
the top-left 8x8 against its median, 64 bits.  Hamming 0-5 is the same picture
re-saved, 6-10 the same content edited, unrelated pictures sit at 25-35.  A
crop hashes further off, so SSIM against the reference and its centre crops
corroborates within PHASH_NEAR.  `edit_gate.frame_diff` is the same idea at
frame scale; this one survives a re-encode and a crop.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

PHASH_COPY = 10
"""Hamming distance at or under which a picture IS a staged input."""
PHASH_NEAR = 14
"""Within this, SSIM at SSIM_COPY or more still says copy (a crop, a re-grade)."""
SSIM_COPY = 0.6
HASH_SIDE, SSIM_SIDE = 32, 256
CROPS = (1.0, 0.8, 0.6)
"""The reference whole and its centre crops: a panel may be a crop of it."""


def _image(picture) -> Image.Image:
    if isinstance(picture, Image.Image):
        return picture.convert("RGB")
    if isinstance(picture, np.ndarray):
        return Image.fromarray(picture).convert("RGB")
    return Image.open(picture).convert("RGB")


def grey(picture, side: int) -> np.ndarray:
    """The picture as a float grey square of `side`."""
    return np.asarray(_image(picture).convert("L").resize((side, side), Image.LANCZOS), dtype=np.float32)


def phash(picture) -> int:
    d = cv2.dct(grey(picture, HASH_SIDE))[:8, :8]
    bits = (d > np.median(d)).ravel()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def ssim(a: np.ndarray, b: np.ndarray) -> float:
    """Mean structural similarity, Gaussian window 11 / sigma 1.5, grey 0-255."""
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2

    def blur(x):
        return cv2.GaussianBlur(x, (11, 11), 1.5)
    mu_a, mu_b = blur(a), blur(b)
    va, vb = blur(a * a) - mu_a ** 2, blur(b * b) - mu_b ** 2
    cov = blur(a * b) - mu_a * mu_b
    num = (2 * mu_a * mu_b + c1) * (2 * cov + c2)
    den = (mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2)
    return float((num / den).mean())


def centre_crop(picture, scale: float) -> Image.Image:
    im = _image(picture)
    w, h = im.size
    cw, ch = w * scale, h * scale
    return im.crop((round((w - cw) / 2), round((h - ch) / 2), round((w + cw) / 2), round((h + ch) / 2)))


def compare(panel, ref) -> dict:
    """{"phash": hamming, "ssim": best over the reference and its centre crops}."""
    p, r = _image(panel), _image(ref)
    pg = grey(p, SSIM_SIDE)
    best = max(ssim(pg, grey(centre_crop(r, s), SSIM_SIDE)) for s in CROPS)
    return {"phash": hamming(phash(p), phash(r)), "ssim": round(best, 3)}


def is_copy(row: dict) -> bool:
    return row["phash"] <= PHASH_COPY or (row["ssim"] >= SSIM_COPY and row["phash"] <= PHASH_NEAR)


def against(panel, refs: list) -> dict | None:
    """The staged input this panel is closest to, and whether it is a copy of it."""
    rows = [{"path": str(ref), **compare(panel, ref)} for ref in refs]
    if not rows:
        return None
    best = min(rows, key=lambda r: (r["phash"], -r["ssim"]))
    return {**best, "copy": is_copy(best)}


def staged_paths(take: Path, root: Path | None = None) -> list[Path]:
    """The pictures this take's graph loaded, as files in ComfyUI's input dir."""
    from studio import comfy, take_currency
    base = Path(root) if root is not None else comfy.COMFY_ROOT
    return [p for p in (base / "input" / name for name in sorted(take_currency.staged_images(Path(take))))
            if p.exists()]
