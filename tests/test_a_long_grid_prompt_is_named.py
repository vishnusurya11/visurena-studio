"""A grid prompt over 350 words is named, never refused (craft ruling A22).

ep01's drawn grid prompts ran 408-1,064 words (median 470) while Qwen's own prompt rewriter writes under 200;
the 1,000-token refusal was rejected as an unmeasured vendor number, so the length is a warning only.
Fixtures: tests/fixtures/craft/grids/ (ep01 night_door 2x2, 1,064 words; s09, 521; a 350-word cut of it)."""
from __future__ import annotations

from pathlib import Path

from studio import grid_lint

GRIDS = Path(__file__).parent / "fixtures" / "craft" / "grids"


def said(name: str) -> str:
    return (GRIDS / f"{name}.txt").read_text(encoding="utf-8")


def long_rows(text: str) -> list[str]:
    return [w for w in grid_lint.warnings(text) if w.startswith("LONG")]


def test_the_night_door_grid_warns_its_length():
    rows = long_rows(said("ep01_grid_night_door_2x2"))
    assert len(rows) == 1 and "1064 words" in rows[0] and "350" in rows[0]


def test_a_prompt_at_the_line_says_nothing():
    assert long_rows(" ".join(said("ep01_grid_night_corner_1x1_s09").split()[:350])) == []


def test_a_long_prompt_is_never_a_fault():
    assert not [f for f in grid_lint.faults(said("ep01_grid_night_door_2x2")) if "LONG" in f or "words" in f]
