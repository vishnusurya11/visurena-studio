"""The honest clock (C3_verdict #3, decision D1): time the PROCESS, not the step.

    clock.jsonl       one row per episode run: run_id, pid, started, ended, seconds, how
    clock.open.json   the live run: run_id, pid, started, last_beat (rewritten every BEAT_S)

`episode_clock.timed` stamps a step's timing.jsonl row in a `finally`; a
Windows Stop-Process runs none, so a killed step left no row at all (398
unlogged machine-minutes over WotW ep19-27, 23 kills).  Here the runner opens
a run row, a daemon thread beats it, a clean exit closes it, and the next run
closes an orphan as `killed` at its last beat -- a kill loses at most one beat.

What the ceiling is charged with is the UNION of the run spans (overlapping
or nested runs count once), plus the legacy timing.jsonl rows that ended
before the first run row (episodes begun before this clock existed).  Times
are epoch seconds; timing.jsonl's stamps are naive local ISO.
"""
from __future__ import annotations

import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable

CLOCK = "clock.jsonl"
OPEN = "clock.open.json"
BEAT_S = 60.0
Now = Callable[[], float]


def _write_atomic(path: Path, doc: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc), encoding="utf-8")
    os.replace(tmp, path)


def read_open(home) -> dict | None:
    path = Path(home) / OPEN
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (ValueError, OSError):
        return None


def rows(home) -> list[dict]:
    """Every closed run row, in file order."""
    path, out = Path(home) / CLOCK, []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line)) if line.strip() else None
        except ValueError:
            continue
    return out


def _append(home, run: dict, ended: float, how: str) -> dict:
    row = {"run_id": run.get("run_id"), "pid": run.get("pid"), "started": float(run["started"]),
           "ended": float(ended), "seconds": round(float(ended) - float(run["started"]), 3), "how": how}
    with (Path(home) / CLOCK).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def close_orphan(home) -> dict | None:
    """A live-run file nobody closed: its run was killed; it ends at its last beat."""
    run = read_open(home)
    if run is None:
        return None
    row = _append(home, run, run.get("last_beat") or run["started"], "killed")
    (Path(home) / OPEN).unlink(missing_ok=True)
    return row


def open_run(home, run_id: str, now: Now = time.time) -> dict:
    """Close any orphan, then open this run's live file."""
    Path(home).mkdir(parents=True, exist_ok=True)
    close_orphan(home)
    t = now()
    run = {"run_id": run_id, "pid": os.getpid(), "started": t, "last_beat": t}
    _write_atomic(Path(home) / OPEN, run)
    return run


def beat(home, run_id: str, now: Now = time.time) -> None:
    """This run is alive now: its live file's last_beat moves (another run's file is left alone)."""
    run = read_open(home)
    if run is not None and run.get("run_id") == run_id:
        _write_atomic(Path(home) / OPEN, {**run, "last_beat": now()})


def close_run(home, how: str = "closed", now: Now = time.time) -> dict | None:
    """A clean exit: the run row is closed now and the live file goes."""
    run = read_open(home)
    if run is None:
        return None
    row = _append(home, run, now(), how)
    (Path(home) / OPEN).unlink(missing_ok=True)
    return row


def spans(home) -> list[tuple[float, float]]:
    """(started, ended) of every run: closed rows, and a live or orphan file to its last beat."""
    out = [(float(r["started"]), float(r["ended"])) for r in rows(home) if "started" in r and "ended" in r]
    run = read_open(home)
    if run is not None:
        out.append((float(run["started"]), float(run.get("last_beat") or run["started"])))
    return out


def union(pairs: list[tuple[float, float]]) -> float:
    """Seconds covered by the spans, each moment counted once."""
    total, reach = 0.0, None
    for start, end in sorted(pairs):
        if reach is None or start > reach:
            total, reach = total + max(0.0, end - start), end
        elif end > reach:
            total, reach = total + (end - reach), end
    return float(total)


