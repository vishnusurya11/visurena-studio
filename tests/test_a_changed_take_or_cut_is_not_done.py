"""Steps 09 and 10 are not done when what they made is older than its inputs.

ep12, 2026-09-25: shot 16 was re-planned (locked, shorter beats) and T19 given
a head; the runner printed 'step 09 (shoot) skipped: output exists' and 'step
10 (edit) skipped: output exists', so T16 was never re-rendered, the master
never re-cut, and QC measured the old cut against the new timeline (7
segments off). Existence is not currency.
"""
import os
import time
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import step_09_shoot as shoot
from scripts.episode import step_10_edit as edit
from studio import episode_home


def ctx_for(tmp_path):
    book = tmp_path / "book"
    home = episode_home.home(book, 12)
    (home / "takes" / "r2v").mkdir(parents=True)
    return SimpleNamespace(book_dir=book, number=12, home=home, extra=[])


def touch(path: Path, t: float):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    os.utime(path, (t, t))


# ---- step 10: the master against what it is cut from ---------------------------------

def test_a_master_older_than_a_take_is_not_done(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    now = time.time()
    monkeypatch.setattr(edit, "title_clip", lambda c: tmp_path / "title.mp4")
    touch(tmp_path / "title.mp4", now - 100)
    touch(episode_home.master_path(ctx.book_dir, 12, "r2v"), now - 50)
    touch(ctx.home / "takes" / "r2v" / "T16.mp4", now - 10)
    ctx.extra = ["--engine=r2v"]
    assert edit.done(ctx) is False


def test_a_master_newer_than_its_inputs_is_done(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    now = time.time()
    monkeypatch.setattr(edit, "title_clip", lambda c: tmp_path / "title.mp4")
    touch(tmp_path / "title.mp4", now - 100)
    touch(ctx.home / "takes" / "r2v" / "T16.mp4", now - 60)
    touch(ctx.home / "heads.json", now - 60)
    touch(episode_home.master_path(ctx.book_dir, 12, "r2v"), now - 10)
    ctx.extra = ["--engine=r2v"]
    assert edit.done(ctx) is True


def test_a_head_written_after_the_cut_is_not_done(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    now = time.time()
    monkeypatch.setattr(edit, "title_clip", lambda c: tmp_path / "title.mp4")
    touch(tmp_path / "title.mp4", now - 100)
    touch(episode_home.master_path(ctx.book_dir, 12, "r2v"), now - 50)
    touch(ctx.home / "heads.json", now - 5)
    ctx.extra = ["--engine=r2v"]
    assert edit.done(ctx) is False


# ---- step 09: every take current to its built card -----------------------------------

def test_a_take_stale_to_its_card_is_not_done(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    room = ctx.home / "takes" / "r2v"
    episode_home.write_json(room / "prompts.json", [{"index": 16, "prompt": "new", "anchors": []}])
    monkeypatch.setattr(shoot, "card_pictures", lambda c, book, n: [])
    monkeypatch.setattr(shoot.take_currency, "is_current", lambda built, take, pictures=None: built == "old")
    assert shoot.stale_takes(ctx) == [16]


def test_takes_current_to_their_cards_are_not_stale(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path)
    room = ctx.home / "takes" / "r2v"
    episode_home.write_json(room / "prompts.json", [{"index": 16, "prompt": "same", "anchors": []}])
    monkeypatch.setattr(shoot, "card_pictures", lambda c, book, n: [])
    monkeypatch.setattr(shoot.take_currency, "is_current", lambda built, take, pictures=None: True)
    assert shoot.stale_takes(ctx) == []
