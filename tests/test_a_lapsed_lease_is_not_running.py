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
from studio.command_center import views

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
    app = make_app(tmp_path, monkeypatch)
    with sqlite3.connect(tmp_path / "t.db") as conn:
        conn.execute("UPDATE work_orders SET lease_until = '2020-01-01T00:00:00Z' WHERE unit = 'ep04'")
    return TestClient(app)


def test_a_lapsed_unit_is_not_pinned_nor_on_the_gpu_card(lapsed_client):
    shell = lapsed_client.get("/api/pulse.json").json()["shell"]
    assert shell["pins"] == [] and shell["gpu"] is None


def test_a_lapsed_unit_is_not_on_the_floor(lapsed_client):
    assert lapsed_client.get("/api/floor.json").json()["running"] == []


def test_no_department_dot_calls_a_lapsed_unit_running(lapsed_client):
    dots = lapsed_client.get("/api/pulse.json").json()["shell"]["dept_dots"]["episode"]
    assert "running" not in dots and dots.get("stale") == 1


def test_the_department_table_shows_it_stale(lapsed_client):
    rows = lapsed_client.get("/api/d/episode.json").json()["rows"]
    assert [r["shown"] for r in rows if r["unit"] == "ep04"] == ["stale"]
