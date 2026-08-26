"""Tests for agents.ingest_validator — input building + verdict handling. LLM faked."""

from __future__ import annotations

import json

from agents import ingest_validator as iv


def _make_book_dir(tmp_path):
    src = tmp_path / "source"
    (src / "chapters").mkdir(parents=True)
    manifest = {
        "title": "A Study in Scarlet", "author": "Arthur Conan Doyle",
        "parts": [{"n": 1, "title": "PART I."}],
        "chapters": [
            {"n": 1, "part": 1, "title": "CHAPTER I.", "file": "chapters/ch_01.json",
             "paragraphs": 2, "words": 14},
        ],
    }
    (src / "book.json").write_text(json.dumps(manifest), encoding="utf-8")
    chapter = {"n": 1, "part": 1, "title": "CHAPTER I.", "paragraphs": [
        {"n": 1, "text": "In the year 1878 I took my degree."},
        {"n": 2, "text": "The campaign brought me nothing but misfortune."},
    ]}
    (src / "chapters" / "ch_01.json").write_text(json.dumps(chapter), encoding="utf-8")
    return src


def test_build_input_contains_manifest_and_samples(tmp_path):
    src = _make_book_dir(tmp_path)
    text = iv.build_input(src)
    assert "A Study in Scarlet" in text
    assert "In the year 1878" in text                    # first paragraph sample
    assert "nothing but misfortune" in text              # last paragraph sample
    assert "PART I." in text


def test_build_input_truncates_long_paragraphs(tmp_path):
    src = _make_book_dir(tmp_path)
    chapter = json.loads((src / "chapters" / "ch_01.json").read_text(encoding="utf-8"))
    chapter["paragraphs"][0]["text"] = "word " * 500
    (src / "chapters" / "ch_01.json").write_text(json.dumps(chapter), encoding="utf-8")
    text = iv.build_input(src)
    assert len(text) < 20_000  # samples stay small — never the whole book


def test_review_returns_verdict_from_llm(tmp_path, monkeypatch):
    src = _make_book_dir(tmp_path)
    canned = iv.Verdict(ok=True, issues=[], summary="clean ingest")
    monkeypatch.setattr(iv.llm, "structured",
                        lambda tier, prompt, schema, **kw: canned)
    verdict = iv.review(src)
    assert verdict.ok is True
    assert verdict.summary == "clean ingest"


def test_review_passes_skill_and_tier(tmp_path, monkeypatch):
    src = _make_book_dir(tmp_path)
    seen = {}

    def fake_structured(tier, prompt, schema, **kw):
        seen.update(tier=tier, prompt=prompt, schema=schema)
        return iv.Verdict(ok=False, issues=[iv.Issue(
            chapter=3, kind="boilerplate", severity="high", note="license text")],
            summary="issues found")

    monkeypatch.setattr(iv.llm, "structured", fake_structured)
    verdict = iv.review(src)
    assert seen["tier"] == iv.TIER
    assert "quality control for a book-ingestion pipeline" in seen["prompt"]  # skill loaded
    assert seen["schema"] is iv.Verdict
    assert verdict.issues[0].kind == "boilerplate"


def test_review_passes_usage_through(tmp_path, monkeypatch):
    src = _make_book_dir(tmp_path)

    def fake_structured(tier, prompt, schema, usage=None, **kw):
        if usage is not None:
            usage.update(input_tokens=100, output_tokens=10, total_tokens=110, tier=tier)
        return iv.Verdict(ok=True, issues=[], summary="fine")

    monkeypatch.setattr(iv.llm, "structured", fake_structured)
    usage = {}
    iv.review(src, usage=usage)
    assert usage["total_tokens"] == 110  # the exact call shape the step runner uses



def test_the_judged_edge_is_never_our_own_truncation():
    """Supersedes the old [cut]-marker contract. Marking our slice was a workaround for
    sending truncations at all; whole sentences remove the need for the marker and the
    class of false positive that came with it."""
    from agents.ingest_validator import build_input
    from pathlib import Path
    import json, tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "chapters").mkdir()
        (root / "chapters" / "ch_01.json").write_text(json.dumps({
            "n": 1, "part": 0, "title": "A",
            "paragraphs": [{"n": 1, "text": "x" * 900 + " and so it ended properly."}]}),
            encoding="utf-8")
        (root / "book.json").write_text(json.dumps({
            "title": "T", "author": "A", "parts": [],
            "chapters": [{"n": 1, "file": "chapters/ch_01.json"}]}), encoding="utf-8")
        text = build_input(root)
    assert "[cut]" not in text


