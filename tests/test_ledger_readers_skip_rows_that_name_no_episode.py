"""The upload ledger holds rows that are no upload: a shorts_poll row (video_id, no
episode), step 13's playlist upkeep rows (neither), a compilation row (episode
"compilation") and a deleted video's `event: deleted` row.  Jekyll's real ledger of
2026-10-21 (copied to tests/fixtures/jekyll_uploads_2026_10_21.jsonl) gave
`KeyError 'episode'` in youtube_retitle.episodes() and harvest_labels.published_units()
(growth review FOLLOWUPS 5), and book_playlist.public_episodes still called a deleted
video public (FOLLOWUPS 4).  $0: files only, no call."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.calibration import harvest_labels
from scripts.publish import youtube_retitle
from studio import book_playlist as bp

JEKYLL = Path(__file__).parent / "fixtures" / "jekyll_uploads_2026_10_21.jsonl"


def jekyll(tmp_path: Path, *extra: dict) -> Path:
    book = tmp_path / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
    book.mkdir()
    shutil.copy(JEKYLL, book / "uploads.jsonl")
    with (book / "uploads.jsonl").open("a", encoding="utf-8") as fh:
        fh.writelines(json.dumps(r) + "\n" for r in extra)
    return book


def test_the_retitle_reads_the_one_upload_and_skips_the_poll_row(tmp_path):
    got = youtube_retitle.episodes(jekyll(tmp_path, {"event": "in_order", "video": "bHj8WAY4rWE"},
                                          {"episode": "compilation", "video_id": "C1", "title": "Book"}))
    assert [(r["episode"], r["video_id"]) for r in got] == [(1, "bHj8WAY4rWE")]
    assert got[0]["title"].startswith("Robert Louis Stevenson: Dr Jekyll and Mr Hyde") and "key" in got[0]


def test_the_harvest_counts_episode_one_published_and_nothing_else(tmp_path):
    book = jekyll(tmp_path, {"episode": "compilation", "video_id": "C1", "privacy": "public"})
    assert harvest_labels.published_units(book) == {"ep01"}


def test_a_deleted_video_is_no_public_episode(tmp_path):
    book = jekyll(tmp_path)
    assert bp.public_episodes(book) == {1: "bHj8WAY4rWE"}
    with (book / "uploads.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"event": "deleted", "episode": 1, "video_id": "bHj8WAY4rWE"}) + "\n")
    assert bp.public_episodes(book) == {}
