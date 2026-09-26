"""The owner asked for a table per department.  The ruling (decision 2026-09-25,
the Command Center) is ONE `work_orders` table, one row per (book, department,
unit), and a VIEW per registered department generated from the registry the way
the codex status columns are -- so a department registered in stages.yaml has its
table without anyone typing a DDL.  Two studio-wide views: v_queue (what a runner
takes next) and v_attention (what needs a person)."""
from __future__ import annotations

import pytest

from studio import db, registry

BOOK = "20260901000001"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=BOOK)
    return connection


def _views(conn) -> set[str]:
    return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'view'")}


def test_every_registered_stage_has_its_own_view(conn):
    assert {f"{s}_orders" for s in registry.stage_names()} <= _views(conn)
    assert {"v_queue", "v_attention"} <= _views(conn)


def test_a_row_shows_in_its_departments_view_and_in_no_other(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="queued")
    assert [r["unit"] for r in db.department_rows(conn, "episode")] == ["ep04"]
    assert db.department_rows(conn, "refs") == []
    assert conn.execute("SELECT COUNT(*) FROM refs_orders").fetchone()[0] == 0


def test_department_rows_refuses_a_stage_the_registry_does_not_know(conn):
    with pytest.raises(ValueError):
        db.department_rows(conn, "cooking")


def test_v_queue_orders_by_priority_then_sequence_and_hides_the_rest(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep13", state="queued", priority=1, sequence=1)
    db.upsert_work_order(conn, BOOK, "episode", "ep12", state="queued", priority=0, sequence=2)
    db.upsert_work_order(conn, BOOK, "episode", "ep11", state="queued", priority=0, sequence=1)
    db.upsert_work_order(conn, BOOK, "episode", "ep10", state="blocked", priority=0, sequence=0)
    units = [r["unit"] for r in conn.execute("SELECT unit FROM v_queue")]
    assert units == ["ep11", "ep12", "ep13"]


def test_v_attention_lists_the_four_states_that_need_a_person_and_no_other(conn):
    states = ("blocked", "queued", "running", "stale", "held", "deferred", "escalated", "failed", "done")
    for n, state in enumerate(states):
        db.upsert_work_order(conn, BOOK, "episode", f"ep{n:02d}", state=state)
    seen = {r["state"] for r in conn.execute("SELECT state FROM v_attention")}
    assert seen == {"failed", "deferred", "escalated", "stale"}


def test_the_row_is_unique_per_book_department_and_unit(conn):
    first = db.upsert_work_order(conn, BOOK, "episode", "ep04", state="queued")
    second = db.upsert_work_order(conn, BOOK, "episode", "ep04", state="running", step_id="03")
    assert first == second
    row = db.work_order(conn, BOOK, "episode", "ep04")
    assert (row["state"], row["step_id"]) == ("running", "03")
    assert conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 1


def test_a_missing_row_is_none(conn):
    assert db.work_order(conn, BOOK, "episode", "ep99") is None


def test_a_new_row_takes_its_home_and_kind_from_the_unit_grammar(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="blocked")
    db.upsert_work_order(conn, BOOK, "refs", "main", state="blocked")
    db.upsert_work_order(conn, BOOK, "analysis", "book", state="blocked")
    rows = {r["stage"]: r for r in conn.execute("SELECT * FROM work_orders")}
    assert (rows["episode"]["home"], rows["episode"]["kind"]) == ("episodes/ep04", "chapter")
    assert (rows["refs"]["home"], rows["refs"]["kind"]) == ("refs", "book")
    assert (rows["analysis"]["home"], rows["analysis"]["kind"]) == ("analysis", "book")
    assert rows["episode"]["updated_at"].endswith("Z")


def test_the_grammar_defaults_are_one_function():
    assert db._order_defaults("episode", "ep04") == {"home": "episodes/ep04", "kind": "chapter"}
    assert db._order_defaults("refs", "main") == {"home": "refs", "kind": "book"}
    assert db._order_defaults("trailer", "main") == {"home": "trailer", "kind": "book"}


def test_a_state_outside_the_nine_is_refused(conn):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        db.upsert_work_order(conn, BOOK, "episode", "ep04", state="parked")
