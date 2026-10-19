"""The Step caps table in GATES.md is a view of stages.yaml `episode.caps`, never typed (P16).

It was typed by hand beside the registry; it was equal on 2026-10-18 and missed the `lines` row the
day P12 added it.  The counter rules the code now keeps sit under the table.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from studio import step_caps

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / ".claude" / "skills" / "episode" / "GATES.md"

spec = importlib.util.spec_from_file_location("ep_commands", ROOT / "scripts" / "episode" / "commands.py")
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def caps_section() -> str:
    text = GATES.read_text(encoding="utf-8")
    return text.split("## Step caps", 1)[1].split("\n## ", 1)[0]


def test_the_gates_carry_the_cap_table_verbatim():
    assert commands.between(GATES.read_text(encoding="utf-8"), "caps") == commands.caps_table()


def test_every_cap_row_of_the_registry_is_a_row_in_file_order():
    rows = commands.caps_table().splitlines()[2:]
    assert [r.split("|")[2].strip() for r in rows] == list(step_caps.table())


def test_a_climb_row_says_how_many_climbs():
    plan = next(r for r in commands.caps_table().splitlines() if "| plan |" in r)
    assert "climb (2 climbs per episode)" in plan


def test_the_wall_is_minutes_from_the_registry():
    lines_row = next(r for r in commands.caps_table().splitlines() if "| lines |" in r)
    assert f"| {int(step_caps.wall_s('lines') // 60)} |" in lines_row


def test_the_counter_rules_stand_under_the_table():
    section = caps_section()
    for rule in ("per episode", "attempts.json", "wall.<id>", "120 min", "CAP ", "a round is a change of bytes"):
        assert rule.lower() in section.lower(), rule
