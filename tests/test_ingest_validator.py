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



def test_samples_take_edges_with_cut_markers(tmp_path):
    """Regression: real-run false positive — last paragraph sampled from its START
    made intact chapters look truncated. Last para must show its true ENDING."""
    src = _make_book_dir(tmp_path)
    chapter = json.loads((src / "chapters" / "ch_01.json").read_text(encoding="utf-8"))
    chapter["paragraphs"][-1]["text"] = ("x" * 500) + " and so it ended properly."
    (src / "chapters" / "ch_01.json").write_text(json.dumps(chapter), encoding="utf-8")
    text = iv.build_input(src)
    assert "and so it ended properly." in text     # true ending visible to the judge
    assert "[cut]" in text                          # our slice explicitly marked


def test_sampling_an_empty_chapter_does_not_crash():
    """A book that opens straight on Chapter 1 has an empty front-matter sentinel, and
    the sampler indexed paragraphs[0] unconditionally. Frankenstein crashed here after
    its checks had already PASSED - the validator killed a successful parse."""
    from agents.ingest_validator import _sample
    sample = _sample({"n": 0, "part": 0, "title": "Front matter", "paragraphs": []})
    assert sample["paragraph_count"] == 0
    assert sample["first_paragraph"] == "" and sample["last_paragraph"] == ""


def test_sampling_a_one_paragraph_chapter_uses_it_for_both_edges():
    from agents.ingest_validator import _sample
    sample = _sample({"n": 1, "part": 0, "title": "A",
                      "paragraphs": [{"text": "only one"}]})
    assert "only one" in sample["first_paragraph"]
    assert "only one" in sample["last_paragraph"]


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


def test_a_structural_issue_still_blocks():
    import pytest
    from scripts.analysis.step_01_ingest import plan_remedies
    from agents.ingest_validator import Issue
    with pytest.raises(ValueError, match="no safe auto-remedy"):
        plan_remedies([Issue(kind="structure", chapter=1, severity="minor", note="no divisions found")])


def test_a_garbled_issue_still_blocks():
    import pytest
    from scripts.analysis.step_01_ingest import plan_remedies
    from agents.ingest_validator import Issue
    with pytest.raises(ValueError, match="no safe auto-remedy"):
        plan_remedies([Issue(kind="garbled", chapter=3, severity="minor", note="mojibake")])


def test_a_fixable_issue_still_returns_its_remedy():
    from scripts.analysis.step_01_ingest import plan_remedies
    from agents.ingest_validator import Issue
    assert plan_remedies([Issue(kind="boilerplate", chapter=0, severity="minor", note="pg text")]) == \
        ["strip_pg_phrases"]


def test_an_advisory_issue_alongside_a_blocking_one_still_blocks():
    import pytest
    from scripts.analysis.step_01_ingest import plan_remedies
    from agents.ingest_validator import Issue
    with pytest.raises(ValueError):
        plan_remedies([Issue(kind="front_matter", chapter=0, severity="minor", note="preface"),
                       Issue(kind="structure", chapter=1, severity="minor", note="no divisions")])
