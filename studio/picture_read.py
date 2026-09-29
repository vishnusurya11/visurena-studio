"""The picture read: what FIXED things stand where in a place picture.

Cells are written FROM the drawn picture, never before it (the skill's own
rule, inverted by the 02 plan -> 03 places order on 2026-09-24; ruled back by
the owner 2026-09-28).  The local vision model lists the room's fixed things
in a closed vocabulary -- which third, which band, near or far, how big -- and
code writes the cells from that list (studio/cells_from_picture).  The model
never judges; it names, like every other reader in the line.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

X = ("LEFT", "CENTRE", "RIGHT")
Y = ("TOP", "MIDDLE", "BOTTOM")
DEPTH = ("near", "far")
SIZE = ("fills", "large", "small")
MOST = 8
WORKFLOW = "image_qwen3vl_caption"
SEED = 11
ASK = ("List the FIXED things in this picture -- walls, furniture, windows, doors, lamps, trees, "
       "roads, buildings, machines, water -- never a person or an animal. Output strict JSON: a "
       f"list of at most {MOST} objects, each with these keys and nothing else: "
       '"thing": a short plain noun phrase; "x": one of LEFT, CENTRE, RIGHT (where it stands across '
       'the frame); "y": one of TOP, MIDDLE, BOTTOM (its band down the frame); "depth": one of near, '
       'far; "size": one of fills, large, small. Order them from the largest to the smallest.')


def parse(text: str) -> list[dict]:
    """The rows in the closed vocabulary; anything else is dropped, not guessed."""
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        rows = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []
    return [row for row in (_row(r) for r in rows if isinstance(r, dict)) if row][:MOST]


def _row(r: dict) -> dict | None:
    thing = re.sub(r"\s+", " ", str(r.get("thing") or "")).strip().lower()
    x, y = str(r.get("x") or "").upper(), str(r.get("y") or "").upper()
    if not thing or x not in X or y not in Y:
        return None
    depth = str(r.get("depth") or "far").lower()
    size = str(r.get("size") or "large").lower()
    return {"thing": thing, "x": x, "y": y, "depth": depth if depth in DEPTH else "far",
            "size": size if size in SIZE else "large"}


def readable(text: str) -> bool:
    return bool(parse(text))


def read(path: Path, run: Callable[[Path], str] | None = None) -> list[dict]:
    """The picture's fixed things, through `run` (the local VLM by default)."""
    return parse((run or _vision)(Path(path)))


def _vision(path: Path) -> str:
    from studio import comfy
    return comfy.cached_text(WORKFLOW, {"image_1": comfy.stage_image(path), "prompt": ASK, "seed": SEED}, readable)
