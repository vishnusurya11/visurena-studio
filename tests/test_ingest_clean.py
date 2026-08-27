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


# --- the contents page (2026-08-26) ------------------------------------------------
#
# Frankenstein's chapter 1 came out as 28 "paragraphs" reading "Letter 1", "Letter 2",
# ... "Chapter 24". That is the book's table of contents ingested as prose. It is
# detectable without a heuristic about page position or word count: a chapter whose
# paragraphs ARE the TOC's own entry titles is the contents page.

TOC_TITLES = ["Letter 1", "Letter 2", "Chapter 1", "Chapter 2", "Chapter 3"]


def _ch(texts, n=1):
    return {"n": n, "part": 0, "title": "Contents",
            "paragraphs": [{"n": i, "text": t} for i, t in enumerate(texts, 1)]}


def test_a_chapter_made_of_toc_entries_is_the_contents_page():
    from scripts.analysis.step_01_ingest import is_contents_page
    assert is_contents_page(_ch(TOC_TITLES), TOC_TITLES)


def test_real_prose_is_not_the_contents_page():
    from scripts.analysis.step_01_ingest import is_contents_page
    prose = ["You will rejoice to hear that no disaster has accompanied the "
             "commencement of an enterprise which you have regarded with such evil "
             "forebodings.", "I arrived here yesterday."]
    assert not is_contents_page(_ch(prose), TOC_TITLES)


def test_a_chapter_that_merely_mentions_a_chapter_title_is_not_contents():
    from scripts.analysis.step_01_ingest import is_contents_page
    mixed = ["Chapter 1", "It was a dark and stormy night, and the wind howled on.",
             "He walked for a long while without speaking to anyone at all."]
    assert not is_contents_page(_ch(mixed), TOC_TITLES)


def test_matching_ignores_case_and_punctuation():
    from scripts.analysis.step_01_ingest import is_contents_page
    assert is_contents_page(_ch(["LETTER 1.", "letter 2", "Chapter 1"]), TOC_TITLES)


def test_an_empty_chapter_is_not_the_contents_page():
    from scripts.analysis.step_01_ingest import is_contents_page
    assert not is_contents_page(_ch([]), TOC_TITLES)


def test_the_front_matter_sentinel_is_never_treated_as_contents():
    """Dropping n==0 would remove the coordinate anchor every later step expects."""
    from scripts.analysis.step_01_ingest import drop_contents_pages
    chapters = [_ch(TOC_TITLES, n=0), _ch(["Real prose here, at some length."], n=1)]
    assert [c["n"] for c in drop_contents_pages(chapters, TOC_TITLES)] == [0, 1]


def test_dropping_contents_renumbers_the_survivors():
    from scripts.analysis.step_01_ingest import drop_contents_pages
    chapters = [
        {"n": 0, "part": 0, "title": "Front matter", "paragraphs": []},
        _ch(TOC_TITLES, n=1),
        _ch(["Real prose here, at some length, with actual sentences in it."], n=2),
    ]
    kept = drop_contents_pages(chapters, TOC_TITLES)
    assert [c["n"] for c in kept] == [0, 1] and len(kept) == 2


def test_a_book_with_no_contents_page_is_untouched():
    from scripts.analysis.step_01_ingest import drop_contents_pages
    chapters = [{"n": 0, "part": 0, "title": "F", "paragraphs": []},
                _ch(["Real prose, long enough to be prose."], n=1)]
    assert drop_contents_pages(chapters, TOC_TITLES) == chapters


# --- the expectation must be cleaned like the body (2026-08-26) --------------------
#
# Third time this repo has hit the same shape: a check whose two sides are derived
# differently. `folded_expectation` adjusted the TOC count by what was removed from the
# BODY, which is only correct when the removed thing was also counted in the TOC.
#
# Dracula's contents page was produced as a chapter and dropped - correctly - but
# "Contents" was never in the TOC's chapter count, so subtracting it made a correct body
# count of 29 fail against a wrongly-shrunk expectation of 28.
#
# The fix is to clean the EXPECTATION at its source instead of patching it afterwards.

def test_a_contents_entry_is_not_counted_as_a_chapter():
    from scripts.analysis.step_01_ingest import chapter_titles
    toc = [{"title": "Contents"}, {"title": "Chapter I"}, {"title": "Chapter II"}]
    assert chapter_titles(toc) == ["Chapter I", "Chapter II"]


def test_front_and_back_matter_entries_are_not_chapters():
    from scripts.analysis.step_01_ingest import chapter_titles
    toc = [{"title": "Title Page"}, {"title": "Chapter I"},
           {"title": "THE FULL PROJECT GUTENBERG LICENSE"}]
    assert chapter_titles(toc) == ["Chapter I"]


def test_a_real_chapter_named_like_matter_is_kept():
    """'The Contents of the Casket' is a chapter, not a contents page. Matching must be
    on the WHOLE entry, never a substring - the mistake that cost 298 character
    references in step 03."""
    from scripts.analysis.step_01_ingest import chapter_titles
    toc = [{"title": "Contents"}, {"title": "The Contents of the Casket"}]
    assert chapter_titles(toc) == ["The Contents of the Casket"]


def test_matching_ignores_case_and_spacing():
    from scripts.analysis.step_01_ingest import chapter_titles
    assert chapter_titles([{"title": "  CONTENTS  "}, {"title": "Chapter I"}]) == \
        ["Chapter I"]


def test_the_expectation_counts_chapters_not_alias_keys():
    """`chapter_ords` maps every TOC heading TEXT to a chapter ordinal, so two headings
    for the same chapter are two keys. Dracula's TOC lists "D R A C U L A" and
    "CHAPTER I ..." both pointing at chapter 2, so len(keys) claimed 29 chapters where
    the book has 28, and a correct parse failed."""
    from scripts.analysis.step_01_ingest import chapter_count
    assert chapter_count({"d r a c u l a": 2, "chapter i": 2, "chapter ii": 3}) == 2


