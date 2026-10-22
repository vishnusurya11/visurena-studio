"""The writer's brief carries the shot framework (shot framework B-6, 2026-10-21).

`plan_brief.camera_catalog()` reads docs/calibration/camera_catalog.md whole into the brief, so the
framework's adopted rows (A1 rise, A2 pull reveal, A3 follow, A4 stride insert, A5 reaction close, A7
insert rise), the path column (F8) and the retired push cure reach the writer in the file it already
reads.  A wall the writer is not told costs a ladder rung."""
from __future__ import annotations

from studio import plan_brief


def section() -> str:
    text = plan_brief.camera_catalog() or ""
    assert "## The shot framework" in text
    return text.split("## The shot framework", 1)[1].split("\n## ", 1)[0]


def test_brief_names_the_rise_and_follow_rules():
    said = section()
    for row in ("A1", "A2", "A3", "A4", "A5", "A7"):
        assert f"| {row} |" in said, row
    assert "crane_up" in said and "top third" in said and "no dialogue" in said.lower()
    assert "side-on or from behind" in said and "toward the lens" in said


def test_brief_says_a_push_is_no_cure():
    said = section()
    assert "a push is no freeze cure" in said.lower()
    assert "G-HOLD" in said and "G-RISE" in said


def test_every_framework_row_names_its_path():
    said = section()
    assert "Kawajiri panel" in said and "distinct-cell n" in said
