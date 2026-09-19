#!/usr/bin/env python
"""Blur and warp per take, joined to each shot's camera move.

    uv run python scripts/episode/motion_quality.py <book_id> <episode> [--fps 6]

Writes episodes/epNN/review/motion_quality.json and prints one row per take,
so the camera catalog can say which moves H3 renders smoothly.  Free, CPU.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cv2
from studio import episode_home
from studio.motion_quality import flags, flow_incoherence, sharpness, summarise

MOVE = re.compile(r"The camera (holds|pushes|pulls|pans|tilts (?:up|down)|tracks|rises|descends|racks|circles|is handheld)")


def frames(path: Path, fps: float, size: int = 384):
    cap = cv2.VideoCapture(str(path))
    native = cap.get(cv2.CAP_PROP_FPS) or 24
    step = max(1, round(native / fps))
    i, out = 0, []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = grey.shape
            out.append(cv2.resize(grey, (size, round(size * h / w))))
        i += 1
    return out


def measure(path: Path, fps: float) -> dict:
    fs = frames(path, fps)
    sharp = [sharpness(f) for f in fs]
    warp = [flow_incoherence(a, b) for a, b in zip(fs, fs[1:])]
    return summarise(sharp, warp) | {"frames": len(fs)}


def move_of(shot: dict) -> str:
    m = MOVE.search(shot.get("motion", ""))
    return m.group(1) if m else "?"


def main(book_id: str, number: int, fps: float = 6.0) -> None:
    book = episode_home.book_dir(book_id)
    home = book / "episodes" / f"ep{number:02d}"
    plan = json.loads((home / "plan.json").read_text(encoding="utf-8"))
    shots = {s["index"]: s for s in plan["shots"]}
    rows = []
    for take in sorted((home / "takes" / "r2v").glob("T*.mp4")):
        idx = int(take.stem[1:])
        row = {"take": take.stem, "move": move_of(shots.get(idx, {})),
               "size": shots.get(idx, {}).get("size", "?")} | measure(take, fps)
        row["flags"] = flags(row)
        rows.append(row)
        print(f"{row['take']} {row['move']:<10} {row['size']:<13} sharp {row['sharp_median']:>6} "
              f"min {row['sharp_min_ratio']:.2f} dips {row['blur_dips']:>2}  "
              f"warp mean {row['warp_mean']:.2f} max {row['warp_max']:.2f}  {' '.join(row['flags'])}", flush=True)
    out = home / "review" / "motion_quality.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    fps = float(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 6.0
    main(sys.argv[1], int(sys.argv[2]), fps)
