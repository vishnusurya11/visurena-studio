"""A verdict for an earlier pack is stale.  The step re-judges the rows that
arrived since (their look-back, lettering and limbs are read again; the bound
rows are read only for the pairwise identity and style comparisons) and
re-signs the pack as it stands now, saying how many rows were new."""
from __future__ import annotations

from scripts.refs import step_04_verdict as step
from studio import refs_verdict
from tests import look_fixtures as lf


def test_only_the_new_rows_are_read_back(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    lf.character(book, "b")
    refs_verdict.sign(book, "the owner looked")
    lf.character(book, "c")
    lf.place(book, "room")
    asked = []
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of({"a": "base", "b": "d3", "c": "d4"}, asked=asked)))
    assert step.done(ctx) is False and refs_verdict.new_rows(book) == 2
    assert step.paths_to_judge(ctx) == ["refs/characters/c/sheet.png"]   # places are not the bible's to judge
    step.run(ctx)
    looked = {p.parent.name for p, q in asked if "absent" in q}
    assert looked == {"c"}
    signed = refs_verdict.current(book)
    assert signed and signed["rows"] == 4 and signed["signed_by"] == "judge:look@1"
    assert "stale" in lf.logged(tmp_path) and "2 new row" in lf.logged(tmp_path)


def test_a_new_row_is_still_compared_with_the_bound_cast(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    refs_verdict.sign(book, "the owner looked")
    lf.character(book, "b")
    drawn = []
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of({"a": "base", "b": "d0"})),
                   draw=lf.drawer(drawn, book))
    step.run(ctx)
    signed = refs_verdict.current(book)
    assert signed["faults"][0]["kind"] == "lookalike"
    assert signed["faults"][0]["where"] == "refs/characters/b/sheet.png"
    assert signed["faults"][0]["evidence"]["other"] == "refs/characters/a/sheet.png"
    assert all("characters_b" in d["filename_prefix"] for d in drawn) and len(drawn) == 2


def test_a_current_pack_judges_every_row(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    lf.character(book, "b")
    ctx = lf.a_ctx(tmp_path, book, **lf.tools())
    assert step.paths_to_judge(ctx) == ["refs/characters/a/sheet.png", "refs/characters/b/sheet.png"]
