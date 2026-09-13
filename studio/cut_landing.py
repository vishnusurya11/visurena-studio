"""G4.3-4.4 -- did the cut land where the plan pinned it, and is every frame the
take's own picture?

Every frame of the take is matched (studio.frame_match signatures, cosine) to
the take's own cells and to every OTHER cell and location plate of the episode.
For each internal cut (a start pin after frame 0) the gate measures:

  landed   the first frame at or after pin-PRE whose closest own cell is the
           target (similarity >= LAND); delta = landed - pin
  foreign  the longest run of frames inside [pin-PRE, pin+POST] whose best match
           is another take's cell or a location plate (by FOREIGN_MARGIN)
  pingpong frames after landing and before the next start pin whose closest own
           cell belongs to an EARLIER segment
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from studio import frame_match as fm

FPS = 24
PRE, POST = 24, 48
LAND = 0.60
"""CALIBRATION: review8/transitions.md -- a frame that reproduces its pinned cell
scores 0.95-1.00; the neighbour cell a missed cut opened on scored 0.31.  0.60 is
the floor for 'this frame IS the target picture'."""
FOREIGN_MARGIN = 0.05
"""CALIBRATION: inherited from take_dq.picture_dq -- a frame is another picture
only when it beats its own cell by this margin."""
FOREIGN_MIN = 0.60
"""CALIBRATION: and it must MATCH that other picture.  Iteration 4 T03, the cab
mid-crossing: own 0.39, other 0.45 -- without the floor that reads FOREIGN, but a
frame matching nothing is off its own composition, which is drift's business."""
MAX_EARLY, MAX_LATE = 4, 6
"""CALIBRATION: frames.  Every honoured cut of iteration 4 landed in [-3, +1];
the failures measured +34, +51, +37, +54 and -5..-24 (review8/transitions.md)."""
MAX_FOREIGN_RUN = 12
"""CALIBRATION: frames (0.5 s).  Honoured cuts carried <= 7 frames of matcher
flicker; the real intrusions ran 25-57 frames (T01's plate_criterion, 40/51)."""
MAX_PINGPONG = 12
"""CALIBRATION: frames (0.5 s).  Honoured cuts went back 0 frames; the ping-pongs
the owner saw ran 36 and 92 frames (T02, T07)."""
FRAME_PER_TOKEN = (1, 4, 4, 4, 4)
"""comfy/ldm/minimax/model.py: 17 frames per 5 video tokens."""


def token_start(frame: int) -> bool:
    """A pin whose time position coincides with a video token's: 17c + {0, 1, 5, 9, 13}."""
    return frame % 17 in (0, 1, 5, 9, 13)


def grey_frames(video: Path) -> np.ndarray:
    """Every frame of the take, 192x336 grey."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", "scale=192:336", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, 336, 192)


def signatures(frames: np.ndarray) -> np.ndarray:
    """One frame_match signature per frame, flattened for a single matrix product."""
    return np.stack([fm.signature(Image.fromarray(f)).ravel() for f in frames])


def own_family(own: set[str]) -> set[str]:
    """A take's own pictures: its anchor cells AND each of their END pictures.

    A segment is SENT from its cell toward that cell's END picture, so arriving
    there is the take doing as it was told.  Once the END pins were removed the
    END cell stopped being an anchor, and every successful arrival was being
    counted as somebody else's shot: on iteration 5, T02 matched its own Q02_0E
    at 0.988 and T03 matched Q03_0E at 0.978, and both takes were failed and
    queued for a retake for it."""
    return set(own) | {f"{Path(n).stem}E.png" for n in own if not Path(n).stem.endswith("E")}


def foreign_names(frames_dir: Path, own: set[str]) -> list[str]:
    """Every cell and location plate of the episode that is NOT this take's own.
    The plates belong here: a take that drifts onto its empty location is the
    fault (T01, 40 frames of plate_criterion) the cell-only set could not see."""
    mine = own_family(own)
    cells = sorted(p.name for p in frames_dir.glob("Q??_?*.png"))
    plates = sorted(p.name for p in frames_dir.glob("plate_*.png"))
    return [n for n in cells + plates if n not in mine]


def classify(sig: np.ndarray, own: dict[str, np.ndarray], other: dict[str, np.ndarray]) -> list[dict]:
    """Per frame: closest own cell + score, closest other + score, foreign flag."""
    names, o_names = list(own), list(other)
    so = sig @ np.stack([own[n] for n in names]).T
    sf = sig @ np.stack([other[n] for n in o_names]).T if o_names else np.zeros((len(sig), 1))
    out = []
    for t in range(len(sig)):
        i, j = int(so[t].argmax()), int(sf[t].argmax())
        out.append({"f": t, "own": names[i], "own_s": float(so[t, i]),
                    "other": o_names[j] if o_names else "", "other_s": float(sf[t, j]),
                    "foreign": bool(o_names and sf[t, j] > so[t, i] + FOREIGN_MARGIN
                                    and sf[t, j] >= FOREIGN_MIN)})
    return out


def start_pins(anchors: list) -> list[tuple[str, int]]:
    """The take's segment starts in time order: the first pin of each cell, END pins dropped."""
    seen, out = set(), []
    for name, frame in sorted(anchors, key=lambda a: a[1]):
        base = name.replace("E.png", ".png")
        if name.endswith("E.png") or base in seen:
            continue
        seen.add(base)
        out.append((name, frame))
    return out


