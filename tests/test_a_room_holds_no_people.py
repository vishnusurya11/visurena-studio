"""A setup's room is emptied of people before any sibling stages it (Jekyll ep06, 2026-10-29).

The doorstep room was cut from anchor panel 27, which held the butler small in the doorway and three
passers-by.  Every sibling grid staged it: panel 23 drew a second, tiny butler behind the real one and
the passers-by (3 figures for 2, so its take went refs-only from a warm place picture -- the style
jump), and take 27 faded the doorway butler into a ghost.  So the cut room gets one local edit that
removes every figure, read back by the panel reader until it counts none (EMPTY_TRIES seeds), and its
sidecar records what is left.  Only an emptied room is kept across an anchor repair."""
import json
from pathlib import Path

from PIL import Image

from studio import grid_room as gr

ROW = {"setup": "doorstep", "cols": 1, "rows": 1, "shots": [27]}


def cut(tmp_path: Path) -> Path:
    grid = tmp_path / "g.png"
    Image.new("RGB", (1024, 1024), (40, 50, 90)).save(grid)
    return gr.cut_room(grid, ROW, 27, gr.room_path(tmp_path, "doorstep"))


def editor(calls: list):
    def edit(prompt: str, source: Path, target: Path, seed: int) -> None:
        calls.append((prompt, Path(source).name, seed))
        Image.new("RGB", (1024, 1024), (seed, 0, 0)).save(target)
    return edit


def test_the_room_is_edited_from_its_peopled_cut_until_none_is_counted(tmp_path):
    room, calls, reads = cut(tmp_path), [], iter([2, 0])
    left = gr.empty_room(room, editor(calls), lambda p: next(reads))
    assert left == 0 and [c[2] for c in calls] == [0, 1]
    assert all(c[1] == "doorstep.peopled.png" for c in calls) and "Change only" in calls[0][0]
    assert sorted(p.name for p in room.parent.iterdir()) == ["doorstep.png"]


def test_a_room_still_peopled_after_every_try_says_how_many_are_left(tmp_path):
    room, calls = cut(tmp_path), []
    assert gr.empty_room(room, editor(calls), lambda p: 1) == 1
    assert len(calls) == gr.EMPTY_TRIES


def test_the_sidecar_records_the_people_left(tmp_path):
    room = cut(tmp_path)
    assert gr.emptied(room) is False                         # no record: a room cut before the rule
    gr.note_people(room, 0)
    assert json.loads(gr.record_path(room).read_text())["people_left"] == 0 and gr.emptied(room)
    gr.note_people(room, 2)
    assert gr.emptied(room) is False


def test_an_unemptied_old_room_is_replaced_even_when_the_place_matches(tmp_path, monkeypatch):
    room = cut(tmp_path)
    monkeypatch.setattr(gr, "same_place", lambda new, old: True)
    grid = tmp_path / "g2.png"
    Image.new("RGB", (1024, 1024), (40, 50, 90)).save(grid)
    kept = gr.recut_room(grid, ROW, 27, room, empty=lambda p: 0)
    assert kept is False and gr.emptied(room)


def test_an_emptied_old_room_of_the_same_place_is_kept(tmp_path, monkeypatch):
    room = cut(tmp_path)
    gr.note_people(room, 0)
    monkeypatch.setattr(gr, "same_place", lambda new, old: True)
    before = room.read_bytes()
    assert gr.recut_room(tmp_path / "g.png", ROW, 27, room, empty=lambda p: 0) is True
    assert room.read_bytes() == before
    assert sorted(p.name for p in room.parent.iterdir()) == ["doorstep.json", "doorstep.png"]
