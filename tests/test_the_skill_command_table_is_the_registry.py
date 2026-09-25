"""The episode skill is the desk over the runner: its command table is a view of
stages.yaml.  If the registry changes and the desk is not regenerated, this
fails, so the two cannot drift apart the way the skill's prose chain did."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "episode" / "SKILL.md"

spec = importlib.util.spec_from_file_location("ep_commands", ROOT / "scripts" / "episode" / "commands.py")
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def test_the_skill_carries_the_registry_table_verbatim():
    text = SKILL.read_text(encoding="utf-8")
    assert commands.between(text, "episode") == commands.table("episode")


def test_every_registered_episode_step_is_a_row():
    rows = commands.table("episode").splitlines()[2:]
    assert [r.split("|")[1].strip() for r in rows] == [f"{n:02d}" for n in range(1, 13)]


def test_the_table_names_the_module_a_step_runs_alone_with():
    assert "scripts/episode/step_04_record.py <book> <n>" in commands.table("episode")


def test_render_into_replaces_only_between_the_markers():
    text = "before\n<!-- registry:episode -->\nold\n<!-- /registry:episode -->\nafter"
    out = commands.render_into(text, "episode", "new")
    assert out == "before\n<!-- registry:episode -->\nnew\n<!-- /registry:episode -->\nafter"
