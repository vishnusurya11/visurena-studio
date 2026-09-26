"""A deferred unit waits (decision 2026-09-25, "Deferred units"): episode 13
burned six identical ladders unattended.  A `retry` order, taken at the top of
the next run, queues the row ONCE -- the order is stamped with the run that
took it, a second run finds nothing pending, and a retry on a row that is not
deferred or failed changes nothing."""
from __future__ import annotations

from studio import db, step_runner, work_orders
from tests.test_step_runner import _ctx, _step, conn  # noqa: F401


def test_a_retry_queues_the_deferred_row_and_is_taken_by_the_run(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    db.upsert_work_order(conn, ctx.codex_id, "episode", "ep01", state="deferred")
    order_id = work_orders.order(conn, "retry", "unit", codex_id=ctx.codex_id, stage="episode", unit="ep01")
    seen = []
    step = _step("02", lambda c: seen.append(db.work_order(conn, c.codex_id, "episode", "ep01")["state"]),
                 done=lambda c: seen.append(db.work_order(conn, c.codex_id, "episode", "ep01")["state"]) or False)
    assert step_runner.run_steps(ctx, [step]) == "completed"
    assert seen[0] == "queued"          # the take queued the row before the first step looked
    row = conn.execute("SELECT taken_ts, taken_by_run FROM orders WHERE id = ?", (order_id,)).fetchone()
    assert row["taken_ts"] and row["taken_by_run"] == ctx.tracker.run_id
    assert db.work_order(conn, ctx.codex_id, "episode", "ep01")["state"] != "deferred"


def test_a_second_run_sees_no_pending_order(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    db.upsert_work_order(conn, ctx.codex_id, "episode", "ep01", state="failed")
    work_orders.order(conn, "retry", "unit", codex_id=ctx.codex_id, stage="episode", unit="ep01")
    assert work_orders.take_orders(conn, ctx.codex_id, "episode", "ep01", "run-1") != []
    assert db.work_order(conn, ctx.codex_id, "episode", "ep01")["state"] == "queued"
    db.upsert_work_order(conn, ctx.codex_id, "episode", "ep01", state="deferred")
    assert work_orders.take_orders(conn, ctx.codex_id, "episode", "ep01", "run-2") == []
    assert db.work_order(conn, ctx.codex_id, "episode", "ep01")["state"] == "deferred"


def test_a_retry_on_a_running_or_done_row_does_nothing(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    for state in ("running", "done", "queued"):
        db.upsert_work_order(conn, ctx.codex_id, "episode", "ep01", state=state)
        work_orders.order(conn, "retry", "unit", codex_id=ctx.codex_id, stage="episode", unit="ep01")
        work_orders.take_orders(conn, ctx.codex_id, "episode", "ep01", f"run-{state}")
        assert db.work_order(conn, ctx.codex_id, "episode", "ep01")["state"] == state


def test_a_retry_with_no_row_yet_makes_none(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    work_orders.order(conn, "retry", "unit", codex_id=ctx.codex_id, stage="episode", unit="ep01")
    work_orders.take_orders(conn, ctx.codex_id, "episode", "ep01", "run-1")
    assert db.work_order(conn, ctx.codex_id, "episode", "ep01") is None
