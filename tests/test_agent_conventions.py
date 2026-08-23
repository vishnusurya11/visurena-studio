"""Convention tests: EVERY agent must go through the gateway and return structured output.

These are guardrails on the codebase itself — an agent that imports strands directly
or skips llm.structured() would silently escape the structured-output guarantee.
"""

from __future__ import annotations

from pathlib import Path

AGENT_FILES = [p for p in Path("agents").glob("*.py")
               if p.name != "__init__.py" and not p.name.startswith("_")]


def test_agents_exist():
    assert AGENT_FILES  # the scan below must actually scan something


def test_no_agent_imports_strands_directly():
    for path in AGENT_FILES:
        source = path.read_text(encoding="utf-8")
        assert "strands" not in source, (
            f"{path.name} imports strands directly — all calls go through studio.llm")


def test_every_agent_declares_tier_and_uses_gateway():
    for path in AGENT_FILES:
        source = path.read_text(encoding="utf-8")
        assert "TIER = " in source, f"{path.name} missing TIER declaration"
        assert "llm.structured(" in source, (
            f"{path.name} never calls llm.structured — structured output not guaranteed")


def test_every_agent_has_a_skill_file():
    for path in AGENT_FILES:
        skill = Path("agents/skills") / f"{path.stem}.md"
        assert skill.exists(), f"{path.name} has no skill file at {skill}"
