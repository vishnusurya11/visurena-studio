"""The owner's hand from a shell: one row per command, its id printed.

    uv run python studio_cli.py hold <studio|book|unit> [--book <codex>] [--stage s] [--unit u] --reason "..."
    uv run python studio_cli.py lift <hold_id>
    uv run python studio_cli.py bump|retry|requeue <codex> <stage> <unit>
    uv run python studio_cli.py redo <codex> <stage> <unit> <step_id> --note "..." [--artefact p] [--class c]

A hold stops every GPU step it reaches, at once; a lift opens it.  The unit
orders wait in `orders` until that unit's runner takes them at the top of its
next run (studio/work_orders).  A redo's note is also an owner row in the
book's casebook, about `--artefact` (book-relative) -- by default the step's
first declared output, when that is a path the casebook can read.  Nothing
here runs a step; `queue` is the tick's (studio.py).
"""
from __future__ import annotations

import argparse
import sys

from studio import db, work_orders
from studio.stage_run import ledger_id


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="studio_cli.py", description=__doc__.split("\n\n")[0])
    sub = top.add_subparsers(dest="command", required=True)
    hold = sub.add_parser("hold", help="stop every GPU step the scope reaches")
    hold.add_argument("scope", choices=work_orders.SCOPES)
    hold.add_argument("--book", help="the codex id (book and unit scope)")
    hold.add_argument("--stage"), hold.add_argument("--unit")
    hold.add_argument("--reason", required=True)
    sub.add_parser("lift", help="open one hold").add_argument("hold_id", type=int)
    for kind in ("bump", "retry", "requeue"):
        _unit_args(sub.add_parser(kind, help=f"a {kind} order on one unit"))
    redo = _unit_args(sub.add_parser("redo", help="run a done step again, with a note"))
    redo.add_argument("step_id"), redo.add_argument("--note", required=True)
    redo.add_argument("--artefact", help="book-relative path the note is about")
    redo.add_argument("--class", dest="fault", default="unknown", help="a casebook fault class")
    return top


def _unit_args(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    p.add_argument("codex"), p.add_argument("stage"), p.add_argument("unit")
    return p


def _hold(conn, args) -> int:
    codex = ledger_id(args.book) if args.book else None
    return work_orders.hold(conn, args.scope, args.reason, codex_id=codex, stage=args.stage, unit=args.unit)


def _lift(conn, args) -> int:
    return work_orders.lift(conn, args.hold_id)


def _unit_order(conn, args) -> int:
    return work_orders.order(conn, args.command, "unit", codex_id=ledger_id(args.codex),
                             stage=args.stage, unit=args.unit)


def _redo(conn, args) -> int:
    return work_orders.order(conn, "redo", "unit", codex_id=ledger_id(args.codex), stage=args.stage,
                             unit=args.unit, step_id=args.step_id, note=args.note,
                             artefact=work_orders.default_artefact(args.stage, args.step_id, args.unit, args.artefact),
                             fault=args.fault)


COMMANDS = {"hold": _hold, "lift": _lift, "bump": _unit_order, "retry": _unit_order,
            "requeue": _unit_order, "redo": _redo}


def main(argv: list[str], conn=None) -> int:
    args = parser().parse_args(argv)
    conn = conn or db.get_connection()
    db.init_db(conn)
    try:
        print(COMMANDS[args.command](conn, args))
    except ValueError as exc:
        raise SystemExit(f"REFUSED: {exc}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
