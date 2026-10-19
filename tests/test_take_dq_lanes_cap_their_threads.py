"""A take_dq lane runs beside the GPU render; torch and OpenCV each default to every core and
starved the render (P07 item 9).  Each lane caps both at VISURENA_LANE_THREADS (default 2)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_dq  # noqa: E402


def test_the_default_is_two_threads():
    assert take_dq.lane_threads({}) == 2


def test_the_setting_overrides_it():
    assert take_dq.lane_threads({"VISURENA_LANE_THREADS": "4"}) == 4


def test_a_bad_or_zero_setting_falls_back_to_two():
    assert take_dq.lane_threads({"VISURENA_LANE_THREADS": "x"}) == 2
    assert take_dq.lane_threads({"VISURENA_LANE_THREADS": "0"}) == 2


def test_both_libraries_are_capped():
    seen = {}
    torch = SimpleNamespace(set_num_threads=lambda n: seen.update(torch=n))
    cv2 = SimpleNamespace(setNumThreads=lambda n: seen.update(cv2=n))
    assert take_dq.cap_threads(3, torch, cv2) == 3
    assert seen == {"torch": 3, "cv2": 3}


def test_the_render_seconds_of_a_take_are_a_log_line():
    assert take_dq.render_line(7, 12.34) == "T07 measured in 12 s"
