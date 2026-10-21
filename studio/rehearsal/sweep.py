"""Sweeps, and what counts as n (2026-10-21_ep02_proof DESIGN 3.3, R13, R14).

The point list: F1, F9, F10, F13, F16 sweep k over EVERY take submit of the checkpoint (read from
an unfaulted run's engine_log.jsonl); F2 and F3 kill at every distinct write SITE (file kind x
code location, from trace's write rows) at its first and one mid occurrence; F18 tears every
record kind x checkpoint.  Distinctness: a point counts toward n only when its recovery trace
is distinct, and a trace class passes only when every point in it passed.  The count is only as
good as the trace is stable, so every shard replays one point and compares (`stability`): a
replay that traces differently fails the instrument, and the sweep's n counts nothing.  Cost: a sweep past
its budget (4 h) is cut into shards run on later nights; the untried count is reported, never
extrapolated."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Mapping

TAKE_FAULTS = {"F1": "crash", "F1b": "lost", "F9": "hang", "F10": "exec_error", "F13": "corrupt", "F16": "exec_fatal"}
WRITE_FAULTS = {"F2": "09", "F3": "10"}
BUDGET_S = 4 * 3600.0
SUBMIT_CALLS = ("prompt", "submit")


@dataclass(frozen=True)
class Point:
    fault: str
    where: Mapping = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.fault + ":" + ",".join(f"{k}={self.where[k]}" for k in sorted(self.where))


def is_take_submit(row: Mapping) -> bool:
    """An engine_log row for a take graph's POST /prompt."""
    take = row.get("kind") == "take" or "take" in str(row.get("workflow") or "") or "r2v" in str(row.get("workflow") or "")
    return row.get("call") in SUBMIT_CALLS and take


def take_points(fault: str, engine_rows: Iterable[Mapping]) -> list[Point]:
    """One point per take submit: k counts the submits of its workflow (the fake engine's fault
    counter is per workflow), so every k of every take workflow, never a sample of them."""
    seen: dict[str, int] = defaultdict(int)
    points = []
    for r in engine_rows:
        if is_take_submit(r):
            seen[str(r.get("workflow"))] += 1
            points.append(Point(fault, {"workflow": str(r.get("workflow")), "k": seen[str(r.get("workflow"))]}))
    return points


def write_sites(write_rows: Iterable[Mapping], step: str) -> dict[tuple[str, str], int]:
    """(file kind, code site) -> how many times the step wrote there."""
    seen: dict[tuple[str, str], int] = defaultdict(int)
    for row in write_rows:
        if row.get("step") == step:
            seen[(row["kind"], row["site"])] += 1
    return dict(seen)


def write_points(fault: str, write_rows: Iterable[Mapping], step: str) -> list[Point]:
    """Every distinct write site at its first occurrence, and at its middle one when it has more."""
    points = []
    for (kind, site), count in sorted(write_sites(write_rows, step).items()):
        for occurrence in (1,) if count < 3 else (1, (count + 1) // 2):
            points.append(Point(fault, {"kind": kind, "site": site, "occurrence": occurrence, "step": step}))
    return points


def record_points(kinds: Iterable[str], checkpoints: Iterable[str], fault: str = "F18") -> list[Point]:
    return [Point(fault, {"record": r, "checkpoint": c}) for c in checkpoints for r in kinds]


def tally(results: Iterable[Mapping], planned: int) -> dict:
    """Points tried, distinct traces, passes over distinct traces (a class passes only when all its
    points passed), the untried count; a point with no trace is listed, never counted."""
    results = list(results)
    classes: dict[str, list[Mapping]] = defaultdict(list)
    for r in results:
        if r.get("trace"):
            classes[r["trace"]].append(r)
    passed = sum(1 for rows in classes.values() if all(x.get("passed") is True for x in rows))
    return {"tried": len(results), "n_distinct": len(classes), "passed_distinct": passed,
            "untried": max(planned - len(results), 0),
            "failing": [r["id"] for r in results if r.get("passed") is not True],
            "untraced": [r["id"] for r in results if not r.get("trace")]}


def stability(first: Mapping, again: Mapping) -> dict:
    """R14's own check on the instrument: the SAME point replayed must trace the same lines, or the
    distinct-trace count is counting timing noise.  `only`: the lines one run executed and the
    other did not, so a moving branch is named."""
    a = {tuple(x) for x in first.get("trace_lines") or ()}
    b = {tuple(x) for x in again.get("trace_lines") or ()}
    same = bool(first.get("trace")) and first.get("trace") == again.get("trace")
    return {"point": first.get("id"), "same": same, "signatures": [first.get("trace"), again.get("trace")],
            "only": [list(x) for x in sorted(a ^ b)][:20]}


def shards(points: list[Point], seconds_per_point: float, budget_s: float = BUDGET_S) -> list[list[Point]]:
    """The points cut into runs that each fit the budget at the MEASURED cost of one point."""
    size = max(int(budget_s // max(seconds_per_point, 1e-9)), 1)
    return [points[i:i + size] for i in range(0, len(points), size)]


def next_shard(points: list[Point], done: set[str], seconds_per_point: float, budget_s: float = BUDGET_S) -> dict:
    """The next shard of the points not yet tried: `untried` before it runs, `after` once it has."""
    left = [p for p in points if p.id not in done]
    run = shards(left, seconds_per_point, budget_s)[0] if left else []
    return {"run": run, "untried": len(left), "after": len(left) - len(run)}
