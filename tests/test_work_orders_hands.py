"""studio/work_orders.py: the hand.  A hold is a `holds` row plus an `orders`
row; a lift closes it; a hold's scope says whom it stops; an order is pending
until a run takes it, and taking it APPLIES it to the unit's work-order row
(bump -> priority 0, retry/requeue -> queued, redo -> the row's redo list)."""
from __future__ import annotations

import json

import pytest

from studio import db, work_orders

BOOK, OTHER = "20260901000001", "20260901000002"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=BOOK)
    db.insert_codex(connection, "Other", codex_id=OTHER)
    return connection


def _orders(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY id")]


def test_a_hold_is_a_holds_row_and_a_hold_order(conn):
    hold_id = work_orders.hold(conn, "book", "ep13 is being re-planned", codex_id=BOOK)
    row = conn.execute("SELECT * FROM holds WHERE id = ?", (hold_id,)).fetchone()
    assert row["scope"] == "book" and row["codex_id"] == BOOK and row["reason"] == "ep13 is being re-planned"
    assert row["held_by"] == "owner" and row["held_at"] and row["lifted_at"] is None
    (order,) = _orders(conn)
    assert (order["kind"], order["scope"], order["codex_id"], order["note"]) == ("hold", "book", BOOK, "ep13 is being re-planned")


def test_a_hold_needs_the_ids_its_scope_names(conn):
    with pytest.raises(ValueError, match="codex_id"):
        work_orders.hold(conn, "book", "no book named")
    with pytest.raises(ValueError, match="unit"):
        work_orders.hold(conn, "unit", "no unit named", codex_id=BOOK, stage="episode")
    with pytest.raises(ValueError, match="scope"):
        work_orders.hold(conn, "planet", "no such scope")


def test_a_lift_closes_the_hold_and_is_a_lift_order(conn):
    hold_id = work_orders.hold(conn, "studio", "power cut")
    work_orders.lift(conn, hold_id)
    row = conn.execute("SELECT lifted_at FROM holds WHERE id = ?", (hold_id,)).fetchone()
    assert row["lifted_at"]
    assert [o["kind"] for o in _orders(conn)] == ["hold", "lift"]
    assert work_orders.active_holds(conn) == []
    with pytest.raises(ValueError, match="lifted"):
        work_orders.lift(conn, hold_id)
    with pytest.raises(ValueError, match="no hold"):
        work_orders.lift(conn, 999)


def test_a_studio_hold_stops_everything_a_book_hold_its_book_a_unit_hold_its_unit(conn):
    assert not work_orders.is_held(conn, BOOK, "episode", "ep01")
    unit_hold = work_orders.hold(conn, "unit", "one take", codex_id=BOOK, stage="episode", unit="ep02")
    assert work_orders.is_held(conn, BOOK, "episode", "ep02")
    assert not work_orders.is_held(conn, BOOK, "episode", "ep01")
    assert not work_orders.is_held(conn, BOOK, "refs", "ep02")
    book_hold = work_orders.hold(conn, "book", "whole book", codex_id=BOOK)
    assert work_orders.is_held(conn, BOOK, "episode", "ep01") and work_orders.is_held(conn, BOOK, "refs", "main")
    assert not work_orders.is_held(conn, OTHER, "episode", "ep01")
    studio_hold = work_orders.hold(conn, "studio", "everything")
    assert work_orders.is_held(conn, OTHER, "episode", "ep01")
    assert [h["id"] for h in work_orders.active_holds(conn, BOOK, "episode", "ep02")] == [unit_hold, book_hold, studio_hold]
    assert [h["id"] for h in work_orders.active_holds(conn)] == [studio_hold]


def test_an_order_is_one_row_with_its_kind_and_scope_checked(conn):
    order_id = work_orders.order(conn, "bump", "unit", codex_id=BOOK, stage="episode", unit="ep04", note="tonight")
    (row,) = _orders(conn)
    assert row["id"] == order_id and row["kind"] == "bump" and row["unit"] == "ep04" and row["by"] == "owner"
    assert row["ts"] and row["taken_ts"] is None and row["taken_by_run"] is None
    with pytest.raises(ValueError, match="kind"):
        work_orders.order(conn, "cancel", "unit", codex_id=BOOK, stage="episode", unit="ep04")
    with pytest.raises(ValueError, match="scope"):
        work_orders.order(conn, "bump", "galaxy", codex_id=BOOK, stage="episode", unit="ep04")


def test_pending_orders_are_the_untaken_ones_addressed_to_the_unit(conn):
    mine = work_orders.order(conn, "bump", "unit", codex_id=BOOK, stage="episode", unit="ep04")
    work_orders.order(conn, "bump", "unit", codex_id=BOOK, stage="episode", unit="ep05")
    work_orders.order(conn, "bump", "unit", codex_id=OTHER, stage="episode", unit="ep04")
    assert [o["id"] for o in work_orders.pending_orders(conn, BOOK, "episode", "ep04")] == [mine]
    taken = work_orders.take_orders(conn, BOOK, "episode", "ep04", "run-1")
    assert [o["id"] for o in taken] == [mine]
    row = conn.execute("SELECT taken_ts, taken_by_run FROM orders WHERE id = ?", (mine,)).fetchone()
    assert row["taken_ts"] and row["taken_by_run"] == "run-1"
    assert work_orders.pending_orders(conn, BOOK, "episode", "ep04") == []
    assert work_orders.take_orders(conn, BOOK, "episode", "ep04", "run-2") == []


def test_a_bump_taken_puts_the_row_first(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="queued", priority=7)
    work_orders.order(conn, "bump", "unit", codex_id=BOOK, stage="episode", unit="ep04")
    work_orders.take_orders(conn, BOOK, "episode", "ep04", "run-1")
    assert db.work_order(conn, BOOK, "episode", "ep04")["priority"] == 0


def test_a_requeue_taken_queues_any_row_but_a_running_one(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="failed")
    work_orders.order(conn, "requeue", "unit", codex_id=BOOK, stage="episode", unit="ep04")
    work_orders.take_orders(conn, BOOK, "episode", "ep04", "run-1")
    assert db.work_order(conn, BOOK, "episode", "ep04")["state"] == "queued"
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="running")
    work_orders.order(conn, "requeue", "unit", codex_id=BOOK, stage="episode", unit="ep04")
    work_orders.take_orders(conn, BOOK, "episode", "ep04", "run-2")
    assert db.work_order(conn, BOOK, "episode", "ep04")["state"] == "running"


