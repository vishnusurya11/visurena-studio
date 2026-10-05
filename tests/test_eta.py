"""studio/eta.py (progress tracker spec §2): elapsed is a fact, the ETA is a
measured band.  Pure functions, `now` always passed in, no network, no GPU."""
from __future__ import annotations

import json
import sqlite3
from datetime import timedelta, timezone
from pathlib import Path

import pytest

from studio import eta

FIX = Path(__file__).resolve().parent / "fixtures" / "progress"


def _events_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, event_ts TEXT, codex_id TEXT, stage TEXT,"
                 " step_id TEXT, event TEXT, run_id TEXT, detail TEXT, unit TEXT, order_id INTEGER)")
    rows = json.loads((FIX / "events_extract.json").read_text(encoding="utf-8"))
    conn.executemany("INSERT INTO events (event_ts, step_id, event, run_id, unit, stage)"
                     " VALUES (?, ?, ?, ?, ?, 'episode')", rows)
    return conn


# --- band ---


def test_band_on_a_known_list():
    assert eta.band(list(range(1, 11))) == pytest.approx((1.9, 5.5, 9.1))


def test_band_of_one_value_is_that_value_and_of_none_is_zero():
    assert eta.band([42.0]) == (42.0, 42.0, 42.0)
    assert eta.band([]) == (0.0, 0.0, 0.0)


def test_fewer_than_five_runs_is_an_estimate():
    assert eta.confidence([1, 2, 3, 4]) == "estimate"
    assert eta.confidence([1, 2, 3, 4, 5]) == "measured"


# --- step history ---


def test_step_history_takes_only_same_run_pairs():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, event_ts TEXT, codex_id TEXT, stage TEXT,"
                 " step_id TEXT, event TEXT, run_id TEXT, detail TEXT, unit TEXT, order_id INTEGER)")
    rows = [("2026-10-01T00:00:00Z", "02", "started", "a", "ep01"),
            ("2026-10-01T00:10:00Z", "02", "completed", "a", "ep01"),
            ("2026-10-01T01:00:00Z", "03", "started", "a", "ep01"),
            ("2026-10-01T05:00:00Z", "03", "completed", "b", "ep01")]   # another run: no pair
    conn.executemany("INSERT INTO events (event_ts, step_id, event, run_id, unit, stage)"
                     " VALUES (?, ?, ?, ?, ?, 'episode')", rows)
    assert eta.step_history(conn) == {"02": [600.0]}


def test_step_history_keeps_the_last_eight_episodes():
    hist = eta.step_history(_events_db(), last_n_episodes=8)
    assert set(hist) >= {"02", "08", "09", "11"}
    few = eta.step_history(_events_db(), last_n_episodes=1)
    assert sum(len(v) for v in few.values()) < sum(len(v) for v in hist.values())


def test_the_measured_shoot_median_matches_the_spec_table():
    hist = eta.step_history(_events_db(), last_n_episodes=8)
    assert 3000 < eta.band(hist["09"])[1] < 4500


# --- takes ---


def test_a_take_prior_is_fixed_plus_frames_and_cold_once():
    assert eta.take_prior(192) == pytest.approx(60 + 1.2 * 192)
    assert eta.take_prior(192, cold=True) == pytest.approx(300 + 60 + 1.2 * 192)


def test_the_pace_is_seeded_at_three_quarters():
    left = eta.take_remaining(done=[], remaining=[192, 192], cold_paid=False)
    assert left["r"] == pytest.approx(0.75) and left["basis"] == "norm"
    assert left["secs"] == pytest.approx(0.75 * (eta.take_prior(192, cold=True) + eta.take_prior(192)))


def test_the_pace_moves_to_the_ewma_after_three_items():
    p = eta.take_prior(100)
    two = eta.take_remaining(done=[(p, 100), (p, 100)], remaining=[100], cold_paid=True)
    assert two["basis"] == "norm"
    three = eta.take_remaining(done=[(p, 100)] * 3, remaining=[100], cold_paid=True)
    expected = 0.75
    for _ in range(3):
        expected = 0.3 * 1.0 + 0.7 * expected
    assert three["basis"] == "measured" and three["r"] == pytest.approx(expected)


def test_an_overrunning_take_pulls_the_pace_up_before_it_lands():
    p = eta.take_prior(100)
    calm = eta.take_remaining(done=[], remaining=[100, 100], cold_paid=True, inflight_s=0.0)
    late = eta.take_remaining(done=[], remaining=[100, 100], cold_paid=True, inflight_s=2 * p)
    assert late["r"] > calm["r"]


def _replay_ep16() -> list[tuple[float, int]]:
    shots = json.loads((FIX / "ep16_shots.json").read_text(encoding="utf-8"))
    return [(row["render_s"], row["frames"]) for row in shots]


def test_replaying_ep16_the_finish_never_rises_when_a_take_lands():
    takes = _replay_ep16()
    t = 0.0
    for i, (secs, frames) in enumerate(takes):
        t += secs
        rest = [f for _, f in takes[i + 1:]]
        before = t + eta.take_remaining(takes[:i], [frames] + rest, cold_paid=True, inflight_s=secs)["secs"]
        after = t + eta.take_remaining(takes[:i + 1], rest, cold_paid=True)["secs"]
        assert after <= before + 1e-6, (i, before, after)


# --- loops ---


def test_remaining_unknown_is_the_median_of_what_is_left():
    assert eta.remaining_unknown(100, [50, 200, 300, 400]) == pytest.approx(200)


def test_remaining_unknown_is_none_past_p90():
    assert eta.remaining_unknown(10_000, [100, 200, 300, 400, 500]) is None


# --- the episode ---


def test_the_episode_band_is_capped_at_the_ceiling():
    out = eta.episode_eta(now=1000.0, running_left=600.0, running_sigma=60.0,
                          later=[[100, 200, 300, 4000, 9000]] * 3, ceiling_at=3000.0)
    assert out["hi"] <= 3000.0 and out["capped"] is True
    assert out["lo"] <= out["finish_at"]


def test_a_long_running_step_has_no_finish():
    out = eta.episode_eta(now=1000.0, running_left=None, running_sigma=0.0, later=[[10]], ceiling_at=99999.0)
    assert out["long"] is True and out["finish_at"] is None


def test_the_finish_rounds_to_five_minutes():
    assert eta.round_to(300.0 * 7 + 149) == 300.0 * 7
    assert eta.round_to(300.0 * 7 + 151) == 300.0 * 8


def test_mixed_utc_and_naive_local_stamps_normalise():
    utc = eta.to_epoch("2026-10-05T00:43:47Z")
    pdt = timezone(timedelta(hours=-7))
    local = eta.to_epoch("2026-10-04T17:43:47", tz=pdt)
    offset = eta.to_epoch("2026-10-05T00:43:47+00:00")
    assert utc == local == offset
    assert eta.to_epoch("junk") is None


def test_timing_rows_give_a_measured_checks_tail():
    rows = [json.loads(line) for line in (FIX / "ep16_timing.jsonl").read_text(encoding="utf-8").splitlines()]
    tail = eta.sub_norm([rows], ("take_dq", "take_content", "strip", "take_eye"))
    assert 100 < tail < 2000


def test_timing_rows_fold_into_step_norms_per_episode():
    rows = [{"stage": "takes", "seconds": 100}, {"stage": "take_dq", "seconds": 50},
            {"stage": "qc", "seconds": 7}, {"stage": "unknown", "seconds": 9}]
    assert eta.timing_history([rows, rows]) == {"09": [150.0, 150.0], "11": [7.0, 7.0]}
