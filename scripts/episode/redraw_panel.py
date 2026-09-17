#!/usr/bin/env python
"""Redraw ONE storyboard cell, under its own sheet's laws.

    uv run python scripts/episode/redraw_panel.py <codex_id> <episode> Q14_1 --approved

A sheet costs $0.20 and redraws every panel on it, including the ones that came
back right; one panel costs $0.08 and touches only the picture that was wrong
(owner, 2026-09-11, on S14.1: "legs are small, proportions are off").  The
replacement carries the sheet's location, geometry and wardrobe blocks, so it
still belongs beside its neighbours.  PAID, and it refuses without `--approved`.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib.util as _iu

from studio import approval, canvas, episode_home, episode_seq_board as sq, house_style
from studio.episode_spec import Episode, Setup

SIZE = (1024, 1536)
"""The 9:16 default. A square plan draws a square cell instead: `panel_size()`."""


def panel_size(aspect: str) -> tuple[int, int]:
    """One cell's paid canvas at the plan's own aspect."""
    width, height = canvas.still_size(aspect).split("x")
    return int(width), int(height)
USD = 0.08


def _sibling(name: str):
    spec = _iu.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = _iu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find(episode: Episode, key: str) -> tuple[str, dict]:
    """The setup name and the drawable panel a key like 'S14.1' or 'S05.0E' names.

    A trailing E is that segment's END cell.  `sq.segments` yields start cells
    only, so the END panel is derived from its own start panel -- which is also
    the picture it will be drawn from."""
    index, sub, end = sq.end_key(key)
    shot = next(s for s in episode.shots if s.index == index)
    segs = sq.segments(episode.shots, shot.setup)
    panel = next(s for s in segs if (s["shot"], s["sub"]) == (index, sub))
    return shot.setup, (sq.end_panel(panel, segs.index(panel) + 1) if end else panel)


def prompt_for(episode: Episode, panel: dict, setup: Setup, physical: dict) -> str:
    """The one panel's prompt, under ITS EPISODE'S place and light.

    MEASURED on episode 10: all four `boards/panels/*.prompt.txt` say "1881
    London, gaslight from one side" over Ferrier's Utah farm in 1860.
    `seq_boards.main` adopts the plan's place before it builds a sheet; this
    script never did, so `sq.single()` printed the book's default -- the ep08
    bug in a third module.  A repair drawn under another sky is not a repair."""
    house_style.adopt(episode.where, episode.light)
    end = bool(panel.get("end"))
    return (sq.end_single if end else sq.single)(panel, setup, physical, episode.aspect)


def main(book_id: str, number: int, key: str, approved: bool) -> None:
    sb = _sibling("storyboard")
    boards = _sibling("seq_boards")
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    root = episode_home.boards_dir(book, number)
    name, panel = find(episode, key)
    setup = episode.setups[name]
    cell = sq.cell_path(root, panel["shot"], panel["sub"], panel.get("end", False))
    end = bool(panel.get("end"))
    text = prompt_for(episode, panel, setup, boards.physicals(book))
    approval.require("panel", f"one gpt-image still to replace {cell.name} ({key}, {name})", USD, approved)
    # An END cell is drawn FROM ITS OWN START CELL: measured, 9 of episode 2's 13
    # END cells were re-staged to a different camera when asked for in prose alone.
    # It goes in FIRST because `end_single` numbers it Image 1 and shifts the rest.
    refs = [sq.cell_path(root, panel["shot"], panel["sub"])] if end else []
    refs += [sq.plate_path(root, name)]
    refs += [sq.plate_path(root, p) for p in setup.props if p != name]
    # `setup.state` IS the wardrobe selector, and dropping it silently picks a
    # DIFFERENT card than the sheet this panel is repairing: measured 2026-09-13,
    # the hall sheet referenced `char-john_watson_indoor.png` while this $0.08
    # redraw of one of its panels referenced `char-john_watson_bench.png` -- the
    # same man with a bowler in his hand, in an episode whose prose says
    # "bare-headed" throughout.  A repair that changes the wardrobe is not a repair.
    refs += [sq.cast_sheet(book, who, name, setup.state) for who in setup.cast]
    panels = sq.panels_in(root)
    panels.mkdir(parents=True, exist_ok=True)
    out = panels / f"panel_{cell.stem}.png"
    out.unlink(missing_ok=True)
    sb.adopt(episode.aspect)   # the cell is cropped to the PLAN's canvas, not a module default
    drawn = sb.draw(text, [r for r in refs if r.exists()], out,
                    panel_size(episode.aspect), approved=True)
    # the draft goes to `panels/`, not beside the cells: a superseded `.before.png`
    # sitting in `cells/` was read as another shot's picture and cost episode 3
    # ten of its eighteen foreign-frame flags.
    cell.replace(panels / f"{cell.stem}.before.png")
    sb.conform(drawn, cell)
    (panels / f"{cell.stem}.prompt.txt").write_text(text, encoding="utf-8")
    print(f"{key} redrawn -> {cell} (the old one kept as {cell.stem}.before.png)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], int(args[1]), args[2], approval.approved_for("panel", sys.argv))
