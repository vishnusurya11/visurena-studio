"""The board's hand (decision 2026-09-25, "Owner actions": one writer, `orders`).
Every POST under /act/ is exactly one work_orders call -- `hold` (a holds row
and its orders receipt), `lift`, or `order` -- through a SEPARATE writable
connection factory; the read routes keep `mode=ro`.  No action spawns a
process.  A POST from a foreign page is refused 403, a board started without a
write factory answers 405, a stage the registry does not know 404, an empty
reason or note 422.  Each action answers with the receipt fragment: the new
orders row's id and what it will do."""
from __future__ import annotations

import sqlite3
import subprocess

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app, make_db, make_library, make_writable_app
from studio import casebook, db
from studio.command_center import actions
from studio.command_center import app as cc_app

LOCAL = {"Origin": "http://127.0.0.1:8700"}


@pytest.fixture()
def board(tmp_path, monkeypatch):
    """(client, read) over the writable board; `read(sql)` reads the tmp DB."""
    app, path = make_writable_app(tmp_path, monkeypatch)

    def read(sql, *args):
        conn = db.get_connection(path)
        try:
            return [dict(r) for r in conn.execute(sql, args)]
        finally:
            conn.close()
    return TestClient(app), read


@pytest.fixture(autouse=True)
def no_process(monkeypatch):
    """Any process an action tried to start fails the test."""
    def refuse(*a, **k):
        raise AssertionError("an action spawned a process")
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)


def _orders(read):
    return read("SELECT * FROM orders ORDER BY id")


def _unit(kind="bump", unit="ep07", **extra):
    return {"codex": CODEX, "stage": "episode", "unit": unit, **extra}


@pytest.mark.parametrize("kind", ["bump", "retry", "requeue"])
def test_a_unit_order_is_one_orders_row_and_a_receipt(board, kind):
    client, read = board
    response = client.post(f"/act/{kind}", data=_unit(), headers=LOCAL)
    assert response.status_code == 200, response.text
    (row,) = _orders(read)
    assert (row["kind"], row["scope"], row["codex_id"], row["stage"], row["unit"]) == (kind, "unit", CODEX, "episode", "ep07")
    assert row["taken_ts"] is None and row["by"] == "owner"
    assert f"#{row['id']}" in response.text and "queued at next run" in response.text
    assert "<html" not in response.text and response.headers["HX-Trigger"] == "orders-changed"


@pytest.mark.parametrize("fields", [
    {"scope": "unit", "codex": CODEX, "stage": "episode", "unit": "ep04"},
    {"scope": "book", "codex": CODEX},
    {"scope": "studio"}])
def test_a_hold_is_a_holds_row_and_one_orders_row(board, fields):
    client, read = board
    response = client.post("/act/hold", data={**fields, "reason": "look again"}, headers=LOCAL)
    assert response.status_code == 200, response.text
    (order,) = _orders(read)
    (hold,) = read("SELECT * FROM holds")
    assert order["kind"] == "hold" and order["scope"] == hold["scope"] == fields["scope"]
    assert hold["reason"] == "look again" and hold["lifted_at"] is None
    assert f"#{order['id']}" in response.text
    assert "held — runs stop before the first GPU step" in response.text


def test_a_studio_hold_ignores_the_ids_it_does_not_reach(board):
    client, read = board
    client.post("/act/hold", data={"scope": "studio", "codex": CODEX, "stage": "episode",
                                   "unit": "ep04", "reason": "power"}, headers=LOCAL)
    (hold,) = read("SELECT * FROM holds")
    assert (hold["codex_id"], hold["stage"], hold["unit"]) == (None, None, None)


def test_a_lift_closes_the_hold_with_one_more_orders_row(board):
    client, read = board
    client.post("/act/hold", data={"scope": "book", "codex": CODEX, "reason": "re-plan"}, headers=LOCAL)
    (hold,) = read("SELECT * FROM holds")
    response = client.post(f"/act/lift/{hold['id']}", headers=LOCAL)
    assert response.status_code == 200, response.text
    assert [o["kind"] for o in _orders(read)] == ["hold", "lift"]
    assert read("SELECT lifted_at FROM holds")[0]["lifted_at"]
    assert f"#{_orders(read)[-1]['id']}" in response.text and "lifted" in response.text


