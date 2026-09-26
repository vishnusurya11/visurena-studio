#!/usr/bin/env python
"""One finding of the owner's, into the casebook.

    uv run python scripts/audit/note.py <codex_id> <unit> <artefact> <class> "<words>"

`<artefact>` is a path relative to the book (as the audit sheet prints it);
`<class>` is a fault class from studio.casebook.CLASSES, or `pass`.  The row
goes onto the end of library/<book>/casebook/owner.jsonl through
studio.casebook.note_owner -- append-only, weight 1, the row the bench and
the ratchet answer to on the next commit.  A redo order (studio/work_orders)
walks through the same door.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import casebook, episode_home  # noqa: E402
from studio.stage_run import ledger_id  # noqa: E402


def kind_of(artefact: str) -> str:
    """The casebook's reading of the path, as a refusal on the command line."""
    try:
        return casebook.kind_of(artefact)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) < 5:
        raise SystemExit('usage: note.py <codex_id> <unit> <artefact> <class> "<words>"')
    codex, unit, artefact, cls, words = args[0], args[1], args[2], args[3], " ".join(args[4:])
    kind_of(artefact)
    try:
        print(casebook.note_owner(episode_home.book_dir(codex), ledger_id(codex), unit, artefact, cls, words))
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
