"""The wall clock of an episode, stage by stage, so the owner can see what a
chapter costs in TIME and where it goes.

OWNER 2026-09-16: "check time to get total time for a episode". Nine episodes
were built without one number for that; the GPU stages were felt to be long and
the paid stages felt short, and nothing said whether the gates added an hour.

`episodes/epNN/timing.jsonl`, one row per stage run: stage, started, ended,
seconds, ok, note. A stage that runs twice is two rows -- a retry is time too.
`report()` totals them and names the slowest, and `NORMS` (seconds, measured on
episode 9) is what a stage is expected to take, so a run far past its norm is
flagged rather than silently absorbed.
"""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from studio import episode_home

NORMS = {
    "plan": 0, "lines": 900, "respot": 30, "timeline": 30, "frames": 600,
    "cast": 600, "sheets": 900, "takes": 7200, "take_dq": 1200, "assemble": 900,
    "qc": 300, "title": 120, "eye_review": 120, "publish": 600,
}
"""Expected seconds per stage, measured on episode 9 (28 takes, six sheets).
Zero means 'authoring, not timed'. A stage over 2x its norm is flagged."""
SLOW = 2.0


def path(book: Path, number: int) -> Path:
    return episode_home.home(book, number) / "timing.jsonl"


def stamp(book: Path, number: int, stage: str, started: float, ended: float,
          ok: bool = True, note: str = "") -> dict:
    """Record one stage run. Append-only; a retry is another row."""
    row = {"stage": stage, "started": datetime.fromtimestamp(started).isoformat(timespec="seconds"),
           "ended": datetime.fromtimestamp(ended).isoformat(timespec="seconds"),
           "seconds": round(ended - started, 1), "ok": ok, "note": note}
    p = path(book, number)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


@contextmanager
def timed(book: Path, number: int, stage: str, note: str = ""):
    """`with timed(book, n, "takes"): ...` -- stamps on exit, failure included."""
    started, ok = time.time(), True
    try:
        yield
    except BaseException:
        ok = False
        raise
    finally:
        stamp(book, number, stage, started, time.time(), ok, note)


def rows(book: Path, number: int) -> list[dict]:
    p = path(book, number)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def slow(row: dict) -> bool:
    """Past twice its norm -- and a stage with no norm is never slow."""
    norm = NORMS.get(row["stage"], 0)
    return bool(norm) and row["seconds"] > SLOW * norm


def report(book: Path, number: int) -> str:
    """Total wall time, per stage, retries counted, the slow ones named."""
    got = rows(book, number)
    if not got:
        return "no stages timed"
    by: dict[str, float] = {}
    for r in got:
        by[r["stage"]] = by.get(r["stage"], 0.0) + r["seconds"]
    total = sum(by.values())
    lines = [f"{'stage':<12} {'seconds':>8} {'share':>6}  runs  norm"]
    for stage, secs in by.items():
        runs = [r for r in got if r["stage"] == stage]
        flag = "  SLOW" if any(slow(r) for r in runs) else ""
        lines.append(f"{stage:<12} {secs:>8.0f} {secs / total:>6.0%}  {len(runs):>4}  {NORMS.get(stage, 0):>5}{flag}")
    span = (datetime.fromisoformat(got[-1]["ended"]) - datetime.fromisoformat(got[0]["started"])).total_seconds()
    lines.append(f"{'TOTAL':<12} {total:>8.0f}  ({total / 3600:.1f} h of stages; {span / 3600:.1f} h first start to last end)")
    return "\n".join(lines)
