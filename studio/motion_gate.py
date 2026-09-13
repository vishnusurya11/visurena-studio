"""G4.1-4.2 -- is the picture alive?  Block-max motion energy per frame step,
judged per storyboard segment.

The old scan (96x168 grey, 8 fps, global mean |diff|) called a speaking mouth
frozen a quarter of the time: lips move in one small region and the frame-wide
mean dilutes them.  Here every frame step is scored by the LARGEST mean |diff|
over 24x24 blocks of a 192x336 grey frame (a block is ~96x96 px at 768x1344, a
mouth's size).

Verdict per segment (from the anchors: each start pin opens a segment, an END
pin belongs to its start cell): seconds frozen at the segment START (the
owner's "a static image and then after some time video", 2026-09-11 15:15) and
the frozen share.  HARD: no segment frozen longer than START_LIMIT_S at its
start.  ADVISORY: the frozen share against a ceiling per segment kind.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

FPS = 24
SIZE = (192, 336)
BLOCK = 24
BIN_S = 0.25
STILL = 1.2
"""CALIBRATION: review8/motion_gate.md, 13 813 frame steps over 63 H3 takes
(iterations 2-4, retakes and fails, 2026-09-11).  A pinned still reads 0.2-0.7,
a slow drift the eye still reads as a still 0.8-1.1, a living hold at rest
(breathing, a head sway, ink in water) 1.8-3.0, a speaking mouth 3-15, a walk
9-16, the cab crossing 40-55.  1.2 is the gap between 'still' and 'alive'."""
START_LIMIT_S = 1.0
"""CALIBRATION: owner 2026-09-11 15:15 ("a static image and then after some time
video").  Iteration-4 offenders measured 1.5-5.75 s of frozen start (T01, T10,
T11, T12, T13, T17); the takes no reviewer named measured 0-0.88 s (T20)."""
GRACE_S = 0.5
"""CALIBRATION: a pinned cell settles in its first frames (a twitch of 1.3-2.0 in
the first bin, then the still -- iteration-4 T17 segment 0).  A still run that
begins inside GRACE_S still counts as 'at the start'."""
SHARE_CEILING = {"dialogue": 0.20, "hold": 0.35, "insert": 0.50, "track": 0.10}
"""CALIBRATION: per-kind frozen-share distributions over 136 segments
(review8/motion_gate/calib.json).  Advisory only: a share is a taste call, a
frozen start is not."""


def frames(video: Path, seconds: float | None = None) -> np.ndarray:
    """Grey frames (n, 336, 192) at FPS, the first `seconds` only."""
    w, h = SIZE
    cut = ["-t", f"{seconds:.3f}"] if seconds else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), *cut, "-vf", f"fps={FPS},scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w).astype(np.float32)


def block_max(fr: np.ndarray) -> np.ndarray:
    """Per frame step, the largest mean |diff| over BLOCK x BLOCK blocks."""
    if len(fr) < 2:
        return np.zeros(0, dtype=np.float32)
    d = np.abs(fr[1:] - fr[:-1])
    n, h, w = d.shape
    blocks = d.reshape(n, h // BLOCK, BLOCK, w // BLOCK, BLOCK).mean(axis=(2, 4))
    return blocks.max(axis=(1, 2))


def bin_means(energy: np.ndarray, fps: int = FPS, bin_s: float = BIN_S) -> list[float]:
    """Mean energy per bin of `bin_s` seconds; a trailing bin under half full is dropped."""
    per = max(1, int(round(fps * bin_s)))
    out = []
    for i in range(0, len(energy), per):
        chunk = energy[i:i + per]
        if len(chunk) * 2 >= per:
            out.append(round(float(chunk.mean()), 3))
    return out


def segments(anchors: list, total_frames: int) -> list[tuple[str, int, int]]:
    """(cell, first frame, end frame) per segment in time order; an END pin
    (a name ending E.png, or the start cell pinned again) opens no segment."""
    starts: dict[str, int] = {}
    for name, frame in anchors:
        if not name.endswith("E.png"):
            starts[name] = min(starts.get(name, frame), frame)
    order = sorted(starts.items(), key=lambda x: x[1])
    return [(name, f, order[i + 1][1] if i + 1 < len(order) else total_frames) for i, (name, f) in enumerate(order)]


def shot_of(cell: str) -> int:
    """Cell name to shot index: Q17_2.png -> 17."""
    return int(cell[1:3])


def kind_of(shot, lines: list) -> str:
    """What the segment is: a dialogue line plays on it, a tracking move, an insert, or a hold."""
    if any(line.kind == "dialogue" and line.shot == shot.index for line in lines):
        return "dialogue"
    if shot.motion.lower().startswith("tracking"):
        return "track"
    if shot.size == "insert":
        return "insert"
    return "hold"


def leading_still_s(bins: list[float], still: float = STILL, bin_s: float = BIN_S, grace_s: float = GRACE_S) -> float:
    """Seconds of the first still run that begins within `grace_s` of the segment's
    first frame (the owner's static image, then video); 0 if the picture moves."""
    first = next((i for i, v in enumerate(bins) if v < still), None)
    if first is None or first * bin_s > grace_s:
        return 0.0
    n = 0
    for v in bins[first:]:
        if v >= still:
            break
        n += 1
    return round(n * bin_s, 2)


def still_share(bins: list[float], still: float = STILL) -> float:
    """Fraction of the segment's bins the eye reads as a still."""
    return round(sum(v < still for v in bins) / len(bins), 3) if bins else 0.0


def frozen_spans(bins: list[float], still: float = STILL, bin_s: float = BIN_S,
                 min_s: float = 0.75) -> list[tuple[float, float]]:
    """(start, end) seconds of every run of still bins at least `min_s` long."""
    out, start = [], None
    for i, v in enumerate(bins + [still + 1]):
        if v < still and start is None:
            start = i
        elif v >= still and start is not None:
            if (i - start) * bin_s >= min_s:
                out.append((round(start * bin_s, 2), round(i * bin_s, 2)))
            start = None
    return out


def segment_verdict(bins: list[float], kind: str) -> dict:
    """One segment's numbers: how long it opened frozen, how much of it is still."""
    lead, share = leading_still_s(bins), still_share(bins)
    return {"kind": kind, "seconds": round(len(bins) * BIN_S, 2), "leading_still_s": lead, "still_share": share,
            "mean_energy": round(float(np.mean(bins)), 2) if bins else 0.0,
            "start_ok": lead <= START_LIMIT_S, "share_ok": share <= SHARE_CEILING.get(kind, SHARE_CEILING["hold"])}


def report(energy: np.ndarray, anchors: list, kinds: dict[str, str] | None = None) -> dict:
    """The motion verdict for one take, from its per-step energy and its anchors."""
    segs = segments(anchors or [("Q00_0.png", 0)], len(energy) + 1)
    kinds = kinds or {}
    out = []
    for cell, start, end in segs:
        v = segment_verdict(bin_means(energy[start:min(end, len(energy))]), kinds.get(cell, "hold"))
        out.append({"cell": cell, "start_s": round(start / FPS, 2), "end_s": round(min(end, len(energy)) / FPS, 2), **v})
    allbins = bin_means(energy)
    return {"segments": out, "worst_leading_still_s": max((s["leading_still_s"] for s in out), default=0.0),
            "still_share": still_share(allbins), "frozen_spans": frozen_spans(allbins),
            "motion_ok": all(s["start_ok"] for s in out), "share_ok": all(s["share_ok"] for s in out),
            "bins": allbins}


def motion_dq(video: Path, anchors: list, seconds: float, kinds: dict[str, str] | None = None) -> dict:
    """The take's motion verdict over its placed `seconds`, per segment of `anchors`
    (a list of [cell name, frame]); `kinds` maps a cell to its kind (default hold)."""
    return report(block_max(frames(video, seconds)), anchors, kinds)


def attempt_score(report_: dict) -> tuple:
    """Lower is better: the hard gates first, then the freeze at a start, the frozen
    share, foreign frames, audio drift."""
    motion = report_.get("motion", {})
    audio = report_.get("audio", {})
    passed = motion.get("motion_ok", True) and report_.get("foreign", 0) == 0 and audio.get("lag_ok", True)
    return (0 if passed else 1, motion.get("worst_leading_still_s", 0.0), motion.get("still_share", 0.0),
            report_.get("foreign", 0), abs(audio.get("lag_s", 0.0)))


def best_attempt(reports: dict[str, dict]) -> str:
    """The attempt (key) with the lowest score; a tie keeps the first listed (the current file)."""
    return min(reports, key=lambda k: attempt_score(reports[k]))
