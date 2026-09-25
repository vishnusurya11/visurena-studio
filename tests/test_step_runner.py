"""The step runner every format line shares.

A step whose output already exists is skipped (resume = the output on disk).
A step that needs an owner signature raises Escalation: the runner records
`escalated` with the call-sheet line, prints it, and stops the unit cleanly --
no `failed`, no later step.  A refusal (SystemExit) or a crash is `failed`.
RENDER_HOLD stops the runner before the first GPU step, not after it.
"""
from __future__ import annotations

import types

import pytest

from studio import db, step_runner
from studio.escalate import Escalation
from studio.stage_run import StageContext


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


def _ctx(conn, tmp_path, **kw):
    codex_id = db.insert_codex(conn, "Book", codex_id="20260901000001")
    opts = dict(logs_root=tmp_path / "logs", busy=lambda: False,
                hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)
    opts.update(kw)
    return StageContext(conn, codex_id, tmp_path / "book", "episode", unit="ep01", number=1, **opts)


def _step(step_id, run, done=lambda ctx: False, gpu=False):
    return types.SimpleNamespace(STEP_ID=step_id, NAME="x", GPU=gpu, run=run, done=done)


def test_a_done_step_is_skipped_and_the_rest_run(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    ran = []
    steps = [_step("01", lambda c: ran.append("01"), done=lambda c: True),
             _step("02", lambda c: ran.append("02"))]
    assert step_runner.run_steps(ctx, steps) == "completed"
    assert ran == ["02"]
    assert db.unit_status(conn, ctx.codex_id, "episode", "ep01") == {"01": "skipped", "02": "completed"}


def test_an_escalation_parks_the_unit_and_stops(conn, tmp_path, capsys):
    ctx = _ctx(conn, tmp_path)
    ran = []

    def gate(c):
        raise Escalation("PLAN", "plan.verdict.json", "sign the plan")

    steps = [_step("02", gate), _step("03", lambda c: ran.append("03"))]
    assert step_runner.run_steps(ctx, steps) == "escalated"
    assert ran == []
    status = db.unit_status(conn, ctx.codex_id, "episode", "ep01")
    assert status == {"02": "escalated"}
    row = conn.execute("SELECT detail FROM events WHERE event = 'escalated'").fetchone()
    assert "PLAN" in row["detail"] and "plan.verdict.json" in row["detail"]
    assert "OWNER" in capsys.readouterr().out


def test_a_refusal_is_a_failure_that_names_itself(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)

    def refuse(c):
        raise SystemExit("REFUSED: no panel verdict")

    with pytest.raises(RuntimeError, match="no panel verdict"):
        step_runner.run_steps(ctx, [_step("09", refuse)])
    assert db.unit_status(conn, ctx.codex_id, "episode", "ep01") == {"09": "failed"}


def test_render_hold_stops_before_the_first_gpu_step(conn, tmp_path):
    ctx = _ctx(conn, tmp_path)
    ctx.hold.write_text("owner", encoding="utf-8")
    ran = []
    steps = [_step("05", lambda c: ran.append("05")), _step("07", lambda c: ran.append("07"), gpu=True)]
    with pytest.raises(SystemExit, match="HELD"):
        step_runner.run_steps(ctx, steps)
    assert ran == ["05"]
    assert db.unit_status(conn, ctx.codex_id, "episode", "ep01") == {"05": "completed"}


def test_the_registry_and_the_modules_agree_on_ids():
    steps = step_runner.load_steps("trailer")
    assert [s.STEP_ID for s in steps] == [f"{n:02d}" for n in range(1, 11)]


def test_a_script_step_waits_for_the_gpu_queue_then_launches(conn, tmp_path):
    calls = {"busy": 3, "launched": []}

    def busy():
        calls["busy"] -= 1
        return calls["busy"] > 0

    ctx = _ctx(conn, tmp_path, busy=busy, launch=lambda cmd: calls["launched"].append(cmd) or 0)
    ctx.sleep = lambda s: None
    rc = ctx.run_script("scripts/episode/say_lines.py", gpu=True, clock="lines")
    assert rc == 0 and calls["busy"] == 0
    assert calls["launched"][0][1:] == ["scripts/episode/say_lines.py", ctx.codex_id, "1"]


def test_a_script_step_refuses_when_the_queue_never_drains(conn, tmp_path):
    ctx = _ctx(conn, tmp_path, busy=lambda: True)
    ctx.sleep = lambda s: None
    ctx.wait_cap = 2
    with pytest.raises(SystemExit, match="queue"):
        ctx.run_script("scripts/episode/say_lines.py", gpu=True)


def test_a_failing_script_is_a_refusal_with_its_exit_code(conn, tmp_path):
    ctx = _ctx(conn, tmp_path, launch=lambda cmd: 2)
    with pytest.raises(SystemExit, match="exit 2"):
        ctx.run_script("scripts/episode/plan_check.py")
