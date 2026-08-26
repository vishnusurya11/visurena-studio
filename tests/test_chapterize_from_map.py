"""Assemble chapters from the cartographer's map instead of by matching the TOC.

The deterministic path matched TOC entry text against body heading text and worked on 3
of 8 books. The map replaces that: every heading already has a ROLE, and a chapter opens
at each heading whose role is `chapter`. No text matching, so none of the five ways a
TOC and a body disagree can break it.
"""

from __future__ import annotations

from agents.book_cartographer import BookMap
from scripts.analysis import step_01_ingest as s1


def _book(blocks):
    """One document whose blocks are (kind, text) pairs."""
    return {"title": "T", "docs": [{"href": "a.xhtml", "blocks": [
        {"kind": k, "text": t, "ids": []} for k, t in blocks]}]}


def _map(roles):
    """roles: candidate_id -> role, in order."""
    divisions = [{"candidate_id": cid, "role": role, "reason": "t",
                  "ordinal": i + 1 if role == "chapter" else None}
                 for i, (cid, role) in enumerate(roles)]
    return BookMap.model_validate({"structure": "s", "divisions": divisions,
                                   "missing": []})


BLOCKS = [("heading", "TITLE PAGE"), ("para", "by an author"),
          ("heading", "Chapter I"), ("para", "First chapter prose."),
          ("heading", "Chapter II"), ("para", "Second chapter prose."),
          ("heading", "NOTE"), ("para", "Closing note.")]


def test_only_chapter_roles_open_chapters():
    chapters = s1.chapters_from_map(
        _book(BLOCKS),
        _map([("h001", "title"), ("h002", "chapter"),
              ("h003", "chapter"), ("h004", "back_matter")]))
    assert [c["n"] for c in chapters if c["n"] > 0] == [1, 2]


def test_the_titles_come_from_the_body_not_the_toc():
    chapters = s1.chapters_from_map(
        _book(BLOCKS),
        _map([("h001", "title"), ("h002", "chapter"),
              ("h003", "chapter"), ("h004", "back_matter")]))
    assert [c["title"] for c in chapters if c["n"] > 0] == ["Chapter I", "Chapter II"]


def test_prose_under_a_non_chapter_heading_is_not_lost():
    """A closing NOTE is not a chapter, but its words are still part of the book and
    must not vanish silently - silent loss is the failure mode of every join here."""
    chapters = s1.chapters_from_map(
        _book(BLOCKS),
        _map([("h001", "title"), ("h002", "chapter"),
              ("h003", "chapter"), ("h004", "back_matter")]))
    everything = " ".join(p["text"] for c in chapters for p in c["paragraphs"])
    assert "Closing note." in everything and "by an author" in everything


def test_prose_before_the_first_chapter_becomes_front_matter():
    chapters = s1.chapters_from_map(
        _book(BLOCKS),
        _map([("h001", "title"), ("h002", "chapter"),
              ("h003", "chapter"), ("h004", "back_matter")]))
    assert chapters[0]["n"] == 0
    assert "by an author" in chapters[0]["paragraphs"][0]["text"]


def test_a_part_role_sets_the_part_for_the_chapters_that_follow():
    blocks = [("heading", "PART I"), ("heading", "Chapter I"), ("para", "a"),
              ("heading", "PART II"), ("heading", "Chapter II"), ("para", "b")]
    chapters = s1.chapters_from_map(
        _book(blocks),
        _map([("h001", "part"), ("h002", "chapter"),
              ("h003", "part"), ("h004", "chapter")]))
    real = [c for c in chapters if c["n"] > 0]
    assert [c["part"] for c in real] == [1, 2]


def test_a_book_with_no_parts_leaves_part_at_zero():
    chapters = s1.chapters_from_map(
        _book(BLOCKS),
        _map([("h001", "title"), ("h002", "chapter"),
              ("h003", "chapter"), ("h004", "back_matter")]))
    assert {c["part"] for c in chapters if c["n"] > 0} == {0}


def test_chapters_are_numbered_contiguously_from_one():
    blocks = [("heading", "A"), ("para", "a"), ("heading", "B"), ("para", "b"),
              ("heading", "C"), ("para", "c")]
    chapters = s1.chapters_from_map(
        _book(blocks),
        _map([("h001", "chapter"), ("h002", "ignore"), ("h003", "chapter")]))
    assert [c["n"] for c in chapters if c["n"] > 0] == [1, 2]


def test_paragraph_numbering_restarts_within_each_chapter():
    blocks = [("heading", "A"), ("para", "a1"), ("para", "a2"),
              ("heading", "B"), ("para", "b1")]
    chapters = s1.chapters_from_map(
        _book(blocks), _map([("h001", "chapter"), ("h002", "chapter")]))
    real = [c for c in chapters if c["n"] > 0]
    assert [p["n"] for p in real[0]["paragraphs"]] == [1, 2]
    assert [p["n"] for p in real[1]["paragraphs"]] == [1]


def test_an_empty_front_matter_sentinel_is_still_emitted():
    """Later steps anchor on n == 0 whether or not the book has front matter."""
    blocks = [("heading", "Chapter I"), ("para", "prose")]
    chapters = s1.chapters_from_map(_book(blocks), _map([("h001", "chapter")]))
    assert chapters[0]["n"] == 0


def test_a_map_naming_an_unknown_candidate_does_not_crash():
    """The agent returns ids; a hallucinated one must be ignored, not fatal."""
    chapters = s1.chapters_from_map(
        _book(BLOCKS),
        _map([("h001", "chapter"), ("h999", "chapter")]))
    assert [c["n"] for c in chapters if c["n"] > 0] == [1]


def test_a_mapped_chapter_with_no_prose_is_folded_forward():
    """Moby Dick: the map called a heading a chapter and no prose followed it, so
    chapter 100 came out empty. The skill tells the agent not to do this; the code must
    survive it doing so anyway - an agent's output is input, not a guarantee."""
    blocks = [("heading", "CHAPTER 100"), ("heading", "CHAPTER 101"), ("para", "prose")]
    chapters = s1.chapters_from_map(
        _book(blocks), _map([("h001", "chapter"), ("h002", "chapter")]))
    real = [c for c in chapters if c["n"] > 0]
    assert len(real) == 1
    assert real[0]["title"] == "CHAPTER 100 CHAPTER 101"


def test_folding_keeps_the_numbering_contiguous():
    blocks = [("heading", "A"), ("heading", "B"), ("para", "b"),
              ("heading", "C"), ("para", "c")]
    chapters = s1.chapters_from_map(
        _book(blocks),
        _map([("h001", "chapter"), ("h002", "chapter"), ("h003", "chapter")]))
    assert [c["n"] for c in chapters if c["n"] > 0] == [1, 2]
