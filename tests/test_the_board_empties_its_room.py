"""Step 07 cuts a setup's room and empties it with the local one-image edit, read back by the panel
reader (Jekyll ep06, 2026-10-29).  The GPU edit and the reader are faked: no test renders."""
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from scripts.episode import step_07_board as s7
from studio import grid_room as gr

ROW = {"setup": "doorstep", "cols": 1, "rows": 1, "shots": [27], "tag": "b"}
SHOTS = [{"index": 27, "setup": "doorstep", "size": "full"}, {"index": 26, "setup": "doorstep", "size": "close"}]


def ctx_at(tmp_path: Path) -> SimpleNamespace:
    logs = []
    ctx = SimpleNamespace(home=tmp_path, number=6, logs=logs,
                          log=lambda msg, **kw: logs.append((msg, kw.get("level"))))
    grid = s7.grid_path(ctx, ROW)
    grid.parent.mkdir(parents=True)
    Image.new("RGB", (1024, 1024), (40, 50, 90)).save(grid)
    return ctx


def fake_edit(prompt, source, target, seed):
    Image.new("RGB", (1024, 1024), (seed, 9, 9)).save(target)


def test_the_cut_room_is_emptied_and_recorded(tmp_path, monkeypatch):
    ctx = ctx_at(tmp_path)
    monkeypatch.setattr(s7, "edit_room", fake_edit)
    monkeypatch.setattr(s7, "people_in", lambda path: 0)
    s7.cut_room(ctx, ROW, SHOTS)
    assert gr.emptied(gr.room_path(tmp_path, "doorstep")) and not ctx.logs


def test_a_room_left_with_people_is_logged(tmp_path, monkeypatch):
    ctx = ctx_at(tmp_path)
    monkeypatch.setattr(s7, "edit_room", fake_edit)
    monkeypatch.setattr(s7, "people_in", lambda path: 1)
    s7.cut_room(ctx, ROW, SHOTS)
    assert not gr.emptied(gr.room_path(tmp_path, "doorstep"))
    assert ctx.logs and ctx.logs[0][1] == "WARNING" and "people left" in ctx.logs[0][0]


def test_people_are_counted_by_the_panel_reader(monkeypatch):
    import panel_content_check
    monkeypatch.setattr(panel_content_check, "read", lambda path: SimpleNamespace(people=3))
    assert s7.people_in(Path("x.png")) == 3


def test_the_edit_is_the_book_pictures_one_image_edit(tmp_path, monkeypatch):
    from studio import comfy
    seen = {}
    out = tmp_path / "out.png"
    out.write_bytes(b"edited")
    monkeypatch.setattr(comfy, "stage_image", lambda p: "staged.png")
    monkeypatch.setattr(comfy, "run", lambda wf, values: seen.update(wf=wf, **values) or [out])
    s7.edit_room("empty it", tmp_path / "src.png", tmp_path / "t.png", 1)
    assert seen["wf"] == "image_qwen_image_edit_2511_single_image" and seen["seed"] == 1
    assert (tmp_path / "t.png").read_bytes() == b"edited"
