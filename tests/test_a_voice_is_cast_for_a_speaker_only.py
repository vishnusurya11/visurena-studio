"""A voice is for a SPEAKER.  The bible casts the bound characters a plan gives a
line to and no one else; the record step casts, just in time, any speaker of
its own plan who has no clip yet.  The first unattended run wanted 35 voices
for a chapter with two speakers, and the voice script refused the folder name
a runner hands it."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import step_04_record as record
from scripts.refs import step_03_voices as voices
from studio import cast_home, db, episode_home
from studio.stage_run import StageContext

CODEX = "20260901000001"


def _book(tmp_path: Path) -> Path:
    book = tmp_path / f"{CODEX}_a-book"
    (book / "refs").mkdir(parents=True)
    (book / "refs" / "refs.json").write_text(json.dumps({"refs": [
        {"entity_id": "lead", "kind": "character"}, {"entity_id": "guest", "kind": "character"},
        {"entity_id": "walker", "kind": "character"}]}), encoding="utf-8")
    for who in ("lead", "guest", "walker", "stranger"):
        card = cast_home.card(book, who)
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text("{}", encoding="utf-8")
    clip = cast_home.clip(book, "lead")
    clip.parent.mkdir(parents=True, exist_ok=True)
    clip.write_bytes(b"wav")
    home = episode_home.home(book, 3)
    home.mkdir(parents=True)
    (home / "plan.json").write_text(json.dumps({"lines": [
        {"index": 0, "kind": "narration", "speaker": "lead", "text": "x", "shot": 0},
        {"index": 1, "kind": "dialogue", "speaker": "guest", "text": "y", "shot": 1}]}), encoding="utf-8")
    return book


def _ctx(tmp_path: Path, book: Path, launched: list, stage="refs", number=None) -> StageContext:
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    ctx = StageContext(conn, CODEX, book, stage, unit="main" if stage == "refs" else "ep03", number=number,
                       logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "HOLD",
                       launch=lambda cmd: launched.append(cmd) or 0)
    ctx.extra = []
    ctx.home = episode_home.home(book, 3)
    return ctx


def test_the_bible_casts_only_the_bound_speakers_without_a_clip(tmp_path):
    book = _book(tmp_path)
    assert voices.uncast(book) == ["guest"]           # walker is bound but never speaks; stranger is not bound
    launched = []
    ctx = _ctx(tmp_path, book, launched)
    assert voices.done(ctx) is False
    voices.run(ctx)
    assert launched[0][3:] == ["--only=guest"]


def test_nobody_to_cast_means_no_gpu_call(tmp_path):
    book = _book(tmp_path)
    clip = cast_home.clip(book, "guest")
    clip.parent.mkdir(parents=True, exist_ok=True)
    clip.write_bytes(b"wav")
    launched = []
    ctx = _ctx(tmp_path, book, launched)
    assert voices.done(ctx) is True
    voices.run(ctx)
    assert launched == []


def test_the_record_step_casts_its_own_speakers_first(tmp_path):
    book = _book(tmp_path)
    launched = []
    ctx = _ctx(tmp_path, book, launched, stage="episode", number=3)
    assert record.voiceless(ctx) == ["guest"]
    record.run(ctx)
    assert launched[0][1] == "scripts/cast/cast_voices.py" and "--only=guest" in launched[0]
    assert launched[1][1] == "scripts/episode/say_lines.py"


def test_the_voice_script_accepts_the_folder_name(tmp_path, monkeypatch):
    from scripts.cast import cast_voices
    (tmp_path / "library" / f"{CODEX}_a-book").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert cast_voices.book_dir(f"{CODEX}_a-book").name == f"{CODEX}_a-book"
    assert cast_voices.book_dir(CODEX).name == f"{CODEX}_a-book"
