"""G-ZOOM -- how far did the push actually travel?

Episode 10 (2026-09-16): the ref2v model (MiniMax-H3) turns a planned push-in
of "a hand's breadth" into a dolly that ends one or two SIZES tighter -- a
close that ends on nostrils.  Coherence off-board, last-vs-cell and drift all
passed those takes: a dolly on the board is not an abandonment of it, and none
of them measures scale.  This does.

    ratio      apparent scale change of the SUBJECT, first frame -> last frame
               (> 1 tighter / pushed in, < 1 pulled back); the judged number
    camera     the same for the whole frame (the room, the plate): the camera
    per_step   the consecutive subject ratios between the sampled frames
    monotonic  every step (beyond STILL) goes the same way
    measured   False when a step had fewer than MIN_INLIERS agreeing windows;
               then ratio is 1.0 and the verdict is advisory only

HOW.  numpy + PIL only (no OpenCV in the lock).  Between two sampled frames a
GRID x GRID lattice of overlapping Hann windows is phase-correlated (sub-pixel
parabolic peak): each textured window gives one displacement vector.  A zoom
about c moves the content at p by  d = (s - 1)(p - c) + t,  linear in
(s - 1, t): RANSAC on two-window samples keeps the windows that agree on one
similarity, the scale is the least-squares fit on those inliers.  It is fitted
twice from the same field: over every window (`camera`) and over the windows
within RADIUS of the centre (`ratio`), because the plan centres the frame on
the thing it pushes in on, and that thing is what the reviewer sizes.  A step
that reads over SPLIT is re-read through its middle frame so every phase
correlation stays inside its window; the steps compound into the ratio.

WHY THE SUBJECT AND NOT THE WHOLE FRAME.  On T12, T25 and T33 the model walks
the man at the lens: the room zooms less than he grows.  The whole-frame fit
lets the wall behind him vote and reads under the subject fit on exactly the
over-pushed takes (T12 1.80 vs 1.98, T33 1.44 vs 1.52) and over it on a fine
one (T09 1.55 vs 1.48).  Against the reviewer's labels the whole-frame read
separates by -0.11 (T33 1.44 under T14 1.47, T09 1.55); the subject read by
+0.02.  Both are reported; the subject read is judged.

CALIBRATION (episode 10, 768x768, the shipped settings, 2026-09-16; two-shot
takes read up to their internal pin; `attempts/` holds the superseded
renders).  The reviewer's frame strips: over-pushed = T05 first render
(nostrils), T12, T13, T16, T25, T28, T33; fine = T07, T08, T09, T14, T21, T24,
T27.

    take        planned    ratio (subject)  camera   reviewer
    T16         forearm      2.40           2.35     over-pushed
    T13         hand         2.16           2.06     over-pushed
    T25         hand         2.12           2.05     over-pushed
    T12         stride       1.98           1.80     over-pushed
    T05_fail1   hand         1.93           1.91     over-pushed (nostrils)
    T28         hand         1.63           1.59     over-pushed
    T33         stride       1.52           1.44     over-pushed
    ------------------------------------------------ OVER_PUSH 1.55
    T14         hand         1.50           1.47     fine
    T09         hand         1.48           1.55     fine
    T21         stride       1.47           1.44     fine
    T07         forearm      1.46           1.44     fine
    T24         hand         1.37           1.36     fine
    T08         hand         1.28           1.26     fine
    T27         hand         1.26           1.24     fine

Every fine take is under 1.55; six of the seven over-pushed takes are over
it and the seventh, T33 at 1.52, is under it by 0.03.  The margin is +0.08
(T28 1.63) above and -0.05 (T14 1.50) below, and the read-to-read noise across
the lattice settings swept is about +-0.05, so this is a fit to fourteen
labelled takes, not a separation.  The
wall is honest only for the reach it applies to: T33 and T12 were planned as a
stride, which REACH_WALLS allows up to OVER_PUSH_LONG, so T33 is NOT caught by
the verdict and T12 sits 0.02 under its wall.  Six of the seven over-pushed
takes (all but T33) read >= 1.63 and every fine take <= 1.50; the strong cases
(>= 1.9) are clear by 0.4.  Full table, sweep and unlabelled flags:
docs/calibration/take_zoom.md.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

# ---- the walls (see docs/calibration/take_zoom.md) ----------------------------
OVER_PUSH = 1.55           # a hand's / a finger's breadth, measured this tight: hard
OVER_PUSH_LONG = 2.0       # a forearm or a long stride allows up to here
OVER_PUSH_ANY = 2.5        # over this it is hard whatever was planned
ADVISORY_PUSH = 1.4        # a hand's breadth that read this far: worth a look
WRONG_WAY = 1.15           # moved the other way by this much: advisory

# ---- the measure ---------------------------------------------------------------
GRID = 9                   # window centres per axis; windows are 2 strides wide
RADIUS = 0.35              # the subject: windows within this fraction of min(h, w) of the centre
MIN_INLIERS = 8            # fewer windows agreeing than this: not measured
RANSAC_ITERS = 300
INLIER_FRAC = 0.01         # residual under this fraction of min(h, w) is an inlier
TEXTURE = 3.0              # a window whose grey std is under this has nothing to match
STILL = 0.01               # |s - 1| under this is not a move
SPLIT = 1.07               # a step over this is re-read through its middle frame
SAMPLES = 12               # 6 reads T12 at 1.59 on 8 inliers; 12 reads 1.98 on 17
FRAME_EXT = (".png", ".jpg", ".jpeg")

REACH_WALLS = {"finger": OVER_PUSH, "hand": OVER_PUSH, "forearm": OVER_PUSH_LONG,
               "stride": OVER_PUSH_LONG, None: OVER_PUSH_ANY}


# ---- decoding ------------------------------------------------------------------

def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # pragma: no cover - the lock pins imageio-ffmpeg
        return "ffmpeg"


def probe_size(video: Path) -> tuple[int, int]:
    """(width, height) from the first frame; no ffprobe needed."""
    import io
    png = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", str(video), "-frames:v", "1", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).size


def decode(video: Path, end_frame: int | None = None) -> np.ndarray:
    """Grey frames (n, h, w) uint8 at native size and fps, the first end_frame only."""
    w, h = probe_size(video)
    cut = ["-frames:v", str(end_frame)] if end_frame else []
    raw = subprocess.run([ffmpeg_exe(), "-v", "error", "-i", str(video), *cut, "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w)


def read_dir(folder: Path, end_frame: int | None = None) -> np.ndarray:
    """Grey frames from a folder of images, in name order."""
    names = sorted(p for p in folder.iterdir() if p.suffix.lower() in FRAME_EXT)[:end_frame]
    return np.stack([np.asarray(Image.open(p).convert("L")) for p in names])


def load_frames(path: Path, end_frame: int | None = None) -> np.ndarray:
    path = Path(path)
    return read_dir(path, end_frame) if path.is_dir() else decode(path, end_frame)


def sample_indices(n: int, samples: int) -> list[int]:
    """`samples` frame indices spread evenly over n frames, first and last included."""
    return sorted(set(int(round(x)) for x in np.linspace(0, n - 1, max(2, min(samples, n)))))


# ---- one step: the displacement field and its similarity ----------------------

def lattice(h: int, w: int) -> tuple[np.ndarray, int]:
    """GRID x GRID window centres (N, 2) as (y, x), and the (even) window size."""
    stride = min(h, w) / (GRID + 1)
    ys = np.linspace(stride, h - stride, GRID)
    xs = np.linspace(stride, w - stride, GRID)
    centres = np.array([(y, x) for y in ys for x in xs])
    return centres, int(2 * stride) // 2 * 2


def hann(size: int) -> np.ndarray:
    win = np.hanning(size)
    return np.outer(win, win)


def subpixel(r: np.ndarray, peak: tuple[int, int]) -> tuple[float, float]:
    """Parabolic refinement of a wrapped peak location; the shift as (dy, dx)."""
    n = r.shape[0]
    out = []
    for axis, k in enumerate(peak):
        line = np.take(r, [(k - 1) % n, k, (k + 1) % n], axis=axis)
        a, b, c = line[:, peak[1]] if axis == 0 else line[peak[0], :]
        denom = a - 2 * b + c
        off = 0.5 * (a - c) / denom if abs(denom) > 1e-9 else 0.0
        out.append(((k + off + n / 2) % n) - n / 2)
    return out[0], out[1]


def shift(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Phase correlation: where the content of window a lies in window b, (dy, dx)."""
    win = hann(a.shape[0])
    fa = np.fft.fft2((a - a.mean()) * win)
    fb = np.fft.fft2((b - b.mean()) * win)
    cross = fb * np.conj(fa)
    r = np.real(np.fft.ifft2(cross / (np.abs(cross) + 1e-9)))
    peak = np.unravel_index(int(np.argmax(r)), r.shape)
    return subpixel(r, (int(peak[0]), int(peak[1])))


