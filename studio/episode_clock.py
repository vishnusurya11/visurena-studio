"""The wall clock of an episode, stage by stage, so the owner can see what a
chapter costs in TIME and where it goes.

OWNER 2026-09-16: "check time to get total time for a episode". Nine episodes
were built without one number for that; the GPU stages were felt to be long and
the paid stages felt short, and nothing said whether the gates added an hour.

`episodes/epNN/timing.jsonl`, one row per stage run: stage, started, ended,
seconds, ok, note. A stage that runs twice is two rows -- a retry is time too.
`report()` totals them and names the slowest.

A NORM IS A FUNCTION OF THE RUN'S CONDITIONS (ep10 synthesis F5). `NORMS` is
the constant table measured on episode 9 and stays as the fallback; `norm_for`
scales with what the run actually covered -- a retake of two takes is not a run
of thirty, and a constant 1200 s for take_dq hid a 1095 s run that was five
times its warm time because it shared the queue with a retake. That sharing is
the other thing the report now names: a row whose interval overlaps another
row's in the same file is CONTENDED, which on one GPU is the whole story of
why it was slow.
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
Zero means 'authoring, not timed'. The fallback when `norm_for` has no
condition to scale by. A stage over 2x its norm is flagged."""
SLOW = 2.0

DEFAULT_TAKES, DEFAULT_FRAMES = 30, 141
"""What a takes run is assumed to cover when shots.json is not there yet."""

TAKE_COLD, TAKE_FIXED, TAKE_PER_FRAME = 300.0, 60.0, 1.2
"""One cold load of the MiniMax weights per run, a fixed per-take cost (encode
+ VAE decode) and the sampler's slope -- least squares on ep09 and ep10, I.md §2."""


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


def norm_for(stage: str, count: int | None = None, frames: list[int] | None = None) -> float:
    """Expected seconds under the run's own conditions: `frames` per take for a
    takes run (30 x 141 when unknown), `count` of takes for take_dq, of lines
    for qc and lines. Anything else is the episode-9 table."""
    if stage == "takes":
        frames = frames or [DEFAULT_FRAMES] * DEFAULT_TAKES
        return TAKE_COLD + sum(TAKE_FIXED + TAKE_PER_FRAME * f for f in frames)
    if stage == "title":
        return 40 + 100        # the gpt-image still + one H3 i2v animate on warm weights
    if count:
        scaled = {"take_dq": 30 + 8 * count, "qc": 60 + 5 * count, "lines": 20 * count}
        if stage in scaled:
            return float(scaled[stage])
    return float(NORMS.get(stage, 0))


def conditions(book: Path, number: int) -> dict:
    """What the episode's own files say a run covers: the frame count of every
    take BY ITS INDEX (shots.json; a take is named by its first shot, so the
    numbering has holes) and the number of lines (placed.json)."""
    home = episode_home.home(book, number)
    out: dict = {}
    shots = home / "takes" / "r2v" / "shots.json"
    if shots.exists():
        out["frames"] = {r["index"]: r["frames"] for r in json.loads(shots.read_text(encoding="utf-8"))}
    placed = home / "placed.json"
    if placed.exists():
        out["lines"] = len(json.loads(placed.read_text(encoding="utf-8"))["lines"])
    return out


def indices_in(note: str) -> list[int]:
    """The take or line numbers a row's note names: `--retake=3,4`, `--redo=27`,
    or take_dq's bare `3 4 5`. A flag that carries no number names none."""
    found = []
    for word in note.split():
        body = word.split("=", 1)[1] if word.startswith(("--retake=", "--redo=")) else word
        found += [int(v) for v in body.split(",") if v.isdigit()]
    return found


def row_norm(row: dict, cond: dict) -> float:
    """The norm for THIS run: a retake of two takes is not a run of thirty, and
    a DQ of one take is not a DQ of the episode."""
    stage, named = row["stage"], indices_in(row.get("note", ""))
    frames = cond.get("frames") or dict(enumerate([DEFAULT_FRAMES] * DEFAULT_TAKES))
    if stage == "takes":
        picked = [frames[i] for i in named if i in frames] if named else list(frames.values())
        return norm_for(stage, frames=picked or list(frames.values()))
    if stage == "take_dq":
        return norm_for(stage, count=len(named) or len(frames))
    if stage == "lines" and named:
        return norm_for(stage, count=len(named))
    return norm_for(stage, count=cond.get("lines"))


