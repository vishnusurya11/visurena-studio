"""Out of rungs on a narration shot with a HARD content fault, the terminal
rung is a STILL: the panel the panel eye passed, named in stills.json beside
the takes with the shot's placed seconds, and the verdict signed flagged with
`still` as its rung.  The take stays on disk; nothing is dropped."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from studio import episode_home, panel_content, take_content, take_ladder
from studio.judges import take_eye
from studio.judges.verdict import Fault, Verdict

ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads((ROOT / "tests" / "fixtures" / "vlm" / "take_content_rows.json").read_text(encoding="utf-8"))
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"


def home_with_panels(tmp_path: Path) -> Path:
    home = tmp_path / "book" / "episodes" / "ep05"
    (home / "storyboard").mkdir(parents=True)
    shutil.copy(PLAN, home / "plan.json")
    for i in (1, 2, 3):
        Image.new("RGB", (8, 8), (i * 30, 0, 0)).save(home / "storyboard" / f"shot_{i:02d}.png")
    episode_home.write_json(home / "placed.json", {"shots": [{"index": i, "seconds": 3.0 + i} for i in (1, 2, 3)]})
    return home


def faulted() -> Verdict:
    faults = take_eye.content_faults(2, ROWS["content"]["T02"])
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=2,
                   faults=faults, terminal="keep_best")


def test_the_content_fault_is_hard_and_the_narration_take_becomes_a_still(tmp_path):
    home = home_with_panels(tmp_path)
    plan = episode_home.load_plan(tmp_path / "book", 5)
    out = take_ladder.terminal(home, plan, faulted(), order=[1, 2, 3])
    assert out.terminal == "still"
    assert out.faults[0].kind == "content" and out.faults[0].evidence["still"] == "storyboard/shot_02.png"
    stills = take_ladder.load_stills(home)
    assert stills[2]["panel"] == "episodes/ep05/storyboard/shot_02.png"
    assert stills[2]["seconds"] == 5.0 and "content" in stills[2]["why"]
    assert (home / "takes" / "r2v" / "stills.json").exists()


def test_a_take_with_no_passed_panel_is_kept_best_instead(tmp_path):
    home = home_with_panels(tmp_path)
    (home / "storyboard" / "shot_02.png").unlink()
    out = take_ladder.terminal(home, episode_home.load_plan(tmp_path / "book", 5), faulted(), order=[1, 2, 3])
    assert out.terminal == "keep_best" and not take_ladder.load_stills(home)


def test_the_second_vote_reads_framing_and_action_and_a_malformed_answer_raises():
    said = take_content.second_vote(ROWS["votes"]["T01"])
    assert said == {"framing": "medium_close", "action": "writing"}
    planned = ROWS["planned"]["T01"]
    assert take_eye.vote_faults(1, said, planned["size"], planned["motion"]) == []
    wide = take_content.second_vote(ROWS["votes"]["T02"])
    kinds = {f.kind: f.severity for f in take_eye.vote_faults(2, wide, "medium_close", ROWS["planned"]["T02"]["motion"])}
    assert kinds == {"framing": "low", "action": "low"}
    with pytest.raises(panel_content.Unreadable):
        take_content.second_vote(ROWS["votes"]["T03"])
    assert "framing" in take_content.ASK and "action" in take_content.ASK


def test_a_low_fault_alone_is_kept_best_never_a_still(tmp_path):
    home = home_with_panels(tmp_path)
    low = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, terminal="keep_best",
                  faults=[Fault(kind="framing", where="T02", severity="low")])
    out = take_ladder.terminal(home, episode_home.load_plan(tmp_path / "book", 5), low, order=[1, 2, 3])
    assert out.terminal == "keep_best" and not take_ladder.load_stills(home)
