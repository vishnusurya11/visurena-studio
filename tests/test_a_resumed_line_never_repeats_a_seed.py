"""A resumed record step says a failed line on NEW seeds every time (Jekyll ep01 HEL, 2026-10-14).

The narrator's l15 ("The lawyer walks on, weighing every word.", 3.0 s) failed the
listen gate on its two tries.  Every relaunch then rendered attempt `0 + tries` (2)
and, on the second pass, attempt `1 + 0` -- the prior was zeroed after the first
pass -- so the second try repeated the seed already refused (sim 0.59 three runs
running) and the record kept `tries: 2`, never advancing.  The autopilot burned
three brain attempts on a loop that could not change its own input.
"""
from __future__ import annotations

from scripts.episode import say_lines as say


def test_a_fresh_line_takes_attempts_zero_and_one():
    assert say.attempts_from(0) == [0, 1]


def test_a_resumed_line_starts_after_its_last_try():
    assert say.attempts_from(2) == [2, 3]
    assert say.attempts_from(4) == [4, 5]


def test_two_resumes_never_share_a_seed():
    first = say.attempts_from(0)
    second = say.attempts_from(first[-1] + 1)
    third = say.attempts_from(second[-1] + 1)
    seen = first + second + third
    assert len(seen) == len(set(seen))


def test_past_the_second_try_the_design_and_the_best_line_take_turns(tmp_path, monkeypatch):
    """l15's alternate reference (the narrator's best line) scored 0.42 and 0.53 where the
    design clip scored 0.59-0.63; a resume that only ever cloned the best line could never
    try the design again.  From the third try the two references alternate."""
    from types import SimpleNamespace
    design, best = tmp_path / "design.wav", tmp_path / "best.wav"
    monkeypatch.setattr(say, "reference_for", lambda book, who: design)
    monkeypatch.setattr(say, "book_best_reference", lambda book, records, who, index: best)
    line = SimpleNamespace(speaker="narrator", index=15)
    got = [say.line_reference(tmp_path, {}, line, a).name for a in range(6)]
    assert got == ["design.wav", "design.wav", "best.wav", "design.wav", "best.wav", "design.wav"]
