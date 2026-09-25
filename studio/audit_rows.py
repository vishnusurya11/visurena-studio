"""The audit sheet's rows: `library/<book>/audit/rows.jsonl`, one line per
terminal rung.

Every terminal rung appends a row -- which unit, which gate, which judge, the
artefact it kept and the faults it kept it with.  The sheet builder under
`scripts/audit/` reads them; NO STEP DOES.  The rows are the owner's
after-the-fact look, never a gate: a test greps the step modules for the path.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from studio import db

FILE = Path("audit") / "rows.jsonl"


class AuditRow(BaseModel):
    unit: str
    gate: str
    judge: str
    sha8: str = ""
    artefact: str = ""      # relative to the book, posix
    faults: list[dict] = Field(default_factory=list)
    terminal: str
    ts: str = ""


def path(book_dir: Path | str) -> Path:
    return Path(book_dir) / FILE


def append(book_dir: Path | str, row: dict | AuditRow) -> Path:
    """One more row, stamped now, at the end of the book's audit file."""
    made = row if isinstance(row, AuditRow) else AuditRow.model_validate(row)
    if not made.ts:
        made.ts = db.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")
    target = path(book_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(made.model_dump_json() + "\n")
    return target


def load(book_dir: Path | str) -> list[AuditRow]:
    """Every row, for the sheet builder; an absent file is no rows."""
    target = path(book_dir)
    if not target.exists():
        return []
    lines = target.read_text(encoding="utf-8").splitlines()
    return [AuditRow.model_validate(json.loads(line)) for line in lines if line.strip()]
