"""The pulse (panel ruling 2026-10-04, C1): one small JSON every two seconds
says, per section, a fingerprint from cheap DB aggregates -- the same while the
studio is quiet, new the moment a runner writes -- plus the shell's numbers and
the events since the client's cursor.  Nothing here renders HTML."""
from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, RUN, make_app, make_db, make_library
from studio import db
from studio.command_center import app as cc_app
from studio.command_center import pulse, views


@pytest.fixture()
def board(tmp_path, monkeypatch):
    """(client, db path) over the seeded tmp DB; the GPU card's progress is faked."""
    library = make_library(tmp_path, monkeypatch)
    path = make_db(tmp_path, library)
    app = cc_app.make_app(cc_app.readonly_factory(path), library, logs=tmp_path / "logs")
    app.state.progress = lambda codex, unit: {"vital": "live", "run_started": 1000.0, "now": 1500.0,
                                              "eta": {"finish_at": 2000.0, "finish": "21:35"}}
    return TestClient(app), path


def write_event(path, step="10", event="started", unit="ep04", run=RUN):
    conn = db.get_connection(path)
    db.add_event(conn, CODEX, "episode", step, event, run_id=run, unit=unit)
    conn.close()


def test_a_quiet_studio_answers_the_same_fingerprints(board):
    client, _ = board
    first, second = client.get("/api/pulse.json").json(), client.get("/api/pulse.json").json()
    assert first["fp"] == second["fp"] and first["boot"] == second["boot"]
    for key in ("shell", "floor", "attention", "orders", "lanes", "dept:episode", f"book:{CODEX}",
                f"unit:episode/{CODEX}/ep04"):
        assert key in first["fp"], key


def test_an_event_changes_the_sections_it_touches_and_not_the_orders(board):
    client, path = board
    before = client.get("/api/pulse.json").json()["fp"]
    write_event(path)
    after = client.get("/api/pulse.json").json()["fp"]
    assert after["floor"] != before["floor"] and after["dept:episode"] != before["dept:episode"]
    assert after[f"unit:episode/{CODEX}/ep04"] != before[f"unit:episode/{CODEX}/ep04"]
    assert after["orders"] == before["orders"] and after["dept:refs"] == before["dept:refs"]


def test_the_needs_count_is_the_inbox_count(board, tmp_path):
    client, path = board
    body = client.get("/api/pulse.json").json()
    conn = cc_app.readonly_factory(path)()
    assert body["shell"]["needs"] == views.inbox_count(conn) == len(views.attention(conn)) == 3
    assert body["shell"]["queue"] == 1


def test_the_shell_carries_dots_pins_the_gpu_and_no_hold(board):
    shell = board[0].get("/api/pulse.json").json()["shell"]
    assert shell["dept_dots"]["episode"]["running"] == 1 and shell["dept_dots"]["episode"]["failed"] == 1
    assert shell["dept_dots"]["refs"] == {"done": 1}
    assert shell["pins"] == [{"href": f"/d/episode/{CODEX}/ep04", "label": "ep04 · 09 shoot 18/25", "state": "running"}]
    gpu = shell["gpu"]
    assert gpu["unit"] == "ep04" and gpu["finish"] == "21:35" and gpu["vital"] == "live" and gpu["frac"] == 0.5
    assert gpu["held"] is False and shell["hold"] is None


def test_a_studio_hold_reaches_the_shell_and_the_gpu_card(board):
    client, path = board
    conn = db.get_connection(path)
    conn.execute("INSERT INTO holds (scope, reason, held_at) VALUES ('studio', 'night', '2026-10-04T19:21:00Z')")
    conn.commit()
    conn.close()
    shell = client.get("/api/pulse.json").json()["shell"]
    assert shell["hold"]["reason"] == "night" and shell["hold"]["since"] == "2026-10-04T19:21:00Z"
    assert shell["gpu"]["held"] is True


def test_the_pulse_stays_small(board):
    response = board[0].get("/api/pulse.json")
    assert len(response.content) <= 1536 and response.headers["cache-control"] == "no-store"


# --- events since the cursor (1.3) ---


