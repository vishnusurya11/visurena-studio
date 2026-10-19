"""One clock table, from run_budget and stages.yaml (P16).

ep01's operator met three clocks (the 5 h rung ceiling, the owner's 6 h limit, the 120 min
first-render wall) and no page said which one stops what.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from studio import run_budget, step_caps

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / ".claude" / "skills" / "episode" / "GATES.md"

spec = importlib.util.spec_from_file_location("ep_commands", ROOT / "scripts" / "episode" / "commands.py")
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def row(name: str) -> str:
    return next(l for l in commands.clock_table().splitlines() if l.startswith(f"| {name} |"))


def test_the_gates_carry_the_clock_table_verbatim():
    assert commands.between(GATES.read_text(encoding="utf-8"), "clock") == commands.clock_table()


def test_the_rung_ceiling_is_run_budgets():
    assert f"| {run_budget.EPISODE_CEILING_SECONDS // 60} min |" in row("rung ceiling")


def test_the_owner_limit_is_run_budgets():
    assert f"| {run_budget.OWNER_LIMIT_SECONDS // 60} min |" in row("owner limit")


def test_the_first_render_wall_is_the_takes_cap():
    assert f"| {int(step_caps.wall_s('takes') // 60)} min |" in row("first-render wall")


def test_the_cheap_check_and_dark_episodes_are_the_code():
    assert f"| {int(run_budget.CHEAP_CHECK_SECONDS)} s |" in row("cheap check")
    assert f"| {run_budget.DARK_EPISODES_REQUIRED} episodes |" in row("dark budget")


def test_the_repair_cap_is_repair_clocks():
    from studio import repair_clock
    assert f"| {int(repair_clock.cap_for(['09']) // 60)} min for a redo of 09 |" in row("repair cap")
