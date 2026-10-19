"""C6 (Jekyll Kawajiri ep01 retro, close-out): the clock pieces that were built but never called.

- the drive's finish prints 'charged | wall | dead' (gpu_ledger.finish_line) from ep01's clock.jsonl;
- the step runner opens comfy.row_deadline around a step that has a wall left (P14);
- the runner writes a dark-budget row per step (P12): what the budget would have said, cutting nothing;
- a relaunch after the owner's manual pause/resume is dead time, not an attempt against the step cap (P13).
Every outward call is a fake; ep01's records are copies in tests/fixtures/ep01_replay/P12.
"""
from __future__ import annotations

import json
import shutil
import types
from pathlib import Path

from studio import comfy, run_budget, run_clock, step_runner, step_wall
from tests import autopilot_cli_fixtures as fx
from tests.test_a_capped_step_keeps_its_best_and_goes_on import _runner_ctx

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P12"


def _ledger():
    from tests.test_gpu_ledger import load
    return load()


def _ep01(tmp_path):
    for name in ("clock.jsonl", "drive.jsonl"):
        shutil.copy(FIX / name, tmp_path / name)
    return tmp_path


# ---- the finish line --------------------------------------------------------------------

def test_the_finish_line_on_ep01s_clock_names_charged_wall_and_dead(tmp_path):
    home = _ep01(tmp_path)
    line = _ledger().finish_line(home)
    spans = run_clock.spans(home)
    wall = max(e for _, e in spans) - min(s for s, _ in spans)
    dead = sum(g["seconds"] for g in run_clock.dead_gaps(home))
    assert line == _ledger().time_line(run_clock.spent(home), wall, dead)
    assert dead > 0 and wall > run_clock.spent(home)


def test_the_finish_line_of_an_unrun_home_is_all_zero(tmp_path):
    assert _ledger().finish_line(tmp_path) == "charged 0.00 h | wall 0.00 h | dead 0.00 h"


def test_steps_busy_idle_minutes_come_from_timing_spans(tmp_path):
    rows = [{"stage": "step_09", "started": "2026-10-19T00:00:00", "ended": "2026-10-19T00:10:00", "seconds": 600.0}]
    (tmp_path / "timing.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    spans = _ledger().step_spans(tmp_path)
    assert [s for s, _, _ in spans] == ["09"] and spans[0][2] - spans[0][1] == 600.0


# ---- row_deadline around a step ---------------------------------------------------------

def test_a_step_with_wall_left_runs_under_a_row_deadline(tmp_path):
    ctx, seen = _runner_ctx(tmp_path), []
    ctx.clock = lambda: 1000.0
    step = types.SimpleNamespace(STEP_ID="05", NAME="timeline", GPU=False, done=lambda c: False,
                                 run=lambda c: seen.append(comfy.ROW_DEADLINE))
    assert step_runner.run_steps(ctx, [step]) == "completed"
    assert seen == [1000.0 + step_wall_s("05")] and comfy.ROW_DEADLINE is None


def step_wall_s(step_id):
    from studio import step_caps
    return step_caps.step_wall_s(step_id)


def test_a_step_with_its_wall_already_spent_gets_no_row_deadline():
    wall = step_wall.StepWall("05", 100.0, 0.0, clock=lambda: 50.0, prior=200.0)
    assert step_wall.deadline_of(wall) is None


def test_a_step_with_no_wall_gets_no_row_deadline():
    assert step_wall.deadline_of(step_wall.StepWall("05", 0.0, 0.0, clock=lambda: 5.0)) is None


# ---- the dark-budget row ----------------------------------------------------------------

def test_a_step_writes_a_dark_row_that_cuts_nothing(tmp_path):
    ctx, now = _runner_ctx(tmp_path), [0.0]
    ctx.clock = lambda: now[0]
    ctx.budget = run_budget.Budget(18000, run_budget.EPISODE_SHARES, clock=lambda: 0.0)
    step = types.SimpleNamespace(STEP_ID="05", NAME="timeline", GPU=False, done=lambda c: False,
                                 run=lambda c: now.__setitem__(0, 400.0))
    assert step_runner.run_steps(ctx, [step]) == "completed"
    rows = run_budget.read_dark(step_wall.home_of(ctx))
    assert rows[0]["step"] == "05" and rows[0]["seconds"] == 400.0 and rows[0]["would_cut"] is True


def test_a_dark_row_for_a_step_with_no_share_is_skipped(tmp_path):
    budget = run_budget.Budget(18000, {"01": 0.5}, clock=lambda: 0.0)
    assert run_budget.step_dark_row(budget, "zz", 5.0) is None


# ---- a manual pause/resume is dead time -------------------------------------------------

def _events(book, *words):
    cli = fx.load()
    for w in words:
        cli.event(book, {"event": w})
    return cli


def test_a_relaunch_after_a_manual_resume_is_not_counted_against_the_step_cap(tmp_path):
    book = fx.book(tmp_path)
    (book / "episodes" / "ep01").mkdir(parents=True)
    cli, d = _events(book, "relaunch", "pause", "resume"), fx.deps(tmp_path)
    for _ in range(12):
        assert cli.step_guard(book, 1, "step 09 ok", d, why="relaunch") is None


def test_the_launch_after_the_resume_counts_again(tmp_path):
    book = fx.book(tmp_path)
    (book / "episodes" / "ep01").mkdir(parents=True)
    cli, d = _events(book, "pause", "resume", "relaunch"), fx.deps(tmp_path)
    got = [cli.step_guard(book, 1, "step 09 ok", d, why="relaunch") for _ in range(12)]
    assert "step_cap" in got
