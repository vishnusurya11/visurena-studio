"""Candidate enumeration: every place a division could open.

Code enumerates; an agent adjudicates; code slices. This file covers the first third —
and its contract is COMPLETENESS, not precision. A candidate the code fails to enumerate
is one the agent can never recover, so the enumerator is deliberately generous and every
discriminator it computes is evidence handed onward rather than a hidden threshold.
"""

from __future__ import annotations

from scripts.analysis import step_01_ingest as s01


def _book(*docs):
    return {"title": "T", "author": "A",
            "docs": [{"href": h, "blocks": b} for h, b in docs]}


def _h(text, ids=None):
    return {"kind": "heading", "text": text, "ids": ids or []}


def _p(text, n=8):
    return {"kind": "para", "text": " ".join(["word"] * n), "ids": []}


def test_every_heading_becomes_a_candidate():
    book = _book(("c1.xhtml", [_h("CHAPTER I"), _p("x"), _h("CHAPTER II"), _p("y")]))
    got = s01.enumerate_candidates(book, [])
    assert [c["text"] for c in got] == ["CHAPTER I", "CHAPTER II"]


def test_candidate_ids_are_stable_and_ordered():
    """id = the n-th heading in the cleaned stream. Invariant under paragraph-level
    filtering, so the improve loop's knobs cannot invalidate a cached map."""
    book = _book(("c1.xhtml", [_h("ONE"), _p("a"), _h("TWO")]))
    assert [c["id"] for c in s01.enumerate_candidates(book, [])] == ["h001", "h002"]


def test_words_after_measures_up_to_the_next_candidate():
    """A title page has a handful of words after it; a chapter has thousands. This is
    the discriminator that separates Dracula's spaced-out title from chapter one, and
    it goes to the agent as evidence rather than being thresholded here."""
    book = _book(("c1.xhtml", [_h("D R A C U L A"), _p("x", 5),
                               _h("CHAPTER I"), _p("y", 300)]))
    got = s01.enumerate_candidates(book, [])
    assert got[0]["words_after"] == 5
    assert got[1]["words_after"] == 300


def test_preview_carries_the_opening_words_of_what_follows():
    book = _book(("c1.xhtml", [_h("CHAPTER I"),
                               {"kind": "para", "ids": [],
                                "text": "In the year 1878 I took my degree."}]))
    assert s01.enumerate_candidates(book, [])[0]["preview"].startswith("In the year 1878")


def test_a_toc_anchor_marks_its_candidate_resolved():
    book = _book(("OEBPS/c1.xhtml", [_h("CHAPTER I", ids=["pgepubid00003"]), _p("x")]))
    toc = [{"title": "CHAPTER I", "href": "c1.xhtml#pgepubid00003", "level": 1}]
    got = s01.enumerate_candidates(book, toc)
    assert got[0]["anchor_resolved"] is True
    assert "toc_anchor" in got[0]["signals"]


def test_an_unanchored_heading_is_still_a_candidate():
    """Completeness beats precision — the agent can drop it, but only if it exists."""
    book = _book(("c1.xhtml", [_h("A STRAY HEADING"), _p("x")]))
    got = s01.enumerate_candidates(book, [])
    assert len(got) == 1
    assert got[0]["anchor_resolved"] is False


def test_a_toc_title_match_is_recorded_as_a_weaker_signal():
    book = _book(("c1.xhtml", [_h("CHAPTER I. MR. SHERLOCK HOLMES."), _p("x")]))
    toc = [{"title": "CHAPTER I. MR. SHERLOCK HOLMES.", "href": "c1.xhtml", "level": 1}]
    got = s01.enumerate_candidates(book, toc)
    assert "toc_title" in got[0]["signals"]
    assert got[0]["anchor_resolved"] is False


def test_a_numbered_heading_carries_its_parsed_ordinal():
    book = _book(("c1.xhtml", [_h("CHAPTER XVII"), _p("x"),
                               _h("Chapter 5"), _p("y"),
                               _h("Letter 3"), _p("z"),
                               _h("The Flower of Utah"), _p("w")]))
    got = s01.enumerate_candidates(book, [])
    assert [c["ordinal"] for c in got] == [17, 5, 3, None]
    assert [c["series"] for c in got] == ["chapter", "chapter", "letter", None]


def test_a_missing_space_in_the_numeral_still_parses():
    """Pride and Prejudice ships CHAPTERXXVII. and CHAPTERXXVIII. — a search-anywhere
    match with the space optional takes that book from 0 chapters to 61."""
    book = _book(("c1.xhtml", [_h("CHAPTERXXVII."), _p("x")]))
    assert s01.enumerate_candidates(book, [])[0]["ordinal"] == 27


def test_a_caption_glued_before_the_numeral_still_parses():
    """34 of P&P's 65 headings read 'I hope Mr. Bingley will like it. CHAPTER II.'"""
    book = _book(("c1.xhtml", [_h("I hope Mr. Bingley will like it. CHAPTER II."), _p("x")]))
    assert s01.enumerate_candidates(book, [])[0]["ordinal"] == 2


def test_a_bare_roman_numeral_heading_parses():
    book = _book(("c1.xhtml", [_h("II"), _p("x")]))
    got = s01.enumerate_candidates(book, [])
    assert got[0]["ordinal"] == 2 and got[0]["series"] == "bare"


def test_a_part_heading_is_recognised_as_its_own_series():
    book = _book(("c1.xhtml", [_h("PART II. The Country of the Saints."), _p("x")]))
    got = s01.enumerate_candidates(book, [])
    assert got[0]["series"] == "part" and got[0]["ordinal"] == 2


def test_part_of_the_plan_is_not_a_part():
    book = _book(("c1.xhtml", [_h("Part of the Plan"), _p("x")]))
    assert s01.enumerate_candidates(book, [])[0]["series"] is None


def test_a_leading_numeral_before_a_title_parses():
    """The Adventures of Sherlock Holmes titles its twelve stories
    'I. A SCANDAL IN BOHEMIA', 'II. THE RED-HEADED LEAGUE'. Neither the series pattern
    (no series word) nor the bare pattern (the heading is not ONLY a numeral) sees it,
    and the book scores 3 of 12 without this."""
    book = _book(("c1.xhtml", [_h("I. A SCANDAL IN BOHEMIA"), _p("x"),
                               _h("II. THE RED-HEADED LEAGUE"), _p("y"),
                               _h("12. The Copper Beeches"), _p("z")]))
    got = s01.enumerate_candidates(book, [])
    assert [c["ordinal"] for c in got] == [1, 2, 12]
    assert all(c["series"] == "bare" for c in got)


def test_an_implausible_roman_reading_is_refused():
    """'MIX.' is a word, not 1009. Cap the ordinal at something a book could have."""
    book = _book(("c1.xhtml", [_h("MIX. A Cocktail Recipe"), _p("x")]))
    assert s01.enumerate_candidates(book, [])[0]["ordinal"] is None


def test_a_plain_titled_heading_is_still_unnumbered():
    book = _book(("c1.xhtml", [_h("THE SONNETS"), _p("x")]))
    assert s01.enumerate_candidates(book, [])[0]["ordinal"] is None
