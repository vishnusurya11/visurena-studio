"""P13: ComfyUI health (a dead engine restarted after two missed ticks in any
state, low host commit freed, no hard recycle under a live drive), auto-unpark
and the successor handover.  Fakes only; nothing spawns or spends."""
from __future__ import annotations

import json

from studio import engine_ops
from tests import autopilot_cli_fixtures as fx


class HealthEngine(fx.FakeEngine):
    """The fixture's engine plus the P13 probes; commit is a list consumed per read."""

    def __init__(self, up=True, commits=(32.0,), prompt=None):
        super().__init__(up=up, prompt=prompt)
        self.commits = list(commits)

    def commit_free_gb(self):
        self.calls.append("commit")
        return self.commits.pop(0) if len(self.commits) > 1 else self.commits[0]

    def free(self, base_url):
        self.calls.append("free")
        return True

    def log_tail(self, n=3):
        return ["boom 1", "boom 2", "boom 3"][-n:]


def _events(cli, book):
    return cli.rows_of(book / "autopilot" / "events.jsonl")


def _live(cli):
    return cli.ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1")


# ---- engine_ops ------------------------------------------------------------------

def test_commit_free_gb_reads_the_available_page_file():
    stat = lambda: {"ullAvailPageFile": 8 * 2**30, "ullAvailPhys": 1}
    assert engine_ops.commit_free_gb(stat) == 8.0


def test_free_posts_to_the_engine_and_says_whether_it_answered():
    seen = []
    assert engine_ops.free("http://x", post=lambda url, body: seen.append((url, body)) or True) is True
    assert seen[0][0] == "http://x/free" and seen[0][1]["free_memory"] is True

    def broken(url, body):
        raise OSError("down")
    assert engine_ops.free("http://x", post=broken) is False


def test_log_tail_returns_the_last_lines_and_survives_a_missing_log(tmp_path):
    log = tmp_path / "ComfyUI" / "user" / "comfyui.log"
    log.parent.mkdir(parents=True)
    log.write_text("a\nb\nc\nd\n", encoding="utf-8")
    assert engine_ops.log_tail(3, root=tmp_path) == ["b", "c", "d"]
    assert engine_ops.log_tail(3, root=tmp_path / "none") == []


# ---- engine down -----------------------------------------------------------------

