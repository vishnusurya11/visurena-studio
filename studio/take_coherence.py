"""G-COHERENCE -- does the take stay on its storyboard for the WHOLE take?

The freeze gate's opposite.  Episode 9 scored 28/28 at 100.0 while 62 % of its
frames matched no pinned cell (docs/analysis/ep08_ep09_why_worse.md): `drift`
reads the END frame only, `foreign` only knows OTHER takes' pictures, and the
churn in between -- the wagon train multiplying, the town swapping to bare
hills, a laughing close whipping into four riders -- had no gate.

Four numbers off the decoded grey frames, ffmpeg + numpy only, no GPU:

  offboard_share  frames whose best similarity to ANY RE-FRAMING of one of the
                  take's own pinned cells is under ON_BOARD.  A re-framing is
                  the cell or one of its zoom crops (ZOOMS x a 3x3 grid): a
                  dolly on the board is not an abandonment of it.
  last_vs_cell    the last frame against the last pinned cell, the same way.
  nonrigid        mean |diff| per frame step after a global translation
                  (phase correlation on a 1/DOWN grey) is removed.  A pan is
                  rigid; a morph is not.
  hard_cut        the largest single-step mean |diff| away from any internal
                  pin (+-PIN_TOL frames): a cut the plan did not ask for.

CALIBRATION (ep05-09 takes on disk, 768x768, 2026-09-16; the report's numbers
reproduce: mean |diff| median 1.46/2.81/4.57/5.49/6.63 against its 1.47/2.83/
4.58/5.51/6.67, the named cuts ep07 T13 57.5, ep08 T28 81.8, ep09 T11 32.2).

A PLAIN cosine to the static cell does NOT separate the owner's judgement:
off-board share (< 0.5) medians 0.00/0.60/0.49/0.29/0.59 -- episode 6, which
he thought fine, is the worst.  Against the cell's zoom crops the medians are
0.00/0.00/0.08/0.03/0.36, and the three ep09 takes the report named read
T02 0.60, T10 0.78, T20 0.79.  Fail counts per episode (ep05/06/07/08/09,
n = 25/26/25/28/28) under the zoom-tolerant reading:

    offboard_share > 0.30     4  11   9   6  17
    offboard_share > 0.40     3  10   4   4  10     <- OFFBOARD_HARD
    offboard_share > 0.50     2   8   3   1   7
    offboard_share > 0.60     1   7   3   0   4
    last_vs_cell   < 0.20     0   1   0   0   4     <- LAST_HARD
    last_vs_cell   < 0.30     0   4   2   1   9
    last_vs_cell   < 0.40     4   7   7   3  13     <- LAST_ADVISORY
    hard_cut       > 20       1   0   1   2   3     <- CUT_ADVISORY
    hard_cut       > 30       0   0   1   2   1     <- CUT_HARD
    nonrigid       > 5        1  10   9  16  21
    nonrigid       > 6        1   5   4  12  17     (DOWN=8 pass; see below)
    nonrigid, DOWN=2 (the shipped grid), ep05 / ep07 / ep09 only:
    nonrigid       > 5        1   7  --  --  20
    nonrigid       > 6        0   5  --  --  14
    nonrigid       > 7        0   3  --  --   8     <- NONRIGID_ADVISORY
    nonrigid       > 8        0   1  --  --   6
    medians                 1.55 4.09  -- -- 5.89
    nonrigid       > 8        0   1   1   5   9

    HARD (off-board > 0.40 or cut > 30 or last < 0.20)
                              3  10   4   4  10    ep07 16 %, ep09 36 %
    HARD or churn > 6         3  12   5  13  18    ep07 20 %, ep09 64 %

SAID PLAINLY: no threshold on the hard rungs alone fails 50 % of ep09 while
passing 70 % of ep07 -- 0.35 does it by a knife-edge (7/25 vs 15/28) with five
takes inside 0.03 of the line, and that is a fit, not a separation.  The rung
the owner's eye actually tracked is the churn (nonrigid > 6: 4 of ep07, 17 of
ep09), and it is ADVISORY here because it cannot tell a morph from a large
honest move.  What the off-board share flags on a fine episode, seen by eye:
ep06 T04 is a dolly through the room ending on the boys' faces, ep06 T14 a
hand lifting the glass out of an insert -- action that leaves the cell, which
a cosine to that cell cannot forgive.  That is this instrument's ceiling.
"""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from studio import frame_match as fm

