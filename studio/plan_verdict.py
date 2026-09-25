"""The PLAN gate's signature: `plan.verdict.json` beside `plan.json`, bound to
the plan's sha8.

    {"plan_sha8": "1a2b3c4d", "verdict": "APPROVE", "note": "...", "date": "YYYY-MM-DD"}

A signature names the bytes it was given.  A plan rewritten after the owner
read it is unsigned again, because the sha no longer matches -- the same rule
the refs stage applies to its pack.  Only APPROVE is a signature; any other
verdict is a note, and the unit stays parked.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date as _date
from pathlib import Path

APPROVE = "APPROVE"
FILE = "plan.verdict.json"


def plan_sha8(plan: Path) -> str:
    """The first eight hex digits of the plan file's sha256."""
    return hashlib.sha256(Path(plan).read_bytes()).hexdigest()[:8]


def verdict_path(plan: Path) -> Path:
    return Path(plan).with_name(FILE)


def read(plan: Path) -> dict | None:
    """The verdict beside this plan, or None when nobody has signed."""
    path = verdict_path(plan)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def current(plan: Path) -> bool:
    """Is there an APPROVE beside this plan for exactly these bytes?"""
    plan = Path(plan)
    if not plan.exists():
        return False
    doc = read(plan)
    return bool(doc) and doc.get("verdict") == APPROVE and doc.get("plan_sha8") == plan_sha8(plan)


def sign(plan: Path, note: str, date: str | None = None) -> Path:
    """Write the owner's APPROVE for the plan as it stands now."""
    doc = {"plan_sha8": plan_sha8(plan), "verdict": APPROVE, "note": note,
           "date": date or _date.today().isoformat()}
    out = verdict_path(plan)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return out
