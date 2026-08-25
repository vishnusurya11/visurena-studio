"""Analysis stage worker.

DESIGN (owner, 2026-08-23): this runner scans the codex table for books whose
analysis is not complete, then processes them one by one. Eventually it runs
constantly (set POLL_SECONDS); today it does a single scan so runs are manual
and inspectable.

Steps come from stages.yaml (THE registry) — file order = execution order.
No CLI args by design: configuration is the variables below, or read from the DB.

Run: uv run python analysis.py
"""

from __future__ import annotations

import importlib
import time
from pathlib import Path

import yaml

from studio import db, llm, spend

REGISTRY_PATH = Path("stages.yaml")
STAGE = "analysis"
FINAL_STEP_ID = "06"      # analysis is complete when this step has a 'completed' event

# --- configuration (hardcoded; no CLI args by convention) ---
RUN_UNTIL_STEP = "06"     # manual mode: stop after this step ("06" = full pipeline)
POLL_SECONDS = None       # None = single scan and exit; e.g. 300 = daemon mode


def load_registry(stage: str = STAGE) -> dict:
    """Read one stage's entry from the single all-stages registry file."""
    with open(REGISTRY_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["stages"][stage]


def load_steps(stage: str = STAGE) -> list:
    """Resolve each registry entry to its script module, in file order."""
    steps = []
    for entry in load_registry(stage)["steps"]:
        module = importlib.import_module(f"scripts.{stage}.{entry['script']}")
        if module.STEP_ID != entry["id"]:
            raise ValueError(f"registry id {entry['id']!r} != script id {module.STEP_ID!r}")
        steps.append(module)
    return steps


def run_step(conn, codex_id: str, step) -> None:
    """Run one step, bracketed by STEP-LEVEL events.

    Steps write their own SUBSTEP events (01_01, 01_02 …) via Tracker. Nothing wrote the
    step id itself, so codex_pending_stage — which keys on exactly that — never matched
    and a finished book stayed pending forever. The runner owns this event because the
    runner is what decides a step is done. Same code in screenplay.py, deliberately.
    """
    db.add_event(conn, codex_id, STAGE, step.STEP_ID, "started")
    try:
        # Every paid call inside this block is attributed to (book, stage, step) with
        # no cooperation from the step itself — see studio/llm.spend_context.
        with llm.spend_context(conn, codex_id, STAGE, step.STEP_ID):
            step.run(codex_id)
    except Exception as exc:
        db.add_event(conn, codex_id, STAGE, step.STEP_ID, "failed", detail=str(exc)[:200])
        raise
    db.add_event(conn, codex_id, STAGE, step.STEP_ID, "completed")


def process(conn, codex_id: str) -> None:
    """Run the stage's steps for one book, stopping after RUN_UNTIL_STEP.

    Codex summary trio: running at start; completed only when the FINAL step ran;
    a partial (RUN_UNTIL_STEP) run stays 'running' = in progress; failed on error."""
    print(f"=== ANALYSIS start | codex_id={codex_id} ===")
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
    report_spend(conn, codex_id)
    print(f"=== ANALYSIS done | codex_id={codex_id} ===")


def report_spend(conn, codex_id: str) -> dict:
    """Print what this book actually cost, per step. Never let a spend be invisible."""
    totals = spend.total(conn, codex_id)
    if not totals["calls"]:
        return totals
    print(f"--- spend | {totals['calls']} call(s), "
          f"{totals['input_tokens']:,} in / {totals['output_tokens']:,} out, "
          f"${totals['cost_usd']:.4f}"
          + (f" (+{totals['unpriced_calls']} UNPRICED)" if totals["unpriced_calls"]
             else "") + " ---")
    for step_id, row in spend.by_step(conn, codex_id, STAGE).items():
        print(f"      step {step_id}: {row['calls']:4} call(s)  "
              f"{row['input_tokens']:>9,} in  {row['output_tokens']:>8,} out  "
              f"${row['cost_usd']:.4f}")
    return totals


def scan_once(conn) -> list[str]:
    """One pass: find books needing analysis, process each in id order."""
    pending = db.codex_pending_stage(conn, STAGE, FINAL_STEP_ID)
    print(f"scan: {len(pending)} book(s) pending analysis: {pending}")
    for codex_id in pending:
        process(conn, codex_id)
    return pending


def main(conn=None) -> None:
    conn = conn or db.get_connection()
    while True:
        scan_once(conn)
        if POLL_SECONDS is None:
            break
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
