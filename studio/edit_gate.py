"""G5.1-5.6 -- edit integrity: the master IS the takes, frame for frame, at the
frames the plan names, with nothing held, nothing dropped, and no take on disk
that is no longer the one the cut used.

Every function here is pure except the two ffmpeg readers.  Measured on ep01
master_iter11 against shots_r2v (2026-09-11): two crf-17 encodes of one frame
differ by 0.16-0.59 (mean |grey| at 128x224, 0-255); neighbouring frames of the
slowest take differ by 1.4-9.7; frames of different shots by 32-63.  So
SAME_FRAME sits an order of magnitude above encoder noise and an order below
any other picture.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np

FPS = 24
GREY_W, GREY_H = 128, 224
SAME_FRAME = 4.0
"""CALIBRATION (above): encoder noise 0.16-0.59, another picture 32-63."""
SEGMENT_MEAN = 1.0
"""CALIBRATION: a segment that IS its take measured 0.16-0.59 mean; one frame off
lifts the mean to 1.6-9.7."""
DUP = 0.6
"""CALIBRATION: |f[k+1]-f[k]| below this and the frame is a repeat -- the encoder
reproduces an identical frame to within 0.59."""
HOLD_FRAMES = 3
"""CALIBRATION: singletons are threshold noise (0.623 against 0.609); a run of
three or more repeats the master has and the take does not is an edit hold."""
PTS_TOL = 0.001
PTS = re.compile(r"pts_time:\s*([0-9.]+)")


def grey_frames(video: Path, w: int = GREY_W, h: int = GREY_H) -> np.ndarray:
    """Every decoded frame, timestamps passed through (no dup, no drop), small and grey."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-an", "-fps_mode", "passthrough",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w)


