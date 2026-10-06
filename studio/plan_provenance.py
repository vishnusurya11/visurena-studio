"""The cure ledger: why a plan's bytes moved without its signature.

`plan.cures.jsonl` sits beside `plan.json`; every mechanical repair round
appends one row -- the sha8 the plan had before the write, the sha8 it has
after, and the cure names that moved it.  `chain` then answers the only
question step 02 needs: did these bytes move ONLY through recorded cures?
A yes lets a stale-but-clean APPROVE be re-signed with zero writer/critic
calls (ep18: a mechanical cure lapsed the signature and the paid climb ran
again, 48 calls / $1.05).  Any write nobody recorded -- a hand edit, a crash
between write and record -- breaks the chain, which fails safe: the critic
reads once.  Rows carry sha8s only, never a path (the no-absolute-path rule).
"""
from __future__ import annotations

import json
from datetime import date as _date
from pathlib import Path

from studio import plan_verdict

CURES_FILE = "plan.cures.jsonl"


def cures_path(plan: Path) -> Path:
    """The ledger beside this plan."""
    return Path(plan).with_name(CURES_FILE)


def record(plan: Path, before_sha8: str, cures: list[str]) -> Path:
    """Append one row: the plan's bytes before the recorded write -> as they
    stand now, with the cure names that carried them."""
    row = {"from_sha8": before_sha8, "to_sha8": plan_verdict.plan_sha8(plan),
           "cures": list(cures), "date": _date.today().isoformat()}
    path = cures_path(plan)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return path


def rows(plan_dir: Path) -> list[dict]:
    """Every readable row, in file order; a broken line is skipped, which can
    only ever break a chain, never fake one."""
    path = Path(plan_dir) / CURES_FILE
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def chain(plan_dir: Path, from_sha8: str, to_sha8: str) -> list[str] | None:
    """The cure names that carried from_sha8 to to_sha8 through contiguous
    recorded rows, in order; [] when the sha8s are equal; None when any link
    is missing -- then somebody wrote bytes nobody recorded."""
    if from_sha8 == to_sha8:
        return []
    names, at, walking = [], from_sha8, False
    for row in rows(plan_dir):
        if row.get("from_sha8") != at:
            if walking:
                return None             # a write between rounds nobody recorded
            continue                    # rows older than the signature's bytes
        walking = True
        names.extend(str(n) for n in row.get("cures") or [])
        at = row.get("to_sha8")
        if at == to_sha8:
            return names
    return None
