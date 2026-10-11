"""The book video's cold open reads each chapter's SHIPPED timeline through
`episode_home.shipped_timeline`, never `placed.json` raw (C2_verdict #2).

`load_placed` is the wrong door here: it refuses a timeline older than its plan,
which is every chapter WotW ep02-07 and Scarlet 1-14 shipped with.  The cold
open picks shots from masters that are already cut, so the timeline they were
cut on is the one to read.  The change must not move the book video by a frame:
the candidates are compared against a frozen copy of the old body."""
from __future__ import annotations

import functools
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pytest

from studio import book_title as bt
from studio import episode_home

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_book_title_c2", ROOT / "scripts" / "episode" / "book_title.py")
runner = importlib.util.module_from_spec(spec)
sys.modules["ep_book_title_c2"] = runner
spec.loader.exec_module(runner)

BOOKS = {"20260827135508_the-war-of-the-worlds": 27, "20260822113400_a-study-in-scarlet": 14}


def old_cold_candidates(book: Path, episodes: int) -> list[dict]:
    """FROZEN: the body of cold_candidates before C2_verdict #2."""
    out = []
    for n in range(1, episodes + 1):
        ep = episode_home.home(book, n)
        if not (ep / "placed.json").exists() or not runner.chapter_main(book, n).exists() or not runner.square_short(book, n):
            continue
        for c in bt.candidates(n, episode_home.read_json(ep / "plan.json"), episode_home.read_json(ep / "placed.json")):
            out.append(c | {"sharp": runner.sharpness(runner.chapter_main(book, n), (c["start_s"] + c["end_s"]) / 2)})
    return out


def test_shipped_timeline_reads_the_file_as_it_stands(tmp_path, monkeypatch):
    monkeypatch.setattr(episode_home, "home", lambda book, n: tmp_path / f"ep{n:02d}")
    (tmp_path / "ep01").mkdir()
    (tmp_path / "ep01" / "placed.json").write_text(json.dumps({"shots": [1]}))
    assert episode_home.shipped_timeline(tmp_path, 1) == {"shots": [1]}
    assert episode_home.shipped_timeline(tmp_path, 2) is None


def test_a_plan_newer_than_its_timeline_still_yields_candidates(tmp_path, monkeypatch):
    ep = tmp_path / "ep01"
    ep.mkdir()
    (ep / "placed.json").write_text(json.dumps({"t": 1}))
    (ep / "plan.json").write_text(json.dumps({"p": 1}))
    old = time.time() - 3600
    os.utime(ep / "placed.json", (old, old))
    monkeypatch.setattr(episode_home, "home", lambda book, n: tmp_path / f"ep{n:02d}")
    monkeypatch.setattr(runner, "chapter_main", lambda book, n: ep / "plan.json")
    monkeypatch.setattr(runner, "square_short", lambda book, n: True)
    monkeypatch.setattr(runner, "sharpness", lambda video, at: 1.0)
    monkeypatch.setattr(bt, "candidates", lambda n, plan, placed: [{"start_s": 0, "end_s": 2, "t": placed["t"]}])
    assert runner.cold_candidates(tmp_path, 1) == [{"start_s": 0, "end_s": 2, "t": 1, "sharp": 1.0}]


@pytest.mark.parametrize("name", sorted(BOOKS))
def test_the_cold_candidates_are_unchanged_on_the_shipped_books(name, monkeypatch):
    book = episode_home.book_dir(name)
    if not (book / "compilation" / "chapters").exists():
        pytest.skip(f"{name}: no compiled chapters on this machine")
    monkeypatch.setattr(runner, "sharpness", lambda video, at: 1.0)
    # square_short hashes each shipped master; both bodies call it alike, so it is read once
    monkeypatch.setattr(runner, "square_short", functools.cache(runner.square_short))
    old = old_cold_candidates(book, BOOKS[name])
    assert old, "the replay must cover real candidates"
    assert runner.cold_candidates(book, BOOKS[name]) == old