def _epoch(stamp) -> float | None:
    try:
        return datetime.fromisoformat(str(stamp)).timestamp() if stamp else None
    except ValueError:
        return None


def counts(ended: float | None, until: float | None, since: float) -> bool:
    """A legacy row counts when it ended inside [since, until); with no `until`
    every row does (a home this clock never ran in), a stampless one included."""
    if ended is None:
        return until is None
    return ended >= since and (until is None or ended < until)


def legacy_seconds(home, until: float | None, since: float = 0.0) -> float:
    """timing.jsonl rows that ended before `until` (the first run row, or the
    asking moment) and not before `since`."""
    path, total = Path(home) / "timing.jsonl", 0.0
    if not path.exists():
        return 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line) if line.strip() else None
            if row and counts(_epoch(row.get("ended")), until, since):
                total += float(row.get("seconds") or 0.0)
        except (ValueError, TypeError, AttributeError):
            continue
    return total


def spent_before(home, t0: float | None = None, since: float = 0.0) -> float:
    """Seconds the episode spent before `t0` (all of it when None) and after
    `since`: the legacy rows before the first run, plus the union of the runs."""
    every = spans(home)
    pairs = [(max(s, since), e if t0 is None else min(e, t0)) for s, e in every]
    pairs = [(s, e) for s, e in pairs if e > s]
    cuts = [x for x in (min((s for s, _ in every), default=None), t0) if x is not None]
    return legacy_seconds(home, min(cuts) if cuts else None, since) + union(pairs)


def spent(home) -> float:
    return spent_before(home, None)


class Heartbeat:
    """A daemon thread beating the live file every `every` seconds until stopped."""

    def __init__(self, home, run_id: str, every: float = BEAT_S):
        self.home, self.run_id, self.every = home, run_id, every
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._loop, name="run-clock", daemon=True)

    def _loop(self) -> None:
        while not self.stop.wait(self.every):
            try:
                beat(self.home, self.run_id)
            except OSError:
                continue


@contextmanager
def running(home, run_id: str, every: float = BEAT_S):
    """The run's span: opened, beaten while the body runs, closed on any exit
    Python sees.  A kill skips the close; the next run reads the last beat."""
    open_run(home, run_id)
    heart = Heartbeat(home, run_id, every)
    heart.thread.start()
    try:
        yield heart
    finally:
        heart.stop.set()
        heart.thread.join(timeout=5)
        close_run(home)


def _merged(pairs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """The spans with overlaps and nests folded together, in time order."""
    out: list[list[float]] = []
    for start, end in sorted(pairs):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [(a, b) for a, b in out]


def _drive_events(home) -> list[tuple[float, str]]:
    """(epoch, word) of drive.jsonl's `run` rows -- the outcome a launch ended with -- else its `end`."""
    path, out = Path(home) / "drive.jsonl", []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            at = datetime.fromisoformat(row["ts"]).timestamp()
        except (ValueError, KeyError, TypeError):
            continue
        word = row.get("outcome") if row.get("event") == "run" else None
        if word:
            out.append((at, f"{word} ({row['error']})" if row.get("error") else str(word)))
    return out


def _reason(events: list[tuple[float, str]], start: float, slack: float = 120.0) -> str:
    """The outcome the drive wrote last at or just after the gap opened."""
    near = [(at, word) for at, word in events if start - slack <= at <= start + slack]
    return min(near, key=lambda e: abs(e[0] - start))[1] if near else "unknown"


def dead_gaps(home) -> list[dict]:
    """Contract K4: the gaps between runs, [{start, end, seconds, reason}], reason from drive.jsonl."""
    merged, events = _merged(spans(home)), _drive_events(home)
    return [{"start": a_end, "end": b_start, "seconds": round(b_start - a_end, 1),
             "reason": _reason(events, a_end)}
            for (_, a_end), (b_start, _) in zip(merged, merged[1:]) if b_start > a_end]
