"""An eye verdict is bound to the bytes it was given: the same pictures in any
order give the same word; a changed picture lapses the signature; a step asks
for one by raising the gate with the file's relative name."""
from __future__ import annotations

import pytest

from studio import eye_verdict as ev
from studio.escalate import Escalation


def _pictures(folder, names=("shot_01.png", "shot_02.png"), salt=b""):
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for i, name in enumerate(names):
        p = folder / name
        p.write_bytes(bytes([i]) * 8 + salt)
        out.append(p)
    return out


def test_the_fingerprint_is_stable_and_order_free(tmp_path):
    pics = _pictures(tmp_path / "a")
    assert ev.fingerprint(pics) == ev.fingerprint(list(reversed(pics)))
    assert len(ev.fingerprint(pics)) == 8


def test_a_changed_picture_changes_the_fingerprint(tmp_path):
    before = ev.fingerprint(_pictures(tmp_path / "a"))
    after = ev.fingerprint(_pictures(tmp_path / "a", salt=b"x"))
    assert before != after


def test_the_path_names_the_sha(tmp_path):
    assert ev.path(tmp_path, "abcd1234") == tmp_path / "eye_abcd1234.json"


def test_require_raises_the_gate_naming_the_file(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    with pytest.raises(Escalation) as got:
        ev.require(tmp_path / "storyboard", pics, "EYE", "look", home=tmp_path)
    assert got.value.gate == "EYE"
    assert got.value.verdict == f"storyboard/eye_{ev.fingerprint(pics)}.json"


def test_sign_makes_the_verdict_current_and_require_returns_it(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    out = ev.sign(tmp_path / "storyboard", pics, "pass", "every panel on its cell")
    assert out.exists() and ev.current(tmp_path / "storyboard", pics)["verdict"] == "pass"
    assert ev.passed(tmp_path / "storyboard", pics)
    assert ev.require(tmp_path / "storyboard", pics, "EYE", "look")["note"] == "every panel on its cell"


def test_a_changed_picture_makes_the_verdict_stale(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    ev.sign(tmp_path / "storyboard", pics, "pass", "fine")
    pics = _pictures(tmp_path / "storyboard", salt=b"redrawn")
    assert ev.current(tmp_path / "storyboard", pics) is None
    with pytest.raises(Escalation):
        ev.require(tmp_path / "storyboard", pics, "EYE", "look")


def test_a_fault_verdict_is_a_refusal_not_a_signature(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    ev.sign(tmp_path / "storyboard", pics, "fault", "two hats on one man in shot 2")
    assert not ev.passed(tmp_path / "storyboard", pics)
    with pytest.raises(SystemExit, match="two hats"):
        ev.require(tmp_path / "storyboard", pics, "EYE", "look")


def test_sign_refuses_an_unknown_verdict_and_an_empty_note(tmp_path):
    pics = _pictures(tmp_path / "storyboard")
    with pytest.raises(SystemExit, match="pass"):
        ev.sign(tmp_path / "storyboard", pics, "maybe", "hm")
    with pytest.raises(SystemExit, match="note"):
        ev.sign(tmp_path / "storyboard", pics, "pass", "   ")
