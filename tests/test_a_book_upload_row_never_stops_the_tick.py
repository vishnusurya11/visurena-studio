"""A book-level upload row is not an episode (2026-10-11): book_compilation
appends uploads.jsonl rows with episode='compilation', and the autopilot
int()ed every public row, so from 2026-10-10 23:24Z every tick raised
ValueError (1,927 tick_error events) and status.json froze.  The series
reads only the rows whose episode is a chapter number."""
from __future__ import annotations

import json

from studio import autopilot as ap
from tests import autopilot_cli_fixtures as fx

# the shipped WotW row, uploads.jsonl line 67 (2026-10-11)
BOOK_ROW = {"key": "20260827135508_the-war-of-the-worlds/compilation/23887a2d", "episode": "compilation",
            "video_id": "HSn8Gl7mnyA", "privacy": "public", "sha8": "23887a2d"}
PUBLIC = [{"episode": n, "privacy": "public", "video_id": f"v{n}"} for n in (1, 2)]


def test_episode_rows_keep_only_chapter_numbers():
    assert ap.episode_rows(PUBLIC + [BOOK_ROW, {"privacy": "public"}]) == PUBLIC


def test_next_unit_and_published_skip_a_book_row():
    assert ap.next_unit([1, 2, 3], PUBLIC + [BOOK_ROW], [], 3) == 3
    assert ap.published([BOOK_ROW] + PUBLIC, 2) and not ap.published([BOOK_ROW], 3)


def _uploads(book, rows):
    (book / "uploads.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_a_tick_with_a_book_row_writes_its_status(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    _uploads(book, PUBLIC + [BOOK_ROW])
    doc = cli.tick(book, fx.CODEX, fx.deps(tmp_path, "RUNNING"), 1)
    assert doc["series"]["published"] == [1, 2] and doc["series"]["next"] == 3


def test_a_complete_series_with_a_book_row_counts_its_episodes(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    _uploads(book, PUBLIC + [BOOK_ROW, {"episode": 3, "privacy": "public", "video_id": "v3"}])
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert doc["series"]["state"] == "complete" and "3/3" in d.calls["notify"][0]
