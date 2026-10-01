"""Five-hour plan fix 3b (2026-09-30): title cards are pre-baked for the whole
season before the episodes are written, so the 17-25 min render leaves every
episode's critical path.  A card without a plan takes the SERIES aspect."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    loader = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "episode" / f"{name}.py")
    mod = importlib.util.module_from_spec(loader)
    sys.modules[name] = mod
    loader.loader.exec_module(mod)
    return mod


def test_an_unwritten_episode_takes_the_series_aspect(tmp_path, monkeypatch):
    st = load("series_title")
    from studio import episode_home
    monkeypatch.setattr(episode_home, "home", lambda book, n: tmp_path / f"ep{n:02d}")
    assert st.aspect_of(tmp_path, 15) == "1:1"               # canvas.DEFAULT, no series.json
    (tmp_path / "series.json").write_text(json.dumps({"aspect": "9:16"}), encoding="utf-8")
    assert st.aspect_of(tmp_path, 15) == "9:16"              # the series' own word


def test_the_batch_takes_an_inclusive_range():
    tb = load("titles_batch")
    assert tb.numbers_of(["15", "27"]) == list(range(15, 28))
    assert tb.numbers_of(["15"]) == [15]
    with pytest.raises(SystemExit):
        tb.numbers_of(["20", "15"])
    # no range = whatever the book is missing (owner design 2026-09-30;
    # resolved in main against the book's own chapters)
    assert tb.numbers_of([]) == []
