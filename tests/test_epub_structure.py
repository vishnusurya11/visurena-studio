"""Ingest structure: text that renders as separate words must not be glued together,
and a book whose chapters were never found must not report success.

Audit 2026-08-23 of step 01. A Study in Scarlet ingests perfectly — every chapter's
paragraph count matches its source document's <p> count exactly — so these are all
generalization defects found by probing, not by observing damage.
"""

from __future__ import annotations

import pytest

from scripts.analysis import step_01_ingest as s01
from studio import epub


# --- a tag that renders as a break must produce whitespace ------------------------

def test_br_does_not_glue_words_together():
    """<br/> rendered a line break and produced NOTHING, so 'red,<br/>Violets' came out
    as 'red,Violets'. Silent word corruption anywhere a source lacked stray whitespace."""
    blocks = epub.html_to_blocks("<p>Roses are red,<br/>Violets are blue.</p>")
    assert "red,Violets" not in blocks[0]["text"]


def test_verse_keeps_its_lines():
    blocks = epub.html_to_blocks("<p>Roses are red,<br/>Violets are blue.</p>")
    assert blocks[0]["text"] == "Roses are red,\nViolets are blue."


def test_a_heading_split_by_br_joins_on_one_line():
    """'CHAPTER I.<br/> MR. SHERLOCK HOLMES.' is one title, not two lines."""
    blocks = epub.html_to_blocks("<h2>CHAPTER I.<br/>MR. SHERLOCK HOLMES.</h2>")
    assert blocks[0] == {"kind": "heading", "text": "CHAPTER I. MR. SHERLOCK HOLMES."}


def test_table_cells_do_not_run_together():
    blocks = epub.html_to_blocks(
        "<table><tr><td>Name</td><td>Age</td></tr><tr><td>Hope</td><td>34</td></tr></table>")
    assert not any("NameAge" in b["text"] or "Hope34" in b["text"] for b in blocks)


def test_inline_emphasis_still_stays_inside_its_sentence():
    """<i> renders inline — it must NOT split a sentence into pieces."""
    blocks = epub.html_to_blocks("<p>He was <i>quite</i> certain.</p>")
    assert blocks == [{"kind": "para", "text": "He was quite certain."}]


# --- an EPUB2 book still has a table of contents -----------------------------------

def test_ncx_navigation_is_parsed_when_there_is_no_nav_document():
    """EPUB3 prefers the nav document, but EPUB2 books — and plenty of EPUB3 ones —
    carry only toc.ncx. Reading neither left the TOC empty, and an empty TOC means no
    chapter is ever recognised."""
    ncx = """<?xml version="1.0"?>
    <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap>
      <navPoint><navLabel><text>CHAPTER I.</text></navLabel><content src="c1.xhtml"/>
        <navPoint><navLabel><text>A Sub Part</text></navLabel><content src="c1.xhtml#a"/>
        </navPoint>
      </navPoint>
      <navPoint><navLabel><text>CHAPTER II.</text></navLabel><content src="c2.xhtml"/>
      </navPoint>
    </navMap></ncx>"""
    entries = epub.parse_ncx(ncx)
    assert [e["title"] for e in entries] == ["CHAPTER I.", "A Sub Part", "CHAPTER II."]
    assert [e["level"] for e in entries] == [1, 2, 1]
    assert entries[0]["href"] == "c1.xhtml"


# --- a check that cannot fail is not a check ---------------------------------------

def test_finding_no_chapters_is_a_failure_not_a_pass():
    """The expectation came from the TOC, so an empty TOC expected zero chapters and
    zero chapters matched. The whole book landed in 'Front matter' and step 01 reported
    checks PASS."""
    chapters = [{"n": 0, "part": 0, "title": "Front matter",
                 "paragraphs": [{"n": 1, "text": "The whole novel, unsplit."}]}]
    with pytest.raises(ValueError, match="no chapters"):
        s01._check_chapters(chapters, 0)


def test_a_normal_book_still_passes():
    chapters = [{"n": 1, "part": 1, "title": "I", "paragraphs": [{"n": 1, "text": "a"}]},
                {"n": 2, "part": 1, "title": "II", "paragraphs": [{"n": 1, "text": "b"}]}]
    s01._check_chapters(chapters, 2)


# --- 'Part' is only a part when a number follows it --------------------------------

def test_a_chapter_titled_part_of_the_plan_is_a_chapter():
    toc = [{"title": "Part of the Plan", "href": "a", "level": 0},
           {"title": "The Reckoning", "href": "b", "level": 0}]
    parts, chapters, _ = s01._toc_parts_and_chapters(toc, "T")
    assert parts == {}
    assert set(chapters) == {"part of the plan", "the reckoning"}


@pytest.mark.parametrize("title", ["PART I.", "Part 2", "BOOK III", "Volume One",
                                   "PART II. The Country of the Saints."])
def test_a_real_part_heading_is_still_a_part(title):
    parts, _, _ = s01._toc_parts_and_chapters(
        [{"title": title, "href": "a", "level": 0},
         {"title": "Chapter I", "href": "b", "level": 0}], "T")
    assert len(parts) == 1, title


# --- mechanical damage is caught over EVERY paragraph, not a sample ----------------

def test_mojibake_anywhere_in_a_chapter_fails_the_check():
    """The agent only ever sees a chapter's first and last paragraph, so corruption in
    paragraph 30 was invisible to the one check that claimed to look for it."""
    chapters = [{"n": 1, "part": 1, "title": "I", "paragraphs": [
        {"n": 1, "text": "clean"}, {"n": 2, "text": "he said \u00e2\u20ac\u2122tis so"}]}]
    with pytest.raises(ValueError, match="garbled"):
        s01._check_chapters(chapters, 1)


def test_a_raw_html_tag_in_the_text_fails_the_check():
    chapters = [{"n": 1, "part": 1, "title": "I", "paragraphs": [
        {"n": 1, "text": "a"}, {"n": 2, "text": "then <span class='x'>this</span>"}]}]
    with pytest.raises(ValueError, match="garbled"):
        s01._check_chapters(chapters, 1)


def test_an_impossibly_long_token_fails_the_check():
    """The signature of glued text — the defect this audit found in html_to_blocks."""
    chapters = [{"n": 1, "part": 1, "title": "I", "paragraphs": [
        {"n": 1, "text": "Roses are red,VioletsAreBlueAndThisNeverEndsNorDoesItStop"}]}]
    with pytest.raises(ValueError, match="garbled"):
        s01._check_chapters(chapters, 1)


def test_ordinary_long_words_and_punctuation_are_fine():
    chapters = [{"n": 1, "part": 1, "title": "I", "paragraphs": [
        {"n": 1, "text": "The counter-revolutionaries' incomprehensibilities—dashes, "
                         "em—dashes, U.S.A., McDonald, and 3.14159 all pass."}]}]
    s01._check_chapters(chapters, 1)
