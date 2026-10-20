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

from studio import episode_home, run_clock

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

RENDERS = ("takes", "take_render")
"""The rows priced by the takes they render: the takes run, and the GPU render span takes_r2v
stamps inside it (deadline retro 2026-10-20: ep01's 84.7 min of renders had no row of their own)."""
DETAIL = "detail"
"""A row that times a span INSIDE another row's wall that a sibling row already counts: take_render, the
GPU span inside takes while the CPU lane's take_dq rows (also `within` takes) run beside it.  Netting
the takes row of both clamped it to 0 and summed ep01 span 1 to 3,865 s against a 2,054 s wall (skeptic,
package F round 1), so a detail row carries `seconds` 0 -- every summing reader adds nothing, as for a
zero-second `started` mark -- and its span in `span_s`, which `judged` reads for its norm."""
KILLED = "killed"
"""The stage of a row `report` adds for a run clock.jsonl closed `killed`: the seconds of its span no
timing row covers (a Stop-Process runs no `finally`; ep01 run 12's av3 hang left 41 min on no row)."""


def path(book: Path, number: int) -> Path:
    return episode_home.home(book, number) / "timing.jsonl"


def stamp(book: Path, number: int, stage: str, started: float, ended: float,
          ok: bool = True, note: str = "", within: str = "", net_of: float = 0.0,
          device: str = "", detail: bool = False) -> dict:
    """Record one stage run. Append-only; a retry is another row.

    `within` names the stage this run happened INSIDE (the master's upscale runs
    inside assemble, 2026-10-14); the outer row is then stamped `net_of` it, so
    every reader that sums `seconds` counts that time once.  A row never goes negative
    (ep01 held -421.1 s): `seconds` is max(0, gross - nested), the rest is `overlap_s`.
    `t0`/`t1` are the epoch ends; `device` says where it ran (cpu / gpu), blank when unknown.
    A `detail` row (`DETAIL`) has `seconds` 0 and its span in `span_s`."""
    gross = ended - started
    row = {"stage": stage, "started": datetime.fromtimestamp(started).isoformat(timespec="seconds"),
           "ended": datetime.fromtimestamp(ended).isoformat(timespec="seconds"),
           "seconds": 0.0 if detail else round(max(0.0, gross - net_of), 1), "ok": ok, "note": note,
           "t0": started, "t1": ended}
    if detail:
        row.update(detail=True, span_s=round(gross, 1))
    if device:
        row["device"] = device
    if within:
        row["within"] = within
    if net_of:
        row.update(net_of_s=round(net_of, 1), gross_s=round(gross, 1), overlap_s=round(max(0.0, net_of - gross), 1))
    return append(book, number, row)


def append(book: Path, number: int, row: dict) -> dict:
    """One row onto the episode's timing.jsonl."""
    p = path(book, number)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def judged(row: dict) -> float:
    """The seconds a row is judged by against its norm: a detail row's span, any other row's seconds."""
    return float(row.get("span_s", row.get("seconds") or 0)) if row.get("detail") else float(row.get("seconds") or 0)


@contextmanager
def timed(book: Path, number: int, stage: str, note: str = "", within: str = ""):
    """`with timed(book, n, "takes"): ...` -- stamps on exit, failure included,
    net of the rows stamped `within` this stage while it ran."""
    started, ok = time.time(), True
    try:
        yield
    except BaseException:
        ok = False
        raise
    finally:
        stamp(book, number, stage, started, time.time(), ok, note, within,
              net_of=nested_seconds(book, number, stage, started))


def nested_seconds(book: Path, number: int, stage: str, since: float) -> float:
    """Seconds of the rows stamped `within` this stage that started at or after `since`."""
    floor = datetime.fromtimestamp(since).replace(microsecond=0)
    return sum(float(r.get("seconds") or 0) for r in rows(book, number)
               if r.get("within") == stage and datetime.fromisoformat(r["started"]) >= floor)


def rows(book: Path, number: int) -> list[dict]:
    p = path(book, number)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def local_epoch(stamp: str) -> float:
    """A naive timing.jsonl stamp (this machine's local time) as epoch seconds."""
    return datetime.fromisoformat(stamp).timestamp()


def epochs(row: dict) -> tuple[float, float] | None:
    """A row's (start, end) in epoch seconds: its `t0`/`t1` when stamped, else its ISO stamps."""
    if "t0" in row and "t1" in row:
        return float(row["t0"]), float(row["t1"])
    try:
        return local_epoch(row["started"]), local_epoch(row["ended"])
    except (KeyError, TypeError, ValueError):
        return None


def covered(start: float, end: float, got: list[dict]) -> float:
    """Seconds of [start, end] some timing row covers, each moment once."""
    pairs = [(max(start, a), min(end, b)) for a, b in filter(None, map(epochs, got))]
    return run_clock.union([(a, b) for a, b in pairs if b > a])


def in_flight(start: float, end: float, got: list[dict]) -> str:
    """The step whose `started` mark is the last inside [start, end]: the step a kill caught."""
    seen = [(span[0], r["stage"]) for r in got
            if r.get("note") == "started" and (span := epochs(r)) and start <= span[0] <= end]
    return max(seen)[1] if seen else "no step"


def killed_row(run: dict, lost: float, step: str) -> dict:
    """The row a killed run's uncovered seconds are charged on: never `ok`, marked KILLED."""
    s, e = float(run["started"]), float(run["ended"])
    return {"stage": KILLED, "started": datetime.fromtimestamp(s).isoformat(timespec="seconds"),
            "ended": datetime.fromtimestamp(e).isoformat(timespec="seconds"), "seconds": round(lost, 1),
            "ok": False, "killed": True, "run_id": run.get("run_id"), "t0": s, "t1": e,
            "note": f"run killed in {step}; charged to its last beat" + (" (repair)" if run.get("repair") else "")}


