"""The measured speech gap is refused at the timeline, before any take renders.

ep13 (finding 64): the plan battery checked the PROJECTED gap and passed; the
measured timeline carried 6.72 s against QC's 6.0 s wall, found only at QC
after five masters, and cost a retake of T09.  The same measure, one step 05.
"""
from studio import speech_gap

PLACED = {"duration_s": 20.0,
          "shots": [{"index": 0, "t_start": 0.0, "t_end": 8.0}, {"index": 1, "t_start": 8.0, "t_end": 20.0}],
          "lines": [{"at": 0.3, "seconds": 2.0, "shot": 0}, {"at": 9.0, "seconds": 10.5, "shot": 1}]}


def test_the_longest_gap_is_measured_from_the_placed_lines():
    assert speech_gap.longest_gap(PLACED["lines"], 20.0) == 6.7


def test_a_gap_over_the_wall_is_refused_naming_its_shot():
    got = speech_gap.refusal(PLACED)
    assert got and "6.70" in got and "shot 0" in got


def test_a_gap_under_the_wall_passes():
    ok = {**PLACED, "lines": [{"at": 0.3, "seconds": 5.0, "shot": 0}, PLACED["lines"][1]]}
    assert speech_gap.refusal(ok) is None


def test_step_05_refuses_and_is_not_done_over_the_wall(monkeypatch):
    import importlib.util
    import sys
    from pathlib import Path
    import pytest
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("step_05_gap", root / "scripts/episode/step_05_timeline.py")
    step = importlib.util.module_from_spec(spec)
    sys.modules["step_05_gap"] = step
    spec.loader.exec_module(step)
    monkeypatch.setattr(step, "fresh", lambda book, number: True)
    monkeypatch.setattr(step, "placed_of", lambda book, number: PLACED)

    class Ctx:
        book_dir, number = Path("."), 13
        def run_script(self, *a, **k):
            pass
    assert step.done(Ctx()) is False
    with pytest.raises(SystemExit, match="hole in speech"):
        step.run(Ctx())
