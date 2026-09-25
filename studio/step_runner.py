"""Run a stage's steps over one unit, the way every format line does it.

    skip when done  ->  started  ->  run  ->  completed
                                 \\->  Escalation  ->  escalated, stop the unit
                                 \\->  SystemExit / crash  ->  failed, raise

A step module exposes STEP_ID, NAME, run(ctx) and, optionally, done(ctx) (its
output exists) and GPU (it puts a job on ComfyUI).  The registry's ids and the
modules' ids must agree or nothing runs.
"""
from __future__ import annotations

import importlib

from studio import registry
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


def _done(step, ctx) -> bool:
    done = getattr(step, "done", None)
    return bool(done(ctx)) if done else False


def run_steps(ctx, steps: list) -> str:
    """'completed'; 'escalated' when a step parked the unit; 'deferred' when a
    judge set it aside.  Raises on failure."""
    for step in steps:
        if getattr(step, "GPU", False) and ctx.held():
            raise SystemExit(f"HELD: {ctx.hold.name} is there; {ctx.label} stops before step {step.STEP_ID}")
        if _done(step, ctx):
            ctx.tracker.event(step.STEP_ID, "skipped", detail="output exists")
            print(f"--- step {step.STEP_ID} ({step.NAME}) skipped: output exists")
            continue
        print(f"--- step {step.STEP_ID} ({step.NAME}) | {ctx.label} ---")
        ctx.tracker.event(step.STEP_ID, "started")
        try:
            step.run(ctx)
        except Escalation as gate:
            line = gate.line(ctx.label)
            ctx.tracker.event(step.STEP_ID, "escalated", detail=line[:200])
            ctx.log(line, step_id=step.STEP_ID, level="WARNING")
            print(line)
            return "escalated"
        except Deferred as aside:
            line = aside.line(ctx.label)
            ctx.tracker.event(step.STEP_ID, "deferred", detail=line[:200])
            ctx.log(line, step_id=step.STEP_ID, level="WARNING")
            print(line)
            return "deferred"
        except SystemExit as exc:
            ctx.tracker.event(step.STEP_ID, "failed", detail=str(exc)[:200])
            raise RuntimeError(str(exc)) from exc
        except Exception as exc:
            ctx.tracker.event(step.STEP_ID, "failed", detail=f"{type(exc).__name__}: {exc}"[:200])
            raise
        ctx.tracker.event(step.STEP_ID, "completed")
    return "completed"
