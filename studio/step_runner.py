"""Run a stage's steps over one unit, the way every format line does it.

    take the owner's orders (once, before the first step)
    skip when done  ->  started (STEP <id> start, the wall opens)  ->  run  ->  completed
                                 \\->  Escalation  ->  escalated, stop the unit
                                 \\->  Deferred    ->  deferred, stop the unit
                                 \\->  SystemExit / crash  ->  failed, raise

A step module exposes STEP_ID, NAME, run(ctx) and, optionally, done(ctx) (its
output exists) and GPU (it puts a job on ComfyUI).  The registry's ids and the
modules' ids must agree or nothing runs.  A `redo` order (studio/work_orders)
names a step that runs although done(); the redo clears when it completes.
"""
from __future__ import annotations

import importlib
import re
import sys
from contextlib import contextmanager

from studio import boundary, comfy, registry, run_budget, step_caps, step_wall, work_orders
from studio.deferral import Deferred
from studio.escalate import Escalation


def import_step(stage: str, entry: dict):
    module = importlib.import_module(f"scripts.{stage}.{entry['script']}")
    if module.STEP_ID != entry["id"]:
        raise ValueError(f"registry id {entry['id']!r} != script id {module.STEP_ID!r}")
    return module


def load_steps(stage: str) -> list:
    """Every registry entry as a module, in file order."""
    return [import_step(stage, entry) for entry in registry.steps(stage)]


class Outcome(str):
    """run_steps' word ('completed', 'escalated', ...) that also says which step ended the run."""
    step: str = ""

    def __new__(cls, word: str, step: str = ""):
        self = super().__new__(cls, word)
        self.step = step
        return self


REFUSAL = re.compile(r"^\s*(REFUSED|CAP )")


class _Tail:
    """Passes stdout through and remembers the last REFUSED / CAP line printed."""

    def __init__(self, inner):
        self.inner, self.last, self._partial = inner, "", ""

    def write(self, text):
        self._partial += text
        *lines, self._partial = self._partial.split(chr(10))
        self.last = next((l.strip() for l in reversed(lines) if REFUSAL.match(l)), self.last)
        return self.inner.write(text)

    def __getattr__(self, name):
        return getattr(self.inner, name)


@contextmanager
def _watching():
    tail, before = _Tail(sys.stdout), sys.stdout
    sys.stdout = tail
    try:
        yield tail
    finally:
        sys.stdout = before


def _with_refusal(text: str, tail: _Tail) -> str:
    """The failure text, plus the last refusal line the step printed when it is not in it."""
    return text if not tail.last or tail.last in text else f"{text} | {tail.last}"


def _free_family(step, ctx, last: str) -> str:
    """Free the engine's models when a GPU step's family differs from the last; the family now.
    Best effort: a failed free is logged and the step runs on (its time counts in the step)."""
    family = step_caps.family(step.STEP_ID, ctx.stage)
    if not getattr(step, "GPU", False) or family in ("none", "") or family == last:
        return last
    try:
        comfy.free_on_family(family)
    except Exception as exc:                              # noqa: BLE001 -- never fails the step
        ctx.log(f"family free {last or '-'} -> {family} failed: {type(exc).__name__}", step_id=step.STEP_ID,
                level="WARNING")
    return family


def _orders_taken(ctx) -> list:
    """The owner's pending orders for this unit, stamped with this run and applied; a taken
    redo is also receipted beside the episode (the only proof of an owner order, K12)."""
    rows = work_orders.take_orders(ctx.conn, ctx.codex_id, ctx.stage, ctx.unit or "book",
                                   ctx.tracker.run_id)
    work_orders.note_redos_taken(getattr(ctx, "home", None), rows)
    return rows


def _hooked(ctx, name: str, *args) -> None:
    """A context that keeps a clock of its own is told: `after_orders` once the owner's orders are
    taken (the episode's repair window, studio/repair_clock), `before_step` before each step runs."""
    hook = getattr(ctx, name, None)
    if callable(hook):
        hook(*args)


def _wants_redo(step, ctx) -> bool:
    return step.STEP_ID in work_orders.redo_steps(ctx.conn, ctx.codex_id, ctx.stage, ctx.unit or "book")


def _redo_cleared(step, ctx) -> None:
    if getattr(ctx, "home", None) is not None and work_orders.recorded(ctx.home, step.STEP_ID):
        work_orders.clear_taken(ctx.home, step.STEP_ID)
    work_orders.clear_redo(ctx.conn, ctx.codex_id, ctx.stage, ctx.unit or "book", step.STEP_ID)


