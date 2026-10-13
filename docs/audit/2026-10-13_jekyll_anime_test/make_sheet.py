"""Style A (photoreal) over anime gothic, the same six subjects, on the Studio dark (#0f1012).

uv run python docs/audit/2026-10-13_jekyll_anime_test/make_sheet.py RECIPE [RECIPE2]
Writes compare_sheet.jpg beside this file. Row A is the 2026-10-11 look test (cast, door) and the
2026-10-12 samples (two scenes); each further row is one anime recipe folder here.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
A_CELLS = {"1_jekyll": AUDIT / "2026-10-11_jekyll_look_test/A/1_jekyll.png",
           "2_hyde": AUDIT / "2026-10-11_jekyll_look_test/A/2_hyde.png",
           "3_utterson": AUDIT / "2026-10-11_jekyll_look_test/A/3_utterson.png",
           "4_door": AUDIT / "2026-10-11_jekyll_look_test/A/4_door.png",
           "2_trampling": AUDIT / "2026-10-12_jekyll_style_samples/A/2_trampling.png",
           "4_carew": AUDIT / "2026-10-12_jekyll_style_samples/A/4_carew.png"}
LABELS = ["Jekyll", "Hyde", "Utterson", "The door street", "ch1 Hyde and the child", "ch4 the cane in fog"]
ROWS = {"A": ("A. Photoreal gothic", "Krea2 turbo, no LoRA (chosen 2026-10-12)"),
        "Q21": ("Anime gothic", "Qwen-Image 2.1, words only"),
        "DG": ("Anime gothic", "Qwen-Image + DarkGhibli LoRA"),
        "NU": ("Anime gothic", "Qwen-Image + Urasawa LoRA"),
        "MA": ("Anime gothic", "Qwen-Image + MysticAnime LoRA"),
        "K2": ("Anime gothic", "Krea2 turbo, words only")}
CELL, PAD, LEFT, TOP = 520, 14, 300, 60
BG, INK, DIM = (15, 16, 18), (230, 230, 230), (150, 150, 150)


def font(px: int):
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", px)


def cells(row: str) -> list[Path]:
    """The six picture paths of one row, in LABELS order."""
    return list(A_CELLS.values()) if row == "A" else [HERE / row / f"{n}.png" for n in A_CELLS]


def draw_row(sheet: Image.Image, draw: ImageDraw.ImageDraw, row: str, y: int) -> None:
    """Paste one row's six cells at height y with its two-line label on the left."""
    title, recipe = ROWS[row]
    draw.text((PAD, y + CELL // 2 - 20), title, font=font(26), fill=INK, anchor="lm")
    draw.text((PAD, y + CELL // 2 + 18), recipe, font=font(16), fill=DIM, anchor="lm")
    for j, path in enumerate(cells(row)):
        pic = Image.open(path).convert("RGB").resize((CELL, CELL), Image.LANCZOS)
        sheet.paste(pic, (LEFT + j * (CELL + PAD), y))


def main() -> None:
    rows = ["A", *sys.argv[1:]]
    width = LEFT + len(LABELS) * (CELL + PAD) + PAD
    sheet = Image.new("RGB", (width, TOP + len(rows) * (CELL + PAD) + PAD), BG)
    draw = ImageDraw.Draw(sheet)
    for j, label in enumerate(LABELS):
        draw.text((LEFT + j * (CELL + PAD) + CELL // 2, TOP // 2), label, font=font(24), fill=INK, anchor="mm")
    for i, row in enumerate(rows):
        draw_row(sheet, draw, row, TOP + i * (CELL + PAD))
    sheet.save(HERE / "compare_sheet.jpg", quality=88)


if __name__ == "__main__":
    main()
