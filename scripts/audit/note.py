#!/usr/bin/env python
"""One finding of the owner's, into the casebook.

    uv run python scripts/audit/note.py <codex_id> <unit> <artefact> <class> "<words>"

`<artefact>` is a path relative to the book (as the audit sheet prints it);
`<class>` is a fault class from studio.casebook.CLASSES, or `pass`.  The row
goes onto the end of library/<book>/casebook/owner.jsonl through
studio.casebook.append_owner -- append-only, weight 1, the row the bench and
the ratchet answer to on the next commit.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import casebook, db, episode_home  # noqa: E402
from studio.casebook import Row  # noqa: E402
from studio.stage_run import ledger_id  # noqa: E402

KINDS_BY_PATH = (("storyboard/grids", "grid"), ("storyboard/shot_", "panel"), ("/takes/", "take"),
                 ("/cut/", "master"), ("/review/", "master"), ("refs/", "sheet"), ("plan", "plan"))
"""The first match names the kind; the grids row sits before the panels' folder."""


def kind_of(artefact: str) -> str:
    path = artefact.replace("\\", "/")
    for needle, kind in KINDS_BY_PATH:
        if needle in path:
            return kind
    raise SystemExit(f"{artefact}: not a sheet, plan, grid, panel, take or master path")


def row_of(codex: str, unit: str, artefact: str, cls: str, words: str, book: Path) -> Row:
    """The owner's row: a fault of the named class, or a pass; the file's sha8 when it is there."""
    today = db.utc_now().strftime("%Y-%m-%d")
    if cls != "pass" and cls not in casebook.CLASSES:
        raise SystemExit(f"{cls!r} is not a fault class; one of pass, {', '.join(casebook.CLASSES)}")
    return Row(codex=ledger_id(codex), unit=unit, kind=kind_of(artefact), path=artefact,
               sha8=casebook.sha8_of(Path(book) / artefact),
               verdict="pass" if cls == "pass" else "fault", fault_class=None if cls == "pass" else cls,
               verdict_by="owner", verdict_at=today, source=f"owner note {today}: {words.strip()}")


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) < 5:
        raise SystemExit('usage: note.py <codex_id> <unit> <artefact> <class> "<words>"')
    codex, unit, artefact, cls, words = args[0], args[1], args[2], args[3], " ".join(args[4:])
    if not words.strip():
        raise SystemExit("say what was seen: the words may not be empty")
    book = episode_home.book_dir(codex)
    print(casebook.append_owner(book / "casebook", row_of(codex, unit, artefact, cls, words, book)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
