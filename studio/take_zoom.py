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
OVER_PUSH_STRIDE = 1.6
"""A stride's wall.  Was OVER_PUSH_LONG (2.0): ep10 T12 planned a stride and
pushed 1.98x -- a medium to a close, the reviewer's WATCH -- and sat 0.02
under it, while T33 1.52 / T21 1.47 / T31 1.43 / T06 1.14 (KEEPs) all read
under 1.6.  Margin +0.38 above, -0.08 below (analyst H, ep10)."""
OVER_PUSH_LONG = 2.0       # a forearm allows up to here
OVER_PUSH_ANY = 2.5        # over this it is hard whatever was planned
ADVISORY_PUSH = 1.4        # a hand's breadth that read this far: worth a look
WRONG_WAY = 1.15           # moved the other way by this much: advisory
NO_MOVE = 0.05
"""|ratio - 1| under this with a push or a pull-back planned: the move did not
happen.  ep10 T05's current render planned a pull-back and read 0.99x at
100/100 -- `judge` knew the wrong way and not the no way (analyst B)."""
CAMERA_FOLLOW = 0.3
"""camera - ratio at or over this: the frame travelled further than the subject
grew, i.e. the camera FOLLOWED the subject.  ep10 T06: the whole frame read
1.57x while the subject fit read 1.14x because the men's backs fill the
centre; the plan asked one stride and the frame ended inside the doorway.
T29 s1 (1.59 vs 1.31, 0.28) sits just under the line."""
EXIT_FIELD = 0.75
"""A planned exit (`has_exit`) is read only to the step where the subject
field breaks up: the first step whose agreeing windows fall under this
fraction of the segment's opening step.  MEASURED on ep10 T17 (the only exit
clause in the episode): the steps agreed on 48 47 47 49 47 49 42, then 21 and
13 as the fist left the boards behind it.  Margin: 42 above the 36 floor, 21
below.  The on-board cosine cap the analyst proposed does NOT do this on its
own -- the boards behind the fist ARE the cell, so the frame stays on-board
until frame 119 and the read to there is 1.71x; to the field break it is
1.47x, the reviewer's "push ~1.3x by frame 4".  Both caps apply; the earlier
governs (`exit_cap`).  n = 1; ep11 confirms or moves it."""

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
               "stride": OVER_PUSH_STRIDE, None: OVER_PUSH_ANY}


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


# ---- per segment, and the planned exit ------------------------------------------

def spans(anchors: list, n: int) -> list[tuple[int, int]]:
    """(start, end) frames of every anchor segment of an n-frame take: the START
    pins in order, END pins folded into their segment, the last span to n."""
    starts = sorted({int(f) for name, f in anchors if not str(name).endswith("E.png")} | {0})
    starts = [f for f in starts if f < n]
    return list(zip(starts, starts[1:] + [n]))


def field_break(inliers: list[int]) -> int:
    """The first step whose agreeing windows fall under EXIT_FIELD of the opening
    step's -- where the subject stops moving as one picture -- else len(inliers)."""
    if not inliers:
        return 0
    floor = EXIT_FIELD * inliers[0]
    return next((k for k, n in enumerate(inliers) if n < floor), len(inliers))


def exit_cap(z: dict, onboard_last: int | None) -> dict:
    """A segment whose subject was TOLD to leave the frame, read only up to the
    earlier of the field break and the last on-board sample; the full read is
    kept as `full_ratio`, the cap frame as `exit_at`.  See EXIT_FIELD."""
    k = field_break(z["inliers"])
    if onboard_last is not None:
        k = min(k, sum(f <= onboard_last for f in z["frames"]) - 1)
    k = max(k, 0)
    kept = list(zip(z["per_step"][:k], z["inliers"][:k]))
    ratio, measured = compound(kept)
    cam, _ = compound(list(zip(z["camera_steps"][:k], z["inliers"][:k])))
    return z | {"ratio": ratio, "camera": cam, "measured": measured, "monotonic": is_monotonic([s for s, _ in kept]),
                "exit_at": z["frames"][k], "full_ratio": z["ratio"]}