def killed_rows(book: Path, number: int) -> list[dict]:
    """One row per run clock.jsonl closed `killed`, for the seconds of its span that no timing row
    covers (the step in flight never stamped): on the clock as killed, never lost."""
    got, out = rows(book, number), []
    for run in run_clock.rows(episode_home.home(book, number)):
        if run.get("how") != "killed":
            continue
        s, e = float(run["started"]), float(run["ended"])
        if (lost := (e - s) - covered(s, e, got)) >= 1.0:
            out.append(killed_row(run, lost, in_flight(s, e, got)))
    return out


def killed_part(home) -> str:
    """The finish line's killed part: the hours of the runs a kill ended (charged to their last beat),
    each named as the share of the charge or of the repair it already sits in, so nobody adds it a
    second time; '' when no run was killed.  ep01: 1.73 h in 4 runs, 0.73 h charge + 1.00 h repair."""
    dead = [r for r in run_clock.rows(home) if r.get("how") == "killed"]
    if not dead:
        return ""
    repair = sum(float(r["seconds"]) for r in dead if r.get("repair")) / 3600
    episode = sum(float(r["seconds"]) for r in dead if not r.get("repair")) / 3600
    shares = [f"{h:.2f} h of the {where}" for h, where in ((episode, "charge"), (repair, "repair")) if h]
    return (f" | killed {episode + repair:.2f} h in {len(dead)} run{'s' if len(dead) > 1 else ''}"
            + f" ({', '.join(shares)})")


def norm_for(stage: str, count: int | None = None, frames: list[int] | None = None) -> float:
    """Expected seconds under the run's own conditions: `frames` per take for a
    takes run (30 x 141 when unknown), `count` of takes for take_dq, of lines
    for qc and lines. Anything else is the episode-9 table.  A `take_render` row (the render span
    inside a takes run) is priced as the takes it rendered."""
    if stage in RENDERS:
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
    if stage in RENDERS:
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
    return bool(norm) and judged(row) > SLOW * norm


def _span(row: dict) -> tuple[datetime, datetime]:
    return datetime.fromisoformat(row["started"]), datetime.fromisoformat(row["ended"])


def nested(a: dict, b: dict) -> bool:
    """One row ran inside the other (`within`): a part of a run, not a rival."""
    return a.get("within") == b.get("stage") or b.get("within") == a.get("stage")


def contended(row: dict, others: list[dict]) -> bool:
    """Whether another run in the file overlapped this one's interval. Strict at
    the ends, so a stage that starts the second another ends is clean; a
    zero-second row (a refusal) is a mark, not a run, and contends with nothing; nor does a KILLED
    row, which is the uncovered rest of a run whose rows lie inside its span."""
    if not row.get("seconds") or row.get("killed"):
        return False
    a0, a1 = _span(row)
    for other in others:
        if other is row or not other.get("seconds") or other.get("killed") or nested(row, other):
            continue
        b0, b1 = _span(other)
        if a0 < b1 and b0 < a1:
            return True
    return False


def marks(row: dict, got: list[dict], cond: dict) -> list[str]:
    """What is wrong with one run, in words the report prints."""
    out = []
    if row.get("killed"):
        out.append("KILLED")
    elif not row.get("ok", True):
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
    inside = [r for r in runs if r.get("detail")]
    return (f"{stage:<12} {secs:>8.0f} {secs / total:>6.0%}  {len(runs):>4}  {stage_norm(stage, cond):>5.0f}"
            + ("  " + " ".join(flags) if flags else "")
            + (f"  [{sum(map(judged, inside)):.0f} s inside {inside[0].get('within')}]" if inside else ""))


def _flagged_lines(got: list[dict], cond: dict) -> list[str]:
    out = []
    for r in got:
        if said := marks(r, got, cond):
            out.append(f"  {r['started'][11:]} {r['stage']:<11} {judged(r):>7.0f} s"
                       f"  norm {row_norm(r, cond):>5.0f}  {' '.join(said)}"
                       + (f"  ({r['note']})" if r.get("note") else ""))
    return out


def report(book: Path, number: int) -> str:
    """Total wall time, per stage, retries counted; the norm scaled to the
    episode's own take frames and line count; every SLOW, FAIL, REFUSED,
    CONTENDED or KILLED run listed underneath with the norm it was judged by.
    A killed run's uncovered seconds are a `killed` row (`killed_rows`)."""
    got = rows(book, number) + killed_rows(book, number)
    if not got:
        return "no stages timed"
    cond = conditions(book, number)
    by: dict[str, list[dict]] = {}
    for r in got:
        by.setdefault(r["stage"], []).append(r)
    total = sum(r["seconds"] for r in got)
    lines = [f"{'stage':<12} {'seconds':>8} {'share':>6}  runs   norm  flags"]
    lines += [_stage_line(stage, runs, total, got, cond) for stage, runs in by.items()]
    span = (max(datetime.fromisoformat(r["ended"]) for r in got)
            - min(datetime.fromisoformat(r["started"]) for r in got)).total_seconds()
    lines.append(f"{'TOTAL':<12} {total:>8.0f}  ({total / 3600:.1f} h of stages; {span / 3600:.1f} h first start to last end)")
    if flagged := _flagged_lines(got, cond):
        lines += ["flagged runs:"] + flagged
    return "\n".join(lines)
