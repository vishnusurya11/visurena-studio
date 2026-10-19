"""One room per setup: a setup's grids are chained on its ANCHOR.

Five-agent debate 2026-09-28 (docs/audit/2026-09-28_grid_place_constancy_plan.md):
a place is held by pixels, not words.  Within one render the room holds;
between renders of one setup the drawer re-dresses it (ep14: two biology
classrooms, a mirrored Waterloo, an attic that became a street).  So:

- the ANCHOR grid of a setup is the grid holding its widest shot, drawn first;
- its widest cell is cut to storyboard/anchors/<setup>.png -- the ROOM;
- every other grid of the setup stages the room as a reference ("this exact
  room, already drawn") and NOT the plate: the room IS the place, so two people
  keep their slots (Jekyll ep01 audit 2026-10-15, 01_staged_refs 3.2; grids.py no
  longer calls `stages_plate`);
- the grid manifest's `inputs` hash covers the staged bytes, so a redrawn
  anchor makes every sibling stale and they follow it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from studio.storyboard_grid import panel_box, seam_box

RANK = ("wide", "full", "medium", "medium_close", "close", "extreme_close", "insert")
"""Widest first: the anchor is the lowest rank, then the lowest index."""
PLATE_SIZES = ("wide", "full")
"""A chained grid stages the place picture beside the room only for these."""
ANCHORS = Path("storyboard") / "anchors"
SIDE = 1024


def _get(shot, key: str):
    return shot.get(key) if isinstance(shot, dict) else getattr(shot, key, None)


def anchor_shot(shots, setup: str) -> int | None:
    """The setup's widest shot (ties: the earliest), or None for no shots."""
    own = [s for s in shots if _get(s, "setup") == setup]
    if not own:
        return None
    return int(_get(min(own, key=lambda s: (rank(_get(s, "size")), int(_get(s, "index")))), "index"))


def rank(size) -> int:
    """Widest first; a size the ladder does not know sorts last."""
    return RANK.index(size) if size in RANK else len(RANK)


def anchor_row(rows: list[dict], anchor: int | None) -> dict | None:
    return next((r for r in rows if anchor in (r.get("shots") or [])), None) if anchor is not None else None


def is_anchor(indices: list[int], anchor: int | None) -> bool:
    return anchor is not None and anchor in indices


def room_path(home: Path, setup: str) -> Path:
    return Path(home) / ANCHORS / f"{setup}.png"


def room_for(home: Path, setup: str, indices: list[int], anchor: int | None) -> Path | None:
    """The room a grid stages: none for the anchor grid itself, none before it is cut."""
    if is_anchor(indices, anchor):
        return None
    path = room_path(home, setup)
    return path if path.exists() else None


def stages_plate(shots) -> bool:
    return any(_get(s, "size") in PLATE_SIZES for s in shots)


def draw_order(rows: list[dict], shots) -> list[dict]:
    """Each setup's anchor grid before its siblings; setups keep their order."""
    out = []
    for setup in dict.fromkeys(r.get("setup") for r in rows):
        own = [r for r in rows if r.get("setup") == setup]
        lead = anchor_row(own, anchor_shot(shots, setup))
        out += ([lead] if lead else []) + [r for r in own if r is not lead]
    return out


def siblings(rows: list[dict], row: dict, shots) -> list[dict]:
    """The other grids of `row`'s setup when `row` is its anchor; else none."""
    own = [r for r in rows if r.get("setup") == row.get("setup")]
    if len(own) < 2 or anchor_row(own, anchor_shot(shots, row.get("setup"))) is not row:
        return []
    return [r for r in own if r is not row]


def room_stale(home: Path, setup: str, grid: Path) -> bool:
    """The room is missing or older than the anchor grid it is cut from."""
    room = room_path(home, setup)
    return not room.exists() or room.stat().st_mtime < Path(grid).stat().st_mtime


def cut_room(grid: Path, row: dict, anchor: int, out: Path) -> Path:
    """The anchor's cell, shaved of its gutter and cropped square, at panel size."""
    image = Image.open(grid).convert("RGB")
    panel = image.crop(panel_box(row["shots"].index(anchor), row["cols"], row["rows"], image.size))
    panel = panel.crop(seam_box(np.asarray(panel)))
    w, h = panel.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.crop((left, top, left + side, top + side)).resize((SIDE, SIDE), Image.LANCZOS).save(out)
    return out


PLACE_FLOOR = 0.5
"""How well a re-cut room's background must agree with the old room's (studio.measure.place
`prof_same` and `wings_same`) for the place to count as the same.  ep06's same-place wides
measured +0.63..+0.84; a mirror or a re-dressed room reads below zero."""


def same_place(new: Path, old: Path) -> bool:
    """The re-cut room is the old room's place: agreeing backgrounds, and not its mirror."""
    from studio.measure import place
    read = place.versus(place.load(new), place.load(old))
    return min(read["prof_same"], read["wings_same"]) >= PLACE_FLOOR and not place.mirrored(read)


def recut_room(grid: Path, row: dict, anchor: int, out: Path) -> bool:
    """Re-cut the room from the (repaired) anchor cell.  A place that matches the old room keeps
    the OLD bytes -- touched fresh -- so the siblings' manifests, which hash them, stay valid
    (Jekyll ep01 2026-10-18: one repaired cell restaged grids 13-17).  Else the new room
    replaces it and the siblings follow.  True when the old room was kept."""
    out = Path(out)
    candidate = cut_room(grid, row, anchor, out.with_name(f"{out.stem}.recut.png"))
    kept = out.exists() and same_place(candidate, out)
    if kept:
        candidate.unlink()
        out.touch()
    else:
        candidate.replace(out)
    return kept
