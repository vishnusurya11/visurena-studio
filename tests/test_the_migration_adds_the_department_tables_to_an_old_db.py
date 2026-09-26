"""A live runner writes db/visurena_studio.db while the studio evolves, so the
Command Center's tables arrive the way every column before them did: init_db on
an old file ADDs and CREATEs, never renames, drops or rebuilds.  An old DB with
only codex + events (the four-word CHECK) must gain the four tables, the views,
events.order_id and usage.unit/order_id -- with every events row untouched --
and a second init_db must change nothing."""
from __future__ import annotations

import pytest

from studio import db, registry
from tests.test_events_carry_a_unit import OLD_DDL

OLD_USAGE = """
CREATE TABLE usage (id INTEGER PRIMARY KEY, recorded_at TEXT NOT NULL, codex_id TEXT NOT NULL,
  stage TEXT NOT NULL, step_id TEXT NOT NULL, tier TEXT, model TEXT,
  input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0, cost_usd REAL);
"""


@pytest.fixture()
def old(tmp_path):
    conn = db.get_connection(tmp_path / "old.db")
    conn.executescript(OLD_DDL)
    conn.execute("INSERT INTO codex (id, name, updated_at) VALUES ('20260901000001', 'B', 'x')")
    conn.execute("INSERT INTO events (event_ts, codex_id, stage, step_id, event, run_id, detail)"
                 " VALUES ('t1', '20260901000001', 'analysis', '01', 'completed', 'r1', 'd1')")
    conn.execute("INSERT INTO events (event_ts, codex_id, stage, step_id, event)"
                 " VALUES ('t2', '20260901000001', 'analysis', '02', 'failed')")
    conn.commit()
    return conn


def _names(conn, kind: str) -> set[str]:
    return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = ?", (kind,))}


def _cols(conn, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}


def test_an_old_db_gains_the_four_tables_and_the_views(old):
    db.init_db(old)
    assert {"work_orders", "work_steps", "orders", "holds", "usage"} <= _names(old, "table")
    assert {f"{s}_orders" for s in registry.stage_names()} | {"v_queue", "v_attention"} <= _names(old, "view")
    assert {"ix_work_orders_queue", "ux_gpu_lease"} <= _names(old, "index")


def test_an_old_db_gains_the_journal_and_ledger_columns(old):
    db.init_db(old)
    assert "order_id" in _cols(old, "events")
    assert {"unit", "order_id"} <= _cols(old, "usage")


def test_an_old_usage_table_is_widened_not_replaced(old):
    old.executescript(OLD_USAGE)
    old.execute("INSERT INTO usage (recorded_at, codex_id, stage, step_id) VALUES ('t', 'c', 's', '01')")
    old.commit()
    db.init_db(old)
    assert {"unit", "order_id"} <= _cols(old, "usage")
    assert old.execute("SELECT COUNT(*) FROM usage").fetchone()[0] == 1


def test_the_old_events_rows_survive_untouched(old):
    before = [tuple(r) for r in old.execute("SELECT id, event_ts, codex_id, stage, step_id, event, run_id, detail FROM events ORDER BY id")]
    db.init_db(old)
    after = [tuple(r) for r in old.execute("SELECT id, event_ts, codex_id, stage, step_id, event, run_id, detail FROM events ORDER BY id")]
    assert after == before and len(after) == 2
    assert old.execute("SELECT order_id FROM events").fetchone()["order_id"] is None


def test_init_db_twice_is_a_no_op(old):
    db.init_db(old)
    schema = sorted(tuple(r) for r in old.execute("SELECT type, name, sql FROM sqlite_master"))
    db.init_db(old)
    assert sorted(tuple(r) for r in old.execute("SELECT type, name, sql FROM sqlite_master")) == schema


def test_add_column_is_idempotent(old):
    db._add_column(old, "events", "order_id", "INTEGER")
    db._add_column(old, "events", "order_id", "INTEGER")
    assert "order_id" in _cols(old, "events")


def test_the_migration_only_adds_and_creates():
    """The guard for the live DB: no RENAME, DROP or table rebuild in the Command
    Center's migration (the events rebuild lives in _migrate_events, on purpose)."""
    import inspect
    source = (inspect.getsource(db._migrate_work_orders) + inspect.getsource(db._add_column)
              + db._WORK_ORDERS_DDL)
    for verb in ("RENAME TO", "DROP TABLE", "DROP VIEW", "DROP INDEX", "INSERT INTO", "DELETE FROM"):
        assert verb not in source.upper()
