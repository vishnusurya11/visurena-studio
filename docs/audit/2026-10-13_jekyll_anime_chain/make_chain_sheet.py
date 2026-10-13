"""chain_sheet.jpg: per style and shot, sheet(s) | place | panel | take frames at 0/25/50/75/100 %.

    uv run python docs/audit/2026-10-13_jekyll_anime_chain/make_chain_sheet.py [OUT.jpg] [--panel NAME]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROWS = [("VHD", "a"), ("VHD", "b"), ("HEL", "a"), ("HEL", "b")]
STYLE = {"VHD": "1. Bloodlust", "HEL": "2. Hellsing"}
SHOT = {"a": "a. ch1 trampling", "b": "b. ch3 fireside, l25"}
SHEETS = {"a": ["hyde"], "b": ["jekyll", "utterson"]}
PLACE = {"a": "corner", "b": "study"}
S, GAP, LABEL, SHEETW, HEAD = 300, 10, 330, 420, 60
BG, FG, DIM = (15, 16, 18), (235, 235, 235), (200, 170, 110)


def font(size: int):
    for name in ("segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit(path: Path, w: int, h: int) -> Image.Image:
    im = Image.open(path).convert("RGB")
    im.thumbnail((w, h))
    return im


def row_cells(style: str, shot: str, panel: str) -> list[tuple[str, Image.Image]]:
    folder = HERE / style
    sheets = Image.new("RGB", (SHEETW, S), BG)
    x = 0
    for who in SHEETS[shot]:
        im = fit(folder / f"{who}.png", SHEETW // len(SHEETS[shot]) - 4, S)
        sheets.paste(im, (x + (SHEETW // len(SHEETS[shot]) - im.width) // 2, 0))
        x += SHEETW // len(SHEETS[shot])
    cells = [("sheet" + ("s" if len(SHEETS[shot]) > 1 else ""), sheets),
             ("place master", fit(folder / f"{PLACE[shot]}.png", S, S)),
             ("Qwen panel", fit(folder / f"{panel}_{shot}.png", S, S))]
    cells += [(f"H3 take {p}%", fit(folder / f"take_{shot}_f{p:03d}.png", S, S)) for p in (0, 25, 50, 75, 100)]
    return cells


def main(out: Path, panel: str = "panel") -> None:
    rows = [(st, sh, row_cells(st, sh, panel)) for st, sh in ROWS]
    width = LABEL + SHEETW + 7 * (S + GAP) + GAP * 2
    height = HEAD + len(rows) * (S + 34 + GAP) + GAP
    sheet = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(sheet)
    d.text((GAP, 14), "Jekyll anime chain: NoobAI refs -> Qwen-Image 2.1 panel (grids.py v2) -> MiniMax-H3 ref2va take "
           "(takes_r2v BASE, CRF 10, 768x768, 124 f)", fill=FG, font=font(26))
    y = HEAD
    for style, shot, cells in rows:
        d.text((GAP, y + 20), STYLE[style], fill=DIM, font=font(20))
        d.text((GAP, y + 80), SHOT[shot], fill=FG, font=font(18))
        x = LABEL
        for label, im in cells:
            w = SHEETW if label.startswith("sheet") else S
            sheet.paste(im, (x + (w - im.width) // 2, y + (S - im.height) // 2))
            d.text((x + 4, y + S + 4), label, fill=FG, font=font(18))
            x += w + GAP
        y += S + 34 + GAP
    sheet.save(out, quality=90)
    print(out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    panel = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--panel=")), "panel")
    main(Path(args[0]) if args else HERE / "chain_sheet.jpg", panel)
