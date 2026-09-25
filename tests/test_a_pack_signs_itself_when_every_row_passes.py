"""Every row passes: the step signs refs/verdict.json in the judge's name, bound
to the pack's sha8, with no fault, no rung, no learning and no audit row; an
empty pack signs the same way, reading nothing."""
from __future__ import annotations

from scripts.refs import step_04_verdict as step
from studio import audit_rows, refs_verdict
from tests import look_fixtures as lf


def test_a_passing_pack_is_signed_by_the_judge_and_bound_to_its_sha8(tmp_path):
    book = lf.a_book(tmp_path)
    lf.place(book, "room")
    lf.character(book, "a")
    lf.character(book, "b")
    drawn, asked = [], []
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of({"a": "base", "b": "d4"}, asked=asked)),
                   draw=lf.drawer(drawn, book))
    assert step.done(ctx) is False
    step.run(ctx)
    signed = refs_verdict.current(book)
    assert signed and signed["verdict"] == "APPROVE" and signed["rows"] == 3
    assert signed["signed_by"] == "judge:look@1" and signed["faults"] == []
    assert signed["note"].startswith("no fault named in")
    assert drawn == [] and audit_rows.load(book) == []
    assert not (book / "refs" / "learnings.jsonl").exists()
    assert {p.parent.name for p, q in asked if "absent" in q} == {"a", "b"}   # a place is judged by the line at its own hour, not by the bible
    assert step.done(ctx) is True


def test_an_empty_pack_signs_without_a_read(tmp_path):
    book = lf.a_book(tmp_path)
    asked = []
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of(asked=asked)))
    step.run(ctx)
    signed = refs_verdict.current(book)
    assert signed and signed["rows"] == 0 and signed["signed_by"] == "judge:look@1"
    assert asked == []
