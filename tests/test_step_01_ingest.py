"""Tests for analysis step 01 substeps (01_01 read_source .. 01_04 finalize)."""

from __future__ import annotations

import json

import pytest

from scripts.analysis import step_01_ingest as s01
from studio import epub


# --- studio.epub (used by 01_01) ---


def test_read_epub_metadata_and_spine(fixture_epub):
    raw = epub.read_epub(fixture_epub)
    assert raw["title"] == "A Study in Scarlet"
    assert raw["author"] == "Arthur Conan Doyle"
    assert [d["href"] for d in raw["spine"]] == [
        "front.xhtml", "contents.xhtml", "part1.xhtml", "part2.xhtml", "license.xhtml"]


def test_read_epub_toc_levels(fixture_epub):
    toc = epub.read_epub(fixture_epub)["toc"]
    assert toc[0] == {"title": "PART I. THE REMINISCENCES", "href": "part1.xhtml", "level": 1}
    assert toc[1]["level"] == 2  # chapters nested under parts
    assert len(toc) == 6  # 2 parts + 4 chapters; landmarks nav ignored


def test_html_to_blocks_kinds():
    blocks = epub.html_to_blocks("<h2>Title</h2><p>One two.</p><p>  </p>")
    assert blocks == [{"kind": "heading", "text": "Title"},
                      {"kind": "para", "text": "One two."}]


# --- 01_02 clean ---


def test_clean_drops_license_doc_and_strips_pg_header(fixture_epub):
    raw = epub.read_epub(fixture_epub)
    clean = s01.clean(raw)
    hrefs = [d["href"] for d in clean["docs"]]
    assert "license.xhtml" not in hrefs      # after *** END *** -> empty -> dropped
    assert "nav.xhtml" not in hrefs
    front = next(d for d in clean["docs"] if d["href"] == "front.xhtml")
    texts = [b["text"] for b in front["blocks"]]
    assert texts == ["This preface paragraph introduces the tale to the reader."]


# --- 01_03 chapterize ---


@pytest.fixture()
def chapterized(fixture_epub, tmp_path):
    raw = epub.read_epub(fixture_epub)
    out_dir = tmp_path / "source"
    chapters, parts_meta, _toc_expected = s01.chapterize(s01.clean(raw), raw["toc"], out_dir)
    return chapters, parts_meta, out_dir


def test_chapterize_continuous_numbering_across_parts(chapterized):
    chapters, _, _ = chapterized
    real = [c for c in chapters if c["part"] > 0]
    assert [c["n"] for c in real] == [1, 2, 3, 4]
    assert [c["part"] for c in real] == [1, 1, 2, 2]
    assert real[2]["title"] == "Chapter III. On the Great Plain"


def test_chapterize_front_matter_is_chapter_zero(chapterized):
    chapters, _, _ = chapterized
    front = chapters[0]
    assert front["n"] == 0 and front["part"] == 0
    assert "preface paragraph" in front["paragraphs"][0]["text"]


def test_chapterize_numbers_paragraphs_and_writes_files(chapterized):
    chapters, _, out_dir = chapterized
    ch1 = json.loads((out_dir / "chapters" / "ch_01.json").read_text("utf-8"))
    assert [p["n"] for p in ch1["paragraphs"]] == [1, 2]
    assert ch1["paragraphs"][0]["text"].startswith("In the year 1878")


# --- 01_04 finalize ---


def test_finalize_writes_manifest(chapterized, fixture_epub):
    chapters, parts_meta, out_dir = chapterized
    manifest = s01.finalize(chapters, out_dir, fixture_epub,
                            title="A Study in Scarlet", author="Arthur Conan Doyle",
                            expected_chapters=4, parts=parts_meta)
    on_disk = json.loads((out_dir / "book.json").read_text("utf-8"))
    assert on_disk == manifest
    assert len(manifest["source_sha256"]) == 64
    assert [c["n"] for c in manifest["chapters"]] == [0, 1, 2, 3, 4]
    assert manifest["chapters"][1]["words"] > 0


