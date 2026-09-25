"""A dialogue, turn or button shot never becomes a still: a spoken line on a
held picture breaks the mouth, and the turn is the one shot the episode
exists for.  Out of rungs, the best take is kept and the verdict signed
flagged with `severity: high` on those faults; so is a third still."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from studio import episode_home, take_ladder
from studio.judges.verdict import Fault, Verdict

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
DIALOGUE, TURN, BUTTON, NARRATION = 4, 14, 23, 9


def home(tmp_path: Path) -> Path:
    where = tmp_path / "book" / "episodes" / "ep05"
    (where / "storyboard").mkdir(parents=True)
    shutil.copy(PLAN, where / "plan.json")
    for i in (DIALOGUE, TURN, BUTTON, NARRATION, 10, 11, 13):
        Image.new("RGB", (8, 8), (i, 0, 0)).save(where / "storyboard" / f"shot_{i:02d}.png")
    episode_home.write_json(where / "placed.json", {"shots": [{"index": i, "seconds": 4.0} for i in range(30)]})
    return where


def faulted(*indices: int) -> Verdict:
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, terminal="keep_best",
                   faults=[Fault(kind="content", where=f"T{i:02d}", evidence={"hard": True}) for i in indices])


def test_dialogue_turn_and_button_shots_are_kept_best_high(tmp_path):
    where = home(tmp_path)
    plan = episode_home.load_plan(tmp_path / "book", 5)
    order = sorted({DIALOGUE, TURN, BUTTON, NARRATION, 10, 11})
    out = take_ladder.terminal(where, plan, faulted(DIALOGUE, TURN, BUTTON), order=order)
    assert out.terminal == "keep_best"
    assert [f.severity for f in out.faults] == ["high", "high", "high"]
    assert take_ladder.load_stills(where) == {}
    assert [take_ladder.shot_kind(plan, i) for i in (DIALOGUE, TURN, NARRATION)] == ["dialogue", "turn", "narration"]
    assert take_ladder.shot_kind(plan, BUTTON) in ("button", "dialogue")   # this plan's button is spoken


def test_a_third_still_is_kept_best_high_and_the_two_stills_stand(tmp_path):
    where = home(tmp_path)
    plan = episode_home.load_plan(tmp_path / "book", 5)
    take_ladder.write_still(where, 9, where / "storyboard" / "shot_09.png", 4.0, "content")
    take_ladder.write_still(where, 11, where / "storyboard" / "shot_11.png", 4.0, "content")
    out = take_ladder.terminal(where, plan, faulted(TURN - 1), order=[9, 11, 13, 14])
    assert out.terminal == "keep_best" and out.faults[0].severity == "high"
    assert sorted(take_ladder.load_stills(where)) == [9, 11]


def test_a_narration_take_beside_the_faulted_dialogue_take_may_still_be_a_still(tmp_path):
    where = home(tmp_path)
    plan = episode_home.load_plan(tmp_path / "book", 5)
    out = take_ladder.terminal(where, plan, faulted(DIALOGUE, NARRATION), order=[4, 9, 10, 11])
    assert out.terminal == "still"
    assert {f.where: f.severity for f in out.faults} == {"T04": "high", "T09": "normal"}
    assert sorted(take_ladder.load_stills(where)) == [9]
