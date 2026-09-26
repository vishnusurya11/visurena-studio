"""`episode.py <book>` with no unit takes the desk's queue (decision
2026-09-25, "Explicit invocation"): every row the desk has queued for this
book's episode line, in v_queue order (priority, then sequence), each claimed
under its run before its steps and released after.  A deferred, blocked or
held row is never taken.  The run takes what is queued NOW and exits -- no
loop, no sleep, no poll ("Not built, on purpose").  `--all` is the old form:
every folder with a plan, off the disk.

The desk's tick is a no-op here (it has its own tests; left live it would
re-derive the hand-made rows), and every step is monkeypatched: nothing real
runs, no GPU, no model."""
from __future__ import annotations

import time

import pytest

import episode
from studio import db, queue, step_runner, tick
from tests.test_episode_runner import CODEX, _opts, book, conn, stub_step_02  # noqa: F401


@pytest.fixture(autouse=True)
def no_tick(monkeypatch):
    monkeypatch.setattr(tick, "tick_book", lambda conn, codex_id: None)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: pytest.fail(f"the runner slept {s}s"))


@pytest.fixture()
def steps(monkeypatch):
    """Every step but the last is skipped; the last runs (a no-op) so the unit
    completes and its row is done.  `seen` records which unit each step saw."""
    seen = []
    loaded = step_runner.load_steps("episode")
    for step in loaded:
        monkeypatch.setattr(step, "done", lambda ctx, s=step: seen.append((ctx.unit, s.STEP_ID)) or True)
    monkeypatch.setattr(loaded[-1], "done", lambda ctx: False)
    monkeypatch.setattr(loaded[-1], "run", lambda ctx: seen.append((ctx.unit, "run")))
    return seen


def _order(conn, unit, state, priority=0, **fields):
    return db.upsert_work_order(conn, CODEX, "episode", unit, state=state, priority=priority,
                                sequence=int(unit[2:]), **fields)


def _units(seen):
    order = []
    for unit, _ in seen:
        if unit not in order:
            order.append(unit)
    return order


def test_the_queue_is_taken_in_priority_then_sequence_order_and_nothing_else_is(conn, book, tmp_path, steps):
    _order(conn, "ep02", "queued", priority=1)
    _order(conn, "ep05", "queued", priority=0)
    _order(conn, "ep03", "queued", priority=0)
    _order(conn, "ep04", "deferred")
    _order(conn, "ep01", "blocked", blocked_on="refs/04")
    _order(conn, "ep06", "held", hold_reason="recast")
    assert episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert _units(steps) == ["ep03", "ep05", "ep02"]
    for unit, state in (("ep04", "deferred"), ("ep01", "blocked"), ("ep06", "held")):
        assert db.work_order(conn, CODEX, "episode", unit)["state"] == state
    assert [db.work_order(conn, CODEX, "episode", u)["state"] for u in ("ep02", "ep03", "ep05")] == ["done"] * 3


def test_a_claim_sets_the_lease_under_the_run_and_the_release_clears_it(conn, book, tmp_path, monkeypatch):
    _order(conn, "ep03", "queued")
    during = {}
    loaded = step_runner.load_steps("episode")

    def look(ctx):
        row = db.work_order(conn, CODEX, "episode", "ep03")
        during.update(state=row["state"], claimed_by=row["claimed_by"], lease=row["lease_until"],
                      run_id=row["run_id"], tracker=ctx.tracker.run_id)
        return True
    for step in loaded:
        monkeypatch.setattr(step, "done", look)
    monkeypatch.setattr(loaded[-1], "done", lambda ctx: False)
    monkeypatch.setattr(loaded[-1], "run", lambda ctx: None)
    assert episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert during["state"] == "running" and during["claimed_by"] and during["lease"]
    assert during["run_id"] == during["tracker"]
    row = db.work_order(conn, CODEX, "episode", "ep03")
    assert (row["state"], row["claimed_by"], row["lease_until"]) == ("done", None, None)
    assert row["run_id"] == during["tracker"]


def test_a_unit_whose_every_step_is_skipped_goes_back_to_the_queue_unclaimed(conn, book, tmp_path, monkeypatch):
    for step in step_runner.load_steps("episode"):
        monkeypatch.setattr(step, "done", lambda ctx: True)
    _order(conn, "ep03", "queued")
    assert episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path)) == 0
    row = db.work_order(conn, CODEX, "episode", "ep03")
    assert (row["state"], row["claimed_by"], row["lease_until"]) == ("queued", None, None)


def test_the_run_takes_what_is_queued_now_and_exits(conn, book, tmp_path, monkeypatch, steps):
    """A row queued while the run is on the floor is not taken: the next
    invocation is the next request."""
    _order(conn, "ep03", "queued")
    loaded = step_runner.load_steps("episode")
    monkeypatch.setattr(loaded[-1], "run", lambda ctx: _order(conn, "ep04", "queued"))
    assert episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert _units(steps) == ["ep03"]
    assert db.work_order(conn, CODEX, "episode", "ep04")["state"] == "queued"


def test_a_failed_claim_is_skipped_with_a_line_and_the_rest_run(conn, book, tmp_path, monkeypatch, steps, capsys):
    _order(conn, "ep03", "queued")
    _order(conn, "ep04", "queued")
    real = queue.claim
    monkeypatch.setattr(queue, "claim", lambda conn, c, s, unit, run_id, **kw: (
        False if unit == "ep03" else real(conn, c, s, unit, run_id, **kw)))
    assert episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path)) == episode.PARKED
    assert _units(steps) == ["ep04"]
    assert "SKIPPED 20260901000001 episode/ep03" in capsys.readouterr().out


def test_nothing_queued_is_a_refusal_that_names_the_other_forms(conn, book, tmp_path):
    _order(conn, "ep01", "blocked", blocked_on="refs/04")
    with pytest.raises(SystemExit, match="nothing queued.*--all"):
        episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path))
    assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_all_runs_every_planned_folder_off_the_disk_and_the_flag_stays_out_of_the_steps(conn, book, tmp_path, monkeypatch):
    for n in (2, 1):
        (book / "episodes" / f"ep{n:02d}").mkdir(parents=True)
        (book / "episodes" / f"ep{n:02d}" / "plan.json").write_text("{}", encoding="utf-8")
    seen, extras = [], []
    for step in step_runner.load_steps("episode"):
        monkeypatch.setattr(step, "done", lambda ctx: seen.append(ctx.unit) or extras.append(list(ctx.extra)) or True)
    assert episode.main([CODEX, "--all", "--cast=a"], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert _units([(u, None) for u in seen]) == ["ep01", "ep02"]
    assert extras[0] == ["--cast=a"]


def test_number_of_is_the_inverse_of_the_unit_grammar():
    from studio import episode_run
    assert episode.number_of(episode_run.unit_of(4)) == 4
    assert episode.number_of("ep12") == 12


def test_the_main_ticks_its_book_before_reading_the_queue(conn, book, tmp_path, monkeypatch, steps):
    calls = []
    monkeypatch.setattr(tick, "tick_book", lambda conn, codex_id: calls.append(codex_id))
    _order(conn, "ep03", "queued")
    episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path))
    assert calls[0] == CODEX
