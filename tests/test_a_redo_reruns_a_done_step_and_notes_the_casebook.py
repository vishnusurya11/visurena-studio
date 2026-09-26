"""A `redo` order names a step: the runner runs it although its output is on
disk (done() is True), clears the redo once the step completes, and the
order's note is one owner row in the book's casebook -- through the same
function scripts/audit/note.py uses, so the bench answers to it."""
from __future__ import annotations

import pytest

from studio import casebook, db, episode_home, step_runner, work_orders
from tests.test_step_runner import _ctx, _step, conn  # noqa: F401


@pytest.fixture()
def book(tmp_path, monkeypatch):
    home = tmp_path / "book"
    plan = home / "episodes" / "ep01" / "plan.json"
    plan.parent.mkdir(parents=True)
    plan.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: home)
    return home


def test_a_redo_runs_a_done_step_and_is_cleared_after(conn, tmp_path, book):
    ctx = _ctx(conn, tmp_path)
    ran = []
    steps = [_step("02", lambda c: ran.append("02"), done=lambda c: True),
             _step("03", lambda c: ran.append("03"), done=lambda c: True)]
    work_orders.order(conn, "redo", "unit", codex_id=ctx.codex_id, stage="episode", unit="ep01", step_id="02")
    assert step_runner.run_steps(ctx, steps) == "completed"
    assert ran == ["02"]
    assert db.unit_status(conn, ctx.codex_id, "episode", "ep01") == {"02": "completed", "03": "skipped"}
    assert work_orders.redo_steps(conn, ctx.codex_id, "episode", "ep01") == set()
    ran.clear()
    assert step_runner.run_steps(ctx, steps) == "completed" and ran == []


def test_a_redo_that_escalates_keeps_the_redo_for_the_next_run(conn, tmp_path, book):
    from studio.escalate import Escalation
    ctx = _ctx(conn, tmp_path)

    def park(c):
        raise Escalation("PLAN", "plan.verdict.json", "sign the plan")

    work_orders.order(conn, "redo", "unit", codex_id=ctx.codex_id, stage="episode", unit="ep01", step_id="02")
    assert step_runner.run_steps(ctx, [_step("02", park, done=lambda c: True)]) == "escalated"
    assert work_orders.redo_steps(conn, ctx.codex_id, "episode", "ep01") == {"02"}


def test_the_redo_note_is_an_owner_row_in_the_casebook(conn, book):
    work_orders.order(conn, "redo", "unit", codex_id="20260901000001", stage="episode", unit="ep01",
                      step_id="02", note="the plan opens on the wrong street",
                      artefact="episodes/ep01/plan.json")
    (row,) = casebook.read_rows(book / "casebook" / casebook.OWNER)
    assert row.codex == "20260901000001" and row.unit == "ep01" and row.kind == "plan"
    assert row.verdict == "fault" and row.fault_class == "unknown" and row.verdict_by == "owner"
    assert row.sha8 == casebook.sha8_of(book / "episodes" / "ep01" / "plan.json")
    assert row.source.endswith(": the plan opens on the wrong street") and casebook.weight(row) == 1.0


def test_a_redo_note_may_name_its_class_and_needs_its_artefact(conn, book):
    work_orders.order(conn, "redo", "unit", codex_id="20260901000001", stage="episode", unit="ep01",
                      step_id="02", note="two of him", artefact="episodes/ep01/plan.json", fault="copies")
    (row,) = casebook.read_rows(book / "casebook" / casebook.OWNER)
    assert row.fault_class == "copies"
    with pytest.raises(ValueError, match="artefact"):
        work_orders.order(conn, "redo", "unit", codex_id="20260901000001", stage="episode", unit="ep01",
                          step_id="02", note="no artefact named")
    with pytest.raises(ValueError, match="not a fault class"):
        work_orders.order(conn, "redo", "unit", codex_id="20260901000001", stage="episode", unit="ep01",
                          step_id="02", note="x", artefact="episodes/ep01/plan.json", fault="ugly")
    assert conn.execute("SELECT count(*) FROM orders").fetchone()[0] == 1


def test_a_redo_without_a_note_writes_no_casebook_row(conn, book):
    work_orders.order(conn, "redo", "unit", codex_id="20260901000001", stage="episode", unit="ep01", step_id="02")
    assert not (book / "casebook" / casebook.OWNER).exists()


def test_the_casebook_owns_the_owner_note(book):
    target = casebook.note_owner(book, "20260901000001", "ep01", "episodes/ep01/plan.json", "pass", "fine")
    assert target == book / "casebook" / casebook.OWNER
    (row,) = casebook.read_rows(target)
    assert row.verdict == "pass" and row.fault_class is None and row.kind == "plan"
    assert casebook.kind_of("episodes/ep01/storyboard/grids/g.png") == "grid"
    with pytest.raises(ValueError, match="not a sheet"):
        casebook.kind_of("episodes/ep01/audio/lines/l01.wav")
