"""An owner ruling retires a sentence, and the sentence must go (Jekyll Kawajiri ep01 retro, P16).

At HEAD 6572728 five sentences an agent reads first were false: "Only the owner waives", the face
paste "after the 4x", "or ask the owner", G-DEAD's "never a flagged ship" and "Resume with
`drive.py`".  Two of them would have made the next agent refuse a cut the owner approved or undo an
owner order.  The phrases live in a data file; a ruling that retires one adds it in its own commit.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "fixtures" / "ep01_replay" / "P16" / "retired_phrases.json"
SKILL = ROOT / ".claude" / "skills" / "episode" / "SKILL.md"


def retired() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def text_of(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_no_retired_phrase_stands_in_the_skill_the_gates_the_lessons_or_the_agent():
    data = retired()
    found = [(row["phrase"], rel) for rel in data["files"] for row in data["retired"]
             if row["phrase"] in text_of(rel)]
    assert found == []


def test_a_terminal_is_not_a_pass_is_kept():
    assert all(kept in SKILL.read_text(encoding="utf-8") for kept in retired()["kept"])


def test_the_publish_row_publishes_only_when_the_owner_asks():
    row = next(l for l in SKILL.read_text(encoding="utf-8").splitlines() if l.startswith("| 13 | Publish"))
    assert "only when the owner asks" in row


def test_rule_five_says_who_clears_a_terminal():
    rule = SKILL.read_text(encoding="utf-8").split("5. **A terminal is not a pass.**", 1)[1].split("\n6. ", 1)[0]
    assert "judge-signed" in rule and "hand-waived" in rule
