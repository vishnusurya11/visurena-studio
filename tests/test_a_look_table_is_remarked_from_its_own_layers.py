"""A look table's markers re-derive from its own layers when the vocabulary moves (2026-10-14).

Jekyll's refs/looks.json stamped Hyde (and Lanyon's rosy look) `facial_hair: moustache`
from "mutton-chop side-whiskers" -- the closed FACIAL table read `whisker` as a
moustache.  The table is never rewritten for a character already in it (its drawn
looks keep their pictures), and re-drafting the cast is fifteen writer calls that may
draw different spans.  `looks_table.py <book> --remark` re-derives every look's
markers from the words the table already holds, with today's tables, and changes
nothing else: no writer, no picture, no span.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.refs import looks_table
from studio import look_timeline as ltl
from studio.continuity_spec import CharacterLooks, Layers, Look, LookBook, Markers

FACE = "thick, bushy black mutton-chop side-whiskers down both cheeks to the jaw"


def hyde() -> CharacterLooks:
    base = Look(layers=Layers(headwear="soft black felt wideawake hat", hair="coarse black hair", face=FACE),
                markers=Markers(headwear="felt_hat", hair_colour="dark", facial_hair="moustache"),
                made_by="base", sheet="refs/characters/edward_hyde/sheet.png", seed=11)
    return CharacterLooks(base="base", body="A small, pale young man.", looks={"base": base})


def test_remarked_rewrites_only_the_markers():
    before = hyde()
    after = ltl.remarked(before)
    look = after.looks["base"]
    assert look.markers.facial_hair == "sideburns"
    assert (look.markers.headwear, look.markers.hair_colour) == ("felt_hat", "dark")
    assert look.layers == before.looks["base"].layers
    assert (look.sheet, look.seed, look.made_by) == ("refs/characters/edward_hyde/sheet.png", 11, "base")


def test_remark_cli_rewrites_the_table_without_the_writer(tmp_path, monkeypatch):
    book = tmp_path / "library" / "1_book"
    (book / "refs").mkdir(parents=True)
    table = LookBook(book=book.name, characters={"edward_hyde": hyde()})
    ltl.path_of(book).write_text(json.dumps(table.model_dump(mode="json")), encoding="utf-8")
    monkeypatch.setattr(looks_table.episode_home, "book_dir", lambda _id: book)
    monkeypatch.setattr(looks_table, "drafted", lambda *a, **k: (_ for _ in ()).throw(AssertionError("writer")))
    assert looks_table.main("1", ["--remark"]) == 0
    assert ltl.load(book).characters["edward_hyde"].looks["base"].markers.facial_hair == "sideburns"