FPS = 24
DOWN = 2
"""Phase correlation runs on a 1/2 grey (384x384 of 768) in whole pixels, so a
pan is resolved to 2 px per step at full size.  It was 8, and at 8 a pan under
8 px/frame -- every dolly in the series -- rounded to no shift at all, and the
'non-rigid' residual equalled the raw diff on every take: the pan removal was
removing nothing.  A synthetic 4 px/frame pan now reads rigid (residual under
a fifth of the raw diff)."""
ZOOMS = (1.15, 1.3, 1.5, 1.75, 2.0)
"""The re-framings of a cell a take may legitimately show: up to 2x in, at a
3x3 grid of positions.  Beyond 2x a close-up of a wide is a different picture."""
ON_BOARD = 0.50
"""frame_match cosine at or above which a frame IS a re-framing of the cell
(the report's definition: 'off-board' = under 0.5 to any pinned cell)."""
OFFBOARD_HARD, OFFBOARD_ADVISORY = 0.40, 0.20
LAST_HARD, LAST_ADVISORY = 0.20, 0.40
CUT_HARD, CUT_ADVISORY = 30.0, 20.0
PIN_TOL = 6
"""A two-anchor take is allowed its one cut within +-6 frames of the pin
(cut_landing.MAX_LATE); ep09 T16 landed at 102 on a pin of 102, T18 at 85 on 85."""
NONRIGID_ADVISORY = 7.0
"""Churn wall, set at the corrected phase-correlation grid (DOWN=2), where a pan
under 8 px/frame is actually removed. At 6.0 -- the DOWN=8 number -- it flagged a
fifth of episode 7, which the owner judged fine, and the union with the hard rungs
reached 48 %. At 7.0 the gap in the data is clean: ep05 0/25, ep07 3/25 (7.2, 7.4,
8.1 -- T14 among them, the borderline morph seen by eye), ep09 8/28. Advisory."""


# ---- decoding ----------------------------------------------------------------

def probe_size(video: Path) -> tuple[int, int]:
    """(width, height) of the take, from its first frame; no ffprobe needed."""
    png = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-frames:v", "1", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).size


def frames(video: Path, seconds: float | None = None) -> np.ndarray:
    """Grey frames (n, h, w) uint8 at native size, the first `seconds` only."""
    w, h = probe_size(video)
    cut = ["-t", f"{seconds:.3f}"] if seconds else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), *cut, "-vf", f"fps={FPS}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w)


# ---- the take's own pictures ------------------------------------------------

def pinned_names(record: dict) -> list[str]:
    """The cells the take was pinned to: its anchors, then any staged END picture."""
    names = list(dict.fromkeys(n for n, _ in record.get("anchors") or []))
    for r in record.get("refs") or []:
        if r.startswith("Q") and r.endswith("E.png") and r not in names:
            names.append(r)
    return names


def last_pinned(record: dict) -> str:
    """The picture the take should END on: the staged END cell, else the last anchor."""
    ends = [r for r in record.get("refs") or [] if r.startswith("Q") and r.endswith("E.png")]
    if ends:
        return ends[-1]
    return max(record.get("anchors") or [("", 0)], key=lambda a: a[1])[0]


def load_cells(cells: Path, names: list[str]) -> dict[str, Image.Image]:
    """The named cells as images.  A named cell that is not there is an ERROR,
    not an omission (see take_verdict.cell_signatures)."""
    missing = [n for n in names if not (cells / n).exists()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} pinned cells are not in {cells}: {', '.join(sorted(missing)[:4])}")
    return {n: fm.load(cells / n) for n in names}


def reframings(cell: Image.Image) -> list[Image.Image]:
    """The cell and its zoom crops: every picture a camera on the board may show."""
    w, h = cell.size
    out = [cell]
    for z in ZOOMS:
        cw, ch = int(w / z), int(h / z)
        for fy in (0.0, 0.5, 1.0):
            for fx in (0.0, 0.5, 1.0):
                x, y = int((w - cw) * fx), int((h - ch) * fy)
                out.append(cell.crop((x, y, x + cw, y + ch)))
    return out


def bank(cells: dict[str, Image.Image]) -> dict[str, np.ndarray]:
    """Per cell, one frame_match signature per re-framing, stacked (k, 4032)."""
    return {n: np.stack([fm.signature(r).ravel() for r in reframings(img)]) for n, img in cells.items()}


def signatures(fr: np.ndarray) -> np.ndarray:
    """One frame_match signature per frame."""
    return np.stack([fm.signature(Image.fromarray(f)).ravel() for f in fr])


def best_match(sigs: np.ndarray, sigbank: dict[str, np.ndarray]) -> np.ndarray:
    """Per frame, the best similarity to any re-framing of any pinned cell."""
    if not sigbank:
        return np.zeros(len(sigs))
    return (sigs @ np.concatenate(list(sigbank.values())).T).max(axis=1)


# ---- rigid versus non-rigid motion ---------------------------------------------

