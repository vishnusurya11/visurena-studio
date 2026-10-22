"""Wave 1 review finding 6: only a gap mark the book does not have is a fault (craft ruling A6).

The ruling refuses "a `…` that the book does not have".  The Line validator refused every U+2026, so a
book whose own text uses the mark would have every verbatim line refused, stripped, and then failed by
the verbatim quote checks.  The check now sits on the Episode: `book_gap_mark` (set from the chapter by
`plan_gates.at_series_rate`, beside the series rate) says the book's own text uses the mark, and then a
line may carry it.  The strip cure also closes the gap it leaves before punctuation ("Wait …, I go."
read "Wait , I go.").  Fixtures: tests/fixtures/craft (Jekyll ep01 plan.json, ch_01).  No spend."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from studio import episode_spec, plan_cures, plan_gates

CRAFT = Path(__file__).parent / "fixtures" / "craft"


def plan(mark: str = "Did you ever … remark that door?") -> dict:
    doc = json.loads((CRAFT / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8"))
    line = next(l for l in doc["lines"] if l["index"] == 3)
    line["text"] = mark
    return doc


def test_a_gap_mark_the_book_lacks_is_a_contract_fault():
    with pytest.raises(ValidationError, match="line 3 carries a gap mark"):
        episode_spec.Episode(**plan())


def test_a_gap_mark_the_book_uses_is_spoken():
    assert episode_spec.Episode(**{**plan(), "book_gap_mark": True}).book_gap_mark is True


def test_jekyll_ch1_does_not_use_the_mark():
    assert plan_gates.at_series_rate(plan(), CRAFT, 1)["book_gap_mark"] is False


def test_a_chapter_that_uses_the_mark_lets_its_lines_carry_it(tmp_path):
    chapters = tmp_path / "source" / "chapters"
    chapters.mkdir(parents=True)
    (chapters / "ch_01.json").write_text(json.dumps({"paragraphs": [{"text": "“Wait … I go.”"}]}),
                                         encoding="utf-8")
    doc = plan_gates.at_series_rate(plan(), tmp_path, 1)
    assert doc["book_gap_mark"] is True and episode_spec.Episode(**doc)


def test_the_strip_leaves_no_gap_before_punctuation():
    doc = {"lines": [{"index": 0, "text": "Wait …, I go."}, {"index": 1, "text": "No …! Not now…"}]}
    assert [l["text"] for l in plan_cures.strip_gap_marks(doc)["lines"]] == ["Wait, I go.", "No! Not now."]
