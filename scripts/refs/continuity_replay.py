#!/usr/bin/env python
"""Replay the continuity plan gates over a finished book's plans. CPU only, $0.

    uv run python scripts/refs/continuity_replay.py <book_id> [--json]

Verdict S's acceptance (decision 2026-10-10): G-LOOK and G-PLACE replayed on all
of a book's plans give at most one false refusal per plan, each read by hand.
Each plan is judged against what was DRAWN BEFORE it -- every place's anchor
and the views earlier plans staged -- so a room an episode drew from words
reads as the new room it was.  The look table comes from the dossiers'
costume plot when the book has no refs/looks.json; nothing under library/ is
written.  G-LOOK-WORDS (shot prose naming a hair, beard or hat the staged look
contradicts) is counted as an advisory: it refuses nothing until this replay
has been read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import continuity_place as cp, episode_home, look_table as lt, look_timeline  # noqa: E402
from studio.continuity_spec import LookBook  # noqa: E402


def table_of(book: Path) -> LookBook:
    """The book's look table, else one read from its dossiers' costume plots."""
    table = look_timeline.load(book)
    if table is not None:
        return table
    out = LookBook(book=Path(book).name)
    for path in sorted((Path(book) / "analysis" / "characters").glob("*.json")):
        looks = look_timeline.looks_from_dossier(json.loads(path.read_text(encoding="utf-8")))
        if looks is not None:
            out.characters[path.stem] = looks
    return out


def drawn_before(book: Path, number: int):
    """`drawn(book, location)` as it stood when episode `number` was planned."""
    staged: dict[str, set[str]] = {}
    for line in cp.history(book, number, [r["id"] for r in cp.location_rows(book)]):
        loc, _, view = line.split(" ", 1)[1].partition("/")
        staged.setdefault(loc, set()).add(view)
    return lambda b, loc: sorted(v for v in cp.drawn_views(b, loc) if v == cp.ANCHOR or v in staged.get(loc, set()))


def word_advisories(table: LookBook, episode) -> list[str]:
    """G-LOOK-WORDS: one-face shots whose prose names a hair colour, beard or hat
    the person's chapter look contradicts."""
    out = []
    for shot in episode.shots:
        card = table.characters.get((shot.faces or [""])[0]) if len(shot.faces or []) == 1 else None
        if card is None:
            continue
        want = card.looks[card.look_id_at(episode.number)].markers
        said = f"{shot.frame} {getattr(shot, 'at_rest', '') or ''}"
        hair = lt.seen_hair(said)
        if hair and want.hair_colour and hair != lt.family("hair_colour", want.hair_colour):
            out.append(f"G-LOOK-WORDS shot {shot.index}: prose says {hair} hair, the look is {want.hair_colour}")
    return out


def replay_one(book: Path, number: int, table: LookBook, places: dict, rows: list[dict]) -> dict:
    episode = episode_home.load_plan(book, number)
    return {"G-LOOK": cp.look_gate(table, episode),
            "G-PLACE": cp.place_gate(book, episode, places, rows, drawn_before(book, number)),
            "G-LOOK-WORDS (advisory)": word_advisories(table, episode)}


def replay(book: Path) -> dict[int, dict]:
    table, places, rows = table_of(book), cp.place_map(book), cp.location_rows(book)
    numbers = sorted(int(p.parent.name[2:]) for p in (Path(book) / "episodes").glob("ep*/plan.json")
                     if p.parent.name[2:].isdigit())
    return {n: replay_one(book, n, table, places, rows) for n in numbers}


def main(book_id: str, as_json: bool) -> int:
    got = replay(episode_home.book_dir(book_id))
    if as_json:
        print(json.dumps(got, indent=1))
        return 0
    for n, gates in got.items():
        print(f"ep{n:02d}  " + "  ".join(f"{k} {len(v)}" for k, v in gates.items()))
        for lines in gates.values():
            for line in lines:
                print("    ", line[:170])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], "--json" in sys.argv))
