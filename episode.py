"""Episode stage runner -- one unit is one episode folder.  A SIBLING of trailer.py.

    uv run python episode.py <codex_id> <n> [--flag ...]   # one unit: its own row claimed
    uv run python episode.py <codex_id>                    # the queue: every row the desk has
                                                           # queued for this book, in priority,
                                                           # sequence order -- then exit
    uv run python episode.py <codex_id> --all              # the old form: every episodes/epNN
                                                           # with a plan, ascending, off the disk

The queue form (decision 2026-09-25, "Explicit invocation") takes what is
queued NOW and exits: no loop, no sleep, no poll.  A deferred, blocked or held
row is never taken.  Each unit is claimed (claimed_by, a 15-minute lease the
tracker's writes renew, run_id) before its steps and released after; a claim
that fails -- another run took it, the desk moved it -- is skipped with a
printed line.  The explicit form claims its own queued row; a HELD row is
REFUSED naming the hold; a row that says blocked (or any other state) is a
WARN and the unit runs anyway: the disk is the truth of a step; no row at all
(a book the desk never ticked) runs as before.  `units()` stays for `--all`.

Steps come from the `episode` stage of stages.yaml (studio/step_runner); a
step whose output is on disk is skipped; an owner gate parks the unit with an
`escalated` event and the call-sheet line, and the runner exits 2 having marked
nothing failed.  Flags after the unit reach the step that runs (`ctx.extra`).
Zero credits: every model is the local ComfyUI.  ffmpeg is asked for BEFORE
the run opens, as trailer.py learned to.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from studio import db, episode_home, episode_run, llm, queue, step_runner, tick
from studio.stage_run import ledger_id

STAGE = episode_run.STAGE
TOOLS = ("ffmpeg",)
PARKED = 2
ALL = "--all"


def preflight(tools: tuple[str, ...] = TOOLS) -> list[str]:
    """Every tool's resolved path, or a refusal naming the first one missing."""
    found = []
    for name in tools:
        path = shutil.which(name)
        if path is None:
            raise SystemExit(f"REFUSED: {name} is not on PATH; nothing was started")
        found.append(path)
    return found


def units(book: Path) -> list[int]:
    """Every episode folder that has a plan, ascending (the `--all` form's units)."""
    root = Path(book) / "episodes"
    if not root.is_dir():
        return []
    return sorted(int(p.name[2:]) for p in root.glob("ep[0-9][0-9]") if (p / "plan.json").exists())


def number_of(unit: str) -> int:
    """epNN -> NN: the inverse of episode_run.unit_of."""
    return int(unit[2:])


def queued(conn, codex_id: str) -> list[int]:
    """The desk's queue for this book's episode line, first to run first."""
    return [number_of(unit) for unit in queue.queued_units(conn, ledger_id(codex_id), STAGE)]


def parse(argv: list[str]) -> tuple[str, int | None, list[str]]:
    """(codex_id, episode number or None, the --flags)."""
    plain = [a for a in argv if not a.startswith("--")]
    if not plain:
        raise SystemExit("usage: episode.py <codex_id> [<n>] [--flag ...]")
    number = int(plain[1]) if len(plain) > 1 and plain[1].isdigit() else None
    return plain[0], number, [a for a in argv if a.startswith("--")]


def _context(conn, codex_id: str, number: int, extra: list[str], **kw):
    """The unit's context, the flags on it.  Its tracker's start ticks the book."""
    ctx = episode_run.context(conn, codex_id, number, **kw)
    ctx.extra = list(extra)
    return ctx


def run_unit(ctx) -> str:
    """One unit through every step: 'completed', 'escalated' or 'deferred'; a
    failure raises after the stage is marked failed."""
    print(f"=== EPISODE start | {ctx.label} | run {ctx.tracker.run_id} ===")
    db.mark_stage(ctx.conn, ctx.codex_id, STAGE, "running")
    try:
        # every paid call inside is the unit's, attributed to the step the journal started
        with llm.spend_context(ctx.conn, ctx.codex_id, STAGE, None, unit=ctx.unit):
            outcome = step_runner.run_steps(ctx, step_runner.load_steps(STAGE))
    except Exception:
        db.mark_stage(ctx.conn, ctx.codex_id, STAGE, "failed")
        raise
    if outcome == "completed":
        db.mark_stage(ctx.conn, ctx.codex_id, STAGE, "completed")
    print(f"=== EPISODE {outcome} | {ctx.label} ===")
    return outcome


