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

from studio import boundary, registry, step_wall, work_orders
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


def _orders_taken(ctx) -> list:
    """The owner's pending orders for this unit, stamped with this run and applied."""
    return work_orders.take_orders(ctx.conn, ctx.codex_id, ctx.stage, ctx.unit or "book",
                                   ctx.tracker.run_id)


def _wants_redo(step, ctx) -> bool:
    return step.STEP_ID in work_orders.redo_steps(ctx.conn, ctx.codex_id, ctx.stage, ctx.unit or "book")


def _redo_cleared(step, ctx) -> None:
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
        ctx.tracker.event(step.STEP_ID, "failed", detail=str(exc)[:200])
        raise RuntimeError(str(exc)) from exc
    except Exception as exc:
        if boundary.requested(home):
            return _paused(step, ctx, f"step {step.STEP_ID}: {type(exc).__name__}")
        ctx.tracker.event(step.STEP_ID, "failed", detail=f"{type(exc).__name__}: {exc}"[:200])
        raise
    return "completed"


def run_steps(ctx, steps: list) -> str:
    """'completed'; 'escalated' when a step parked the unit; 'deferred' when a
    judge set it aside.  Raises on failure."""
    _orders_taken(ctx)
    for step in steps:
        if getattr(step, "GPU", False) and ctx.held():
            _refuse_held(ctx, step)
        if _done(step, ctx):
            ctx.tracker.event(step.STEP_ID, "skipped", detail="output exists")
            print(f"--- step {step.STEP_ID} ({step.NAME}) skipped: output exists")
            continue
        if boundary.requested(getattr(ctx, "home", None)):
            return _paused(step, ctx, f"before step {step.STEP_ID}", started=False)
        print(f"--- step {step.STEP_ID} ({step.NAME}) | {ctx.label} ---")
        ctx.tracker.event(step.STEP_ID, "started")
        ctx.step_wall = step_wall.open_wall(ctx, step)     # the cap table's wall (owner 2026-10-18)
        outcome = _run_one(step, ctx)
        step_wall.close_wall(ctx, ctx.step_wall)
        if outcome != "completed":
            return outcome
        ctx.tracker.event(step.STEP_ID, "completed")
        _redo_cleared(step, ctx)
    return "completed"