def test_without_a_cursor_there_are_no_events_but_a_cursor(board):
    body = board[0].get("/api/pulse.json").json()
    assert body["events"] == [] and body["cursor"] > 0


def test_events_after_the_cursor_only_newest_first(board):
    client, path = board
    cursor = client.get("/api/pulse.json").json()["cursor"]
    write_event(path, "10", "started")
    write_event(path, "10", "completed")
    body = client.get(f"/api/pulse.json?since={cursor}").json()
    assert [e["id"] for e in body["events"]] == [cursor + 2, cursor + 1] and body["cursor"] == cursor + 2
    assert body["events"][0]["href"] == f"/d/episode/{CODEX}/ep04" and body["events"][0]["unit"] == "ep04"
    assert "completed" in body["events"][0]["text"] and "10" in body["events"][0]["text"]


def test_the_feed_is_capped_at_twenty(board):
    client, path = board
    for _ in range(25):
        write_event(path, "10", "started")
    assert len(client.get("/api/pulse.json?since=0").json()["events"]) == 20


def test_an_order_taken_after_the_cursor_is_an_event(board):
    client, path = board
    cursor = client.get("/api/pulse.json").json()["cursor"]
    conn = db.get_connection(path)
    conn.execute("INSERT INTO orders (ts, kind, scope, codex_id, stage, unit, taken_ts, taken_by_run)"
                 " VALUES ('2026-10-04T00:00:00Z', 'redo', 'unit', ?, 'episode', 'ep05', '2999-01-01T00:00:00Z', 'r9')",
                 (CODEX,))
    conn.commit()
    conn.close()
    events = client.get(f"/api/pulse.json?since={cursor}").json()["events"]
    assert events[0]["id"] == "ord-1" and events[0]["order"] == 1 and "r9" in events[0]["text"]


# --- the pure parts ---


def test_the_age_bucket_follows_the_youngest_row():
    now = 10 * 86400.0
    assert pulse.bucket(now, now - 30) == pulse.bucket(now + 20, now - 30) != pulse.bucket(now + 61, now - 30)
    assert pulse.bucket(now, now - 7200) == pulse.bucket(now + 600, now - 7200)
    assert pulse.bucket(now, None) == pulse.bucket(now + 3 * 3600, None)
    assert pulse.bucket(now, now - 7200, running=True) != pulse.bucket(now + 61, now - 7200, running=True)


def test_a_fingerprint_for_one_key_matches_the_map(board):
    _, path = board
    conn = cc_app.readonly_factory(path)()
    now = time.time()
    fps = pulse.fingerprints(conn, now)
    for key in ("floor", "attention", "orders", "lanes", "dept:episode", f"book:{CODEX}", f"unit:episode/{CODEX}/ep04"):
        assert pulse.fingerprint(conn, key, now) == fps[key], key
    assert pulse.fingerprint(conn, "unit:episode/x/none", now) == pulse.fingerprint(conn, "unit:episode/x/none", now)


def test_the_gpu_fraction_is_elapsed_over_the_span():
    assert pulse.frac({"run_started": 100.0, "now": 150.0, "eta": {"finish_at": 200.0}}) == 0.5
    assert pulse.frac({"run_started": 100.0, "now": 300.0, "eta": {"finish_at": 200.0}}) == 1.0
    assert pulse.frac({"run_started": None, "now": 300.0, "eta": {}}) is None


def test_the_progress_cache_reads_once_within_its_ttl():
    calls = []
    cache = pulse.Ttl(5.0)
    read = lambda: calls.append(1) or {"x": 1}
    assert cache.get("k", 100.0, read) == cache.get("k", 104.0, read) == {"x": 1} and len(calls) == 1
    cache.get("k", 106.0, read)
    assert len(calls) == 2


def test_the_boot_stamp_is_the_server_start(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    path = make_db(tmp_path, library)
    before = time.time()
    app = cc_app.make_app(cc_app.readonly_factory(path), library, logs=tmp_path / "logs")
    assert before <= app.state.boot <= time.time()
    assert json.loads(TestClient(app).get("/api/pulse.json").text)["boot"] == app.state.boot
