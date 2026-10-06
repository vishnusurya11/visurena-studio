"""The series driver and the status contract (ops engineer §4-§5): the next
unit is the lowest chapter with no public upload and no parked row, and
status.json carries the keys the CLI, the board and the owner read, with
no absolute path inside (the books move between drives; a status that names
D:\\ is wrong on the next box)."""
from __future__ import annotations

import json
import re
from dataclasses import replace

from studio import autopilot as ap
from studio.autopilot import Derived, Signals, State

PUBLIC = [{"episode": n, "privacy": "public", "video_id": "v"} for n in range(1, 19)]
PRIVATE = [{"episode": 19, "privacy": "private", "video_id": "v"}]
PARKED = [{"episode": 19, "reason": "over_budget", "ts": "2026-10-06T15:00:00+00:00"}]


def test_next_unit_skips_published_and_parked_and_completes_at_the_book_end():
    chapters = list(range(1, 28))
    assert ap.next_unit(chapters, PUBLIC, [], 27) == 19
    assert ap.next_unit(chapters, PUBLIC + PRIVATE, [], 27) == 19
    assert ap.next_unit(chapters, PUBLIC, PARKED, 27) == 20
    assert ap.next_unit([1, 2, 3], PUBLIC, [], None) is None
    assert ap.next_unit(chapters, PUBLIC, PARKED, 19) is None
    assert ap.next_unit([3, 1, 2], [], [], None) == 1


def signals() -> Signals:
    return Signals(drive_rows=[{"event": "start", "sha": "2a50fc4f5a73943bf9211f999e66accade6260d3"},
                               {"event": "run", "n": 1, "sha": "2a50fc4f", "outcome": "refused", "step": "09"}],
                   exit_code=None, lock={"drive_pid": 5678, "started": 1.0, "book": "b", "episode": 20},
                   proc_alive=True, uploads_rows=PUBLIC, parked_rows=PARKED, home_files={"plan.json"},
                   log_tail='  File "D:\\Projects\\x\\studio\\llm.py", line 1\nstep 09 renders', porcelain="",
                   engine_up=True, clock_spent_s=3120.0, brain_attempts=0, brain_verdict=None, paused=False,
                   head_sha="2a50fc4f5a73943bf9211f999e66accade6260d3", media_spent_usd=1.42)


SERIES = {"book": "20260827135508", "first": 1, "last": 27, "published": list(range(1, 19)),
          "parked": PARKED, "next": 20, "state": "running", "supervisor_pid": 1234,
          "heartbeat_age_s": 12, "queue_running": 1, "restarts_today": 0,
          "last_events": [{"ts": "t", "event": "launch", "episode": 20, "home": "episodes/ep20"}]}


def test_status_has_the_contract_keys():
    derived = Derived(State.RUNNING, "drive alive", None, {"episode": "ep20"})
    doc = ap.status(derived, signals(), SERIES, now="2026-10-06T15:00:00+00:00")
    assert set(doc) == {"ts", "supervisor_pid", "heartbeat_age_s", "engine", "series", "episode", "last_events"}
    assert doc["engine"] == {"up": True, "queue_running": 1, "restarts_today": 0}
    assert set(doc["series"]) == {"book", "first", "last", "published", "parked", "next", "state"}
    assert set(doc["episode"]) >= {"n", "state", "drive_pid", "sha", "run", "step", "clock_spent_s",
                                   "media_spent_usd", "brain_attempts", "reason"}
    assert (doc["episode"]["n"], doc["episode"]["state"], doc["episode"]["sha"]) == (20, "RUNNING", "2a50fc4f")
    assert doc["ts"] == "2026-10-06T15:00:00+00:00" and doc["supervisor_pid"] == 1234


def test_no_absolute_path_in_status():
    """The log tail carries drive letters; the packet and the status may not."""
    derived = ap.derive(replace(signals(), proc_alive=False), 20)
    doc = ap.status(derived, signals(), SERIES)
    text = json.dumps(doc) + json.dumps(derived.packet)
    assert not re.search(r"[A-Za-z]:\\\\|/Users/|/home/", text), text
    assert "ts" in doc and doc["ts"]


def test_jsonl_and_atomic_json_round_trip(tmp_path):
    path = tmp_path / "drive.jsonl"
    path.write_text('{"event": "start"}\n\nnot json\n{"event": "end", "code": 0}\n', encoding="utf-8")
    assert ap.read_jsonl(path) == [{"event": "start"}, {"event": "end", "code": 0}]
    assert ap.read_jsonl(tmp_path / "missing.jsonl") == []
    out = tmp_path / "deep" / "status.json"
    ap.write_json_atomic(out, {"a": 1})
    ap.write_json_atomic(out, {"a": 2})
    assert json.loads(out.read_text(encoding="utf-8")) == {"a": 2}
    assert sorted(p.name for p in out.parent.iterdir()) == ["status.json"]
