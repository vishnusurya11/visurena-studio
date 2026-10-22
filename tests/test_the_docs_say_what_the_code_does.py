"""A5: docstrings and the writer skill tell the truth (craft ruling 2026-10-21, wave 1).

`INNER_MAX_WORDS` is HARD in code (the Line validator raises), but its docstring said ADVISORY.
G-MOVES leaves held dialogue shots out of the quarter (`plan_gates.moves_faults`), and only the code
knew it: the skill said "no move on more than a quarter of the shots".  Whether the cap lets the book's
own 9-14 word thoughts through is owner question Q4; this changes no number.  No spend."""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from studio import episode_spec

SKILL = Path(__file__).resolve().parents[1] / "agents" / "skills" / "episode_writer.md"


def test_a_nine_word_inner_line_is_refused():
    with pytest.raises(ValidationError, match="a thought is at most 8"):
        episode_spec.Line(index=0, kind="inner", speaker="u", shot=0, text="If he be Mr. Hyde I shall be Seek.")


def test_the_inner_cap_is_documented_as_hard():
    source = inspect.getsource(episode_spec.Line)
    said = re.search(r"`inner`.*?INNER_MAX_WORDS[^.]*\.[^.]*\.", source, re.S).group(0)
    assert "HARD" in said and "ADVISORY" not in said


def test_the_skill_states_the_held_dialogue_exemption_of_the_move_share():
    text = re.sub(r"\s+", " ", SKILL.read_text(encoding="utf-8"))
    assert "no move on over a quarter of the shots (held dialogue shots uncounted)" in text
