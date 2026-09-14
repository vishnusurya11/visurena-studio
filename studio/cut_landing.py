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
PRE, POST = 48, 48
"""How far either side of a pin `landing` looks, in frames.

PRE WAS 24, WHICH IS A FLOOR WEARING A NUMBER'S CLOTHES.  The backward search
stops there, so a cut that landed 40 frames early reports exactly -24 -- and
BOTH of episode 3's catastrophic takes report exactly -24, which is the search
limit and not a measurement.  Two seconds is wide enough for the reported delta
to be a value you can act on."""
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
"""CALIBRATION: frames, measured from `stated_frame(pin)` -- the whole second the
model was asked for -- and NOT from the pin.  Every honoured cut of iteration 4
landed in [-3, +1]; the failures measured +34, +51, +37, +54 and -5..-24
(review8/transitions.md).

The origin matters more than the width.  Measured from the pin, 7 of episode 3's
15 internal cuts could not pass even with perfect obedience, because a
whole-second stamp bounds the model to +-12 frames before it does anything
(tests/test_cut_landing_judges_the_ask.py).  A gate may only demand a precision
the instruction can express."""
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


def foreign_names(cells: Path, plates: Path, own: set[str]) -> list[str]:
    """Every cell and location plate of the episode that is NOT this take's own.
    The plates belong here: a take that drifts onto its empty location is the
    fault (T01, 40 frames of plate_criterion) the cell-only set could not see."""
    mine = own_family(own)
    seen = sorted(p.name for p in cells.glob("Q??_?*.png"))
    seen += sorted(p.name for p in plates.glob("plate_*.png"))
    # A `.before.png` is a cell AS IT WAS BEFORE A REDRAW -- a draft that was never
    # rendered against, so no take can legitimately be drifting onto it.  MEASURED
    # on episode 3: 10 of 18 foreign-flagged samples (56 %) were a `.before`
    # sibling, and T12 hard-failed on three of them by 0.08 against a 0.05 margin
    # -- a coin flip between two near-identical pictures of the same panel.
    return [n for n in seen if n not in mine and ".before." not in n]


def foreign_pictures(cells: Path, plates: Path, own: set[str]) -> dict[str, Path]:
    """Every foreign picture as a RESOLVED PATH, because a bare name has to be
    joined to a room and both call sites joined every one of them to `cells`.

    `foreign_names` returns cell names and plate names together; plates live in
    `boards/plates/`, so `cells / "plate_cab.png"` never existed and the plate
    signatures were silently skipped.  That set is the one that caught T01
    drifting onto plate_criterion for 40 frames."""
    return {n: (plates if n.startswith("plate_") else cells) / n
            for n in foreign_names(cells, plates, own)}


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


def stated_frame(pin: int, fps: int = FPS) -> int:
    """The frame the model was actually ASKED for.

    It never sees `pin`.  `episode_ref_official.stamp` rounds every time to a
    whole second -- the engine's own grammar -- so a pin at frame 137 is asked
    for as "00:06", which is frame 144.  Obedience is measured against this;
    the pin stays what the PICTURE is matched against."""
    return round(pin / fps) * fps


def off_span(landed: int, pin: int, asked: int) -> int:
    """How far a landing is OUTSIDE the span the instruction could mean; 0 inside.

    The plan wants `pin`; the words say `asked`.  Both are obedient landings and
    so is anything between them, so the tolerance is applied to the distance from
    that span and not from either end.  Judging against `asked` alone refuses a
    cut that lands exactly on the pin; judging against `pin` alone refuses one
    that lands exactly on the second it was asked for."""
    lo, hi = min(pin, asked), max(pin, asked)
    return 0 if lo <= landed <= hi else (landed - hi if landed > hi else landed - lo)


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
        # A PING-PONG NEEDS THE FRAME TO ACTUALLY BE THE EARLIER CELL.  `landed`
        # above requires `own_s >= LAND`; this required nothing, so a frame that
        # matched NOTHING was reported as a cut back.  MEASURED on T07: the camera
        # walks off its cell (end_sim 0.087) and for 44 straight frames every
        # own-score is 0.022-0.352, argmax lands on whichever cell is the better
        # nearest-neighbour of noise, and the gate said "cut back to shot 0".
        # Four identical re-rolls could never fix that, because the fault was in
        # the reading, not the render.
        back = [t for t in range((landed if landed is not None else pin), nxt)
                if not per_frame[t]["foreign"] and per_frame[t]["own_s"] >= LAND
                and segment[per_frame[t]["own"].replace("E.png", ".png")] < k]
        asked = stated_frame(pin)
        rows.append({"cut": k, "target": target, "pin": pin, "asked": asked, "landed": landed,
                     "delta": None if landed is None else off_span(landed, pin, asked),
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
            return {"passed": False, "reason": f"cut {r['cut']} to {r['target']}: landed {r['delta']} frames from the {r.get('asked', r['pin'])/FPS:.0f}s it was asked for"}
        if r["pingpong"] > MAX_PINGPONG:
            return {"passed": False, "reason": f"cut {r['cut']}: {r['pingpong']} frames back on {r['pingpong_to']} after landing"}
    return {"passed": True, "reason": ""}


def cut_landing(video: Path, anchors: list, cells: Path) -> dict:
    """The take's cut-landing report: rows per internal cut, the verdict, and the
    measured cut frames the assembler should use (`measured_cuts`)."""
    own_names = list(dict.fromkeys(n for n, _ in anchors))
    own = {n: fm.signature(fm.load(cells / n)).ravel() for n in own_names if (cells / n).exists()}
    other = {n: fm.signature(fm.load(p)).ravel()
             for n, p in foreign_pictures(cells, cells.parent / "plates", set(own)).items()}
    per_frame = classify(signatures(grey_frames(video)), own, other)
    rows = landing(per_frame, anchors)
    out = verdict(rows)
    out["cuts"] = rows
    out["measured_cuts"] = [r["landed"] for r in rows]
    out["foreign_frames"] = sum(r["foreign"] for r in per_frame)
    out["foreign_worst"] = max((r["other"] for r in per_frame if r["foreign"]), key=lambda n: n, default="")
    return out