def _done(step, ctx) -> bool:
    """The output is on disk -- unless the owner ordered the step run again."""
    done = getattr(step, "done", None)
    if not done or _wants_redo(step, ctx):
        return False
    return bool(done(ctx))


def _refuse_held(ctx, step) -> None:
    why = f"{ctx.hold.name} is there" if ctx.hold.exists() else "a hold row is open (studio_cli lift <id>)"
    raise SystemExit(f"HELD: {why}; {ctx.label} stops before step {step.STEP_ID}")


def _paused(step, ctx, why: str, started: bool = True) -> str:
    """The boundary flag ended the unit (C3_verdict #7): paused, never failed.
    A started step is closed `deferred` (the events table's word for a step
    that handed the unit back; it has no 'paused'); a step never started
    writes nothing."""
    line = boundary.PausedAtBoundary(why).line(ctx.label)
    if started:
        ctx.tracker.event(step.STEP_ID, "deferred", detail=line[:200])
    print(line)
    return boundary.OUTCOME


def _run_one(step, ctx) -> str:
    """One step's body: 'completed', or the word a gate stopped the unit with."""
    home = getattr(ctx, "home", None)
    try:
        with _watching() as tail:
            step.run(ctx)
    except boundary.PausedAtBoundary as stop:
        return _paused(step, ctx, str(stop))
    except (Escalation, Deferred) as gate:
        word = "escalated" if isinstance(gate, Escalation) else "deferred"
        line = gate.line(ctx.label)
        ctx.tracker.event(step.STEP_ID, word, detail=line[:200])
        ctx.log(line, step_id=step.STEP_ID, level="WARNING")
        print(line)
        return word
    except SystemExit as exc:
        if boundary.requested(home):             # a child script stopped on the flag
            return _paused(step, ctx, f"step {step.STEP_ID}: {str(exc)[:120]}")
        text = _with_refusal(str(exc), tail)
        ctx.tracker.event(step.STEP_ID, "failed", detail=text[:200])
        raise RuntimeError(text) from exc
    except Exception as exc:
        if boundary.requested(home):
            return _paused(step, ctx, f"step {step.STEP_ID}: {type(exc).__name__}")
        ctx.tracker.event(step.STEP_ID, "failed", detail=f"{type(exc).__name__}: {exc}"[:200])
        raise
    return "completed"


def _dark_row(step, ctx) -> None:
    """P12: what the budget would have said of this step, written and never acted on."""
    budget, home = getattr(ctx, "budget", None), step_wall.home_of(ctx)
    if budget is None or home is None:
        return
    row = run_budget.step_dark_row(budget, step.STEP_ID, ctx.step_wall.this_run())
    try:
        run_budget.append_dark(home, row) if row is not None else None
    except OSError:                                    # a watcher's row never fails the step
        pass


def run_steps(ctx, steps: list) -> str:
    """'completed'; 'escalated' when a step parked the unit; 'deferred' when a
    judge set it aside.  Raises on failure.  The word is an Outcome: it also names the step that
    ended the run (P13's drive.jsonl row)."""
    _orders_taken(ctx)
    _hooked(ctx, "after_orders")
    family, last = "", ""
    for step in steps:
        if getattr(step, "GPU", False) and ctx.held():
            _refuse_held(ctx, step)
        if _done(step, ctx):
            ctx.tracker.event(step.STEP_ID, "skipped", detail="output exists")
            print(f"--- step {step.STEP_ID} ({step.NAME}) skipped: output exists")
            continue
        if boundary.requested(getattr(ctx, "home", None)):
            return Outcome(_paused(step, ctx, f"before step {step.STEP_ID}", started=False), step.STEP_ID)
        print(f"--- step {step.STEP_ID} ({step.NAME}) | {ctx.label} ---")
        _hooked(ctx, "before_step", step.STEP_ID)
        ctx.tracker.event(step.STEP_ID, "started")
        ctx.step_wall = step_wall.open_wall(ctx, step)     # the cap table's wall (owner 2026-10-18)
        try:
            family = _free_family(step, ctx, family)         # best effort; the time is this step's
            with comfy.row_deadline(step_wall.deadline_of(ctx.step_wall)):   # P14: a text call stays in the row
                outcome = _run_one(step, ctx)
        finally:
            step_wall.record_spent(ctx, ctx.step_wall)     # a failed run's time is kept too
            _dark_row(step, ctx)
        step_wall.close_wall(ctx, ctx.step_wall)
        last = step.STEP_ID
        if outcome != "completed":
            return Outcome(outcome, step.STEP_ID)
        ctx.tracker.event(step.STEP_ID, "completed")
        _redo_cleared(step, ctx)
    return Outcome("completed", last)
