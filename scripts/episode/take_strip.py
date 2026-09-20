#!/usr/bin/env python
"""A contact sheet of the takes on disk: three frames across each take.

    uv run python scripts/episode/take_strip.py <codex_id> <episode> [first] [last] [per_row]

Free, local, no GPU. Each row is one take -- first third, middle, last third --
so a reader can see in one picture whether a take froze, churned, reframed or
changed its subject, which is the check the skill asks for before the cut ("look
at the take strips before the cut. Report what you saw, not what you hoped").

Writes `reports/strip_T<first>_T<last>.png` under the episode.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home

CELL = 320
"""Pixels a side per frame: three of them is a 960 px row, legible at a glance."""


def frames_of(path: Path, n: int = 3) -> list[np.ndarray]:
    """`n` frames evenly spread over the take, each cell-sized."""
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out = []
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 0.5) / n))
        ok, frame = cap.read()
        out.append(cv2.resize(frame, (CELL, CELL)) if ok else np.zeros((CELL, CELL, 3), np.uint8))
    cap.release()
    return out


def label(row: np.ndarray, text: str) -> np.ndarray:
    cv2.putText(row, text, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
    cv2.putText(row, text, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return row


def sheet(takes: list[Path]) -> np.ndarray:
    rows = [label(np.hstack(frames_of(p)), p.stem) for p in takes]
    return np.vstack(rows)


def main(book_id: str, number: int, first: int = 0, last: int = 99) -> int:
    home = episode_home.home(episode_home.book_dir(book_id), number)
    takes = sorted(p for p in (home / "takes" / "r2v").glob("T??.mp4")
                   if first <= int(p.stem[1:]) <= last)
    if not takes:
        print("no takes on disk")
        return 1
    out = home / "reports" / f"strip_{takes[0].stem}_{takes[-1].stem}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), sheet(takes))
    print(out)
    return 0


if __name__ == "__main__":
    a = sys.argv
    raise SystemExit(main(a[1], int(a[2]), int(a[3]) if len(a) > 3 else 0,
                          int(a[4]) if len(a) > 4 else 99))
