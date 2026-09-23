"""A one-sheet book is bound by its sheets, not by another book's busts and cards.

MEASURED 2026-09-22 (audit item 3). CAST BOUND asks every character for a
`sheet` block, a bound wardrobe CARD per state and a bust read-back -- the
paid bust-and-card casting of the Scarlet book. WotW draws one sheet per
character, so it failed every WotW plan (7, 18, 6 and 24 hard faults on
ep06-09), plan_check exited 1 on every episode, and the exit code stopped
meaning anything.

A book that casts from sheets (refs/characters/<who>/sheet.png) is bound when
the character has a row and a sheet on disk. The bust-and-card rule still
applies to a book that casts that way.
"""
import json

from studio.cast_refs import bound, casts_from_sheets, sheet_unbound


def book(tmp_path, rows, sheets):
    (tmp_path / "refs" / "characters").mkdir(parents=True)
    (tmp_path / "refs" / "refs.json").write_text(json.dumps(
        {"refs": [{"entity_id": w, "kind": "character", "physical": "a man"} for w in rows]}))
    for who in sheets:
        (tmp_path / "refs" / "characters" / who).mkdir()
        (tmp_path / "refs" / "characters" / who / "sheet.png").write_bytes(b"png")
    return tmp_path


def test_a_book_with_sheets_casts_from_sheets(tmp_path):
    assert casts_from_sheets(book(tmp_path, ["a"], ["a"]))


def test_a_book_without_sheets_does_not(tmp_path):
    assert not casts_from_sheets(book(tmp_path, ["a"], []))


def test_a_row_and_a_sheet_is_bound(tmp_path):
    assert sheet_unbound(book(tmp_path, ["a"], ["a"]), "a") == []


def test_no_row_is_unbound(tmp_path):
    assert any("no row" in why for why in sheet_unbound(book(tmp_path, [], ["a"]), "a"))


def test_no_sheet_is_unbound(tmp_path):
    b = book(tmp_path, ["a", "b"], ["a"])
    assert any("sheet" in why for why in sheet_unbound(b, "b"))


def test_bound_uses_the_sheet_rule_in_a_sheet_book(tmp_path):
    b = book(tmp_path, ["a"], ["a"])
    assert bound(b, "a", "outdoor") == []
