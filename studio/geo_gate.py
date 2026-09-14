"""G3 geography -- SUPERSEDED IN PART, UNWIRED IN THE REST. Read this before using it.

NOTHING IMPORTS THIS MODULE except its own test. That is not an invitation to
wire it up: one half of it is a worse-founded duplicate of a rule that now lives
elsewhere, and wiring it would re-introduce a fault this repo has already paid
to remove.

`end_moved` / `frozen_end_cells` (END_MOVED = 0.75) -- SUPERSEDED by
`episode_seq_board.end_pair_verdict`. `_sig` here is byte-for-byte
`frame_match.signature`, so `end_moved` IS `fm.similarity(start, end) < 0.75`:
the same measurement as END_CEILING = 0.80, compared to a different number. The
replacement is better founded on every axis -- 12 episode-2 pairs plus all 11 of
episode 4's against four samples here, plus the `SUBJECT_FILLS` exemption for an
insert and the 7x4 `changed_blocks` override for a locked-off camera. And this
version's stated "moved" range of 0.34-0.62 is FALSIFIED by episode 4: Q09 at
0.807, Q20 and Q21 at 0.856 and Q15 at 0.938 all moved, verified by eye, and
every one is above 0.75. `frozen_end_cells` would call 7 of episode 4's 11 END
pairs frozen -- the identical false refusal that commit e30f5e4 removed.

The rest -- `cuts_from_energy`, `unplanned_cuts`, `landmark_track`,
`direction_breaks`, `floor_slide` -- is UNWIRED rather than superseded. It was
written against the i2v-era chain and nothing in the r2v chain calls it. The
take-side cut detection overlaps `cut_landing`, which is live and calibrated on
more data; the landmark and direction rules overlap `route_gate` and the size
ladder in `episode_seq_board`.

IT IS KEPT, NOT DELETED, ON PURPOSE. `studio/identity.py` was deleted in 1c04e40
because "nothing was importing it yet", and it turned out to be 173 lines of
measured, licence-audited work that the next person needed and had to recover
out of git history. A banner costs nothing and a deletion costs that.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

CUT, CUT_RATIO, PIN_TOL_S = 20.0, 4.0, 0.3
"""CALIBRATION: review8/geography.md, iterations 3 and 4.  A pinned cut is a
frame-to-frame mean |diff| of 20-60 on 96x168 grey at 24 fps; a moving wide (T03,
the cab) peaks at 14 and a spring-up in a wide (T12) at 8.  The 4x-the-local-
median rule stops a busy shot faking a cut.  PIN_TOL_S: a pin lands on a video
token, so a cut within 0.3 s of one is that pin's."""
END_MOVED = 0.75
"""CALIBRATION: a walk END cell that froze reads 0.82-0.89 against its start cell;
one that moved reads 0.34-0.62.  Four samples -- thin, and said so in the report."""
SHRINK, GROW, ROUTE_STEP = 0.25, 1.3, 0.3
"""CALIBRATION: the far landmark stays within 2 % across a 3 s static hold (T11,
T13) and shrinks 9 % while the camera settles (T12); a lens change between size
classes moves it up to 50 %, so only geography sizes are compared.  A route step
of 0.3 or more with the landmark under 1.3x is a walk the drawer did not draw."""
WALK = 20.0
"""CALIBRATION: floor slide (bottom 22 % band, phase correlation, px/s at 192
wide).  Tracking walks that read real measured 25-49; a close that crawls 12; a
hold 0."""
GEO_SIZES = {"medium", "full", "wide"}


def energy(frames: np.ndarray) -> np.ndarray:
    """Mean |diff| between consecutive grey frames (N-1 values)."""
    return np.abs(np.diff(frames.astype(np.float32), axis=0)).mean(axis=(1, 2))


