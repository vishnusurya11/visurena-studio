"""The title card's OCR gate cannot see a glyph that is not a letter.

MEASURED on WotW ep05 (2026-09-20).  `plate_caption` asks Ideogram for `the
words "<line>" (exact, no typos)` -- the quotation marks belong to the PROMPT --
and the card came back lettered `The Heat-ray"`, the closing curly quote set in
the same ivory serif as the words.  It read back "OK" on the first try, because
`missing_lines` normalises every non-alphanumeric character away before it
compares, so no stray glyph can ever fail it.

ep01-ep04's cards are clean, so this is a seed rather than a certainty -- which
is the argument for a gate and a re-roll rather than for rewriting the caption.
"""
from __future__ import annotations

from studio.series_title import lines_read, missing_lines, stray_glyphs

LINES = ["THE WAR OF THE WORLDS", "EPISODE 5", "THE HEAT-RAY"]


def test_the_old_gate_passes_the_stray_quote():
    """The fault this test exists for: the card that shipped read back clean."""
    ocr = '["THE WAR OF THE WORLDS", "EPISODE 5", "THE HEAT-RAY\\u201d"]'
    assert missing_lines(LINES, ocr) == []
    assert lines_read(LINES, ocr)


def test_a_stray_closing_quote_is_named():
    ocr = '["THE WAR OF THE WORLDS", "EPISODE 5", "THE HEAT-RAY\\u201d"]'
    assert stray_glyphs(LINES, ocr) == ["”"]


def test_a_clean_card_has_no_stray_glyph():
    ocr = '["THE WAR OF THE WORLDS", "EPISODE 4", "THE CYLINDER OPENS"]'
    assert stray_glyphs(["THE WAR OF THE WORLDS", "EPISODE 4", "THE CYLINDER OPENS"], ocr) == []


def test_a_quote_the_title_itself_asks_for_is_not_stray():
    """A chapter whose own name carries an apostrophe keeps it."""
    lines = ["THE WAR OF THE WORLDS", "EPISODE 9", "WHAT I SAW OF THE DESTRUCTION OF WEYBRIDGE"]
    assert stray_glyphs(["A MAN'S HOUSE"], '["A MAN\'S HOUSE"]') == []
    assert stray_glyphs(lines, '["THE WAR OF THE WORLDS","EPISODE 9",'
                               '"WHAT I SAW OF THE DESTRUCTION OF WEYBRIDGE"]') == []


def test_a_straight_quote_and_a_backtick_count_too():
    assert stray_glyphs(["EPISODE 5"], '["EPISODE 5\\""]') == ['"']
    assert stray_glyphs(["EPISODE 5"], '["`EPISODE 5"]') == ["`"]
