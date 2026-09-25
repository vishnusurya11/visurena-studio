"""The audit rows are the owner's after-the-fact look and never a gate: no
refs or episode step module reads them.  A grep is the test."""
from __future__ import annotations

from pathlib import Path

from studio import audit_rows, registry

STEPS = ("scripts/refs", "scripts/episode")
WORDS = ("audit_rows", "audit/rows", "rows.jsonl")


def test_no_step_module_names_the_audit_rows():
    hits = []
    for folder in STEPS:
        for path in sorted((registry.ROOT / folder).glob("*.py")):
            text = path.read_text(encoding="utf-8")
            hits += [f"{folder}/{path.name}: {w}" for w in WORDS if w in text]
    assert hits == []


def test_the_rows_live_under_the_book_not_the_code_tree():
    assert audit_rows.path(Path("book")) == Path("book") / "audit" / "rows.jsonl"
