"""Which places are flat and which subjects are banned live with the book.

Audit item 7, measured 2026-09-22: the panel and take content runners each
carried their own FLAT set and BANNED list, and they had drifted -- FLAT held
four places in one and two in the other, and the take checker still banned
"car", so a railway CARRIAGE failed. Flatness is a property of the place, so
it is a field on the location row; the banned list is the book's.
"""
import json

from studio.panel_content import banned_subjects, flat_place


def book(tmp_path, rows: dict, rules=None):
    loc = tmp_path / "analysis" / "locations"
    loc.mkdir(parents=True)
    for lid, fields in rows.items():
        (loc / f"{lid}.json").write_text(json.dumps({"id": lid, **fields}))
    if rules is not None:
        (tmp_path / "analysis" / "dq_rules.json").write_text(json.dumps(rules))
    return tmp_path


def test_a_place_whose_row_says_flat_is_flat(tmp_path):
    assert flat_place(book(tmp_path, {"common": {"landform": "flat"}}), "common")


def test_a_hill_is_not(tmp_path):
    assert not flat_place(book(tmp_path, {"hill": {"landform": "hill"}}), "hill")


def test_a_row_that_does_not_say_is_not_assumed_flat(tmp_path):
    assert not flat_place(book(tmp_path, {"room": {}}), "room")


def test_no_location_is_not_flat(tmp_path):
    assert not flat_place(book(tmp_path, {}), "")


def test_the_banned_subjects_are_the_books(tmp_path):
    b = book(tmp_path, {}, {"banned_subjects": ["doll", "motor car"]})
    assert banned_subjects(b) == ("doll", "motor car")


def test_a_book_with_no_rules_bans_nothing(tmp_path):
    assert banned_subjects(book(tmp_path, {})) == ()
