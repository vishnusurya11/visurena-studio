"""The inbox rule (premium board P0.2; research 07 §5): a unit needs the owner
when it is failed, deferred, escalated or stale (v_attention, kept) OR when it
shipped with flags and the owner has not acknowledged them.  An acknowledgement
is one `acknowledge` orders row stamped with the unit's verdict state (its flags
count and the sha of its verdicts); it holds until that state changes, so a new
flag puts the unit back in Needs you.  The fixture's ep03 is done with flags."""
from __future__ import annotations

import json
import sqlite3

import pytest

from command_center_fixtures import CODEX, make_library, seed
from studio import db, work_orders
from studio.command_center import views

VERDICTS = {"PLAN": {"word": "APPROVE", "faults": 0}, "MASTER": {"word": "", "faults": 2},
            "EYE_TAKES": {"word": "flagged", "faults": 0}}


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, make_library(tmp_path, monkeypatch))
    db.upsert_work_order(connection, CODEX, "episode", "ep03", verdicts=json.dumps(VERDICTS))
    return connection


def _ack(conn, unit="ep03", note=None):
    row = db.work_order(conn, CODEX, "episode", unit)
    return work_orders.order(conn, "acknowledge", "unit", codex_id=CODEX, stage="episode", unit=unit,
                             note=db.ack_note(row, note))


def _units(conn):
    return [r["unit"] for r in views.attention(conn)]


def test_a_flagged_done_unit_needs_you_after_the_failed_and_deferred(conn):
    got = views.attention(conn)
    assert [r["unit"] for r in got] == ["ep05", "ep07", "ep03"]
    ep03 = got[-1]
    assert ep03["reason"] == "shipped with flags, not acknowledged" and ep03["glyph"] == "⚑2"
    assert ep03["gates"] == ["MASTER ⚑2", "EYE_TAKES ⚑"]


def test_an_acknowledged_unit_leaves_needs_you_and_the_failed_and_deferred_stay(conn):
    assert db.acknowledged(conn, CODEX, "episode", "ep03") is False
    _ack(conn)
    assert db.acknowledged(conn, CODEX, "episode", "ep03") is True
    assert _units(conn) == ["ep05", "ep07"]


def test_a_new_flag_reopens_it(conn):
    _ack(conn)
    db.upsert_work_order(conn, CODEX, "episode", "ep03", flags=3)
    assert db.acknowledged(conn, CODEX, "episode", "ep03") is False
    assert _units(conn) == ["ep05", "ep07", "ep03"]


def test_a_changed_verdict_reopens_it(conn):
    _ack(conn)
    db.upsert_work_order(conn, CODEX, "episode", "ep03",
                         verdicts=json.dumps({**VERDICTS, "MASTER": {"word": "", "faults": 1, "sha8": "beef"}}))
    assert "ep03" in _units(conn)


def test_an_owner_note_rides_with_the_stamp(conn):
    _ack(conn, note="seen it, ship")
    (row,) = conn.execute("SELECT * FROM orders").fetchall()
    assert row["note"].startswith("flags 2 · verdicts ") and row["note"].endswith(" — seen it, ship")
    assert db.acknowledged(conn, CODEX, "episode", "ep03") is True


def test_another_units_acknowledgement_does_not_count(conn):
    db.upsert_work_order(conn, CODEX, "episode", "ep09", state="done", flags=2, verdicts=json.dumps(VERDICTS))
    _ack(conn, unit="ep09")
    assert db.acknowledged(conn, CODEX, "episode", "ep03") is False
    assert db.acknowledged(conn, CODEX, "episode", "nope") is False


def test_a_clean_done_unit_never_needs_you(conn):
    db.upsert_work_order(conn, CODEX, "episode", "ep03", flags=0)
    assert _units(conn) == ["ep05", "ep07"]


def test_the_stamp_is_the_flags_and_the_verdicts_sha(conn):
    row = db.work_order(conn, CODEX, "episode", "ep03")
    stamp = db.verdict_stamp(row)
    assert stamp.startswith("flags 2 · verdicts ") and len(stamp.split()[-1]) == 8
    assert db.ack_note(row, "  ") == stamp


def test_non_pass_gates_are_the_amber_and_red_chips():
    verdicts = {"A": {"word": "pass"}, "B": {"word": "fail"}, "C": {"word": "x", "faults": 4}, "D": {}}
    assert views.non_pass_gates(verdicts) == ["B ✕", "C ⚑4"]


def test_an_old_orders_table_without_the_word_still_takes_an_acknowledge(tmp_path):
    old = sqlite3.connect(tmp_path / "old.db")
    old.row_factory = sqlite3.Row
    old.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, ts TEXT NOT NULL,"
                " kind TEXT NOT NULL CHECK (kind IN ('hold','lift','redo','bump','retry','requeue')),"
                " scope TEXT NOT NULL CHECK (scope IN ('studio','book','unit')),"
                " codex_id TEXT, stage TEXT, unit TEXT, step_id TEXT, note TEXT,"
                " by TEXT NOT NULL DEFAULT 'owner', taken_ts TEXT, taken_by_run TEXT)")
    work_orders.order(old, "acknowledge", "unit", codex_id=CODEX, stage="episode", unit="ep03", note="flags 1")
    assert old.execute("SELECT kind FROM orders").fetchone()["kind"] == "acknowledge"
    with pytest.raises(sqlite3.IntegrityError):
        old.execute("INSERT INTO orders (ts, kind, scope) VALUES ('t', 'bogus', 'unit')")
    with pytest.raises(ValueError):
        work_orders.order(old, "bogus", "unit", codex_id=CODEX, stage="episode", unit="ep03")


def test_a_fresh_orders_table_admits_the_word():
    assert "'acknowledge'" in db._WORK_ORDERS_DDL and "acknowledge" in work_orders.KINDS


def test_an_acknowledge_is_applied_at_once_not_pending(conn):
    _ack(conn)
    assert views.recent_orders(conn)[0]["taken"] == "applied"
