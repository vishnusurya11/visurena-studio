"""A running row whose lease ran out is not running (decision 2026-09-25: an expired lease is
`stale`). The tick writes that word only when it next runs; until then the board reads the
same rule itself: the row shows `stale`, it is not pinned, it is not the GPU card, it is not on
the floor and no department dot calls it running. Owner, 2026-10-06: "why is ep18 running when
it is already uploaded ... why is it pinned". TestClient over the tmp fixtures, $0."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import procs, views

NOW = datetime(2026, 10, 6, 0, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize("lease, lapsed", [("2026-10-05T20:43:34Z", True), ("2026-10-06T00:20:00Z", False), (None, False)])
def test_a_lease_lapses_when_its_time_has_passed(lease, lapsed):
    assert views.lease_lapsed({"state": "running", "lease_until": lease}, NOW) is lapsed


def test_only_a_running_row_can_lapse():
    assert views.lease_lapsed({"state": "done", "lease_until": "2026-10-05T20:43:34Z"}, NOW) is False


def test_a_lapsed_running_row_shows_stale(monkeypatch):
    monkeypatch.setattr(views, "utc_now", lambda: NOW)
    row = views.row_view({"state": "running", "lease_until": "2026-10-05T20:43:34Z", "stage": "episode",
                          "step_id": "11", "flags": 0, "started_at": None, "updated_at": None})
    assert row["shown"] == "stale" and row["elapsed"] == ""


@pytest.fixture()
def lapsed_client(tmp_path, monkeypatch):
    monkeypatch.setattr(procs, "list_processes", lambda: [])   # no process carries anything
    app = make_app(tmp_path, monkeypatch)
    with sqlite3.connect(tmp_path / "t.db") as conn:
        conn.execute("UPDATE work_orders SET lease_until = '2020-01-01T00:00:00Z' WHERE unit = 'ep04'")
    return TestClient(app)


@pytest.fixture()
def carried_client(tmp_path, monkeypatch):
    """ep04's lease lapsed, but a drive process still carries it (ep23's case,
    2026-10-07: step 09 renders for long stretches without a ledger write)."""
    monkeypatch.setattr(procs, "list_processes",
                        lambda: [procs.ProcInfo(4242, 1.0, f"python.exe scripts/episode/drive.py {CODEX} 4")])
    app = make_app(tmp_path, monkeypatch)
    with sqlite3.connect(tmp_path / "t.db") as conn:
        conn.execute("UPDATE work_orders SET lease_until = '2020-01-01T00:00:00Z' WHERE unit = 'ep04'")
    return TestClient(app)


def test_a_carried_unit_stays_running_pinned_and_on_the_gpu_card(carried_client):
    shell = carried_client.get("/api/pulse.json").json()["shell"]
    assert [p["href"].rsplit("/", 1)[-1] for p in shell["pins"]] == ["ep04"]
    assert shell["gpu"] and shell["gpu"]["unit"] == "ep04"


def test_a_carried_unit_is_on_the_floor_and_not_in_needs_you(carried_client):
    running = carried_client.get("/api/floor.json").json()["running"]
    assert [r["unit"] for r in running] == ["ep04"]
    assert carried_client.get("/api/pulse.json").json()["shell"]["needs"] == 3


def test_a_carried_units_dot_and_row_say_running(carried_client):
    dots = carried_client.get("/api/pulse.json").json()["shell"]["dept_dots"]["episode"]
    assert dots.get("running") == 1 and "stale" not in dots
    rows = carried_client.get("/api/d/episode.json").json()["rows"]
    assert [r["shown"] for r in rows if r["unit"] == "ep04"] == ["running"]


def test_a_process_of_another_unit_carries_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(procs, "list_processes",
                        lambda: [procs.ProcInfo(1, 1.0, f"python.exe scripts/episode/drive.py {CODEX} 23")])
    app = make_app(tmp_path, monkeypatch)
    with sqlite3.connect(tmp_path / "t.db") as conn:
        conn.execute("UPDATE work_orders SET lease_until = '2020-01-01T00:00:00Z' WHERE unit = 'ep04'")
    client = TestClient(app)
    assert client.get("/api/pulse.json").json()["shell"]["pins"] == []


def test_a_lapsed_unit_is_not_pinned_nor_on_the_gpu_card(lapsed_client):
    shell = lapsed_client.get("/api/pulse.json").json()["shell"]
    assert shell["pins"] == [] and shell["gpu"] is None


def test_a_lapsed_unit_is_not_on_the_floor(lapsed_client):
    assert lapsed_client.get("/api/floor.json").json()["running"] == []


def test_no_department_dot_calls_a_lapsed_unit_running(lapsed_client):
    dots = lapsed_client.get("/api/pulse.json").json()["shell"]["dept_dots"]["episode"]
    assert "running" not in dots and dots.get("stale") == 1


def test_a_lapsed_unit_lands_in_needs_you(lapsed_client):
    """Referee D1: ep18's class of fault must not vanish from home -- it needs a person."""
    shell = lapsed_client.get("/api/pulse.json").json()["shell"]
    page = lapsed_client.get("/inbox").text
    assert shell["needs"] == 4 and "ep04" in page   # seeded ep05 failed + ep07 deferred + ep03 flagged, + the lapsed ep04


def test_a_lapsed_unit_is_in_the_attention_list_as_stale(lapsed_client):
    inbox = lapsed_client.get("/inbox").text
    card = inbox[inbox.index("ep04"):][:600]
    assert "stale" in card


def test_the_department_table_shows_it_stale(lapsed_client):
    rows = lapsed_client.get("/api/d/episode.json").json()["rows"]
    assert [r["shown"] for r in rows if r["unit"] == "ep04"] == ["stale"]


def _lease(tmp_path, unit, stamp):
    with sqlite3.connect(tmp_path / "t.db") as conn:
        conn.execute("UPDATE work_orders SET lease_until = ? WHERE unit = ?", (stamp, unit))


def recent(minutes=10):
    from datetime import timedelta
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


AUTOPILOT = "python.exe scripts/episode/autopilot.py run --book 20260901000001_a-book"


def test_a_book_wide_carrier_vouches_for_a_freshly_lapsed_unit(tmp_path, monkeypatch):
    """ep23, 2026-10-07: the autopilot names the book, not the unit; it carries the
    row whose lease starved minutes ago."""
    monkeypatch.setattr(procs, "list_processes", lambda: [procs.ProcInfo(1, 1.0, AUTOPILOT)])
    app = make_app(tmp_path, monkeypatch)
    _lease(tmp_path, "ep04", recent(10))
    client = TestClient(app)
    assert [p["href"].rsplit("/", 1)[-1] for p in client.get("/api/pulse.json").json()["shell"]["pins"]] == ["ep04"]


def test_a_book_wide_carrier_never_revives_a_long_dead_row(tmp_path, monkeypatch):
    """ep18's row died days ago; a live autopilot on the same book must not revive it."""
    monkeypatch.setattr(procs, "list_processes", lambda: [procs.ProcInfo(1, 1.0, AUTOPILOT)])
    app = make_app(tmp_path, monkeypatch)
    _lease(tmp_path, "ep04", "2020-01-01T00:00:00Z")
    client = TestClient(app)
    shell = client.get("/api/pulse.json").json()["shell"]
    assert shell["pins"] == [] and shell["dept_dots"]["episode"].get("stale") == 1
