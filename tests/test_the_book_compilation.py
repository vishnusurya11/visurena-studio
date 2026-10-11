"""The whole book as one regular video (owner, 2026-10-10): every published
episode in chapter order, ONE file, uploaded as a normal video whose description
OPENS with YouTube chapter timestamps -- one chapter per episode, the first at
0:00 -- so the player shows each chapter.  The parts are the exact masters the
channel already carries (matched by the sha8 the ledger recorded), never a
later re-cut."""
from __future__ import annotations

import json
from pathlib import Path

from studio import book_compilation as bc
from studio import youtube_publish as yp


def test_a_timestamp_is_minutes_under_an_hour_and_hours_after():
    assert bc.stamp(0) == "0:00"
    assert bc.stamp(125.9) == "2:05"
    assert bc.stamp(3725) == "1:02:05"


def test_chapters_start_at_zero_and_add_each_parts_length():
    parts = [(1, "The Eve of the War", 150.4), (2, "The Falling Star", 171.0), (3, "On Horsell Common", 162.2)]
    assert bc.chapter_lines(parts) == ["0:00 Ep 1 — The Eve of the War",
                                       "2:30 Ep 2 — The Falling Star",
                                       "5:21 Ep 3 — On Horsell Common"]


def test_the_description_opens_with_the_chapters():
    lines = ["0:00 Ep 1 — A", "2:30 Ep 2 — B", "5:21 Ep 3 — C"]
    text = bc.description(lines, intro="The whole book.", footer="AI DISCLOSURE: generated.")
    assert text.startswith("0:00 Ep 1 — A\n2:30 Ep 2 — B\n5:21 Ep 3 — C\n")
    assert text.index("The whole book.") > text.index("5:21 Ep 3 — C")
    assert len(text) <= yp.DESCRIPTION_MAX


def test_the_chapter_title_is_read_off_the_episode_title():
    assert bc.chapter_of('H. G. Wells: The War of the Worlds — Ep 26/27 — "Wreckage"') == "Wreckage"
    assert bc.chapter_of("no quotes here") == "no quotes here"


def test_the_part_is_the_master_the_channel_carries(tmp_path):
    cut = tmp_path / "cut"
    cut.mkdir()
    for name, body in (("master_iter1.mp4", b"first"), ("master_iter2.mp4", b"shipped"), ("master_r2v.mp4", b"later")):
        (cut / name).write_bytes(body)
    shipped = yp.sha8(cut / "master_iter2.mp4")
    assert bc.uploaded_master(cut, shipped) == cut / "master_iter2.mp4"
    assert bc.uploaded_master(cut, "00000000") is None


def test_the_concat_list_names_every_part_in_order(tmp_path):
    a, b = tmp_path / "ep01" / "master_iter6.mp4", tmp_path / "it's" / "master_r2v.mp4"
    text = bc.concat_list([a, b])
    lines = text.strip().splitlines()
    assert lines[0] == f"file '{a.resolve().as_posix()}'"
    assert lines[1].endswith("it'\\''s/master_r2v.mp4'")          # a quote in a path is escaped


def test_the_title_calls_it_an_adaptation_never_the_complete_book():
    """Owner 2026-10-11: it is our adapted screenplay, not the complete book."""
    title = bc.title("H. G. Wells: The War of the Worlds", 27)
    assert title == "H. G. Wells: The War of the Worlds — Full Adaptation, All 27 Episodes"
    assert "Complete" not in title and len(title) <= yp.TITLE_MAX


def test_a_retitle_changes_only_the_title_and_description_of_the_live_video():
    from scripts.publish import book_compilation as script
    live = {"title": "old", "description": "old", "categoryId": "1", "tags": ["a"], "defaultLanguage": "en"}
    sent = {}

    class Api:
        def videos(self):
            return self

        def list(self, part, id):
            return SimpleCall({"items": [{"snippet": dict(live)}]})

        def update(self, part, body):
            sent.update(body)
            return SimpleCall(body)

    script.retitle(Api(), "vid", {"title": "New", "description": "Fresh"})
    assert sent["id"] == "vid"
    assert sent["snippet"] == dict(live, title="New", description="Fresh")


class SimpleCall:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


def test_the_published_episodes_are_read_off_the_ledger_in_order(tmp_path):
    # the ledger's real shape: the upload row carries the sha8, the public flip only the video id
    rows = [{"episode": 1, "video_id": "a", "sha8": "11111111", "privacy": "private"},
            {"episode": 2, "video_id": "x", "sha8": "99999999", "privacy": "private"},   # an upload never made public
            {"episode": 2, "video_id": "b", "sha8": "22222222", "privacy": "private"},
            {"episode": 2, "video_id": "b", "event": "privacy", "privacy": "public"},
            {"episode": 1, "video_id": "a", "privacy": "public", "why": "owner"},
            {"episode": 3, "video_id": "c", "sha8": "33333333", "privacy": "private"},
            # the compilation's own row is public with a sha8, and is no episode
            {"episode": "compilation", "video_id": "z", "sha8": "77777777", "privacy": "public"}]
    (tmp_path / "uploads.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert bc.published(tmp_path) == [(1, "11111111"), (2, "22222222")]


def test_the_footer_names_the_books_own_author_and_says_adapted():
    """No book is named in code: Scarlet's video got Wells's footer (2026-10-11)."""
    text = bc.footer(author="Arthur Conan Doyle", book="A Study in Scarlet")
    assert text.startswith("Source: Arthur Conan Doyle, A Study in Scarlet, in the public domain.")
    assert "adapted, abridged screenplay" in text and "AI DISCLOSURE" in text
    assert "Wells" not in text


def test_the_intro_counts_the_episodes_and_names_no_other_book():
    text = bc.intro(book="A Study in Scarlet", episodes=14)
    assert text.startswith("A Study in Scarlet, told from beginning to end as one film")
    assert "in 14 episodes" in text and "Martian" not in text


def test_the_book_video_opens_on_its_main_title_then_runs_title_first():
    from scripts.publish import book_compilation as script
    parts = [(1, "A", [Path("t1"), Path("m1")], 150.0), (2, "B", [Path("t2"), Path("m2")], 160.0)]
    assert script.running_order(Path("main_title.mp4"), parts) == [
        Path("main_title.mp4"), Path("t1"), Path("m1"), Path("t2"), Path("m2")]


def test_a_thumbnail_is_set_and_a_refusal_is_returned_not_raised(tmp_path):
    from scripts.publish import book_compilation as script
    jpg = tmp_path / "t.jpg"
    jpg.write_bytes(b"\xff\xd8\xff")
    calls = []

    class Api:
        def thumbnails(self):
            return self

        def set(self, videoId, media_body):
            calls.append(videoId)
            return SimpleCall({"items": [{"default": {}}]})

    assert script.set_thumbnail(Api(), "vid", jpg) == "set"
    assert calls == ["vid"]

    class Refusing(Api):
        def set(self, videoId, media_body):
            raise RuntimeError("HttpError 403: the channel is not verified")

    assert script.set_thumbnail(Refusing(), "vid", jpg).startswith("refused")
