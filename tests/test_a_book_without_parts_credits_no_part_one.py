"""Growth apply 2026-10-21 (VERIFY flag): Jekyll ep01's live description reads
`Chapter STORY OF THE DOOR of Part One of ... Dr Jekyll and Mr Hyde, "", in the
public domain.`  The named-chapter half was fixed on 2026-10-20 (B14); the
generator still wrote "Part One" for a NUMBERED chapter of a book with no parts
(The Time Machine: 'I. Introduction', part 0), and `""` for a numeral with no name
after it.  A chapter whose recorded part is 0 is credited with no part at all, and
an empty name is left out, never quoted.  $0: no call."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "publish"))

import metadata  # noqa: E402

PRIOR = [{"description": "Chapter IV of H. G. Wells's The Time Machine (1895), \"Time Travelling\", "
                         "in the public domain."}]


def time_machine(tmp_path, *chapters):
    (tmp_path / "source").mkdir(parents=True)
    rows = [{"title": "Front matter", "part": 0}] + [{"title": t, "part": 0} for t in chapters]
    (tmp_path / "source" / "book.json").write_text(json.dumps({
        "title": "The Time Machine", "author": "H. G. Wells", "display_title": "The Time Machine",
        "parts": [], "chapters": rows}), encoding="utf-8")
    return tmp_path


def test_a_numbered_chapter_of_a_book_without_parts_names_no_part(tmp_path):
    line = metadata.attribution(time_machine(tmp_path, "I. Introduction"), 1, [])
    assert line == "Chapter I of H. G. Wells's The Time Machine, \"Introduction\", in the public domain."
    assert not metadata.credit_faults(line)


def test_the_year_the_priors_carry_still_follows_the_work(tmp_path):
    line = metadata.attribution(time_machine(tmp_path, "I. Introduction"), 1, PRIOR)
    assert line == "Chapter I of H. G. Wells's The Time Machine (1895), \"Introduction\", in the public domain."


def test_a_numeral_with_no_name_is_never_an_empty_quote(tmp_path):
    line = metadata.attribution(time_machine(tmp_path, "I. Introduction", "II."), 2, [])
    assert line == "Chapter II of H. G. Wells's The Time Machine, in the public domain."
    assert '""' not in line and not metadata.credit_faults(line)


def test_a_named_chapter_with_no_name_is_credited_by_its_number(tmp_path):
    line = metadata.attribution(time_machine(tmp_path, "   "), 1, [])
    assert line == "Chapter 1 of The Time Machine by H. G. Wells, in the public domain."
    assert not metadata.credit_faults(line)