def process(conn, codex_id: str, number: int, extra: list[str], **kw) -> str:
    """One unit through every step, no claim: the `--all` form and the tests' door."""
    return run_unit(_context(conn, codex_id, number, extra, **kw))


def take(conn, codex_id: str, number: int, extra: list[str], **kw) -> str | None:
    """The queue form's unit: claimed under its run, run, released.  None and
    a printed line when the claim failed -- another run took it, or the desk
    moved it between the read and the claim."""
    ctx = _context(conn, codex_id, number, extra, **kw)
    if not queue.claim(conn, ctx.codex_id, STAGE, ctx.unit, ctx.tracker.run_id):
        print(f"SKIPPED {ctx.label}: not queued any more (another run took it, or the desk moved it)")
        return None
    try:
        return run_unit(ctx)
    finally:
        queue.release(conn, ctx.codex_id, STAGE, ctx.unit, ctx.tracker.run_id)


def take_explicit(conn, codex_id: str, number: int, extra: list[str], **kw) -> str:
    """The `<n>` form: its own row claimed when queued; REFUSED when held,
    naming the hold; otherwise a WARN naming the row's word and want, and the
    unit runs -- the disk is the truth of a step (queue.explicit_claim)."""
    ctx = _context(conn, codex_id, number, extra, **kw)
    word, why = queue.explicit_claim(conn, ctx.codex_id, STAGE, ctx.unit, ctx.tracker.run_id)
    if word == "held":
        raise SystemExit(f"REFUSED: {ctx.label} is held ({why}); lift it (studio_cli.py lift <id>) and run again")
    if word not in ("claimed", "none"):
        want = f" on {why}" if why else ""
        print(f"WARN {ctx.label}: the desk says {word}{want}; running on the owner's word -- the disk is the truth of a step")
    try:
        return run_unit(ctx)
    finally:
        queue.release(conn, ctx.codex_id, STAGE, ctx.unit, ctx.tracker.run_id)


def run_all(conn, codex_id: str, extra: list[str], **kw) -> list[str]:
    """The `--all` form: every planned folder off the disk, the flag kept from the steps."""
    extra = [a for a in extra if a != ALL]
    numbers = units(episode_home.book_dir(codex_id))
    if not numbers:
        raise SystemExit(f"REFUSED: no episodes/epNN folder with a plan.json for {codex_id}")
    return [process(conn, codex_id, n, extra, **kw) for n in numbers]


def run_queue(conn, codex_id: str, extra: list[str], **kw) -> list[str | None]:
    """The queue form: what the desk has queued now, in its order, then exit."""
    numbers = queued(conn, codex_id)
    if not numbers:
        raise SystemExit(f"REFUSED: nothing queued for {codex_id} {STAGE}; `studio.py board` shows"
                         f" the desk, `{ALL}` runs every planned folder off the disk")
    return [take(conn, codex_id, n, extra, **kw) for n in numbers]


def exit_code(outcomes: list[str | None]) -> int:
    """0 when every unit completed; PARKED (2) when one was parked, deferred or skipped."""
    return PARKED if any(o != "completed" for o in outcomes) else 0


def main(argv: list[str], conn=None, tools: tuple[str, ...] = TOOLS, **kw) -> int:
    codex_id, number, extra = parse(argv)
    conn = conn or db.get_connection()
    db.init_db(conn)
    preflight(tools)
    tick.tick_book(conn, codex_id)  # the desk refreshed before its rows are read; never a stop
    if number is not None:
        return exit_code([take_explicit(conn, codex_id, number, extra, **kw)])
    if ALL in extra:
        return exit_code(run_all(conn, codex_id, extra, **kw))
    return exit_code(run_queue(conn, codex_id, extra, **kw))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
