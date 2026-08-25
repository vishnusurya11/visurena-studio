"""Text repairs for Ebookmaker-generated EPUBs.

Corpus audit 2026-08-25 over 11 Gutenberg books. Every pathology below is a property of
`Ebookmaker 0.14.2`, which generates the whole ~75,000-book PG corpus — not of any one
book. Counts in each docstring are measured, not estimated.
"""

from __future__ import annotations

from studio import epub


# --- drop caps: the worst of them ---------------------------------------------------

def test_an_image_drop_cap_contributes_its_letter():
    """Pride and Prejudice sets the opening capital of 60 of its 61 chapters as an
    image. Extraction silently dropped it, so every chapter began one letter short:
    'R. BENNET was among the earliest...'"""
    html = ('<p><span class="letra"><img alt="M" src="i_035_b.png"/></span>'
            'R. BENNET was among the earliest of those who waited.</p>')
    blocks = epub.html_to_blocks(html)
    assert blocks[0]["text"].startswith("MR. BENNET was among the earliest")


def test_a_text_drop_cap_is_unaffected():
    """Chapter I of the same book uses a text drop cap — it already worked."""
    html = '<p><span class="letra">I</span>T is a truth universally acknowledged.</p>'
    assert epub.html_to_blocks(html)[0]["text"] == \
        "IT is a truth universally acknowledged."


def test_an_illustration_does_not_dump_its_caption_into_the_prose():
    """Only a single-letter alt is a drop cap. A described illustration is not text."""
    html = '<p>He looked up. <img alt="Elizabeth at the window" src="i_1.jpg"/> Then on.</p>'
    text = epub.html_to_blocks(html)[0]["text"]
    assert "Elizabeth at the window" not in text
    assert text == "He looked up. Then on."


def test_an_empty_alt_contributes_nothing():
    html = '<p>Before <img alt="" src="x.jpg"/> after.</p>'
    assert epub.html_to_blocks(html)[0]["text"] == "Before after."


# --- injected page numbers ---------------------------------------------------------

def test_page_number_spans_are_dropped():
    """496 of these are injected mid-sentence in Pride and Prejudice."""
    html = ('<p>had been insufficient to'
            '<span class="x-ebookmaker-pageno" title="{5}"><a id="page_5"></a></span>'
            ' make his wife understand his character.</p>')
    assert epub.html_to_blocks(html)[0]["text"] == \
        "had been insufficient to make his wife understand his character."


# --- headings ----------------------------------------------------------------------

def test_an_illustration_caption_is_stripped_from_a_heading():
    """34 of Pride and Prejudice's 65 headings carry a glued caption, which is why the
    nav entry reads 'I hope Mr. Bingley will like it. CHAPTER II.'"""
    html = ('<h2><img alt="" src="i_035_a.jpg"/>'
            '<span class="caption">I hope Mr. Bingley will like it.</span>'
            '<br/><br/>CHAPTER II.</h2>')
    blocks = epub.html_to_blocks(html)
    assert blocks[0]["kind"] == "heading"
    assert blocks[0]["text"] == "CHAPTER II."


def test_a_heading_split_by_br_joins_on_one_line():
    """62/66 P&P, 23/33 Dracula, 17/23 Peter Pan headings put number and title on
    separate lines."""
    html = '<h2>CHAPTER I<br/><br/><small>JONATHAN HARKER\u2019S JOURNAL</small></h2>'
    assert epub.html_to_blocks(html)[0]["text"] == \
        "CHAPTER I JONATHAN HARKER\u2019S JOURNAL"


def test_non_breaking_spaces_normalize_to_ordinary_spaces():
    """Dracula's title page is '<h2>D\xa0R\xa0A\xa0C\xa0U\xa0L\xa0A</h2>', which
    defeats any comparison against the metadata title 'Dracula'."""
    assert epub.html_to_blocks("<h2>D\u00a0R\u00a0A\u00a0C\u00a0U\u00a0L\u00a0A</h2>") \
        [0]["text"] == "D R A C U L A"


def test_an_empty_heading_is_discarded():
    """Two of P&P's 65 h2 elements extract to ''."""
    blocks = epub.html_to_blocks('<h2><img alt="" src="x.jpg"/></h2><p>Body.</p>')
    assert [(b['kind'], b['text']) for b in blocks] == [('para', 'Body.')]


# --- what must not regress ----------------------------------------------------------

def test_inline_emphasis_still_stays_inside_its_sentence():
    blocks = epub.html_to_blocks('<p>He was <i>quite</i> certain.</p>')
    assert [(b['kind'], b['text']) for b in blocks] == [('para', 'He was quite certain.')]


def test_a_real_br_in_a_paragraph_still_breaks_the_line():
    assert epub.html_to_blocks("<p>Roses are red,<br/>Violets are blue.</p>")[0]["text"] \
        == "Roses are red,\nViolets are blue."
