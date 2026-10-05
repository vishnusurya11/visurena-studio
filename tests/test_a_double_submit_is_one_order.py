"""A double press is one order (panel ruling PKG-6, 6.1).  The forms disable
their button while the POST is in flight and drop a second request
(`hx-disabled-elt`, `hx-sync="this:drop"`); the server is the second wall: an
order that is already pending for the same unit, kind and step (and note), an
open hold with the same scope and reason, or an acknowledge of a stamp that is
already acknowledged answers with the FIRST order's receipt and writes nothing.
Tmp DB only; nothing spends or starts a process."""
from __future__ import annotations

import subprocess

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_writable_app
from studio import db

LOCAL = {"Origin": "http://127.0.0.1:8700"}


@pytest.fixture()
def board(tmp_path, monkeypatch):
    app, path = make_writable_app(tmp_path, monkeypatch)

    def count(sql):
        conn = db.get_connection(path)
        try:
            return conn.execute(sql).fetchone()[0]
        finally:
            conn.close()
    return TestClient(app), count


@pytest.fixture(autouse=True)
def no_process(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("an action spawned a process")
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)


def _twice(client, path, data):
    first = client.post(path, data=data, headers=LOCAL)
    second = client.post(path, data=data, headers=LOCAL)
    assert first.status_code == second.status_code == 200, second.text
    return first.text, second.text


@pytest.mark.parametrize("kind", ["bump", "retry", "requeue"])
def test_a_second_unit_order_while_the_first_is_pending_writes_nothing(board, kind):
    client, count = board
    first, second = _twice(client, f"/act/{kind}", {"codex": CODEX, "stage": "episode", "unit": "ep06"})
    assert count("SELECT COUNT(*) FROM orders") == 1
    assert 'data-order="1"' in first and 'data-order="1"' in second and "already placed" in second


def test_a_second_redo_with_the_same_note_writes_nothing(board):
    client, count = board
    data = {"codex": CODEX, "stage": "episode", "unit": "ep04", "step_id": "02", "note": "wrong street"}
    _twice(client, "/act/redo", data)
    assert count("SELECT COUNT(*) FROM orders") == 1


def test_a_redo_with_other_words_is_a_second_order(board):
    client, count = board
    data = {"codex": CODEX, "stage": "episode", "unit": "ep04", "step_id": "02", "note": "wrong street"}
    client.post("/act/redo", data=data, headers=LOCAL)
    client.post("/act/redo", data={**data, "note": "and the lamp"}, headers=LOCAL)
    assert count("SELECT COUNT(*) FROM orders") == 2


def test_a_second_identical_hold_writes_nothing(board):
    client, count = board
    first, second = _twice(client, "/act/hold", {"scope": "studio", "reason": "checking output"})
    assert count("SELECT COUNT(*) FROM holds") == 1 and count("SELECT COUNT(*) FROM orders") == 1
    assert "hold 1" in second and "already placed" in second


def test_a_second_acknowledge_of_the_same_stamp_writes_nothing(board):
    client, count = board
    _twice(client, "/act/acknowledge", {"codex": CODEX, "stage": "episode", "unit": "ep03"})
    assert count("SELECT COUNT(*) FROM orders") == 1


def test_an_order_taken_by_a_run_does_not_block_the_next(board):
    client, count = board
    data = {"codex": CODEX, "stage": "episode", "unit": "ep06"}
    client.post("/act/bump", data=data, headers=LOCAL)
    conn = client.app.state.write_factory()
    conn.execute("UPDATE orders SET taken_ts = 'x', taken_by_run = 'r'")
    conn.commit()
    conn.close()
    client.post("/act/bump", data=data, headers=LOCAL)
    assert count("SELECT COUNT(*) FROM orders") == 2
