"""OPERATOR.md answers a symptom with its cause and its act, says how a guard is derived, and caps the
agents that fix an owner-reported defect (deadline retro 2026-10-20, items 9, 10, 14).

ep01's record (docs/audit/2026-10-20_deadline_retro/RETRO.md; copied here as the facts the page must
carry, code never reads docs/audit/):
- three repair launches were stopped, each a symptom the next agent must recognise: every delivered take
  read stale (P03's words), the ladder retook frozen T01 (P08's round), and the operator's own guard
  killed the legal tiny-face draw because it waited for a line the rung prints AFTER its queueing line;
- 185 agents ran on the face chain with no budget: 11.2 h of agent building while the machine waited; in
  round 1 two of three builds moved nothing (the framing floor moved 0 of 12 plans), because nobody
  counted the defect before building; a 45 min cap would have killed the 151 min round that worked, so
  the cap is on rounds (2), not minutes.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "episode"
OPERATOR, SKILL = SKILL_DIR / "OPERATOR.md", SKILL_DIR / "SKILL.md"

SYMPTOMS = ("every delivered take reads stale", "a frozen take", "a guard killed", "REFUSED to start",
            "every unchanged take re-measured", "the pin test is red", "supervisor silent",
            "YouTube token", "HELD_PUBLISH", "repair X h of a Y h cap")
DEFECT = ("round 0", "predicts", "on the real ep01 files", "unproven half", "at most 2 fix rounds",
          "main session", "one research fleet", "2 build rounds", "3 h", "one-line stop", "docs/audit/")


def section(text: str, heading: str) -> str:
    assert f"\n## {heading}" in text, heading
    return text.split(f"\n## {heading}", 1)[1].split("\n## ", 1)[0]


def test_the_symptom_table_names_each_incident_with_its_cause_and_act():
    rows = [l for l in section(OPERATOR.read_text(encoding="utf-8"), "Symptoms").splitlines()
            if l.startswith("| ") and not l.startswith("| symptom") and not l.startswith("|---")]
    assert all(l.count(" | ") >= 2 for l in rows)
    assert [s for s in SYMPTOMS if not any(s in l for l in rows)] == []


def test_a_guard_is_derived_from_the_code_and_keys_on_bytes():
    guards = section(OPERATOR.read_text(encoding="utf-8"), "Guards")
    assert "print order" in guards and "bytes" in guards and "dry run" in guards


def test_an_owner_defect_counts_first_and_has_a_budget():
    defect = section(OPERATOR.read_text(encoding="utf-8"), "Fixing an owner-reported defect")
    assert [w for w in DEFECT if w not in defect] == []


def test_the_skill_sends_the_orchestrator_there_after_every_run():
    after = section(SKILL.read_text(encoding="utf-8"), "After every run: improve this skill")
    assert "Fixing an owner-reported defect" in after and "OPERATOR.md" in after
