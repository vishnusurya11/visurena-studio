"""One contact sheet of every storyboard panel, each stamped with its shot number.

The panel eye looks at ONE picture, not thirty files: `storyboard/contact.png`,
a grid of `shot_NN.png` in shot order with the number drawn in the corner so a
fault can be named by shot.  Free, CPU, PIL only.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

COLS, CELL = 6, 256
NUMBER = re.compile(r"(\d+)")


def shot_number(panel: Path) -> int:
    """The shot a panel is named for: the first number in `shot_NN.png`."""
    found = NUMBER.search(Path(panel).stem)
    return int(found.group(1)) if found else 0


def fitted(image, cell: int):
    """The panel scaled to fit a square cell, aspect kept."""
    scale = cell / max(image.width, image.height)
    return image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))))


def sheet(panels: list[Path], cols: int = COLS, cell: int = CELL):
    """The panels on a cols x ceil(n / cols) grid, numbered."""
    from PIL import Image, ImageDraw

    rows = max(1, math.ceil(len(panels) / cols))
    out = Image.new("RGB", (cols * cell, rows * cell), (24, 24, 24))
    draw = ImageDraw.Draw(out)
    for i, panel in enumerate(panels):
        image = fitted(Image.open(panel).convert("RGB"), cell)
        x, y = (i % cols) * cell, (i // cols) * cell
        out.paste(image, (x + (cell - image.width) // 2, y + (cell - image.height) // 2))
        draw.text((x + 4, y + 4), str(shot_number(panel)), fill=(255, 255, 0))
    return out


def write(panels: list[Path], dest: Path, cols: int = COLS, cell: int = CELL) -> Path:
    """The contact sheet on disk; refuses an empty list (nothing to look at)."""
    if not panels:
        raise SystemExit("no panels to lay out")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet(sorted(panels, key=shot_number), cols, cell).save(dest)
    return dest