def downscale(f: np.ndarray, k: int = DOWN) -> np.ndarray:
    """Block-mean by k; a ragged edge is dropped."""
    h, w = f.shape
    return f[:h - h % k, :w - w % k].reshape(h // k, k, w // k, k).mean(axis=(1, 3))


def shift_of(a: np.ndarray, b: np.ndarray) -> tuple[int, int]:
    """(dy, dx) that moves `b` onto `a`, by phase correlation; whole pixels."""
    fa, fb = np.fft.fft2(a - a.mean()), np.fft.fft2(b - b.mean())
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    corr = np.fft.ifft2(r).real
    h, w = corr.shape
    dy, dx = np.unravel_index(int(corr.argmax()), corr.shape)
    return (dy - h if dy > h // 2 else dy), (dx - w if dx > w // 2 else dx)


def residual(prev: np.ndarray, cur: np.ndarray, dy: int, dx: int) -> float:
    """Mean |diff| over the overlap once `prev` is shifted by (dy, dx)."""
    h, w = prev.shape
    if abs(dy) >= h // 2 or abs(dx) >= w // 2:
        return float(np.abs(prev.astype(np.int16) - cur).mean())
    p = prev[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)].astype(np.int16)
    c = cur[max(0, dy):h - max(0, -dy), max(0, dx):w - max(0, -dx)]
    return float(np.abs(p - c).mean())


def step_diffs(fr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per frame step: the raw mean |diff| and the residual after pan removal."""
    raw, rigid = [], []
    for i in range(1, len(fr)):
        raw.append(float(np.abs(fr[i].astype(np.int16) - fr[i - 1]).mean()))
        dy, dx = shift_of(downscale(fr[i]), downscale(fr[i - 1]))
        rigid.append(residual(fr[i], fr[i - 1], -dy * DOWN, -dx * DOWN))
    return np.array(raw), np.array(rigid)


def hard_cut(raw: np.ndarray, anchors: list | None, tol: int = PIN_TOL) -> tuple[float, int]:
    """The largest step away from every internal pin, and the frame it lands on."""
    pins = [int(f) for _, f in anchors or [] if f > 0]
    best, at = 0.0, 0
    for i, v in enumerate(raw, start=1):
        if v > best and not any(abs(i - p) <= tol for p in pins):
            best, at = float(v), i
    return best, at


# ---- the measurement ---------------------------------------------------------

def measure(fr: np.ndarray, cells: dict[str, Image.Image], anchors: list | None = None) -> dict:
    """The four coherence numbers of one take, off its grey frames and the images
    of its own pinned cells; `anchors` are `[[cell, frame], ...]` from the record."""
    sigbank = bank(cells)
    sigs = signatures(fr)
    best = best_match(sigs, sigbank)
    last = last_pinned({"anchors": anchors or [], "refs": [n for n in cells if n.endswith("E.png")]}) or next(iter(cells), "")
    last_sim = float((sigs[-1] @ sigbank[last].T).max()) if last in sigbank and len(sigs) else 0.0
    raw, rigid = step_diffs(fr)
    cut, at = hard_cut(raw, anchors)
    return {"frames": int(len(fr)), "offboard_share": round(float((best < ON_BOARD).mean()), 3) if len(best) else 0.0,
            "last_vs_cell": round(last_sim, 3), "last_cell": last,
            "raw_diff": round(float(raw.mean()), 2) if len(raw) else 0.0,
            "nonrigid": round(float(rigid.mean()), 2) if len(rigid) else 0.0,
            "hard_cut": round(cut, 1), "hard_cut_at": at}


def rows(m: dict) -> list:
    """The four verdict rows: off-board, last-vs-cell and cut are HARD, churn advisory."""
    from studio.take_verdict import Gate
    if not m:
        return [Gate(n, None, True, False, "not measured") for n in ("coherence off-board", "last-vs-cell", "cut", "churn")]
    share, last, cut, churn = m["offboard_share"], m["last_vs_cell"], m["hard_cut"], m["nonrigid"]
    # Every penalty starts where its advisory band starts: a dolly on the board
    # reads 0.00-0.10 off-board and must cost nothing (test_score_is_honest).
    return [Gate("coherence off-board", share, share <= OFFBOARD_ADVISORY, share > OFFBOARD_HARD, f"{share:.2f}",
                 50.0 * max(0.0, share - OFFBOARD_ADVISORY) / (1.0 - OFFBOARD_ADVISORY)),
            Gate("last-vs-cell", last, last >= LAST_ADVISORY, last < LAST_HARD, f"{last:.2f}",
                 20.0 * max(0.0, LAST_ADVISORY - last) / LAST_ADVISORY),
            Gate("cut", cut, cut <= CUT_ADVISORY, cut > CUT_HARD, f"{cut:.1f}",
                 min(40.0, 4.0 * max(0.0, cut - CUT_ADVISORY))),
            Gate("churn", churn, churn <= NONRIGID_ADVISORY, False, f"{churn:.1f}",
                 min(30.0, 10.0 * max(0.0, churn - NONRIGID_ADVISORY)))]
