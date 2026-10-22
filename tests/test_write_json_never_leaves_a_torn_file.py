"""A3 (fleet E, 2026-10-22): write_json writes a temp file beside the target, then os.replace.

Bench I1: write_text left 548 of 1,000 killed writes unreadable; temp + os.replace left 0, every
file exactly old or new.  A write that fails mid-stream must leave the old file whole.  A reader
holding the file (the :8700 board, the lane's polls) makes Windows refuse the replace
(WinError 5: 280 of 500 replaces under a tight reader failed four tries, build/a3_result.json),
so a held file is retried, then written in place as before: a write is never lost."""
from __future__ import annotations

import json

from studio import episode_home


def test_a_write_that_fails_mid_stream_leaves_the_old_file_whole(tmp_path):
    path = episode_home.write_json(tmp_path / "plan.json", {"shots": [1, 2, 3]})
    try:
        episode_home.write_json(path, {"shots": ["x" * 20000, "\ud800"]})   # unencodable: raises mid-write
    except UnicodeEncodeError:
        pass
    assert json.loads(path.read_text(encoding="utf-8")) == {"shots": [1, 2, 3]}


def test_no_temp_file_is_left_beside_the_target(tmp_path):
    episode_home.write_json(tmp_path / "a.json", {"x": 1})
    try:
        episode_home.write_json(tmp_path / "a.json", {"x": "\ud800"})
    except UnicodeEncodeError:
        pass
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.json"]


def test_a_file_a_reader_holds_open_still_gets_the_new_content(tmp_path):
    path = episode_home.write_json(tmp_path / "board.json", {"v": 1})
    with open(path, encoding="utf-8"):                  # held: no delete sharing on Windows
        episode_home.write_json(path, {"v": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"v": 2}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["board.json"]