def test_sampling_an_empty_chapter_does_not_crash():
    """A book that opens straight on Chapter 1 has an empty front-matter sentinel, and
    the sampler indexed paragraphs[0] unconditionally. Frankenstein crashed here after
    its checks had already PASSED - the validator killed a successful parse."""
    from agents.ingest_validator import _sample
    sample = _sample({"n": 0, "part": 0, "title": "Front matter", "paragraphs": []})
    assert sample["paragraph_count"] == 0
    assert sample["opens_with"] == "" and sample["ends_with"] == ""


def test_sampling_a_one_paragraph_chapter_uses_it_for_both_edges():
    from agents.ingest_validator import _sample
    sample = _sample({"n": 1, "part": 0, "title": "A",
                      "paragraphs": [{"text": "only one"}]})
    assert "only one" in sample["opens_with"]
    assert "only one" in sample["ends_with"]


# --- advisory issue kinds (2026-08-26) ---------------------------------------------
#
# Once the cartographer got the CHAPTERS right, two books still failed on front matter:
# Pride and Prejudice carries a real 225-paragraph Saintsbury preface and Tom Sawyer a
# 203-paragraph one. Both had every chapter correct - 61 of 61 for P&P. Front matter
# having content is what front matter IS, so blocking a whole ingest on it stops a
# correct parse over a matter of taste.
#
# Structure, boundary and garbled stay blocking: those say the TEXT is wrong.

def test_a_front_matter_issue_does_not_block_the_ingest():
    from scripts.analysis.step_01_ingest import ADVISORY_KINDS, plan_remedies
    from agents.ingest_validator import Issue
    assert "front_matter" in ADVISORY_KINDS
    plan_remedies([Issue(kind="front_matter", chapter=0, severity="minor", note="preface present")])


def test_a_fixable_issue_still_returns_its_remedy():
    from scripts.analysis.step_01_ingest import plan_remedies
    from agents.ingest_validator import Issue
    assert plan_remedies([Issue(kind="boilerplate", chapter=0, severity="minor", note="pg text")]) == \
        ["strip_pg_phrases"]


def test_the_first_sentence_is_whole():
    from agents.ingest_validator import first_sentence
    text = "It was the best of times. It was the worst of times. And so on."
    assert first_sentence(text) == "It was the best of times."


def test_the_last_sentence_is_whole():
    from agents.ingest_validator import last_sentence
    text = "It was the best of times. It was the worst of times."
    assert last_sentence(text) == "It was the worst of times."


def test_a_paragraph_that_truly_ends_mid_sentence_is_visible_as_such():
    """The real damage this check exists to find must survive the change."""
    from agents.ingest_validator import last_sentence
    assert last_sentence("He turned the corner and saw") == "He turned the corner and saw"


def test_a_single_sentence_paragraph_works_from_both_ends():
    from agents.ingest_validator import first_sentence, last_sentence
    text = "Only one sentence here."
    assert first_sentence(text) == text and last_sentence(text) == text


def test_a_very_long_sentence_is_still_capped():
    """A cap is still needed - one runaway sentence must not blow up a per-book prompt."""
    from agents.ingest_validator import first_sentence, MAX_SENTENCE
    assert len(first_sentence("word " * 500)) <= MAX_SENTENCE + 8


def test_dialogue_punctuation_does_not_split_a_sentence_early():
    from agents.ingest_validator import first_sentence
    text = '"Whatever have you been doing with yourself, Watson?" he asked. Then he sat.'
    assert first_sentence(text).endswith("he asked.")


def test_the_sample_carries_both_whole_sentences():
    from agents.ingest_validator import _sample
    chapter = {"n": 1, "part": 0, "title": "A", "paragraphs": [
        {"text": "First sentence. Second one."}, {"text": "Middle."},
        {"text": "Penultimate. Final sentence."}]}
    sample = _sample(chapter)
    assert sample["opens_with"] == "First sentence."
    assert sample["ends_with"] == "Final sentence."


def test_the_sample_no_longer_advertises_a_cut_edge():
    from agents.ingest_validator import _sample
    chapter = {"n": 1, "part": 0, "title": "A",
               "paragraphs": [{"text": "Short. " * 200}]}
    sample = _sample(chapter)
    assert "[cut]" not in sample["opens_with"] and "[cut]" not in sample["ends_with"]


