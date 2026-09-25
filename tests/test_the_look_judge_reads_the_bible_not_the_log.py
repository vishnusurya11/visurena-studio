"""The LOOK judge reads the bible's sheets -- characters and props on disk --
never every path pack.jsonl has ever logged.  On the first real run the pack
held 178 paths: 150 per-episode places (judged by the line at their own hour)
and 5 superseded views whose files were gone; the judge died on the first."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.refs import step_04_verdict as verdict
from studio import db
from studio.stage_run import StageContext

CODEX = "20260901000001"


def _book(tmp_path: Path) -> Path:
    book = tmp_path / f"{CODEX}_a-book"
    rows = ["refs/characters/lead/sheet.png", "refs/characters/lead/old_view.png",
            "refs/props/lamp/sheet.png", "refs/locations/lane/wide_day.png"]
    (book / "refs").mkdir(parents=True)
    bound = [{"entity_id": "lead", "kind": "character"}, {"entity_id": "lamp", "kind": "prop"}]
    (book / "refs" / "refs.json").write_text(json.dumps({"refs": bound}), encoding="utf-8")
    with (book / "refs" / "pack.jsonl").open("w", encoding="utf-8") as fh:
        for p in rows:
            fh.write(json.dumps({"path": p, "prompt": "x", "seed": 1}) + "\n")
    for p in rows:
        if "old_view" in p:
            continue                                  # the superseded view: logged, gone
        (book / p).parent.mkdir(parents=True, exist_ok=True)
        (book / p).write_bytes(b"png")
    return book


def test_only_bible_sheets_on_disk_are_judged(tmp_path):
    book = _book(tmp_path)
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    ctx = StageContext(conn, CODEX, book, "refs", unit="main", logs_root=tmp_path / "logs",
                       busy=lambda: False, hold=tmp_path / "HOLD", launch=lambda cmd: 0)
    assert verdict.paths_to_judge(ctx) == ["refs/characters/lead/sheet.png", "refs/props/lamp/sheet.png"]


def test_a_bound_row_whose_picture_is_gone_is_read_from_nothing(tmp_path):
    from studio.judges import look
    asked = []

    def reader(picture, question):
        asked.append(picture)
        return "{}"

    acc = look.Reads()
    look.read_bound(tmp_path, {"path": "refs/characters/gone/sheet.png"},
                    lambda name: reader if name == "reader" else (lambda p: None), acc)
    assert asked == [] and acc.cards == {} and acc.faces == {}


def _ctx(tmp_path, book):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    return StageContext(conn, CODEX, book, "refs", unit="main", logs_root=tmp_path / "logs",
                        busy=lambda: False, hold=tmp_path / "HOLD", launch=lambda cmd: 0)


def test_only_a_bound_entity_is_the_bibles_to_judge(tmp_path):
    """49 sheets on disk for 19 bound rows: the unbound thirty are nobody's."""
    book = _book(tmp_path)
    (book / "refs" / "refs.json").write_text(json.dumps({"refs": [{"entity_id": "lead"}]}), encoding="utf-8")
    assert verdict.paths_to_judge(_ctx(tmp_path, book)) == ["refs/characters/lead/sheet.png"]


def test_a_bible_that_shipped_episodes_before_any_verdict_is_grandfathered(tmp_path):
    """Its identity was judged by the twelve episodes that used it; a NEW book's
    first bible is read in full."""
    book = _book(tmp_path)
    ctx = _ctx(tmp_path, book)
    assert verdict.grandfathered(ctx) is False
    (book / "episodes" / "ep01" / "cut").mkdir(parents=True)
    (book / "episodes" / "ep01" / "cut" / "master_iter1.mp4").write_bytes(b"mp4")
    assert verdict.grandfathered(ctx) is True


def test_a_light_read_asks_no_reader_and_grades_nothing_hard_but_lettering_and_limbs(tmp_path):
    from studio.judges import look
    from tests import look_fixtures as lf
    asked = []
    lf.draw(tmp_path, "refs/characters/a/sheet.png")
    row = {"path": "refs/characters/a/sheet.png", "prompt": "A man with a lantern.", "seed": 1}
    found = [([[10, 10], [200, 10], [200, 60], [10, 60]], "XQZ", 0.95)]
    v = look.judge(tmp_path, [row], light=True, reader=lambda p, q: asked.append(p) or "{}",
                   ocr=lambda p: found, keypoints=lf.two_wrists)
    assert asked == [] and not v.passed and [f.kind for f in v.faults] == ["lettering"]


def test_every_fault_outside_hard_is_advisory():
    from studio.judges import look
    from studio.judges.verdict import Fault
    graded = look.graded([Fault(kind="identity", where="x"), Fault(kind="lettering", where="x")])
    assert [f.severity for f in graded] == ["advisory", "normal"]


def test_a_place_on_disk_is_context_for_the_style_row_never_a_judged_row(tmp_path):
    book = _book(tmp_path)
    bound = verdict.bound_ids(book)
    assert verdict.context_path(book, "refs/locations/lane/wide_day.png", bound) is True
    assert verdict.context_path(book, "refs/locations/lane/gone.png", bound) is False
    assert verdict.context_path(book, "refs/characters/lead/sheet.png", bound) is True
    assert "refs/locations/lane/wide_day.png" not in verdict.paths_to_judge(_ctx(tmp_path, book))
