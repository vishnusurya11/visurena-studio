"""Who signs each gate: `gates.yaml` at the repo root, read by the judged steps.

A row is `human` (a person signs; legal only outside the refs and episode
lines) or `auto` (the judge signs pass or flagged and never parks).  `auto`
is a retirement, and a retirement is a decision with a date: the row carries
a decision id `YYYY-MM-DD-<slug>` that appears literally in docs/DECISIONS.md,
and a row without one is refused when read.  `shadow` is a FIELD, not a
state: a newer judge version run beside the current one, signing nothing.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from studio import registry

STATES = ("human", "auto")
PATH = registry.ROOT / "gates.yaml"
DECISIONS = registry.ROOT / "docs" / "DECISIONS.md"
DECISION_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Literal["human", "auto"]
    judge: str = ""             # "<name>@<version>"
    shadow: str = ""            # "<name>@<version+1>", benched beside `judge`
    decision: str = ""
    terminal: str = ""          # keep_best | still | flag | defer
    battery_terminal: str = ""
    max_grids: int = 0
    still_max: int = 0
    ceiling_seconds: float = 0.0


def load(path: Path | None = None) -> dict:
    return yaml.safe_load(Path(path or PATH).read_text(encoding="utf-8")) or {}


def rows(doc: dict) -> list[tuple[str, str, dict]]:
    """Every (stage, gate, row) under `gates`, in file order."""
    return [(stage, gate, row or {})
            for stage, gates in (doc.get("gates") or {}).items()
            for gate, row in (gates or {}).items()]


def decided(decision: str, decisions: Path | None = None) -> bool:
    """Whether the id appears literally in docs/DECISIONS.md."""
    path = Path(decisions or DECISIONS)
    return bool(decision) and decision in path.read_text(encoding="utf-8")


def check(stage: str, gate: str, row: Policy, decisions: Path | None = None) -> Policy:
    """An auto row without a decided id is refused: nobody retires a gate by feel."""
    if row.state != "auto":
        return row
    if not row.decision:
        raise SystemExit(f"gates.yaml: {stage}/{gate} is auto without a decision id")
    if not DECISION_ID.match(row.decision):
        raise SystemExit(f"gates.yaml: {stage}/{gate} decision {row.decision!r} is not YYYY-MM-DD-<slug>")
    if not decided(row.decision, decisions):
        raise SystemExit(f"gates.yaml: {stage}/{gate} decision {row.decision!r} is not in docs/DECISIONS.md")
    return row


def of(stage: str, gate: str, path: Path | None = None, decisions: Path | None = None) -> Policy:
    """The policy the step obeys: the registry's row, or `human` when none is written."""
    raw = dict(load(path).get("gates", {}).get(stage, {}).get(gate) or {"state": "human"})
    try:
        row = Policy(**raw)
    except ValidationError as exc:
        raise SystemExit(f"gates.yaml: {stage}/{gate}: {exc.errors()[0].get('msg')} "
                         f"(state is one of {STATES})") from exc
    return check(stage, gate, row, decisions)
