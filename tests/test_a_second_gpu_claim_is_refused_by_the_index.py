"""There is one GPU.  A second unit claiming it while one is running is refused
by the database itself -- a partial unique index on work_orders(gpu) WHERE gpu = 1
AND state = 'running' -- not by a check a runner might forget (decision 2026-09-25).
CPU work beside the GPU is fine, and a finished GPU row blocks nobody."""
from __future__ import annotations

import sqlite3

import pytest

from studio import db

BOOK = "20260901000001"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=BOOK)
    return connection


def test_a_second_running_gpu_row_is_an_integrity_error(conn):
    first = db.upsert_work_order(conn, BOOK, "episode", "ep04", state="queued")
    second = db.upsert_work_order(conn, BOOK, "episode", "ep05", state="queued")
    db.claim_gpu(conn, first)
    with pytest.raises(sqlite3.IntegrityError):
        db.claim_gpu(conn, second)
    assert db.work_order(conn, BOOK, "episode", "ep05")["state"] == "queued"


def test_a_running_cpu_row_beside_the_gpu_is_fine(conn):
    gpu = db.upsert_work_order(conn, BOOK, "episode", "ep04", state="queued")
    db.claim_gpu(conn, gpu)
    db.upsert_work_order(conn, BOOK, "analysis", "book", state="running", gpu=0)
    running = conn.execute("SELECT COUNT(*) FROM work_orders WHERE state = 'running'").fetchone()[0]
    assert running == 2


def test_a_done_gpu_row_does_not_block_the_next_claim(conn):
    db.upsert_work_order(conn, BOOK, "episode", "ep04", state="done", gpu=1)
    order = db.upsert_work_order(conn, BOOK, "episode", "ep05", state="queued")
    db.claim_gpu(conn, order)
    row = db.work_order(conn, BOOK, "episode", "ep05")
    assert (row["state"], row["gpu"]) == ("running", 1)
