"""C3_verdict #7 (T1b, D4): stop at a boundary, never mid-step.

22 of 23 killed WotW runs (ep19-27) were a session pausing the series to land
a fix -- 527 waste-minutes, the top cause of the P90 tail.  `autopilot pause
--at-boundary` writes `stop_at_boundary` in the running episode's home; the
runner reads it between steps, between ladder rungs, between grids and
between takes, exits `paused_at_boundary` with its clock row closed, and the
autopilot reads that as PAUSED, never as a crash or a stop."""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from studio import boundary, judged_gate, step_runner
from studio.ladder import Ladder, Rung
from tests.test_step_runner import _ctx, _step, conn  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def test_a_flag_set_during_a_step_lets_it_finish_and_stops_before_the_next(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    ctx.home = tmp_path / "ep01"
    ctx.home.mkdir()
    ran = []
    steps = [_step("05", lambda c: ran.append("05") or boundary.request(c.home)),
             _step("06", lambda c: ran.append("06"))]
    assert step_runner.run_steps(ctx, steps) == boundary.OUTCOME
    assert ran == ["05"]


def test_a_step_that_ends_on_the_flag_is_paused_not_failed(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    ctx.home = tmp_path / "ep01"
    ctx.home.mkdir()

    def takes(c):
        boundary.request(c.home)
        raise SystemExit("REFUSED: scripts/episode/takes_r2v.py exit 1")     # the child stopped on the flag

    assert step_runner.run_steps(ctx, [_step("09", takes)]) == boundary.OUTCOME
    from studio import db
    # the events table's CHECK has no 'paused': a started step closes `deferred`, never `failed`
    assert db.unit_status(conn, ctx.codex_id, "episode", "ep01") == {"09": "deferred"}


def test_a_ladder_stops_between_rungs(tmp_path):
    home = tmp_path / "ep01"
    home.mkdir()
    from studio.judges.verdict import Fault, Verdict
    bad = Verdict(judge="j", version="1", passed=False, confidence=1.0, reads=1,
                  faults=[Fault(kind="k", where="w", note="n")])
    taken = []
    ctx = types.SimpleNamespace(home=home, budget=types.SimpleNamespace(step="02", clock=lambda: 0.0),
                                learn=lambda learning: None)
    rungs = judged_gate.Rungs(Ladder([Rung("improve", 0.0, tries=3)], "keep_best"),
                              take=lambda rung, i, v: taken.append(i) or boundary.request(home))
    import studio.judged_gate as jg
    jg_aff = jg.affordable
    jg.affordable = lambda *a, **k: True
    try:
        with pytest.raises(boundary.PausedAtBoundary):
            judged_gate.climbed(ctx, "PLAN", lambda: bad, rungs, "keep_best")
    finally:
        jg.affordable = jg_aff
    assert taken == [0]


def _takes():
    spec = importlib.util.spec_from_file_location("takes_r2v_c3", ROOT / "scripts" / "episode" / "takes_r2v.py")
    sys.path.insert(0, str(ROOT / "scripts" / "episode"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_takes_stop_after_the_current_take(monkeypatch, tmp_path):
    tr = _takes()
    collected, cancelled = [], []
    stop = {"now": False}
    monkeypatch.setattr(tr, "collect", lambda c, pid, out: collected.append(c["index"]) or stop.update(now=True)
                        or {"index": c["index"]})
    monkeypatch.setattr(tr, "cancel_pending", lambda ids: cancelled.extend(ids) or set(ids[1:]))
    tickets = [({"index": i}, f"p{i}") for i in range(4)]
    done, lost = tr.collect_all(tickets, where=lambda c: tmp_path, stop=lambda: stop["now"])
    assert collected == [0, 1]                       # the take in hand, then the one already running
    assert cancelled == ["p1", "p2", "p3"]
    assert sorted(c["index"] for c, _ in lost) == [2, 3]
    assert all("boundary" in said for _, said in lost)


def test_the_flag_is_consumed_on_resume(tmp_path, monkeypatch):
    import episode
    from studio import db, episode_home
    from tests.test_episode_runner import CODEX, _opts
    monkeypatch.setattr(episode_home, "book_dir", lambda codex_id: tmp_path / "book")
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    for step in step_runner.load_steps("episode"):
        monkeypatch.setattr(step, "done", lambda ctx: True)
    home = episode_home.home(tmp_path / "book", 1)
    boundary.request(home)
    assert episode.main([CODEX, "1"], conn=connection, tools=(), **_opts(tmp_path)) == 0
    assert not boundary.requested(home)


ap = importlib.util.module_from_spec(importlib.util.spec_from_file_location("ap_core_c3b", ROOT / "studio" / "autopilot.py"))


def _signals(**kw):
    from tests.test_autopilot_derives_state_from_disk import signals
    return signals(**kw)


def test_the_autopilot_reads_a_boundary_exit_as_paused_never_as_a_stop():
    from studio import autopilot as core
    start = {"event": "start", "sha": "x"}
    end = {"event": "end", "code": 2, "sha": "x", "paused_at_boundary": True}
    drive = [start, end]
    assert core.stops(drive) == 0
    paused = core.derive(_signals(drive_rows=drive, paused=True, log_tail="=== EPISODE paused_at_boundary ==="), 20)
    assert paused.state is core.State.PAUSED
    resumed = core.derive(_signals(drive_rows=drive, log_tail="=== EPISODE paused_at_boundary ==="), 20)
    assert (resumed.state, resumed.reason) == (core.State.IDLE, "boundary_resume")


def test_the_drive_records_a_boundary_exit():
    from studio import episode_drive
    assert episode_drive.outcome("=== EPISODE paused_at_boundary | ep20 ===") == "paused"


def test_pause_at_boundary_flags_the_running_episode(tmp_path):
    from tests import autopilot_cli_fixtures as fx
    cli = fx.load()
    root = fx.book(tmp_path)
    deps = fx.deps(tmp_path, "RUNNING")
    (deps.root / "gpu.lock").parent.mkdir(parents=True, exist_ok=True)
    (deps.root / "gpu.lock").write_text(json.dumps({"drive_pid": 1, "episode": 21}), encoding="utf-8")
    cli.pause_at_boundary(root, root.name.split("_", 1)[0], deps)
    assert boundary.requested(root / "episodes" / "ep21")
    assert json.loads((root / "autopilot" / "series.json").read_text(encoding="utf-8"))["paused"] is True
