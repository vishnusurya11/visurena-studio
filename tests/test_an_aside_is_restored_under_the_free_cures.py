"""ep21 (2026-10-08 05:49Z): the ladder deferred on a 17-word style line; on
the relaunch, plan_repair --from-aside validated the RAW aside before any cure
and refused, so the one-line cure never ran and the climb started over from
nothing.  The restore runs the free pre-contract cures first."""
from __future__ import annotations

import importlib

from studio import house_style


def test_a_restored_aside_has_its_style_line_trimmed_and_its_button_beat():
    pr = importlib.import_module("scripts.episode.plan_repair")
    doc = {"where": "a ruined villa in Mortlake", "light": "grey daylight through the kitchen doorway, dust in the air, deep shadow",
           "shots": [], "lines": []}
    out = pr.restored(dict(doc))
    assert not house_style.style_faults(out["where"], out["light"])


def test_a_cure_that_raises_never_breaks_the_restore(monkeypatch):
    pr = importlib.import_module("scripts.episode.plan_repair")

    def boom(doc):
        raise RuntimeError("x")
    monkeypatch.setattr(pr.pc, "button_beat", boom)
    assert pr.restored({"where": "Woking", "light": "noon sun", "shots": [], "lines": []})["where"] == "Woking"


def test_an_aside_with_no_draft_is_named_not_crashed(tmp_path, monkeypatch):
    """ep21's climb never wrote a plan, so its aside held draft: null and the
    restore died on None.get -- a traceback where a sentence belongs."""
    import json
    import pytest
    pr = importlib.import_module("scripts.episode.plan_repair")
    from studio import episode_home
    book = tmp_path / "20990101000000_book"
    home = episode_home.home(book, 3)
    home.mkdir(parents=True)
    (home / "plan.deferred.json").write_text(json.dumps({"verdict": "DEFERRED", "draft": None}), encoding="utf-8")
    monkeypatch.setattr(episode_home, "book_dir", lambda book_id: book)
    with pytest.raises(SystemExit, match="holds no draft"):
        pr.main("20990101000000", 3, from_aside=True, no_llm=True)
