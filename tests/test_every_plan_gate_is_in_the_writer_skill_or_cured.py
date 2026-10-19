"""Every gate the plan battery can print is either stated in the writer skill or has a free cure
(Jekyll ep01 Kawajiri, 2026-10-18: 34 of 61 gate ids were in neither; G-TWO, G-PRESENT, G-CROWD, G-LAID, G-ORDER,
G-SYNC, G-HOLE and G-AIM persisted through five writer rounds because nothing told the writer the rule).

ABSENT is the allowlist of ids that are in neither today.  It may only SHRINK: a new gate must arrive
stated or cured, and a gate that gets a line or a cure is struck from this list.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import plan_cures  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "agents" / "skills" / "episode_writer.md"
GATE_ID = re.compile(r"""["'](G-[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*)\b""")

ABSENT = {"G-BANNED-PROP", "G-CURE-VERIFY", "G-DIAL", "G-FIRSTFRAME", "G-FULL", "G-HAT", "G-NAMES", "G-ORDER",
          "G-PRESENT-WIDE", "G-PROPCARD", "G-RATE", "G-READER", "G-ROWTEXT", "G-TAKELINT", "G-VARIETY"}


def battery_ids() -> set[str]:
    studio = ROOT / "studio"
    files = sorted(studio.glob("plan_*.py")) + [studio / "judges" / "plan.py", ROOT / "scripts" / "episode" / "plan_check.py",
                                                studio / "cell_gates.py", studio / "framing_grammar.py", studio / "move_rebalance.py"]
    return {i for f in files for i in GATE_ID.findall(f.read_text(encoding="utf-8"))}


def named(gate: str, skill: str) -> bool:
    return re.search(re.escape(gate) + r"(?![A-Z0-9-])", skill) is not None


def cured(gate: str) -> bool:
    return any(gate in pattern.pattern for pattern, _ in plan_cures.CURES)


def unstated() -> set[str]:
    skill = SKILL.read_text(encoding="utf-8")
    return {g for g in battery_ids() if not named(g, skill) and not cured(g)}


def test_the_battery_names_the_gates_the_ep01_climbs_chased():
    ids = battery_ids()
    assert {"G-TWO", "G-PRESENT", "G-CROWD", "G-LAID", "G-SYNC", "G-AIM", "G-HOLE"} <= ids


def test_every_gate_is_stated_or_cured_or_on_the_shrinking_allowlist():
    assert unstated() <= ABSENT, f"a gate arrived neither stated nor cured: {sorted(unstated() - ABSENT)}"


def test_the_ep01_chased_gates_are_stated_in_the_skill():
    skill = SKILL.read_text(encoding="utf-8")
    assert all(named(g, skill) for g in ("G-AIM", "G-SYNC", "G-CROWD", "G-LAID", "G-PRESENT", "G-TWO"))
