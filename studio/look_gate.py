"""G-LOOK: does the picture have a black in it, and more than one hue?

MEASURED 2026-09-16 on every cell and plate of episodes 5-9
(`docs/analysis/ep08_ep09_why_worse.md`).  Global contrast (std) is the SAME
across the five episodes; what episode 8 and 9 lost is the FLOOR -- the
histogram lifted off black, so the picture reads as a print, not a projection:

    cells   p5 luma     6.7 / 12.4 / 8.5   (ep05-07)   36.0 (ep08)   23.9 (ep09)
    cells   near-black  .43 / .25 / .28                 .03           .06
    plates  p5 luma     1.7 - 4.1                       62            29

And episode 9 is ONE HUE: 71 % of its pixels orange (ep08 20 %, ep06/07 33 %).
The lamplit parlour cells (Q24_0A: luma 40, p5 ~ 0) prove the drawer still
does it when asked; the sunlit setups were never asked.

Free: PIL and numpy over files on disk.  No model, no GPU, no credit.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

P5_FLOOR = 15.0
BLACK_SHARE = 0.10
NEAR_BLACK = 25.0
"""A picture has NO BLACK FLOOR when its 5th-percentile Rec.709 luma is above
P5_FLOOR and fewer than BLACK_SHARE of its pixels are under NEAR_BLACK.  Both,
because a night street with one lamp has a low p5 by the street alone, and a
noon plate with a doorway has its tenth in shadow.

Re-measured here, medians over the cells on disk: p5 3.4 / 10.1 / 8.2 (ep05-07)
against 28.3 (ep08) and 22.5 (ep09); near-black .47 / .26 / .26 against .03 /
.06.  Pictures called no-floor: 3/32, 2/27, 1/32 in London; 33/46 and 30/44 in
Part Two.  The floor at 15 sits between London's 10.1 and Part Two's 22.5."""

SATURATED, LIT = 0.20, 0.10
"""A pixel is COLOURED when its HSV saturation is at least SATURATED and its
value at least LIT; the rest is grey and votes for no hue."""
SECTOR = 30
"""Degrees of hue in one sector: twelve sectors, orange is 15-45."""
ONE_HUE_SHARE = 0.60
"""The share of ALL pixels that are coloured and fall in the one busiest sector.
MEASURED medians over cells: ep05 0.52, ep06 0.28, ep07 0.28, ep08 0.28,
ep09 0.68.  The report's 71 % orange is this number.  (Episode 5 is high because
its cells are gaslit amber over black -- and its floor is 3.4, so the black
carries the picture; the one-hue verdict is meant for a picture with no black
to set the hue against.)"""

HUE_BINS = 24
HUE_ENTROPY_FLOOR = 1.10
"""Shannon entropy (nats) of a HUE_BINS-bin hue histogram in which every pixel
votes with its saturation times its value, so grey votes for nothing.

MEASURED medians over cells: ep06 1.37, ep07 1.50, ep08 1.23, ep09 0.91.  The
report read 1.31-1.40 for London and 0.71 for ep09 on its own histogram; this
one reproduces London's scale and puts ep09 at 0.91, so the asked-for 0.9 would
miss the one episode it was built for by a hundredth.  The floor sits in the
measured gap, 0.91 | 1.23, nearer neither side."""


def pixels(path: Path) -> np.ndarray:
    """One picture as float RGB."""
    from PIL import Image

    return np.asarray(Image.open(path).convert("RGB"), dtype=float)


def luma(rgb: np.ndarray) -> np.ndarray:
    """Rec.709 Y per pixel."""
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def hsv(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hue in degrees, saturation and value in 0-1."""
    from PIL import Image

    got = np.asarray(Image.fromarray(rgb.astype(np.uint8), "RGB").convert("HSV"), dtype=float)
    return got[..., 0] * (360.0 / 255.0), got[..., 1] / 255.0, got[..., 2] / 255.0


def black_floor(y: np.ndarray) -> tuple[float, float]:
    """(5th-percentile luma, share of pixels under NEAR_BLACK)."""
    return round(float(np.percentile(y, 5)), 2), round(float((y < NEAR_BLACK).mean()), 4)


def no_black_floor(p5: float, near_black: float) -> bool:
    return p5 > P5_FLOOR and near_black < BLACK_SHARE


def hue_entropy(h: np.ndarray, s: np.ndarray, v: np.ndarray) -> float:
    """Entropy of the saturation-weighted hue histogram; 0 for a grey picture."""
    hist, _ = np.histogram(h, bins=HUE_BINS, range=(0.0, 360.0), weights=s * v)
    if hist.sum() <= 0:
        return 0.0
    p = hist / hist.sum()
    p = p[p > 0]
    return round(float(-(p * np.log(p)).sum()), 3)


def dominant_hue(h: np.ndarray, s: np.ndarray, v: np.ndarray) -> tuple[int, float]:
    """(start of the busiest sector in degrees, its share of ALL pixels)."""
    coloured = (s >= SATURATED) & (v >= LIT)
    if not coloured.any():
        return -1, 0.0
    hist, _ = np.histogram(h[coloured], bins=360 // SECTOR, range=(0.0, 360.0))
    top = int(hist.argmax())
    return top * SECTOR, round(float(hist[top] / h.size), 4)


def one_hue(share: float, entropy: float) -> bool:
    """A grey picture (share 0) has no hue to be one of; its entropy is 0 by
    construction and says nothing."""
    return share > 0 and (share > ONE_HUE_SHARE or entropy < HUE_ENTROPY_FLOOR)


def judge(path: Path) -> dict:
    """Every number for one picture, and the faults they add up to."""
    rgb = pixels(Path(path))
    p5, near_black = black_floor(luma(rgb))
    h, s, v = hsv(rgb)
    entropy, (sector, share) = hue_entropy(h, s, v), dominant_hue(h, s, v)
    faults_ = []
    if no_black_floor(p5, near_black):
        faults_.append(f"no black floor (p5 {p5:.1f} over {P5_FLOOR:.0f}, "
                       f"near-black {near_black:.2f} under {BLACK_SHARE:.2f})")
    if one_hue(share, entropy):
        faults_.append(f"one hue (sector {sector} holds {share:.2f} of the frame, "
                       f"hue entropy {entropy:.2f})")
    return {"p5": p5, "near_black": near_black, "hue_entropy": entropy,
            "dominant_hue": sector, "dominant_share": share, "faults": faults_}


def roll_up(judged: list[dict]) -> list[str]:
    """The episode's verdict: medians over its pictures, against the same floors."""
    if not judged:
        return []
    med = {k: float(np.median([j[k] for j in judged]))
           for k in ("p5", "near_black", "dominant_share", "hue_entropy")}
    out = []
    if no_black_floor(med["p5"], med["near_black"]):
        out.append(f"episode: no black floor (median p5 {med['p5']:.1f} over {P5_FLOOR:.0f}, "
                   f"median near-black {med['near_black']:.2f} under {BLACK_SHARE:.2f})")
    if one_hue(med["dominant_share"], med["hue_entropy"]):
        out.append(f"episode: one hue (median dominant-hue share {med['dominant_share']:.2f} "
                   f"against {ONE_HUE_SHARE:.2f}, median hue entropy {med['hue_entropy']:.2f} "
                   f"against {HUE_ENTROPY_FLOOR:.2f})")
    return out


def faults(paths: list[Path]) -> list[str]:
    """Per-picture faults by file name, then the episode roll-up."""
    judged = [judge(p) for p in paths]
    out = [f"{Path(p).name}: {f}" for p, j in zip(paths, judged) for f in j["faults"]]
    return out + roll_up(judged)
