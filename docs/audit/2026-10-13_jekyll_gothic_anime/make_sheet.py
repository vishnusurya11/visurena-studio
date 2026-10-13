"""Gothic anime styles sheet: one row per style (Hyde, Jekyll, ch1 scene) on the Studio dark #0f1012.

uv run python docs/audit/2026-10-13_jekyll_gothic_anime/make_sheet.py OUT.jpg STYLE [STYLE ...]
Each row is labelled with the style's name, its reference anime and its recipe (base + LoRA).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
COLUMNS = [("hyde", "Hyde"), ("jekyll", "Jekyll"), ("ch1", "ch1: Hyde over the fallen child")]
ROWS = {  # style -> (name, reference anime, recipe)
    "VHD": ("Bloodlust gothic", "Vampire Hunter D: Bloodlust (2000, Madhouse)", "WAI-Illustrious v14 + Kawajiri XL 0.45"),
    "KAW": ("Kawajiri OVA noir", "Wicked City (1987) / Ninja Scroll (1993)", "WAI-Illustrious v14 + Kawajiri XL 0.9"),
    "HEL": ("Hellsing ink-red", "Hellsing Ultimate (2006-12, Satelight/Madhouse)", "WAI-Illustrious v14, tags only"),
    "BER": ("Berserk '97 retro cel", "Kenpuu Denki Berserk (1997, OLM)", "WAI-Illustrious v14, tags only"),
    "KUR": ("Black Butler Victorian", "Kuroshitsuji (2008, A-1 Pictures)", "WAI-Illustrious v14, tags only"),
    "CAS": ("Kojima baroque", "Castlevania (Netflix) / Ayami Kojima art", "WAI-Illustrious v14 + Kojima Pony 0.8"),
    "MON": ("Mononoke washi", "Mononoke (2007, Toei)", "WAI-Illustrious v14, tags only"),
    "AMA": ("Amano watercolour", "Yoshitaka Amano's VHD illustrations", "WAI-Illustrious v14, tags only"),
}
CELL, PAD, LEFT, TOP = 560, 14, 380, 64
BG, INK, DIM, ACC = (15, 16, 18), (232, 232, 232), (150, 150, 150), (196, 160, 96)


def font(px: int):
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", px)


def wrap(text: str, width: int, draw: ImageDraw.ImageDraw, face) -> list[str]:
    """Greedy word wrap of text to a pixel width."""
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=face) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def draw_label(draw: ImageDraw.ImageDraw, style: str, index: int, y: int) -> None:
    """The row's number + style name, reference anime and recipe, in the left column."""
    name, anime, recipe = ROWS[style]
    ty = y + 150
    draw.text((PAD + 4, ty), f"{index}. {name}", font=font(30), fill=INK)
    ty += 52
    for part, face, colour in ((anime, font(20), ACC), (recipe, font(17), DIM)):
        for line in wrap(part, LEFT - 3 * PAD, draw, face):
            draw.text((PAD + 4, ty), line, font=face, fill=colour)
            ty += face.size + 8
        ty += 10


def main() -> None:
    out, styles = sys.argv[1], sys.argv[2:]
    width = LEFT + len(COLUMNS) * (CELL + PAD)
    sheet = Image.new("RGB", (width, TOP + len(styles) * (CELL + PAD) + PAD), BG)
    draw = ImageDraw.Draw(sheet)
    for j, (_, label) in enumerate(COLUMNS):
        draw.text((LEFT + j * (CELL + PAD) + CELL // 2, TOP // 2), label, font=font(24), fill=INK, anchor="mm")
    for i, style in enumerate(styles):
        y = TOP + i * (CELL + PAD)
        draw_label(draw, style, i + 1, y)
        for j, (subject, _) in enumerate(COLUMNS):
            pic = Image.open(HERE / style / f"{subject}.png").convert("RGB").resize((CELL, CELL), Image.LANCZOS)
            sheet.paste(pic, (LEFT + j * (CELL + PAD), y))
    sheet.save(HERE / out, quality=88)
    print(HERE / out)


if __name__ == "__main__":
    main()
