#!/usr/bin/env python
"""refs 01_03 -- the book's look table, refs/looks.json, for its bound characters.

    uv run python scripts/refs/looks_table.py <book_id> [<who> ...]

Each character's looks come from its dossier's own costume plot when it has one
(`wardrobe_by_chapter`, WotW's format), else from the look-timeline writer over
the script supervisor's `state_changes` (one workhorse call per character; a
look whose quote is not in its chapter at 0.85 never lands).  A character
already in the table is never rewritten: its drawn looks keep their pictures.
Decision 2026-10-10 (continuity).  No who given: every bound refs.json row.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, look_timeline, plan_brief  # noqa: E402


def card_of(book: Path, who: str) -> dict:
    return json.loads((Path(book) / "analysis" / "characters" / f"{who}.json").read_text(encoding="utf-8"))


def row_of(book: Path, who: str) -> dict:
    """The bound refs.json row of `who`, {} when it is not bound."""
    return next((r for r in rows(book) if r["entity_id"] == who), {})


def table_for(book: Path, who: str, _agent=None):
    """One character's looks: its costume plot, else the writer's verified draft;
    a silent dossier head is the bound row's; no dossier: the row's own cards."""
    from agents import look_timeline_writer as writer
    row = row_of(book, who)
    if not (Path(book) / "analysis" / "characters" / f"{who}.json").exists():
        return look_timeline.looks_from_cards(row)
    card, fallback = card_of(book, who), row.get("physical", "")
    looks = look_timeline.looks_from_dossier(card, fallback=fallback)
    if looks is None:
        draft = writer.write(look_timeline.dossier_text(card), _agent=_agent)
        looks = look_timeline.looks_from_draft(draft, card, lambda n: plan_brief.chapter_text(book, n), fallback)
    return looks


def build(book: Path, cast: list[str], _agent=None) -> list[str]:
    """Every character of `cast` not yet in the table, written; their ids."""
    table = look_timeline.load(book)
    have = set(table.characters) if table else set()
    written = []
    for who in cast:
        if who not in have:
            looks = table_for(book, who, _agent=_agent)
            if why := look_timeline.head_refusal(who, looks):     # C1_verdict #9: never a blank judge
                raise SystemExit(f"REFUSED: {why}")
            look_timeline.write_looks(book, who, looks)
            written.append(who)
    return written


def rows(book: Path) -> list[dict]:
    """Every character row refs.json binds; none without a refs.json."""
    path = Path(book) / "refs" / "refs.json"
    found = (episode_home.read_json(path).get("refs") or []) if path.exists() else []
    return [r for r in found if r.get("kind", "character") == "character" and r.get("entity_id")]


def bound(book: Path) -> list[str]:
    """Every character row refs.json binds."""
    return [r["entity_id"] for r in rows(book)]


def main(book_id: str, who: list[str]) -> int:
    book = episode_home.book_dir(book_id)
    for name in build(book, who or bound(book)):
        print(f"  looks: {name}")
    print(f"  table: {episode_home.relative(book, look_timeline.path_of(book))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2:]))
