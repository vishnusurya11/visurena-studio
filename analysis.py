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

from studio import db

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
            step.run(codex_id)
            last_run = step.STEP_ID
            if RUN_UNTIL_STEP and step.STEP_ID >= RUN_UNTIL_STEP:
                print(f"=== stopping after step {step.STEP_ID} (RUN_UNTIL_STEP) ===")
                break
    except Exception:
        db.mark_stage(conn, codex_id, STAGE, "failed")
        raise
    if last_run == FINAL_STEP_ID:
        db.mark_stage(conn, codex_id, STAGE, "completed")
    print(f"=== ANALYSIS done | codex_id={codex_id} ===")


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
