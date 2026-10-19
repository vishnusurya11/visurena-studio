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
    age: str = ""                    # "2 m" since updated_at (panel ruling 1.8)
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
    # the redesigned page's bands (research F/G); optional so an older view still validates
    head: dict[str, Any] | None = None
    bar: list[dict[str, Any]] = []
    health: dict[str, Any] | None = None
    gates: list[dict[str, Any]] = []
    pictures: dict[str, Any] | None = None
    master: dict[str, Any] | None = None
    orders: list[dict[str, Any]] = []
    hold: dict[str, Any] | None = None
    suggest: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


# --- the pulse (panel ruling 2026-10-04, contract C1) ---


class Pin(BaseModel):
    href: str
    label: str
    state: str


class Gpu(BaseModel):
    href: str | None = None
    unit: str | None = None
    step: str | None = None
    frac: float | None = None        # 0..1 from the run's start to its finish
    finish: str | None = None        # "21:35" (local)
    vital: str | None = None
    held: bool = False


class Hold(BaseModel):
    id: int
    since: str
    reason: str


class Engine(BaseModel):
    busy: bool                       # ComfyUI runs a prompt (comfy_tap), whoever queued it
    running: int
    pending: int
    who: str = ""                    # `refs/looks_table.py · Jekyll` from the process table


class AutopilotLine(BaseModel):
    codex: str
    book: str
    state: str                       # paused, complete, running, parked, ...
    why: str = ""
    age: str = ""


class Shell(BaseModel):
    needs: int                       # views.inbox_count(): the one "needs you" number
    queue: int
    dept_dots: dict[str, dict[str, int]]
    pins: list[Pin]
    gpu: Gpu | None = None
    hold: Hold | None = None
    engine: Engine | None = None     # None while ComfyUI is down (board review 2026-10-12)
    autopilot: list[AutopilotLine] = []


class Event(BaseModel):
    model_config = ConfigDict(extra="allow")   # an order receipt also carries `order`
    id: int | str                    # an events row id, or `ord-<orders id>`
    ts: str
    href: str | None = None
    unit: str
    text: str


class Pulse(BaseModel):
    boot: float                      # the server's start: a new one means reload
    now: float
    fp: dict[str, str]               # shell, floor, attention, orders, lanes, dept:*, book:*, unit:*
    shell: Shell
    events: list[Event]
    cursor: int


# --- the episode progress card (progress tracker spec §3) ---


class RailStep(BaseModel):
    id: str
    name: str
    state: str                       # waiting | running | done | skip | fail | deferred | refused | escalated
    secs: float | None = None        # this run: done -> measured, running -> elapsed so far
    median_s: float | None = None    # the measured norm the rail's width is proportional to
    retries: int = 0                 # runs of this unit that started the step before this one
    will_run: bool | None = None     # a later step: runs again in this run (eta.will_run); None = not later
    window: str = ""                 # a later step: "~18m" projected, "kept" (this make) or "—"
    when: str = ""                   # a later step's Seattle window "5:01–5:19 pm" (the tooltip)
    end: float | None = None         # this run: when the step ended
    made: dict[str, float] | None = None   # this make: {secs, end} from timing.jsonl
    fin: str = ""                    # a finished step: "50m · 3:52 pm" (Seattle)


class Sampler(BaseModel):
    k: int
    of: int
    phase: str


class Rung(BaseModel):
    gate: str
    measured: float | None = None
    action: str
    terminal: bool = False


class NowStep(BaseModel):
    id: str
    name: str
    kind: str                        # counted | loop
    done: int = 0
    total: int = 0
    weight_done: float = 0.0
    weight_total: float = 0.0
    current: str | None = None
    sampler: Sampler | None = None
    rounds: list[Rung] = []


class Item(BaseModel):
    id: str
    state: str                       # waiting | rendering | landed | failed | retake
    panel: str | None = None         # under `media_base` (+ ?v=mtime): the panel thumbnail
    video: str | None = None         # under `lib_base` (+ ?v=mtime): the take, loaded on hover only
    secs: float | None = None
    prior_s: float | None = None     # the take's modelled seconds x pace: drives the developing tile


class Eta(BaseModel):
    finish_at: float | None = None   # epoch, rounded to five minutes
    lo: float | None = None
    hi: float | None = None
    finish: str = ""                 # "6:45 pm" (Seattle): the EPISODE's finish, never the step's
    finish_raw: float | None = None  # the unrounded finish the time left counts to
    left_s: float | None = None
    left: str = ""                   # "3h 05m": the hero, the card's biggest words
    range: str = ""                  # "6:15–7:15 pm"
    step_end: str = ""               # "5:01 pm" (Seattle): the running step's projected end; "" past its p90
    steps_left: int = 0              # later steps that will run in this run
    basis: str = "estimate"          # norm | measured | estimate
    n_runs: int = 0
    long: bool = False
    capped: bool = False


class Progress(BaseModel):
    codex: str
    unit: str
    run_id: str | None = None
    vital: str                       # live | quiet | stalled | dead | refused | deferred | done | idle
    vital_reason: str = ""
    quiet_s: float | None = None
    budget_s: float | None = None
    run_started: float | None = None
    step_started: float | None = None
    now: float
    elapsed_s: float = 0.0
    work_s: float = 0.0
    ceiling_s: float = 0.0           # the 5 h rung ceiling (run_budget.EPISODE_CEILING_SECONDS)
    limit_s: float = 0.0             # the owner's 6 h (run_budget.OWNER_LIMIT_SECONDS): the episode clock's "of"
    steps: list[RailStep] = []
    now_step: NowStep | None = None
    items: list[Item] = []
    inflight_started: float | None = None
    media_base: str = ""
    lib_base: str = ""
    eta: Eta = Eta()
    trace: list[float] = []
    last_words: str = ""
    why: str = ""                    # the run's newest warning or refusal (legacy_progress.why_of)
    title: str = ""
    master: str | None = None
    qc: dict[str, Any] | None = None
