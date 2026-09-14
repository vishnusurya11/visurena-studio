"""The take's own storyboard strip as the continuity reference.

The 3x3 sheet gives continuity (same room, light, wardrobe) but also hands
the model every face on the sheet; measured 2026-09-10, the "second
Stamford" in a from-behind take was the sheet's own frontal cell.  A strip of
the panels around the take carries the same family of light and wardrobe
while showing only what the take itself shows next door.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

GUTTER = 24


def neighbours(run: list[int], first: int, last: int) -> list[int]:
    """The panel before the run, the run, the panel after it (within the episode)."""
    lo, hi = max(run[0] - 1, first), min(run[-1] + 1, last)
    return list(range(lo, hi + 1))


def compose(panels: list[Image.Image], height: int = 1024) -> Image.Image:
    tiles = [p.resize((round(p.width * height / p.height), height)) for p in panels]
    width = sum(t.width for t in tiles) + GUTTER * (len(tiles) - 1)
    out = Image.new("RGB", (width, height), "white")
    x = 0
    for t in tiles:
        out.paste(t, (x, 0))
        x += t.width + GUTTER
    return out


def strip_for(cells: Path, run: list[int], first: int, last: int, out: Path) -> Path:
    panels = [Image.open(cells / f"S{i:02d}.png").convert("RGB") for i in neighbours(run, first, last)]
    compose(panels).save(out)
    return out
