"""Jekyll Kawajiri ep01 (2026-10-18 17:03): step 05 refused "the measured timeline still packs
[[4, 5], [16, 17], [24, 25]] after the hold cure" on an anime-TV grammar plan.  Its packer read
the legacy 8 s budget; takes_r2v packs a grammar plan at `episode_takes.budget_for` (ONE_SHOT),
so every shot is its own take and nothing the step refused would ever have been packed."""
from __future__ import annotations

import json
from types import SimpleNamespace

from scripts.episode import step_05_timeline as step
from studio import episode_home

PLACED = {"shots": [{"index": 4, "seconds": 3.0}, {"index": 5, "seconds": 2.5}]}


def _ctx(tmp_path, monkeypatch, grammar: str):
    book = tmp_path / "book"
    plan = episode_home.plan_path(book, 1)
    plan.parent.mkdir(parents=True)
    doc = {"grammar": grammar, "lines": [],
           "shots": [{"index": 4, "setup": "corner"}, {"index": 5, "setup": "corner"}]}
    plan.write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(step, "placed_of", lambda b, n: PLACED)
    return SimpleNamespace(book_dir=book, number=1)


def test_a_grammar_plan_packs_nothing(tmp_path, monkeypatch):
    assert step.packed(_ctx(tmp_path, monkeypatch, "anime_tv")) == []


def test_a_legacy_plan_still_packs_its_short_pair(tmp_path, monkeypatch):
    assert step.packed(_ctx(tmp_path, monkeypatch, "")) == [[4, 5]]
