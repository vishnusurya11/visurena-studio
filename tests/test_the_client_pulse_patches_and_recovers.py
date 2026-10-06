"""The client half of the refresh fix (board refresh brief, row A2): pulse.js's
PAGE script -- not just its pure core -- run once under node against the DOM
double in `tests/board_pulse_dom.js`.  It must fire `pulse:<key>` for exactly
the changed fingerprints, patch the shell in place (badges, dots, pins, GPU
card, title, heartbeat chip, held bar), ride the `since` cursor, land `data-v`
on 200 AND on 204, keep a '·' label intact, and -- the owner's complaint --
never die: a failing fetch backs off and recovers, and an error thrown while
handling a pulse still schedules the next one.  Skipped where node is not
installed; it spends nothing."""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
PULSE = TESTS.parent / "studio" / "command_center" / "static" / "pulse.js"
HARNESS = TESTS / "board_pulse_dom.js"
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


@pytest.fixture(scope="module")
def report() -> dict:
    """The harness's checks by name, from one node run of the real pulse.js."""
    out = subprocess.run([NODE, str(HARNESS), str(PULSE)], capture_output=True, timeout=60)
    assert out.returncode == 0, out.stderr.decode("utf-8", "replace")
    body = json.loads(base64.b64decode(out.stdout).decode("utf-8"))
    return {c["name"]: c for c in body["checks"]}


def passed(report: dict, *names: str) -> None:
    for name in names:
        assert name in report, f"the harness never ran {name!r}"
        assert report[name]["pass"], f"{name}: got {report[name]['got']!r}"


def test_the_first_pulse_fires_every_section_and_a_quiet_pulse_fires_none(report):
    passed(report, "first pulse fires every key", "only the changed key fires", "a quiet pulse fires nothing")


def test_the_shell_is_patched_in_place(report):
    passed(report, "needs badge patched and washed", "queue count patched", "dept dot drawn",
           "dept speaks its dots", "pin appears", "gpu card runs", "gpu progress drawn",
           "title goes live", "chip reads live")


def test_a_pin_label_keeps_its_middle_dot(report):
    passed(report, "pin label keeps its middle dot", "pin splits id from the rest")


def test_the_since_cursor_rides_every_poll(report):
    passed(report, "second poll carries since=7", "third poll carries since=9")


def test_a_pulse_fired_request_carries_v_and_lands_data_v(report):
    passed(report, "request carries the drawn v", "200 lands data-v", "the changed row washes",
           "204 lands data-v too")


def test_a_failing_fetch_backs_off_and_recovers(report):
    passed(report, "a bad answer backs off", "a good answer recovers the chip")


def test_a_patch_error_never_kills_the_heartbeat(report):
    passed(report, "a patch error still schedules the next pulse", "the loop goes on after the error",
           "no promise leaks from the loop")


def test_a_held_studio_reaches_the_bar_the_card_and_the_title(report):
    passed(report, "held bar shows and reads local time", "held card never says idle", "held title")
