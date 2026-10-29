"""A board drawn from an older plan is not done (ep13, 2026-09-26).

The plan was edited after its grids were drawn (the hedge's hills became a tree
line, the pit a shallow crater); step 07 printed 'skipped: output exists' and
panels.py then refused with 'grids drawn from an older plan'.  Existence is not
currency: the step asks the same question panels.py asks, and redraws."""
from __future__ import annotations

from types import SimpleNamespace as NS

from scripts.episode import step_07_board as board


def ctx_for(tmp_path, monkeypatch, rows, stale):
    ctx = NS(home=tmp_path, number=13, book_dir=tmp_path, extra=[], ran=[])
    ctx.run_script = lambda script, *argv, **kw: ctx.ran.append(argv)
    monkeypatch.setattr(board, "layout", lambda c: rows)
    monkeypatch.setattr(board, "stale_names", lambda c: set(stale))
    monkeypatch.setattr(board.grid_layout, "write", lambda home, rows: None)
    monkeypatch.setattr(board.grid_layout, "argv", lambda row: [row["tag"]])
    monkeypatch.setattr(board.grid_layout, "name_of", lambda number, row: row["tag"])
    for row in rows:
        path = board.grid_path(ctx, row)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"png")
    return ctx


def test_a_stale_grid_is_not_done_and_is_redrawn(tmp_path, monkeypatch):
    rows = [{"tag": "hedge"}, {"tag": "pit"}]
    ctx = ctx_for(tmp_path, monkeypatch, rows, stale=["hedge"])
    assert board.done(ctx) is False
    board.run(ctx)
    assert ctx.ran == [("hedge",)]


def test_current_grids_are_done(tmp_path, monkeypatch):
    ctx = ctx_for(tmp_path, monkeypatch, [{"tag": "hedge"}], stale=[])
    assert board.done(ctx) is True


def rendered_ctx(tmp_path, monkeypatch, ordered):
    rows = [{"tag": "doorstep"}, {"tag": "dining"}]
    ctx = ctx_for(tmp_path, monkeypatch, rows, stale=["doorstep"])
    (tmp_path / "takes" / "r2v").mkdir(parents=True)
    (tmp_path / "takes" / "r2v" / "T00.mp4").write_bytes(b"take")
    ctx.log = lambda *a, **k: None
    monkeypatch.setattr(board, "owner_ordered", lambda c: ordered)
    monkeypatch.setattr(board.boundary, "check", lambda *a, **k: None)
    return ctx


def test_under_rendered_takes_a_stale_grid_is_left_without_an_order(tmp_path, monkeypatch):
    ctx = rendered_ctx(tmp_path, monkeypatch, ordered=False)
    board.run(ctx)
    assert ctx.ran == []


def test_an_owner_redo_redraws_the_stale_grids_under_rendered_takes(tmp_path, monkeypatch):
    """Jekyll ep06 (2026-10-29): Poole was redrawn and step 07 redone by an owner order; the guard
    against a prompt-builder change walking a resume into redraws returned at once, and seven takes
    re-rendered from his old picture.  An owner's redo is the order to redraw what is stale."""
    ctx = rendered_ctx(tmp_path, monkeypatch, ordered=True)
    board.run(ctx)
    assert ctx.ran == [("doorstep",)]