def test_a_book_with_one_heading_per_chapter_is_unaffected():
    from scripts.analysis.step_01_ingest import chapter_count
    assert chapter_count({"chapter i": 1, "chapter ii": 2, "chapter iii": 3}) == 3


def test_an_empty_ordinal_map_counts_zero():
    from scripts.analysis.step_01_ingest import chapter_count
    assert chapter_count({}) == 0


# --- garbled-text false positives (2026-08-26) -------------------------------------
#
# The long-token check stripped dashes only from the ENDS of a token, so a legitimate
# hyphenated compound counted as one long word. Dracula's "two-pages-to-the-week-with-
# Sunday-squeezed-in-a-corner" and Peter Pan's em-dashed "but-I-am-too-tired-to-bring-
# it" both tripped it. Glued text has no separators; a compound is separators.

def test_a_long_hyphenated_compound_is_not_garbled():
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("a two-pages-to-the-week-with-Sunday-squeezed-in-a-corner diary") is None


def test_an_em_dashed_run_is_not_garbled():
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("but\u2014I\u2014am\u2014too\u2014tired\u2014to\u2014bring\u2014it") is None


def test_genuinely_glued_text_is_still_caught():
    """The bug this check exists for: words run together with no separator at all."""
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("thequickbrownfoxjumpedoverthelazydogandkeptonrunning") is not None


def test_a_normal_sentence_is_clean():
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("It was the best of times, it was the worst of times.") is None


# --- boilerplate vs a transcriber's note (2026-08-26) ------------------------------
#
# Moby Dick carries a front-matter note reading "This text is a combination of etexts,
# one from the now-defunct ERIS project at Virginia Tech and one from Project
# Gutenberg." That is a publication note about the edition - exactly the kind of thing
# front matter is FOR - and the boilerplate check killed the whole ingest over it.
#
# Boilerplate in a CHAPTER is real damage: it means the license text was chapterized as
# prose. In front matter it is just an honest note about provenance.

def _chapters_with(text, n):
    return [{"n": 0, "part": 0, "title": "Front matter",
             "paragraphs": [{"n": 1, "text": "ordinary front matter"}]},
            {"n": 1, "part": 0, "title": "Chapter I",
             "paragraphs": [{"n": 1, "text": "prose"}]}] if n is None else \
           [{"n": n, "part": 0, "title": "T",
             "paragraphs": [{"n": 1, "text": text}]}]


def test_boilerplate_inside_a_chapter_still_fails():
    import pytest
    from scripts.analysis.step_01_ingest import _check_chapters
    chapters = [{"n": 0, "part": 0, "title": "F", "paragraphs": []},
                {"n": 1, "part": 0, "title": "A", "paragraphs": [
                    {"n": 1, "text": "START OF THE PROJECT GUTENBERG EBOOK MOBY DICK"}]}]
    with pytest.raises(ValueError, match="boilerplate"):
        _check_chapters(chapters, 1)


def test_a_transcribers_note_in_front_matter_is_allowed():
    from scripts.analysis.step_01_ingest import _check_chapters
    chapters = [{"n": 0, "part": 0, "title": "Front matter", "paragraphs": [
                    {"n": 1, "text": "This text is a combination of etexts, one from "
                                     "the now-defunct ERIS project and one from "
                                     "Project Gutenberg."}]},
                {"n": 1, "part": 0, "title": "A", "paragraphs": [{"n": 1, "text": "x"}]}]
    _check_chapters(chapters, 1)      # must not raise


# --- punctuation runs are not words (2026-08-27) -----------------------------------
#
# Around the World in Eighty Days died on "impossibly long token '.........................'"
# - a row of dots, the leader rule from a table of contents or a printed pause. The check
# splits on dashes but treated a run of dots as one enormous word.
#
# A word is letters. The check exists to find LETTERS glued together with no separator.

def test_a_run_of_dots_is_not_a_long_token():
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("Chapter I " + "." * 40 + " page 1") is None


def test_a_run_of_underscores_or_asterisks_is_not_a_long_token():
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("_" * 50) is None and _garbled("*" * 50) is None


def test_glued_letters_are_still_caught():
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("thequickbrownfoxjumpedoverthelazydogandkeptrunning") is not None


def test_a_long_number_is_not_glued_prose():
    from scripts.analysis.step_01_ingest import _garbled
    assert _garbled("1234567890123456789012345678901234567890") is None


# --- console encoding must never lose a book (2026-08-27) --------------------------
#
# Twenty Thousand Leagues died with "'charmap' codec can't encode character '\u2032'".
# That is a PRINT failing on a Windows cp1252 console - the data was fine, the parse was
# fine, and the book was lost to a progress message. Any book with a prime, a curly
# quote or an accent could hit it.

def test_console_safe_never_raises_on_any_unicode():
    from scripts.analysis.step_01_ingest import console_safe
    for text in ("30\u2032 45\u2033", "caf\u00e9", "\u201cquoted\u201d",
                 "\u4e2d\u6587", "plain ascii"):
        assert isinstance(console_safe(text), str)


def test_console_safe_keeps_text_that_encodes_cleanly():
    from scripts.analysis.step_01_ingest import console_safe
    assert console_safe("It was the best of times.") == "It was the best of times."


def test_console_safe_replaces_rather_than_dropping_the_line():
    """Losing the character is fine; losing the message is not."""
    from scripts.analysis.step_01_ingest import console_safe
    got = console_safe("chapter 30\u2032 title")
    assert "chapter" in got and "title" in got
