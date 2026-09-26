"""studio.py: the desk from a shell (decision 2026-09-25, "How a department is driven").

    uv run python studio.py tick [--book <codex>]              every book's rows refreshed; the counts
    uv run python studio.py queue <codex> <stage> [<unit>] [--priority N]
                                                                one row materialized and promoted; its state
    uv run python studio.py verify <codex> <stage> <unit>       rows against the disk; exit 1 on a disagreement
    uv run python studio.py board                               v_queue and v_attention as text tables

The tick materializes and promotes; the runner claims and settles; the owner's
hand is studio_cli.py (hold, lift, bump, retry, requeue, redo).  Nothing here
runs a step: a queued row is a request until the owner says it is an
instruction.  The `studio` package shadows this file's name, so a test loads
it by path.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from studio import approval, db, episode_home, registry, tick
from studio.stage_run import ledger_id

HOLD = approval.HOLD
QUEUE_COLUMNS = ("stage", "unit", "codex_id", "priority", "sequence", "step_id", "requested_at")
ATTENTION_COLUMNS = ("stage", "unit", "codex_id", "state", "step_id", "blocked_on", "updated_at")


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="studio.py", description=__doc__.split("\n\n")[0])
    sub = top.add_subparsers(dest="command", required=True)
    sub.add_parser("tick", help="refresh every book's rows").add_argument("--book", help="one codex id")
    queue = sub.add_parser("queue", help="materialize one row and promote it")
    queue.add_argument("codex"), queue.add_argument("stage"), queue.add_argument("unit", nargs="?")
    queue.add_argument("--priority", type=int, help="lower first; 0 = bumped")
    verify = sub.add_parser("verify", help="rows against the disk; resolves nothing")
    verify.add_argument("codex"), verify.add_argument("stage"), verify.add_argument("unit")
    sub.add_parser("board", help="the queue and the attention strip, as text")
    return top


def _book(library: Path, codex: str) -> tuple[str, Path]:
    """(the ledger id, the book folder) or a refusal naming what is missing."""
    codex_id = ledger_id(codex)
    book = tick.book_folder(library, codex_id)
    if book is None:
        raise SystemExit(f"REFUSED: no folder for {codex_id} under the library {library}")
    return codex_id, book


def _unit(stage: str, unit: str | None) -> str:
    """The unit named, or the book-level name; a chapter-grain stage needs one."""
    if unit:
        return unit
    if "chapter" in registry.unit_of(stage):
        raise SystemExit(f"say which unit: studio.py queue <codex> {stage} <unit>")
    return tick.book_unit(stage)


def _tick(conn, args, library: Path) -> int:
    ids = [ledger_id(args.book)] if args.book else None
    counts = tick.tick(conn, library, ids, hold_path=HOLD)
    print(" ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


def _queue(conn, args, library: Path) -> int:
    codex_id, book = _book(library, args.codex)
    unit = _unit(args.stage, args.unit)
    tick.materialize(conn, codex_id, args.stage, [unit])
    if args.priority is not None:
        db.upsert_work_order(conn, codex_id, args.stage, unit, priority=args.priority)
    tick.settle_skipped(conn, codex_id, args.stage, unit, book)
    state = tick.promote(conn, codex_id, args.stage, unit, book)
    row = db.work_order(conn, codex_id, args.stage, unit)
    print(" ".join(filter(None, (f"{args.stage}/{unit}", state, row["blocked_on"]))))
    return 0


def _verify(conn, args, library: Path) -> int:
    codex_id, book = _book(library, args.codex)
    lines = tick.verify(conn, codex_id, args.stage, args.unit, book)
    print("\n".join(lines) if lines else f"{args.stage}/{args.unit}: rows and disk agree")
    return 1 if lines else 0


def table(rows: list, columns: tuple[str, ...]) -> str:
    """Rows as an aligned text table under a header and a rule; '(none)' for no rows."""
    if not rows:
        return "(none)"
    cells = [[("" if row[col] is None else str(row[col])) for col in columns] for row in rows]
    widths = [max(len(col), *(len(line[i]) for line in cells)) for i, col in enumerate(columns)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*columns), "  ".join("-" * w for w in widths)]
    return "\n".join(lines + [fmt.format(*line) for line in cells])


def _board(conn, args, library: Path) -> int:
    queue = list(conn.execute("SELECT * FROM v_queue"))
    attention = list(conn.execute("SELECT * FROM v_attention"))
    print(f"QUEUE ({len(queue)})\n{table(queue, QUEUE_COLUMNS)}\n")
    print(f"NEEDS YOU ({len(attention)})\n{table(attention, ATTENTION_COLUMNS)}")
    return 0


COMMANDS = {"tick": _tick, "queue": _queue, "verify": _verify, "board": _board}


def main(argv: list[str], conn=None, library: Path | None = None) -> int:
    args = parser().parse_args(argv)
    conn = conn or db.get_connection()
    db.init_db(conn)
    return COMMANDS[args.command](conn, args, Path(library or episode_home.LIBRARY))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
