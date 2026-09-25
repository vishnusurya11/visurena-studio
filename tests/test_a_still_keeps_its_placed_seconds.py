"""A still in the cut is the panel held for exactly its shot's PLACED seconds
with a slow push -- the same `-t` a take's segment would get -- so the picture
stays on the measured voice.  assemble reads stills.json beside the takes and
never opens that shot's take file."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import assemble
from studio import episode_home
from studio.trailer_assemble import frames_arg


def test_the_still_segment_is_the_panel_for_its_seconds_with_a_push(tmp_path):
    calls = []
    panel = tmp_path / "shot_02.png"
    panel.write_bytes(b"png")
    out = assemble.still_segment(panel, 5.0, tmp_path / "seg02.mp4", 768, 768, 24,
                                 ffmpeg=lambda cmd, check: calls.append(cmd))
    cmd = calls[0]
    assert out == tmp_path / "seg02.mp4" and cmd[-1] == str(out)
    assert cmd[cmd.index("-t") + 1] == frames_arg(5.0, 24)
    assert cmd[cmd.index("-frames:v") + 1] == "120"
    assert "zoompan" in cmd[cmd.index("-vf") + 1] and "-an" in cmd
    assert cmd[cmd.index("-i") + 1] == str(panel)


def test_the_cut_takes_the_still_for_its_placed_seconds_and_leaves_the_take(tmp_path, monkeypatch):
    book = tmp_path / "book"
    home = book / "episodes" / "ep05"
    room = home / "takes" / "r2v"
    (home / "storyboard").mkdir(parents=True)
    (home / "storyboard" / "shot_02.png").write_bytes(b"png")
    episode_home.write_json(room / "stills.json",
                            {"2": {"panel": "episodes/ep05/storyboard/shot_02.png", "seconds": 5.0, "why": "content"}})
    takes = {1: assemble.TakePath(room / "T01.mp4", [1]), 2: assemble.TakePath(room / "T02.mp4", [2])}
    placed = {"shots": [{"index": 1, "seconds": 4.0}, {"index": 2, "seconds": 5.0}], "lines": []}
    cut, stilled, opened = [], [], []
    monkeypatch.setattr(assemble, "guard", lambda take, seconds, work: "")
    monkeypatch.setattr(assemble, "clip_seconds", lambda p: opened.append(p) or 4.0)
    monkeypatch.setattr(assemble, "extract", lambda v, start, seconds, out, *a, **k: cut.append((v, seconds)) or out)
    monkeypatch.setattr(assemble, "still_segment",
                        lambda panel, seconds, out, *a, **k: stilled.append((panel, seconds)) or out)
    monkeypatch.setattr(assemble, "concat", lambda segs, out: out)
    work = tmp_path / "work"
    work.mkdir()
    assemble.picture(placed, takes, work, stills=assemble.stills_of(room, book))
    assert cut == [(takes[1], 4.0)]
    assert stilled == [(home / "storyboard" / "shot_02.png", 5.0)]
    assert opened == [takes[1]]                       # the still's take is never opened
    assert json.loads((work / "gutter.json").read_text(encoding="utf-8")) == {}


def test_stills_json_is_read_by_index_and_absent_means_none(tmp_path):
    room = tmp_path / "takes" / "r2v"
    assert assemble.stills_of(room, tmp_path) == {}
    episode_home.write_json(room / "stills.json", {"7": {"panel": "episodes/ep01/storyboard/shot_07.png", "seconds": 3.0}})
    assert assemble.stills_of(room, tmp_path) == {7: tmp_path / "episodes" / "ep01" / "storyboard" / "shot_07.png"}
