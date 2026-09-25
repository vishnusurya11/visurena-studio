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
