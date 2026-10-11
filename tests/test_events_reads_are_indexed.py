"""The Command Center's events reads never scan the table (2026-10-11): the
episode lane, the ETA history and the unit walls each read all 26k rows per
pulse, a 7 MB burst every ~10 s that held the D: disk at 800-1700% busy."""
import sqlite3

from studio import db

READS = {
    "viz.event_rows": ("SELECT event_ts, step_id, event, run_id FROM events WHERE stage = 'episode'"
                       " AND event_ts >= ? ORDER BY id", ("2026-10-11",)),
    "eta.step_history": ("SELECT event_ts, step_id, event, run_id, unit FROM events WHERE stage = ?"
                         " AND event IN ('started', 'completed') ORDER BY id", ("episode",)),
    "views.unit_walls": ("SELECT MIN(e.event_ts), MAX(e.event_ts) FROM events e JOIN work_orders w"
                         " ON w.id = e.order_id WHERE w.stage = ? AND w.state = 'done' GROUP BY w.id",
                         ("episode",)),
}


def plan(conn: sqlite3.Connection, sql: str, args: tuple) -> list[str]:
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql, args)]


def fresh() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    db.init_db(conn)
    return conn


def test_no_command_center_read_scans_the_events_table():
    conn = fresh()
    scans = {name: p for name, (sql, args) in READS.items()
             for p in [plan(conn, sql, args)] if any(s.startswith("SCAN e") for s in p)}
    assert scans == {}


def test_init_db_twice_keeps_one_copy_of_each_index():
    conn = fresh()
    db.init_db(conn)
    names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'"
                                        " AND tbl_name = 'events'")]
    assert sorted(names) == sorted(set(names))
    assert {"ix_events_stage_ts", "ix_events_order"} <= set(names)
