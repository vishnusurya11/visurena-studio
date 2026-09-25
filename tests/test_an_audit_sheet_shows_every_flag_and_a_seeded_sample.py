"""The audit sheet: every flagged artefact of the unit with the judge's numbers
beside the wall, the contact sheet, the strips, the master, and three passed
artefacts per gate drawn by a seed the unit fixes, so the page is the same page
tomorrow.  Built from the rows alone; no step is imported."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from scripts.audit import sheet
from studio import audit_rows

FIXTURE = Path(__file__).parent / "fixtures" / "audit" / "rows.jsonl"


def _png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), (20, 20, 20)).save(path)
    return path


def book_with_rows(tmp_path) -> Path:
    book = tmp_path / "book"
    (book / "audit").mkdir(parents=True)
    shutil.copy(FIXTURE, audit_rows.path(book))
    home = book / "episodes" / "ep01"
    for i in range(1, 9):
        _png(home / "storyboard" / f"shot_{i:02d}.png")
    for i in range(1, 7):
        (home / "takes" / "r2v").mkdir(parents=True, exist_ok=True)
        (home / "takes" / "r2v" / f"T{i:02d}.mp4").write_bytes(b"take")
    (home / "cut").mkdir()
    (home / "cut" / "master_r2v.mp4").write_bytes(b"cut")
    _png(home / "storyboard" / "contact.png")
    _png(home / "review" / "contact_cccc3333.png")
    _png(home / "reports" / "strip_T01_T06.png")
    return book


def test_every_flag_is_on_the_page_with_its_numbers_beside_the_wall(tmp_path):
    book = book_with_rows(tmp_path)
    out = sheet.write(book, "ep01")
    assert out == book / "audit" / "ep01.html"
    page = out.read_text(encoding="utf-8")
    for word in ("clones", "shot_02", "cosine: 0.81", "<b>wall: 0.75</b>", "pass_through", "T03",
                 "steps: 23", "shadow", "p5: 16.5", "near_black: 0.02", "judge:master_eye@1", "terminal flag"):
        assert word in page, word
    assert "../episodes/ep01/review/contact_cccc3333.png" in page
    assert "../episodes/ep01/storyboard/contact.png" in page
    assert "../episodes/ep01/reports/strip_T01_T06.png" in page
    assert "../episodes/ep01/cut/master_r2v.mp4" in page
    assert "lettering" not in page and "ep02" not in page.split("<main>")[1]


def test_three_passed_artefacts_per_gate_never_a_flagged_one_and_the_same_three_again(tmp_path):
    book = book_with_rows(tmp_path)
    rows = sheet.rows_for(audit_rows.load(book), "ep01")
    seed = sheet.unit_seed("ep01", rows)
    assert seed == "cccc3333"
    picked = sheet.sample(book, "ep01", rows, seed)
    assert len(picked["EYE_PANELS"]) == 3 and len(picked["EYE_TAKES"]) == 3 and len(picked["MASTER"]) == 1
    assert "episodes/ep01/storyboard/shot_02.png" not in picked["EYE_PANELS"]
    assert "episodes/ep01/takes/r2v/T03.mp4" not in picked["EYE_TAKES"]
    assert picked == sheet.sample(book, "ep01", rows, seed)
    assert sheet.write(book, "ep01").read_text(encoding="utf-8") == sheet.page(book, "ep01", rows)


def test_the_index_lists_every_unit_and_the_runner_may_pass_a_number(tmp_path):
    book = book_with_rows(tmp_path)
    sheet.write(book, "ep01")
    index = (book / "audit" / "index.html").read_text(encoding="utf-8")
    assert "ep01.html" in index and "ep02.html" in index
    assert sheet.unit_of("4") == "ep04" and sheet.unit_of("ep04") == "ep04"
    assert sheet.unit_seed("ep02", sheet.rows_for(audit_rows.load(book), "ep02")) != "cccc3333"
