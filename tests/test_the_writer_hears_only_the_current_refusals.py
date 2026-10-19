"""The writer EDITS the previous plan, so it hears the current rows plus one line naming the gates
already fixed (Jekyll ep01 Kawajiri, 2026-10-18: merged() re-asserted G-AIM rows after the glue was fixed
and climb 2 improve 2 re-broke G-TWO).  merged() stays for the no-previous path.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.test_a_climb_that_moves_no_row_stops import IMPROVE, TIER, desk_with_plan, rows  # noqa: E402


def test_round_three_does_not_hear_a_row_round_one_had(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-AIM", "G-AIM", "G-TWO", "G-PUSH"))
    desk.take(IMPROVE, 1, rows("G-TWO", "G-PUSH", "G-LAID"))
    second = writer.calls[1]["refusals"]
    assert not any(line.startswith("    G-AIM") for line in second)
    assert [l for l in second if "G-LAID" in l] and [l for l in second if "G-TWO" in l]


def test_the_fixed_gates_ride_one_line(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-AIM", "G-AIM", "G-TWO"))
    desk.take(IMPROVE, 1, rows("G-TWO", "G-PUSH"))
    second = writer.calls[1]["refusals"]
    assert second[-1] == "already fixed, keep fixed: G-AIM"
    assert sum(l.startswith("already fixed") for l in second) == 1


def test_no_line_when_nothing_was_fixed(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    desk.take(IMPROVE, 0, rows("G-AIM"))
    desk.take(TIER, 0, rows("G-AIM", "G-TWO"))
    assert not any(l.startswith("already fixed") for l in writer.calls[1]["refusals"])


def test_with_no_previous_plan_the_history_is_merged(tmp_path):
    desk, writer = desk_with_plan(tmp_path)
    (tmp_path / "plan.json").unlink()
    desk.refusals = ["    G-OLD shot 1: an old row"]
    desk.take(IMPROVE, 0, rows("G-NEW"))
    heard = writer.calls[0]["refusals"]
    assert heard[0] == "    G-OLD shot 1: an old row" and any("G-NEW" in l for l in heard)
