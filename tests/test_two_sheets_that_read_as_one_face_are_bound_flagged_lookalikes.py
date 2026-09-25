"""Two sheets whose trait cards sit under DISTINCT_AT read as one face; so do
two whose facenet cosine reaches STRANGER.  Since first contact with a real
bible (2026-09-25: different characters read 0.6 alike on full-figure sheets,
cards 2.0-2.5 apart) both rows are ADVISORY: the pair is listed with the
signed pack, severity advisory, nothing is redrawn and no audit row is owed --
the take identity judge catches the consequence in the episode."""
from __future__ import annotations

import numpy as np

from scripts.refs import step_04_verdict as step
from studio import audit_rows, identity_gate
from studio.judges import look
from tests import look_fixtures as lf


def test_lookalike_cards_end_bound_and_listed_advisory(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    lf.character(book, "b")
    drawn = []
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of({"a": "base", "b": "d2"})),
                   draw=lf.drawer(drawn, book))
    step.run(ctx)
    assert drawn == []
    signed = lf.verdict(book)
    assert signed["verdict"] == "APPROVE" and signed["signed_by"] == "judge:look@1"
    fault = signed["faults"][0]
    assert fault["kind"] == "lookalike" and fault["where"] == "refs/characters/b/sheet.png"
    assert fault["evidence"]["other"] == "refs/characters/a/sheet.png" and fault["evidence"]["distance"] == 2.0
    assert fault["severity"] == "advisory"
    assert (book / "refs/characters/a/sheet.png").exists() and (book / "refs/characters/b/sheet.png").exists()
    assert audit_rows.load(book) == []
    assert step.done(ctx) is True


def test_keep_best_restores_the_try_with_the_fewest_hard_faults(tmp_path):
    """Two hard faults on the last redraw, one on the first try: the first try
    comes back to the live path, the last redraw goes aside, and the verdict
    lists the kept try's faults."""
    from studio import sheet_ladder
    from studio.judges.verdict import Fault, Verdict
    book = lf.a_book(tmp_path)
    row = lf.add_row(book, "refs/characters/a/sheet.png", seed=5)
    drawn = []
    ladder = sheet_ladder.SheetLadder(book, run=lf.drawer(drawn, book))
    one = [Fault(kind="must_noun", where=row["path"], evidence={"missing": ["lantern"]})]
    ladder.take(sheet_ladder.LADDER.rungs[0], 0, Verdict(judge="look", version="1", passed=False, faults=one, confidence=1.0))
    two = one + [Fault(kind="lettering", where=row["path"], evidence={"strings": ["XQZ"]})]
    kept = ladder.keep_best(Verdict(judge="look", version="1", passed=False, faults=two, confidence=1.0, terminal="keep_best"))
    assert [f.kind for f in kept.faults] == ["must_noun"]
    first = (book / "refs/characters/a/superseded/sheet_try1.png").read_bytes()
    assert (book / row["path"]).read_bytes() == first
    assert (book / "refs/characters/a/superseded/sheet_try2.png").exists()
    last = sheet_ladder.pack_rows(book)[-1]
    assert last["rung"] == "keep_best" and last["kept"] == "sheet_try1.png" and last["seed"] == 5


def test_a_card_three_traits_apart_is_another_person():
    verdict = look.judge(None, [{"path": "refs/characters/a/sheet.png", "prompt": lf.PROMPT, "seed": 1},
                                {"path": "refs/characters/b/sheet.png", "prompt": lf.PROMPT, "seed": 1}],
                         **lf.tools(reader=lf.reader_of({"a": "base", "b": "d3"})))
    assert verdict.passed and verdict.faults == []


def test_two_faces_at_or_above_stranger_are_one_identity():
    v = np.zeros(8)
    v[0] = 1.0
    near = np.array([0.9, 0.44, 0, 0, 0, 0, 0, 0])
    near /= np.linalg.norm(near)
    tools = lf.tools(embed=lf.faces_of({"a": v, "b": near}), reader=lf.reader_of({"a": "base", "b": "d4"}))
    verdict = look.judge(None, [{"path": "refs/characters/a/sheet.png", "prompt": lf.PROMPT, "seed": 1},
                                {"path": "refs/characters/b/sheet.png", "prompt": lf.PROMPT, "seed": 1}], **tools)
    assert verdict.passed and verdict.faults[0].severity == "advisory"
    assert verdict.faults[0].kind == "identity" and verdict.faults[0].evidence["wall"] == identity_gate.STRANGER
    assert verdict.faults[0].evidence["cosine"] >= identity_gate.STRANGER


def test_an_unverifiable_card_lowers_confidence_and_refuses_nothing():
    verdict = look.judge(None, [{"path": "refs/characters/a/sheet.png", "prompt": lf.PROMPT, "seed": 1}],
                         **lf.tools(reader=lf.reader_of({"a": "unverifiable"})))
    assert verdict.passed and [f.kind for f in verdict.faults] == ["unread"]
    assert verdict.reads == 2 and verdict.confidence == 0.5
