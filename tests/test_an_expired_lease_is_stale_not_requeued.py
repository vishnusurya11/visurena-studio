"""The GPU ruling (decision 2026-09-25): a running row whose lease has run out
is `stale` -- never requeued by the tick.  A runner that died mid-run left a
unit nobody is working on; whether it goes again is the owner's (a `requeue`
order), not the scheduler's.  A live lease and a row with no lease (today's
runners set none; C9 does) are left alone, and a stale row stays stale on
every later tick."""
from __future__ import annotations

import pytest

from studio import db, episode_home, tick, work_orders

CODEX = "20260901000001"


@pytest.fixture()
def book(tmp_path, monkeypatch):
    root = tmp_path / "library"
    folder = root / f"{CODEX}_a-book"
    (folder / "episodes" / "ep04").mkdir(parents=True)
    monkeypatch.setattr(episode_home, "LIBRARY", root)
    return folder


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _running(conn, unit, lease_until):
    db.upsert_work_order(conn, CODEX, "episode", unit, state="running", lease_until=lease_until,
                         claimed_by="episode.py", run_id="r1")


def test_an_expired_lease_is_stale_with_its_reason(conn):
    _running(conn, "ep04", "2026-09-26T10:00:00Z")
    assert tick.sweep_leases(conn, "2026-09-26T10:16:00Z") == 1
    row = db.work_order(conn, CODEX, "episode", "ep04")
    assert (row["state"], row["blocked_on"]) == ("stale", "lease expired")
    assert row["run_id"] == "r1"                       # the dead run stays named


def test_a_live_lease_and_a_row_without_one_are_left_alone(conn):
    _running(conn, "ep04", "2026-09-26T10:30:00Z")
    _running(conn, "ep05", None)
    assert tick.sweep_leases(conn, "2026-09-26T10:16:00Z") == 0
    assert db.work_order(conn, CODEX, "episode", "ep04")["state"] == "running"
    assert db.work_order(conn, CODEX, "episode", "ep05")["state"] == "running"


def test_a_stale_row_is_not_requeued_by_a_later_tick(conn, book):
    _running(conn, "ep04", "2026-09-26T10:00:00Z")
    hold_path = book.parent / "RENDER_HOLD"
    assert tick.tick(conn, book.parent, hold_path=hold_path, now="2026-09-26T10:16:00Z")["stale"] == 1
    for rel in ("analysis/scenes.json", "refs/refs.json"):
        (book / rel).parent.mkdir(parents=True, exist_ok=True)
        (book / rel).write_text("{}", encoding="utf-8")
    db.upsert_work_order(conn, CODEX, "analysis", "book", state="done")
    db.upsert_work_order(conn, CODEX, "refs", "main", state="done")
    counts = tick.tick(conn, book.parent, hold_path=hold_path, now="2026-09-26T11:00:00Z")
    assert counts["stale"] == 0
    assert db.work_order(conn, CODEX, "episode", "ep04")["state"] == "stale"   # requires done, inputs there: still stale
    assert [r["unit"] for r in conn.execute("SELECT unit FROM v_attention")] == ["ep04"]


def test_only_a_requeue_order_brings_a_stale_row_back(conn):
    _running(conn, "ep04", "2026-09-26T10:00:00Z")
    tick.sweep_leases(conn, "2026-09-26T10:16:00Z")
    work_orders.order(conn, "requeue", "unit", codex_id=CODEX, stage="episode", unit="ep04")
    work_orders.take_orders(conn, CODEX, "episode", "ep04", "r2")
    assert db.work_order(conn, CODEX, "episode", "ep04")["state"] == "queued"
