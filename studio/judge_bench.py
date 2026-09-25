"""The judge bench: every judge measured against the casebook, never by feel.

    uv run python -m studio.judge_bench <codex> <judge>

A judge is a callable Row -> {"refused": bool, "classes": [..], "values": {}}
from `studio.judges.registry`; it reads the values the row already carries
(the machine json harvested beside the artefact) and never decodes video.

Metrics (decision 2026-09-24 section 1.4): recall on OWNER rows with the
Wilson interval, per class and pooled; recall on all rows (owner + agent +
default); the false-refusal rate on pass rows weighted owner 1 / agent 0.75 /
default 0.5; synthetic rows in their own column; the reject-only recall on
attempts of unknown class; the flag rate per unit; and the cost of the
refusals in GPU minutes (a retake measured at 5-9 min: 7).  Misses are named
by relative path, never by what was said.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

from studio import casebook
from studio.casebook import Row

Judge = Callable[[Row], dict]
GPU_MINUTES_PER_REFUSAL = 7.0
REAL = ("owner", "agent", "default")


@dataclass
class Outcome:
    row: Row
    refused: bool
    classes: list[str] = field(default_factory=list)
    values: dict = field(default_factory=dict)


@dataclass
class Interval:
    point: float
    low: float
    high: float
    n: int
    k: int


# ---- rows in, outcomes out ----------------------------------------------------

def load_rows(casebook_dir: Path, kind: str) -> list[Row]:
    return [r for r in casebook.load(casebook_dir) if r.kind == kind]


def in_scope(row: Row, classes) -> bool:
    """Pass rows always; fault rows of the judge's classes, plus the reject-only unknowns."""
    return row.verdict == "pass" or classes is None or row.fault_class in classes or row.fault_class == "unknown"


def run(rows: list[Row], judge: Judge, classes=None) -> list[Outcome]:
    out = []
    for row in rows:
        if not in_scope(row, classes):
            continue
        said = judge(row)
        out.append(Outcome(row, bool(said.get("refused")), list(said.get("classes") or []), dict(said.get("values") or {})))
    return out


# ---- the numbers --------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """The Wilson score interval of k successes in n; (0, 0) when there is nothing to count."""
    if n == 0:
        return 0.0, 0.0
    p, z2 = k / n, z * z
    centre = (p + z2 / (2 * n)) / (1 + z2 / n)
    half = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)


def interval(k: int, n: int) -> Interval:
    low, high = wilson(k, n)
    return Interval(round(k / n, 4) if n else 0.0, low, high, n, k)


def measured(o: Outcome) -> bool:
    """A judge shown a row without its inputs says "not measured": neither a catch nor a miss."""
    return o.values.get("note") != "not measured"


def unmeasured(outcomes: list[Outcome]) -> int:
    return sum(not measured(o) for o in outcomes)


def faults(outcomes: list[Outcome], by: str = "owner") -> list[Outcome]:
    """The fault rows recall is counted over: one source, or `all` real ones; unknowns aside."""
    who = REAL if by == "all" else (by,)
    return [o for o in outcomes if measured(o) and o.row.verdict == "fault" and o.row.verdict_by in who
            and o.row.fault_class != "unknown"]


def recall(outcomes: list[Outcome], by: str = "owner") -> Interval:
    rows = faults(outcomes, by)
    return interval(sum(o.refused for o in rows), len(rows))


def reject_recall(outcomes: list[Outcome]) -> Interval:
    """Attempts refused for a reason nobody wrote down count for "reject" alone."""
    rows = [o for o in outcomes if measured(o) and o.row.verdict == "fault" and o.row.fault_class == "unknown"]
    return interval(sum(o.refused for o in rows), len(rows))


def by_class(outcomes: list[Outcome], by: str = "owner") -> dict[str, Interval]:
    out: dict[str, list[Outcome]] = {}
    for o in faults(outcomes, by):
        out.setdefault(o.row.fault_class, []).append(o)
    return {c: interval(sum(o.refused for o in rows), len(rows)) for c, rows in sorted(out.items())}


def false_refusals(outcomes: list[Outcome]) -> Interval:
    """The weighted share of pass rows refused; the interval on the row count."""
    rows = [o for o in outcomes if measured(o) and o.row.verdict == "pass"]
    total = sum(casebook.weight(o.row) for o in rows)
    refused = sum(casebook.weight(o.row) for o in rows if o.refused)
    share = refused / total if total else 0.0
    low, high = wilson(round(share * len(rows)), len(rows))
    return Interval(round(share, 4), low, high, len(rows), sum(o.refused for o in rows))


def flag_rate(outcomes: list[Outcome]) -> dict:
    """Refusals per unit (keyed codex/unit: two books number their units alike) and the share overall."""
    per_unit: dict[str, int] = {}
    for o in outcomes:
        if o.refused:
            key = f"{o.row.codex}/{o.row.unit}"
            per_unit[key] = per_unit.get(key, 0) + 1
    share = sum(per_unit.values()) / len(outcomes) if outcomes else 0.0
    return {"share": round(share, 4), "per_unit": dict(sorted(per_unit.items()))}


def gpu_minutes(outcomes: list[Outcome], per_refusal: float = GPU_MINUTES_PER_REFUSAL) -> float:
    return per_refusal * sum(o.refused for o in outcomes)


