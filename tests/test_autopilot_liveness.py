"""P13 item 7, 9, 10: a quiet log is not liveness.  The watchdog kills a step only
when it ran past 1.5x its cap wall AND the run tree burned no CPU AND its outputs
stopped growing; the GPU ledger starts beside a drive; a runtime edit during a run
is an event, never a pause.  Every probe is a fake."""
from __future__ import annotations

import json

from studio import step_caps
from tests import autopilot_cli_fixtures as fx

STEP = "07"
LIMIT = max(1.5 * step_caps.step_wall_s(STEP), 20 * 60)


def _events(cli, book):
    return [r for r in cli.rows_of(book / "autopilot" / "events.jsonl")]


def _home(book, elapsed_s, started=True):
    home = book / "episodes" / "ep01"
    home.mkdir(parents=True, exist_ok=True)
    rows = [{"stage": "step_06", "seconds": 5.0}]
    if started:
        rows.append({"stage": f"step_{STEP}", "event": "started", "seconds": 0.0})
    (home / "timing.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (home / "attempts.json").write_text(json.dumps({f"wall.{STEP}": {"rounds": 0, "seconds": elapsed_s}}), encoding="utf-8")
    return home


def _setup(tmp_path, elapsed_s, cpu, out_age_s, started=True):
    cli, book = fx.load(), fx.book(tmp_path)
    _home(book, elapsed_s, started)
    clock = [1_000_000.0]
    live = cli.ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1")
    d = fx.deps(tmp_path, "RUNNING", procs=[live], now=lambda: clock[0])
    d.cpu_s = lambda rows, codex, n: cpu[0]
    d.outputs_at = lambda home: clock[0] - out_age_s
    return cli, book, d, clock


def _ticks(cli, book, d, clock, count=3):
    for i in range(count):
        cli.tick(book, fx.CODEX, d, i + 1)
        clock[0] += 400


def test_a_idle_cpu_step_past_1_5x_wall_is_killed_and_relaunched(tmp_path):
    cli, book, d, clock = _setup(tmp_path, LIMIT + 60, [100.0], out_age_s=3600)
    _ticks(cli, book, d, clock)
    assert "kill_run_tree" in d.engine.calls and len(d.calls["popen"]) == 1
    over = [r for r in _events(cli, book) if r["event"] == "step_overran"][0]
    assert over["step"] == STEP and over["elapsed_s"] > over["limit_s"]


def test_a_quiet_log_with_cpu_growth_is_not_killed(tmp_path):
    cpu = [100.0]
    cli, book, d, clock = _setup(tmp_path, LIMIT + 60, cpu, out_age_s=3600)
    for i in range(4):
        cpu[0] += 50.0
        cli.tick(book, fx.CODEX, d, i + 1)
        clock[0] += 400
    assert "kill_run_tree" not in d.engine.calls and d.calls["popen"] == []


def test_a_step_whose_outputs_still_grow_is_not_killed(tmp_path):
    cli, book, d, clock = _setup(tmp_path, LIMIT + 60, [100.0], out_age_s=120)
    _ticks(cli, book, d, clock)
    assert "kill_run_tree" not in d.engine.calls


def test_a_step_inside_its_limit_is_not_killed(tmp_path):
    cli, book, d, clock = _setup(tmp_path, LIMIT - 300, [100.0], out_age_s=3600)
    _ticks(cli, book, d, clock)
    assert "kill_run_tree" not in d.engine.calls


def test_a_closed_step_is_not_a_stuck_step(tmp_path):
    cli, book, d, clock = _setup(tmp_path, LIMIT + 60, [100.0], out_age_s=3600, started=False)
    _ticks(cli, book, d, clock)
    assert "kill_run_tree" not in d.engine.calls


def test_the_third_overrun_of_a_step_parks_the_episode(tmp_path):
    cli, book, d, clock = _setup(tmp_path, LIMIT + 60, [100.0], out_age_s=3600)
    for _ in range(3):
        cli.append_row(book / "autopilot" / "events.jsonl", {"event": "step_overran", "episode": 1, "step": STEP})
    _ticks(cli, book, d, clock)
    assert [r["reason"] for r in cli.rows_of(book / "autopilot" / "parked.jsonl")] == ["step_overran"]


def test_the_ledger_starts_beside_a_drive_once(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE", reason="launch")
    started = []
    d.ledger = lambda: started.append(1)
    cli.tick(book, fx.CODEX, d, 1)
    assert started == [1]


def test_a_runtime_edit_during_a_run_is_an_event_not_a_pause(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    live = cli.ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1")
    d = fx.deps(tmp_path, "RUNNING", procs=[live])
    d.root.mkdir(parents=True)
    (d.root / "gpu.lock").write_text(json.dumps({"episode": 1, "drive_pid": 777}), encoding="utf-8")
    d.git = lambda *a: " M studio/comfy.py\n?? tests/t.py\n" if a[0] == "status" else "abc123def\n"
    for i in (1, 2):
        cli.tick(book, fx.CODEX, d, i)
    rows = [r for r in _events(cli, book) if r["event"] == "code_dirty_during_run"]
    assert len(rows) == 1 and rows[0]["files"] == ["studio/comfy.py"]
    assert not cli.is_paused(book)


def test_a_silence_row_names_the_minutes_and_the_log():
    from scripts.episode import drive
    row = drive.silence_row("drive_run03.log", 20 * 60)
    assert row == {"event": "silent", "minutes": 20, "log": "drive_run03.log"}


def test_tree_cpu_sums_the_run_tree_only():
    from studio import engine_ops
    from studio.command_center.procs import ProcInfo
    rows = [ProcInfo(1, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1"),
            ProcInfo(2, 0.0, f"python episode.py {fx.CODEX} 1"), ProcInfo(3, 0.0, "notepad")]
    assert engine_ops.tree_cpu_s(rows, fx.CODEX, 1, cpu=lambda pid: float(pid) * 10) == 30.0


def test_newest_output_ignores_logs_ledgers_and_the_attempt_heartbeat(tmp_path):
    import os
    cli = fx.load()
    (tmp_path / "drive_run01.log").write_text("x", encoding="utf-8")
    (tmp_path / "attempts.json").write_text("{}", encoding="utf-8")
    (tmp_path / "timing.jsonl").write_text("", encoding="utf-8")
    sub = tmp_path / "takes"
    sub.mkdir()
    take = sub / "T01.mp4"
    take.write_bytes(b"x")
    os.utime(take, (500.0, 500.0))
    assert cli.newest_output(tmp_path) == 500.0
    assert cli.newest_output(tmp_path / "none") == 0.0
