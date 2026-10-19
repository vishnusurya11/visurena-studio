"""The finish counts the rework relaunches add (timeline debate 2026-10-18, D2; owner go): a
published WotW episode re-entered an earlier step 6.2 times on average and its step time ran a
median +15 % (0-65 %) over its first pass; the median chain alone ignored it.  The p50 is the
time left x (1 + the measured median share), the high end x (1 + the 80th percentile), the low
end the clean first pass; firm with five finished episodes and a tight band, else rough."""
from __future__ import annotations

import sqlite3

import pytest

from studio import eta


def test_a_units_share_is_its_repeat_time_over_its_first_pass():
    pairs = [("b/ep01", "02", 100.0), ("b/ep01", "09", 300.0), ("b/ep01", "09", 100.0),
             ("b/ep02", "02", 200.0)]
    shares = eta.rework_shares(pairs, finished={"b/ep01", "b/ep02"})
    assert shares == pytest.approx([0.25, 0.0])


def test_an_unfinished_unit_is_not_a_norm():
    assert eta.rework_shares([("b/ep03", "02", 100.0), ("b/ep03", "02", 900.0)], finished=set()) == []


def test_the_band_is_the_median_and_p80_or_the_prior():
    assert eta.rework_band([0.1]) == (eta.REWORK_PRIOR, 2 * eta.REWORK_PRIOR, 1)
    p50, p80, n = eta.rework_band([0.0, 0.1, 0.15, 0.2, 0.65])
    assert (p50, n) == (0.15, 5) and 0.2 <= p80 <= 0.65


def test_rework_stretches_what_is_left_not_what_is_done():
    p = {"finish_at": 1600.0, "lo": 1500.0, "hi": 1700.0, "capped": False, "long": False}
    got = eta.with_rework(p, 1000.0, (0.15, 0.5, 9), ceiling_at=1e9)
    assert got["finish_at"] == pytest.approx(1690.0) and got["hi"] == pytest.approx(1900.0)
    assert got["lo"] == 1600.0 and got["rework"] == 0.15 and got["rework_n"] == 9


def test_the_ceiling_still_caps_the_stretched_finish():
    p = {"finish_at": 1600.0, "lo": 1500.0, "hi": 1700.0, "capped": False, "long": False}
    got = eta.with_rework(p, 1000.0, (0.15, 0.5, 9), ceiling_at=1650.0)
    assert got["finish_at"] == 1650.0 and got["hi"] == 1650.0 and got["capped"] is True


def test_firm_needs_history_a_tight_band_and_a_step_inside_its_runs():
    assert eta.firmness(9, False, 20 * 60) == "firm"
    assert eta.firmness(3, False, 20 * 60) == "rough"
    assert eta.firmness(9, True, 20 * 60) == "rough"
    assert eta.firmness(9, False, 45 * 60) == "rough"


def test_finished_units_are_the_ones_that_delivered(tmp_path):
    conn = sqlite3.connect(tmp_path / "t.db")
    conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, codex_id TEXT, stage TEXT, unit TEXT,"
                 " step_id TEXT, event TEXT, run_id TEXT, event_ts TEXT)")
    rows = [("A", "ep01", "12", "completed"), ("A", "ep02", "11", "failed"), ("B", "ep01", "12", "completed")]
    conn.executemany("INSERT INTO events (codex_id, stage, unit, step_id, event) VALUES (?, 'episode', ?, ?, ?)", rows)
    assert eta.finished_units(conn) == {"A/ep01", "B/ep01"}


def test_the_norm_is_the_most_recent_finished_units(tmp_path):
    # 2026-10-18 measured: September's episodes carried 90-320 % rework, ep22-27 0-17 %
    conn = sqlite3.connect(tmp_path / "t.db")
    conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, codex_id TEXT, stage TEXT, unit TEXT,"
                 " step_id TEXT, event TEXT, run_id TEXT, event_ts TEXT)")
    rows = [("A", f"ep0{i}", "12", "completed", f"2026-10-0{i}T00:00:00Z") for i in range(1, 6)]
    conn.executemany("INSERT INTO events (codex_id, stage, unit, step_id, event, event_ts)"
                     " VALUES (?, 'episode', ?, ?, ?, ?)", rows)
    assert eta.finished_units(conn, last_n=2) == {"A/ep04", "A/ep05"}