def misses(outcomes: list[Outcome], by: str = "all") -> list[str]:
    """Every fault the judge passed, by relative path (unknowns included: a reject is a reject)."""
    who = REAL if by == "all" else (by,)
    return sorted(o.row.path for o in outcomes
                  if measured(o) and o.row.verdict == "fault" and not o.refused and o.row.verdict_by in who)


def caught(outcomes: list[Outcome]) -> list[dict]:
    """The owner catches this judge made: the ratchet's memory, opaque ids only."""
    return [{"codex": o.row.codex, "sha8": o.row.sha8, "path": o.row.path}
            for o in outcomes if o.refused and o.row.verdict == "fault" and o.row.verdict_by == "owner"]


def lost_catches(baseline: dict, outcomes: list[Outcome]) -> list[str]:
    """Baseline catches whose row is here and is no longer refused, by path."""
    now = {(o.row.codex, o.row.path): o.refused for o in outcomes}
    return sorted(c["path"] for c in baseline.get("caught", [])
                  if (c["codex"], c["path"]) in now and not now[(c["codex"], c["path"])])


def confusion(outcomes: list[Outcome]) -> dict[str, dict]:
    """Per class: tp / fn on real rows, the synthetic pair, fp on pass rows under 'pass', unmeasured apart."""
    table: dict[str, dict] = {}
    for o in outcomes:
        key = o.row.fault_class if o.row.verdict == "fault" else "pass"
        cell = table.setdefault(key, {"tp": 0, "fn": 0, "fp": 0, "tn": 0, "synthetic_tp": 0, "synthetic_n": 0,
                                      "weighted_fp": 0.0, "unmeasured": 0})
        if not measured(o):
            cell["unmeasured"] += 1
        elif key == "pass":
            cell["fp" if o.refused else "tn"] += 1
            cell["weighted_fp"] += casebook.weight(o.row) if o.refused else 0.0
        elif o.row.verdict_by == "synthetic":
            cell["synthetic_n"] += 1
            cell["synthetic_tp"] += int(o.refused)
        else:
            cell["tp" if o.refused else "fn"] += 1
    return dict(sorted(table.items()))


# ---- the report ---------------------------------------------------------------

def _line(name: str, i: Interval) -> str:
    return f"- {name}: {i.point:.3f} [{i.low:.3f}, {i.high:.3f}] on {i.k}/{i.n}"


def _table(table: dict[str, dict]) -> list[str]:
    head = ["| class | tp | fn | synthetic tp/n | fp | tn | unmeasured |", "|---|---|---|---|---|---|---|"]
    return head + [f"| {c} | {v['tp']} | {v['fn']} | {v['synthetic_tp']}/{v['synthetic_n']} | {v['fp']} | {v['tn']} | {v['unmeasured']} |"
                   for c, v in table.items()]


def report(outcomes: list[Outcome], judge_name: str, version: str, machine_version: str = "") -> str:
    """The markdown for docs/calibration/<judge>.md: numbers, the table, misses by path."""
    rate = flag_rate(outcomes)
    lines = [f"## Bench {date.today().isoformat()} -- {judge_name}@{version}", "",
             f"rows {len(outcomes)} ({unmeasured(outcomes)} without this judge's inputs, not counted); "
             f"machine_version {machine_version or 'n/a'}; "
             f"flag rate {rate['share']:.3f}; refusals per unit {rate['per_unit']}; "
             f"expected GPU minutes {gpu_minutes(outcomes):.0f}", "",
             _line("recall on owner rows", recall(outcomes, "owner")),
             _line("recall on all rows", recall(outcomes, "all")),
             _line("synthetic (own column)", recall(outcomes, "synthetic")),
             _line("reject-only recall (unknown class)", reject_recall(outcomes)),
             _line("false refusals (weighted)", false_refusals(outcomes)), ""]
    lines += [_line(f"owner recall on {c}", i) for c, i in by_class(outcomes, "owner").items()]
    lines += ["", *_table(confusion(outcomes)), "", "misses (fault rows passed), by path:"]
    lines += [f"- {p}" for p in misses(outcomes)] or ["- none"]
    return "\n".join(lines) + "\n"


def baseline(outcomes: list[Outcome], judge_name: str, version: str, machine_version: str = "") -> dict:
    r = recall(outcomes, "owner")
    return {"judge": judge_name, "version": version, "machine_version": machine_version,
            "date": date.today().isoformat(), "rows": len(outcomes), "unmeasured": unmeasured(outcomes),
            "recall_owner": {"point": r.point, "low": r.low, "high": r.high, "n": r.n, "k": r.k},
            "recall_all": recall(outcomes, "all").point, "false_refusals": false_refusals(outcomes).point,
            "caught": caught(outcomes)}


def main(argv: list[str]) -> int:
    from studio import episode_home
    from studio.judges import registry
    if len(argv) < 2:
        print(__doc__)
        return 2
    entry = registry.get(argv[1])
    folder = episode_home.book_dir(argv[0]) / "casebook"
    outcomes = run(load_rows(folder, entry.kind), entry.judge, entry.classes)
    print(report(outcomes, entry.name, entry.version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
