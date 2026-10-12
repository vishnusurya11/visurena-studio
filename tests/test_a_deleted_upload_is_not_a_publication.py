"""Board review 2026-10-12 (02 S1): WotW uploads.jsonl line 29 is a `deleted`
row that carries a video id and a sha8.  `publish_row` kept every row with
both, so an episode deleted and not replaced would stay published and settle
done.  A video id any row calls deleted is no publication.  $0."""
from __future__ import annotations

import json

from studio import backfill, episode_home

CODEX = "20990101000000"


def _book(tmp_path, rows):
    book = tmp_path / f"{CODEX}_a-fake-book"
    episode_home.write_json(book / "episodes" / "ep14" / "youtube.json", {})
    (book / "uploads.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return book


def test_a_deleted_video_is_not_published(tmp_path):
    book = _book(tmp_path, [{"episode": 14, "video_id": "NJn", "sha8": "abf09823", "privacy": "public"},
                            {"episode": 14, "video_id": "NJn", "event": "deleted", "sha8": "abf09823"}])
    assert backfill.publish_row(book, CODEX, "ep14") is None


def test_the_replacement_after_a_deletion_is_the_publication(tmp_path):
    book = _book(tmp_path, [{"episode": 14, "video_id": "NJn", "sha8": "abf09823"},
                            {"episode": 14, "video_id": "7wo", "sha8": "994ee36f", "privacy": "public"},
                            {"episode": 14, "video_id": "NJn", "event": "deleted", "sha8": "abf09823"}])
    row = backfill.publish_row(book, CODEX, "ep14")
    assert row["unit"] == "994ee36f@youtube" and row["note"].startswith("video 7wo public")


def test_the_deleted_flag_spelling_also_counts(tmp_path):
    book = _book(tmp_path, [{"episode": 14, "video_id": "X", "sha8": "aaaaaaaa"},
                            {"episode": 14, "video_id": "X", "deleted": True}])
    assert backfill.deleted_ids(backfill.upload_rows(book, 14)) == {"X"}
    assert backfill.publish_row(book, CODEX, "ep14") is None
