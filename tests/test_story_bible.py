"""`story.md`: the one file a fresh window reads to know what this episode is,
where it got to, and what was already decided.

From sw-workflow (screenwriting-skills), read 2026-09-12: keep project state in
one file so work resumes across sessions, and on resuming read only the current
stage, the settled decisions and the decision log -- then do NOT re-litigate a
settled decision unless the owner overturns it.

Ours splits the file in two halves for one reason: the facts (what stage, how
many takes, which paths) rot the moment anything runs, so they are REGENERATED
from disk; the judgement (what was settled, why, what is next) cannot be
derived from disk at all, so it is KEPT verbatim through every regeneration.
A generated file nobody trusts and a hand-written file nobody updates both fail;
this fails neither way.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import story_bible as sb

FACTS = {"title": "A Study in Scarlet — episode 1", "question": "Today, can Watson find rooms?",
         "stage": "8 takes", "lines": 23, "shots": 23, "seconds": 150.04,
         "takes_done": 14, "takes_total": 19,
         "master": "D:/library/.../master_iter5.mp4", "pages": ["takes.html", "sheets.html"]}


def test_a_new_bible_carries_the_facts_and_empty_places_for_the_judgement():
    text = sb.render(FACTS, kept={})
    assert "A Study in Scarlet" in text and "14 of 19" in text
    for heading in (sb.SETTLED, sb.DECISIONS, sb.NEXT):
        assert heading in text


def test_the_judgement_survives_a_regeneration():
    """The whole point: running the pipeline must not erase what was decided."""
    first = sb.render(FACTS, kept={})
    written = first.replace(sb.PLACEHOLDER, "- END pins removed 2026-09-11: a second pin says nothing changes.")
    later = sb.merge(written, {**FACTS, "takes_done": 19})
    assert "END pins removed 2026-09-11" in later and "19 of 19" in later


def test_the_facts_are_replaced_not_appended():
    later = sb.merge(sb.render(FACTS, kept={}), {**FACTS, "takes_done": 19})
    assert "14 of 19" not in later and later.count("19 of 19") == 1


def test_parse_returns_the_hand_written_sections_only():
    text = sb.render(FACTS, kept={}).replace(sb.PLACEHOLDER, "- decided a thing")
    kept = sb.parse(text)
    assert set(kept) == {sb.SETTLED, sb.DECISIONS, sb.NEXT}
    assert "decided a thing" in "".join(kept.values())


def test_a_decision_is_appended_with_its_date_and_its_reason():
    text = sb.render(FACTS, kept={})
    after = sb.decide(text, "2026-09-12", "MAX_FACES 2 -> 4", "faces said whose face must READ, not who is there")
    assert "2026-09-12" in after and "MAX_FACES 2 -> 4" in after
    assert "not who is there" in after


def test_decisions_accumulate_oldest_first():
    text = sb.decide(sb.render(FACTS, kept={}), "2026-09-11", "first thing", "because")
    text = sb.decide(text, "2026-09-12", "second thing", "because")
    assert text.index("first thing") < text.index("second thing")


def test_the_placeholder_goes_away_once_there_is_a_real_decision():
    text = sb.decide(sb.render(FACTS, kept={}), "2026-09-12", "a thing", "a reason")
    assert text.count(sb.PLACEHOLDER) == 1  # only the still-empty section keeps it


def test_the_next_line_is_one_line_and_always_last():
    text = sb.render(FACTS, kept={})
    assert text.rstrip().splitlines()[-1].startswith("-")
    assert text.index(sb.NEXT) > text.index(sb.DECISIONS)


def test_three_sentences_is_what_a_fresh_window_says_back():
    """The resume protocol: what it is, where it is, what was last decided."""
    text = sb.decide(sb.render(FACTS, kept={}), "2026-09-12", "dropped the gateway END panel", "a wide cannot show two paces")
    said = sb.restate(text)
    assert said.count(".") >= 3
    assert "A Study in Scarlet" in said and "14 of 19" in said and "gateway END" in said
