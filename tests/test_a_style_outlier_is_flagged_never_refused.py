"""A sheet whose DINOv3 vector sits far from the pack's own place pictures is a
style outlier: listed as a fault, signed beside the pass, and never a reason
to climb -- two books of evidence is a flag's worth, not a wall's."""
from __future__ import annotations

from scripts.refs import step_04_verdict as step
from studio import audit_rows
from studio.judges import look
from tests import look_fixtures as lf

CARDS = {"a": "base", "b": "d4"}


def _rows(book):
    rows = [lf.place(book, f"room{n}") for n in range(3)]
    return rows + [lf.character(book, "a"), lf.character(book, "b")]


def test_the_outlier_is_listed_and_the_verdict_still_passes(tmp_path):
    book = lf.a_book(tmp_path)
    rows = _rows(book)
    styles = lf.styles_of({"room0": 0, "room1": 1, "room2": 2, "a": 3, "b": 4})
    verdict = look.judge(book, rows, **lf.tools(style_embed=styles, reader=lf.reader_of(CARDS)))
    assert verdict.passed
    assert [(f.kind, f.where) for f in verdict.faults] == [("style", "refs/characters/b/sheet.png")]
    assert verdict.faults[0].evidence["cosine"] < look.STYLE_OUTLIER
    assert verdict.faults[0].evidence["places"] == 3


def test_the_step_signs_the_flag_without_a_rung_or_an_audit_row(tmp_path):
    book = lf.a_book(tmp_path)
    _rows(book)
    drawn = []
    styles = lf.styles_of({"room0": 0, "room1": 1, "room2": 2, "a": 3, "b": 4})
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(style_embed=styles, reader=lf.reader_of(CARDS)),
                   draw=lf.drawer(drawn, book))
    step.run(ctx)
    assert drawn == []
    signed = lf.verdict(book)
    assert signed["signed_by"] == "judge:look@1" and [f["kind"] for f in signed["faults"]] == ["style"]
    assert audit_rows.load(book) == [] and step.done(ctx) is True


def test_a_pack_without_a_place_picture_has_no_style_to_judge(tmp_path):
    book = lf.a_book(tmp_path)
    rows = [lf.character(book, "a"), lf.character(book, "b")]
    verdict = look.judge(book, rows, **lf.tools(style_embed=lf.styles_of({"b": 4}), reader=lf.reader_of(CARDS)))
    assert verdict.passed and verdict.faults == []
