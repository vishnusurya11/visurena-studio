#!/usr/bin/env python
"""Clones per take: big faces beyond the people the shot planned.

    uv run python scripts/episode/people_check.py <book_id> <episode> [--fps 4]

Writes episodes/epNN/review/people_check.json. Free, CPU.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cv2
from studio import episode_home, face_end
from studio.people_count import summarise_people


def face_heights(frame) -> list[float]:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    found = face_end.faces(rgb) or []
    fh = rgb.shape[0]
    return sorted((f["h"] / fh for f in found), reverse=True)


def per_frame(path: Path, fps: float) -> list[list[float]]:
    cap = cv2.VideoCapture(str(path))
    native = cap.get(cv2.CAP_PROP_FPS) or 24
    step = max(1, round(native / fps))
    out, i = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            out.append(face_heights(frame))
        i += 1
    return out


def main(book_id: str, number: int, fps: float = 4.0) -> None:
    book = episode_home.book_dir(book_id)
    home = book / "episodes" / f"ep{number:02d}"
    plan = json.loads((home / "plan.json").read_text(encoding="utf-8"))
    shots = {s["index"]: s for s in plan["shots"]}
    rows = []
    for take in sorted((home / "takes" / "r2v").glob("T*.mp4")):
        shot = shots.get(int(take.stem[1:]), {})
        planned = len(shot.get("faces") or [])
        row = {"take": take.stem, "size": shot.get("size", "?")} | summarise_people(
            per_frame(take, fps), planned)
        rows.append(row)
        mark = "CLONE" if row["clone_frames"] else ""
        print(f"{row['take']} {row['size']:<13} planned {row['planned']}  "
              f"clone frames {row['clone_frames']:>2}/{row['frames']:<3} worst +{row['worst_extra']}  {mark}",
              flush=True)
    out = home / "review" / "people_check.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    fps = float(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 4.0
    main(sys.argv[1], int(sys.argv[2]), fps)
