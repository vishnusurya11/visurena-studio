"""The queue's finish (panel ruling 1.9, P06.4): a clean pass at the steps' p50s
is not what a unit takes as run (first to last event, 11-60 h measured), so the
ETA carries both and the clean one says "if clean"."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from command_center_fixtures import CODEX, make_library, seed
from studio import db
from studio.command_center import views

UTC = timezone.utc
MON = datetime(2026, 10, 5, 0, 0, tzinfo=UTC).timestamp()        # a Monday, 00:00 UTC
HIST = {"01": [60.0, 120.0, 180.0], "05": [600.0], "09": [3600.0, 7200.0, 10800.0]}


def test_the_clean_seconds_are_the_p50s_from_a_step_on():
    assert views.clean_seconds(HIST) == 120.0 + 600.0 + 7200.0
    assert views.clean_seconds(HIST, "05") == 600.0 + 7200.0 and views.clean_seconds({}, "01") == 0.0


def test_the_lane_eta_has_a_clean_finish_and_an_as_run_band():
    e = views.lane_eta(MON, clean_left=5 * 3600 + 29 * 60, units=2, walls=[86400.0, 2 * 86400.0, 3 * 86400.0])
    assert e["clean"] == MON + 5 * 3600 + 29 * 60
    assert e["as_run"] == MON + 2 * 2 * 86400.0 and e["as_run_lo"] < e["as_run"] < e["as_run_hi"]
    assert views.lane_eta(MON, 60.0, 1, [])["as_run"] is None


def test_the_kpi_reads_if_clean_and_names_the_as_run_days():
    e = views.lane_eta(MON, 5 * 3600 + 29 * 60, 1, [86400.0, 2 * 86400.0, 3 * 86400.0])
    words = views.eta_words(e, UTC)
    assert words["clean_text"] == "~Mon 05:29 if clean"
    assert words["as_run_text"].startswith("as run Tue") and "–" in words["as_run_text"]
    assert views.eta_words(views.lane_eta(MON, 60.0, 1, []), UTC)["as_run_text"] == ""


def test_a_day_span_on_one_day_is_one_name():
    assert views.day_span(MON, MON + 3600, UTC) == "Mon" and views.day_span(MON, MON + 86400, UTC) == "Mon–Tue"


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, library)
    return connection


def test_the_queue_eta_counts_the_running_unit_from_its_step(conn):
    e = views.queue_eta(conn, "episode", now=MON, tz=UTC)
    assert e is not None and e["units"] == 2 and e["clean"] >= MON
    assert e["clean_text"].endswith("if clean") and "as_run_text" in e


def test_a_stage_with_nothing_to_do_has_no_eta(conn):
    assert views.queue_eta(conn, "trailer", now=MON, tz=UTC) is None


def test_the_walls_are_first_to_last_event_of_a_done_unit(conn):
    walls = views.unit_walls(conn, "refs")
    assert len(walls) == 1 and walls[0] >= 0.0