def test_one_missed_poll_does_not_restart(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(up=False)
    d = fx.deps(tmp_path, "RUNNING", procs=[_live(cli)], engine=engine)
    cli.tick(book, fx.CODEX, d, 1)
    assert "restart" not in engine.calls
    engine.up = True
    cli.tick(book, fx.CODEX, d, 2)
    engine.up = False
    cli.tick(book, fx.CODEX, d, 3)
    assert "restart" not in engine.calls, "the counter reset on the tick it answered"


def test_a_dead_engine_is_restarted_after_two_ticks_in_any_state(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(up=False)
    d = fx.deps(tmp_path, "RUNNING", procs=[_live(cli)], engine=engine)
    cli.tick(book, fx.CODEX, d, 1)
    cli.tick(book, fx.CODEX, d, 2)
    assert engine.calls.count("restart") == 1
    down = [r for r in _events(cli, book) if r["event"] == "engine_down"][0]
    assert down["log"] == ["boom 1", "boom 2", "boom 3"] and down["commit_free_gb"] == 32.0


def test_a_paused_series_never_restarts_a_dead_engine(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(up=False)
    d = fx.deps(tmp_path, "PAUSED", reason="paused", engine=engine)
    for i in (1, 2, 3):
        cli.tick(book, fx.CODEX, d, i)
    assert "restart" not in engine.calls


# ---- host commit -----------------------------------------------------------------

def test_low_commit_with_empty_queue_posts_free(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(commits=(0.8, 9.0))
    d = fx.deps(tmp_path, "RUNNING", procs=[_live(cli)], engine=engine)
    cli.tick(book, fx.CODEX, d, 1)
    assert "free" in engine.calls and "restart" not in engine.calls
    low = [r for r in _events(cli, book) if r["event"] == "commit_low"][0]
    assert (low["before_gb"], low["after_gb"]) == (0.8, 9.0)


def test_low_commit_with_a_busy_queue_is_left_alone(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(commits=(0.8,), prompt="p1")
    d = fx.deps(tmp_path, "RUNNING", procs=[_live(cli)], engine=engine)
    cli.tick(book, fx.CODEX, d, 1)
    assert "free" not in engine.calls


def test_hard_recycle_never_while_a_drive_is_alive(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(commits=(0.5,))
    d = fx.deps(tmp_path, "RUNNING", procs=[_live(cli)], engine=engine)
    cli.tick(book, fx.CODEX, d, 1)
    assert "free" in engine.calls and "restart" not in engine.calls and "kill_engine" not in engine.calls


def test_a_stuck_low_commit_is_recycled_between_drives(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(commits=(0.5,))
    d = fx.deps(tmp_path, "WAIT_TREE", reason="tree_dirty", engine=engine)
    cli.tick(book, fx.CODEX, d, 1)
    assert "kill_engine" in engine.calls and "restart" in engine.calls
    assert "engine_recycled" in [r["event"] for r in _events(cli, book)]


# ---- auto-unpark -----------------------------------------------------------------

def _park(cli, book, n=1, reason="brain: qc fail", sha="aaaa1111"):
    cli.append_row(book / "autopilot" / "parked.jsonl",
                   {"ts": "t", "episode": n, "sha": sha, "reason": reason, "evidence": {}})


def _git_changed(files):
    return lambda *a: "" if a[0] == "status" else ("\n".join(files) if a[0] == "diff" else "bbbb2222\n")


def test_a_brain_park_clears_only_when_runtime_files_changed_since_its_sha(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    _park(cli, book)
    d.git = _git_changed(["docs/x.md", "tests/test_a.py"])
    assert cli.auto_unpark(book, d) == []
    d.git = _git_changed(["docs/x.md", "studio/judged_gate.py"])
    assert cli.auto_unpark(book, d) == [1]
    assert cli.rows_of(book / "autopilot" / "parked.jsonl") == []
    assert "auto_unpark" in [r["event"] for r in _events(cli, book)]


def test_step_cap_park_never_auto_clears(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    d.git = _git_changed(["studio/x.py"])
    for reason in ("step_cap", "over_budget", "safety: x", "youtube_token_expired: y", "clock_loop", "brain_exhausted"):
        _park(cli, book, reason=reason)
    assert cli.auto_unpark(book, d) == []


def test_auto_unpark_capped_at_two(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    d.git = _git_changed(["studio/x.py"])
    for _ in range(3):
        _park(cli, book)
        cli.auto_unpark(book, d)
    assert len(cli.rows_of(book / "autopilot" / "parked.jsonl")) == 1
    assert [r["event"] for r in _events(cli, book)].count("auto_unpark") == 2


def test_an_unparked_episode_queues_behind_a_unit_holding_the_gpu(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    other = cli.ProcRow(900, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 2")
    d = fx.deps(tmp_path, "IDLE", reason="launch", procs=[other])
    d.root.mkdir(parents=True)
    (d.root / "gpu.lock").write_text(json.dumps({"episode": 2, "drive_pid": 900}), encoding="utf-8")
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert d.calls["popen"] == [] and doc["episode"]["action"] == "wait"


# ---- handover --------------------------------------------------------------------

def test_code_moved_spawns_the_successor_after_releasing_the_claim(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "PAUSED", reason="paused")
    order = []
    d.popen = lambda argv, **kw: order.append(("popen", (d.root / "supervisor.lock").exists(), argv)) or fx.FakeProc(55)
    heads = iter(["aaa\n", "aaa\n", "bbb\n", "bbb\n", "bbb\n", "bbb\n"])
    d.git = lambda *a: "" if a[0] == "status" else next(heads)
    assert cli.run_loop(book, fx.CODEX, d, every=0, ticks=5) == 0
    assert len(order) == 1 and order[0][1] is False, "the claim was released before the spawn"
    assert "autopilot.py" in " ".join(order[0][2]) and "run" in order[0][2]


def test_successor_spawn_is_once_per_head(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    assert cli.spawn_successor(book, fx.CODEX, d, "bbbb", 30) is True
    assert cli.spawn_successor(book, fx.CODEX, d, "bbbb", 30) is False
    assert cli.spawn_successor(book, fx.CODEX, d, "cccc", 30) is True
    assert len(d.calls["popen"]) == 2


# ---- a restarted engine is let boot (2026-10-29) ------------------------------------

def test_a_restarted_engine_is_let_boot_before_another_restart(tmp_path):
    """After the Windows Update reboot ComfyUI took over a minute to answer; act_idle restarted it
    every tick and watch_engine every two, killing each boot.  One restart, then BOOT_GRACE_S."""
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(up=False)
    clock = [1_000_000.0]
    d = fx.deps(tmp_path, "IDLE", engine=engine, now=lambda: clock[0])
    for _ in range(4):
        cli.tick(book, fx.CODEX, d, 1)
        clock[0] += 30
    assert engine.calls.count("restart") == 1
    clock[0] += cli.BOOT_GRACE_S
    cli.tick(book, fx.CODEX, d, 1)
    assert engine.calls.count("restart") == 2


def test_a_running_units_engine_is_let_boot_too(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    engine = HealthEngine(up=False)
    clock = [1_000_000.0]
    d = fx.deps(tmp_path, "RUNNING", procs=[_live(cli)], engine=engine, now=lambda: clock[0])
    for i in range(1, 7):
        cli.tick(book, fx.CODEX, d, i)
        clock[0] += 30
    assert engine.calls.count("restart") == 1
