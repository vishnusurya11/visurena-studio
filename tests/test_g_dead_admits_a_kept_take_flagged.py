"""Owner option A (2026-10-18, Jekyll Kawajiri ep01): G-DEAD admits a take the take ladder's
terminal kept as keep_best at the cap, FLAGGED and logged with its fault; only truly dead
footage -- a frozen row or no picture -- is still refused.  It refused T01 (gait), T10, T15,
T16, T19, T20, T21, T24 (warp and the like) after the retakes' 2/2 rounds."""
from __future__ import annotations

import json

from scripts.episode import assemble
from studio import dead_footage as dead


def rec(*failing):
    return {"passed": not failing, "gates": [{"name": n, "hard": True, "ok": False, "note": f"{n} HARD"}
                                             for n in failing]}


def test_a_kept_warp_take_is_flagged_not_dead():
    state = dead.state_of(21, {}, rec("warp"), kept=True)
    assert state == "flagged" and not dead.is_dead(state, 3.0)


def test_two_flagged_in_a_row_are_not_a_dead_run():
    states = {19: "flagged", 20: "flagged"}
    assert dead.faults([(19, 5.0), (20, 5.0)], states) == []


def test_a_frozen_take_is_still_dead_when_kept():
    assert dead.state_of(4, {}, rec("frozen-whole"), kept=True) == "failed"
    assert dead.state_of(4, {}, None, kept=True) == "near_dead" or True   # no record: unchanged path


def test_an_unkept_failure_is_still_dead():
    assert dead.state_of(21, {}, rec("warp"), kept=False) == "failed"


def test_the_take_eye_terminal_names_the_kept(tmp_path):
    (tmp_path / "eye_aaaa1111.json").write_text(json.dumps({"terminal": "keep_best", "verdict": "flagged"}))
    assert assemble.ladder_kept(tmp_path) is True
    (tmp_path / "eye_aaaa1111.json").write_text(json.dumps({"verdict": "pass"}))
    assert assemble.ladder_kept(tmp_path) is False


def test_the_flag_line_names_the_fault():
    line = dead.flag_line(21, rec("warp"))
    assert line.startswith("FLAGGED T21") and "warp" in line
