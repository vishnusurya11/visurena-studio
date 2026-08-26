"""The cartographer maps a book's real divisions. No API calls; a fake model throughout.

Built because counting stopped working. Five of seven books failed step 01 on the same
assumption - that TOC entries and body headings correspond one to one - and each failed
differently: Dracula opens "NOTE" as a chapter, Peter Pan has 17 headings for 18 TOC
entries, Pride and Prejudice finds 27 of 61. Patching the arithmetic fixed one book and
broke another, which is the signature of a wrong model rather than a missing case.
"""

from __future__ import annotations

import pytest

from agents import book_cartographer as bc


def _cand(cid, text, words_after=800, series="chapter", ordinal=1, **over):
    base = dict(id=cid, text=text, preview="Narrative prose begins here and continues.",
                words_after=words_after, anchor_resolved=True,
                series=series, ordinal=ordinal, signals=["toc_anchor"])
    return {**base, **over}


class _Fake:
    """Returns canned structured output. Records the prompt so we can assert on it."""

    def __init__(self, payload):
        self.payload, self.prompt = payload, None

    def __call__(self, prompt, structured_output_model=None):
        from types import SimpleNamespace
        self.prompt = prompt
        return SimpleNamespace(
            structured_output=structured_output_model.model_validate(self.payload),
            metrics=SimpleNamespace(accumulated_usage={
                "inputTokens": 100, "outputTokens": 20, "totalTokens": 120}))


def _map(divisions, structure="3 chapters", missing=None):
    return {"structure": structure, "divisions": divisions, "missing": missing or []}


# --- the contract ------------------------------------------------------------------

def test_a_division_requires_a_role():
    from studio.screenplay_spec import __name__ as _  # noqa: F401
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        bc.Division(candidate_id="h001", reason="x")


def test_role_is_restricted_to_the_known_kinds():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        bc.Division(candidate_id="h001", role="probably-a-chapter", reason="x")


def test_every_documented_role_validates():
    for role in ("chapter", "part", "front_matter", "back_matter",
                 "contents", "title", "ignore"):
        assert bc.Division(candidate_id="h001", role=role, reason="x").role == role


def test_a_missing_division_records_where_it_hides():
    m = bc.MissingDivision(expected_ordinal=17, inside_candidate_id="h016",
                           evidence="TOC lists 18; only 17 headings exist")
    assert m.inside_candidate_id == "h016"


def test_the_map_schema_is_provider_safe():
    """Same rule as every other agent here: strict structured outputs reject oneOf."""
    import json
    schema = json.dumps(bc.BookMap.model_json_schema())
    assert "oneOf" not in schema and "discriminator" not in schema


# --- the brief: evidence in, noise out ---------------------------------------------

def test_the_brief_carries_only_judgeable_evidence():
    """hrefs and block indices are how CODE reassembles the book. In a prompt they are
    noise, and noise in a per-book prompt is paid for on every book."""
    candidates = [{**_cand("h001", "Chapter I"), "href": "x.xhtml",
                   "doc_index": 3, "block_index": 0}]
    sent = bc.brief(candidates, [])["candidates"][0]
    assert "href" not in sent and "doc_index" not in sent
    assert sent["words_after"] == 800 and sent["text"] == "Chapter I"


def test_the_brief_labels_the_toc_as_a_claim():
    """The naming is the point: five of seven books disagreed with their own TOC."""
    payload = bc.brief([], [{"title": "Contents"}])
    assert "toc_claims" in payload and payload["toc_entry_count"] == 1


def test_the_brief_states_both_counts_so_a_mismatch_is_visible():
    payload = bc.brief([_cand("h001", "Chapter I")], [{"title": "a"}, {"title": "b"}])
    assert payload["headings_found"] == 1 and payload["toc_entry_count"] == 2


# --- the five failure shapes, one test each ----------------------------------------

def test_a_split_heading_is_not_a_chapter():
    """Frankenstein sets its title across two lines; the first has no text under it.
    Exercised through map_book with a fake caller, so the prompt is built for real."""
    fake = _Fake(_map([
        {"candidate_id": "h001", "role": "title", "reason": "no prose follows"},
        {"candidate_id": "h002", "role": "chapter", "ordinal": 1, "reason": "prose"},
    ], structure="1 chapter after a two-line title"))
    result = bc.map_book(
        [_cand("h001", "Frankenstein;", words_after=0, series=None, ordinal=None),
         _cand("h002", "or, the Modern Prometheus")], [], _agent=fake)
    assert [d.role for d in result.divisions] == ["title", "chapter"]
    assert len(bc.chapters(result)) == 1


