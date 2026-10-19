"""The live card's client keeps polling and patches the honest timeline (page experts
2026-10-18, D1 + A1/A2): progress.js run once under node against the page double in
`tests/live_card_dom.js`.  A swap whose partial answers empty or fails returned without
scheduling the next poll, so the card froze while its clock ticked on; a quiet poll now
patches the episode finish, the step's end and each later step's window.  $0."""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
JS = TESTS.parent / "studio" / "command_center" / "static" / "progress.js"
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


@pytest.fixture(scope="module")
def report() -> dict:
    out = subprocess.run([NODE, str(TESTS / "live_card_dom.js"), str(JS)], capture_output=True, timeout=60)
    assert out.returncode == 0, out.stderr.decode("utf-8", "replace")
    return {c["name"]: c for c in json.loads(base64.b64decode(out.stdout).decode("utf-8"))["checks"]}


def passed(report: dict, *names: str) -> None:
    for name in names:
        assert name in report, f"the harness never ran {name!r}"
        assert report[name]["pass"], f"{name}: got {report[name]['got']!r}"


def test_a_swap_that_lands_nothing_still_schedules_the_next_poll(report):
    passed(report, "the card schedules its first poll", "an empty partial still schedules the next poll",
           "a failed partial still schedules the next poll", "the harness ran to the end")


def test_a_quiet_poll_patches_the_episode_finish_the_step_end_and_the_windows(report):
    passed(report, "a quiet poll patches the episode finish", "a quiet poll patches the step end",
           "a quiet poll patches a later window", "a quiet poll schedules the next")


def test_a_quiet_poll_patches_the_time_left_the_range_and_the_finished_steps(report):
    # owner 2026-10-18: "time left ... also display time on finished events"
    passed(report, "a quiet poll patches the time left", "a quiet poll patches the range",
           "a quiet poll patches a finished step")
