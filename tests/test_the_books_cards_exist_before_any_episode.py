"""Owner design 2026-09-30: a book's title cards are ALL baked before its
first episode runs -- the card depends only on the book (base art, chapter
title, series aspect), so it is book-level work in one i2v session, never a
17-25 min render inside an episode's window (ep14 paid it twice).  The driver
bakes stragglers before every launch; step 10 only consumes."""
from __future__ import annotations

import json
from pathlib import Path

import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("titles_batch", ROOT / "scripts" / "episode" / "titles_batch.py")
tb = importlib.util.module_from_spec(loader)
sys.modules["titles_batch"] = tb
loader.loader.exec_module(tb)


def book(tmp_path: Path, chapters: int, baked: list[int]) -> Path:
    src = tmp_path / "source" / "chapters"
    src.mkdir(parents=True)
    (src / "ch_00.json").write_text(json.dumps({"title": "front matter"}), encoding="utf-8")
    for n in range(1, chapters + 1):
        (src / f"ch_{n:02d}.json").write_text(json.dumps({"title": f"CHAPTER {n}"}), encoding="utf-8")
    (tmp_path / "title").mkdir()
    for n in baked:
        (tmp_path / "title" / f"ep{n:02d}.mp4").write_bytes(b"card")
    return tmp_path


def test_the_chapters_come_from_the_source_and_skip_front_matter(tmp_path):
    b = book(tmp_path, 3, baked=[])
    assert tb.chapters_of(b) == [1, 2, 3]          # ch_00 is never an episode


def test_missing_names_exactly_the_unbaked_chapters(tmp_path):
    b = book(tmp_path, 4, baked=[1, 3])
    assert tb.missing(b) == [2, 4]
    b2 = book(tmp_path / "full", 2, baked=[1, 2])
    assert tb.missing(b2) == []


def test_no_range_means_whatever_is_missing(tmp_path, monkeypatch):
    b = book(tmp_path, 3, baked=[2])
    from studio import episode_home
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: b)
    made = []
    monkeypatch.setattr(tb.series_title, "main", lambda _id, n: made.append(n))
    assert tb.main("the-book", []) == 0
    assert made == [1, 3]
    made.clear()
    for n in (1, 3):
        (b / "title" / f"ep{n:02d}.mp4").write_bytes(b"card")
    assert tb.main("the-book", []) == 0            # nothing to bake, says so
    assert made == []
