"""Jekyll ep07 retro S6: the 2-thread cap is for the lane that runs beside a GPU render.
A serial pass (no --cpu-only) ran with the GPU idle on 2 of 32 cores: 54.7 of take_dq's
179.6 min were exposed, and gait measured 2.9x faster at 8 threads than at 2."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_dq  # noqa: E402


def test_the_lane_beside_a_render_keeps_two():
    assert take_dq.judge_threads(True, {}, cores=32) == 2


def test_a_serial_pass_takes_half_the_cores():
    assert take_dq.judge_threads(False, {}, cores=32) == 16


def test_the_lane_setting_still_rules_the_lane():
    assert take_dq.judge_threads(True, {"VISURENA_LANE_THREADS": "4"}, cores=32) == 4


def test_a_serial_pass_never_takes_fewer_than_the_lane():
    assert take_dq.judge_threads(False, {"VISURENA_LANE_THREADS": "6"}, cores=4) == 6


def test_an_unknown_core_count_counts_as_four():
    assert take_dq.judge_threads(False, {}, cores=None) == 2
