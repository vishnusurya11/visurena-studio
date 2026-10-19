"""The step order is one algorithm block in SKILL.md, generated from stages.yaml (P16).

The order was told three ways (the registry table, a 1-16 tools numbering ending "Step 16", the
autopilot table) and none said what runs next, what stops it and what it is capped at.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from studio import registry, step_caps

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "episode" / "SKILL.md"

spec = importlib.util.spec_from_file_location("ep_commands", ROOT / "scripts" / "episode" / "commands.py")
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def block() -> str:
    return commands.algorithm()


def test_the_skill_carries_the_algorithm_verbatim():
    assert commands.between(SKILL.read_text(encoding="utf-8"), "algorithm") == block()


def test_every_step_appears_in_registry_order():
    ids = [s["id"] for s in registry.steps("episode")]
    starts = [l.split()[0] for l in block().splitlines() if l[:2].isdigit()]
    assert starts == ids


def test_every_cap_row_appears_once_under_its_step():
    caps = [part.split()[0] for l in block().splitlines() if "caps:" in l
            for part in l.split("caps:", 1)[1].split(";")]
    assert caps == list(step_caps.table())


def test_the_skill_numbers_no_step_sixteen():
    assert "Step 16" not in SKILL.read_text(encoding="utf-8")
