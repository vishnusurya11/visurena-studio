"""Five-iterations build B14 (2026-10-20): Jekyll's chapters are named, not
numbered ("STORY OF THE DOOR", part 0), and the composed credit line read
`Chapter STORY OF THE DOOR of Part One of Robert Louis Stevenson's Dr Jekyll
and Mr Hyde, "", in the public domain.` -- live on ep01's public page
(youtube.json).  A numeral is read only from a `^[IVXLC]+\\. ` title; a named
chapter is credited by its title and the episode's number; and G-META refuses
empty quotes or a bare chapter name, so recheck regenerates a broken line
before an upload.  WotW's line is pinned byte-equal.  $0: no call."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "publish"))

import metadata  # noqa: E402

SHIPPED_EP01 = ("Chapter STORY OF THE DOOR of Part One of Robert Louis Stevenson's "
                "Dr Jekyll and Mr Hyde, \"\", in the public domain.")
WOTW_PRIOR = [{"description": "Chapter XVI of Book One of H. G. Wells's The War of the Worlds (1898), "
                              "\"The Exodus from London\", in the public domain."}]


def jekyll(tmp_path):
    src = tmp_path / "source"
    src.mkdir(parents=True)
    chapters = [{"title": "Front matter", "part": 0}, {"title": "STORY OF THE DOOR", "part": 0},
                {"title": "SEARCH FOR MR. HYDE", "part": 0}]
    (src / "book.json").write_text(json.dumps({
        "title": "The strange case of Dr. Jekyll and Mr. Hyde", "author": "Robert Louis Stevenson",
        "series": "Robert Louis Stevenson", "display_title": "Dr Jekyll and Mr Hyde", "episodes": 10,
        "chapters": chapters}), encoding="utf-8")
    return tmp_path


def wotw(tmp_path):
    src = tmp_path / "source"
    src.mkdir(parents=True)
    chapters = [{"title": "PREFACE", "part": 1}, {"title": "I. THE EVE OF THE WAR.", "part": 1},
                {"title": "I. UNDER FOOT.", "part": 2}]
    (src / "book.json").write_text(json.dumps({"title": "The War of the Worlds", "author": "H. G. Wells",
                                               "display_title": "The War of the Worlds",
                                               "chapters": chapters}), encoding="utf-8")
    return tmp_path


def test_a_named_chapter_has_no_numeral(tmp_path):
    assert metadata.chapter_marker(jekyll(tmp_path), 2) == ("", "Search for Mr. Hyde", 1)


def test_a_named_chapter_is_credited_by_its_title_and_number(tmp_path):
    line = metadata.attribution(jekyll(tmp_path), 1, [])
    assert line == ("\"Story of the Door\", Chapter 1 of Dr Jekyll and Mr Hyde by "
                    "Robert Louis Stevenson, in the public domain.")
    assert "Part" not in line and '""' not in line


def test_the_numbered_book_keeps_its_line_byte_equal(tmp_path):
    assert metadata.attribution(wotw(tmp_path), 2, WOTW_PRIOR) == (
        "Chapter I of Book Two of H. G. Wells's The War of the Worlds (1898), "
        "\"Under Foot\", in the public domain.")


def test_the_shipped_ep01_line_is_a_credit_fault():
    assert metadata.credit_faults(SHIPPED_EP01)
    assert metadata.credit_faults("x Chapter  of y")
    assert not metadata.credit_faults(WOTW_PRIOR[0]["description"])
    assert not metadata.credit_faults("\"Story of the Door\", Chapter 1 of Dr Jekyll and Mr Hyde by R, in the public domain.")
