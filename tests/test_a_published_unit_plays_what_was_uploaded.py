"""Board review 2026-10-12 (02 #5, 03 A2): Scarlet ep08 played cut/master_r2v.mp4
(sha8 d22b381b, written after the upload) while the channel has master_iter3
(f12decbd); ep01 played master_iter13 against the uploaded master_iter7.  A
published unit plays the file whose bytes hash to the upload's sha8, and the
page links the video itself ("Watch on YouTube"), not only youtube.json.  $0."""
from __future__ import annotations

import json

from studio import backfill, episode_home, tick
from studio.command_center import unit_view
from studio.youtube_publish import sha8

CODEX = "20990101000000"


def _book(tmp_path, masters: dict[str, bytes], uploaded: str, qc_master: str | None = None):
    book = tmp_path / f"{CODEX}_a-book"
    home = book / "episodes" / "ep08"
    for name, data in masters.items():
        (home / "cut").mkdir(parents=True, exist_ok=True)
        (home / "cut" / name).write_bytes(data)
    episode_home.write_json(home / "youtube.json", {"privacy": "public"})
    if qc_master:
        rel = f"episodes/ep08/cut/{qc_master}"
        episode_home.write_json(home / "qc_r2v.json", {"master": rel, "sha8": sha8(book / rel)})
    row = {"episode": 8, "video_id": "V5s", "sha8": sha8(home / "cut" / uploaded), "privacy": "public"}
    (book / "uploads.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    return book, home


def test_the_live_upload_names_the_video_and_its_privacy(tmp_path):
    book, _ = _book(tmp_path, {"master_iter3.mp4": b"three"}, "master_iter3.mp4")
    up = backfill.live_upload(book, "ep08")
    assert (up["video_id"], up["privacy"], up["sha8"]) == ("V5s", "public", sha8(book / "episodes/ep08/cut/master_iter3.mp4"))
    assert backfill.live_upload(book, "ep09") is None


def test_the_uploaded_master_is_played_not_the_qc_one(tmp_path):
    book, home = _book(tmp_path, {"master_iter3.mp4": b"three", "master_r2v.mp4": b"r2v"}, "master_iter3.mp4",
                       qc_master="master_r2v.mp4")
    got = unit_view.published_master(book, CODEX, "ep08", json.loads((home / "qc_r2v.json").read_text()))
    assert got["rel"] == "episodes/ep08/cut/master_iter3.mp4"
    assert got["youtube"] == "https://youtu.be/V5s" and got["privacy"] == "public"


def test_a_qc_master_with_the_uploads_sha8_needs_no_hashing(tmp_path, monkeypatch):
    book, home = _book(tmp_path, {"master_iter3.mp4": b"three"}, "master_iter3.mp4", qc_master="master_iter3.mp4")
    monkeypatch.setattr(unit_view, "file_sha8", lambda p: (_ for _ in ()).throw(AssertionError("hashed")))
    got = unit_view.published_master(book, CODEX, "ep08", json.loads((home / "qc_r2v.json").read_text()))
    assert got["rel"] == "episodes/ep08/cut/master_iter3.mp4"


def test_an_unpublished_unit_has_no_published_master(tmp_path):
    book = tmp_path / f"{CODEX}_a-book"
    (book / "episodes" / "ep08").mkdir(parents=True)
    assert unit_view.published_master(book, CODEX, "ep08", {}) is None


def test_a_master_is_hashed_once_per_size_and_mtime(tmp_path, monkeypatch):
    path = tmp_path / "m.mp4"
    path.write_bytes(b"bytes")
    calls = []
    monkeypatch.setattr(unit_view, "sha8", lambda p: calls.append(p) or "abcd1234")
    unit_view._SHA8.clear()
    assert unit_view.file_sha8(path) == unit_view.file_sha8(path) == "abcd1234" and len(calls) == 1


def test_the_tick_finds_the_uploaded_file_with_any_hasher(tmp_path):
    book, _ = _book(tmp_path, {"master_iter3.mp4": b"three"}, "master_iter3.mp4")
    assert tick.uploaded_file(book, "ep08", "feedface", hasher=lambda p: "feedface") == "episodes/ep08/cut/master_iter3.mp4"
