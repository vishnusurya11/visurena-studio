"""Reader 2 for the mouth exam: lower-face motion on the face refine's own face boxes, against
the line's phrases.

FaceMesh reads a photographic face; on Jekyll ep01's cel faces it read 1-2 % of the medium
shots and failed the exam (studio/measure/mouth_exam.py: 7 of 10 wrong-line, 0 of 2 known
offsets).  face_yolov8m (the face refine's anime-trained detector, studio/face_detect.py) finds
those faces from about 37 px, and studio/face_track.py links and smooths its boxes.  This reads:

- the speaker = the face track with the most face (sum of its heights), its smoothed box;
- per frame, that box as a 64 x 64 grey crop; the motion of the lower face (rows 0.55-0.85 of
  the box, where a face_yolov8m box holds the mouth) less the motion of the upper face (rows
  0.15-0.45): a pan or a head move moves both, a speaking mouth only the lower;
- the line's phrases (voiced runs over 8 % of its range, gaps under 3 frames closed, runs under
  3 frames dropped) as a 0/1 gate, and the peak of the gate's cross-correlation with the motion
  within +-window (`mouth.best_lag`), positive when the mouth is late;
- per phrase, the onset error (where the motion steps up nearest each phrase's start) and the
  share of silent frames moving as much as the speech does, reported beside the score.

Fixed on the five other ep01 dialogue takes (T03 T04 T11 T20 T23), never on an exam render,
and committed before the exam ran (docs/audit/2026-10-21_lipsync_audio_ref/exam/).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from studio.measure import mouth
from studio.measure.mouth_exam import WINDOW

REL = 0.08
GAP = 3
LEAST = 3
LOWER = ((0.55, 0.85), (0.25, 0.75))
UPPER = ((0.15, 0.45), (0.25, 0.75))
SIZE = 64
HALF = 6
"""Frames each side of a phrase onset the step is read over (0.25 s)."""


def runs(on: np.ndarray) -> list[list[int]]:
    """[start, end) of each run of True."""
    edges = np.diff(np.concatenate([[0], on.astype(int), [0]]))
    return [[int(a), int(b)] for a, b in zip(np.where(edges == 1)[0], np.where(edges == -1)[0])]


def phrases(line: np.ndarray, rel: float = REL, gap: int = GAP, least: int = LEAST) -> list[tuple[int, int]]:
    """The line's phrases: voiced runs, gaps under `gap` frames closed, runs under `least` dropped."""
    line = np.asarray(line, dtype=float)
    out: list[list[int]] = []
    for a, b in runs(line > line.min() + rel * (line.max() - line.min())):
        if out and a - out[-1][1] < gap:
            out[-1][1] = b
        else:
            out.append([a, b])
    return [(a, b) for a, b in out if b - a >= least]


def gate(line: np.ndarray, n: int) -> np.ndarray:
    """1 on the phrases' frames, 0 elsewhere, over n frames."""
    g = np.zeros(n)
    for a, b in phrases(np.asarray(line, dtype=float)[:n]):
        g[a:b] = 1.0
    return g


def region(crops: np.ndarray, part) -> np.ndarray:
    (r0, r1), (c0, c1) = part
    s = crops.shape[1]
    return crops[:, int(r0 * s):int(r1 * s), int(c0 * s):int(c1 * s)]


def motion(stack: np.ndarray) -> np.ndarray:
    """Mean |change| from the frame before; the first frame takes the second's."""
    m = np.abs(np.diff(np.asarray(stack, dtype=float), axis=0)).mean(axis=(1, 2))
    return np.concatenate([m[:1], m]) if len(m) else np.zeros(len(stack))


def face_motion(crops: np.ndarray) -> np.ndarray:
    """Lower-face motion less upper-face motion, per frame."""
    return motion(region(crops, LOWER)) - motion(region(crops, UPPER))


