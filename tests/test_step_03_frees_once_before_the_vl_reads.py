"""Step 03 frees the engine ONCE at the vl family boundary, never per read, and times each read."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import scripts.episode.step_03_places as step


def ctx_of(tmp_path, logs):
    return SimpleNamespace(home=tmp_path, book_dir=tmp_path, log=lambda msg, **kw: logs.append(msg))


def test_free_once_before_the_reads_and_each_read_is_timed(tmp_path, monkeypatch):
    events, logs = [], []
    monkeypatch.setattr(step, "FREE", lambda family: events.append(("free", family)))
    monkeypatch.setattr(step, "READ", lambda path: events.append(("read", Path(path).name)) or [{"x": 1}])
    monkeypatch.setattr(step, "by_setup", lambda book, doc: {"a": Path("a.png"), "b": Path("b.png"), "c": Path("c.png")})
    readings = step.read_places(ctx_of(tmp_path, logs), {})
    assert events == [("free", "vl"), ("read", "a.png"), ("read", "b.png"), ("read", "c.png")]
    assert sorted(readings) == ["a", "b", "c"]
    assert all("device=cuda" in line and "s " in line for line in logs) and len(logs) == 3


def test_no_setup_pictures_means_no_free(tmp_path, monkeypatch):
    events = []
    monkeypatch.setattr(step, "FREE", lambda family: events.append(family))
    monkeypatch.setattr(step, "by_setup", lambda book, doc: {})
    assert step.read_places(ctx_of(tmp_path, []), {}) == {}
    assert events == []
