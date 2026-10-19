"""The episode's cap table, read: stages.yaml `episode.caps` (owner 2026-10-18, the caps of
docs/audit/2026-10-18_step_caps/STEP_CAPS.md).

Every phase of the episode line has a round cap and a wall.  The table is data: the ladders
ask here (`rounds`, `wall_s`) and no cap is a constant of its own.  At a cap a ladder takes
its terminal -- keep the best, log `cap_line`, the run goes on; it never parks, never loops.
The 6 h episode clock (studio/run_budget) stays the outer wall.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from studio import registry

STAGE = "episode"


@dataclass(frozen=True)
class Cap:
    name: str
    step: str
    rounds: int
    per: str
    wall_s: float
    gate: str = ""
    climbs: int = 1
    read: str = ""
    """`step` declares the row has no reader of its own: it is only summed into the step wall."""
    share_min: float = 0.0
    """Report-only: the row's priced share of the episode, in minutes (never a wall)."""


def _cap(name: str, row: dict) -> Cap:
    return Cap(name=name, step=str(row["step"]), rounds=int(row["rounds"]), per=str(row.get("per", "pass")),
               wall_s=float(row["wall_min"]) * 60, gate=str(row.get("gate", "")),
               climbs=int(row.get("climbs", 1)), read=str(row.get("read", "")),
               share_min=float(row.get("share_min", 0.0)))


def table(stage: str = STAGE, path: Path = registry.PATH) -> dict[str, Cap]:
    """Every row of the stage's cap table, by phase name, in file order."""
    rows = registry.stage(stage, path).get("caps") or {}
    return {name: _cap(name, row) for name, row in rows.items()}


def cap(name: str) -> Cap:
    return table()[name]


def rounds(name: str) -> int:
    return cap(name).rounds


def wall_s(name: str) -> float:
    return cap(name).wall_s


def step_wall_s(step_id: str, stage: str = STAGE) -> float:
    """A step's wall: the sum of its rows' walls, a climb row once per climb; 0 for no row."""
    return sum(c.wall_s * (c.climbs if c.per == "climb" else 1)
               for c in table(stage).values() if c.step == step_id)


def family(step_id: str, stage: str = STAGE) -> str:
    """The model family a step loads (K2): text, image, vl, tts, video or none (unknown: none)."""
    for entry in registry.steps(stage):
        if entry["id"] == step_id:
            return str(entry.get("family", "none"))
    return "none"


def share_min(step_id: str, stage: str = STAGE) -> float:
    """Report-only: a step's rows' share_min summed; the step wall never reads it."""
    return sum(c.share_min for c in table(stage).values() if c.step == step_id)


def for_gate(gate: str, stage: str = STAGE) -> Cap | None:
    """The row capping a judged gate's rungs, or None."""
    return next((c for c in table(stage).values() if c.gate == gate), None)


def mmss(seconds: float) -> str:
    s = int(max(0.0, seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


def cap_line(name: str, taken: int, of: int, seconds: float, advisories: int) -> str:
    """What the log says at a cap: rounds, time, what was kept."""
    return f"CAP {name}: {taken}/{of} rounds, {mmss(seconds)}, kept best ({advisories} advisories)"
