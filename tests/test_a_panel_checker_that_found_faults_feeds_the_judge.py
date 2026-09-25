"""A panel checker that FOUND faults hands them to the panel judge and its ladder.

ep12, 2026-09-24: panel_content_check exited 1 on three failing panels and
run_script made that a refusal, so step 08 died before the panel judge and its
redraw ladder -- built for exactly those faults -- could run. Exit 1 is also a
crash, so it passes only when the checker rewrote its verdict file this run.
"""
import os
import time
from types import SimpleNamespace

import pytest

from scripts.episode import step_08_panels as step


def ctx_for(tmp_path, rc: int, writes: bool):
    board = tmp_path / "storyboard"
    board.mkdir(parents=True)
    verdict = board / "panel_content.json"
    verdict.write_text("[]", encoding="utf-8")
    old = time.time() - 3600
    os.utime(verdict, (old, old))
    logged = []

    def run_script(script, *extra, gpu=False, clock=None):
        if writes:
            verdict.write_text("[]", encoding="utf-8")
        if rc:
            raise SystemExit(f"REFUSED: {script} exit {rc}")
        return 0

    return SimpleNamespace(home=tmp_path, run_script=run_script,
                           log=lambda msg, **kw: logged.append(msg)), logged


def test_faults_found_with_a_fresh_verdict_pass_on(tmp_path):
    ctx, logged = ctx_for(tmp_path, 1, writes=True)
    step.checked(ctx, "scripts/episode/panel_content_check.py", "panel_content", "panel_content.json")
    assert logged and "faults found" in logged[0]


def test_a_checker_that_wrote_nothing_still_refuses(tmp_path):
    ctx, _ = ctx_for(tmp_path, 1, writes=False)
    with pytest.raises(SystemExit):
        step.checked(ctx, "scripts/episode/panel_content_check.py", "panel_content", "panel_content.json")


def test_any_other_exit_code_refuses(tmp_path):
    ctx, _ = ctx_for(tmp_path, 2, writes=True)
    with pytest.raises(SystemExit):
        step.checked(ctx, "scripts/episode/panel_content_check.py", "panel_content", "panel_content.json")
