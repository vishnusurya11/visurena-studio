"""A13: the tease spec can be satisfied (craft ruling 2026-10-21, wave 1).

The skill asked for "the NEXT chapter's first image", but the writer never receives chapter N+1, and
G-SOURCE checks a tease's spans against the NEXT chapter: 0 of 30 plans managed one.  The bullet now asks
for a tease only from the NEXT CHAPTER rows when the brief gives them (supplying the rows is arm 4 of
T4), and `tease_advisories` on a brief with no such rows says "tease not asked", never a fault.  The
bullet is no longer than it was.  No render, no network, no spend."""
from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

from studio import screenplay_grammar as sg

SKILL = Path(__file__).resolve().parents[1] / "agents" / "skills" / "episode_writer.md"
OLD_BULLET_BYTES = 193
"""The bullet at HEAD before A13: '- Optional TEASE: one last shot, ... name that image in `tease`.'"""


def plan(with_tease: bool):
    shots = [SimpleNamespace(index=0, setup="door", section="hook"),
             SimpleNamespace(index=1, setup="door", section="tease" if with_tease else "button")]
    return SimpleNamespace(shots=shots, omit=[], tease="the key in the lock" if with_tease else "",
                           setups={"door": SimpleNamespace(location="door")})


def test_a_tease_with_no_next_chapter_rows_is_not_asked_never_a_fault():
    said = sg.tease_advisories(plan(True))
    assert said == ["G-TEASE: tease not asked (the brief gave no NEXT CHAPTER rows); advisory, never a fault"]


def test_with_next_chapter_rows_the_tease_is_read_as_before():
    assert sg.tease_advisories(plan(True), next_rows=["Mr. Hyde has a key."]) == []


def test_no_tease_shot_says_nothing():
    assert sg.tease_advisories(plan(False)) == []


def bullet() -> str:
    text = SKILL.read_text(encoding="utf-8").replace("\r\n", "\n")
    return re.search(r"- Optional TEASE.*?`tease`\.", text, re.S).group(0)


def test_the_skill_asks_for_a_tease_only_from_the_rows_and_spends_no_bytes():
    said = bullet()
    assert "only from the NEXT CHAPTER rows when the brief gives them" in re.sub(r"\s+", " ", said)
    assert "first\n  image" not in said and len(said.encode("utf-8")) <= OLD_BULLET_BYTES
