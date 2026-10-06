"""The micro-line agent: a FakeCaller through studio.llm's `_agent` seam is
the only callable -- ZERO network, no paid API.  The schema refuses 7 and 15
words, parentheses and a trailing '!'; the book-grounded post-checks
(lifted_run over QUOTE_WALL, a pace word) re-ask exactly once with the
refusal quoted, then give up."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from strands.types.exceptions import StructuredOutputException

from agents import line_filler as lf
from studio import llm

BOOK = ("the lamp burned low upon the table and the wind cried against the "
        "shutters of the old house while we waited for the bell")
LIFT = "the lamp burned low upon the table and the wind"        # 10 words, verbatim
CLEAN = "I felt the cold reach through every seam of my coat"   # 11 words, paraphrase
SHOT = {"index": 7, "size": "wide", "frame": "an empty lane", "motion": "mist drifts",
        "why": "the wait before the knock"}


class FakeCaller:
    def __init__(self, answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, prompt, structured_output_model=None):
        self.prompts.append(prompt)
        return SimpleNamespace(structured_output=self.answers.pop(0))


def call_fill(caller):
    return lf.fill(SHOT, "He waited in the lane.", "prev line", "next line",
                   6.2, BOOK, _agent=caller)


def test_a_clean_answer_comes_back_in_one_call():
    caller = FakeCaller([lf.MicroLine(text=CLEAN)])
    assert call_fill(caller) == CLEAN
    assert len(caller.prompts) == 1
    assert "6.2 second" in caller.prompts[0] and "shot 7" in caller.prompts[0]


def test_an_over_wall_lift_is_re_asked_once_with_the_refusal():
    caller = FakeCaller([lf.MicroLine(text=LIFT), lf.MicroLine(text=CLEAN)])
    assert call_fill(caller) == CLEAN
    assert len(caller.prompts) == 2
    assert llm.REFUSED in caller.prompts[1]                     # the refusal is quoted back


def test_a_second_bad_answer_gives_up_and_stays_creative():
    caller = FakeCaller([lf.MicroLine(text=LIFT), lf.MicroLine(text=LIFT)])
    assert call_fill(caller) is None
    assert len(caller.prompts) == 2                             # ONE re-ask, never a loop


def test_a_schema_refusal_climbs_llm_structureds_own_ladder():
    seven = {"text": "seven words only sit right here now"}
    caller = FakeCaller([seven, seven, seven])
    with pytest.raises(StructuredOutputException):
        call_fill(caller)
    assert len(caller.prompts) == 3                             # the ladder's retries, then raise


@pytest.mark.parametrize("bad", [
    "seven words only sit right here now",                      # 7 words
    "fifteen words in a row is one word too many for a micro line to carry",  # 15
    "I saw the brother (grey eyes) waiting at the long dark gate",
    "I heard the bell ring out across the empty frozen lane!",
])
def test_the_schema_refuses_the_banned_shapes(bad):
    with pytest.raises(ValidationError):
        lf.MicroLine(text=bad)


def test_the_post_checks_name_the_lift_and_the_pace_word():
    assert any("consecutive words" in w for w in lf.refusals(LIFT, BOOK))
    assert any("pace word" in w
               for w in lf.refusals("I walked slowly down the long dark empty lane", BOOK))
    assert lf.refusals(CLEAN, BOOK) == []
