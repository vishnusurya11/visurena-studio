"""G-LOOK on a TAKE -- does the picture keep a black in it for its whole length?

studio/look_gate.py judged cells and plates only (scripts/episode/seq_boards.py).
Episode 10 (2026-09-16, dq10/C) shipped one print -- T20, a sunlit wide with a
5th-percentile luma of 43 and one pixel in a hundred near black -- and two
takes that went bright and orange over their length: T16 and T28, a push that
ends on a face filling the frame, so the black jamb and the dark side of the
face leave with it.  All three at 100/100.  This row reads SAMPLES frames
spread over the take with look_gate's own numbers and judges the take's
medians and its ends.

CALIBRATION (docs/calibration/take_look.md; 8 frames per take, 768x768):

    HARD      no floor on the take median   T20  p5 43.3 / near-black 0.01
              clean                          T31  p5  2.0 / near-black 0.63
    ADVISORY  black lost over the length     T16  near-black .45 -> .18, hue share .31 -> .75
              (scored)                       T28  near-black .66 -> .28, hue share .39 -> .79
              clean, darkening on the push   T07 .54 -> .70   T13 .39 -> .53   T15 .36 -> .50
    ADVISORY  level: median mean over 100 with p5 over 15 (T20 117/43; ep09's
              median 95/17.8 fails 15 of 28; T18's second segment 103/9 passes)

Known false alarm: T18, a two-shot take whose planned internal cut goes from
a hat under a doorway to a man walking away in the sun, reads near-black
.49 -> .16 across the cut.  The row reads the whole take; a planned cut is a
planned change of picture.  Free: ffmpeg + PIL + numpy, no GPU, no credit.
"""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from studio import look_gate as lg

FPS = 24
SAMPLES = 8
BLACK_DROP = 0.20
"""Near-black share, first sampled frame to last: a drop this large is the
black leaving the frame (T16 -0.27, T28 -0.38; the darkening takes rise)."""
SHARE_RISE = 0.25
"""Dominant-hue share, first to last: a rise this large is the picture going
one colour (T16 +0.44, T28 +0.40; T25 +0.21 stays under)."""
LEVEL_MEAN = 100.0
"""A take whose median mean luma is over this WITH a lifted p5 is a stop up:
a print between two projections, even when a shadow keeps its near-black."""
PENALTY_NO_FLOOR, PENALTY_LOST, PENALTY_LEVEL = 30.0, 15.0, 5.0
FRAME_EXT = (".png", ".jpg", ".jpeg")
PNG_SIG = b"\x89PNG\r\n\x1a\n"


# ---- the frames ------------------------------------------------------------------

def sample_indices(n: int, samples: int = SAMPLES) -> list[int]:
    """`samples` frame indices spread evenly over n frames, first and last included."""
    return sorted(set(int(round(x)) for x in np.linspace(0, n - 1, max(2, min(samples, n)))))


def frames(video: Path, seconds: float, samples: int = SAMPLES) -> list[np.ndarray]:
    """The sampled frames as float RGB.  A folder of images serves the same."""
    video = Path(video)
    if video.is_dir():
        names = sorted(p for p in video.iterdir() if p.suffix.lower() in FRAME_EXT)
        return [lg.pixels(names[i]) for i in sample_indices(len(names), samples)]
    idx = sample_indices(max(1, int(round(seconds * FPS))), samples)
    sel = "select='" + "+".join(f"eq(n,{i})" for i in idx) + "'"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", sel, "-vsync", "0",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return [np.asarray(Image.open(io.BytesIO(PNG_SIG + chunk)).convert("RGB"), dtype=float)
            for chunk in raw.split(PNG_SIG) if chunk]


# ---- the numbers -----------------------------------------------------------------

def stats(rgb: np.ndarray) -> dict:
    """One frame: look_gate's floor and hue numbers, and its mean luma."""
    y = lg.luma(rgb)
    p5, near_black = lg.black_floor(y)
    _, share = lg.dominant_hue(*lg.hsv(rgb))
    return {"p5": p5, "near_black": near_black, "share": share, "mean": round(float(y.mean()), 2)}


def measure(video: Path, seconds: float) -> dict:
    """The take's medians over its sampled frames, and its first and last."""
    per = [stats(f) for f in frames(video, seconds)]
    if len(per) < 2:
        return {"n": len(per)}
    med = {k: round(float(np.median([p[k] for p in per])), 3) for k in ("p5", "near_black", "share", "mean")}
    ends = {f"{k}_{end}": per[i][k] for k in ("near_black", "share") for end, i in (("first", 0), ("last", -1))}
    return {"n": len(per)} | med | ends


# ---- the verdict -----------------------------------------------------------------

def lost_black(m: dict) -> str:
    """The advisory's words when the black left over the length, else ''."""
    out = []
    if m["near_black_first"] - m["near_black_last"] >= BLACK_DROP:
        out.append(f"black lost {m['near_black_first']:.2f}->{m['near_black_last']:.2f}")
    if m["share_last"] - m["share_first"] >= SHARE_RISE:
        out.append(f"hue rose {m['share_first']:.2f}->{m['share_last']:.2f}")
    return ", ".join(out)


def level(m: dict) -> str:
    """The advisory's words when the take sits a stop up with a lifted p5, else ''."""
    if m["mean"] > LEVEL_MEAN and m["p5"] > lg.P5_FLOOR:
        return f"level mean {m['mean']:.0f} p5 {m['p5']:.0f}"
    return ""


def verdict(m: dict):
    """HARD with no floor on the median; scored ADVISORY when the black is lost
    over the length or the level is a stop up; quiet with fewer than two frames."""
    from studio.take_verdict import Gate
    if m.get("n", 0) < 2:
        return Gate("look", None, True, False, "not measured")
    said = f"p5 {m['p5']:.0f} black {m['near_black']:.2f} hue {m['share']:.2f}"
    if lg.no_black_floor(m["p5"], m["near_black"]):
        return Gate("look", m["p5"], False, True, "no floor " + said, PENALTY_NO_FLOOR)
    lost, up = lost_black(m), level(m)
    penalty = (PENALTY_LOST if lost else 0.0) + (PENALTY_LEVEL if up else 0.0)
    note = "; ".join(s for s in (said, lost, up) if s)
    return Gate("look", m["p5"], not (lost or up), False, note, penalty)


def row(video: Path, seconds: float):
    """The look row for one take."""
    return verdict(measure(video, seconds))
