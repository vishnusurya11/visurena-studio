"""The dialogue ceiling follows the chapter (anime-TV grammar, 2026-10-17;
research 04 P4).  The floor already did (ep22: a chapter that speaks no line has
no floor); the ceiling was the contract's 20 % for every chapter, and Jekyll's
chapter 1 -- nearly all quoted speech -- could not put its bargain in the
characters' mouths.  The ceiling is the chapter's speech + 8 points, never under
the old 20 % and never over 35 %; a chapter the battery cannot read keeps 20 %.

An inner line is a thought, not the chapter's speech: it meets neither the floor
nor the ceiling, and its speaker is a cast member, never the narrator.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_gates


def _ep(dialogue_words: int, other_words: int, other_kind: str = "narration"):
    lines = [SimpleNamespace(kind="dialogue", text=" ".join(["w"] * dialogue_words)),
             SimpleNamespace(kind=other_kind, text=" ".join(["w"] * other_words))]
    return SimpleNamespace(lines=lines)


def test_the_ceiling_is_the_chapters_speech_plus_eight_points_inside_20_to_35():
    assert plan_gates.dial_ceiling(None) == 0.20
    assert plan_gates.dial_ceiling(0.05) == 0.20
    assert plan_gates.dial_ceiling(0.20) == 0.28
    assert plan_gates.dial_ceiling(0.60) == 0.35


def test_a_talky_chapter_lets_its_plan_speak_more():
    ep = _ep(25, 75)                                   # 25 % dialogue
    assert plan_gates.dial_faults(ep, speech=0.05)      # a quiet chapter: over 20 %
    assert plan_gates.dial_faults(ep, speech=0.40) == []


def test_an_inner_line_is_not_the_chapters_speech():
    ep = _ep(0, 10, "inner")
    ep.lines.append(SimpleNamespace(kind="narration", text=" ".join(["w"] * 90)))
    assert plan_gates.dial_faults(ep, speech=0.5)       # the floor is not met by a thought


def test_an_inner_line_is_a_cast_members_never_the_narrators():
    line = SimpleNamespace(index=3, kind="inner", speaker="narrator", text="Hyde.")
    assert plan_gates.speaker_fault(line, {"lawyer"}, "narrator", ["lawyer"])
    line.speaker = "lawyer"
    assert plan_gates.speaker_fault(line, {"lawyer"}, "narrator", ["lawyer"]) is None
