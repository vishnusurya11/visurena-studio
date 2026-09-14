"""The next master_iter number is read off the room the masters are actually in.

`assemble` keeps every cut under a numbered name so no iteration overwrites the
one before it -- the owner's standing rule.  It chose the number with

    home.glob("master_iter*.mp4")

and masters moved to `home/"cut"/` in the layout change.  The glob then matches
nothing on every episode, `max(taken, default=0) + 1` is always 1, and each
assemble writes `master_iter1.mp4` over the last one.  The rule would have been
silently inverted: the numbering exists precisely so this cannot happen.

MEASURED 2026-09-14: episode 3 holds master_iter1 through master_iter6 in
`cut/`, all written before the move; episode 4 was one assemble away from
starting again at 1.

Four readers globbed masters from `home`: assemble (the number), runcards (the
report's newest cut), and story twice (the stage line, which reported a
published episode as "8 takes").  `report_final.html` had moved to `reports/`
in the same way.
"""
from pathlib import Path

import pytest


def masters(home: Path, *names: str) -> Path:
    (home / "cut").mkdir(parents=True, exist_ok=True)
    for n in names:
        (home / "cut" / n).write_bytes(b"x")
    return home


def test_the_next_number_follows_the_masters_on_disk(tmp_path):
    from scripts.episode.assemble import next_iteration
    home = masters(tmp_path, "master_iter1.mp4", "master_iter2.mp4", "master_iter6.mp4")
    assert next_iteration(home) == 7


def test_the_first_cut_is_iteration_one(tmp_path):
    from scripts.episode.assemble import next_iteration
    assert next_iteration(masters(tmp_path)) == 1


def test_a_gap_is_never_filled(tmp_path):
    """Always the next number, so a file name is a moment in time."""
    from scripts.episode.assemble import next_iteration
    assert next_iteration(masters(tmp_path, "master_iter1.mp4", "master_iter5.mp4")) == 6


def test_the_delivered_master_is_not_counted(tmp_path):
    from scripts.episode.assemble import next_iteration
    home = masters(tmp_path, "master_r2v.mp4", "master_withends.mp4", "master_iter3.mp4")
    assert next_iteration(home) == 4


def test_it_does_not_look_in_the_episode_root(tmp_path):
    """A stray master left in the old place must not decide the number."""
    from scripts.episode.assemble import next_iteration
    home = masters(tmp_path, "master_iter1.mp4")
    (tmp_path / "master_iter9.mp4").write_bytes(b"x")
    assert next_iteration(home) == 2


def test_a_published_episode_reads_as_delivered(tmp_path):
    """The stage line called episode 3 "8 takes" because it looked for the
    masters and the report in rooms they had left."""
    import importlib.util
    import sys
    ROOT = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("ep_story2", ROOT / "scripts" / "episode" / "story.py")
    story = importlib.util.module_from_spec(spec)
    sys.modules["ep_story2"] = story
    spec.loader.exec_module(story)

    home = masters(tmp_path, "master_iter6.mp4")
    (home / "reports").mkdir(parents=True, exist_ok=True)
    (home / "reports" / "report_final.html").write_text("x", encoding="utf-8")
    assert story.stage_of(home, takes=[1] * 24, plan_exists=True, total=24) == "10 pages — delivered"
