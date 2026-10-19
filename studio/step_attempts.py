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
import time
from contextlib import contextmanager
from pathlib import Path

FILE = "attempts.json"
LOCK_STALE_S = 30.0
"""A lock file older than this belongs to a dead writer and is broken."""


def read(home: Path) -> dict:
    path = Path(home) / FILE
    for _ in range(20):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except ValueError:
            return {}
        except PermissionError:                  # Windows: the writer's os.replace is in flight
            time.sleep(0.005)
    return {}


def _write(home: Path, doc: dict) -> None:
    """tmp + os.replace: a reader sees the old count or the new one, never a torn file."""
    path = Path(home) / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(FILE + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def _locked(home: Path):
    """One writer at a time: a lock file made with O_EXCL; a dead writer's is broken when stale."""
    lock = Path(home) / (FILE + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except (FileExistsError, PermissionError):   # Windows: a lock being deleted refuses a create
            _break_if_stale(lock)
            time.sleep(0.005)
    try:
        yield
    finally:
        _unlink(lock)


def _unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _break_if_stale(lock: Path) -> None:
    try:
        if time.time() - lock.stat().st_mtime > LOCK_STALE_S:
            _unlink(lock)
    except OSError:
        pass


def count(home: Path, key: str) -> int:
    return int((read(home).get(key) or {}).get("rounds", 0))


def seconds(home: Path, key: str) -> float:
    return float((read(home).get(key) or {}).get("seconds", 0.0))


def spend(home: Path, key: str, seconds: float = 0.0) -> int:
    """One more round of `key`, and its seconds; the new count."""
    with _locked(home):
        doc = read(home)
        row = doc.get(key) or {"rounds": 0, "seconds": 0.0}
        row = {"rounds": int(row.get("rounds", 0)) + 1,
               "seconds": round(float(row.get("seconds", 0.0)) + seconds, 1)}
        doc[key] = row
        _write(home, doc)
    return row["rounds"]


def add_seconds(home: Path, key: str, seconds: float) -> None:
    """Seconds onto `key` with no round (a folded heartbeat is time, not an attempt)."""
    with _locked(home):
        doc = read(home)
        row = doc.get(key) or {"rounds": 0, "seconds": 0.0}
        doc[key] = {**row, "seconds": round(float(row.get("seconds", 0.0)) + seconds, 1)}
        _write(home, doc)


def set_seconds(home: Path, key: str, seconds: float) -> None:
    """`key`'s seconds REPLACED (a heartbeat is this run's absolute total, not an increment)."""
    with _locked(home):
        doc = read(home)
        doc[key] = {"rounds": 0, "seconds": round(float(seconds), 1)}
        _write(home, doc)


def drop(home: Path, key: str) -> None:
    with _locked(home):
        doc = read(home)
        if doc.pop(key, None) is not None:
            _write(home, doc)


def elapsed(home: Path, key: str) -> float:
    """Contract K3: booked seconds plus the live heartbeat of a run that has not booked yet."""
    return round(seconds(home, key) + seconds(home, key + ".live"), 1)


def mark(home: Path, key: str) -> None:
    """A once-only fact (the plan's one park), written without a round."""
    with _locked(home):
        doc = read(home)
        doc[key] = {**(doc.get(key) or {}), "marked": True}
        _write(home, doc)


def marked(home: Path, key: str) -> bool:
    return bool((read(home).get(key) or {}).get("marked"))


def spent(home: Path, cap, key: str = "") -> bool:
    """The row's rounds or its wall are used up for this episode."""
    key = key or cap.name
    return count(home, key) >= cap.rounds or seconds(home, key) >= cap.wall_s
