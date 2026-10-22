#!/usr/bin/env python
"""One finding of the owner's, into the casebook.

    uv run python scripts/audit/note.py <codex_id> <unit> <artefact> <class> "<words>"

`<artefact>` is a path relative to the book (as the audit sheet prints it);
`<class>` is a fault class from studio.casebook.CLASSES, or `pass`.  The row
goes onto the end of library/<book>/casebook/owner.jsonl through
studio.casebook.note_owner -- append-only, weight 1, the row the bench and
the ratchet answer to on the next commit.  A redo order (studio/work_orders)
walks through the same door.

The row snapshots the machine json that judged the file's bytes (the take's
dq record, the panel's dq and content rows) so the bench can measure it; a
file no json judged goes on casebook/needs_rejudge.jsonl as well.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.calibration import harvest_labels  # noqa: E402
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
    book = episode_home.book_dir(codex)
    machine = harvest_labels.machine_for(ledger_id(codex), book, artefact)
    try:
        print(casebook.note_owner(book, ledger_id(codex), unit, artefact, cls, words, machine))
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    if not machine:
        print(f"no machine json judged these bytes of {artefact}: on the needs-rejudge list")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