def longest_run(flags: list[bool]) -> int:
    """The longest run of True in `flags`."""
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    return best


def landing(per_frame: list[dict], anchors: list) -> list[dict]:
    """One row per internal cut: pin, landed, delta, foreign run, ping-pong frames."""
    starts = start_pins(anchors)
    segment = {n.replace("E.png", ".png"): k for k, (n, _) in enumerate(starts)}
    n = len(per_frame)
    rows = []
    for k, (target, pin) in enumerate(starts[1:], start=1):
        nxt = starts[k + 1][1] if k + 1 < len(starts) else n
        lo = max(pin - PRE, 0)
        landed = next((t for t in range(lo, nxt) if per_frame[t]["own"] == target and per_frame[t]["own_s"] >= LAND), None)
        window = per_frame[lo:min(pin + POST, n)]
        back = [t for t in range((landed if landed is not None else pin), nxt)
                if not per_frame[t]["foreign"] and segment[per_frame[t]["own"].replace("E.png", ".png")] < k]
        rows.append({"cut": k, "target": target, "pin": pin, "landed": landed,
                     "delta": None if landed is None else landed - pin,
                     "foreign_run": longest_run([w["foreign"] for w in window]),
                     "foreign_cell": next((w["other"] for w in window if w["foreign"]), ""),
                     "pingpong": len(back), "pingpong_to": per_frame[back[0]]["own"] if back else ""})
    return rows


def verdict(rows: list[dict]) -> dict:
    """Every cut landed within [-MAX_EARLY, +MAX_LATE], no foreign run over
    MAX_FOREIGN_RUN, no ping-pong over MAX_PINGPONG.  Names the first reason."""
    for r in rows:
        if r["foreign_run"] > MAX_FOREIGN_RUN:
            return {"passed": False, "reason": f"cut {r['cut']}: {r['foreign_run']} frames of {r['foreign_cell']} at the cut"}
        if r["delta"] is None or r["delta"] < -MAX_EARLY or r["delta"] > MAX_LATE:
            return {"passed": False, "reason": f"cut {r['cut']} to {r['target']}: landed {r['delta']} frames from the pin"}
        if r["pingpong"] > MAX_PINGPONG:
            return {"passed": False, "reason": f"cut {r['cut']}: {r['pingpong']} frames back on {r['pingpong_to']} after landing"}
    return {"passed": True, "reason": ""}


def cut_landing(video: Path, anchors: list, frames_dir: Path) -> dict:
    """The take's cut-landing report: rows per internal cut, the verdict, and the
    measured cut frames the assembler should use (`measured_cuts`)."""
    own_names = list(dict.fromkeys(n for n, _ in anchors))
    own = {n: fm.signature(fm.load(frames_dir / n)).ravel() for n in own_names if (frames_dir / n).exists()}
    other = {n: fm.signature(fm.load(frames_dir / n)).ravel() for n in foreign_names(frames_dir, set(own))}
    per_frame = classify(signatures(grey_frames(video)), own, other)
    rows = landing(per_frame, anchors)
    out = verdict(rows)
    out["cuts"] = rows
    out["measured_cuts"] = [r["landed"] for r in rows]
    out["foreign_frames"] = sum(r["foreign"] for r in per_frame)
    out["foreign_worst"] = max((r["other"] for r in per_frame if r["foreign"]), key=lambda n: n, default="")
    return out
