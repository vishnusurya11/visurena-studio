"""The department table reads at a glance (2026-09-26, the owner: "improve this
visually"): each unit carries a bar of its steps -- one segment per registry
step, coloured by that step's state -- the time since it last moved, its GPU
in hours, and the units are grouped under their book."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from command_center_fixtures import CODEX, make_library, seed
from studio import db, registry
from studio.command_center import views


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, library)
    return connection


def _iso(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_ago_says_how_long_since_a_row_moved():
    assert views.ago(None) == ""
    assert views.ago(_iso(timedelta(seconds=20))) == "just now"
    assert views.ago(_iso(timedelta(minutes=12))) == "12m ago"
    assert views.ago(_iso(timedelta(hours=7, minutes=3))) == "7h ago"
    assert views.ago(_iso(timedelta(days=3, hours=2))) == "3d ago"
    assert views.ago("not a time") == ""


def test_gpu_reads_in_hours_and_nothing_is_a_dash():
    assert views.gpu_hours(None) == "–" and views.gpu_hours(0) == "–"
    assert views.gpu_hours(35220) == "9.8 h"
    assert views.gpu_hours(1380) == "23 m"


def test_the_bar_takes_each_steps_own_state_first():
    row = {"stage": "episode", "state": "running", "step_id": "09"}
    bar = views.step_bar(row, {"01": "done", "02": "skipped", "09": "running"})
    by_id = {s["id"]: s["css"] for s in bar}
    assert len(bar) == len(registry.steps("episode")) and bar[0]["name"] == "bind"
    assert by_id["01"] == "green" and by_id["02"] == "green"      # skipped = its output was on disk
    assert by_id["09"] == "blue" and by_id["10"] == "none"


def test_a_row_without_step_rows_is_drawn_from_its_cursor():
    bar = views.step_bar({"stage": "episode", "state": "deferred", "step_id": "02"}, {})
    assert [s["css"] for s in bar[:3]] == ["green", "purple", "none"]
    done = views.step_bar({"stage": "episode", "state": "done", "step_id": "11"}, {})
    assert {s["css"] for s in done} == {"green"}


def test_units_are_grouped_under_their_book_attention_first():
    rows = [{"codex_id": "b", "shown": "done", "unit": "ep01", "sequence": 1},
            {"codex_id": "a", "shown": "done", "unit": "ep02", "sequence": 2},
            {"codex_id": "b", "shown": "running", "unit": "ep03", "sequence": 3}]
    groups = views.book_groups(rows, {"a": "Alpha", "b": "Beta"})
    assert [g["name"] for g in groups] == ["Beta", "Alpha"]      # the book with work running leads
    assert [r["unit"] for r in groups[0]["rows"]] == ["ep01", "ep03"]
    assert groups[0]["done"] == 1 and groups[0]["total"] == 2


def test_gate_labels_drop_the_eye_prefix():
    assert views.gate_label("EYE_PANELS") == "panels" and views.gate_label("PLAN") == "plan"


def test_the_department_carries_groups_bars_and_times(conn):
    dept = views.department(conn, "episode")
    assert dept["groups"] and sum(len(g["rows"]) for g in dept["groups"]) == len(dept["rows"])
    ep04 = next(r for r in dept["rows"] if r["unit"] == "ep04")
    assert len(ep04["bar"]) == len(registry.steps("episode")) and ep04["gpu_h"] and "ago" in ep04 and ep04["gate_labels"]
