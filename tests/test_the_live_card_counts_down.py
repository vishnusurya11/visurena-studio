"""The live card counts DOWN (owner 2026-10-18, Jekyll ep01's card: "episode done
is a shit way .. I don't know .. time left ... also display time on finished
events"): the headline is the time left, every time reads Seattle 12-hour, each
finished step says how long it took and when it ended in THIS make, a step no run
of this make finished never says `kept`, and the episode clock reads against the
owner's 6 h.  $0: a tmp library, no process table, no network."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from command_center_fixtures import CODEX
from studio.command_center import progress_view as pv
from test_progress_card_api import _drive, board  # noqa: F401  (the fixture)


def _utc(*a) -> float:
    return datetime(*a, tzinfo=timezone.utc).timestamp()


# --- Seattle, 12-hour ---


def test_the_pacific_offset_follows_us_daylight_time():
    assert pv.pacific_offset(_utc(2026, 10, 19, 1, 45)) == -7          # 18 Oct, PDT
    assert pv.pacific_offset(_utc(2026, 12, 2, 2, 45)) == -8           # 1 Dec, PST
    assert pv.pacific_offset(_utc(2026, 3, 8, 9, 59)) == -8            # 01:59 PST, the spring jump
    assert pv.pacific_offset(_utc(2026, 3, 8, 10, 0)) == -7
    assert pv.pacific_offset(_utc(2026, 11, 1, 8, 59)) == -7           # 01:59 PDT, the fall back
    assert pv.pacific_offset(_utc(2026, 11, 1, 9, 0)) == -8


def test_a_clock_reads_seattle_twelve_hour():
    assert pv.clock(_utc(2026, 10, 19, 1, 45)) == "6:45 pm"
    assert pv.clock(_utc(2026, 10, 18, 7, 5)) == "12:05 am"
    assert pv.clock(_utc(2026, 10, 18, 19, 0)) == "12:00 pm"
    assert pv.clock(None) == ""


def test_a_range_names_its_half_of_the_day_once():
    assert pv.clock_range(_utc(2026, 10, 19, 1, 15), _utc(2026, 10, 19, 2, 15)) == "6:15–7:15 pm"
    assert pv.clock_range(_utc(2026, 10, 18, 18, 45), _utc(2026, 10, 18, 19, 15)) == "11:45 am–12:15 pm"


# --- the time left ---


def test_the_time_left_reads_hours_and_minutes():
    assert pv.left_words(3 * 3600 + 5 * 60 + 20) == "3h 05m"
    assert pv.left_words(42 * 60) == "42m"
    assert pv.left_words(20) == "<1m"
    assert pv.left_words(None) == ""


def test_the_range_line_joins_the_range_the_steps_and_the_runs():
    e = {"range": "6:15–7:15 pm", "finish": "6:45 pm", "steps_left": 7, "n_runs": 9, "basis": "measured"}
    assert pv.range_words(e) == "range 6:15–7:15 pm · 7 steps to run · 9 runs · measured"
    assert pv.range_words({**e, "long": True, "steps_left": 1}) == "1 step to run · 9 runs · measured"
    assert pv.range_words({}) == ""


def test_the_time_left_counts_to_the_unrounded_finish():
    assert pv.with_left({"finish_raw": 1000.0 + 3 * 3600 + 5 * 60}, now=1000.0)["left"] == "3h 05m"
    assert "left" not in pv.with_left({}, now=1000.0)


# --- this make's finished steps (timing.jsonl) ---


ROWS = [
    {"stage": "step_02", "started": "2026-10-18T15:00:06", "ended": "2026-10-18T15:00:06", "event": "started"},
    {"stage": "plan", "started": "2026-10-18T15:00:06", "ended": "2026-10-18T15:28:42"},
    {"stage": "step_02", "started": "2026-10-18T15:40:06", "ended": "2026-10-18T15:40:06", "event": "started"},
    {"stage": "plan", "started": "2026-10-18T15:40:06", "ended": "2026-10-18T15:50:46"},
    {"stage": "step_03", "started": "2026-10-18T15:50:47", "ended": "2026-10-18T15:50:47", "event": "started"},
    {"stage": "places", "started": "2026-10-18T15:50:47", "ended": "2026-10-18T15:55:04"},
]


def _t(stamp: str) -> float:
    return datetime.fromisoformat(stamp).timestamp()


def test_each_step_of_the_make_sums_its_spans_and_keeps_its_last_end():
    got = pv.make_steps(ROWS, since=_t("2026-10-18T15:00:00"))
    assert round(got["02"]["secs"]) == 1716 + 640
    assert got["02"]["end"] == _t("2026-10-18T15:50:46")
    assert round(got["03"]["secs"]) == 257


def test_rows_before_the_make_are_not_its_steps():
    assert "02" not in pv.make_steps(ROWS, since=_t("2026-10-18T15:50:00"))


def test_the_make_is_the_runs_on_its_clock(tmp_path):
    (tmp_path / "clock.jsonl").write_text(json.dumps({"run_id": "r1", "started": 100.0, "ended": 200.0}) + "\n")
    (tmp_path / "clock.open.json").write_text(json.dumps({"run_id": "r2", "started": 300.0, "last_beat": 350.0}))
    assert pv.make_runs(tmp_path, "r3") == {"r1", "r2", "r3"}
    assert pv.make_start(tmp_path, 300.0) == 100.0


def test_a_step_only_an_earlier_make_finished_is_not_kept():
    rows = [{"run_id": "old", "step_id": "07", "event": "completed"},
            {"run_id": "r1", "step_id": "03", "event": "skipped"}]
    assert pv.kept_steps(rows, {"r1", "r2"}) == {"03"}


def test_a_finished_step_reads_its_duration_and_seattle_end():
    s = {"state": "skip", "made": {"secs": 3000.0, "end": _utc(2026, 10, 18, 22, 52)}}
    assert pv.finished_words(s) == "50m · 3:52 pm"
    assert pv.finished_words({"state": "waiting"}) == ""


def test_a_step_kept_from_this_make_reads_its_make_time():
    s = {"state": "waiting", "window": "kept", "made": {"secs": 1080.0, "end": _utc(2026, 10, 18, 23, 45)}}
    assert pv.finished_words(s) == "18m · 4:45 pm"


def test_a_skipped_step_ends_at_its_skip():
    rows = [{"run_id": "r", "step_id": "01", "event": "skipped", "event_ts": 100.0}]
    assert pv._pair(rows, "r", "01") == (None, 100.0)
    assert pv.with_made([{"id": "01", "state": "skip", "end": 100.0}], {})[0]["fin"].startswith("<1m · ")


def test_a_later_step_reads_its_projected_minutes_or_kept_or_a_dash():
    assert pv.window_words({"will_run": True, "start_at": 0.0, "end_at": 18 * 60.0}) == "~18m"
    assert pv.window_words({"will_run": False}) == "kept"
    assert pv.window_words({"will_run": True, "start_at": None, "end_at": None}) == "—"


# --- the page ---


def _card(board) -> str:
    board["app"].state.procs = lambda: _drive(time.time() - 3600)
    html = TestClient(board["app"]).get(f"/d/episode/{CODEX}/ep04").text
    start = html.index('<section id="live"')
    return html[start:html.index("</section>", start)]


def test_the_headline_is_the_time_left(board):
    card = _card(board)
    big = re.search(r'class="lv-big">(.*?)</div>', card, re.S).group(1)
    assert re.search(r'data-k="left">(\d+h \d\dm|\d+m|<1m)</span>', big.replace("&lt;", "<")) and "left" in big
    assert re.search(r'data-k="finish">done ~<b>\d{1,2}:\d\d [ap]m</b>', card)
    assert "episode done ~" not in card                  # the old headline


def test_the_episode_clock_reads_against_the_owners_six_hours(board):
    assert re.search(r"episode clock .*? of 6h", _card(board), re.S)


def test_a_finished_step_on_the_rail_says_how_long_and_when(board):
    card = _card(board)
    fins = re.findall(r'<span class="fin">([^<]*)</span>', card)
    assert fins and all(re.fullmatch(r"(\d+h\d\d|\d+m|\d+s|&lt;1m) · \d{1,2}:\d\d [ap]m", f) for f in fins), fins
