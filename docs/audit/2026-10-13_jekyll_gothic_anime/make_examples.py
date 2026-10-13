"""Examples sheets for the owner's five shortlisted gothic anime looks, on the Studio dark #0f1012.

uv run python docs/audit/2026-10-13_jekyll_gothic_anime/make_examples.py STYLE   -> examples_<n>_<name>.jpg (2 x 3)
uv run python docs/audit/2026-10-13_jekyll_gothic_anime/make_examples.py overview -> examples_overview.jpg
The kept file per style x picture is in picks.json (the seed's reroll salt is in its name: _sb, _sc ...).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PICTURES = [("ex_hyde", "Hyde"), ("ex_jekyll", "Jekyll"), ("ex_utterson", "Utterson"),
            ("ex_trample", "ch1: Hyde strides over the fallen girl"), ("ex_door", "ch1: Utterson and Enfield pass the door"),
            ("ex_study", "ch3: Jekyll and Utterson by the fire")]
STYLES = {  # style -> (owner's number, file name, label, reference, recipe)
    "HEL": (2, "hellsing", "Hellsing ink-red", "Hellsing Ultimate (2006-12)", "NoobAI-XL 1.1, tags only"),
    "VHD": (1, "bloodlust", "Bloodlust gothic", "Vampire Hunter D: Bloodlust (2000, Madhouse)", "NoobAI-XL 1.1 + Kawajiri XL 0.45"),
    "MON": (6, "mononoke", "Mononoke washi", "Mononoke (2007, Toei)", "NoobAI-XL 1.1 + Mononoke IL LoRA 0.6"),
    "AMA": (13, "amano", "Amano watercolour", "Yoshitaka Amano's VHD illustrations", "NoobAI-XL 1.1, tags only"),
    "TRI": (15, "trigun_stampede", "Trigun Stampede 3D cel", "Trigun Stampede (2023, Orange)", "NoobAI-XL 1.1, tags only"),
}
CELL, PAD, HEAD, CAP = 600, 14, 70, 40
BG, INK, DIM, ACC = (15, 16, 18), (232, 232, 232), (150, 150, 150), (196, 160, 96)


def font(px: int):
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", px)


def picks() -> dict:
    return json.loads((HERE / "picks.json").read_text(encoding="utf-8"))


def cell(draw: ImageDraw.ImageDraw, sheet: Image.Image, style: str, subject: str, label: str, x: int, y: int) -> None:
    """One picture at (x, y) with its caption under it."""
    pic = Image.open(HERE / style / picks()[style][subject]).convert("RGB").resize((CELL, CELL), Image.LANCZOS)
    sheet.paste(pic, (x, y))
    draw.text((x + CELL // 2, y + CELL + CAP // 2), label, font=font(20), fill=INK, anchor="mm")


def style_sheet(style: str) -> Path:
    """2 rows x 3 of one style's six pictures under a header naming the look."""
    n, slug, name, ref, recipe = STYLES[style]
    width = PAD + 3 * (CELL + PAD)
    sheet = Image.new("RGB", (width, HEAD + 2 * (CELL + CAP + PAD) + PAD), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD + 4, HEAD // 2), f"{n}. {name}", font=font(32), fill=INK, anchor="lm")
    draw.text((width - PAD - 4, HEAD // 2), f"{ref}  |  {recipe}", font=font(20), fill=ACC, anchor="rm")
    for k, (subject, label) in enumerate(PICTURES):
        cell(draw, sheet, style, subject, label, PAD + (k % 3) * (CELL + PAD), HEAD + (k // 3) * (CELL + CAP + PAD))
    out = HERE / f"examples_{n}_{slug}.jpg"
    sheet.save(out, quality=88)
    return out


def overview() -> Path:
    """The five styles as rows: Hyde, Jekyll and the ch1 trampling."""
    cols, left = [PICTURES[0], PICTURES[1], PICTURES[3]], 330
    sheet = Image.new("RGB", (left + 3 * (CELL + PAD), PAD + len(STYLES) * (CELL + CAP + PAD)), BG)
    draw = ImageDraw.Draw(sheet)
    for i, (style, (n, _, name, ref, recipe)) in enumerate(STYLES.items()):
        y = PAD + i * (CELL + CAP + PAD)
        draw.text((PAD + 4, y + 220), f"{n}. {name}", font=font(28), fill=INK)
        draw.text((PAD + 4, y + 270), ref[:34], font=font(18), fill=ACC)
        draw.text((PAD + 4, y + 300), recipe, font=font(16), fill=DIM)
        for j, (subject, label) in enumerate(cols):
            cell(draw, sheet, style, subject, label, left + j * (CELL + PAD), y)
    out = HERE / "examples_overview.jpg"
    sheet.save(out, quality=86)
    return out


if __name__ == "__main__":
    print(overview() if sys.argv[1] == "overview" else style_sheet(sys.argv[1]))
