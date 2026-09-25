"""A sheet carries no words.  A recognised string from EasyOCR -- a cast id, a
prompt word, gibberish alike -- is a hard lettering fault; a box without a
recognised string is not, and a wordless sheet passes."""
from __future__ import annotations

import json
from pathlib import Path

from studio.judges import look
from tests import look_fixtures as lf

FIX = Path(__file__).parent / "fixtures" / "measures"
ROW = {"path": "refs/props/p/sheet.png", "prompt": "A brass lantern on a table.", "seed": 1}


def test_a_recognised_string_is_a_lettering_fault(tmp_path):
    book = lf.a_book(tmp_path)
    lf.draw(book, ROW["path"])
    found = json.load((FIX / "ocr_cast_id.json").open())
    verdict = look.judge(book, [ROW], **lf.tools(ocr=lambda picture: found))
    assert not verdict.passed
    fault = verdict.faults[0]
    assert fault.kind == "lettering" and fault.where == ROW["path"]
    assert "MARROW" in fault.evidence["strings"]


def test_a_box_without_a_string_is_not_lettering(tmp_path):
    book = lf.a_book(tmp_path)
    lf.draw(book, ROW["path"])
    found = json.load((FIX / "ocr_no_string.json").open())
    verdict = look.judge(book, [ROW], **lf.tools(ocr=lambda picture: found))
    assert verdict.passed and verdict.faults == []


def test_a_wordless_sheet_passes():
    verdict = look.judge(None, [ROW], **lf.tools())
    assert verdict.passed and verdict.faults == [] and verdict.confidence == 1.0
