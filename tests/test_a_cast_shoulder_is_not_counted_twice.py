"""Jekyll ep05 shots 6 and 22 (owner deleted the episode, 2026-10-28: "same characters duplicated
multiple times"). Each is a two-person over-the-shoulder medium close -- "over the doctor's shoulder
toward the lawyer", faces [utterson, jekyll] -- and each panel drew THREE men: the shoulder, and
the shoulder's owner again facing the camera. The panel gate allowed cast + 1 for the shoulder,
3 for 2, and passed it ("people": 3, "passed": true).

The shoulder is a person the shot already casts when it casts two: the allowance is only for a
shot casting one, whose shoulder belongs to someone unnamed (J5)."""
from __future__ import annotations

from studio import panel_content as pc

OTS = "Medium close over the doctor's shoulder toward the lawyer as he presses his question."


def seen(people: int) -> pc.Seen:
    return pc.Seen(people=people, landform="indoors")


def counted(frame: str, planned: int, people: int) -> bool:
    return any("declared" in f for f in pc.faults(seen(people), frame, planned, crowd=False,
                                                   flat=True, night=True, size="medium_close"))


def test_a_two_cast_shoulder_shot_with_three_figures_is_a_fault():
    assert counted(OTS, planned=2, people=3)


def test_a_two_cast_shoulder_shot_with_two_figures_passes():
    assert not counted(OTS, planned=2, people=2)


def test_a_one_cast_shoulder_shot_still_allows_the_shoulder():
    assert not counted(OTS, planned=1, people=2)


def test_the_allowance_is_for_one_cast_only():
    assert pc.shoulder_figure(OTS, planned=1) == 1
    assert pc.shoulder_figure(OTS, planned=2) == 0