def test_finalize_fails_loud_on_chapter_count_mismatch(chapterized, fixture_epub):
    chapters, _, out_dir = chapterized
    with pytest.raises(ValueError, match="chapter count"):
        s01.finalize(chapters, out_dir, fixture_epub,
                     title="t", author="a", expected_chapters=14)
    assert not (out_dir / "book.json").exists()  # no manifest on failure


# --- real pg244 TOC shape: FLAT, junk entries, PART II restarts CHAPTER I ---

FLAT_TOC = [
    {"title": "A STUDY IN SCARLET", "href": "x1", "level": 1},
    {"title": "CONTENTS", "href": "x2", "level": 1},
    {"title": "A STUDY IN SCARLET.", "href": "x3", "level": 1},
    {"title": "PART I.", "href": "x4", "level": 1},
    {"title": "CHAPTER I. MR. SHERLOCK HOLMES.", "href": "x5", "level": 1},
    {"title": "CHAPTER II. THE SCIENCE OF DEDUCTION.", "href": "x6", "level": 1},
    {"title": "PART II. The Country of the Saints.", "href": "x7", "level": 1},
    {"title": "CHAPTER I. ON THE GREAT ALKALI PLAIN.", "href": "x8", "level": 1},
    {"title": "THE FULL PROJECT GUTENBERG\u2122 LICENSE", "href": "x9", "level": 1},
]


def test_flat_toc_parts_by_title_pattern_and_junk_filtered():
    parts, chapters, parts_meta = s01._toc_parts_and_chapters(
        FLAT_TOC, book_title="A Study in Scarlet")
    assert len(parts) == 2
    assert [p["title"] for p in parts_meta] == ["PART I.", "PART II. The Country of the Saints."]
    assert len(chapters) == 3  # junk (title pages, contents, license) excluded
    assert list(chapters.values()) == [1, 2, 3]  # continuous across parts


def test_flat_toc_chapterize_assigns_parts_and_matches_short_part_heading(tmp_path):
    book = {"title": "A Study in Scarlet", "author": "x", "docs": [
        {"href": "d1", "blocks": [
            {"kind": "heading", "text": "PART I."},
            {"kind": "heading", "text": "CHAPTER I. MR. SHERLOCK HOLMES."},
            {"kind": "para", "text": "In the year 1878 I took my degree."},
            {"kind": "heading", "text": "CHAPTER II. THE SCIENCE OF DEDUCTION."},
            {"kind": "para", "text": "We met next day."},
            {"kind": "heading", "text": "PART II."},   # short heading; toc title is longer
            {"kind": "heading", "text": "CHAPTER I. ON THE GREAT ALKALI PLAIN."},
            {"kind": "para", "text": "An arid desert."},
        ]},
    ]}
    chapters, parts_meta, _ = s01.chapterize(book, FLAT_TOC, tmp_path / "source")
    real = [c for c in chapters if c["part"] > 0]
    assert [(c["n"], c["part"]) for c in real] == [(1, 1), (2, 1), (3, 2)]
    assert real[2]["title"] == "CHAPTER I. ON THE GREAT ALKALI PLAIN."


def test_clean_strips_license_doc_after_end_marker_globally(fixture_epub):
    raw = epub.read_epub(fixture_epub)
    # move the END marker into the last content doc; the license doc has no marker
    raw["spine"][-1]["raw_html"] = "<html><body><p>Pure license text here.</p></body></html>"
    raw["spine"][-2]["raw_html"] += "<p>*** END OF THE PROJECT GUTENBERG EBOOK ***</p>"
    clean = s01.clean(raw)
    all_text = " ".join(b["text"] for d in clean["docs"] for b in d["blocks"])
    assert "Pure license text" not in all_text  # docs after END are dropped globally


# --- 01_06 improve: deterministic remedy playbook (no agent) ---


@pytest.fixture(autouse=True)
def _reset_adjustments():
    s01.ADJUSTMENTS["strip_pg_phrases"] = False
    yield
    s01.ADJUSTMENTS["strip_pg_phrases"] = False


