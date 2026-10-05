"""An order's receipt tells the truth (panel ruling PKG-6, 6.2-6.4).  A bump,
retry, requeue or redo is applied only when a run of THAT unit starts
(step_runner -> work_orders.take_orders), and the queue claims only queued
rows, so the receipt names what will take the order -- or says that nothing
will (a done, deferred, failed or escalated unit: a dead letter).  The receipt
is a chip bound to its order id (`data-order`), pending until a run takes it
(the pulse's order-taken events move it), and `trigger` carries the id in the
HX-Trigger detail.  A hold's receipt is the one HOLD_EFFECT sentence.
Every test runs on a tmp DB; nothing here spends or starts a process."""
from __future__ import annotations

import json
import re
import subprocess

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_db, make_library, make_writable_app
from studio import db
from studio.command_center import actions

LOCAL = {"Origin": "http://127.0.0.1:8700"}


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    """A writable connection to the seeded tmp DB (ep03 done+flagged, ep04
    running, ep05 failed, ep06 queued, ep07 deferred)."""
    path = make_db(tmp_path, make_library(tmp_path, monkeypatch))
    c = db.get_connection(path)
    yield c
    c.close()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    app, _ = make_writable_app(tmp_path, monkeypatch)
    return TestClient(app)


@pytest.fixture(autouse=True)
def no_process(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("an action spawned a process")
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)


@pytest.mark.parametrize("unit, dead, words", [
    ("ep06", False, "the next run of episode takes it"),
    ("ep04", False, "waits for ep04's next run"),
    ("ep03", True, "no run will take it: ep03 is done"),
    ("ep05", True, "ep05 is failed"),
    ("ep07", True, "ep07 is deferred")])
def test_the_taker_is_named_by_the_units_state(conn, unit, dead, words):
    found = actions.taker(conn, CODEX, "episode", unit)
    assert found["dead"] is dead and words in found["taker"]


def test_a_held_unit_waits_for_the_run_after_the_lift(conn):
    db.upsert_work_order(conn, CODEX, "episode", "ep06", state="held")
    assert "after the lift" in actions.taker(conn, CODEX, "episode", "ep06")["taker"]


def test_a_redo_on_a_done_unit_says_no_run_will_take_it(client):
    response = client.post("/act/bump", data={"codex": CODEX, "stage": "episode", "unit": "ep03"},
                           headers=LOCAL)
    assert response.status_code == 200, response.text
    assert "no run will take it" in response.text and 'data-dead="1"' in response.text
    assert "queued at next run" not in response.text


def test_a_receipt_is_a_chip_bound_to_its_order_id(client):
    response = client.post("/act/bump", data={"codex": CODEX, "stage": "episode", "unit": "ep06"},
                           headers=LOCAL)
    order_id = re.search(r'data-order="(\d+)"', response.text).group(1)
    assert f"#{order_id}" in response.text and 'data-state="pending"' in response.text
    assert "the next run of episode takes it" in response.text and "data-say=" in response.text


def test_an_applied_order_says_applied_and_never_pending(client):
    response = client.post("/act/hold", data={"scope": "studio", "reason": "checking output"},
                           headers=LOCAL)
    assert 'data-state="applied"' in response.text and "pending" not in response.text
    assert actions.HOLD_EFFECT in response.text


def test_the_trigger_detail_holds_the_order_id():
    done = {"order_id": 41, "kind": "bump", "state": "pending"}
    assert json.loads(actions.trigger(done)) == {"orders-changed": {"order": 41, "kind": "bump", "state": "pending"}}


def test_the_spoken_sentence_names_the_order_and_its_taker():
    done = actions.receipt(7, "bump", "episode › ep03", taker="no run will take it: ep03 is done", dead=True)
    assert done["say"] == ("Order 7, bump episode › ep03: pending. "
                           "No run will take it: ep03 is done.")


def test_the_hold_sentence_has_one_definition():
    assert actions.effect("hold") == actions.HOLD_EFFECT
    assert "next GPU step" in actions.HOLD_EFFECT and "first GPU step" not in actions.HOLD_EFFECT
    assert "Nothing new starts until you lift" in actions.HOLD_EFFECT
