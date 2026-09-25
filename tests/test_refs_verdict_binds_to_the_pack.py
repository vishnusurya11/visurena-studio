"""The LOOK verdict is bound to the pack it was given on: refs/verdict.json carries
the sha8 of refs/pack.jsonl, and a pack that has grown since is a pack nobody has
looked at whole -- done() is False again and the step re-escalates saying so."""
from __future__ import annotations

import json

import pytest

from scripts.refs import step_04_verdict as step
from studio import db, refs_verdict
from studio.escalate import Escalation
from studio.stage_run import StageContext


def a_book(tmp_path, rows=2):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    with (book / "refs" / "pack.jsonl").open("w", encoding="utf-8") as fh:
        for n in range(rows):
            fh.write(json.dumps({"path": f"refs/characters/c{n}/sheet.png", "prompt": "x", "seed": n}) + "\n")
    return book


def a_ctx(tmp_path, book):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    return StageContext(conn, codex, book, "refs", unit="main", logs_root=tmp_path / "logs",
                        busy=lambda: False, hold=tmp_path / "HOLD", launch=lambda cmd: 0)


def test_sign_then_current_returns_the_verdict_bound_to_this_pack(tmp_path):
    book = a_book(tmp_path)
    path = refs_verdict.sign(book, "every face reads as its own person")
    assert path == book / "refs" / "verdict.json"
    got = refs_verdict.current(book)
    assert got["verdict"] == "APPROVE" and got["note"].startswith("every face")
    assert got["pack_sha8"] == refs_verdict.pack_sha8(book) and len(got["pack_sha8"]) == 8
    assert got["date"][:2] == "20"


def test_no_verdict_means_nothing_current_and_the_step_asks_for_a_look(tmp_path):
    book = a_book(tmp_path)
    ctx = a_ctx(tmp_path, book)
    assert refs_verdict.current(book) is None
    assert step.done(ctx) is False
    with pytest.raises(Escalation) as parked:
        step.run(ctx)
    assert parked.value.gate == "LOOK" and parked.value.verdict == "refs/verdict.json"
    assert "look at every sheet" in parked.value.ask


def test_a_signed_pack_is_done(tmp_path):
    book = a_book(tmp_path)
    refs_verdict.sign(book, "ok")
    assert step.done(a_ctx(tmp_path, book)) is True


def test_a_changed_pack_undoes_the_verdict_and_the_step_escalates_naming_the_new_rows(tmp_path):
    book = a_book(tmp_path)
    refs_verdict.sign(book, "ok")
    with (book / "refs" / "pack.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"path": "refs/props/p/sheet.png", "prompt": "y", "seed": 9}) + "\n")
    ctx = a_ctx(tmp_path, book)
    assert refs_verdict.current(book) is None
    assert step.done(ctx) is False
    with pytest.raises(Escalation) as parked:
        step.run(ctx)
    assert "changed" in parked.value.ask and "1 new row" in parked.value.ask
    logged = "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "logs").rglob("*.log"))
    assert "stale" in logged


def test_a_book_with_no_pack_yet_hashes_the_empty_pack(tmp_path):
    book = tmp_path / "book"
    book.mkdir()
    assert refs_verdict.pack_sha8(book) == refs_verdict.pack_sha8(book)
    assert refs_verdict.current(book) is None
