"""A rehearsal that permits YouTube must get through G-INORDER (growth review FOLLOWUPS 1):
the fake channel answers videos.list with the snippet the upload sent, and holds
playlists and playlist items, every write a would_* row in <sandbox>/youtube.jsonl.
Before this the fake answered only `status` and `upkeep` raised KeyError 'snippet'
inside step 13, after the video was public.  $0: nothing leaves the process."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.publish import youtube_playlist, youtube_privacy, youtube_upload
from studio.rehearsal import fakes
from tests.publish_fixtures import book_with

TITLE = 'A. B. Author: The Test Book — Ep 01/09 — "The Red Weed"'
BODY = {"snippet": {"title": TITLE, "description": "A measured episode.", "tags": ["t"], "categoryId": "1"},
        "status": {"privacyStatus": "private"}}


@pytest.fixture
def box(tmp_path):
    fakes.install({"youtube": "permit"}, tmp_path)
    yield tmp_path
    fakes.uninstall()


def youtube_rows(box: Path) -> list[dict]:
    return [json.loads(x) for x in (box / "youtube.jsonl").read_text(encoding="utf-8").splitlines()]


def public_episode(box: Path) -> tuple[Path, str]:
    """Episode 1 uploaded and flipped public through the fake, its ledger rows written."""
    vid = youtube_upload.send(Path("m.mp4"), BODY, None)["id"]
    api = youtube_privacy._build_api()
    youtube_privacy.set_privacy(api, vid, youtube_privacy.live_status(api, vid), "public")
    book = book_with(box / "library")
    rows = [{"key": f"{book.name}/ep01/abcd", "episode": 1, "video_id": vid, "title": TITLE},
            {"event": "privacy", "episode": 1, "video_id": vid, "privacy": "public"}]
    (book / "uploads.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return book, vid


def test_the_snippet_the_upload_sent_is_what_videos_list_answers(box):
    vid = youtube_upload.send(Path("m.mp4"), BODY, None)["id"]
    got = youtube_privacy._build_api().videos().list(part="snippet", id=vid).execute()["items"][0]
    assert got["snippet"]["title"] == TITLE and got["snippet"]["categoryId"] == "1"
    assert "status" not in got


def test_upkeep_runs_in_a_permitted_rehearsal_and_every_write_is_a_would_row(box):
    book, vid = public_episode(box)
    pid = youtube_playlist.upkeep(youtube_privacy._build_api(), book, 1, vid)
    assert pid and pid.startswith("rehearsal")
    events = [r["event"] for r in youtube_rows(box)]
    assert events[-3:] == ["would_make_playlist", "would_add_item", "would_set_snippet"]
    said = youtube_privacy._build_api().videos().list(part="snippet", id=vid).execute()["items"][0]["snippet"]
    assert said["description"].endswith(f"All episodes in order: https://www.youtube.com/playlist?list={pid}")


def test_a_second_upkeep_finds_the_playlist_and_writes_nothing(box):
    book, vid = public_episode(box)
    pid = youtube_playlist.upkeep(youtube_privacy._build_api(), book, 1, vid)
    kept = [r for r in book.joinpath("uploads.jsonl").read_text(encoding="utf-8").splitlines()
            if json.loads(r).get("event") not in {"playlist_item", "watch_block", "in_order"}]
    book.joinpath("uploads.jsonl").write_text("\n".join(kept) + "\n", encoding="utf-8")
    before = len(youtube_rows(box))
    assert youtube_playlist.upkeep(youtube_privacy._build_api(), book, 1, vid) == pid
    assert [r["event"] for r in youtube_rows(box)[before:]] == []