def zoom_take(video: Path, anchors: list, samples: int = SAMPLES,
              onboard_last: list[int | None] | None = None) -> dict:
    """The zoom of every anchor segment of a take, the head's read at the top
    level (the record's readers expect it there) and all of them under
    `segments`.  `onboard_last[k]`, when given, caps segment k as a planned
    exit (`exit_cap`).  The head-only read judged a two-shot take's second
    shot by nothing (ep10 T29 s2's full turn-away, analyst B)."""
    frames = load_frames(video)
    caps = list(onboard_last or [])
    segs = []
    for k, (a, b) in enumerate(spans(anchors, len(frames))):
        z = zoom_frames(frames[a:b], samples)
        z["frames"] = [f + a for f in z["frames"]]
        if k < len(caps) and caps[k] is not None:
            z = exit_cap(z, caps[k])
        segs.append(z | {"start": a, "end": b})
    return dict(segs[0]) | {"segments": segs}


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


def planned_move(motion: str) -> bool:
    """Did the plan ask for a scale change at all -- a push in or a pull back?"""
    return bool(re.search(r"push\w* in|pull\w* (?:back|out|away)|doll(?:y|ies)\b", motion.lower()))


def has_exit(motion: str) -> bool:
    """Does a clause of the motion send its subject OUT of the frame?  Then the
    last frame is not the cell's picture by instruction (ep10 T17: "the fist
    drops out of the bottom of the frame" -- bare boards, 25 points lost)."""
    return bool(re.search(r"drops? out of the (?:frame|bottom|top)|out of the (?:bottom|top) of the frame"
                          r"|leaves the frame|goes out of the frame", motion.lower()))


def planned_phrase(reach: str | None, direction: int) -> str:
    """'planned pull-back of a hand', 'planned push' -- the subject of every sentence."""
    verb = "push" if direction > 0 else "pull-back"
    return f"planned {verb} of a {reach}" if reach else f"planned {verb}"


def reach_verdict(ratio: float, travel: float, reach: str | None, direction: int, exit: bool) -> tuple[list, list]:
    """The wall for the planned reach: hard over it; near it, advisory -- except
    on an exit segment, where the approach that precedes the exit is the
    planned action and the near-wall band sits inside the subject's own move."""
    wall, what = REACH_WALLS[reach], planned_phrase(reach, direction)
    size, seen = max(ratio, 1.0 / max(ratio, 1e-6)), "pushed in" if ratio > 1 else "pulled back"
    if size >= wall and travel >= 1.0:
        return [f"{what} travelled {travel:.2f}x, over the {wall:.2f}x wall"], []
    if size >= wall:
        return [f"{what} but the picture {seen} {size:.2f}x, over the {wall:.2f}x wall"], []
    if reach in ("finger", "hand") and travel >= ADVISORY_PUSH and not exit:
        return [], [f"{what} travelled {travel:.2f}x, near the {wall:.2f}x wall"]
    return [], []


def move_advisories(ratio: float, travel: float, planned: str, direction: int,
                    camera: float | None, monotonic: bool) -> list[str]:
    """The wrong way, the no way, the camera that followed, the reversal."""
    what, size = planned_phrase(planned_reach(planned), direction), max(ratio, 1.0 / max(ratio, 1e-6))
    out = []
    if travel < 1.0 / WRONG_WAY:
        out.append(f"{what} travelled {travel:.2f}x its own way: the picture "
                   f"{'pushed in' if ratio > 1 else 'pulled back'} {size:.2f}x")
    if planned_move(planned) and abs(ratio - 1.0) < NO_MOVE:
        out.append(f"{what} but the picture did not move ({ratio:.2f}x)")
    if camera is not None and camera - ratio >= CAMERA_FOLLOW:
        out.append(f"the camera followed the subject: the frame travelled {camera:.2f}x while the subject read {ratio:.2f}x")
    if not monotonic and size >= ADVISORY_PUSH:   # a flip inside the noise band is not a reversal
        out.append("the zoom reversed mid-take")
    return out


