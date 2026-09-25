"""The identity gate is handed the cast sheets the take itself staged.

ep12, 2026-09-25: take_verdict called identity_dq with no sheets, so every face
scored against an empty bank -- the gate is armed and has never compared one
face in the runner. The record already names them: `faces` lists who, `refs`
lists `refs/characters/<who>/sheet.png`, relative to the book.
"""
from pathlib import Path

from studio import take_verdict as tv


def test_each_face_gets_its_own_sheet_from_the_record(tmp_path):
    record = {"faces": ["artilleryman"],
              "refs": ["refs/characters/artilleryman/sheet.png", "episodes/ep12/storyboard/h3/shot_02.png"]}
    assert tv.sheets_of(record, tmp_path) == {"artilleryman": tmp_path / "refs/characters/artilleryman/sheet.png"}


def test_no_book_no_sheets():
    assert tv.sheets_of({"faces": ["a"], "refs": ["refs/characters/a/sheet.png"]}, None) == {}


def test_a_face_without_a_staged_sheet_is_left_out(tmp_path):
    record = {"faces": ["artilleryman", "narrator"], "refs": ["refs/characters/artilleryman/sheet.png"]}
    assert list(tv.sheets_of(record, tmp_path)) == ["artilleryman"]
