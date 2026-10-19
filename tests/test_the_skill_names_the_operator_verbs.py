"""The operator's acts on a live run have one home: SKILL "Operating a live run" (P16).

On Jekyll Kawajiri ep01 every operating act (a recorded plan_repair cure, the owner_order_2_27 plan
edit, a ruler fault fixed test-first, a pause to land a fix) was improvised and logged by hand in a
RUNLOG; the agent file had no table for it.  The agent file points at the section, never copies it.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "episode" / "SKILL.md"
AGENT = ROOT / ".claude" / "agents" / "episode.md"

VERBS = ("autopilot.py pause --at-boundary", "paused_at_boundary", "resume", "retry N",
         "plan_repair", "plan.cures.jsonl", "owner_order", "plan_check.py <book> <n> --plan=",
         "ruler", "inputs: all N takes current", "CAP")


def section() -> str:
    text = SKILL.read_text(encoding="utf-8")
    assert "## Operating a live run" in text
    return text.split("## Operating a live run", 1)[1].split("\n## ", 1)[0]


def test_the_section_names_every_operator_verb():
    missing = [v for v in VERBS if v not in section()]
    assert missing == []


def test_the_report_line_leads_with_the_master_path():
    assert "report line" in section() and "full path" in section()


def test_the_agent_file_points_at_the_section():
    assert "Operating a live run" in AGENT.read_text(encoding="utf-8")