def judge(ratio: float, planned: str, measured: bool = True, monotonic: bool = True,
          camera: float | None = None, exit: bool = False) -> dict:
    """Hard when the measured travel is over the wall for the planned reach, or
    over OVER_PUSH_ANY whatever was planned; every sentence reports travel in
    the PLANNED direction (a pull-back to 0.54x is 1.85x of travel)."""
    reach, direction = planned_reach(planned), planned_direction(planned)
    travel = ratio if direction > 0 else 1.0 / max(ratio, 1e-6)   # in the planned direction
    if not measured:
        hard, advisory = [], ["zoom not measured: too few windows agreed on one camera move"]
    else:
        hard, advisory = reach_verdict(ratio, travel, reach, direction, exit)
        advisory += move_advisories(ratio, travel, planned, direction, camera, monotonic)
    return {"ok": not hard, "hard": hard, "advisory": advisory, "ratio": ratio, "planned": reach}


# ---- the seat in the take gate ----------------------------------------------

ZOOM_PENALTY = 15.0            # over the wall: points off, never a FAIL (see row)
ZOOM_ADVISORY_PENALTY = 5.0    # near the wall, or the picture went the other way


def head_frame(anchors: list) -> int | None:
    """The frame of a take's second anchor -- where the head segment ends.  The
    gate now reads every segment (`zoom_take`); this stays for callers that
    want the head alone, because the internal cut is a planned scale change,
    not a push, and must never be read as one."""
    return int(anchors[1][1]) if len(anchors) > 1 else None


def segment_row(z: dict, planned: str, k: int, n: int):
    """One segment's verdict as a Gate: its own plan, its own camera read, its
    own exit clause; the note names the segment when the take has several."""
    from studio.take_verdict import Gate
    exit = has_exit(planned)
    v = judge(z["ratio"], planned, z.get("measured", True), z.get("monotonic", True), z.get("camera"), exit)
    hard, advisory = bool(v["hard"]), bool(v["advisory"])
    note = (f"s{k + 1} " if n > 1 else "") + f"{z['ratio']:.2f}x {v['planned'] or 'push'}"
    note += " pull-back" if planned_direction(planned) < 0 else ""
    note += f" to exit f{z['exit_at']}" if "exit_at" in z else ""
    penalty = ZOOM_PENALTY if hard else (ZOOM_ADVISORY_PENALTY if advisory and z.get("measured", True) else 0.0)
    return Gate("zoom", z["ratio"], not hard and not advisory, False, note, penalty)


def row(z: dict, planned: str | list[str]):
    """The verdict row: a SCORED ADVISORY over the wall for the planned reach,
    quiet when unmeasured, like the identity row.  Every anchor segment is
    judged against its own shot's motion (`planned` may be one string for the
    whole take or one per segment) and the WORST segment is the row.

    Never hard, MEASURED on the ep10 re-read: the wall at 1.55 failed six takes
    in the cut, and four of them (T13 2.16, T16 2.40, T17 1.73, T25 2.12) were
    the reviewer's KEEPs -- a size tighter than planned with the face whole.
    T05's nostrils at 1.93 read the same as T13's whole face at 2.16: scale
    separates pushed from not pushed, not usable from not. The points rank the
    attempts (best-of-N prefers the take that held its size); the FAIL waits
    for the face-at-end row."""
    from studio.take_verdict import Gate
    if not z:
        return Gate("zoom", None, True, False, "not measured")
    segs = z.get("segments") or [z]
    plans = list(planned) if isinstance(planned, list) else [planned]
    plans = (plans or [""]) + [(plans or [""])[-1]] * len(segs)
    rows = [segment_row(s, p, k, len(segs)) for k, (s, p) in enumerate(zip(segs, plans))]
    return max(rows, key=lambda g: (g.penalty, not g.ok))



def is_pan(motion) -> bool:
    """True when the motion's head clause is a pan or a tilt (the camera reveals
    picture beyond the cell by design, so off-board gets its wider wall)."""
    head = (motion[0] if isinstance(motion, (list, tuple)) and motion else motion) or ""
    head = str(head).split(";")[0].lower()
    return bool(re.search(r"\bcamera (?:pans|tilts)\b", head))
