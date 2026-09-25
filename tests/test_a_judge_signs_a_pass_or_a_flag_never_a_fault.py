"""A judge signs `pass` or, at a terminal rung, `flagged`.  It never signs a
`fault`: a fault is work to do (the ladder's), not a file for the next step to
refuse on.  The verdict file carries who signed and the faults it lists."""
from __future__ import annotations

import json

import pytest

from studio import eye_verdict as ev
from studio.judges.verdict import Fault, Verdict


def _pictures(folder):
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for i, name in enumerate(("shot_01.png", "shot_02.png")):
        (folder / name).write_bytes(bytes([i]) * 8)
        out.append(folder / name)
    return out


def _verdict(passed: bool, terminal: str = "", faults=()):
    return Verdict(judge="panel_eye", version="1", passed=passed, faults=list(faults),
                   confidence=1.0, reads=2, terminal=terminal)


def test_flagged_is_a_verdict_word():
    assert ev.VERDICTS == ("pass", "flagged", "fault")


def test_a_passing_verdict_signs_pass_under_the_judge_name(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    out = ev.sign_verdict(tmp_path / "storyboard", pics, _verdict(True))
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["verdict"] == "pass" and doc["signed_by"] == "judge:panel_eye@1"
    assert doc["faults"] == [] and doc["note"]


def test_a_terminal_verdict_signs_flagged_with_its_faults_listed(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    fault = Fault(kind="clones", where="shot_02", evidence={"cosine": 0.81, "wall": 0.75})
    out = ev.sign_verdict(tmp_path / "storyboard", pics, _verdict(False, "keep_best", [fault]))
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["terminal"] == "keep_best"
    assert doc["faults"][0]["kind"] == "clones" and doc["faults"][0]["where"] == "shot_02"
    assert doc["faults"][0]["evidence"] == {"cosine": 0.81, "wall": 0.75}


def test_a_fault_without_a_terminal_is_never_signed(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    fault = Fault(kind="lettering", where="shot_01")
    with pytest.raises(SystemExit, match="ladder"):
        ev.sign_verdict(tmp_path / "storyboard", pics, _verdict(False, faults=[fault]))
    assert ev.current(tmp_path / "storyboard", pics) is None
