"""Per-episode attempt counts: episodes/epNN/attempts.json (owner 2026-10-18).

A ladder's rounds were counted per climb, so a relaunch, a second drive run or an autopilot
cure started the count again (STEP_CAPS.md finding 5: 5 regrid and 7 retake batches in one
episode after the caps).  Here a phase's rounds and seconds are written per EPISODE, beside
the plan, and every run reads the same file.  {key: {"rounds": n, "seconds": s}}; a key is a
cap-table phase (`retakes`) or a phase and its thing (`face_refine.T05`).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

FILE = "attempts.json"


def read(home: Path) -> dict:
    path = Path(home) / FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def _write(home: Path, doc: dict) -> None:
    """tmp + os.replace: a reader sees the old count or the new one, never a torn file."""
    path = Path(home) / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(FILE + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def count(home: Path, key: str) -> int:
    return int((read(home).get(key) or {}).get("rounds", 0))


def seconds(home: Path, key: str) -> float:
    return float((read(home).get(key) or {}).get("seconds", 0.0))


def spend(home: Path, key: str, seconds: float = 0.0) -> int:
    """One more round of `key`, and its seconds; the new count."""
    doc = read(home)
    row = doc.get(key) or {"rounds": 0, "seconds": 0.0}
    row = {"rounds": int(row.get("rounds", 0)) + 1, "seconds": round(float(row.get("seconds", 0.0)) + seconds, 1)}
    doc[key] = row
    _write(home, doc)
    return row["rounds"]


def mark(home: Path, key: str) -> None:
    """A once-only fact (the plan's one park), written without a round."""
    doc = read(home)
    doc[key] = {**(doc.get(key) or {}), "marked": True}
    _write(home, doc)


def marked(home: Path, key: str) -> bool:
    return bool((read(home).get(key) or {}).get("marked"))


def spent(home: Path, cap, key: str = "") -> bool:
    """The row's rounds or its wall are used up for this episode."""
    key = key or cap.name
    return count(home, key) >= cap.rounds or seconds(home, key) >= cap.wall_s
