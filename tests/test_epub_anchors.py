"""Nav anchors resolved to positions in the block stream.

Corpus audit 2026-08-25: the nav TOC anchor is the single most reliable structure
signal in the corpus — 1549/1549 fragments resolve, 11/11 books, 100%. It is also the
only signal that works for BOTH archetypes: 13 of 75 Gutenberg books are one-file-per-
chapter, and the other 83% pack 8-12 chapters into a single document. Cutting by
document works on the 17%; cutting by anchor works on all of it.

The detail that makes or breaks it: Ebookmaker usually puts the anchor on the <div>
WRAPPING the heading, not on the heading itself. Resolving only ids carried by the
heading element scores 423/1549 (27%).
"""

from __future__ import annotations

from studio import epub


def test_a_block_carries_the_id_of_its_own_element():
    blocks = epub.html_to_blocks('<h2 id="c1">CHAPTER I</h2>')
    assert blocks[0]["ids"] == ["c1"]


def test_a_block_carries_the_id_of_the_div_wrapping_it():
    """The Ebookmaker case: <div class="chapter" id="pgepubid00003"><h2>..."""
    html = '<div class="chapter" id="pgepubid00003"><h2>CHAPTER I</h2><p>Body.</p></div>'
    blocks = epub.html_to_blocks(html)
    assert "pgepubid00003" in blocks[0]["ids"]
    assert blocks[0]["text"] == "CHAPTER I"


def test_the_wrapper_id_does_not_leak_onto_a_later_block():
    html = '<div id="wrap"><h2>CHAPTER I</h2><p>First.</p><p>Second.</p></div>'
    blocks = epub.html_to_blocks(html)
    assert "wrap" in blocks[0]["ids"]
    assert blocks[1]["ids"] == []
    assert blocks[2]["ids"] == []


def test_an_anchor_before_a_heading_attaches_to_that_heading():
    """<a id="chap01"/> sits inside the h2 in Dracula and Peter Pan."""
    blocks = epub.html_to_blocks('<h2><a id="chap01"></a>CHAPTER I</h2>')
    assert blocks[0]["ids"] == ["chap01"]
    assert blocks[0]["text"] == "CHAPTER I"


def test_ids_inside_dropped_content_are_not_collected():
    html = '<h2><span class="caption">A caption<a id="nope"></a></span>CHAPTER II.</h2>'
    blocks = epub.html_to_blocks(html)
    assert blocks[0]["ids"] == []
    assert blocks[0]["text"] == "CHAPTER II."


# --- choosing which nav depth is the chapter level ---------------------------------

def _entries(*levels):
    return [{"title": f"e{i}", "href": f"#a{i}", "level": lv}
            for i, lv in enumerate(levels)]


def test_a_flat_nav_uses_its_only_level():
    assert epub.boundary_depth(_entries(1, 1, 1, 1, 1)) == 1


def test_nested_subsections_do_not_become_chapters():
    """Sherlock Holmes: 12 stories at depth 1, but story I alone carries three
    depth-2 sections I. II. III. Those are inside a story, not stories."""
    entries = _entries(*([1] * 12 + [2, 2, 2]))
    assert epub.boundary_depth(entries) == 1


def test_a_deeply_nested_anthology_still_uses_its_top_level():
    """Complete Shakespeare's measured nav: 289 depth-1, 876 depth-2, 4 depth-3.
    A share-of-the-nav rule picks depth 2 here — 876 acts and scenes as 'chapters'.
    The top level is the unit."""
    entries = _entries(*([1] * 289 + [2] * 876 + [3] * 4))
    assert epub.boundary_depth(entries) == 1


def test_a_depth_with_too_few_entries_is_skipped():
    """A single depth-1 wrapper over all the real divisions."""
    entries = _entries(*([1] * 2 + [2] * 20))
    assert epub.boundary_depth(entries) == 2


def test_an_empty_nav_has_no_boundary_depth():
    assert epub.boundary_depth([]) is None
