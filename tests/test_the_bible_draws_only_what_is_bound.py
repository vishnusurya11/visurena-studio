"""The reference bible draws the characters and props the line has BOUND, never
every entity the analysis knows and never a location.  The first unattended
run asked for 66 pictures for a chapter that needed one."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.refs import step_02_sheets as sheets
from studio import db
from studio.stage_run import StageContext

CODEX = "20260901000001"


def _profile(book: Path, kind: str, who: str) -> None:
    folder = book / "analysis" / kind
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{who}.json").write_text(json.dumps(
        {"id": who, "name": who, "profile": {"design": {"sheet_prompt": f"A {who}. Sheet."},
                                            "visual": f"a {who} place"}}), encoding="utf-8")


def _book(tmp_path: Path, bound: list[str] | None) -> Path:
    book = tmp_path / f"{CODEX}_a-book"
    for who in ("lead", "guest", "extra"):
        _profile(book, "characters", who)
    _profile(book, "props", "lantern")
    _profile(book, "locations", "lane")
    if bound is not None:
        (book / "refs").mkdir(parents=True, exist_ok=True)
        (book / "refs" / "refs.json").write_text(json.dumps(
            {"refs": [{"entity_id": w, "kind": "character"} for w in bound]}), encoding="utf-8")
    return book


def _ctx(tmp_path: Path, book: Path, launched: list, extra=None) -> StageContext:
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    ctx = StageContext(conn, CODEX, book, "refs", unit="main", logs_root=tmp_path / "logs",
                       busy=lambda: False, hold=tmp_path / "HOLD", launch=lambda cmd: launched.append(cmd) or 0)
    ctx.extra = extra or []
    return ctx


def test_only_the_bound_characters_are_drawn(tmp_path):
    launched = []
    ctx = _ctx(tmp_path, _book(tmp_path, ["lead"]), launched)
    assert [j.entity for j in sheets.jobs(ctx)] == ["lead"]
    sheets.run(ctx)
    flags = launched[0][3:]
    assert "--only=lead" in flags and "--kind=characters" in flags and "--kind=props" in flags
    assert "--kind=locations" not in flags and "--only=guest" not in flags


def test_nothing_bound_and_missing_means_no_gpu_call(tmp_path):
    launched = []
    book = _book(tmp_path, ["lead"])
    picture = book / "refs" / "characters" / "lead" / "sheet.png"
    picture.parent.mkdir(parents=True)
    picture.write_bytes(b"png")
    ctx = _ctx(tmp_path, book, launched)
    assert sheets.done(ctx) is True
    sheets.run(ctx)
    assert launched == []


def test_explicit_flags_still_decide(tmp_path):
    launched = []
    ctx = _ctx(tmp_path, _book(tmp_path, ["lead"]), launched, ["--kind=characters", "--only=guest"])
    assert [j.entity for j in sheets.jobs(ctx)] == ["guest"]
    sheets.run(ctx)
    assert launched[0][3:] == ["--kind=characters", "--only=guest"]


def test_a_book_without_a_bible_keeps_the_old_scope(tmp_path):
    launched = []
    ctx = _ctx(tmp_path, _book(tmp_path, None), launched)
    assert {j.entity for j in sheets.jobs(ctx)} >= {"lead", "guest", "extra"}
