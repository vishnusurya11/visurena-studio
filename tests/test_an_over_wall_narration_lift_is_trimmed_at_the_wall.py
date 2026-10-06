"""QUOTE's mechanical cure (2026-10-05): a narration line that lifts more than
QUOTE_WALL consecutive book words is trimmed AT a word boundary to land at the
wall -- the ep02 craft (cutting Doyle's trailing "No answer? Right, sir." to
land at the wall) codified.  Only a lift touching the line's start or end is
mechanical; a mid-line lift is the writer's.  Dialogue is advisory by the
gate's own split and is never touched.  $0: regex arithmetic, no API."""
from __future__ import annotations

from studio import episode_spec as es
from studio import plan_cures as pc

RUN = "the brown masses of the red weed lay before us along the margin of the river"
SOURCE = f"It was all changed now. {RUN.capitalize()}. Nothing else remained."


def line_of(index: int, text: str, kind: str = "narration") -> dict:
    return {"index": index, "kind": kind, "speaker": "narrator", "text": text, "shot": 0}


def doc_of(*lines: dict) -> dict:
    return {"shots": [], "lines": list(lines)}


def test_lifted_offsets_index_the_original_line_string():
    text = f"I looked again, and {RUN}."
    a, b, n = es.lifted_offsets(text, SOURCE)
    assert n == es.lifted_run(text, SOURCE) > es.QUOTE_WALL
    assert text[a:b] == RUN                     # char offsets survive normalization
    assert es.lifted_offsets("nothing shared here", SOURCE) == (0, 0, 0)


def test_seen_runs_holds_only_over_wall_runs():
    found = es._tokens(SOURCE)
    seen = es._seen_runs(found)
    assert " ".join(found[:es.QUOTE_WALL + 1]) in seen      # a 9-word run is scannable
    assert " ".join(found[:es.QUOTE_WALL]) not in seen      # an 8-word run never lifts


def test_a_tail_lift_is_trimmed_to_the_wall_with_its_punctuation():
    text = f"I looked again, and {RUN}."
    assert es.lifted_run(text, SOURCE) > es.QUOTE_WALL
    out = pc.quote_trim(doc_of(line_of(3, text)), SOURCE)
    cured = out["lines"][0]["text"]
    assert es.lifted_run(cured, SOURCE) <= es.QUOTE_WALL
    assert cured.endswith(".")
    assert cured.startswith("I looked again, and ")


def test_a_head_lift_is_trimmed_and_recapitalized():
    text = f"{RUN.capitalize()}, and I turned away."
    assert es.lifted_run(text, SOURCE) > es.QUOTE_WALL
    out = pc.quote_trim(doc_of(line_of(1, text)), SOURCE)
    cured = out["lines"][0]["text"]
    assert es.lifted_run(cured, SOURCE) <= es.QUOTE_WALL
    assert cured[0].isupper()
    assert cured.endswith(", and I turned away.")


def test_a_mid_line_lift_is_the_writers_and_stays_byte_identical():
    text = f"He said that {RUN} while we walked."
    assert es.lifted_run(text, SOURCE) > es.QUOTE_WALL
    out = pc.quote_trim(doc_of(line_of(2, text)), SOURCE)
    assert out["lines"][0]["text"] == text


def test_a_dialogue_lift_is_advisory_and_never_touched():
    text = f"I looked again, and {RUN}."
    out = pc.quote_trim(doc_of(line_of(4, text, kind="dialogue")), SOURCE)
    assert out["lines"][0]["text"] == text


def test_quote_trim_is_idempotent():
    doc = doc_of(line_of(3, f"I looked again, and {RUN}."))
    once = pc.quote_trim(doc, SOURCE)
    texts = [l["text"] for l in once["lines"]]
    twice = pc.quote_trim(once, SOURCE)
    assert [l["text"] for l in twice["lines"]] == texts
