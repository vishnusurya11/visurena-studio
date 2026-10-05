"""Ages next to stamps (panel ruling 1.8): a row the board prints carries `age`
("9 d", "2 m") beside its ISO stamp, so a list reads at a glance and the stamp
moves to a title."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from command_center_fixtures import CODEX, make_library, seed
from studio import db
from studio.command_center import views

NOW = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("ts, want", [
    ("2026-10-04T11:59:30Z", "now"), ("2026-10-04T11:58:00Z", "2 m"), ("2026-10-04T11:00:01Z", "59 m"),
    ("2026-10-04T09:00:00Z", "3 h"), ("2026-10-03T12:00:01Z", "23 h"), ("2026-09-25T12:00:00Z", "9 d"),
    ("2026-10-04T12:05:00Z", "now"), (None, ""), ("junk", ""), ("2026-10-04T11:57:59.5Z", "2 m")])
def test_an_age_reads_in_one_unit(ts, want):
    assert views.age(NOW, ts) == want


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, library)
    connection.execute("INSERT INTO holds (scope, reason, held_at) VALUES ('studio', 'night', '2026-10-04T00:00:00Z')")
    connection.execute("INSERT INTO orders (ts, kind, scope) VALUES ('2026-10-04T00:00:00Z', 'hold', 'studio')")
    return connection


def test_rows_orders_holds_and_steps_carry_an_age(conn):
    assert all(r["age"] for r in views.queue(conn) + views.attention(conn) + views.floor(conn)["running"])
    assert views.recent_orders(conn)[0]["age"] and views.holds(conn)[0]["age"]
    assert all(r["age"] for r in views.today(conn))