def flow(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Points (N, 2) and displacements (N, 2) of every textured window from a to b."""
    centres, size = lattice(*a.shape)
    af, bf = a.astype(np.float32), b.astype(np.float32)
    pts, disp = [], []
    for cy, cx in centres:
        y0, x0 = int(round(cy - size / 2)), int(round(cx - size / 2))
        wa, wb = af[y0:y0 + size, x0:x0 + size], bf[y0:y0 + size, x0:x0 + size]
        if wa.std() < TEXTURE or wb.std() < TEXTURE:
            continue
        pts.append((cy, cx))
        disp.append(shift(wa, wb))
    return np.array(pts).reshape(-1, 2), np.array(disp).reshape(-1, 2)


def fit_similarity(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray) -> np.ndarray:
    """Least squares (s - 1, ty, tx) for  d = (s - 1)(p - c) + t."""
    rel = pts - centre
    rows = np.zeros((2 * len(pts), 3))
    rows[0::2, 0], rows[0::2, 1] = rel[:, 0], 1.0
    rows[1::2, 0], rows[1::2, 2] = rel[:, 1], 1.0
    sol, *_ = np.linalg.lstsq(rows, disp.reshape(-1), rcond=None)
    return sol


def residuals(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray, sol: np.ndarray) -> np.ndarray:
    pred = sol[0] * (pts - centre) + sol[1:]
    return np.linalg.norm(disp - pred, axis=1)


def ransac(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray, tol: float) -> np.ndarray:
    """The largest set of windows that agree on one similarity, as a boolean mask."""
    rng = np.random.default_rng(0)
    best = np.zeros(len(pts), bool)
    if len(pts) < 2:
        return best
    for _ in range(RANSAC_ITERS):
        pick = rng.choice(len(pts), 2, replace=False)
        sol = fit_similarity(pts[pick], disp[pick], centre)
        mask = residuals(pts, disp, centre, sol) < tol
        if mask.sum() > best.sum():
            best = mask
    return best


def fit_field(pts: np.ndarray, disp: np.ndarray, centre: np.ndarray, tol: float) -> tuple[float, int]:
    """The scale the field agrees on and how many windows agreed (1.0 when too few)."""
    inliers = ransac(pts, disp, centre, tol)
    if inliers.sum() < MIN_INLIERS:
        return 1.0, int(inliers.sum())
    sol = fit_similarity(pts[inliers], disp[inliers], centre)
    return float(1.0 + sol[0]), int(inliers.sum())


def step_fields(a: np.ndarray, b: np.ndarray) -> tuple[tuple[float, int], tuple[float, int]]:
    """((subject scale, inliers), (camera scale, inliers)) from one displacement field:
    the subject is the windows within RADIUS of the centre, the camera is all of them."""
    pts, disp = flow(a, b)
    centre = np.array(a.shape, float) / 2
    tol = INLIER_FRAC * min(a.shape)
    near = np.all(np.abs(pts - centre) <= RADIUS * min(a.shape), axis=1)
    return fit_field(pts[near], disp[near], centre, tol), fit_field(pts, disp, centre, tol)


def step_scale(a: np.ndarray, b: np.ndarray) -> tuple[float, int]:
    """The subject's scale from frame a to frame b and the number of windows that agreed."""
    return step_fields(a, b)[0]


def step_between(frames: np.ndarray, i: int, j: int, depth: int = 4) -> tuple[tuple[float, int], tuple[float, int]]:
    """Subject and camera scales from frame i to frame j; a large step is read
    through its middle frame so that every phase correlation stays inside its window."""
    (s, n), cam = step_fields(frames[i], frames[j])
    mid = (i + j) // 2
    if depth == 0 or mid in (i, j) or (n >= MIN_INLIERS and abs(s - 1) < SPLIT - 1):
        return (s, n), cam
    (s1, n1), (c1, m1) = step_between(frames, i, mid, depth - 1)
    (s2, n2), (c2, m2) = step_between(frames, mid, j, depth - 1)
    return (s1 * s2, min(n1, n2)), (c1 * c2, min(m1, m2))


# ---- the take ------------------------------------------------------------------

def is_monotonic(per_step: list[float]) -> bool:
    """Every step beyond STILL goes the same way (no step at all counts as True)."""
    signs = {np.sign(s - 1) for s in per_step if abs(s - 1) >= STILL}
    return len(signs) <= 1


def compound(steps: list[tuple[float, int]]) -> tuple[float, bool]:
    """(product of the step scales, every step had MIN_INLIERS); 1.0 when not."""
    measured = bool(steps) and min(n for _, n in steps) >= MIN_INLIERS
    return (float(np.prod([s for s, _ in steps])) if measured else 1.0), measured


def zoom_frames(frames: np.ndarray, samples: int = SAMPLES) -> dict:
    """The zoom of an (n, h, w) grey clip already in memory."""
    idx = sample_indices(len(frames), samples)
    subject, camera = [], []
    for i, j in zip(idx, idx[1:]):
        s, c = step_between(frames, i, j)
        subject.append(s)
        camera.append(c)
    ratio, measured = compound(subject)
    cam, _ = compound(camera)
    return {"ratio": ratio, "monotonic": is_monotonic([s for s, _ in subject]), "measured": measured,
            "per_step": [float(s) for s, _ in subject], "inliers": [n for _, n in subject],
            "camera": cam, "camera_steps": [float(s) for s, _ in camera], "frames": idx}


def zoom(video: Path, samples: int = SAMPLES, end_frame: int | None = None) -> dict:
    """The zoom of a take on disk (an mp4, or a folder of frames), the first
    end_frame frames only -- a two-shot take is read up to its internal pin."""
    return zoom_frames(load_frames(video, end_frame), samples)


# ---- the verdict ---------------------------------------------------------------

REACH_WORDS = ("finger", "hand", "forearm", "stride")


def planned_reach(motion: str) -> str | None:
    """The camera's reach word from the plan's motion string: the 'travelling ...'
    phrase first, else the first reach word anywhere in it."""
    text = motion.lower()
    m = re.search(r"travelling (?:a|an|one)?\s*([a-z' ]+?)(?:[;,.]|$)", text)
    scope = m.group(1) if m else text
    for word in REACH_WORDS:
        if word in scope:
            return word
    return next((w for w in REACH_WORDS if w in text), None)


def planned_direction(motion: str) -> int:
    """+1 for a push in, -1 for a pull back / dolly out."""
    return -1 if re.search(r"pulls? (?:back|out|away)|dolly out|dollies out", motion.lower()) else 1


def judge(ratio: float, planned: str, measured: bool = True, monotonic: bool = True) -> dict:
    """Hard when the measured travel in the planned direction is over the wall for
    the planned reach, or over OVER_PUSH_ANY whatever was planned."""
    reach, direction = planned_reach(planned), planned_direction(planned)
    wall = REACH_WALLS[reach]
    travel = ratio if direction > 0 else 1.0 / max(ratio, 1e-6)   # in the planned direction
    size = max(ratio, 1.0 / max(ratio, 1e-6))                     # either direction
    hard, advisory = [], []
    if not measured:
        advisory.append("zoom not measured: too few windows agreed on one camera move")
    elif size >= wall:
        hard.append(f"planned {reach or 'push'} travelled {ratio:.2f}x, over the {wall:.2f}x wall")
    elif reach in ("finger", "hand") and travel >= ADVISORY_PUSH:
        advisory.append(f"planned {reach} travelled {ratio:.2f}x, near the {wall:.2f}x wall")
    if measured and travel < 1.0 / WRONG_WAY:
        advisory.append(f"planned {'push' if direction > 0 else 'pull-back'} but the picture read {ratio:.2f}x")
    if measured and not monotonic and size >= ADVISORY_PUSH:   # a flip inside the noise band is not a reversal
        advisory.append("the zoom reversed mid-take")
    return {"ok": not hard, "hard": hard, "advisory": advisory, "ratio": ratio, "planned": reach}


# ---- the seat in the take gate ----------------------------------------------

ZOOM_PENALTY = 15.0            # over the wall: points off, never a FAIL (see row)
ZOOM_ADVISORY_PENALTY = 5.0    # near the wall, or the picture went the other way


def head_frame(anchors: list) -> int | None:
    """The frame of a take's second anchor: the zoom reads the first shot only,
    because the internal cut is a planned scale change, not a push."""
    return int(anchors[1][1]) if len(anchors) > 1 else None


def row(z: dict, planned: str):
    """The verdict row: a SCORED ADVISORY over the wall for the planned reach,
    quiet when unmeasured, like the identity row.

    Never hard, MEASURED on the ep10 re-read: the wall at 1.55 failed six takes
    in the cut, and four of them (T13 2.16, T16 2.40, T17 1.73, T25 2.12) were
    the reviewer's KEEPs -- a size tighter than planned with the face whole.
    T05's nostrils at 1.93 read the same as T13's whole face at 2.16: scale
    separates pushed from not pushed, not usable from not. The points rank the
    attempts (best-of-N prefers the take that held its size); the FAIL waits
    for a face-in-frame read."""
    from studio.take_verdict import Gate
    if not z:
        return Gate("zoom", None, True, False, "not measured")
    v = judge(z["ratio"], planned, z.get("measured", True), z.get("monotonic", True))
    hard, advisory = bool(v["hard"]), bool(v["advisory"])
    note = f"{z['ratio']:.2f}x {v['planned'] or 'push'}"
    penalty = ZOOM_PENALTY if hard else (ZOOM_ADVISORY_PENALTY if advisory and z.get("measured", True) else 0.0)
    return Gate("zoom", z["ratio"], not hard and not advisory, False, note, penalty)
