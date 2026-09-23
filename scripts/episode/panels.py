#!/usr/bin/env python
"""Cut an episode's grids into ONE PANEL PER SHOT, where the takes read them.

    uv run python scripts/episode/panels.py <book_id> <episode>

Reads every grid manifest under episodes/epNN/storyboard/grids/ (written by
`grids.py` after each render) and writes, per shot:
  storyboard/shot_NN.png      at 1024, for a person to look at
  storyboard/h3/shot_NN.png   at H3 ref2va's native 768, which takes_r2v stages

Promoted from a session driver (audit 2026-09-22, items 9, 12, 22). On the way in:
- WHICH GRID EACH SHOT COMES FROM IS THE GRIDS' OWN ACCOUNT, read from the
  episode folder. The first exporter carried a typed list of grid names and cut
  28 panels out of a previous plan's grids; the session driver read manifests
  from a session folder and globbed ComfyUI's shared output for the picture.
- Every shot of the plan is covered exactly once: a shot in two manifests is a
  superseded grid nobody removed, a shot in none is a grid nobody drew, and a
  grid drawn from an older plan is refused.
- The crop sheds the gutter it measures (`seam_box`), not a guessed 16 px.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from PIL import Image

from grids import grids_dir, plan_sha, shots_sha
from studio import episode_home
from studio.episode_home import episode_arg
from studio.storyboard_grid import panel_box, seam_box

NATIVE = 768


def manifests(book: Path, number: int) -> list[dict]:
    """Every grid filed for this episode, by its own account of itself."""
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(grids_dir(book, number).glob("*.json"))]


def owner_of(rows: list[dict], wanted: list[int]) -> dict[int, tuple[dict, int]]:
    """{shot: (grid, slot)}, refusing a shot drawn by two grids or by none."""
    seen: dict[int, list[tuple[dict, int]]] = {}
    for row in rows:
        for slot, shot in enumerate(row["shots"]):
            seen.setdefault(shot, []).append((row, slot))
    if twice := {s: [r["name"] for r, _ in v] for s, v in seen.items() if len(v) > 1}:
        raise SystemExit(f"shots drawn by two grids -- remove the superseded one: {twice}")
    if missing := [s for s in wanted if s not in seen]:
        raise SystemExit(f"shots no grid holds: {missing}")
    return {s: v[0] for s, v in seen.items() if s in wanted}


def stale_grids(rows: list[dict], current: str, ep=None) -> list[str]:
    """Grids whose own shots changed since they were drawn. A manifest with no
    `drawn_from` (before 2026-09-23) falls back to the whole plan's hash."""
    def stale(r: dict) -> bool:
        if ep is not None and "drawn_from" in r:
            return r["drawn_from"] != shots_sha(ep, r["shots"])
        return r.get("plan") != current
    return [r["name"] for r in rows if stale(r)]


def save_if_changed(img: Image.Image, out: Path) -> bool:
    """Write the panel only when its pixels differ from the file on disk. A
    re-cut of unchanged grids rewrote all 23 ep09 panels, and the takes then
    refused every verdict as older than its picture."""
    if out.exists():
        with Image.open(out) as old:
            if old.size == img.size and np.array_equal(np.asarray(old.convert("RGB")), np.asarray(img)):
                return False
    img.save(out)
    return True


def cut(grid: Image.Image, row: dict, slot: int) -> Image.Image:
    """One panel out of its grid, less the gutter the fixed trim left behind."""
    panel = grid.crop(panel_box(slot, row["cols"], row["rows"], grid.size))
    return panel.crop(seam_box(np.asarray(panel)))


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    rows = manifests(book, number)
    if old := stale_grids(rows, plan_sha(book, number), ep):
        raise SystemExit(f"grids drawn from an older plan -- redraw them: {old}")
    owner = owner_of(rows, [s.index for s in ep.shots])
    out = episode_home.home(book, number) / "storyboard"
    (out / "h3").mkdir(parents=True, exist_ok=True)
    for shot in ep.shots:
        row, slot = owner[shot.index]
        panel = cut(Image.open(grids_dir(book, number) / f"{row['name']}.png").convert("RGB"), row, slot)
        save_if_changed(panel.resize((1024, 1024), Image.LANCZOS), out / f"shot_{shot.index:02d}.png")
        save_if_changed(panel.resize((NATIVE, NATIVE), Image.LANCZOS), out / "h3" / f"shot_{shot.index:02d}.png")
        print(f"  shot {shot.index:02d}  <- {row['name']} slot {slot}", flush=True)
    print(f"{len(ep.shots)} panels -> {episode_home.relative(book, out)}")


if __name__ == "__main__":
    main(sys.argv[1], episode_arg(sys.argv))
