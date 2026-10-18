"""Which flags need the owner is answered for every row at once (page experts 2026-10-18, D4 /
backend #5, known-open since 04 #2): `flags_open` per flagged row cost ~115 of the 132 SQL
statements on every pulse (43 acknowledge queries plus work-order re-reads), growing with
every flagged row.  `open_flag_keys` reads the flagged rows, the acknowledge notes and the
done publish rows once; the inbox and the dots read the set."""
from __future__ import annotations

from command_center_fixtures import CODEX, make_db, make_library
from studio import db
from studio.command_center import views


def flagged(conn, n: int) -> None:
    for i in range(n):
        db.upsert_work_order(conn, CODEX, "episode", f"ep{50 + i}", state="done", flags=2)


def statements(conn, fn) -> int:
    seen = []
    conn.set_trace_callback(seen.append)
    try:
        fn()
    finally:
        conn.set_trace_callback(None)
    return len([s for s in seen if s.lstrip().upper().startswith("SELECT")])


def test_the_set_agrees_with_the_one_row_rule(tmp_path, monkeypatch):
    conn = db.get_connection(make_db(tmp_path, make_library(tmp_path, monkeypatch)))
    flagged(conn, 5)
    rows = [dict(r) for r in views.flagged_rows(conn)]
    assert views.open_flag_keys(conn) == {views.flag_key(r) for r in rows if views.flags_open(conn, r)}


def test_the_inbox_and_the_dots_cost_the_same_for_forty_flagged_rows_as_for_four(tmp_path, monkeypatch):
    conn = db.get_connection(make_db(tmp_path, make_library(tmp_path, monkeypatch)))
    flagged(conn, 4)
    few = statements(conn, lambda: (views.flagged_unacknowledged(conn), views.closed_flags(conn)))
    for i in range(36):
        db.upsert_work_order(conn, CODEX, "episode", f"ep{100 + i}", state="done", flags=1)
    many = statements(conn, lambda: (views.flagged_unacknowledged(conn), views.closed_flags(conn)))
    assert many == few and many <= 12, (few, many)