def test_an_abbreviation_does_not_end_a_sentence():
    """Peter Pan chapter 2 was reported as opening with the single word "Mrs." - the
    splitter ended the sentence at the honorific because a capital followed it. A
    sampler bug that manufactures the exact damage it is looking for is worse than no
    sampler."""
    from agents.ingest_validator import first_sentence
    assert first_sentence("Mrs. Darling screamed, and the door opened. Then silence.") \
        == "Mrs. Darling screamed, and the door opened."


def test_common_honorifics_and_initials_are_all_handled():
    from agents.ingest_validator import first_sentence
    for opener in ("Mr. Darling was a good man.", "Dr. Watson returned home.",
                   "St. Paul's loomed above them.", "Capt. Hook drew his sword.",
                   "J. M. Barrie wrote it down."):
        assert first_sentence(opener + " Next sentence.") == opener


def test_a_real_sentence_break_after_a_period_still_splits():
    from agents.ingest_validator import first_sentence
    assert first_sentence("He went home. She stayed.") == "He went home."


def test_boundary_is_advisory_because_damage_is_checked_mechanically():
    """`boundary` blocked four books whose chapters were demonstrably correct - Peter
    Pan chapter 1 was flagged for "opening mid-sentence" on "All children, except one,
    grow up.", the book's famous first line.

    The reason it can be advisory is not that the agent is bad at it. It is that
    _garbled() already checks mechanical damage over EVERY paragraph of every chapter,
    while the agent sees one sentence from each end. Blocking on the weaker evidence
    while the stronger check passes is backwards."""
    from scripts.analysis.step_01_ingest import ADVISORY_KINDS, plan_remedies
    from agents.ingest_validator import Issue
    assert "boundary" in ADVISORY_KINDS
    plan_remedies([Issue(kind="boundary", chapter=1, severity="minor",
                         note="opens mid-sentence")])


def test_an_unfixable_opinion_does_not_halt_the_ingest():
    from scripts.analysis.step_01_ingest import plan_remedies
    from agents.ingest_validator import Issue
    assert plan_remedies([Issue(kind="structure", chapter=1, severity="blocking",
                                note="manifest title looks wrong")]) == []


def test_an_opinion_that_names_a_remedy_still_triggers_it():
    from scripts.analysis.step_01_ingest import plan_remedies
    from agents.ingest_validator import Issue
    assert plan_remedies([Issue(kind="boilerplate", chapter=0, severity="minor",
                                note="pg text")]) == ["strip_pg_phrases"]


def test_unfixable_issues_are_returned_for_logging_not_discarded():
    """Silently dropping a finding would be worse than blocking on it."""
    from scripts.analysis.step_01_ingest import unfixable_issues
    from agents.ingest_validator import Issue
    issues = [Issue(kind="structure", chapter=1, severity="blocking", note="a"),
              Issue(kind="boilerplate", chapter=0, severity="minor", note="b")]
    assert [i.kind for i in unfixable_issues(issues)] == ["structure"]


def test_mechanical_checks_are_untouched_by_this():
    """They raise on their own, from finalize, and are the real gate."""
    import pytest
    from scripts.analysis.step_01_ingest import _check_chapters
    with pytest.raises(ValueError, match="no chapters"):
        _check_chapters([{"n": 0, "part": 0, "title": "F",
                          "paragraphs": [{"n": 1, "text": "whole novel"}]}], None)


def test_no_agent_opinion_halts_an_ingest_that_measured_clean():
    """Supersedes four tests that asserted structure/garbled OPINIONS block. They no
    longer do, and that is the point: _check_chapters and _garbled measure every
    paragraph and raise from finalize(), while the agent sees samples. Blocking on the
    weaker evidence while the stronger check passes is backwards, and it kept five
    correct books out of the pipeline."""
    from scripts.analysis.step_01_ingest import plan_remedies, unfixable_issues
    from agents.ingest_validator import Issue
    opinions = [Issue(kind=k, chapter=1, severity="blocking", note="n")
                for k in ("structure", "garbled", "boundary", "completeness")]
    assert plan_remedies(opinions) == []
    # structure, garbled and completeness are unfixable-but-recorded; boundary is
    # advisory and is not even recorded as unresolved.
    assert [i.kind for i in unfixable_issues(opinions)] == [
        "structure", "garbled", "completeness"]
