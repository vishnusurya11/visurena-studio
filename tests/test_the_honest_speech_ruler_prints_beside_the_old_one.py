"""A16: the speech ruler, measured honestly, printed beside the old one (craft ruling 2026-10-21, wave 1).

`plan_gates.QUOTED` stops at 600 characters, so ch1's long Enfield tale (paragraph 7, 841 quoted words)
is not counted: the old ruler reads ch1 at 0.279 against a quoted share near two thirds.  The honest
ruler has no cap and does not count a quote whose own tag says it was THOUGHT ("If he be Mr. Hyde," he
had thought), even when it opens a paragraph.  The dial's floor and ceiling follow the ruler, so the
switch is the owner's (Q1): today both are printed, and `speech_share` is unchanged.
Fixtures: tests/fixtures/craft (Jekyll ch_01, ch_02).  No spend."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import speech_ruler
from studio import plan_brief, plan_gates

BOOK = Path(__file__).parent / "fixtures" / "craft"


def chapter(n: int) -> list[str]:
    doc = json.loads((BOOK / "source" / "chapters" / f"ch_{n:02d}.json").read_text(encoding="utf-8"))
    return [p["text"] for p in doc["paragraphs"]]


def test_ch1_old_and_new_shares_are_both_pinned():
    assert plan_gates.speech_share(chapter(1)) == 0.279
    assert plan_gates.honest_speech_share(chapter(1)) == 0.628


def test_a_thought_is_not_speech_even_when_it_opens_a_paragraph():
    thought = ["“If he be Mr. Hyde,” he had thought, and walked on past the door."]
    said = ["“If he be Mr. Hyde,” he said, and walked on past the door."]
    assert plan_gates.honest_speech_share(thought) == 0.0
    assert plan_gates.honest_speech_share(said) > 0.0


def test_a_said_tag_that_later_thinks_is_still_speech():
    # wave 1 review, finding 8: the 40-character tag window saw "thought" after "said he" and dropped it
    assert plan_gates.honest_speech_share(["“Yes,” said he, and thought no more of it."]) > 0.0


def test_a_long_quote_counts_whole():
    long = ["“" + " ".join(["word"] * 200) + ".” said he."]
    assert plan_gates.speech_share(long) == 0.0 and plan_gates.honest_speech_share(long) > 0.95


def test_the_dial_still_reads_the_old_ruler_until_the_owner_switches():
    assert plan_brief.dialogue_band(BOOK, 1) == [0.05, 0.35]


def test_the_table_prints_old_beside_new_for_every_chapter():
    rows = speech_ruler.table(BOOK)
    assert [r[0] for r in rows] == [1, 2]
    assert rows[0][1:] == (0.279, 0.628)
    assert speech_ruler.line(rows[0]) == "ch01  old 0.279  new 0.628"
