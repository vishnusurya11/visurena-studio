"""Cleaning must never be able to delete the book.

Corpus audit 2026-08-25. The old `clean()` dropped whole spine documents that looked
like navigation chrome, and tracked the `*** START OF THE PROJECT GUTENBERG EBOOK ***`
marker across them. Two facts make that fatal:

  - The START marker lives in spine document #1 in 11/11 books. If that document is
    dropped, the started-flag never flips and EVERY later document is discarded.
    Sherlock Holmes: 379 KB in, 0 words out.
  - Document #1 is not just a title page. It carries real narrative in 3/11 books —
    17.9% of Pride and Prejudice (chapters I-X), 10.0% of Moby-Dick (chapters 1-8),
    and 63.7% of The Yellow Wallpaper (the entire story).

`class="pg-boilerplate"` appears exactly twice per book — header and footer — in 75/75
Gutenberg books measured. Dropping those two elements is precise; dropping documents
is not.
"""

from __future__ import annotations

import pytest

from scripts.analysis import step_01_ingest as s01
from studio import epub


def _doc(href, html):
    return {"href": href, "raw_html": html}


HEADER = ('<header class="pg-boilerplate pgheader" id="pg-header">'
          '<h1>The Project Gutenberg eBook of Whatever</h1>'
          '<div id="pg-start-separator"><span>*** START OF THE PROJECT GUTENBERG '
          'EBOOK WHATEVER ***</span></div></header>')
FOOTER = ('<section class="pg-boilerplate pgfooter" id="pg-footer">'
          '<div id="pg-end-separator"><span>*** END OF THE PROJECT GUTENBERG EBOOK '
          '***</span></div><p>This eBook is for the use of anyone anywhere.</p></section>')


def test_boilerplate_is_dropped_but_the_document_is_kept():
    """The exact Sherlock Holmes shape: narrative in the same document as the marker."""
    raw = {"title": "T", "author": "A", "toc": [],
           "spine": [_doc("wrap0000.xhtml", "<p>cover</p>"),
                     _doc("bk-h-0.htm.xhtml",
                          HEADER + "<h2>CHAPTER I</h2><p>The story begins here.</p>")]}
    book = s01.clean(raw)
    texts = [b["text"] for d in book["docs"] for b in d["blocks"]]
    assert "The story begins here." in texts
    assert not any("PROJECT GUTENBERG" in t.upper() for t in texts)


def test_a_document_holding_both_the_contents_and_chapters_keeps_its_chapters():
    """Pride and Prejudice and Moby-Dick pack the inline contents table into the same
    file as their first ten chapters. Dropping 'the contents document' costs 17.9% and
    10.0% of those books."""
    raw = {"title": "T", "author": "A", "toc": [],
           "spine": [_doc("bk-h-0.htm.xhtml",
                          HEADER + "<h2>CONTENTS</h2>"
                          '<p><a class="pginternal" href="#c1">Chapter I</a></p>'
                          "<h2>CHAPTER I.</h2><p>It is a truth universally "
                          "acknowledged.</p>")]}
    book = s01.clean(raw)
    texts = [b["text"] for d in book["docs"] for b in d["blocks"]]
    assert "It is a truth universally acknowledged." in texts


def test_the_footer_licence_is_dropped():
    raw = {"title": "T", "author": "A", "toc": [],
           "spine": [_doc("bk-h-9.htm.xhtml", "<p>The end of the tale.</p>" + FOOTER)]}
    book = s01.clean(raw)
    texts = [b["text"] for d in book["docs"] for b in d["blocks"]]
    assert "The end of the tale." in texts
    assert not any("use of anyone anywhere" in t for t in texts)


def test_a_book_with_no_gutenberg_markers_is_left_alone():
    """A commercial EPUB has no boilerplate. The PG logic must be inert, not
    fail-closed-empty."""
    raw = {"title": "T", "author": "A", "toc": [],
           "spine": [_doc("c1.xhtml", "<h2>One</h2><p>All of it survives.</p>")]}
    book = s01.clean(raw)
    texts = [b["text"] for d in book["docs"] for b in d["blocks"]]
    assert texts == ["One", "All of it survives."]


