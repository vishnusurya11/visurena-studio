"""SFX on the measured moment: a planned sound laid on the frame its event happens.

The plan names a shot's sound and a rough time (`Sound.at`, seconds into the
shot); `sfx_cues.placed` laid the render there, so a boot or a door landed
wherever the writer guessed.  The 2026-10-16 battery (F1-F3, Jekyll ep01) put a
Stable Audio 3 cue on a HAND-MARKED visual onset and it landed within 4 ms (T06)
and 41-57 ms (T09); free-running footsteps drifted 200-280 ms by the third step.
This module replaces the hand: it MEASURES the take.

WHAT IT LOOKS FOR (`kind_of`, from the sound's own words):
  steps   footsteps, heels, strides: a heel strike is the walker's widest stride,
          so each peak of the walker's box width is one step (Jekyll ep01 T03:
          -30/-1/+19 ms on the three marked strikes inside the take).
  motion  one event made by a body or a thing (a key, a stamp, a door): the
          strongest peak of camera-compensated motion around the people within
          WINDOW_S of the planned time (T06 stamp +44 ms, T09 key +49, door +5).
  ''      a voice, a crowd, the weather: nothing in the frame times it; the
          planned time stands.
The camera is removed by subtracting the frame's median flow; H3's repeated
frames (every second or third) are bridged by a 3-frame running max.

HOW IT LAYS: a motion cue is shifted so ITS OWN first onset hits the event; a
footsteps render is cut into its steps and one step is laid per measured strike
(cycling through the render's steps).  A cue the picture cannot time keeps its
planned time and says why (`fallback`), so a missing measurement never moves or
drops a sound.  `REPORT` records every placement; QC reads the measured starts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

import numpy as np

FPS = 24
SIZE = 384
"""Frames are read square at this size (the gait reader's)."""
WINDOW_S = 0.75
"""How far from the planned time a single event is looked for."""
STEP_GAP, MOTION_GAP = 5, 4
"""Frames between two peaks of one kind (a step is >= 0.2 s; a motion beat >= 0.17 s)."""
STRIDE_PROMINENCE, MOTION_PROMINENCE = 0.02, 0.05
"""A peak's rise over its neighbourhood, as a share of the curve's median."""
PRE_ROLL = 0.01
"""Seconds kept before a step slice's onset, so its attack is not clipped."""
SLICE_MAX = 0.6
"""Longest step slice: a heel's ring, not the next step."""
REPORT = "onsets.json"

STEPS = re.compile(r"\b(?:foot ?steps?|footfalls?|heels?|treads?|strid\w*|walking|marching|"
                   r"boots? (?:on|striking|strike|clatter\w*|ring\w*|crunch\w*))\b", re.I)
UNSEEN = re.compile(r"\b(?:scream\w*|shout\w*|cry|cries|crying|sob\w*|voices?|whisper\w*|laugh\w*|calls?|"
                    r"calling|ambien\w*|wind|rain|crowds?|murmur\w*|music|bells?|toll\w*|distant|thunder\w*)\b", re.I)


def kind_of(sound: str) -> str:
    """'steps', 'motion' or '' (nothing on screen times it)."""
    if STEPS.search(sound):
        return "steps"
    return "" if UNSEEN.search(sound) else "motion"


# ---------------------------------------------------------------- the people

def iou(a, b) -> float:
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def _follow(tracks: list[dict], k: int, box) -> dict | None:
    """The live track (seen in the last 3 frames, not yet at k) this box continues."""
    live = [t for t in tracks if k not in t and max(t) >= k - 3]
    best = max(live, key=lambda t: iou(t[max(t)], box), default=None)
    return best if best is not None and iou(best[max(best)], box) > 0.3 else None


def tracks(boxes: list[list]) -> list[dict]:
    """Person boxes per frame linked into tracks {frame: box} by overlap."""
    out: list[dict] = []
    for k, frame in enumerate(boxes):
        for box in sorted(frame, key=lambda b: -b[4]):
            track = _follow(out, k, box)
            if track is None:
                out.append({k: box})
            else:
                track[k] = box
    return out


def travel(track: dict, pan) -> float:
    """Pixels the track's centre crossed against the camera's own pan."""
    ks = sorted(track)
    centre = {k: (track[k][0] + track[k][2]) / 2 for k in ks}
    return float(sum(abs(centre[b] - centre[a] - float(np.sum(pan[a + 1:b + 1]))) for a, b in zip(ks, ks[1:])))


def walker(all_tracks: list[dict], pan) -> dict | None:
    """The track that crosses the most ground (a long-lived one): the walker, not the biggest."""
    long = [t for t in all_tracks if len(t) >= 12]
    return max(long, key=lambda t: travel(t, pan), default=None)


def widths(track: dict | None, n: int) -> np.ndarray:
    """The walker's box width per frame; NaN where he is not found."""
    return np.array([(track[k][2] - track[k][0]) if track and k in track else np.nan for k in range(n)])


# ---------------------------------------------------------------- the curves

def smooth(x, k: int = 3) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = np.where(np.isnan(x), np.nanmedian(x) if np.isfinite(x).any() else 0.0, x)
    return np.convolve(np.pad(x, k // 2, mode="edge"), np.ones(k) / k, mode="valid")


def envelope(x, k: int = 3) -> np.ndarray:
    """A running max then a mean: H3's repeated frames are not events."""
    x = np.asarray(x, dtype=float)
    top = np.array([np.max(x[max(0, i - k // 2):i + k // 2 + 1]) for i in range(len(x))])
    return smooth(top, k)


def _refine(x: np.ndarray, i: int) -> float:
    """Sub-frame position of a peak at i (parabola through three samples)."""
    a, b, c = x[i - 1], x[i], x[i + 1]
    den = a - 2 * b + c
    return i + (float(np.clip((a - c) / (2 * den), -0.5, 0.5)) if den else 0.0)


def peaks(x, gap: int = STEP_GAP, prominence: float = STRIDE_PROMINENCE) -> list[float]:
    """Local maxima at least `gap` frames apart, risen `prominence` x median over their neighbourhood."""
    x = np.asarray(x, dtype=float)
    floor, out = abs(float(np.median(x))) or 1e-9, []
    for i in range(1, len(x) - 1):
        near = x[max(0, i - gap):i + gap + 1]
        if x[i] >= near.max() and x[i] - near.min() > prominence * floor and (not out or i - out[-1] >= gap):
            out.append(_refine(x, i))
    return out


def strike_times(width: np.ndarray, fps: int = FPS) -> list[float]:
    """Seconds of each heel strike: a peak of the smoothed stride width."""
    if not np.isfinite(width).any():
        return []
    return [round(p / fps, 3) for p in peaks(smooth(width), STEP_GAP, STRIDE_PROMINENCE)]


def motion_peaks(motion, fps: int = FPS) -> list[list[float]]:
    """[seconds, strength] of each peak of the bridged motion curve."""
    env = envelope(motion)
    return [[round(p / fps, 3), round(float(env[int(round(p))]), 3)]
            for p in peaks(env, MOTION_GAP, MOTION_PROMINENCE)]


def strongest_near(found: list, at: float, window: float = WINDOW_S) -> float | None:
    """The strongest motion peak within `window` of the planned time, or None."""
    near = [(t, v) for t, v in found if abs(t - at) <= window]
    return max(near, key=lambda row: row[1])[0] if near else None


def strikes_in(strikes: list[float], start: float, seconds: float) -> list[float]:
    return [t for t in strikes if start <= t <= start + seconds]


# ---------------------------------------------------------------- the render's own onsets

def levels(samples: np.ndarray, rate: int, window: float = 0.005) -> np.ndarray:
    """RMS dBFS of each `window`-second slice of a mono (or mixed-down) signal."""
    y = np.asarray(samples, dtype=np.float64)
    y = y.mean(axis=1) if y.ndim > 1 else y
    size = max(1, int(window * rate))
    n = len(y) // size
    rms = np.sqrt((y[:n * size].reshape(n, size) ** 2).mean(axis=1))
    return 20.0 * np.log10(np.maximum(rms, 1e-10))


def onsets(samples: np.ndarray, rate: int, window: float = 0.005, drop: float = 18.0,
           rearm: float = 10.0, gap: float = 0.12) -> list[float]:
    """Seconds where the level rises to within `drop` dB of the file's peak after having
    fallen `rearm` dB under that line, backtracked to the start of the rise."""
    lv = levels(samples, rate, window)
    if not len(lv):
        return []
    line, floor = lv.max() - drop, float(np.percentile(lv, 10))
    out, armed = [], True
    for i, v in enumerate(lv):
        if armed and v >= line and (not out or i * window - out[-1] >= gap):
            j = i
            while j > 0 and lv[j - 1] > floor + 6.0 and lv[j - 1] < lv[j]:
                j -= 1
            out.append(round(j * window, 4))
            armed = False
        elif v < line - rearm:
            armed = True
    return out


def first_onset(samples: np.ndarray, rate: int) -> float:
    """Where the render's sound starts (0.0 for a silent file)."""
    found = onsets(samples, rate)
    return found[0] if found else 0.0


def step_slices(src: Path, out_dir: Path) -> list[Path]:
    """A footsteps render cut into one file per step, each starting PRE_ROLL before its onset."""
    import soundfile as sf
    y, rate = sf.read(str(src), dtype="float32", always_2d=True)
    starts = onsets(y, rate)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for k, t in enumerate(starts):
        end = min(starts[k + 1] if k + 1 < len(starts) else len(y) / rate, t + SLICE_MAX)
        a, b = max(0, int((t - PRE_ROLL) * rate)), int(end * rate)
        piece = y[a:b].copy()
        fade = min(len(piece), int(0.02 * rate))
        piece[len(piece) - fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
        path = out_dir / f"{Path(src).stem}_step{k:02d}.wav"
        sf.write(str(path), piece, rate)
        out.append(path)
    return out


# ---------------------------------------------------------------- the clock

def master_time(event: float, run_start: float, head: float) -> float:
    """Take seconds -> master seconds: the take plays from its head at its run's start."""
    return round(run_start + event - head, 4)


def shot_in_take(shot: int, run: list[int], rows: dict, head: float) -> float:
    """Where a shot starts inside its take: the head plus the earlier shots of the run."""
    before = run[:run.index(shot)] if shot in run else []
    return round(head + sum(float(rows[i]["seconds"]) for i in before), 4)


def cue_start(event_master: float, onset: float) -> float:
    """Where the file starts so its own onset lands on the event."""
    return round(event_master - onset, 4)


# ---------------------------------------------------------------- laying one cue

def _planned(cue, wav: Path, rows: dict, row: dict, why: str):
    """The cue where the plan put it (sfx_cues.placed), with the reason it was not measured."""
    from studio import sfx_cues
    laid = sfx_cues.placed([(cue, Path(wav))], list(rows.values()))
    return laid, {**row, "fallback": why, "starts": [t for t, _ in laid]}


def _laid_motion(cue, wav: Path, rows: dict, offset: float, curves: dict, row: dict):
    import soundfile as sf
    event = strongest_near(curves.get("motion") or [], offset + cue.at)
    if event is None:
        return _planned(cue, wav, rows, row, f"no motion peak within {WINDOW_S} s of the planned time")
    y, rate = sf.read(str(wav), dtype="float32")
    at = cue_start(float(rows[cue.shot]["t_start"]) + event - offset, first_onset(y, rate))
    return [(at, Path(wav))], {**row, "event_take_s": event, "starts": [at]}


def _laid_steps(cue, wav: Path, rows: dict, offset: float, curves: dict, row: dict, work: Path):
    room = min(cue.seconds, float(rows[cue.shot]["seconds"]) - cue.at)
    events = strikes_in(curves.get("strikes") or [], offset + cue.at, room)
    slices = step_slices(Path(wav), Path(work) / "steps" / Path(wav).stem) if events else []
    if not slices:
        return _planned(cue, wav, rows, row, "no heel strike measured inside the cue's span")
    start = float(rows[cue.shot]["t_start"]) - offset
    laid = [(round(start + t - PRE_ROLL, 4), slices[k % len(slices)]) for k, t in enumerate(events)]
    return laid, {**row, "events_take_s": events, "starts": [t for t, _ in laid]}


def place_cue(cue, wav: Path, rows: dict, take: dict | None, work: Path):
    """([(master seconds, file)], report row) for one rendered cue."""
    kind = kind_of(cue.sound)
    row = {"shot": cue.shot, "sound": cue.sound, "kind": kind, "at_plan": cue.at}
    if not kind:
        return _planned(cue, wav, rows, row, "the picture does not time this sound")
    if not take or not take.get("curves"):
        return _planned(cue, wav, rows, row, "no measured take for this shot")
    offset = shot_in_take(cue.shot, take["run"], rows, take["head"])
    if kind == "steps":
        return _laid_steps(cue, wav, rows, offset, take["curves"], row, work)
    return _laid_motion(cue, wav, rows, offset, take["curves"], row)


# ---------------------------------------------------------------- the record

def write_report(folder: Path, rows: list[dict]) -> Path:
    path = Path(folder) / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cues": rows}, indent=1), encoding="utf-8")
    return path


def measured_starts(folder: Path) -> dict[str, float]:
    """{'shot|sound': first laid start} from the last placement, {} when none."""
    path = Path(folder) / REPORT
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8")).get("cues", [])
    return {f"{r['shot']}|{r['sound']}": float(r["starts"][0]) for r in rows if r.get("starts")}


# ---------------------------------------------------------------- measuring a take

Detect = Callable[[np.ndarray], list]


def read_frames(video: Path, size: int = SIZE) -> list[np.ndarray]:
    """Every frame of a take, RGB, square at `size`."""
    import cv2
    cap, out = cv2.VideoCapture(str(video)), []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        out.append(cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (size, size), interpolation=cv2.INTER_AREA))
    cap.release()
    return out


def people_mask(shape, boxes: list) -> np.ndarray:
    """Every person box grown by 15 % sideways and 10 % up and down (hands, feet, a door edge)."""
    mask = np.zeros(shape, bool)
    for b in boxes:
        x1, y1, x2, y2 = b[:4]
        dx, dy = 0.15 * (x2 - x1), 0.10 * (y2 - y1)
        mask[max(0, int(y1 - dy)):int(y2 + dy), max(0, int(x1 - dx)):int(x2 + dx)] = True
    return mask


def residual(prev: np.ndarray, cur: np.ndarray, boxes: list) -> tuple[float, float]:
    """(camera pan in x, mean motion against the camera around the people -- or everywhere)."""
    import cv2
    a, b = (cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in (prev, cur))
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    camera = np.median(flow.reshape(-1, 2), axis=0)
    speed = np.linalg.norm(flow - camera, axis=2)
    mask = people_mask(speed.shape, boxes)
    return float(camera[0]), float(speed[mask].mean() if mask.any() else speed.mean())


def curves_of(frames: list[np.ndarray], detect: Detect, fps: int = FPS) -> dict:
    """The take's measured events: heel strikes and motion peaks, in take seconds."""
    boxes = [[[*map(float, box), float(conf)] for box, conf in detect(f)] for f in frames]
    pan, motion = [0.0], [0.0]
    for k in range(1, len(frames)):
        p, m = residual(frames[k - 1], frames[k], boxes[k])
        pan.append(p)
        motion.append(m)
    walk = walker(tracks(boxes), np.array(pan))
    return {"fps": fps, "frames": len(frames), "strikes": strike_times(widths(walk, len(frames)), fps),
            "motion": motion_peaks(motion, fps)}


def take_sha8(path: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def measured(video: Path, cache: Path, detect: Detect | None = None) -> dict | None:
    """The take's curves, cached beside the cues by the take's bytes; None without a detector."""
    path, sha = Path(cache) / f"{Path(video).stem}.json", take_sha8(video)
    if path.exists() and (hit := json.loads(path.read_text(encoding="utf-8"))).get("take_sha8") == sha:
        return hit
    if detect is None:
        from studio import gait
        detect = gait.yolo()
    if detect is None:
        return None
    got = {**curves_of(read_frames(video), detect), "take_sha8": sha}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(got, indent=1), encoding="utf-8")
    return got


# ---------------------------------------------------------------- the episode

TAKES, LAYOUT = Path("takes") / "r2v", Path("takes") / "work" / "layout.json"
"""The r2v takes, and where assemble's `picture` wrote each take's head, slow and still."""


def _json(path: Path, default):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


def runs_of(home: Path) -> dict[int, list[int]]:
    """{take index: the shots it plays} from the takes' shots.json."""
    return {int(r["index"]): [int(s) for s in (r.get("shots") or [r["index"]])]
            for r in _json(Path(home) / TAKES / "shots.json", [])}


def layout_of(home: Path) -> dict[int, dict]:
    """{take index: its layout row}; without the cut's layout, the written heads alone."""
    rows = _json(Path(home) / LAYOUT, None)
    if rows is not None:
        return {int(r["index"]): r for r in rows}
    from studio import edit_gate
    return {i: {"index": i, "head": h, "slow": 1.0, "still": False} for i, h in edit_gate.heads_in(home).items()}


def takes_for(home: Path, shots: list[int], measure: Callable[[Path], dict | None]) -> dict[int, dict]:
    """{shot: {"run", "head", "curves"}} for each shot whose take plays at its own speed."""
    runs, layout, out = runs_of(home), layout_of(home), {}
    for shot in shots:
        index = next((i for i, run in runs.items() if shot in run), None)
        row = layout.get(index, {"head": 0.0, "slow": 1.0, "still": False}) if index is not None else None
        video = Path(home) / TAKES / f"T{index:02d}.mp4" if index is not None else None
        if row is None or row.get("still") or float(row.get("slow", 1.0)) != 1.0 or not video.exists():
            continue
        if curves := measure(video):
            out[shot] = {"run": runs[index], "head": float(row.get("head", 0.0)), "curves": curves}
    return out


def place_all(rendered: list, shots: list[dict], home: Path, folder: Path,
              measure: Callable[[Path], dict | None] | None = None) -> list[tuple[float, Path]]:
    """Every rendered cue laid on its measured moment (or its planned one), the report written."""
    rows = {int(s["index"]): s for s in shots}
    measure = measure or (lambda video: measured(video, Path(folder) / "measured"))
    takes = takes_for(home, sorted({cue.shot for cue, _ in rendered if kind_of(cue.sound)}), measure)
    out, report = [], []
    for cue, wav in rendered:
        laid, row = place_cue(cue, wav, rows, takes.get(cue.shot), folder)
        out += laid
        report.append(row)
    write_report(folder, report)
    return out