def cuts_from_energy(e: np.ndarray, cut: float = CUT, ratio: float = CUT_RATIO, fps: int = 24) -> list[float]:
    """Seconds of every hard cut: a step above `cut` and `ratio` times the median of
    the surrounding second (excluding itself)."""
    out = []
    for i, v in enumerate(e):
        if v < cut:
            continue
        lo, hi = max(0, i - fps // 2), min(len(e), i + fps // 2 + 1)
        around = np.concatenate([e[lo:i], e[i + 1:hi]])
        if len(around) and v >= ratio * max(float(np.median(around)), 0.5):
            out.append(round((i + 1) / fps, 2))
    return out


def unplanned_cuts(cuts: list[float], pin_frames: list[int], fps: int = 24, tol: float = PIN_TOL_S) -> list[float]:
    """Hard cuts with no pin within `tol` seconds: a picture change the plan did not ask for."""
    pins = [f / fps for f in pin_frames]
    return [c for c in cuts if not any(abs(c - p) <= tol for p in pins)]


def transitions(anchors: list) -> int:
    """Pins where the cell CHANGES (an END pin followed by the next start cell)."""
    order = sorted(anchors, key=lambda a: a[1])
    return sum(1 for a, b in zip(order, order[1:]) if a[0].replace("E.png", ".png") != b[0].replace("E.png", ".png"))


def extra_pictures(cuts: list[float], anchors: list) -> int:
    """How many more hard cuts the take made than the plan has cell changes; > 0 is a
    ping-pong or a re-entered doorway (T07: 3 cuts for 2 changes)."""
    return max(0, len(cuts) - transitions(anchors))


def _sig(image: Image.Image) -> np.ndarray:
    a = np.asarray(image.convert("L").resize((48, 84)), dtype=float)
    a = a - a.mean()
    return a / (np.linalg.norm(a) + 1e-9)


def end_moved(start: Image.Image, end: Image.Image, floor: float = END_MOVED) -> bool:
    """A walk's END cell must show a different instant: similarity under `floor`."""
    return float((_sig(start) * _sig(end)).sum()) < floor


def frozen_end_cells(cells_dir: Path, names: list[str], floor: float = END_MOVED) -> list[str]:
    """Every END cell on the sheet that copied its own start cell.  G3: this is the
    fault that produced three frozen takes in iteration 4 (T02, T07, T08)."""
    out = []
    for name in names:
        if not name.endswith("E.png"):
            continue
        start = cells_dir / name.replace("E.png", ".png")
        if start.exists() and not end_moved(Image.open(start), Image.open(cells_dir / name), floor):
            out.append(name)
    return out


def landmark_track(heights: list, paths: list, sizes: list[str],
                   shrink: float = SHRINK, grow: float = GROW, step: float = ROUTE_STEP) -> dict:
    """Over geography cells in story order: indices where the landmark shrank more than
    `shrink`, and indices where the route advanced `step` but the landmark did not grow `grow`x."""
    shrunk, flat, last = [], [], None
    for i, (h, p, s) in enumerate(zip(heights, paths, sizes)):
        if h is None or s not in GEO_SIZES or p is None:
            continue
        if last is not None:
            lh, lp = last
            if h < lh * (1 - shrink):
                shrunk.append(i)
            elif p - lp >= step and h < lh * grow:
                flat.append(i)
        last = (h, p)
    return {"shrunk": shrunk, "flat": flat}


AWAY = re.compile(r"from behind|tracking behind|away from (the )?camera|seen from behind|their backs", re.I)
TOWARD = re.compile(r"toward(s)? the camera|tracking back ahead|facing (them|the camera)|grow larger in frame", re.I)
BESIDE = re.compile(r"tracking beside|side on|in (strict )?profile walking|slide past|sliding past", re.I)
TURN = re.compile(r"\bturns?\b|turning|comes round|wheels", re.I)


def direction_of(text: str) -> str:
    """'away' | 'toward' | 'beside' | 'still' from a segment's frame + motion text."""
    if TOWARD.search(text):
        return "toward"
    if AWAY.search(text):
        return "away"
    if BESIDE.search(text):
        return "beside"
    return "still"


def direction_breaks(segments: list[dict]) -> list[tuple[int, str, str]]:
    """Consecutive walk segments of one setup whose direction changes without a turn
    named in the text: (index, from, to)."""
    out, last = [], None
    for i, s in enumerate(segments):
        if s.get("size") not in GEO_SIZES or s.get("path") is None:
            continue
        text = f"{s.get('frame', '')} {s.get('motion', '')}"
        d = direction_of(text)
        if d == "still":
            continue
        if last is not None and d != last and not TURN.search(text):
            out.append((i, last, d))
        last = d
    return out


def floor_slide(frames: np.ndarray, band: float = 0.22, step: int = 6, fps: int = 24) -> float:
    """Median px/s the floor texture moves (phase correlation on the bottom band)."""
    h = frames.shape[1]
    mags = []
    for i in range(0, len(frames) - step, step):
        a, b = frames[i, int(h * (1 - band)):].astype(float), frames[i + step, int(h * (1 - band)):].astype(float)
        win = np.hanning(a.shape[0])[:, None] * np.hanning(a.shape[1])[None, :]
        fa, fb = np.fft.fft2((a - a.mean()) * win), np.fft.fft2((b - b.mean()) * win)
        r = fa * np.conj(fb)
        c = np.abs(np.fft.ifft2(r / (np.abs(r) + 1e-9)))
        y, x = np.unravel_index(int(np.argmax(c)), c.shape)
        x = x - a.shape[1] if x > a.shape[1] // 2 else x
        y = y - a.shape[0] if y > a.shape[0] // 2 else y
        mags.append(np.hypot(x, y) * fps / step)
    return round(float(np.median(mags)), 1) if mags else 0.0


def walk_moves(slide_px_s: float, floor: float = WALK) -> bool:
    """Did a tracking walk actually travel?"""
    return slide_px_s >= floor