def _issue(kind, chapter=1):
    from agents.ingest_validator import Issue
    return Issue(chapter=chapter, kind=kind, severity="high", note="test")


def test_plan_remedies_known_kind_returns_actions():
    actions = s01.plan_remedies([_issue("boilerplate")])
    assert actions == ["strip_pg_phrases"]


def test_plan_remedies_unknown_kind_escalates():
    with pytest.raises(ValueError, match="no safe auto-remedy"):
        s01.plan_remedies([_issue("boundary")])


def test_apply_remedies_flips_adjustment():
    s01.apply_remedies(["strip_pg_phrases"])
    assert s01.ADJUSTMENTS["strip_pg_phrases"] is True


def test_clean_strips_pg_phrases_when_adjusted(fixture_epub):
    raw = epub.read_epub(fixture_epub)
    raw["spine"][2]["raw_html"] = raw["spine"][2]["raw_html"].replace(
        "</body>", "<p>Visit www.gutenberg.org for more books.</p></body>")  # part1 doc
    baseline = s01.clean(raw)
    assert any("gutenberg.org" in b["text"] for d in baseline["docs"] for b in d["blocks"])
    s01.apply_remedies(["strip_pg_phrases"])
    adjusted = s01.clean(raw)
    assert not any("gutenberg.org" in b["text"]
                   for d in adjusted["docs"] for b in d["blocks"])



# --- regressions from the first real run (agent verdict 2026-08-23) ---


def test_head_title_text_never_becomes_a_paragraph():
    blocks = epub.html_to_blocks(
        "<html><head><title>Book | Project Gutenberg</title><style>p{}</style></head>"
        "<body><p>Real text.</p></body></html>")
    assert blocks == [{"kind": "para", "text": "Real text."}]


def test_clean_drops_contents_doc(fixture_epub):
    raw = epub.read_epub(fixture_epub)
    clean = s01.clean(raw)
    hrefs = [d["href"] for d in clean["docs"]]
    assert "contents.xhtml" not in hrefs          # CONTENTS page is chrome, not content
    all_text = " ".join(b["text"] for d in clean["docs"] for b in d["blocks"])
    assert "Project Gutenberg" not in all_text    # no title-tag junk anywhere


def test_finalize_rejects_leaked_boilerplate(chapterized, fixture_epub):
    chapters, parts_meta, out_dir = chapterized
    chapters[1]["paragraphs"].append(
        {"n": len(chapters[1]["paragraphs"]) + 1,
         "text": "A Study in Scarlet | Project Gutenberg"})
    with pytest.raises(ValueError, match="boilerplate"):
        s01.finalize(chapters, out_dir, fixture_epub, title="t", author="a",
                     expected_chapters=4, parts=parts_meta)


def test_plan_remedies_applies_fixable_before_escalating():
    issues = [_issue("front_matter"), _issue("boilerplate")]
    assert s01.plan_remedies(issues) == ["strip_pg_phrases"]  # fix what we can, re-check


def test_plan_remedies_escalates_only_when_nothing_fixable():
    with pytest.raises(ValueError, match="no safe auto-remedy"):
        s01.plan_remedies([_issue("front_matter"), _issue("boundary")])



def test_expected_chapters_derived_from_toc(chapterized, fixture_epub):
    chapters, parts_meta, out_dir = chapterized
    manifest = s01.finalize(chapters, out_dir, fixture_epub, title="t", author="a",
                            expected_chapters=None, toc_expected=4, parts=parts_meta)
    assert len([c for c in manifest["chapters"] if c["part"] > 0]) == 4


def test_toc_expectation_mismatch_fails_loud(chapterized, fixture_epub):
    chapters, parts_meta, out_dir = chapterized
    with pytest.raises(ValueError, match="chapter count"):
        s01.finalize(chapters, out_dir, fixture_epub, title="t", author="a",
                     expected_chapters=None, toc_expected=9, parts=parts_meta)
