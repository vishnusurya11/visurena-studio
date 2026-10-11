"""Which LOOK a setup stages for each person, and the words that go with it.

Decision 2026-10-10: a take stages the picture of the look its person is in,
and the words describe THAT picture -- the retention line's "face, hair, build
and clothes of <Picture k>" is then true by construction.  The look is the
setup's own pick (`Setup.looks`), else the bound row's chapter look (refs.json
is stamped per chapter).  A book with no `refs/looks.json` resolves nothing
here and keeps its one sheet per character (the legacy path, audited at step 03).
"""
from __future__ import annotations

from pathlib import Path

from studio import look_timeline


def picks(setup) -> dict[str, str]:
    """The setup's explicit look per person."""
    return {p.who: p.look for p in getattr(setup, "looks", None) or [] if p.look}


def look_for(setup, who: str, row: dict) -> str:
    """The look this setup stages for `who`: its pick, else the row's chapter look."""
    return picks(setup).get(who) or (row or {}).get("look", "")


def card_of(book: Path, who: str):
    table = look_timeline.load(book)
    return table.characters.get(who) if table else None


def words_for(book: Path, who: str, look: str, row: dict) -> str:
    """The `physical` a prompt says for `who` in `look`: the bound row when the
    look is the row's own (or the book has no table), else the look's words."""
    card = card_of(book, who)
    if not look or look == row.get("look") or card is None or look not in card.looks:
        return row.get("physical", "")
    return look_timeline.look_words(card, look)


def markers_for(book: Path, who: str, look: str, row: dict) -> dict:
    """The staged look's markers, the same choice `words_for` makes."""
    card = card_of(book, who)
    if not look or look == row.get("look") or card is None or look not in card.looks:
        return row.get("markers") or {}
    return card.looks[look].markers.model_dump()


def faces_by_setup(episode) -> dict[str, list[str]]:
    """Every person each setup's shots cast, first-appearance order."""
    out: dict[str, list[str]] = {}
    for shot in episode.shots:
        for who in shot.faces or []:
            if who not in out.setdefault(shot.setup, []):
                out[shot.setup].append(who)
    return out


def face_fault(book: Path, episode, name: str, who: str, card, row: dict) -> str:
    """Why `who`'s staged picture and words would not name one look, or ''."""
    look = look_for(episode.setups[name], who, row)
    if look not in card.looks:
        return f"G-LOOK setup {name}: {who}'s look {look!r} is not on the book's look table"
    if row.get("look") and row["look"] != card.look_id_at(episode.number):
        return (f"G-LOOK setup {name}: {who}'s bound row is {row['look']!r}, the table says "
                f"{card.look_id_at(episode.number)!r} for chapter {episode.number}; rebind (step 01)")
    if look != card.base and not (Path(book) / "refs" / "characters" / who / "looks" / f"{look}.png").exists():
        return f"G-LOOK setup {name}: {who}'s look {look!r} is not drawn; step 03 draws it"
    return ""


def look_faults(book: Path, episode) -> list[str]:
    """The step-06 lint: every staged person's picture and words name ONE look
    on the book's table.  A book without a table has nothing to lint."""
    from studio import cast_refs
    table = look_timeline.load(book)
    if table is None:
        return []
    out = []
    for name, faces in faces_by_setup(episode).items():
        for who in faces:
            card = table.characters.get(who)
            row = next((r for r in cast_refs.load(book).get("refs", []) if r.get("entity_id") == who), None)
            if card is not None and row is not None and (bad := face_fault(book, episode, name, who, card, row)):
                out.append(bad)
    return out