def test_the_prompt_carries_the_skill_and_the_evidence():
    fake = _Fake(_map([{"candidate_id": "h001", "role": "chapter",
                        "ordinal": 1, "reason": "c"}]))
    bc.map_book([_cand("h001", "Chapter I")], [{"title": "Chapter I"}], _agent=fake)
    assert "book cartographer" in fake.prompt
    assert "words_after" in fake.prompt and "toc_claims" in fake.prompt


def test_usage_is_reported_back_for_the_spend_record():
    fake = _Fake(_map([{"candidate_id": "h001", "role": "chapter",
                        "ordinal": 1, "reason": "c"}]))
    usage: dict = {}
    bc.map_book([_cand("h001", "Chapter I")], [], usage=usage, _agent=fake)
    assert usage["input_tokens"] == 100 and usage["output_tokens"] == 20


def test_chapters_are_the_only_counted_role():
    book_map = bc.BookMap.model_validate(_map([
        {"candidate_id": "h001", "role": "title", "reason": "t"},
        {"candidate_id": "h002", "role": "chapter", "ordinal": 1, "reason": "c"},
        {"candidate_id": "h003", "role": "contents", "reason": "toc as prose"},
        {"candidate_id": "h004", "role": "chapter", "ordinal": 2, "reason": "c"},
        {"candidate_id": "h005", "role": "back_matter", "reason": "note"},
    ]))
    assert [d.candidate_id for d in bc.chapters(book_map)] == ["h002", "h004"]


def test_letters_and_chapters_both_count_as_divisions():
    """Frankenstein is 4 letters plus 24 chapters = 28 divisions. Series is recorded,
    not counted - a reader reads them in one sequence."""
    book_map = bc.BookMap.model_validate(_map([
        {"candidate_id": "h001", "role": "chapter", "series": "letter",
         "ordinal": 1, "reason": "Letter 1"},
        {"candidate_id": "h002", "role": "chapter", "series": "chapter",
         "ordinal": 2, "reason": "Chapter 1"},
    ]))
    assert len(bc.chapters(book_map)) == 2
    assert {d.series for d in bc.chapters(book_map)} == {"letter", "chapter"}


def test_a_missing_heading_is_reported_rather_than_forced():
    """Peter Pan: 18 claimed, 17 headings. Neither 17 nor a silent 18 is the answer."""
    book_map = bc.BookMap.model_validate(_map(
        [{"candidate_id": f"h{i:03d}", "role": "chapter", "ordinal": i,
          "reason": "c"} for i in range(1, 18)],
        structure="17 marked headings for 18 claimed chapters",
        missing=[{"expected_ordinal": 17, "inside_candidate_id": "h016",
                  "evidence": "TOC lists 18; h016 runs to twice the median length"}]))
    assert len(bc.chapters(book_map)) == 17
    assert book_map.missing[0].inside_candidate_id == "h016"


def test_back_matter_is_not_a_chapter():
    """Dracula opens 'NOTE' as a chapter, which is what made 29 out of 28."""
    book_map = bc.BookMap.model_validate(_map([
        {"candidate_id": "h001", "role": "chapter", "ordinal": 1, "reason": "c"},
        {"candidate_id": "h002", "role": "back_matter", "reason": "closing note"},
    ]))
    assert len(bc.chapters(book_map)) == 1


def test_a_part_is_recorded_without_being_counted_as_a_chapter():
    book_map = bc.BookMap.model_validate(_map([
        {"candidate_id": "h001", "role": "part", "reason": "PART I"},
        {"candidate_id": "h002", "role": "chapter", "ordinal": 1, "reason": "c"},
    ]))
    assert len(bc.chapters(book_map)) == 1


def test_the_map_round_trips_through_json():
    book_map = bc.BookMap.model_validate(_map(
        [{"candidate_id": "h001", "role": "chapter", "ordinal": 1, "reason": "c"}]))
    assert bc.BookMap.model_validate_json(book_map.model_dump_json()).structure
