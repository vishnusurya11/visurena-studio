"""The two book videos were retitled live on 2026-10-21 (growth apply): the book's
own name leads (the search term), the author follows, "Full Story Adaptation, N
Chapters", and the description opens with the chapters, then says "dramatised" and
links the book's playlist, the footer and disclosure word for word.  title() and
intro() still built the old shape, so a later `book_compilation.py --retitle=` would
have put the old titles back.  The fixture is the library's own record of what is
live (compilation/youtube.json, rewritten by the apply).  $0: no call."""
from __future__ import annotations

import json
from pathlib import Path

from studio import book_compilation as bc
from studio import youtube_publish as yp

LIVE = json.loads((Path(__file__).parent / "fixtures" / "book_video_live_2026_10_21.json")
                  .read_text(encoding="utf-8"))["books"]


def test_the_title_is_the_live_one_for_both_books():
    for b in LIVE:
        assert bc.title(b["series"], len(b["chapters"]), author=b["author"]) == b["title"]


def test_the_lead_drops_the_author_the_series_already_names():
    assert bc.search_lead("H. G. Wells: The War of the Worlds", "H. G. Wells") == "The War of the Worlds"
    assert bc.search_lead("Sherlock Holmes: A Study in Scarlet", "Arthur Conan Doyle") == \
        "Sherlock Holmes: A Study in Scarlet"


def test_a_long_title_spends_all_first_and_never_passes_the_wall():
    title = bc.title("Robert Louis Stevenson: Dr Jekyll and Mr Hyde", 10, author="Robert Louis Stevenson")
    assert title == "Dr Jekyll and Mr Hyde by Robert Louis Stevenson — Full Story Adaptation, All 10 Chapters"
    long = bc.title("A Very Long Series Name: " + "Word " * 15, 30, author="Somebody Else")
    assert len(long) <= yp.TITLE_MAX and "Full Adaptation, All" not in long


def test_the_description_is_the_live_one_for_both_books():
    for b in LIVE:
        intro = bc.intro(book=b["book"], author=b["author"], episodes=len(b["chapters"]),
                         playlist_url=f"https://www.youtube.com/playlist?list={b['playlist_id']}")
        text = bc.description(b["chapters"], intro=intro, footer=bc.footer(author=b["author"], book=b["book"]))
        assert text == b["description"]


def test_no_playlist_yet_leaves_the_line_out_never_a_placeholder():
    text = bc.intro(book="Dr Jekyll and Mr Hyde", author="Robert Louis Stevenson", episodes=10)
    assert "in 10 chapters, each one also a Short" in text
    assert "playlist" not in text and "{" not in text


def test_the_script_reads_the_playlist_the_apply_recorded(tmp_path):
    from studio import book_playlist as bp
    b = LIVE[0]
    (tmp_path / "compilation").mkdir()
    (tmp_path / "compilation" / "youtube.json").write_text(
        json.dumps({"description": b["description"]}), encoding="utf-8")
    assert bp.recorded_id(tmp_path) == b["playlist_id"]


def test_a_retitle_rebuild_says_exactly_what_is_live(tmp_path, monkeypatch):
    """`book_compilation.py --retitle=` rebuilds title + description from metadata();
    on the apply's own records it must reproduce the live text, never the old one."""
    from scripts.publish import book_compilation as script
    from studio import episode_home
    for k, b in enumerate(LIVE):
        book = tmp_path / f"book{k}"
        (book / "source").mkdir(parents=True)
        (book / "source" / "book.json").write_text(json.dumps({"title": b["book"], "author": b["author"]}),
                                                   encoding="utf-8")
        episode_home.write_json(episode_home.home(book, 1) / "youtube.json",
                                {"title": f'{b["series"]} — Ep 01/{len(b["chapters"]):02d} — "One"', "tags": []})
        episode_home.write_json(book / "compilation" / "youtube.json", {"description": b["description"]})
        monkeypatch.setattr(bc, "chapter_lines", lambda parts, lead_s=0.0, b=b: b["chapters"])
        meta = script.metadata(book, [(n, "t", None, 1.0) for n in range(1, len(b["chapters"]) + 1)])
        assert (meta["title"], meta["description"]) == (b["title"], b["description"])