def test_the_cover_document_is_dropped():
    raw = {"title": "T", "author": "A", "toc": [],
           "spine": [_doc("wrap0000.xhtml", '<div class="x-ebookmaker-cover">'
                                            '<img alt="Cover" src="c.jpg"/></div>'),
                     _doc("bk-h-1.htm.xhtml", "<p>Real text.</p>")]}
    book = s01.clean(raw)
    assert [d["href"] for d in book["docs"]] == ["bk-h-1.htm.xhtml"]


# --- the guard whose expectation comes from OUTSIDE the thing checked ---------------

def test_cleaning_away_the_whole_book_is_a_loud_failure():
    """The retention floor. Its expectation is the INPUT word count, so unlike a check
    that compares the output against itself, it can actually fail."""
    with pytest.raises(ValueError, match="retained"):
        s01.check_retention(words_in=40000, words_out=0)


def test_cleaning_away_most_of_the_book_is_a_loud_failure():
    with pytest.raises(ValueError, match="retained"):
        s01.check_retention(words_in=40000, words_out=9000)


def test_normal_boilerplate_loss_passes():
    """A PG header and footer are ~2,700 words against a novel's tens of thousands."""
    s01.check_retention(words_in=40000, words_out=37300)


# --- books without PARTS (2026-08-26) ----------------------------------------------
#
# _check_chapters used `part > 0` to mean "a real chapter, not front matter". That only
# works on a book that HAS parts. A Study in Scarlet has two, so it passed for months.
# Frankenstein has Letters and Chapters and no parts at all, so every chapter came back
# part 0, the check saw zero real chapters, and ingest died claiming "every paragraph
# landed in front matter" on a book it had chapterized perfectly into 30 files.
#
# Front matter is identified by n == 0. That is the discriminator, and it is true of
# every book.

def _chapters(parts):
    front = [{"n": 0, "part": 0, "title": "Front matter", "paragraphs": []}]
    body = [{"n": i, "part": p, "title": f"Chapter {i}",
             "paragraphs": [{"n": 1, "text": "x"}]}
            for i, p in enumerate(parts, start=1)]
    return front + body


def test_a_book_with_no_parts_passes_the_chapter_check():
    from scripts.analysis.step_01_ingest import _check_chapters
    _check_chapters(_chapters([0, 0, 0]), expected=3)     # must not raise


def test_a_book_with_parts_still_passes():
    from scripts.analysis.step_01_ingest import _check_chapters
    _check_chapters(_chapters([1, 1, 2, 2]), expected=4)


def test_front_matter_is_not_counted_as_a_chapter():
    from scripts.analysis.step_01_ingest import _check_chapters
    import pytest
    with pytest.raises(ValueError, match="!= expected"):
        _check_chapters(_chapters([0, 0]), expected=3)


def test_a_book_with_genuinely_no_chapters_still_fails_loudly():
    """The original bug this check was written for must stay caught."""
    from scripts.analysis.step_01_ingest import _check_chapters
    import pytest
    front = [{"n": 0, "part": 0, "title": "Front matter",
              "paragraphs": [{"n": 1, "text": "the whole novel"}]}]
    with pytest.raises(ValueError, match="no chapters"):
        _check_chapters(front, expected=None)


# --- wrapped headings (2026-08-26) -------------------------------------------------
#
# Frankenstein's own title is set across two heading lines - "Frankenstein;" and
# "or, the Modern Prometheus" - so the first produced a chapter with ZERO paragraphs
# and ingest died on "chapter 1 is empty". A heading with no text before the next
# heading is not a chapter, it is a fragment of the heading that follows it.

def test_a_heading_with_no_text_is_folded_into_the_next():
    from scripts.analysis.step_01_ingest import fold_empty_headings
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        {"n": 1, "part": 0, "title": "Frankenstein;", "paragraphs": []},
        {"n": 2, "part": 0, "title": "or, the Modern Prometheus",
         "paragraphs": [{"n": 1, "text": "x"}]},
    ]
    folded = fold_empty_headings(chapters)
    assert [c["title"] for c in folded] == [
        "Front matter", "Frankenstein; or, the Modern Prometheus"]


