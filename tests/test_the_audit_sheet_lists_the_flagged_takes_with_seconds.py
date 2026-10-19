"""The audit sheet carries a Flagged takes table (contract K7): each take that shipped flagged,
its seconds in the master, its severity and rows, and a link to the strip that shows it."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.audit import sheet

ROWS = [{"take": 8, "shot": [8], "seconds_in_master": 4.0, "slowed": False, "rows": ["clones"],
         "notes": ["clones: two faces read as one man (facenet 0.943)"], "severity": "high"},
        {"take": 21, "shot": [21], "seconds_in_master": 5.25, "slowed": True, "rows": ["warp", "pulse"],
         "notes": ["warp: the face is redrawn"], "severity": "normal"}]


def book_with(tmp_path, rows=ROWS) -> Path:
    home = tmp_path / "book" / "episodes" / "ep01"
    (home / "takes" / "work").mkdir(parents=True)
    (home / "takes" / "work" / "flagged_takes.json").write_text(json.dumps(rows), encoding="utf-8")
    (home / "reports").mkdir()
    (home / "reports" / "strip_T00_T14.png").write_bytes(b"x")
    (home / "reports" / "strip_T15_T27.png").write_bytes(b"x")
    return tmp_path / "book"


def test_the_table_lists_every_take_with_its_seconds(tmp_path):
    html = sheet.flagged_takes_table(book_with(tmp_path), "ep01")
    for word in ("Flagged takes", "T08", "4.0 s", "T21", "5.25 s", "slowed", "high", "clones", "warp, pulse"):
        assert word in html, word


def test_each_take_links_the_strip_that_covers_it(tmp_path):
    html = sheet.flagged_takes_table(book_with(tmp_path), "ep01")
    assert "../episodes/ep01/reports/strip_T00_T14.png" in html
    assert "../episodes/ep01/reports/strip_T15_T27.png" in html


def test_the_page_carries_the_table_and_the_total(tmp_path):
    page = sheet.page(book_with(tmp_path), "ep01", [])
    assert "Flagged takes" in page and "9.25 s" in page


def test_no_file_no_table(tmp_path):
    assert sheet.flagged_takes_table(tmp_path, "ep01") == ""
