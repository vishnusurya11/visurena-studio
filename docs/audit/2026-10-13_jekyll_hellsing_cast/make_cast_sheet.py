"""Contact sheet of Jekyll's Hellsing base sheets (+ ep01 place masters), labelled.

    uv run python docs/audit/2026-10-13_jekyll_hellsing_cast/make_cast_sheet.py [out.jpg]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
BOOK = ROOT / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde" / "refs"
PLACES = ["london_sunday_walks/wide_establishing", "london_sunday_walks/lamplit_cross_street",
          "black_mail_house_door/wide_establishing", "black_mail_house_door/court_entry_pavement",
          "black_mail_house_door/wide_establishing__night_at_four_in_the_morning_the_kerb_gas_lamp_l"]
W, H = 300, 438


def tile(path: Path, label: str, size) -> Image.Image:
    im = Image.open(path).convert("RGB")
    im.thumbnail(size)
    out = Image.new("RGB", (size[0], size[1] + 24), (15, 16, 18))
    out.paste(im, ((size[0] - im.width) // 2, 0))
    ImageDraw.Draw(out).text((6, size[1] + 5), label[:48], fill=(230, 230, 230))
    return out


def main(dest: Path) -> None:
    people = sorted(p for p in (BOOK / "characters").glob("*/sheet.png"))
    tiles = [tile(p, p.parent.name, (W, H)) for p in people]
    places = [tile(BOOK / "locations" / f"{k}.png", k.split("__")[0] + (" (night)" if "__" in k else ""), (450, 300))
              for k in PLACES if (BOOK / "locations" / f"{k}.png").exists()]
    cols = 8
    rows = -(-len(tiles) // cols)
    sheet = Image.new("RGB", (cols * W, rows * (H + 24) + (324 if places else 0)), (15, 16, 18))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * W, (i // cols) * (H + 24)))
    for i, t in enumerate(places):
        sheet.paste(t, (i * 480, rows * (H + 24)))
    sheet.save(dest, quality=90)
    print(dest)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("cast_sheet.jpg"))
