"""The operator's acts on a live run have one home: OPERATOR.md beside the skill (P16; moved there by
the deadline retro 2026-10-20, item 14).

On Jekyll Kawajiri ep01 every operating act (a recorded plan_repair cure, the owner_order_2_27 plan
edit, a ruler fault fixed test-first, a pause to land a fix) was improvised and logged by hand in a
RUNLOG; the agent file had no table for it.  On the ep01 repair the protocol sat in four places (a SKILL
bullet, a GATES paragraph, a LESSONS brick, three archive sections) and the agent who launched at 11:18
had two of them.  So the protocol has one page, SKILL and the agent file point at it, and neither keeps
a copy.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "episode"
SKILL, GATES, OPERATOR = SKILL_DIR / "SKILL.md", SKILL_DIR / "GATES.md", SKILL_DIR / "OPERATOR.md"
AGENT = ROOT / ".claude" / "agents" / "episode.md"

VERBS = ("autopilot.py pause --at-boundary", "paused_at_boundary", "resume", "retry N",
         "plan_repair", "plan.cures.jsonl", "owner_order", "plan_check.py <book> <n> --plan=",
         "ruler", "inputs: all N takes current", "CAP",
         "--by retro", "may-commit", "code_moved_during_run", "RELAUNCH on moved code", "HELD_PUBLISH",
         "repair_dry_check", "REFUSED to start: the dry check", "regress_delivered.py",
         "youtube_auth.py --paste=", "schtasks /run /tn visurena-autopilot")


def page() -> str:
    return OPERATOR.read_text(encoding="utf-8")


def test_the_page_names_every_operator_verb():
    assert [v for v in VERBS if v not in page()] == []


def test_the_report_line_leads_with_the_master_path():
    assert "report line" in page() and "full path" in page()


def test_the_skill_and_the_agent_file_point_at_the_page():
    assert "OPERATOR.md" in SKILL.read_text(encoding="utf-8")
    assert "OPERATOR.md" in AGENT.read_text(encoding="utf-8")


def test_the_skill_and_the_gates_keep_no_copy_of_the_protocol():
    skill = SKILL.read_text(encoding="utf-8")
    assert "## Operating a live run" not in skill and "## Resuming" not in skill
    assert "| land a fix |" not in skill
    repair = GATES.read_text(encoding="utf-8").split("- **Repair clock", 1)[1].split("\n- **", 1)[0]
    assert "OPERATOR.md" in repair
