"""Screenplay stage worker — a SIBLING of analysis.py, never a step inside it.

DESIGN (docs/screenplay/DESIGN.md): analysis ASSERTS what the book says; a screenplay
INVENTS. Putting an inventing step inside an asserting stage would make the grounding
apparatus that earns analysis its trust stop meaning anything. So this is its own stage,
with its own step ids (events key on (codex_id, stage, step_id), so screenplay/01 never
collides with analysis/01).

The one behavioural difference from analysis.py: this stage has a PREREQUISITE. It scans
for books whose analysis has *completed*, not merely for books that lack a screenplay.

One analysis feeds MANY screenplays, so the real unit of work is (book, target). Targets
are hardcoded below until there is a second one worth choosing between.

Steps come from stages.yaml (THE registry) — file order = execution order.
No CLI args by design: configuration is the variables below, or read from the DB.

Run: uv run python screenplay.py
"""

from __future__ import annotations

import importlib
import time
from pathlib import Path

import yaml

from studio import db

REGISTRY_PATH = Path("stages.yaml")
STAGE = "screenplay"
FINAL_STEP_ID = "05"      # screenplay is complete when this step has a 'completed' event

REQUIRES_STAGE = "analysis"     # a screenplay may only be built on finished analysis
REQUIRES_STEP_ID = "06"

# --- configuration (hardcoded; no CLI args by convention) ---
TARGET = "feature"        # which target to build; targets.yaml will hold the configs
RUN_UNTIL_STEP = "01"     # only step 01 is built; raise as steps land ("05" = full)
POLL_SECONDS = None       # None = single scan and exit; e.g. 300 = daemon mode


def load_registry(stage: str = STAGE) -> dict:
    """Read one stage's entry from the single all-stages registry file."""
    with open(REGISTRY_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["stages"][stage]


def _import_step(stage: str, entry: dict):
    """Import one registry entry's module and assert it agrees about its own id."""
    module = importlib.import_module(f"scripts.{stage}.{entry['script']}")
    if module.STEP_ID != entry["id"]:
        raise ValueError(f"registry id {entry['id']!r} != script id {module.STEP_ID!r}")
    return module


def load_steps(stage: str = STAGE, run_until: str | None = None) -> list:
    """Resolve registry entries to modules, in file order, stopping after `run_until`.

    Imports LAZILY, unlike analysis.py, because this stage is being built one step at
    a time: an unwritten step 03 must not stop step 01 from running.
    """
    limit = RUN_UNTIL_STEP if run_until is None else run_until
    steps = []
    for entry in load_registry(stage)["steps"]:
        steps.append(_import_step(stage, entry))
        if limit and entry["id"] >= limit:
            break
    return steps


def run_step(conn, codex_id: str, step) -> None:
    """Run one step, bracketed by STEP-LEVEL events.

    Steps write their own SUBSTEP events (01_01, 01_02 …) via Tracker. Nothing wrote the
    step id itself, so `codex_pending_stage` and `codex_ready_for_stage` — which key on
    exactly that — could never match, and a finished book stayed pending forever. The
    runner owns the step-level event because the runner is what decides a step is done.
    """
    db.add_event(conn, codex_id, STAGE, step.STEP_ID, "started")
    try:
        step.run(codex_id)
    except Exception as exc:
        db.add_event(conn, codex_id, STAGE, step.STEP_ID, "failed", detail=str(exc)[:200])
        raise
    db.add_event(conn, codex_id, STAGE, step.STEP_ID, "completed")


def process(conn, codex_id: str) -> None:
    """Run the stage's steps for one book, stopping after RUN_UNTIL_STEP.

    Codex summary trio: running at start; completed only when the FINAL step ran;
    a partial (RUN_UNTIL_STEP) run stays 'running' = in progress; failed on error."""
    print(f"=== SCREENPLAY start | codex_id={codex_id} target={TARGET} ===")
    db.mark_stage(conn, codex_id, STAGE, "running")
    last_run = None
    try:
        for step in load_steps():
            print(f"--- step {step.STEP_ID} ({step.NAME}) ---")
            run_step(conn, codex_id, step)
            last_run = step.STEP_ID
            if RUN_UNTIL_STEP and step.STEP_ID >= RUN_UNTIL_STEP:
                print(f"=== stopping after step {step.STEP_ID} (RUN_UNTIL_STEP) ===")
                break
    except Exception:
        db.mark_stage(conn, codex_id, STAGE, "failed")
        raise
    if last_run == FINAL_STEP_ID:
        db.mark_stage(conn, codex_id, STAGE, "completed")
    print(f"=== SCREENPLAY done | codex_id={codex_id} ===")


def scan_once(conn) -> list[str]:
    """One pass: find books with finished analysis and no screenplay, process each."""
    ready = db.codex_ready_for_stage(
        conn, STAGE, FINAL_STEP_ID, REQUIRES_STAGE, REQUIRES_STEP_ID)
    print(f"scan: {len(ready)} book(s) ready for screenplay: {ready}")
    for codex_id in ready:
        process(conn, codex_id)
    return ready


def main(conn=None) -> None:
    conn = conn or db.get_connection()
    while True:
        scan_once(conn)
        if POLL_SECONDS is None:
            break
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
