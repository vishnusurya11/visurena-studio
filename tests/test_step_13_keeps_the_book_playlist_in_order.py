"""Step 13's playlist upkeep (growth apply 2026-10-21, "what was skipped"): after a
new episode goes public it joins its book's playlist in episode order, gets the
"— Watch in order —" block on its own description, and the episode before it gets
a Next line -- each once, never twice.  The playlist id is read from where the apply
recorded it (the book video's youtube.json, else the previous episode's own live
block); a playlist is made only when the book has none anywhere.  Every call goes to
a fake; nothing reaches YouTube."""
from __future__ import annotations

import json

from scripts.publish import youtube_playlist as ypl
from studio import book_playlist as bp
from tests.publish_fixtures import book_with
from tests.youtube_fakes import FakeYouTube, video

E1, E2 = "bHj8WAY4rWE", "newEp02vid"
PID = "PLG7jS28mfkpo"
EP1_TEXT = ("Utterson walks.\n\nAI DISCLOSURE: generated.\n\n— Watch in order —\n"
            f"All episodes in order: https://www.youtube.com/playlist?list={PID}")


def jekyll(tmp_path, *published):
    book = book_with(tmp_path, author="Robert Louis Stevenson", series="Robert Louis Stevenson",
                     display_title="Dr Jekyll and Mr Hyde", episodes=10)
    rows = []
    for n, vid in published:
        rows += [{"key": f"{book.name}/ep{n:02d}/abcd", "episode": n, "video_id": vid, "privacy": "private"},
                 {"event": "privacy", "episode": n, "video_id": vid, "privacy": "public"}]
    (book / "uploads.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return book


def title(n: int, chapter: str) -> str:
    return f'Robert Louis Stevenson: Dr Jekyll and Mr Hyde — Ep {n:02d}/10 — "{chapter}"'


def channel(ep1_text=EP1_TEXT, playlists=None):
    return FakeYouTube(videos={E1: video(title(1, "Story of the Door"), ep1_text),
                               E2: video(title(2, "Search for Mr. Hyde"), "Utterson seeks Hyde.\n\nAI DISCLOSURE: generated.")},
                       playlists=playlists if playlists is not None else {PID: {"title": "x", "description": "", "items": [E1]}})


def ledger(book):
    return [json.loads(l) for l in (book / "uploads.jsonl").read_text(encoding="utf-8").splitlines()]


# ---- the text, pure --------------------------------------------------------------

def test_the_next_line_goes_inside_the_block_before_the_playlist_line():
    line = bp.episode_line("Next", 2, "Search for Mr. Hyde", E2)
    got = bp.with_next(EP1_TEXT, line)
    assert got.endswith(f'— Watch in order —\nNext: Ep 02 — "Search for Mr. Hyde" https://youtu.be/{E2}\n'
                        f"All episodes in order: https://www.youtube.com/playlist?list={PID}")
    assert bp.with_next(got, line) == got


def test_a_description_with_no_block_gets_one_holding_the_next_line():
    got = bp.with_next("Old text.", "Next: Ep 02 — \"B\" https://youtu.be/x")
    assert got == "Old text.\n\n— Watch in order —\nNext: Ep 02 — \"B\" https://youtu.be/x"


def test_the_own_block_holds_previous_playlist_and_whole_book_and_is_added_once():
    block = bp.own_block(previous='Previous: Ep 01 — "A" https://youtu.be/p', playlist_id=PID, whole="C1")
    assert block == ("\n\n— Watch in order —\nPrevious: Ep 01 — \"A\" https://youtu.be/p\n"
                     f"All episodes in order: https://www.youtube.com/playlist?list={PID}\n"
                     "The whole book in one video: https://youtu.be/C1")
    once = bp.with_own_block("Text.", block)
    assert once == "Text." + block and bp.with_own_block(once, block) == once


def test_the_position_is_the_episode_order():
    order = {"a": 1, "b": 2, "d": 4}
    assert bp.position(["a", "b", "d"], order, 3) == 2
    assert bp.position([], order, 1) == 0
    assert bp.position(["a", "b"], order, 3) == 2


def test_the_published_episodes_are_the_ones_whose_newest_flip_is_public(tmp_path):
    book = jekyll(tmp_path, (1, E1), (2, E2))
    with (book / "uploads.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"event": "privacy", "episode": 2, "video_id": E2, "privacy": "private"}) + "\n")
    assert bp.public_episodes(book) == {1: E1}


# ---- the acts, against the fake --------------------------------------------------

def test_episode_two_joins_the_playlist_the_apply_left_on_episode_one(tmp_path):
    book, yt = jekyll(tmp_path, (1, E1), (2, E2)), channel()
    ypl.upkeep(yt, book, 2, E2)
    assert yt.lists[PID]["items"] == [E1, E2]
    assert not [w for w in yt.writes if w[0] == "playlists.insert"]
    own = yt.store[E2]["snippet"]["description"]
    assert own.endswith(f'Previous: Ep 01 — "Story of the Door" https://youtu.be/{E1}\n'
                        f"All episodes in order: https://www.youtube.com/playlist?list={PID}")
    assert f'Next: Ep 02 — "Search for Mr. Hyde" https://youtu.be/{E2}' in yt.store[E1]["snippet"]["description"]
    assert yt.store[E2]["snippet"]["categoryId"] == "1" and "channelTitle" not in yt.store[E2]["snippet"]
    assert any(r.get("event") == "playlist" and r["playlist_id"] == PID for r in ledger(book))


def test_a_second_upkeep_writes_nothing(tmp_path):
    book, yt = jekyll(tmp_path, (1, E1), (2, E2)), channel()
    ypl.upkeep(yt, book, 2, E2)
    before = len(yt.writes)
    ypl.upkeep(yt, book, 2, E2)
    assert len(yt.writes) == before
    assert yt.store[E1]["snippet"]["description"].count("Next:") == 1


def test_a_book_with_no_playlist_anywhere_gets_one_made_once(tmp_path):
    book, yt = jekyll(tmp_path, (1, E1)), channel(ep1_text="Utterson walks.", playlists={})
    ypl.upkeep(yt, book, 1, E1)
    made = [w for w in yt.writes if w[0] == "playlists.insert"]
    assert len(made) == 1
    assert made[0][1]["snippet"]["title"] == "Dr Jekyll and Mr Hyde — Robert Louis Stevenson | Episodes in Order"
    assert made[0][1]["status"]["privacyStatus"] == "public"
    pid = next(iter(yt.lists))
    assert yt.lists[pid]["items"] == [E1]
    assert yt.store[E1]["snippet"]["description"].endswith(
        f"— Watch in order —\nAll episodes in order: https://www.youtube.com/playlist?list={pid}")
    assert bp.recorded_id(book) == pid


def test_the_channel_playlist_is_found_by_the_books_name_before_one_is_made(tmp_path):
    held = {"PLheld": {"title": "Dr Jekyll and Mr Hyde — Robert Louis Stevenson | Episodes in Order",
                       "description": "", "items": [E1]}}
    book, yt = jekyll(tmp_path, (1, E1), (2, E2)), channel(ep1_text="Utterson walks.", playlists=held)
    ypl.upkeep(yt, book, 2, E2)
    assert not [w for w in yt.writes if w[0] == "playlists.insert"]
    assert yt.lists["PLheld"]["items"] == [E1, E2]


def test_a_description_past_the_wall_stops_before_it_is_sent(tmp_path):
    book, yt = jekyll(tmp_path, (1, E1), (2, E2)), channel()
    yt.store[E2]["snippet"]["description"] = "x" * 4990
    try:
        ypl.upkeep(yt, book, 2, E2)
    except SystemExit as why:
        assert "5000" in str(why)
    else:
        raise AssertionError("a description over 5000 characters was sent")
    assert not [w for w in yt.writes if w[0] == "videos.update snippet" and w[1]["id"] == E2]


# ---- a re-run adds nothing twice (review 2026-10-21) -------------------------------

UPKEEP = {"playlist", "playlist_item", "watch_block", "next_line", "in_order"}


def test_a_run_cut_short_before_the_next_line_resumes_without_a_second_write(tmp_path, monkeypatch):
    book, yt = jekyll(tmp_path, (1, E1), (2, E2)), channel()
    real = ypl.next_link
    monkeypatch.setattr(ypl, "next_link", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("cut")))
    try:
        ypl.upkeep(yt, book, 2, E2)
    except RuntimeError:
        pass
    monkeypatch.setattr(ypl, "next_link", real)
    ypl.upkeep(yt, book, 2, E2)
    assert yt.lists[PID]["items"] == [E1, E2]
    assert [w[0] for w in yt.writes].count("playlistItems.insert") == 1
    assert [w[1]["id"] for w in yt.writes if w[0] == "videos.update snippet"] == [E2, E1]
    assert yt.store[E2]["snippet"]["description"].count(bp.MARK) == 1


def test_a_ledger_that_lost_its_upkeep_rows_still_writes_nothing_twice(tmp_path):
    """The second guard: every act reads the live channel before it writes."""
    book, yt = jekyll(tmp_path, (1, E1), (2, E2)), channel()
    ypl.upkeep(yt, book, 2, E2)
    before = len(yt.writes)
    kept = [r for r in ledger(book) if r.get("event") not in UPKEEP]
    (book / "uploads.jsonl").write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")
    ypl.upkeep(yt, book, 2, E2)
    assert len(yt.writes) == before
    assert yt.lists[PID]["items"] == [E1, E2]
    assert yt.store[E1]["snippet"]["description"].count("Next:") == 1
