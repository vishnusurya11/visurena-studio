"""The JSON contract of the board (report D §3): one pydantic model per
`/api/*.json` twin, over the very view-model its partial renders.  A key the
view adds beyond these is ignored on the wire; a key these need and the view
lacks is a validation error -- the model is the spec, as the repo rules."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Row(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    codex_id: str
    stage: str
    unit: str
    kind: str
    home: str
    state: str
    shown: str
    glyph: str
    css: str
    step_id: str | None = None
    step_name: str = ""
    progress: str | None = None
    priority: int = 0
    sequence: int | None = None
    gpu: int = 0
    attempts: int = 0
    flags: int = 0
    run_id: str | None = None
    blocked_on: str | None = None
    started_at: str | None = None
    updated_at: str
    finished_at: str | None = None
    elapsed: str = ""
    gpu_seconds: float = 0.0
    cost_usd: float | None = None
    deliverable: str | None = None
    hold_reason: str | None = None
    note: str | None = None
    detail: str | None = None
    verdicts: dict[str, dict[str, Any]] = {}


class Chip(BaseModel):
    gate: str
    word: str
    glyph: str
    css: str
    by: str
    faults: int
    sha8: str
    path: str
    terminal: str


class DepartmentRow(Row):
    strip: list[Chip] = []


class Floor(BaseModel):
    running: list[Row]
    next: list[Row]


class Department(BaseModel):
    stage: str
    rows: list[DepartmentRow]
    gates: list[str]
    counts: dict[str, int]
    books: dict[str, str]


class StepChip(BaseModel):
    step_id: str
    name: str
    state: str
    glyph: str
    css: str
    attempt: int = 0
    run_id: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    seconds: float = 0.0
    verdict_by: str | None = None
    verdict_word: str | None = None
    verdict_path: str | None = None
    terminal: str = ""
    detail: str | None = None


class Thumb(BaseModel):
    kind: str
    rel: str
    url: str


class Deliverable(BaseModel):
    rel: str
    exists: bool
    url: str | None = None


class Unit(BaseModel):
    row: Row
    steps: list[StepChip]
    verdicts: list[Chip]
    deliverable: Deliverable | None = None
    thumbnails: list[Thumb]
    learnings: list[dict[str, Any]]
    log_name: str | None = None
    log: list[dict[str, Any]]
    timing: list[dict[str, Any]]
    running: bool
    book_name: str
