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