def test_a_lift_of_no_hold_is_404_and_of_a_lifted_hold_422(board):
    client, read = board
    assert client.post("/act/lift/999", headers=LOCAL).status_code == 404
    client.post("/act/hold", data={"scope": "studio", "reason": "x"}, headers=LOCAL)
    client.post("/act/lift/1", headers=LOCAL)
    assert client.post("/act/lift/1", headers=LOCAL).status_code == 422
    assert len(_orders(read)) == 2


def test_a_redo_is_one_orders_row_and_a_casebook_row(board, tmp_path):
    client, read = board
    response = client.post("/act/redo", data=_unit(unit="ep04", step_id="02", note="wrong street"),
                           headers=LOCAL)
    assert response.status_code == 200, response.text
    (row,) = _orders(read)
    assert (row["kind"], row["step_id"], row["note"]) == ("redo", "02", "wrong street")
    (note,) = casebook.read_rows(tmp_path / "library" / f"{CODEX}_a-book" / "casebook" / casebook.OWNER)
    assert note.path == "episodes/ep04/plan.json"
    assert "casebook" in response.text and f"#{row['id']}" in response.text


def test_a_redo_whose_artefact_cannot_be_named_is_422_and_writes_nothing(board):
    client, read = board
    response = client.post("/act/redo", data=_unit(unit="ep04", step_id="05", note="off a beat"),
                           headers=LOCAL)
    assert response.status_code == 422 and "artefact" in response.text
    assert _orders(read) == []


@pytest.mark.parametrize("path, fields", [
    ("/act/hold", {"scope": "unit", "codex": CODEX, "stage": "episode", "unit": "ep04", "reason": "  "}),
    ("/act/redo", _unit(unit="ep04", step_id="02", note="")),
    ("/act/redo", _unit(unit="ep04", step_id="99", note="no such step")),
    ("/act/bump", {"codex": "123", "stage": "episode", "unit": "ep04"})])
def test_an_empty_word_a_bad_step_or_a_bad_codex_is_422(board, path, fields):
    client, read = board
    assert client.post(path, data=fields, headers=LOCAL).status_code == 422
    assert _orders(read) == [] and read("SELECT * FROM holds") == []


@pytest.mark.parametrize("fields", [
    {"codex": CODEX, "stage": "nowhere", "unit": "ep04"},
    {"codex": "20991231000000", "stage": "episode", "unit": "ep04"},
    {"codex": CODEX, "stage": "episode", "unit": "ep99"}])
def test_an_unknown_stage_book_or_unit_is_404(board, fields):
    client, read = board
    response = client.post("/act/bump", data=fields, headers=LOCAL)
    assert response.status_code == 404 and "<html" not in response.text
    assert _orders(read) == []


@pytest.mark.parametrize("header", [{"Origin": "http://evil.example"},
                                    {"Referer": "http://evil.example/page"},
                                    {"Origin": "http://127.0.0.1.evil.example:8700"}])
def test_a_post_from_a_foreign_page_is_refused_403(board, header):
    client, read = board
    response = client.post("/act/bump", data=_unit(), headers=header)
    assert response.status_code == 403
    assert _orders(read) == []


@pytest.mark.parametrize("header", [{"Origin": "http://localhost:8700"},
                                    {"Referer": "http://127.0.0.1:8700/d/episode"}, {}])
def test_a_post_from_the_board_or_a_local_shell_is_taken(board, header):
    client, read = board
    assert client.post("/act/bump", data=_unit(), headers=header).status_code == 200
    assert len(_orders(read)) == 1


def test_a_board_started_read_only_answers_405(tmp_path, monkeypatch):
    client = TestClient(make_app(tmp_path, monkeypatch))
    for path in ("/act/bump", "/act/hold", "/act/redo", "/act/lift/1"):
        response = client.post(path, data=_unit(reason="x", note="x", step_id="02", scope="studio"),
                               headers=LOCAL)
        assert response.status_code == 405 and "read-only" in response.text


def test_the_read_routes_keep_the_read_only_factory(board):
    client, _ = board
    assert client.app.state.conn_factory is not client.app.state.write_factory
    conn = client.app.state.conn_factory()
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM orders")
    conn.close()


