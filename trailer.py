"""Trailer stage runner — the blind path.  A SIBLING of analysis.py and screenplay.py.

    uv run python trailer.py              # every book whose screenplay completed
    uv run python trailer.py <codex_id>   # one book

One 6-hour wall-clock ceiling per book, zero credits (every model runs on the local
ComfyUI), no questions: a failed gate climbs its adapt ladder and the terminal rung
always exists.  Contract per step: .claude/skills/trailer/BLUEPRINT.md.  Registry:
the `trailer` stage of stages.yaml — file order = execution order.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

import yaml

from studio import db, llm, paths
from studio.trailer_run import RunContext

REGISTRY_PATH = Path("stages.yaml")
STAGE = "trailer"
FINAL_STEP_ID = "10"
REQUIRES_STAGE = "screenplay"
REQUIRES_STEP_ID = "05"
TOOLS = ("ffmpeg",)
"""Executables the steps shell out to (beatmap.decode, sfx, assemble, qc,
deliver).  Asked for BEFORE the run opens: run 11's first launch inherited a
PATH without ffmpeg, spent step 01's LLM call, and died measuring the first
cue in step 03."""


def load_registry(stage: str = STAGE) -> dict:
    with open(REGISTRY_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["stages"][stage]


def _import_step(stage: str, entry: dict):
    module = importlib.import_module(f"scripts.{stage}.{entry['script']}")
    if module.STEP_ID != entry["id"]:
        raise ValueError(f"registry id {entry['id']!r} != script id {module.STEP_ID!r}")
    return module


def load_steps(stage: str = STAGE) -> list:
    """Every registry entry as a module, in file order."""
    return [_import_step(stage, entry) for entry in load_registry(stage)["steps"]]


def ready(conn) -> list[str]:
    return db.codex_ready_for_stage(conn, STAGE, FINAL_STEP_ID,
                                    REQUIRES_STAGE, REQUIRES_STEP_ID)


def preflight(tools: tuple[str, ...] = TOOLS) -> list[str]:
    """Every tool's resolved path, or a refusal naming the first one missing."""
    found = []
    for name in tools:
        path = shutil.which(name)
        if path is None:
            raise SystemExit(f"REFUSED: {name} is not on PATH; nothing was started")
        found.append(path)
    return found


def run_step(ctx: RunContext, step) -> None:
    """One step, bracketed by step-level events; its rungs summarised on completion."""
    ctx.open_step(step.STEP_ID)
    print(f"--- step {step.STEP_ID} ({step.NAME}) | "
          f"{ctx.budget.remaining(step.STEP_ID) / 60:.0f} min left ---")
    ctx.tracker.event(step.STEP_ID, "started")
    try:
        with llm.spend_context(ctx.conn, ctx.codex_id, STAGE, step.STEP_ID):
            step.run(ctx.codex_id, ctx)
    except SystemExit as exc:  # the CLI scripts REFUSE this way; here it is a failure
        ctx.tracker.event(step.STEP_ID, "failed", detail=str(exc)[:200])
        raise RuntimeError(str(exc)) from exc
    except Exception as exc:
        ctx.tracker.event(step.STEP_ID, "failed", detail=str(exc)[:200])
        raise
    detail = f"{ctx.rungs_in_step} rung(s) taken" if ctx.rungs_in_step else None
    ctx.tracker.event(step.STEP_ID, "completed", detail=detail)


def process(conn, codex_id: str) -> None:
    ctx = RunContext(conn, codex_id, paths.book_dir(codex_id))
    print(f"=== TRAILER start | codex_id={codex_id} | run {ctx.tracker.run_id} ===")
    db.mark_stage(conn, codex_id, STAGE, "running")
    try:
        for step in load_steps():
            run_step(ctx, step)
    except Exception:
        db.mark_stage(conn, codex_id, STAGE, "failed")
        raise
    db.mark_stage(conn, codex_id, STAGE, "completed")
    print(f"=== TRAILER done | {ctx.learnings_path} ===")


def main(argv: list[str], conn=None) -> None:
    conn = conn or db.get_connection()
    db.init_db(conn)  # idempotent; adds the stage's columns to a library.db that predates it
    preflight()
    books = argv or ready(conn)
    print(f"trailer: {len(books)} book(s): {books}")
    for codex_id in books:
        process(conn, codex_id)


if __name__ == "__main__":
    main(sys.argv[1:])
