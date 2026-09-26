"""Refs stage runner -- the reference bible.  A SIBLING of analysis.py and trailer.py.

    uv run python refs.py                                   # every book whose analysis/05 completed
    uv run python refs.py <codex_id> --chapter=N --cast=a,b=Display:gender [--kind=..] [--only=..]

One unit per book today ("main", studio/refs_run.py); the steps come from the
registry's `refs` block in file order; a step whose output is on disk is skipped;
the LOOK gate is judged (judge:look); an `escalated` outcome is a legacy path the
runner still honours with an event and a printed call-sheet
line (exit 2) -- never a `failed`.  Flags pass through to the steps as ctx.extra.
"""
from __future__ import annotations

import sys

from studio import db, llm, refs_run, registry, step_runner

STAGE = refs_run.STAGE
FINAL_STEP_ID = registry.steps(STAGE)[-1]["id"]


def ready(conn) -> list[str]:
    """Books that completed every stage this one requires and have not finished it."""
    books: list[str] | None = None
    for requirement in registry.requires_of(STAGE):
        after, step_id = requirement.split("/")
        found = db.codex_ready_for_stage(conn, STAGE, FINAL_STEP_ID, after, step_id)
        books = found if books is None else [b for b in books if b in found]
    return books or []


def split(argv: list[str]) -> tuple[list[str], list[str]]:
    """Plain arguments (books) apart from the flags the steps read."""
    return [a for a in argv if not a.startswith("--")], [a for a in argv if a.startswith("--")]


def process(conn, codex_id: str, extra=(), **kw) -> str:
    """One book through every refs step: 'completed', or 'escalated' when parked."""
    ctx = refs_run.context(conn, codex_id, **kw)
    ctx.extra = list(extra)
    print(f"=== REFS start | {ctx.label} | run {ctx.tracker.run_id} ===")
    db.mark_stage(conn, ctx.codex_id, STAGE, "running")
    try:
        # every paid call inside is the pack's, attributed to the step the journal started
        with llm.spend_context(conn, ctx.codex_id, STAGE, None, unit=ctx.unit):
            outcome = step_runner.run_steps(ctx, step_runner.load_steps(STAGE))
    except Exception:
        db.mark_stage(conn, ctx.codex_id, STAGE, "failed")
        raise
    # parked at an owner gate is neither running nor failed: it waits
    db.mark_stage(conn, ctx.codex_id, STAGE, "completed" if outcome == "completed" else "pending")
    print(f"=== REFS {outcome} | {ctx.label} ===")
    return outcome


def main(argv: list[str], conn=None, **kw) -> int:
    conn = conn or db.get_connection()
    db.init_db(conn)
    books, extra = split(argv)
    books = books or ready(conn)
    print(f"refs: {len(books)} book(s): {books}")
    outcomes = [process(conn, codex_id, extra, **kw) for codex_id in books]
    return 2 if "escalated" in outcomes else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
