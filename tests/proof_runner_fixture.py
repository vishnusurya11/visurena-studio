"""The REAL studio.step_runner.run_steps over fake step modules (2026-10-21_ep02_proof DESIGN 3).

A rehearsal names a write by the step the runner is in, and S0a stops the runner in front of a
step to copy a checkpoint; both are pinned against the real loop, not a copy of it.  Only the
helpers that reach the DB and the registry (the owner's orders and redos, the model-family free)
are stubbed; the loop, its skip rule, its between-steps boundary check and its pause line are real."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Iterable


def step(step_id: str, run: Callable = lambda ctx: None, done: bool = False) -> SimpleNamespace:
    """A step module: STEP_ID, NAME, run(ctx) and, when `done`, a done() that says its output exists."""
    mod = SimpleNamespace(STEP_ID=step_id, NAME=f"fake {step_id}", run=run)
    if done:
        mod.done = lambda ctx: True
    return mod


def context(home: Path | None) -> SimpleNamespace:
    events: list = []
    return SimpleNamespace(conn=None, codex_id="9999", stage="rehearsal_fixture", unit="ep01", label="ep01",
                           home=home, held=lambda: False, events=events, log=lambda *a, **k: None,
                           tracker=SimpleNamespace(run_id="r1", event=lambda *a, **k: events.append(a)))


def run_real_steps(steps: Iterable, home: Path | None = None) -> str:
    """studio.step_runner.run_steps itself, with the DB- and registry-bound helpers stubbed."""
    from studio import step_runner
    stubs = {"_orders_taken": lambda ctx: [], "_free_family": lambda st, ctx, last: last,
             "_wants_redo": lambda st, ctx: False, "_redo_cleared": lambda st, ctx: None}
    saved = {name: getattr(step_runner, name) for name in stubs}
    for name, stub in stubs.items():
        setattr(step_runner, name, stub)
    try:
        return step_runner.run_steps(context(home), list(steps))
    finally:
        for name, real in saved.items():
            setattr(step_runner, name, real)
