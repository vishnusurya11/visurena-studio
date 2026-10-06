"""A twin fault on a take routes to ONE seed retake, and a reproduced twin to
the terminal -- by construction, with zero routing changes.

G-TWIN cure for takes: 'twin' is DELIBERATELY absent from INPUT_BORNE (the
pin), MOVABLE, LAG and NEVER_SEED, so `cure_of` falls through to 'seed';
`evidence.repeated` then returns '' and the terminal answers -- a narration
shot with this HARD fault is held on its PASSED panel as a still, a dialogue
shot ships keep_best flagged high.  All injected; no render, no API.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from studio import episode_home, take_ladder
from studio.judges.verdict import Fault, Verdict

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
LINE = "twin: woman in a grey shawl x2 (2 figures, 1 distinct)"


def twin(where: str, repeated: bool = False) -> Fault:
    return Fault(kind="twin", where=where, note=LINE, evidence={"hard": True, "repeated": repeated})


def test_a_fresh_twin_wants_one_seed_retake():
    assert take_ladder.cure_of([twin("T11")]) == "seed"


def test_a_reproduced_twin_goes_to_the_terminal():
    assert take_ladder.cure_of([twin("T11", repeated=True)]) == ""


def test_the_pin_twin_is_not_input_borne():
    """A future refactor must not drop 'twin' into INPUT_BORNE silently: that
    routes it to no retake at all and skips the one cure it has."""
    assert "twin" not in take_ladder.INPUT_BORNE
    assert "twin" not in take_ladder.MOVABLE
    assert "twin" not in take_ladder.LAG
    assert "twin" not in take_ladder.NEVER_SEED


def home_with_panels(tmp_path: Path) -> Path:
    home = tmp_path / "book" / "episodes" / "ep05"
    (home / "storyboard").mkdir(parents=True)
    shutil.copy(PLAN, home / "plan.json")
    for i in (2, 4):
        Image.new("RGB", (8, 8), (i * 30, 0, 0)).save(home / "storyboard" / f"shot_{i:02d}.png")
    episode_home.write_json(home / "placed.json", {"shots": [{"index": i, "seconds": 3.0 + i} for i in (2, 4)]})
    return home


def verdict_of(*faults: Fault) -> Verdict:
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                   faults=list(faults), terminal="keep_best")


def test_a_twin_narration_take_is_held_on_its_passed_panel(tmp_path):
    home = home_with_panels(tmp_path)
    plan = episode_home.load_plan(tmp_path / "book", 5)
    out = take_ladder.terminal(home, plan, verdict_of(twin("T02", repeated=True)), order=[2, 4])
    assert out.terminal == "still"
    assert out.faults[0].evidence["still"] == "storyboard/shot_02.png"
    stills = take_ladder.load_stills(home)
    assert "twin" in stills[2]["why"]


def test_a_twin_dialogue_take_is_kept_best_flagged_high(tmp_path):
    home = home_with_panels(tmp_path)
    plan = episode_home.load_plan(tmp_path / "book", 5)
    out = take_ladder.terminal(home, plan, verdict_of(twin("T04", repeated=True)), order=[2, 4])
    assert out.terminal == "keep_best"
    assert out.faults[0].severity == "high"
    assert not take_ladder.load_stills(home)
