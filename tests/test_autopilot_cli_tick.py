"""One tick is a pure function of disk, and it never ends in silence
(decision 2026-10-06 §Layer 1): after any tick, status.json names exactly one
of the six states, a second supervisor on the same box exits 0 without
touching a file, and the same tick twice changes nothing the first did not."""
from __future__ import annotations

import json
import re

import pytest

from tests import autopilot_cli_fixtures as fx

SIX = {"RUNNING", "BRAIN_RUNNING", "PARKED", "PUBLISHED", "PAUSED", "WAIT_TREE"}
DRIVE_LETTER = re.compile(r'"[A-Za-z]:(?:\\\\|/)')


def _status(book):
    return json.loads((book / "autopilot" / "status.json").read_text(encoding="utf-8"))


def test_tick_is_idempotent_and_the_second_instance_exits(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    live = cli.ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1")
    d = fx.deps(tmp_path, "IDLE", procs=[live])
    cli.tick(book, fx.CODEX, d, 1)
    cli.tick(book, fx.CODEX, d, 2)
    assert len(d.calls["popen"]) == 1, "the second tick found the live lock and launched nothing"
    first = _status(book)
    # a second supervisor: the lock names a live pid that is not ours
    (d.root / "supervisor.lock").write_text(json.dumps({"pid": 99}), encoding="utf-8")
    other = fx.deps(tmp_path, "IDLE", procs=[fx.load().ProcRow(99, 0.0, "python autopilot.py run")])
    other.pid = 1
    assert cli.run_loop(book, fx.CODEX, other, every=0, ticks=1) == 0
    assert other.calls["popen"] == [] and _status(book) == first


@pytest.mark.parametrize("state, expect", [
    ("IDLE", "RUNNING"), ("RUNNING", "RUNNING"), ("BRAIN_RUNNING", "BRAIN_RUNNING"),
    ("PARKED", "PARKED"), ("PUBLISHED", "PUBLISHED"), ("PAUSED", "PAUSED"),
    ("WAIT_TREE", "WAIT_TREE"), ("NEEDS_BRAIN", "PARKED"),
])
def test_no_silent_stop_cli(tmp_path, state, expect):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, state, reason="fixture")
    if state == "PAUSED":
        (book / "autopilot").mkdir(parents=True)
        (book / "autopilot" / "STOP").write_text("", encoding="utf-8")
    doc = cli.tick(book, fx.CODEX, d, 1)
    named = [s for s in SIX if s == doc["episode"]["state"]]
    assert named == [expect], doc["episode"]
    assert _status(book)["episode"]["state"] == expect


def test_status_json_is_written_atomically_with_relative_paths(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    cli.tick(book, fx.CODEX, d, 1)
    folder = book / "autopilot"
    assert sorted(p.name for p in folder.iterdir() if p.suffix == ".tmp") == [], "no half-written file left"
    for name in ("status.json", "events.jsonl", "series.json"):
        text = (folder / name).read_text(encoding="utf-8")
        assert not DRIVE_LETTER.search(text), f"{name} stores an absolute path"
        assert str(tmp_path) not in text
    doc = _status(book)
    assert set(doc) >= {"ts", "supervisor_pid", "heartbeat_age_s", "engine", "series", "episode", "last_events"}
    assert doc["series"]["next"] == 1 and doc["episode"]["n"] == 1


def test_write_atomic_replaces_the_file_in_one_step(tmp_path):
    cli = fx.load()
    path = tmp_path / "a" / "status.json"
    cli.write_atomic(path, {"k": 1})
    cli.write_atomic(path, {"k": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"k": 2}
    assert list(path.parent.iterdir()) == [path]


def test_a_complete_series_is_named_and_told_once(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    (book / "uploads.jsonl").write_text("".join(json.dumps({"episode": n, "privacy": "public", "video_id": f"v{n}"}) + "\n"
                                                for n in (1, 2, 3)), encoding="utf-8")
    for i in (1, 2):
        doc = cli.tick(book, fx.CODEX, d, i)
    assert doc["series"]["state"] == "complete" and doc["episode"]["state"] == "COMPLETE"
    assert len(d.calls["notify"]) == 1 and "3/3" in d.calls["notify"][0]


def test_the_heartbeat_names_the_tick_and_the_state(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "RUNNING")
    cli.tick(book, fx.CODEX, d, 7)
    beat = json.loads((d.root / "heartbeat.json").read_text(encoding="utf-8"))
    assert beat["tick"] == 7 and beat["state"] == "RUNNING" and beat["episode"] == 1


def test_a_dead_heartbeat_is_logged_once_by_the_adopting_instance(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "RUNNING")
    d.root.mkdir(parents=True)
    (d.root / "heartbeat.json").write_text(json.dumps({"ts": 1_000_000.0 - 1200, "tick": 3}), encoding="utf-8")
    cli.run_loop(book, fx.CODEX, d, every=0, ticks=1)
    events = [r["event"] for r in cli.rows_of(book / "autopilot" / "events.jsonl")]
    assert events.count("supervisor_died_at") == 1


def test_a_tick_that_raises_is_an_event_not_a_stop(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")

    def boom(signals, n):
        raise RuntimeError("derive broke at " + str(cli.ROOT / "studio" / "autopilot.py"))
    d.derive = boom
    assert cli.run_loop(book, fx.CODEX, d, every=0, ticks=2) == 0
    rows = [r for r in cli.rows_of(book / "autopilot" / "events.jsonl") if r["event"] == "tick_error"]
    assert len(rows) == 2 and str(cli.ROOT) not in rows[0]["error"] and "derive broke" in rows[0]["error"]
