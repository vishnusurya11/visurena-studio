"""A check's gate version is pinned to its code's hash, so every edit of that code is a decision.

The verdict caches key on bytes + gate version (package H, retro 2026-10-20).  The cost of that
is a version nobody bumps: 2026-10-08, the fixed letterbox measure never reached ep21 because
the cache served the old refusals.  So this test fails on ANY edit of the code a check measures
or judges by, until the commit says which it is, in tests/fixtures/gate_pins.json:
  - a verdict or a recorded measure changed -> bump the script's GATE_VERSION and re-pin;
  - nothing a verdict says changed (a refactor, a log line, a cure) -> re-pin the hash only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_content_check  # noqa: E402
import take_dq  # noqa: E402

PINS = Path(__file__).parent / "fixtures" / "gate_pins.json"


def pin(name: str) -> dict:
    return json.loads(PINS.read_text(encoding="utf-8"))[name]


def moved(name: str, sha8: str, version: str) -> str:
    return (f"{name}'s code moved (pinned {pin(name)['code_sha8']}, now {sha8}). If a verdict or a recorded "
            f"measure changes, bump {name}.GATE_VERSION (now {version}); either way re-pin {PINS.name}.")


def test_take_dqs_measuring_code_is_pinned():
    now = take_dq.measures_sha8()
    assert pin("take_dq") == {"code_sha8": now, "gate_version": take_dq.GATE_VERSION}, \
        moved("take_dq", now, take_dq.GATE_VERSION)


def test_take_contents_judging_code_is_pinned():
    now = take_content_check.judges_sha8()
    assert pin("take_content_check") == {"code_sha8": now, "gate_version": take_content_check.GATE_VERSION}, \
        moved("take_content_check", now, take_content_check.GATE_VERSION)


def test_the_pinned_files_are_the_ones_that_judge():
    assert "studio/warp_gate.py" in take_dq.MEASURES and "studio/gait.py" in take_dq.MEASURES
    assert set(take_content_check.JUDGES) == {"scripts/episode/take_content_check.py", "studio/frames.py",
                                             "studio/take_content.py", "studio/panel_content.py",
                                             "studio/look_table.py", "studio/panel_dq.py", "studio/people_count.py",
                                             "studio/figure_who.py", "studio/ship_block.py",
                                             "studio/measure/ocr.py"}
