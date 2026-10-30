"""Every G-WHO rule change replays the eye-judged pictures before it lands (Jekyll ep06 retro B, 2026-10-29).

The fair-vs-grey fix (f5631245) was tested on hand-written cases and hid exactly the double it later met:
panel 25's Utterson drawn where Poole stands.  Each tests/fixtures/who_reads_*.json holds real reads of judged
pictures (scripts/audit/who_fixture.py) with the eye's answer; every one must still come out the eye's way."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import figure_who as fw

FIXTURES = sorted((Path(__file__).parent / "fixtures").glob("who_reads_*.json"))
CASES = [(f.stem, t) for f in FIXTURES for t in json.loads(f.read_text(encoding="utf-8"))["takes"]]


def fired(case: dict) -> bool:
    """A panel (one read) fires on any frame; a take (`kind: take`) only when take_content_check.CONFIRM of its
    read frames do (ep06 T23 run 22: one wide frame of four misread a hat)."""
    from scripts.episode.take_content_check import CONFIRM
    staged = {who: fw.staged_marks(row["markers"], row["top"]) for who, row in case["cast"].items()}
    hits = sum(1 for figs in case["frames"] if fw.fault(figs, staged))
    return hits >= (CONFIRM if case.get("kind") == "take" else 1)


def test_there_is_a_calibration_set():
    assert len(FIXTURES) >= 1 and len(CASES) >= 5


@pytest.mark.parametrize("case", [c for _, c in CASES], ids=[f"{s}:{c['take']}" for s, c in CASES])
def test_every_eye_judged_picture_still_reads_the_eyes_way(case):
    assert fired(case) == case["double_by_eye"]
