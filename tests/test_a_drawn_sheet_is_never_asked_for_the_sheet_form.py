"""A drawn look's sheet is ONE figure drawn from its tags: the house sheet form
("Character reference sheet on a plain mid-grey backdrop with even soft light: front,
three-quarter, profile ...") is cut before drawing (book_look.UNFORMED), so the LOOK
look-back never asks for its nouns.  Jekyll 2026-10-15: the girl's redraw was refused
for a missing 'light' and the ladder redrew the owner's pick."""
from __future__ import annotations

import json

from studio.judges import look
from tests import look_fixtures as lf

FORM = "A girl in a grey pinafore. Character reference sheet on a plain mid-grey backdrop with even soft light."


def a_drawn_book(tmp_path):
    book = lf.a_book(tmp_path)
    recipe = {"workflow": "image_sdxl_t2i_2lora_hires_visurena", "lead": "x", "frames": {}, "entities": {}}
    (book / "refs" / "look.json").write_text(json.dumps({"look": "anime_gothic", "refs": recipe}), encoding="utf-8")
    return book


def asked_of(book, row):
    asked = []
    look.judge(book, [row], **lf.tools(reader=lf.reader_of(asked=asked)))
    return " ".join(q for _p, q in asked if "absent" in q)


def test_a_drawn_book_asks_only_the_figure_words(tmp_path):
    book = a_drawn_book(tmp_path)
    row = lf.add_row(book, "refs/characters/g/sheet.png", FORM)
    assert "'light'" not in asked_of(book, row)


def test_a_house_book_still_asks_the_whole_prompt(tmp_path):
    book = lf.a_book(tmp_path)
    row = lf.add_row(book, "refs/characters/g/sheet.png", FORM)
    assert "'light'" in asked_of(book, row)
