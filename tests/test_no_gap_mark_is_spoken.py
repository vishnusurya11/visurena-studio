"""A6: no gap mark in spoken text (craft ruling 2026-10-21, wave 1).

The Jekyll screenplay cut the narrator's tag out of a quote and left its gap mark:
"If he be Mr. Hyde, … I shall be Mr. Seek." (the book: "If he be Mr. Hyde," he had thought, "I shall be
Mr. Seek.").  TTS reads the mark as a pause the book never had.  A `…` in a line is a CONTRACT fault,
and its cure strips the mark for free.  The book's own ASCII "..." (WotW ep26 "I knew... I knew...")
is not this mark and still passes.  No render, no network, no spend."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from studio import episode_spec, plan_cures

SEEK = "If he be Mr. Hyde, … I shall be Mr. Seek."


def line(text: str) -> episode_spec.Line:
    return episode_spec.Line(index=3, kind="dialogue", speaker="u", shot=0, text=text)


def test_the_screenplays_gap_mark_is_a_contract_fault():
    with pytest.raises(ValidationError, match="line 3 carries a gap mark"):
        line(SEEK)


def test_the_books_own_three_dots_still_pass():
    assert line("I came. I knew... I knew...").text.endswith("...")


def test_the_cure_gives_the_line_without_the_mark():
    doc = {"lines": [{"index": 3, "text": SEEK}, {"index": 4, "text": "I knew…"}]}
    cured = plan_cures.strip_gap_marks(doc)
    assert [l["text"] for l in cured["lines"]] == ["If he be Mr. Hyde, I shall be Mr. Seek.", "I knew."]


def test_the_contract_row_routes_to_the_free_cure():
    assert plan_cures.cure_for("CONTRACT: lines.3 :: line 3 carries a gap mark (…); say it whole") == "strip_gap_marks"


def test_plan_repair_applies_it(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import plan_repair
    doc, uncured, names = plan_repair.apply({"lines": [{"index": 3, "text": SEEK}]},
                                            ["CONTRACT: lines.3 :: line 3 carries a gap mark (…)"], tmp_path, llm=False)
    assert doc["lines"][0]["text"] == "If he be Mr. Hyde, I shall be Mr. Seek." and not uncured
    assert names == ["strip_gap_marks"]