def slow(row: dict, norm: float | None = None) -> bool:
    """Past twice its norm, or failed -- a FAIL row is time spent for nothing,
    and ep10's 806 s lines FAIL sat under a 900 s norm unflagged. A stage with
    no norm is never slow."""
    if not row.get("ok", True):
        return True
    norm = NORMS.get(row["stage"], 0) if norm is None else norm
    return bool(norm) and row["seconds"] > SLOW * norm


def _span(row: dict) -> tuple[datetime, datetime]:
    return datetime.fromisoformat(row["started"]), datetime.fromisoformat(row["ended"])


def contended(row: dict, others: list[dict]) -> bool:
    """Whether another run in the file overlapped this one's interval. Strict at
    the ends, so a stage that starts the second another ends is clean; a
    zero-second row (a refusal) is a mark, not a run, and contends with nothing."""
    if not row.get("seconds"):
        return False
    a0, a1 = _span(row)
    for other in others:
        if other is row or not other.get("seconds"):
            continue
        b0, b1 = _span(other)
        if a0 < b1 and b0 < a1:
            return True
    return False


def marks(row: dict, got: list[dict], cond: dict) -> list[str]:
    """What is wrong with one run, in words the report prints."""
    out = []
    if not row.get("ok", True):
        out.append("REFUSED" if row.get("note", "").startswith("refused") else "FAIL")
    elif slow(row, row_norm(row, cond)):
        out.append("SLOW")
    if contended(row, got):
        out.append("CONTENDED")
    return out


def stage_norm(stage: str, cond: dict) -> float:
    """The norm for a FULL run of the stage under the episode's conditions."""
    frames = cond.get("frames")
    count = len(frames) if stage == "take_dq" and frames else cond.get("lines")
    return norm_for(stage, count=count, frames=list(frames.values()) if frames else None)


def _stage_line(stage: str, runs: list[dict], total: float, got: list[dict], cond: dict) -> str:
    secs = sum(r["seconds"] for r in runs)
    flags = sorted({m for r in runs for m in marks(r, got, cond)})
    return (f"{stage:<12} {secs:>8.0f} {secs / total:>6.0%}  {len(runs):>4}  {stage_norm(stage, cond):>5.0f}"
            + ("  " + " ".join(flags) if flags else ""))


def _flagged_lines(got: list[dict], cond: dict) -> list[str]:
    out = []
    for r in got:
        if said := marks(r, got, cond):
            out.append(f"  {r['started'][11:]} {r['stage']:<11} {r['seconds']:>7.0f} s"
                       f"  norm {row_norm(r, cond):>5.0f}  {' '.join(said)}"
                       + (f"  ({r['note']})" if r.get("note") else ""))
    return out


def report(book: Path, number: int) -> str:
    """Total wall time, per stage, retries counted; the norm scaled to the
    episode's own take frames and line count; every SLOW, FAIL, REFUSED or
    CONTENDED run listed underneath with the norm it was judged by."""
    got = rows(book, number)
    if not got:
        return "no stages timed"
    cond = conditions(book, number)
    by: dict[str, list[dict]] = {}
    for r in got:
        by.setdefault(r["stage"], []).append(r)
    total = sum(r["seconds"] for r in got)
    lines = [f"{'stage':<12} {'seconds':>8} {'share':>6}  runs   norm  flags"]
    lines += [_stage_line(stage, runs, total, got, cond) for stage, runs in by.items()]
    span = (datetime.fromisoformat(got[-1]["ended"]) - datetime.fromisoformat(got[0]["started"])).total_seconds()
    lines.append(f"{'TOTAL':<12} {total:>8.0f}  ({total / 3600:.1f} h of stages; {span / 3600:.1f} h first start to last end)")
    if flagged := _flagged_lines(got, cond):
        lines += ["flagged runs:"] + flagged
    return "\n".join(lines)
