"""What an unattended run learned, one JSON line per rung taken.

The run never edits the skill.  It writes what failed, the measured number,
the threshold it failed against, and the rung it took instead; the
retrospect groups those by (step, gate) across books, and a person or an
agent edits the skill from numbers, not from memory.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from studio import db


class Learning(BaseModel):
    ts: str = ""
    step: str
    substep: str = ""
    gate: str
    measured: float | str | None = None
    threshold: float | str | None = None
    action: str = Field(min_length=1)
    attempt: int = 1
    seconds: float = 0.0
    terminal: bool = False
    note: str = ""


def record(path: Path, learning: Learning) -> None:
    """Append one learning, stamped now, to the run's file."""
    if not learning.ts:
        learning.ts = db.utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(learning.model_dump_json() + "\n")


def load(path: Path) -> list[Learning]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Learning.model_validate(json.loads(line)) for line in lines if line.strip()]


def by_gate(rows: list[Learning]) -> dict[tuple[str, str], dict]:
    """Counts per (step, gate): how often, which rungs, how often terminal."""
    out: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"count": 0, "actions": defaultdict(int), "terminal": 0})
    for row in rows:
        cell = out[(row.step, row.gate)]
        cell["count"] += 1
        cell["actions"][row.action] += 1
        cell["terminal"] += int(row.terminal)
    return {k: {**v, "actions": dict(v["actions"])} for k, v in out.items()}