def test_a_redo_taken_lands_on_the_rows_redo_list_and_is_cleared_by_step(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="done")
    for step in ("07", "09", "07"):
        work_orders.order(conn, "redo", "unit", codex_id=BOOK, stage="episode", unit="ep04", step_id=step)
    work_orders.take_orders(conn, BOOK, "episode", "ep04", "run-1")
    assert json.loads(db.work_order(conn, BOOK, "episode", "ep04")["redo"]) == ["07", "09"]
    assert work_orders.redo_steps(conn, BOOK, "episode", "ep04") == {"07", "09"}
    work_orders.clear_redo(conn, BOOK, "episode", "ep04", "07")
    assert work_orders.redo_steps(conn, BOOK, "episode", "ep04") == {"09"}
    work_orders.clear_redo(conn, BOOK, "episode", "ep04", "09")
    assert db.work_order(conn, BOOK, "episode", "ep04")["redo"] is None
    assert work_orders.redo_steps(conn, BOOK, "episode", "ep99") == set()
    work_orders.clear_redo(conn, BOOK, "episode", "ep99", "07")


def test_a_hold_order_taken_applies_nothing_more(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="queued", priority=3)
    work_orders.hold(conn, "book", "wait", codex_id=BOOK)
    taken = work_orders.take_orders(conn, BOOK, "episode", "ep04", "run-1")
    assert [o["kind"] for o in taken] == ["hold"]
    row = db.work_order(conn, BOOK, "episode", "ep04")
    assert row["state"] == "queued" and row["priority"] == 3


def test_a_redos_default_artefact_is_as_given_else_the_steps_first_casebook_output():
    assert work_orders.default_artefact("episode", "02", "ep04", "episodes/ep04/x.png") == "episodes/ep04/x.png"
    assert work_orders.default_artefact("episode", "02", "ep04") == "episodes/ep04/plan.json"


def test_a_redo_whose_output_the_casebook_cannot_read_asks_for_the_artefact():
    with pytest.raises(ValueError, match="artefact"):
        work_orders.default_artefact("episode", "05", "ep04")
