"""A repaired anchor re-cuts the room and keeps its siblings when the place is the same.

Jekyll ep01 (2026-10-18): redrawing one anchor cell re-cut the setup room; `room_stale` compares
mtime and the room's bytes enter the sibling manifests' `inputs`, so grids 13-17 were redrawn
though the repair changed a figure and not the place.  Now the new room is cut from the repaired
cell, measured against the old with studio.measure.place; a matching place keeps the old bytes
(touched fresh) so every sibling manifest still holds; a changed place replaces them as before.
The old room is never staged into the anchor's redraw (`room_for` is None for the anchor).
"""
import hashlib
import os
from pathlib import Path

import numpy as np
from PIL import Image

from studio import grid_room as gr

ROW = {"setup": "attic", "cols": 1, "rows": 1, "shots": [2]}
SHOTS = [{"index": 2, "setup": "attic", "size": "wide"}, {"index": 3, "setup": "attic", "size": "close"}]


def place(seed: int, figure: int = 60) -> Image.Image:
    """A banded room with a window on one side; `figure` is the person in the centre."""
    rng = np.random.default_rng(seed)
    a = np.zeros((1024, 1024, 3), dtype=np.uint8)
    a[:, :, :] = (np.linspace(40, 200, 1024)[None, :, None] * (1 + 0.4 * (seed % 3))).clip(0, 255)
    a[:512, 100:300] = 250
    a[:, :] = (a + rng.integers(0, 4, a.shape)).clip(0, 255)
    a[400:1000, 440:580] = figure
    return Image.fromarray(a)


def drawn(path: Path, im: Image.Image) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def old_room(tmp_path) -> Path:
    grid = drawn(tmp_path / "g0.png", place(1))
    return gr.cut_room(grid, ROW, 2, gr.room_path(tmp_path, "attic"))


def test_the_same_place_keeps_the_old_room_bytes_and_stays_fresh(tmp_path):
    room = old_room(tmp_path)
    before = sha(room)
    repaired = drawn(tmp_path / "g1.png", place(1, figure=200))       # only the figure changed
    os.utime(room, (room.stat().st_atime, room.stat().st_mtime - 100))     # the repair is newer
    assert gr.room_stale(tmp_path, "attic", repaired)
    assert gr.recut_room(repaired, ROW, 2, room) is True
    assert sha(room) == before and not gr.room_stale(tmp_path, "attic", repaired)


def test_a_changed_place_replaces_the_room_and_the_siblings_follow(tmp_path):
    room = old_room(tmp_path)
    before = sha(room)
    changed = drawn(tmp_path / "g2.png", place(7).transpose(Image.FLIP_LEFT_RIGHT))
    assert gr.recut_room(changed, ROW, 2, room) is False
    assert sha(room) != before


def test_the_room_is_always_cut_from_the_post_repair_cell(tmp_path):
    room = gr.room_path(tmp_path, "attic")
    first = drawn(tmp_path / "g3.png", place(3))
    assert gr.recut_room(first, ROW, 2, room) is False               # no old room: cut as today
    assert sha(room) == sha(gr.cut_room(first, ROW, 2, tmp_path / "ref.png"))


def test_no_candidate_file_is_left_behind(tmp_path):
    room = old_room(tmp_path)
    gr.recut_room(drawn(tmp_path / "g4.png", place(1, figure=200)), ROW, 2, room)
    assert sorted(p.name for p in room.parent.iterdir()) == ["attic.png"]


def test_the_anchor_grid_never_stages_the_old_room(tmp_path):
    old_room(tmp_path)
    assert gr.room_for(tmp_path, "attic", [2], 2) is None


def test_a_kept_room_leaves_the_sibling_inputs_unchanged(tmp_path):
    """The sibling manifest hashes the staged room bytes (panels.drawn_inputs)."""
    room = old_room(tmp_path)
    inputs = sha(room)
    gr.recut_room(drawn(tmp_path / "g5.png", place(1, figure=200)), ROW, 2, room)
    assert sha(room) == inputs


def test_the_place_floor_reads_a_mirror_as_another_place(tmp_path):
    a = drawn(tmp_path / "a.png", place(1))
    assert gr.same_place(a, a) and not gr.same_place(drawn(tmp_path / "m.png", place(1).transpose(Image.FLIP_LEFT_RIGHT)), a)
