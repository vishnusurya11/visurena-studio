"""`require` refuses a `fault` file and only a `fault` file: nobody writes one
now, and if a person ever does, it is work to do, whoever signed it."""
from __future__ import annotations

import pytest

from studio import eye_verdict as ev


def _pictures(folder):
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / "shot_01.png"
    p.write_bytes(b"\x02" * 8)
    return [p]


def test_an_owner_fault_is_refused(tmp_path):
    pics = _pictures(tmp_path / "board")
    ev.sign(tmp_path / "board", pics, "fault", "two hats on one man")
    assert not ev.passed(tmp_path / "board", pics)
    with pytest.raises(SystemExit, match="two hats"):
        ev.require(tmp_path / "board", pics, "EYE", "look")


def test_a_fault_signed_in_a_judge_name_is_refused_the_same(tmp_path):
    pics = _pictures(tmp_path / "board")
    ev.sign(tmp_path / "board", pics, "fault", "a hand-written fault", signed_by="judge:x@1")
    with pytest.raises(SystemExit, match="fault"):
        ev.require(tmp_path / "board", pics, "EYE", "look")


def test_pass_and_flagged_are_the_only_words_require_accepts(tmp_path):
    pics = _pictures(tmp_path / "board")
    for word in ("pass", "flagged"):
        ev.sign(tmp_path / "board", pics, word, "seen")
        assert ev.require(tmp_path / "board", pics, "EYE", "look")["verdict"] == word
