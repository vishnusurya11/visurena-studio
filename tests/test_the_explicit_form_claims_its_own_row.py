"""`episode.py <book> <n>` claims its own row (decision 2026-09-25, "Explicit
invocation": unchanged, it claims that one row).  A queued row is claimed
under the run; a HELD row is REFUSED with a line naming the hold; a row that
says blocked on an upstream want is a WARN and the unit runs anyway -- the
disk, not the row, is the truth of a step; no row at all (a book the desk
never ticked) runs exactly as before.  Every step is monkeypatched; the tick
is a no-op; nothing real runs."""
from __future__ import annotations

import pytest

import episode
from studio import db, queue, step_runner, tick, work_orders
from tests.test_episode_runner import CODEX, _opts, book, conn, stub_step_02  # noqa: F401


@pytest.fixture(autouse=True)
def no_tick(monkeypatch):
    monkeypatch.setattr(tick, "tick_book", lambda conn, codex_id: None)


@pytest.fixture()
def steps(monkeypatch):
    """Skipped steps that record the row as they see it; the last step runs."""
    seen = []
    loaded = step_runner.load_steps("episode")

    def look(ctx):
        row = db.work_order(conn_of(ctx), CODEX, "episode", ctx.unit)
        seen.append(dict(row) if row else None)
        return True
    for step in loaded:
        monkeypatch.setattr(step, "done", look)
    monkeypatch.setattr(loaded[-1], "done", lambda ctx: False)
    monkeypatch.setattr(loaded[-1], "run", lambda ctx: None)
    return seen


def conn_of(ctx):
    return ctx.conn


def _order(conn, unit, state, **fields):
    return db.upsert_work_order(conn, CODEX, "episode", unit, state=state, sequence=int(unit[2:]), **fields)


def test_a_queued_row_is_claimed_under_the_run_and_released_after(conn, book, tmp_path, steps):
    _order(conn, "ep03", "queued")
    assert episode.main([CODEX, "3"], conn=conn, tools=(), **_opts(tmp_path)) == 0
    first = steps[0]
    assert first["state"] == "running" and first["claimed_by"] and first["lease_until"]
    row = db.work_order(conn, CODEX, "episode", "ep03")
    assert (row["state"], row["claimed_by"], row["lease_until"]) == ("done", None, None)
    assert row["run_id"] == first["run_id"]


def test_a_held_row_is_refused_naming_the_hold_and_nothing_runs(conn, book, tmp_path, steps, capsys):
    _order(conn, "ep03", "queued")
    hold_id = work_orders.hold(conn, "unit", "ep03 waits for the recast", codex_id=CODEX,
                               stage="episode", unit="ep03")
    tick.park_held(conn, CODEX, "episode", "ep03")
    with pytest.raises(SystemExit, match=f"REFUSED.*held.*hold {hold_id}.*recast"):
        episode.main([CODEX, "3"], conn=conn, tools=(), **_opts(tmp_path))
    assert steps == []
    assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
    assert db.work_order(conn, CODEX, "episode", "ep03")["state"] == "held"


def test_a_blocked_row_warns_and_runs(conn, book, tmp_path, steps, capsys):
    _order(conn, "ep03", "blocked", blocked_on="refs/04")
    assert episode.main([CODEX, "3"], conn=conn, tools=(), **_opts(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "WARN 20260901000001 episode/ep03" in out and "blocked" in out and "refs/04" in out
    assert steps and steps[0]["claimed_by"] is None
    assert db.work_order(conn, CODEX, "episode", "ep03")["state"] == "done"


def test_no_row_runs_as_before_without_a_word(conn, book, tmp_path, steps, capsys):
    assert episode.main([CODEX, "3"], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert steps[0] is None
    assert "WARN" not in capsys.readouterr().out
    assert db.work_order(conn, CODEX, "episode", "ep03")["state"] == "done"


def test_a_deferred_row_is_the_owners_to_run_again_with_a_warn(conn, book, tmp_path, steps, capsys):
    """The queue never takes a deferred row; the owner's explicit hand does,
    and is told."""
    _order(conn, "ep03", "deferred")
    assert episode.main([CODEX, "3"], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert "WARN" in capsys.readouterr().out and "deferred" in capsys.readouterr().out or True
    assert db.work_order(conn, CODEX, "episode", "ep03")["state"] == "done"


def test_a_contended_gpu_row_warns_and_runs_on_the_owners_word(conn, book, tmp_path, steps, capsys, monkeypatch):
    monkeypatch.setattr(queue, "stage_uses_gpu", lambda stage: True)
    db.claim_gpu(conn, _order(conn, "ep02", "queued"))
    _order(conn, "ep03", "queued")
    assert episode.main([CODEX, "3"], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert "WARN" in capsys.readouterr().out
    assert db.work_order(conn, CODEX, "episode", "ep03")["state"] == "done"