def frame_times(video: Path) -> list[float]:
    """The presentation time of every frame, from showinfo."""
    result = subprocess.run(["ffmpeg", "-i", str(video), "-an", "-fps_mode", "passthrough",
                             "-vf", "showinfo", "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    return [float(m) for m in PTS.findall(result.stderr)]


def frame_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute grey difference between two frames."""
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())


def repeats(frames: np.ndarray, dup: float = DUP) -> set[int]:
    """Indices k where frame k+1 repeats frame k."""
    return {k for k in range(len(frames) - 1) if frame_diff(frames[k], frames[k + 1]) < dup}


def segment_plan(placed: dict, records: list[dict], fps: int = FPS) -> list[dict]:
    """One row per take-run in cut order: master start frame and frames placed."""
    by = {s["index"]: s for s in placed["shots"]}
    rows = []
    for r in sorted(records, key=lambda r: r["index"]):
        shots = r.get("shots") or [r["index"]]
        rows.append({"take": r["index"], "shots": shots, "rel_path": r["rel_path"],
                     "start": int(round(by[shots[0]]["t_start"] * fps)),
                     "n": int(round(sum(by[i]["seconds"] for i in shots) * fps))})
    return rows


def best_offset(master: np.ndarray, take: np.ndarray, start: int, n: int, span: int = 3) -> tuple[int, float]:
    """The take shift (frames) that best explains master[start:start+n], and its mean diff."""
    best = (0, float("inf"))
    for off in range(-span, span + 1):
        pairs = [(start + i, i + off) for i in range(n) if 0 <= i + off < len(take) and start + i < len(master)]
        if pairs:
            mean = float(np.mean([frame_diff(master[a], take[b]) for a, b in pairs]))
            if mean < best[1]:
                best = (off, mean)
    return best


def held_runs(master_dups: set[int], take_dups: set[int], least: int = HOLD_FRAMES) -> list[list[int]]:
    """Runs of frames the master repeats where the take does not."""
    runs: list[list[int]] = []
    for k in sorted(master_dups - take_dups):
        if runs and k == runs[-1][-1] + 1:
            runs[-1].append(k)
        else:
            runs.append([k])
    return [r for r in runs if len(r) >= least]


def segment_match(master: np.ndarray, take: np.ndarray, start: int, n: int) -> dict:
    """Is master[start:start+n] take[0:n]?  Offset, mean, the frames that are another
    picture, and the holds the edit added."""
    per = [frame_diff(master[start + i], take[i]) if start + i < len(master) and i < len(take) else 255.0
           for i in range(n)]
    offset, _ = best_offset(master, take, start, n)
    row = {"offset": offset, "mean": round(float(np.mean(per)), 3),
           "frames_off": [i for i, d in enumerate(per) if d > SAME_FRAME],
           "held": held_runs(repeats(master[start:start + n + 1]), repeats(take[:n + 1]))}
    row["ok"] = offset == 0 and row["mean"] <= SEGMENT_MEAN and not row["frames_off"] and not row["held"]
    return row


def cut_exact(master: np.ndarray, at: int, prev_last: np.ndarray, first: np.ndarray) -> bool:
    """The frame before the cut is the previous take's last placed frame, the frame
    at it is the next take's first."""
    return frame_diff(master[at - 1], prev_last) <= SAME_FRAME and frame_diff(master[at], first) <= SAME_FRAME


def timestamp_holes(times: list[float], fps: int = FPS, tol: float = PTS_TOL) -> list[tuple[int, float]]:
    """(frame, gap) wherever the picture does not advance by one frame: a late first
    frame, or a hole a player fills by holding the frame before it."""
    holes = [(0, round(times[0], 4))] if times and abs(times[0]) > tol else []
    holes += [(k, round(times[k + 1] - times[k], 4)) for k in range(len(times) - 1)
              if abs(times[k + 1] - times[k] - 1 / fps) > tol]
    return holes


def tail_check(master: np.ndarray, picture_frames: int, card: np.ndarray | None, black: int = 48) -> dict:
    """After the picture: the card frame for frame, then `black` black frames, nothing else."""
    card_n = len(card) if card is not None else 0
    out = {"expected_frames": picture_frames + card_n + black, "master_frames": len(master)}
    if card is not None:
        got = master[picture_frames:picture_frames + card_n]
        out["card_frames_off"] = [i for i in range(min(len(got), card_n)) if frame_diff(got[i], card[i]) > SAME_FRAME]
    dark = 0
    for f in master[::-1]:
        if f.max() >= 8:
            break
        dark += 1
    out["black_frames"] = dark
    out["ok"] = out["master_frames"] == out["expected_frames"] and dark == black and not out.get("card_frames_off")
    return out


def cut_manifest(plan: list[dict], book: Path) -> dict:
    """What the cut used: per take file, its relative path, frames placed and size on
    disk.  `assemble.py` writes this as `work/cut.json` AT CUT TIME (G5.6)."""
    out = {}
    for row in plan:
        path = Path(book) / row["rel_path"]
        out[Path(row["rel_path"]).name] = {"rel_path": row["rel_path"], "frames": row["n"],
                                           "bytes": path.stat().st_size if path.exists() else 0}
    return out


def stale_takes(manifest: dict, book: Path) -> list[str]:
    """Take files that are no longer the ones the cut used: a different size, or gone."""
    out = []
    for name, row in manifest.items():
        path = Path(book) / row["rel_path"]
        if not path.exists() or path.stat().st_size != row.get("bytes"):
            out.append(name)
    return sorted(out)


def provenance(plan: list[dict], book: Path, manifest: dict | None) -> dict:
    """G5.6 -- only measurable against a manifest recorded when the cut was made; a
    manifest read off the same files it is compared to can never be stale."""
    if not manifest:
        return {"measured": False, "stale_takes": []}
    return {"measured": True, "stale_takes": stale_takes(manifest, book)}


def edit_integrity(master_path: Path, placed: dict, records: list[dict], book: Path,
                   card: Path | None, manifest: dict | None = None) -> dict:
    """The whole gate: every segment, every cut, every timestamp, the tail, provenance."""
    master = grey_frames(master_path)
    plan = segment_plan(placed, records)
    takes = {row["take"]: grey_frames(book / row["rel_path"]) for row in plan}
    segments = [{**row, **segment_match(master, takes[row["take"]], row["start"], row["n"])} for row in plan]
    cuts = [{"at": nxt["start"],
             "exact": cut_exact(master, nxt["start"], takes[prev["take"]][prev["n"] - 1], takes[nxt["take"]][0])}
            for prev, nxt in zip(plan, plan[1:])]
    holes = timestamp_holes(frame_times(master_path))
    tail = tail_check(master, int(round(placed["duration_s"] * FPS)), grey_frames(card) if card else None)
    prov = provenance(plan, book, manifest)
    return {"segments": segments, "cuts": cuts, "timestamp_holes": holes, "tail": tail,
            "cut_manifest": cut_manifest(plan, book), "provenance": prov,
            "stale_takes": prov["stale_takes"],
            "ok": all(s["ok"] for s in segments) and all(c["exact"] for c in cuts) and not holes
            and tail["ok"] and not prov["stale_takes"]}
