"""The home page's Orders strip (decision 2026-09-25, "Owner actions"): the
last ten orders rows -- when, what, whom it reaches, the note, and the run that
took it or "pending" -- so the owner sees whether a runner acted on his word.
The strip is a partial on a poll and refreshes when an action lands."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_writable_app
from studio import db, work_orders
from studio.command_center import views


@pytest.fixture()
def board(tmp_path, monkeypatch):
    app, path = make_writable_app(tmp_path, monkeypatch)
    conn = db.get_connection(path)
    yield TestClient(app), conn
    conn.close()


def test_a_taken_order_names_its_run_and_an_untaken_one_says_pending(board):
    client, conn = board
    work_orders.order(conn, "bump", "unit", codex_id=CODEX, stage="episode", unit="ep07", note="first")
    work_orders.take_orders(conn, CODEX, "episode", "ep07", "run-took-it")
    work_orders.order(conn, "retry", "unit", codex_id=CODEX, stage="episode", unit="ep05")
    page = client.get("/").text
    assert "ORDERS" in page and "run-took-it" in page and "pending" in page
    assert "episode › ep07" in page and "first" in page


def test_the_strip_shows_the_last_ten_newest_first(board):
    client, conn = board
    for i in range(12):
        work_orders.order(conn, "bump", "unit", codex_id=CODEX, stage="episode", unit="ep06",
                          note=f"word-{i:02d}")
    strip = client.get("/partials/orders").text
    shown = [f"word-{i:02d}" for i in range(12) if f"word-{i:02d}" in strip]
    assert shown == [f"word-{i:02d}" for i in range(2, 12)]
    assert strip.index("word-11") < strip.index("word-02") and "<html" not in strip


def test_the_strip_polls_and_listens_for_an_action(board):
    client, _ = board
    page = client.get("/").text
    assert 'hx-get="/partials/orders"' in page and "orders-changed from:body" in page


def test_an_empty_strip_says_so(board):
    client, _ = board
    assert "no orders yet" in client.get("/partials/orders").text


def test_recent_orders_carries_the_target_and_who_took_it(board):
    _, conn = board
    work_orders.hold(conn, "studio", "power")
    work_orders.order(conn, "bump", "book", codex_id=CODEX)
    work_orders.order(conn, "redo", "unit", codex_id=CODEX, stage="episode", unit="ep04", step_id="09",
                      note=None)
    rows = views.recent_orders(conn)
    assert [r["kind"] for r in rows] == ["redo", "bump", "hold"]
    assert [r["target"] for r in rows] == ["episode › ep04 · step 09", CODEX, "studio"]
    assert [r["taken"] for r in rows] == ["pending", "pending", "applied"]
    assert rows[0]["ts"] and set(rows[0]) >= {"id", "ts", "kind", "scope", "target", "note", "taken"}


def test_recent_orders_is_bounded(board):
    _, conn = board
    for _ in range(4):
        work_orders.order(conn, "bump", "studio")
    assert len(views.recent_orders(conn, limit=3)) == 3