def test_folding_renumbers_the_survivors_contiguously():
    from scripts.analysis.step_01_ingest import fold_empty_headings
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        {"n": 1, "part": 0, "title": "A", "paragraphs": []},
        {"n": 2, "part": 0, "title": "B", "paragraphs": [{"n": 1, "text": "x"}]},
        {"n": 3, "part": 0, "title": "C", "paragraphs": [{"n": 1, "text": "y"}]},
    ]
    assert [c["n"] for c in fold_empty_headings(chapters)] == [0, 1, 2]


def test_a_trailing_empty_heading_is_dropped_not_folded():
    """There is nothing after it to fold into."""
    from scripts.analysis.step_01_ingest import fold_empty_headings
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        {"n": 1, "part": 0, "title": "A", "paragraphs": [{"n": 1, "text": "x"}]},
        {"n": 2, "part": 0, "title": "Colophon", "paragraphs": []},
    ]
    assert [c["title"] for c in fold_empty_headings(chapters)] == ["Front matter", "A"]


def test_folding_leaves_a_clean_book_untouched():
    from scripts.analysis.step_01_ingest import fold_empty_headings
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        {"n": 1, "part": 0, "title": "A", "paragraphs": [{"n": 1, "text": "x"}]},
    ]
    assert fold_empty_headings(chapters) == chapters


def test_the_empty_front_matter_sentinel_survives_folding():
    """It is the n==0 anchor, not a chapter, and later steps expect it."""
    from scripts.analysis.step_01_ingest import fold_empty_headings
    chapters = [{"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
                {"n": 1, "part": 0, "title": "A", "paragraphs": [{"n": 1, "text": "x"}]}]
    assert fold_empty_headings(chapters)[0]["n"] == 0


def test_the_toc_expectation_moves_with_the_fold():
    """The TOC counts a wrapped title as two entries, so folding it into one made the
    actual count disagree with an expectation derived from the unfolded TOC. Fixing one
    side of a comparison and not the other is how this repo has broken checks before."""
    from scripts.analysis.step_01_ingest import fold_empty_headings, folded_expectation
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        {"n": 1, "part": 0, "title": "Frankenstein;", "paragraphs": []},
        {"n": 2, "part": 0, "title": "or, the Modern Prometheus",
         "paragraphs": [{"n": 1, "text": "x"}]},
        {"n": 3, "part": 0, "title": "Letter 1", "paragraphs": [{"n": 1, "text": "y"}]},
    ]
    folded = fold_empty_headings(chapters)
    assert folded_expectation(3, chapters, folded) == 2


def test_the_expectation_is_untouched_when_nothing_folded():
    from scripts.analysis.step_01_ingest import fold_empty_headings, folded_expectation
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        {"n": 1, "part": 0, "title": "A", "paragraphs": [{"n": 1, "text": "x"}]},
    ]
    assert folded_expectation(1, chapters, fold_empty_headings(chapters)) == 1


def test_no_expectation_stays_no_expectation():
    from scripts.analysis.step_01_ingest import fold_empty_headings, folded_expectation
    chapters = [{"n": 0, "part": 0, "title": "F", "paragraphs": []}]
    assert folded_expectation(None, chapters, fold_empty_headings(chapters)) is None


def test_chapter_files_are_written_with_the_folded_numbering(tmp_path):
    """The manifest and the files must agree. Folding after the write renumbered the
    list while ch_NN.json kept the old numbers, and the 01_05 agent check caught it."""
    from scripts.analysis.step_01_ingest import _write_chapters, fold_empty_headings
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        {"n": 1, "part": 0, "title": "Title;", "paragraphs": []},
        {"n": 2, "part": 0, "title": "Subtitle", "paragraphs": [{"n": 1, "text": "x"}]},
    ]
    folded = fold_empty_headings(chapters)
    _write_chapters(folded, tmp_path)
    written = sorted(p.name for p in (tmp_path / "chapters").glob("ch_*.json"))
    assert written == ["ch_00.json", "ch_01.json"]
