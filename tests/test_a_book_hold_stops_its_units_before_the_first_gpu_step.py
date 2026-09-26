"""A hold row stops a runner where RENDER_HOLD does: before the first GPU
step, never after it.  A book-scope hold stops that book's units and no other
book's; a studio-scope hold stops both; the file still works on its own; and
the tick mirrors the file into a studio-scope hold row (and lifts it when the
file is gone), so the board sees the owner's brake."""
from __future__ import annotations

import pytest

from studio import db, step_runner, work_orders
from studio.stage_run import StageContext
from tests.test_step_runner import _ctx, _step, conn  # noqa: F401

OTHER = "20260901000002"


def _other_ctx(conn, tmp_path):
    db.insert_codex(conn, "Other", codex_id=OTHER)
    return StageContext(conn, OTHER, tmp_path / "other", "episode", unit="ep01", number=1,
                        logs_root=tmp_path / "logs", busy=lambda: False,
                        hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)


def _gpu_steps(ran):
    return [_step("05", lambda c: ran.append("05")), _step("07", lambda c: ran.append("07"), gpu=True)]


def test_a_book_hold_stops_that_books_unit_and_not_another_books(conn, tmp_path):
    mine, other = _ctx(conn, tmp_path), _other_ctx(conn, tmp_path)
    work_orders.hold(conn, "book", "re-planning", codex_id=mine.codex_id)
    ran = []
    with pytest.raises(SystemExit, match="HELD"):
        step_runner.run_steps(mine, _gpu_steps(ran))
    assert ran == ["05"]
    assert db.unit_status(conn, mine.codex_id, "episode", "ep01") == {"05": "completed"}
    assert step_runner.run_steps(other, _gpu_steps(ran)) == "completed"
    assert ran == ["05", "05", "07"]


def test_a_studio_hold_stops_both_books(conn, tmp_path):
    mine, other = _ctx(conn, tmp_path), _other_ctx(conn, tmp_path)
    work_orders.hold(conn, "studio", "power")
    for ctx in (mine, other):
        with pytest.raises(SystemExit, match="HELD.*hold row"):
            step_runner.run_steps(ctx, _gpu_steps([]))


def test_a_unit_hold_stops_its_unit_only(conn, tmp_path):
    mine = _ctx(conn, tmp_path)
    work_orders.hold(conn, "unit", "look again", codex_id=mine.codex_id, stage="episode", unit="ep02")
    assert step_runner.run_steps(mine, _gpu_steps([])) == "completed"
    work_orders.hold(conn, "unit", "look again", codex_id=mine.codex_id, stage="episode", unit="ep01")
    with pytest.raises(SystemExit, match="HELD"):
        step_runner.run_steps(mine, _gpu_steps([]))


def test_a_lifted_hold_lets_the_unit_through(conn, tmp_path):
    mine = _ctx(conn, tmp_path)
    hold_id = work_orders.hold(conn, "book", "wait", codex_id=mine.codex_id)
    assert mine.held()
    work_orders.lift(conn, hold_id)
    assert not mine.held()
    assert step_runner.run_steps(mine, _gpu_steps([])) == "completed"


def test_the_render_hold_file_still_stops_the_unit_by_itself(conn, tmp_path):
    mine = _ctx(conn, tmp_path)
    assert not mine.held()
    mine.hold.write_text("owner", encoding="utf-8")
    assert mine.held() and work_orders.active_holds(conn) == []
    with pytest.raises(SystemExit, match="RENDER_HOLD is there"):
        step_runner.run_steps(mine, _gpu_steps([]))


def test_the_file_is_mirrored_into_a_studio_hold_and_lifted_when_it_goes(conn, tmp_path):
    path = tmp_path / "RENDER_HOLD"
    assert work_orders.mirror_render_hold(conn, path) is None
    path.write_text("owner", encoding="utf-8")
    hold_id = work_orders.mirror_render_hold(conn, path)
    (row,) = work_orders.active_holds(conn)
    assert row["id"] == hold_id and row["scope"] == "studio" and row["reason"] == "RENDER_HOLD"
    assert work_orders.mirror_render_hold(conn, path) == hold_id
    assert len(work_orders.active_holds(conn)) == 1
    path.unlink()
    assert work_orders.mirror_render_hold(conn, path) is None
    assert work_orders.active_holds(conn) == []
    assert [o["kind"] for o in conn.execute("SELECT kind FROM orders ORDER BY id")] == ["hold", "lift"]


def test_a_mirrored_hold_is_not_lifted_by_the_file_going_when_the_owner_wrote_the_row(conn, tmp_path):
    path = tmp_path / "RENDER_HOLD"
    hold_id = work_orders.hold(conn, "studio", "owner said stop")
    assert work_orders.mirror_render_hold(conn, path) is None
    assert [h["id"] for h in work_orders.active_holds(conn)] == [hold_id]
