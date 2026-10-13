"""Hyde-only gothic anime styles sheet: one cell per style, labelled underneath, on the Studio dark #0f1012.

uv run python docs/audit/2026-10-13_jekyll_gothic_anime/sheet_hyde.py OUT.jpg STYLE[=file.png] [STYLE ...]
Each cell shows <STYLE>/hyde.png (or the named file) with the style name, reference anime and recipe under it.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LABELS = {  # style -> (name, reference anime, recipe)
    "VHD": ("Bloodlust gothic", "Vampire Hunter D: Bloodlust (2000, Madhouse)", "NoobAI-XL 1.1 + Kawajiri XL 0.45"),
    "HEL": ("Hellsing ink-red", "Hellsing Ultimate (2006-12)", "NoobAI-XL 1.1, tags only"),
    "BER": ("Berserk '97 retro cel", "Kenpuu Denki Berserk (1997, OLM)", "NoobAI-XL 1.1, tags only"),
    "KUR": ("Black Butler Victorian", "Kuroshitsuji (2008, A-1 Pictures)", "NoobAI-XL 1.1, tags only"),
    "MOR": ("Moriarty Victorian", "Moriarty the Patriot (2020, Production I.G)", "NoobAI-XL 1.1, tags only"),
    "MON": ("Mononoke washi", "Mononoke (2007, Toei)", "NoobAI-XL 1.1 + Mononoke IL LoRA 0.6"),
    "CAS": ("Kojima baroque", "Castlevania (Netflix) / Ayami Kojima", "NoobAI-XL 1.1 + Kojima Pony 0.8"),
    "KAW": ("Kawajiri OVA noir", "Wicked City (1987) / Ninja Scroll (1993)", "NoobAI-XL 1.1 + Kawajiri XL 0.9"),
    "GAN": ("Gankutsuou textile", "Gankutsuou (2004, Gonzo)", "NoobAI-XL 1.1, tags only"),
    "DN": ("Death Note Obata", "Death Note (2006, Madhouse)", "NoobAI-XL 1.1, tags only"),
    "ITO": ("Junji Ito ink horror", "Junji Ito manga / Uzumaki (2024)", "NoobAI-XL 1.1, tags only"),
    "PAN": ("Pandora Hearts gothic", "Pandora Hearts (2009, Xebec)", "NoobAI-XL 1.1, tags only"),
    "AMA": ("Amano watercolour", "Yoshitaka Amano's VHD illustrations", "NoobAI-XL 1.1, tags only"),
    "DGM": ("D.Gray-man gothic", "D.Gray-man (2006, TMS)", "NoobAI-XL 1.1, tags only"),
    "TRI": ("Trigun Stampede 3D cel", "Trigun Stampede (2023, Orange)", "NoobAI-XL 1.1, tags only"),
}
CELL, PAD, LABEL_H, COLS = 512, 16, 118, 5
BG, INK, DIM, ACC = (15, 16, 18), (232, 232, 232), (150, 150, 150), (196, 160, 96)


def font(px: int):
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", px)


def parse(arg: str) -> tuple[str, Path]:
    """STYLE or STYLE=file.png -> (style, image path)."""
    style, _, name = arg.partition("=")
    return style, HERE / style / (name or "hyde.png")


def draw_cell(sheet: Image.Image, draw: ImageDraw.ImageDraw, index: int, style: str, path: Path) -> None:
    """Paste one style's Hyde at its grid slot and write its three label lines under it."""
    x = PAD + (index % COLS) * (CELL + PAD)
    y = PAD + (index // COLS) * (CELL + LABEL_H + PAD)
    sheet.paste(Image.open(path).convert("RGB").resize((CELL, CELL), Image.LANCZOS), (x, y))
    name, anime, recipe = LABELS[style]
    draw.text((x, y + CELL + 8), f"{index + 1}. {name}", font=font(28), fill=INK)
    draw.text((x, y + CELL + 48), anime, font=font(19), fill=ACC)
    draw.text((x, y + CELL + 78), recipe, font=font(17), fill=DIM)


def main() -> None:
    out, cells = sys.argv[1], [parse(a) for a in sys.argv[2:]]
    rows = (len(cells) + COLS - 1) // COLS
    size = (PAD + COLS * (CELL + PAD), PAD + rows * (CELL + LABEL_H + PAD))
    sheet = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(sheet)
    for i, (style, path) in enumerate(cells):
        draw_cell(sheet, draw, i, style, path)
    sheet.save(HERE / out, quality=88)
    print(HERE / out)


if __name__ == "__main__":
    main()
