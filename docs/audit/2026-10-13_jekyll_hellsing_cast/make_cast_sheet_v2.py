"""cast_sheet_v2.jpg: Jekyll's 15 base sheets and ep01's place pictures in the approved HEL look, each beside
the flat sheet it superseded (refs/.../superseded/*_2026-10-13_hellsing_flat.png), labelled.

    uv run python docs/audit/2026-10-13_jekyll_hellsing_cast/make_cast_sheet_v2.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REFS = HERE.parents[2] / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde" / "refs"
TAG = "2026-10-13_hellsing_flat"
PLACES = ["london_sunday_walks/wide_establishing", "london_sunday_walks/lamplit_cross_street",
          "black_mail_house_door/wide_establishing", "black_mail_house_door/court_entry_pavement",
          "black_mail_house_door/wide_establishing__night_at_four_in_the_morning_the_kerb_gas_lamp_l"]
NEW_H, OLD_H, LABEL, PAD, COLS = 440, 200, 24, 10, 5
BG, FG, DIM = (15, 16, 18), (230, 230, 230), (140, 140, 140)


def font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def scaled(path: Path, h: int) -> Image.Image:
    im = Image.open(path).convert("RGB")
    return im.resize((round(im.width * h / im.height), h))


def pair(new: Path, label: str) -> Image.Image:
    """The new picture large, the superseded one small at its lower left, the label under both."""
    old = new.parent / "superseded" / f"{new.stem}_{TAG}{new.suffix}"
    a = scaled(new, NEW_H)
    b = scaled(old, OLD_H) if old.exists() else None
    w = a.width + (b.width + 6 if b else 0)
    tile = Image.new("RGB", (w, NEW_H + LABEL), BG)
    d = ImageDraw.Draw(tile)
    if b:
        tile.paste(b, (0, NEW_H - OLD_H))
        d.text((2, NEW_H - OLD_H - 16), "old", fill=DIM, font=font(13))
    tile.paste(a, (w - a.width, 0))
    d.text((2, NEW_H + 4), label, fill=FG, font=font(15))
    return tile


def grid(tiles: list[Image.Image], cols: int) -> Image.Image:
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    W = max(sum(t.width for t in r) + PAD * (len(r) - 1) for r in rows)
    out = Image.new("RGB", (W, len(rows) * (NEW_H + LABEL + PAD)), BG)
    for y, r in enumerate(rows):
        x = 0
        for t in r:
            out.paste(t, (x, y * (NEW_H + LABEL + PAD)))
            x += t.width + PAD
    return out


def main() -> None:
    people = [pair(p, p.parent.name) for p in sorted((REFS / "characters").glob("*/sheet.png"))]
    places = [pair(REFS / "locations" / f"{k}.png", k.split("__")[0] + (" (night, one edit)" if "__" in k else ""))
              for k in PLACES if (REFS / "locations" / f"{k}.png").exists()]
    top, bottom = grid(people, COLS), grid(places, 2)
    sheet = Image.new("RGB", (max(top.width, bottom.width), 50 + top.height + 30 + bottom.height), BG)
    d = ImageDraw.Draw(sheet)
    d.text((10, 12), "Jekyll and Hyde, Hellsing (chain-test HEL look): 15 base sheets + ep01 places, new (large) "
           "beside the flat sheet it supersedes (old, small)", fill=FG, font=font(22))
    sheet.paste(top, (0, 50))
    sheet.paste(bottom, (0, 50 + top.height + 30))
    dest = HERE / "cast_sheet_v2.jpg"
    sheet.save(dest, quality=88)
    print(dest)


if __name__ == "__main__":
    main()
