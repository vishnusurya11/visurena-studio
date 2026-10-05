"""POST /act/acknowledge (premium board P0.2): the owner's "I have seen these
flags" is ONE orders row through work_orders.order, stamped with the unit's
verdict state, under the same rules as every other /act/ route -- refused 403
from a foreign page, 405 on a read-only board, 404 for a unit with no row, 422
for a unit with nothing to acknowledge.  The home's Needs you strip offers the
button on a flagged row, and the strip and the nav count it."""
from __future__ import annotations

import subprocess

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app, make_writable_app
from studio import db

LOCAL = {"Origin": "http://127.0.0.1:8700"}
EP03 = {"codex": CODEX, "stage": "episode", "unit": "ep03"}


@pytest.fixture()
def board(tmp_path, monkeypatch):
    app, path = make_writable_app(tmp_path, monkeypatch)

    def read(sql):
        conn = db.get_connection(path)
        try:
            return [dict(r) for r in conn.execute(sql)]
        finally:
            conn.close()
    return TestClient(app), read


@pytest.fixture(autouse=True)
def no_process(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("an action spawned a process")
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)


def test_an_acknowledge_is_one_orders_row_and_a_receipt(board):
    client, read = board
    response = client.post("/act/acknowledge", data={**EP03, "note": "seen"}, headers=LOCAL)
    assert response.status_code == 200, response.text
    (row,) = read("SELECT * FROM orders")
    assert (row["kind"], row["scope"], row["codex_id"], row["stage"], row["unit"]) == (
        "acknowledge", "unit", CODEX, "episode", "ep03")
    assert row["note"].startswith("flags 2 · verdicts ") and row["note"].endswith("— seen")
    assert f"#{row['id']}" in response.text and "acknowledged" in response.text
    assert response.headers["HX-Trigger"] == "orders-changed"


def test_an_acknowledged_unit_leaves_the_home_strip(board):
    client, _ = board
    assert "ep03" in client.get("/partials/attention").text
    client.post("/act/acknowledge", data=EP03, headers=LOCAL)
    assert "ep03" not in client.get("/partials/attention").text


@pytest.mark.parametrize("header", [{"Origin": "http://evil.example"}, {"Referer": "http://evil.example/x"}])
def test_a_cross_origin_acknowledge_is_refused_403(board, header):
    client, read = board
    assert client.post("/act/acknowledge", data=EP03, headers=header).status_code == 403
    assert read("SELECT * FROM orders") == []


def test_a_read_only_board_answers_405(tmp_path, monkeypatch):
    client = TestClient(make_app(tmp_path, monkeypatch))
    response = client.post("/act/acknowledge", data=EP03, headers=LOCAL)
    assert response.status_code == 405 and "read-only" in response.text


@pytest.mark.parametrize("unit, status", [("ep99", 404), ("ep05", 422), ("ep06", 422)])
def test_a_unit_with_no_row_or_no_flags_is_refused(board, unit, status):
    client, read = board
    assert client.post("/act/acknowledge", data={**EP03, "unit": unit}, headers=LOCAL).status_code == status
    assert read("SELECT * FROM orders") == []


def test_the_home_strip_offers_acknowledge_on_the_flagged_row_and_counts_it(board):
    client, _ = board
    page = client.get("/").text
    assert "Needs you (3)" in page and "shipped with flags, not acknowledged" in page
    assert page.count('hx-post="/act/acknowledge"') == 1 and 'name="unit" value="ep03"' in page


def test_the_nav_counts_what_needs_you(board):
    client, _ = board
    page = client.get("/").text
    assert 'hx-get="/partials/needs-you-count"' in page
    assert client.get("/partials/needs-you-count").text.strip() == "3"
    client.post("/act/acknowledge", data=EP03, headers=LOCAL)
    assert client.get("/partials/needs-you-count").text.strip() == "2"
