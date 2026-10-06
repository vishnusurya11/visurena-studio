"""A prop claim the stage cure added needs its G-SOURCE span: the cure copies a
VERBATIM chapter sentence (<= 25 words around the term) nearest the shot's own
paragraph -- verbatim guarantees span_match >= SPAN_MATCH, so the gate can never
refuse next round what this cure wrote.  Zero candidates leave the row uncured
(the writer's, creative).  $0."""
from __future__ import annotations

from studio import plan_cures as pc
from studio import plan_gates as pg

VOCAB = {"machines": {"fighting_machine": {"name": "the Martian fighting-machine",
                                           "terms": ["tripod"], "physical": "A walker."}},
         "creatures": {}}
PARAGRAPHS = [
    "It was near Weybridge that the smoke first rose above the trees.",
    "The tripod came striding over the pines.",
    "Afterwards the river lay silent under the black smoke of the guns.",
]


def doc_of():
    return {"shots": [
        {"index": 0, "setup": "pines",
         "frame": "the Martian fighting-machine strides over the pines",
         "motion": "", "at_rest": "", "end": "", "source": []},
        {"index": 1, "setup": "pines", "frame": "smoke over the trees",
         "motion": "", "at_rest": "", "end": "",
         "source": ["It was near Weybridge that the smoke first rose above the trees."]}],
        "setups": {"pines": {"described": "The pines.", "props": ["fighting_machine"]}}}


def test_the_span_is_the_chapters_own_sentence_on_the_staging_shot():
    out = pc.prop_spans(doc_of(), PARAGRAPHS, VOCAB)
    span = out["shots"][0]["source"][-1]
    assert span == "The tripod came striding over the pines."
    assert pg.span_match(span, " ".join(PARAGRAPHS)) >= pg.SPAN_MATCH
    assert out["shots"][1]["source"] == [PARAGRAPHS[0]]      # the neighbour is untouched


def test_a_long_sentence_is_trimmed_verbatim_around_the_term():
    long = "In the grey light " + "of that morning " * 4 + \
           "the tripod came striding over the pines " + "toward the river bank " * 4 + "at last."
    out = pc.prop_spans(doc_of(), [long], VOCAB)
    span = out["shots"][0]["source"][-1]
    assert len(span.split()) <= 25 and "tripod" in span
    assert span in long                                      # verbatim: a contiguous window


def test_zero_candidates_leave_the_source_untouched():
    out = pc.prop_spans(doc_of(), ["No machine is named in this chapter at all."], VOCAB)
    assert out["shots"][0]["source"] == []


def test_a_shot_with_a_term_naming_span_is_not_touched():
    doc = doc_of()
    doc["shots"][0]["source"] = ["The tripod came striding over the pines."]
    out = pc.prop_spans(doc, PARAGRAPHS, VOCAB)
    assert out["shots"][0]["source"] == ["The tripod came striding over the pines."]