def test_the_writable_factory_writes_rows_by_name(tmp_path, monkeypatch):
    path = make_db(tmp_path, make_library(tmp_path, monkeypatch))
    conn = cc_app.writable_factory(path)()
    assert conn.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"] == 0
    conn.execute("DELETE FROM orders")
    conn.close()


def test_the_effect_names_what_the_order_will_do():
    assert actions.effect("hold") == "held — runs stop before the first GPU step"
    assert actions.effect("bump").startswith("queued at next run")
    assert "casebook" in actions.effect("redo", step_id="02")
    assert "02" in actions.effect("redo", step_id="02")


@pytest.mark.parametrize("origin, ok", [("http://127.0.0.1:8700", True), ("http://localhost", True),
                                        ("http://[::1]:8700", True), ("https://example.com", False),
                                        ("null", False)])
def test_a_local_origin_is_127_0_0_1_or_localhost(origin, ok):
    assert actions.local_origin({"origin": origin}) is ok


def test_no_origin_and_no_referer_is_a_local_shell():
    assert actions.local_origin({}) is True


def test_command_center_py_passes_a_writable_factory_and_lists_the_actions(tmp_path, monkeypatch, capsys):
    from test_command_center_api_contract import _load_command_center_py
    library = make_library(tmp_path, monkeypatch)
    path = make_db(tmp_path, library)
    cli, apps = _load_command_center_py(), []
    cli.main(["--db", str(path), "--library", str(library)], serve=lambda app, **kw: apps.append(app))
    assert apps[0].state.write_factory is not None
    cli.main(["--check", "--db", str(path), "--library", str(library)])
    out = capsys.readouterr().out
    for route in ("POST /act/hold", "POST /act/lift/{hold_id}", "POST /act/bump", "POST /act/retry",
                  "POST /act/requeue", "POST /act/redo"):
        assert route in out, route


def test_command_center_py_read_only_flag_starts_without_a_write_factory(tmp_path, monkeypatch):
    from test_command_center_api_contract import _load_command_center_py
    library = make_library(tmp_path, monkeypatch)
    path = make_db(tmp_path, library)
    apps = []
    _load_command_center_py().main(["--read-only", "--db", str(path), "--library", str(library)],
                                   serve=lambda app, **kw: apps.append(app))
    assert apps[0].state.write_factory is None


# --- the buttons ---


def test_the_unit_page_posts_hold_redo_requeue_and_bump(board):
    client, _ = board
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    for route in ("/act/hold", "/act/redo", "/act/requeue", "/act/bump"):
        assert f'hx-post="{route}"' in page, route
    assert '<select name="step_id"' in page and '<textarea name="note"' in page
    assert 'value="12"' in page and "also becomes a casebook row" in page
    assert 'hx-post="/act/retry"' not in page and 'title="C11"' not in page


def test_retry_is_offered_only_on_a_deferred_or_failed_unit(board):
    client, _ = board
    assert 'hx-post="/act/retry"' in client.get(f"/d/episode/{CODEX}/ep05").text
    assert 'hx-post="/act/retry"' in client.get(f"/d/episode/{CODEX}/ep07").text


def test_a_department_row_posts_hold_and_retry_or_bump(board):
    client, _ = board
    page = client.get("/d/episode").text
    assert 'hx-post="/act/hold"' in page and 'hx-post="/act/bump"' in page and 'hx-post="/act/retry"' in page
    assert 'title="C11"' not in page


def test_the_floor_holds_the_studio_and_lists_lifts(board):
    client, _ = board
    client.post("/act/hold", data={"scope": "book", "codex": CODEX, "reason": "re-plan"}, headers=LOCAL)
    page = client.get("/floor").text
    assert 'name="scope" value="studio"' in page and 'hx-post="/act/lift/1"' in page
    assert 'title="C11"' not in page


def test_the_book_page_holds_the_book(board):
    client, _ = board
    page = client.get(f"/b/{CODEX}").text
    assert 'hx-post="/act/hold"' in page and 'name="scope" value="book"' in page


def test_a_read_only_board_shows_its_buttons_disabled(tmp_path, monkeypatch):
    page = TestClient(make_app(tmp_path, monkeypatch)).get(f"/d/episode/{CODEX}/ep04").text
    assert "started read-only" in page and 'hx-post="/act/hold"' in page
