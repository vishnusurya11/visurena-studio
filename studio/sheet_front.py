"""One figure of a character sheet, for the storyboard grids.

ep16 (2026-10-02): every grid that staged a four-pose turnaround sheet drew the
character up to four times, and a prompt line saying "exactly once" changed
nothing.  The grid is shown the sheet's FIRST figure only: the first run of
figure columns on the sheet's flat backdrop.  A sheet whose first figure
cannot be separated (overlapping poses) yields None, and the grid draws that
person from their wardrobe words.  Takes keep the whole sheet.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

GAP_STD = 15.0
"""Luma spread down a column under which the column is backdrop.  MEASURED on
miss_elphinstone's sheet: backdrop edge 4, gaps between figures 9-11, figures
30-70.  The backdrop's vignette defeats a corner-colour distance test."""
SMOOTH = 9
"""Columns averaged so one dark whip lash does not bridge a gap."""
BAND = (0.10, 0.60)
"""Rows scanned: floor shadows fill every column near the feet."""
GAP_MIN = 0.015
"""A backdrop run narrower than this share of the sheet is a dip inside one
figure (the brother's plain suit), never the gap between two."""
MIN_WIDTH = 0.04
"""A figure run narrower than this share of the sheet is a stray mark."""
MAX_SHARE = 0.45
"""A first 'figure' wider than this share is several overlapping poses."""
MARGIN = 0.02
"""Backdrop kept either side of the figure, as a share of the sheet width."""


def runs(filled: np.ndarray, gap: int) -> list[tuple[int, int]]:
    """(start, end) column runs of figure, bridging backdrop runs under `gap`."""
    out, start, last = [], None, None
    for x, on in enumerate(filled):
        if on:
            if start is None:
                start = x
            elif last is not None and x - last - 1 >= gap:
                out.append((start, last + 1))
                start = x
            last = x
    if start is not None:
        out.append((start, last + 1))
    return out


def first_figure_box(a: np.ndarray) -> tuple[int, int] | None:
    """(left, right) columns of the first figure, margin included; None when
    no single figure can be separated."""
    h, w = a.shape[:2]
    band = a[int(h * BAND[0]):int(h * BAND[1])].astype(float).mean(axis=2)
    spread = np.convolve(band.std(axis=0), np.ones(SMOOTH) / SMOOTH, mode="same")
    for start, end in runs(spread > GAP_STD, int(GAP_MIN * w)):
        if end - start < MIN_WIDTH * w:
            continue
        if end - start > MAX_SHARE * w:
            return None
        pad = int(MARGIN * w)
        return max(0, start - pad), min(w, end + pad)
    return None


def front_of(sheet: Path) -> Path | None:
    """sheet_front.png beside the sheet (rebuilt when the sheet is newer), or
    None when the sheet's first figure cannot be separated."""
    sheet = Path(sheet)
    out = sheet.with_name("sheet_front.png")
    if out.exists() and out.stat().st_mtime >= sheet.stat().st_mtime:
        return out
    a = np.asarray(Image.open(sheet).convert("RGB"))
    box = first_figure_box(a)
    if box is None:
        return None
    Image.fromarray(a[:, box[0]:box[1]]).save(out)
    return out
