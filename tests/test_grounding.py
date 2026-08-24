"""Grounding: a quote is grounded when the TEXT SAYS THOSE WORDS, in that order.

Audit 2026-08-23. The check demanded an exact normalized substring and reported 316
violations on a book with no fabricated quotes in it. 285 of them (90%) were 100%
present in their own scene and differed only in typography — a closing quote mark the
agent added, a dialogue comma rendered as a full stop, a long passage elided with "...",
or the two halves of a split quotation ('"...," he said, "..."') rejoined.

Under the noise sat real findings, including the two quotes that produced today's
`clock-reversed` timeline contradiction — attributed to a scene whose paragraphs do not
contain them. A check that fires 316 times where two dozen matter is a check nobody
reads. (It never gated the stage, so nothing downstream was blocked by it — it was
simply noise where a signal was needed.)
"""

from __future__ import annotations

from scripts.analysis import step_02_extract as s02

SCENE = ('\u201cIt is not easy to express the inexpressible,\u201d he answered with a '
         'laugh. \u201cHolmes is a little too scientific for my tastes\u2014it approaches '
         'to cold-bloodedness. I could imagine his giving a friend a little pinch of '
         'the latest vegetable alkaloid.\u201d '
         '\u201cLecoq was a miserable bungler,\u201d he said, in an angry voice.')


def grounded(quote):
    return s02.is_grounded(quote, SCENE)


# --- typography is not evidence ----------------------------------------------------

def test_a_closing_quote_mark_the_agent_added_is_not_a_violation():
    assert grounded('\u201cHolmes is a little too scientific for my tastes\u2014it '
                    'approaches to cold-bloodedness.\u201d')


def test_a_dialogue_comma_rendered_as_a_full_stop_is_not_a_violation():
    """Source: '\u201cLecoq was a miserable bungler,\u201d he said'. The dialogue editor
    returns the utterance, ending it with a period. Same words."""
    assert grounded('Lecoq was a miserable bungler.')


def test_straight_quotes_and_hyphens_match_curly_ones():
    assert grounded('"Lecoq was a miserable bungler"')


def test_case_differences_do_not_matter():
    assert grounded('LECOQ WAS A MISERABLE BUNGLER')


# --- elision is allowed, but every fragment must really be there -------------------

def test_an_elided_quote_passes_when_each_fragment_is_in_the_scene():
    assert grounded('It is not easy to express the inexpressible... '
                    'Lecoq was a miserable bungler')


def test_an_elided_quote_fails_when_a_fragment_is_absent():
    assert not grounded('It is not easy to express the inexpressible... '
                        'and then he drew his revolver and fired')


def test_a_paragraph_break_inside_a_quote_is_an_elision_too():
    assert grounded('It is not easy to express the inexpressible\n\n'
                    'Lecoq was a miserable bungler')


# --- what must STILL fail ----------------------------------------------------------

def test_words_that_are_not_in_the_scene_still_fail():
    assert not grounded('To-morrow at midnight')


def test_a_short_phrase_absent_from_the_scene_still_fails():
    """'presently' and 'last night' were real findings — a two-word phrase gets no
    free pass just for being short."""
    assert not grounded('last night')
    assert not grounded('presently')


def test_the_same_words_in_a_different_order_are_not_a_quote():
    assert not grounded('bungler miserable a was Lecoq')


def test_an_empty_quote_is_not_grounded():
    assert not s02.is_grounded('', SCENE)


# --- the check reports WHICH kind of failure it is ---------------------------------

def _extraction(quote):
    return {"chapter": 1, "scenes": [{
        "n": 1, "para_start": 1, "para_end": 1, "events": [], "state_changes": [],
        "time_evidence": [{"text": quote, "type": "time_of_day"}], "dialogue": []}]}


def _chapter():
    return {"n": 1, "paragraphs": [{"n": 1, "text": SCENE},
                                   {"n": 2, "text": "To-morrow at midnight, he said."}]}


def test_a_quote_from_elsewhere_in_the_chapter_is_flagged_as_misattributed():
    v = s02.check_extraction(_extraction("To-morrow at midnight"), _chapter())
    assert len(v) == 1
    assert v[0]["kind"] == "wrong-scene"
    assert "paragraph 2" in v[0]["note"]


def test_a_quote_absent_from_the_whole_chapter_is_flagged_as_ungrounded():
    v = s02.check_extraction(_extraction("he drew his revolver and fired"), _chapter())
    assert len(v) == 1
    assert v[0]["kind"] == "ungrounded"


def test_a_properly_grounded_quote_produces_nothing():
    assert s02.check_extraction(_extraction("Lecoq was a miserable bungler."),
                                _chapter()) == []
