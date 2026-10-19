"""The writer skill names what a refusal costs, by tier (Jekyll ep01 Kawajiri, 2026-10-18): the writer was
never told tier 1 must reach zero, that tier 2 is signed flagged after its rounds, or that tier 3
voice-measured rows are advice, and it chased G-TWO through five rounds.  The tier-1 labels are
`plan_tags.BUILDER`'s own, never retyped.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import plan_tags  # noqa: E402

SKILL = Path(__file__).resolve().parents[1] / "agents" / "skills" / "episode_writer.md"


def lines() -> list[str]:
    return SKILL.read_text(encoding="utf-8").splitlines()


def line_with(phrase: str) -> str:
    return next((l for l in lines() if phrase in l), "")


def test_tier_one_is_named_with_every_builder_label():
    line = line_with("Tier 1 refusals must reach zero")
    assert line and all(label in line for label in plan_tags.BUILDER)


def test_tier_two_gets_three_rounds_then_is_signed_flagged():
    line = line_with("Tier 2 refusals get three rounds")
    assert "signed flagged" in line and all(g in line for g in ("G-AIM", "G-LAID", "G-CROWD", "G-REACT"))


def test_tier_three_voice_measured_rows_are_advice():
    assert "voice-measured" in line_with("Tier 3") and "advice" in line_with("Tier 3")


def test_edit_the_previous_plan_changing_only_the_named_rows():
    line = line_with("Edit the previous plan")
    assert "only the rows" in line and "already fixed, keep fixed" in line


def test_the_setup_crowd_rule_and_the_gate_lines_are_there():
    text = "\n".join(lines())
    assert "rides only a shot that declares `extras` > 0" in text
    for needle in ("G-AIM:", "G-SYNC:", "G-CROWD", "G-LAID:", "without its body in the cell"):
        assert needle in text


def test_each_addition_is_one_line():
    for phrase in ("Tier 1 refusals", "Tier 2 refusals", "Tier 3", "Edit the previous plan", "G-AIM:", "G-SYNC:", "G-LAID:"):
        assert line_with(phrase).strip().startswith("- ")
