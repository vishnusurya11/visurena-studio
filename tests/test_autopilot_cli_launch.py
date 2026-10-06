"""A launch is one detached drive.py and one lock, nothing else; a hung engine
is killed, restarted and the run relaunched at most twice per episode
(ops engineer §2, survival matrix)."""
from __future__ import annotations

import json
import os
import subprocess
import sys

from tests import autopilot_cli_fixtures as fx


def test_launch_spawns_only_drive_and_writes_the_lock(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    d.drive_argv = cli.drive_argv
    doc = cli.tick(book, fx.CODEX, d, 1)
    [(argv, kw)] = d.calls["popen"]
    assert argv == ["uv", "run", "--no-sync", "python", "scripts/episode/drive.py", fx.CODEX, "1"]
    assert kw["env"]["DRIVE_QUIET"] == "1" and kw["stderr"] == subprocess.STDOUT
    if sys.platform == "win32":
        assert kw["creationflags"] & subprocess.DETACHED_PROCESS
    lock = json.loads((d.root / "gpu.lock").read_text(encoding="utf-8"))
    assert lock == {"drive_pid": 777, "started": lock["started"], "book": fx.CODEX, "episode": 1}
    assert (book / "episodes" / "ep01" / "drive_launch01.log").exists()
    assert doc["episode"]["state"] == "RUNNING" and doc["episode"]["drive_pid"] == 777


def test_a_live_lock_blocks_a_second_launch_and_a_stale_one_is_cleared(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    live = fx.load().ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1")
    d = fx.deps(tmp_path, "IDLE", procs=[live])
    cli.tick(book, fx.CODEX, d, 1)
    cli.tick(book, fx.CODEX, d, 2)
    assert len(d.calls["popen"]) == 1
    gone = fx.deps(tmp_path, "IDLE", procs=[])           # the pid left the table
    cli.tick(book, fx.CODEX, gone, 3)
    events = [r["event"] for r in cli.rows_of(book / "autopilot" / "events.jsonl")]
    assert "stale_lock" in events and len(gone.calls["popen"]) == 1


def test_the_fake_drive_runs_detached_and_its_end_row_is_read(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    script = tmp_path / "fake_drive.py"
    script.write_text("import json, sys\n"
                      "from pathlib import Path\n"
                      "home = Path(sys.argv[1]); home.mkdir(parents=True, exist_ok=True)\n"
                      "with (home / 'drive.jsonl').open('a', encoding='utf-8') as f:\n"
                      "    for row in json.loads(sys.argv[2]):\n"
                      "        f.write(json.dumps(row) + '\\n')\n"
                      "sys.exit(int(sys.argv[3]))\n", encoding="utf-8")
    rows = [{"event": "start", "sha": "abc"}, {"event": "end", "code": 1, "sha": "abc"}]
    d = fx.deps(tmp_path, "IDLE")
    d.popen = subprocess.Popen
    d.drive_argv = lambda codex, n: [sys.executable, str(script), str(book / "episodes" / "ep01"), json.dumps(rows), "1"]
    cli.tick(book, fx.CODEX, d, 1)
    pid = json.loads((d.root / "gpu.lock").read_text(encoding="utf-8"))["drive_pid"]
    for _ in range(100):
        if (book / "episodes" / "ep01" / "drive.jsonl").exists():
            break
        __import__("time").sleep(0.1)
    signals = cli.gather(book, fx.CODEX, 1, d, {"paused": False})
    assert signals.exit_code == 1 and [r["event"] for r in signals.drive_rows] == ["start", "end"]
    assert isinstance(pid, int) and pid != os.getpid()


def test_a_hung_engine_is_killed_restarted_and_relaunched_at_most_twice(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    clock = [1_000_000.0]
    engine = fx.FakeEngine(up=True, prompt="prompt-1")
    live = fx.load().ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1")
    d = fx.deps(tmp_path, "RUNNING", procs=[live], engine=engine, now=lambda: clock[0])
    home = book / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive_run01.log").write_text("step 09\n", encoding="utf-8")
    os.utime(home / "drive_run01.log", (clock[0] - 2 * cli.HUNG_S, clock[0] - 2 * cli.HUNG_S))
    states = []
    for _ in range(4):                      # arm, hang 1, hang 2, hang 3
        states.append(cli.tick(book, fx.CODEX, d, 1)["episode"]["state"])
        clock[0] += cli.HUNG_S + 1
    assert len(d.calls["popen"]) == 2, "relaunched twice, never a third time"
    assert engine.calls.count("restart") == 3 and engine.calls.count("kill_run_tree") == 3
    assert states == ["RUNNING", "RUNNING", "RUNNING", "PARKED"]
    parked = cli.rows_of(book / "autopilot" / "parked.jsonl")
    assert [r["reason"] for r in parked] == ["engine"]


def test_an_engine_that_is_down_is_restarted_before_any_launch(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = fx.FakeEngine(up=False)
    d = fx.deps(tmp_path, "IDLE", engine=engine)
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert engine.calls.count("restart") == 1 and d.calls["popen"] == []
    assert doc["engine"]["up"] is False and doc["episode"]["state"] == "IDLE"


def test_running_id_reads_the_queue_in_any_of_its_shapes():
    cli = fx.load()
    assert cli.running_id({"queue_running": [[3, "p9", {}]]}) == "p9"
    assert cli.running_id({"queue_running": []}) is None
    assert cli.running_id(["p1"]) == "p1" and cli.running_id("p2") == "p2" and cli.running_id(None) is None


def test_quiet_seconds_reads_the_newest_run_log(tmp_path):
    cli = fx.load()
    home = tmp_path / "ep01"
    home.mkdir()
    assert cli.quiet_s(home, 10.0) is None
    (home / "drive_run01.log").write_text("x", encoding="utf-8")
    os.utime(home / "drive_run01.log", (100.0, 100.0))
    assert cli.quiet_s(home, 160.0) == 60.0
