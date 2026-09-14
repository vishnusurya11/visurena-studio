"""The publisher looks for the master in the room the master is in.

`youtube_publish.deliverable` built `home / "master_r2v.mp4"`, and masters moved
to `home/cut/` in the layout change.  The QC report stayed at the episode root,
so the pair came apart: episode 4's `qc_r2v.json` said `passed: true` about
sha8 1899e22c and the publisher answered

    no master in ...\ep04 has a QC that passed (none found)

which reads as "the cut is bad".  It is the twelfth reader that change broke,
and like most of them it failed by finding nothing rather than by raising.
"""
import json
from pathlib import Path

import pytest

from studio import youtube_publish as yp


def episode(tmp_path: Path, passed: bool = True) -> Path:
    (tmp_path / "cut").mkdir(parents=True)
    (tmp_path / "cut" / "master_r2v.mp4").write_bytes(b"x")
    (tmp_path / "qc_r2v.json").write_text(json.dumps({"passed": passed, "sha8": "1899e22c"}),
                                          encoding="utf-8")
    return tmp_path


def test_the_master_is_found_in_the_cut_room(tmp_path):
    engine, master, qc = yp.deliverable(episode(tmp_path))
    assert engine == "r2v"
    assert master == tmp_path / "cut" / "master_r2v.mp4"
    assert qc == tmp_path / "qc_r2v.json"


def test_a_failed_qc_is_still_refused(tmp_path):
    with pytest.raises(SystemExit, match="QC that passed"):
        yp.deliverable(episode(tmp_path, passed=False))


def test_naming_the_engine_finds_it_too(tmp_path):
    _, master, _ = yp.deliverable(episode(tmp_path), "r2v")
    assert master == tmp_path / "cut" / "master_r2v.mp4"


def test_a_master_left_in_the_episode_root_is_not_the_deliverable(tmp_path):
    """A stale copy in the old place must not be published instead."""
    home = episode(tmp_path)
    (home / "master_r2v.mp4").write_bytes(b"old")
    _, master, _ = yp.deliverable(home)
    assert master.parent.name == "cut"


def test_two_engines_that_both_passed_still_refuse(tmp_path):
    home = episode(tmp_path)
    (home / "cut" / "master.mp4").write_bytes(b"x")
    (home / "qc.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    with pytest.raises(SystemExit, match="name one with"):
        yp.deliverable(home)
