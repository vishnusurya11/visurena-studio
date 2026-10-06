"""ep18 dry run (2026-10-06): the metadata model wrote "Chapter XVIII of Book One"
by imitating ep16's "Chapter XVI of Book One" -- but Book One has seventeen
chapters; chapter 18 is Book Two, Chapter I, "Under Foot".  A fact is composed
from source/book.json, never written by the model.  $0: no call."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "publish"))

import metadata  # noqa: E402

PRIOR = [{"description": "Chapter XVI of Book One of H. G. Wells's The War of the Worlds (1898), "
                         "\"The Exodus from London\", in the public domain."}]


def book(tmp_path):
    src = tmp_path / "source"
    src.mkdir(parents=True)
    chapters = [{"title": "PREFACE", "part": 1}] + \
        [{"title": f"{r}. CH {r}.", "part": 1} for r in ["I", "II"]] + \
        [{"title": "I. UNDER FOOT.", "part": 2}]
    (src / "book.json").write_text(json.dumps({"title": "The War of the Worlds", "author": "H. G. Wells",
                                               "display_title": "The War of the Worlds",
                                               "chapters": chapters}), encoding="utf-8")
    return tmp_path


def test_the_chapter_marker_reads_the_books_own_division(tmp_path):
    assert metadata.chapter_marker(book(tmp_path), 3) == ("I", "Under Foot", 2)


def test_the_attribution_names_book_two_chapter_one(tmp_path):
    line = metadata.attribution(book(tmp_path), 3, PRIOR)
    assert line == ("Chapter I of Book Two of H. G. Wells's The War of the Worlds (1898), "
                    "\"Under Foot\", in the public domain.")


def test_a_headline_keeps_small_words_lower():
    assert metadata.headline("WHAT WE SAW FROM THE RUINED HOUSE") == "What We Saw from the Ruined House"


def test_a_book_without_chapters_keeps_the_models_line(tmp_path):
    src = tmp_path / "source"
    src.mkdir(parents=True)
    (src / "book.json").write_text(json.dumps({"title": "T", "author": "A"}), encoding="utf-8")
    assert metadata.composed_attribution(tmp_path, 3, PRIOR) is None
