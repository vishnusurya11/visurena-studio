"""Battery rows are compared to battery rows, critic rows to critic rows (Jekyll ep01 Kawajiri,
2026-10-18: a kept 5-fault critic draft was weighed against a 1-row battery draft by raw fault count).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import plan_ladder  # noqa: E402
from studio.judges import plan as plan_judge  # noqa: E402
from studio.judges.verdict import Fault, Verdict  # noqa: E402
from tests.test_a_climb_that_moves_no_row_stops import IMPROVE, desk_with_plan, rows  # noqa: E402


def critic(n: int) -> Verdict:
    faults = [Fault(kind="invented", where=f"shot_{i}", note=f"count 'extras={i}'") for i in range(n)]
    return Verdict(judge=plan_judge.JUDGE, version=plan_judge.VERSION, passed=False, faults=faults,
                   confidence=1.0, reads=1)


def test_a_critic_verdict_never_replaces_the_best_battery_draft(tmp_path):
    desk, _ = desk_with_plan(tmp_path)
    desk.remember(rows("G-TWO"))
    assert desk.best[1] == 1
    five = critic(5)
    assert desk.best_refused(five).faults == five.faults


def test_the_battery_count_is_real_rows_not_printed_lines(tmp_path):
    desk, _ = desk_with_plan(tmp_path)
    many_lines = plan_ladder.battery_verdict(["G-LIGHT      : clean"] * 30 + ["GRAMMAR      : 1", "    G-TWO shot 1: a"])
    desk.remember(many_lines)
    assert desk.best[1] == 1
    desk.remember(rows("G-AIM", "G-AIM"))
    assert desk.best[1] == 1                       # 2 real rows are not fewer than 1


def test_a_stuck_check_is_per_kind(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-TWO"))
    desk.take(IMPROVE, 1, critic(1))
    assert len(writer.calls) == 2 and not desk.stuck


def test_the_terminal_prefers_a_battery_passed_critic_read_draft(tmp_path):
    from studio import episode_home
    from tests.test_episode_writer import canned_plan
    desk, _ = desk_with_plan(tmp_path)
    episode_home.write_plan(desk.plan, canned_plan())
    desk.remember(critic(2))
    out = desk.terminal(rows("G-TWO"))
    assert len(out.faults) == 2 and out.faults[0].kind == "invented"
