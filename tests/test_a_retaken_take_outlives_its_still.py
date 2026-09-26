"""A still is the terminal rung's answer for a take that could not pass.  When
the take is rendered again AFTER that answer, the answer is about a take that
no longer exists.  ep12: stills.json held T19 at 07:09, T19 was retaken at
08:03 and passed, and the cut kept holding the panel -- QC then failed the
edit, comparing the panel's push against the passing take."""
from __future__ import annotations

import os
import time

from scripts.episode import assemble
from studio import episode_home, take_ladder


def _room(tmp_path):
    room = tmp_path / "episodes" / "ep05" / "takes" / "r2v"
    room.mkdir(parents=True)
    return room


def test_a_take_rendered_after_its_still_row_drops_the_still(tmp_path):
    room = _room(tmp_path)
    (room / "T07.mp4").write_bytes(b"take")
    episode_home.write_json(room / "stills.json",
                            {"7": {"panel": "episodes/ep05/storyboard/shot_07.png", "seconds": 3.0,
                                   "decided": time.time() - 3600}})
    assert assemble.stills_of(room, tmp_path) == {}


def test_a_take_older_than_its_still_row_keeps_the_still(tmp_path):
    room = _room(tmp_path)
    take = room / "T07.mp4"
    take.write_bytes(b"take")
    os.utime(take, (time.time() - 7200, time.time() - 7200))
    episode_home.write_json(room / "stills.json",
                            {"7": {"panel": "episodes/ep05/storyboard/shot_07.png", "seconds": 3.0,
                                   "decided": time.time() - 3600}})
    assert list(assemble.stills_of(room, tmp_path)) == [7]


def test_a_row_without_a_stamp_is_dated_by_the_file(tmp_path):
    room = _room(tmp_path)
    episode_home.write_json(room / "stills.json",
                            {"7": {"panel": "episodes/ep05/storyboard/shot_07.png", "seconds": 3.0}})
    past = time.time() - 3600
    os.utime(room / "stills.json", (past, past))
    (room / "T07.mp4").write_bytes(b"take")
    assert assemble.stills_of(room, tmp_path) == {}


def test_write_still_stamps_when_the_still_was_decided(tmp_path):
    home = tmp_path / "episodes" / "ep05"
    panel = home / "storyboard" / "shot_07.png"
    panel.parent.mkdir(parents=True)
    panel.write_bytes(b"png")
    before = time.time()
    take_ladder.write_still(home, 7, panel, 3.0, "content")
    row = take_ladder.load_stills(home)[7]
    assert row["decided"] >= before - 1.0
