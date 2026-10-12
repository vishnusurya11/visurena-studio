"""Board review 2026-10-12 (02 #4, 03 A22): the GPU card said "GPU idle · nothing
running" while ComfyUI ran a prompt for a peer's looks_table.py, and Home never
said the WotW autopilot was paused ("two parked in a row: ep22, ep23").

The card reads ComfyUI's /queue (read-only, cached, refreshed off the request so a
page never waits on it) and names the process holding it; Home and the card say
what the autopilot is doing.  No test reaches ComfyUI: the fetch is injected.  $0."""
from __future__ import annotations

import json

from studio.command_center import comfy_tap, views
from studio.command_center.procs import ProcInfo

QUEUE = {"queue_running": [[226, "p-226", {}, {}, []]], "queue_pending": [[227, "p-227"]]}


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def test_the_queue_doc_is_read_into_a_snapshot():
    assert comfy_tap.parse(QUEUE) == {"up": True, "running": [226], "pending": 1}
    assert comfy_tap.parse({}) == {"up": True, "running": [], "pending": 0}


def test_the_tap_answers_from_its_cache_and_refreshes_after_the_ttl():
    calls, clock = [], Clock()
    tap = comfy_tap.Tap(fetch=lambda: calls.append(1) or QUEUE, ttl=5.0, clock=clock, spawn=lambda fn: fn())
    assert tap.read()["running"] == [226] and len(calls) == 1
    tap.read()
    assert len(calls) == 1
    clock.t += 6
    tap.read()
    assert len(calls) == 2


def test_a_refresh_in_flight_answers_the_last_snapshot_at_once():
    pending = []
    tap = comfy_tap.Tap(fetch=lambda: QUEUE, ttl=5.0, clock=Clock(), spawn=pending.append)
    assert tap.read() == comfy_tap.DOWN and len(pending) == 1
    tap.read()
    assert len(pending) == 1                     # single flight
    pending[0]()
    assert tap.read()["running"] == [226]


def test_an_engine_that_cannot_be_reached_reads_down():
    def boom():
        raise OSError("refused")
    tap = comfy_tap.Tap(fetch=boom, ttl=5.0, clock=Clock(), spawn=lambda fn: fn())
    assert tap.read() == comfy_tap.DOWN


def test_the_holder_is_the_script_naming_a_book():
    rows = [ProcInfo(1, 10.0, "python ComfyUI/main.py --windows-standalone-build"),
            ProcInfo(2, 20.0, "uv run python command_center.py"),
            ProcInfo(3, 30.0, "python scripts/refs/looks_table.py 20260827135504 gabriel_john_utterson")]
    assert comfy_tap.holder(rows, {"20260827135504": "Jekyll"}) == "refs/looks_table.py · Jekyll"
    assert comfy_tap.holder(rows[:2], {}) == ""


def test_the_engine_block_says_busy_only_when_a_prompt_runs():
    rows = [ProcInfo(3, 30.0, "python scripts/refs/looks_table.py 20260827135504")]
    busy = comfy_tap.engine_block(comfy_tap.parse(QUEUE), rows, {"20260827135504": "Jekyll"})
    assert busy == {"busy": True, "running": 1, "pending": 1, "who": "refs/looks_table.py · Jekyll"}
    assert comfy_tap.engine_block(comfy_tap.parse({}), rows, {})["busy"] is False
    assert comfy_tap.engine_block(comfy_tap.DOWN, rows, {}) is None


# --- the autopilot ---


def _autopilot(tmp_path, series, status):
    folder = tmp_path / "20260827135508_the-war-of-the-worlds" / "autopilot"
    folder.mkdir(parents=True)
    (folder / "series.json").write_text(json.dumps(series), encoding="utf-8")
    (folder / "status.json").write_text(json.dumps(status), encoding="utf-8")
    return tmp_path


def test_a_paused_series_says_paused_and_why(tmp_path):
    lib = _autopilot(tmp_path, {"book": "20260827135508", "paused": True, "paused_why": "two parked in a row: ep22, ep23"},
                     {"ts": "2026-10-12T15:00:00+00:00", "episode": {"n": 22, "state": "PARKED"}})
    got = views.autopilot_lines(lib, {"20260827135508": "The War of the Worlds"})
    assert got[0]["state"] == "paused" and got[0]["why"] == "two parked in a row: ep22, ep23"
    assert got[0]["book"] == "The War of the Worlds"


def test_a_complete_series_still_carrying_the_pause_says_both(tmp_path):
    lib = _autopilot(tmp_path, {"book": "20260827135508", "paused": True, "paused_why": "two parked in a row: ep22, ep23"},
                     {"ts": "2026-10-12T15:00:00+00:00", "episode": {"n": None, "state": "COMPLETE"}})
    line = views.autopilot_lines(lib, {})[0]
    assert line["state"] == "complete" and "still paused" in line["why"] and "ep22" in line["why"]


def test_a_library_without_an_autopilot_has_no_line(tmp_path):
    (tmp_path / "20260827135504_jekyll").mkdir()
    assert views.autopilot_lines(tmp_path, {}) == []


# --- the board, end to end over the fixtures ---


def _board(tmp_path, monkeypatch, queue):
    import sqlite3

    from fastapi.testclient import TestClient

    from command_center_fixtures import make_app
    from studio import db
    app = make_app(tmp_path, monkeypatch)
    conn = sqlite3.connect(tmp_path / "t.db")                  # nothing runs: the floor is idle
    conn.execute("UPDATE work_orders SET state = 'queued' WHERE state = 'running'")
    conn.commit()
    conn.close()
    app.state.engine = comfy_tap.Tap(fetch=lambda: queue, spawn=lambda fn: fn())
    app.state.procs = lambda: [ProcInfo(9, 1.0, "python scripts/refs/looks_table.py 20260901000002 x")]
    _autopilot(tmp_path / "library", {"book": "20260901000001", "paused": True,
                                      "paused_why": "two parked in a row: ep22, ep23"},
               {"ts": "2026-10-12T15:00:00+00:00", "episode": {"n": 22, "state": "PARKED"}})
    assert db  # the fixture module seeds through studio.db
    return TestClient(app)


def test_the_card_says_the_gpu_is_busy_outside_the_runner(tmp_path, monkeypatch):
    c = _board(tmp_path, monkeypatch, QUEUE)
    html = c.get("/").text
    assert "GPU busy outside the runner" in html and "refs/looks_table.py · Other Book" in html
    shell = c.get("/api/pulse.json").json()["shell"]
    assert shell["engine"]["busy"] is True and shell["engine"]["who"] == "refs/looks_table.py · Other Book"


def test_an_idle_engine_leaves_the_card_idle(tmp_path, monkeypatch):
    c = _board(tmp_path, monkeypatch, {"queue_running": [], "queue_pending": []})
    assert "GPU busy outside the runner" not in c.get("/").text


def test_home_and_the_card_say_the_autopilot_is_paused(tmp_path, monkeypatch):
    c = _board(tmp_path, monkeypatch, {"queue_running": [], "queue_pending": []})
    html = c.get("/").text
    assert "Autopilot" in html and "paused" in html and "two parked in a row: ep22, ep23" in html
    lines = c.get("/api/pulse.json").json()["shell"]["autopilot"]
    assert lines[0]["state"] == "paused" and lines[0]["book"] == "A Book"