def speaker(dets: dict, n: int):
    """(n x 4 smoothed boxes, frames inside its life) of the face track with the most face;
    (None, all False) with none.  Boxes are read every face_track.EVERY frames."""
    from studio import face_detect, face_track as ft
    strong, weak = ft.by_strength({int(t): v for t, v in dets.items()}, face_detect.CONF)
    tracks = ft.keep(ft.rescue(ft.link(strong), weak))
    if not tracks:
        return None, np.zeros(n, bool)
    best = max(tracks, key=lambda tr: sum(ft.height(b) for _, b in tr))
    a, z = ft.life(best)
    t = np.arange(n)
    return ft.fill(best, n), (t >= a - ft.EVERY + 1) & (t <= z + ft.EVERY - 1)


def crops(frames: list, boxes: np.ndarray, size: int = SIZE) -> np.ndarray:
    """Each frame's box as a size x size grey crop."""
    import cv2
    out = []
    for f, (x1, y1, x2, y2) in zip(frames, boxes):
        h, w = f.shape[:2]
        x1, y1 = int(np.clip(x1, 0, w - 2)), int(np.clip(y1, 0, h - 2))
        x2, y2 = int(np.clip(x2, x1 + 2, w)), int(np.clip(y2, y1 + 2, h))
        grey = cv2.cvtColor(np.ascontiguousarray(f[y1:y2, x1:x2]), cv2.COLOR_RGB2GRAY)
        out.append(cv2.resize(grey, (size, size), interpolation=cv2.INTER_AREA))
    return np.array(out, dtype=float)


def series_of(frames: list, dets: dict) -> np.ndarray:
    """The speaker's face motion per frame; nan where no speaker face is held."""
    boxes, seen = speaker(dets, len(frames))
    if boxes is None:
        return np.full(len(frames), np.nan)
    m = face_motion(crops(frames, boxes))
    m[~seen] = np.nan
    return m


def read(video: Path, finder) -> np.ndarray:
    """A take's series: its frames, and its face boxes from `finder(video)` (a face_detect.Worker)."""
    from studio import take_lock
    return series_of(take_lock.frames(video, None), finder(video))


def fit(series, line, window: int = WINDOW):
    """(lag frames, score, measured): the gate's peak cross-correlation with the motion within
    +-window; measured when half the frames hold a face and the peak clears mouth.CORR_FLOOR."""
    series = np.asarray(series, dtype=float)
    k, c = mouth.best_lag(mouth.smooth(mouth.fill(series)), gate(line, len(series)), window)
    return k, c, mouth.readable(series) >= mouth.READABLE and c >= mouth.CORR_FLOOR


def step(m: np.ndarray, t: int, half: int = HALF) -> float:
    """Mean motion just after frame t less just before; -inf where it would leave the take."""
    if t - half < 0 or t + half > len(m):
        return -np.inf
    return float(m[t:t + half].mean() - m[t - half:t].mean())


def onset_errors(series, line, window: int = WINDOW) -> list[int]:
    """Per phrase: the frames from its start to where the motion steps up most, within +-window."""
    m = mouth.fill(np.asarray(series, dtype=float))
    ks = range(-window, window + 1)
    return [max(ks, key=lambda k: (step(m, a + k), -abs(k))) for a, _ in phrases(np.asarray(line)[:len(m)])]


def silence_motion(series, line, lag: int) -> float:
    """Share of the silent frames (phrases moved `lag` late) moving at least the speech's median."""
    m = mouth.fill(np.asarray(series, dtype=float))
    g = np.roll(gate(line, len(m)), lag) > 0
    if not g.any() or g.all():
        return 0.0
    return float(np.mean(m[~g] >= np.median(m[g])))


def load_series(path: Path) -> dict:
    """A recorded {render: [motion or null]} fixture as arrays with nan."""
    got = json.loads(Path(path).read_text(encoding="utf-8"))["series"]
    return {k: np.array([np.nan if v is None else v for v in a], dtype=float) for k, a in got.items()}
