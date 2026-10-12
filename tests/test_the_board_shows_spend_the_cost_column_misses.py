"""Board review 2026-10-12 (02 #14): Scarlet's episodes carry cost_usd 0.0, so the
unit page hid the cost, while library/<scarlet>/spend.jsonl records $41.02 of
paid gpt-image generation that never reached `usage`; and WotW ep19-23 hid $11.85
of priced calls behind None because one call was @subscription.  The board shows
the priced part with the unpriced count, and the book's spend.jsonl total.  $0."""
from __future__ import annotations

import json

from studio import db
from studio.command_center import views

CODEX = "20990101000000"


def _conn(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "A Book", codex_id=CODEX)
    return conn


def _usage(conn, cost, model="gpt-x"):
    conn.execute("INSERT INTO usage (recorded_at, codex_id, stage, step_id, tier, model, input_tokens, output_tokens,"
                 " cost_usd, unit) VALUES ('2026-10-01T00:00:00Z', ?, 'episode', '02', 'w', ?, 1, 1, ?, 'ep19')",
                 (CODEX, model, cost))


def test_a_partly_unpriced_unit_shows_its_priced_part(tmp_path):
    conn = _conn(tmp_path)
    _usage(conn, 2.5)
    _usage(conn, None, "claude@subscription")
    assert views.unit_spend(conn, CODEX, "episode", "ep19") == {"priced": 2.5, "unpriced": 1, "calls": 2}


def test_a_unit_with_no_call_spent_nothing(tmp_path):
    assert views.unit_spend(_conn(tmp_path), CODEX, "episode", "ep01") == {"priced": 0.0, "unpriced": 0, "calls": 0}


def test_the_books_spend_ledger_is_summed(tmp_path):
    book = tmp_path / "book"
    book.mkdir()
    rows = [{"model": "gpt-image", "usd_estimate": 0.2}, {"model": "gpt-image", "usd_estimate": 0.25}, {"note": "x"}]
    (book / "spend.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows) + "not json\n", encoding="utf-8")
    assert views.book_spend(book) == {"usd": 0.45, "rows": 2}
    assert views.book_spend(tmp_path / "none") is None


def test_the_unit_and_book_pages_print_the_books_spend_ledger(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from command_center_fixtures import CODEX as BOOK, make_app
    app = make_app(tmp_path, monkeypatch)
    (tmp_path / "library" / f"{BOOK}_a-book" / "spend.jsonl").write_text(
        json.dumps({"model": "gpt-image", "usd_estimate": 41.02}) + "\n", encoding="utf-8")
    c = TestClient(app)
    assert "$41.02" in c.get(f"/d/episode/{BOOK}/ep03").text
    assert "$41.02" in c.get(f"/b/{BOOK}").text
