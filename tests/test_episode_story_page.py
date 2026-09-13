"""What stage an episode is at, read off disk.

The first version called episode 1 "delivered" while five takes were still
unrendered, because a master and a report from the PREVIOUS iteration were
lying on disk. A status line that flatters is worse than none: the whole point
of the page is that a fresh window can trust it without asking.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("ep_story", ROOT / "scripts" / "episode" / "story.py")
story = importlib.util.module_from_spec(spec)
spec.loader.exec_module(story)


def home(tmp_path: Path, *made: str) -> Path:
    for name in made:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"")
    (tmp_path / "frames").mkdir(exist_ok=True)
    return tmp_path


def test_an_episode_with_takes_outstanding_is_at_the_take_stage(tmp_path):
    """Even with a master and a report from an earlier iteration on disk."""
    where = home(tmp_path, "master_iter4.mp4", "report_final.html", "placed.json")
    assert story.stage_of(where, takes=[1] * 15, plan_exists=True, total=19) == "8 takes"


def test_an_episode_whose_takes_are_all_in_is_judged_by_what_else_is_on_disk(tmp_path):
    where = home(tmp_path, "master_iter5.mp4", "report_final.html")
    assert story.stage_of(where, takes=[1] * 19, plan_exists=True, total=19).startswith("10 pages")


def test_a_master_with_no_report_is_the_cut_stage(tmp_path):
    where = home(tmp_path, "master_iter5.mp4")
    assert story.stage_of(where, takes=[1] * 19, plan_exists=True, total=19) == "9 cut and QC"


def test_the_earlier_stages_are_read_off_what_exists(tmp_path):
    assert story.stage_of(home(tmp_path), takes=[], plan_exists=True, total=0) == "0 the plan"
    assert story.stage_of(home(tmp_path, "placed.json"), [], True, 0) == "2 timeline"
    assert story.stage_of(home(tmp_path, "frames/plate_lab.png"), [], True, 0) == "3 plates"
    assert story.stage_of(home(tmp_path, "frames/Q02_0.png"), [], True, 0) == "6 storyboards drawn"


def test_no_plan_says_so(tmp_path):
    assert story.stage_of(home(tmp_path), takes=[], plan_exists=False, total=0) == "0 no plan yet"
