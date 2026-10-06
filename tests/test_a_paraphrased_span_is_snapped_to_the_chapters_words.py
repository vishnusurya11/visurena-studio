"""G-SOURCE's mechanical cure (2026-10-05): the scorer that refuses a span
already locates the best chapter window and merely throws its position away.
`snap_span` keeps it: the failing span is replaced by the chapter's OWN words,
expanded to complete sentences -- ep18 shot 16 scored 0.75/0.78 against the
0.85 wall and was hand-fixed exactly this way.  Below the 0.50 floor the span
is invention, not paraphrase, and is DROPPED so the existing 'has no chapter
span' fault escalates it to the writer.  $0: difflib arithmetic, no API."""
from __future__ import annotations

from studio import plan_cures as pc
from studio import plan_gates as pg

CHAPTER = (
    "The pit had been silent since the sunset, and the smoke drifted thinly. "
    "And then followed such a concussion as I had never heard before. "
    "Close upon its heels came a second report, and the glass fell about us."
)
MIDDLE = "And then followed such a concussion as I had never heard before."


def doc_of(*spans: str) -> dict:
    return {"shots": [{"index": 0, "source": list(spans)}]}


def test_a_paraphrase_snaps_to_the_chapters_own_sentence():
    span = "then came such a concussion as I never heard"
    assert pc.SNAP_FLOOR <= pg.span_match(span, CHAPTER) < pg.SPAN_MATCH
    assert pc.snap_span(span, CHAPTER) == MIDDLE


def test_a_snapped_span_clears_the_wall_it_failed():
    snapped = pc.snap_span("then came such a concussion as I never heard", CHAPTER)
    assert pg.span_match(snapped, CHAPTER) >= pg.SPAN_MATCH


def test_an_invented_span_is_dropped_not_snapped():
    span = "the Martian stood over the body"
    assert pc.snap_span(span, CHAPTER) is None
    out = pc.source_spans(doc_of(span), CHAPTER)
    assert out["shots"][0]["source"] == []


def test_a_verbatim_doc_is_left_byte_identical():
    doc = doc_of(MIDDLE, "Close upon its heels came a second report")
    before = [list(s["source"]) for s in doc["shots"]]
    out = pc.source_spans(doc, CHAPTER)
    assert [list(s["source"]) for s in out["shots"]] == before


def test_a_re_added_duplicate_collapses_to_one_snapped_copy():
    span = "then came such a concussion as I never heard"
    out = pc.source_spans(doc_of(span, span), CHAPTER)
    assert out["shots"][0]["source"] == [MIDDLE]


def test_a_snap_past_the_word_cap_keeps_the_midpoint_sentence():
    a = ("The road ran straight between the poplars for a mile and more, white with "
         "the summer dust, and nothing moved upon it but the heat shimmering over "
         "the fields on either side of the long way down")                 # ~40 words
    b = ("there the common opened out and the sand pits lay bare under the evening "
         "light with the heather burned black around them for a hundred yards")
    chapter = a + ". " + b.capitalize() + "."
    span = "the long way down there the common opened"      # straddles the boundary
    got = pc.snap_span(span, chapter)
    assert got is not None
    assert len(got.split()) <= pc.SNAP_WORDS
    assert got == b.capitalize() + "."                       # the midpoint's own sentence
    assert pg.span_match(got, chapter) >= pg.SPAN_MATCH
