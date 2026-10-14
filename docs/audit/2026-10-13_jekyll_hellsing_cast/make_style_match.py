"""style_match.jpg: the chain test's HEL refs + ch1 panel (top) beside the same pictures drawn by the
pipeline's own drawer (book_look.t2i on the book's refs/look.json) and grids.py (bottom).

    uv run python docs/audit/2026-10-13_jekyll_hellsing_cast/make_style_match.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
CHAIN = HERE.parent / "2026-10-13_jekyll_anime_chain" / "HEL"
MATCH = HERE / "match"
COLS = ["Hyde", "Jekyll", "Utterson", "ch1 corner (place master)", "ch1 Qwen panel"]
ROWS = [("chain HEL (target)", [CHAIN / n for n in ("hyde.png", "jekyll.png", "utterson.png", "corner.png", "panel_a.png")]),
        ("pipeline, fixed", [MATCH / n for n in ("edward_hyde_s105.png", "henry_jekyll_s201.png",
                                                                  "gabriel_john_utterson_s301.png", "corner_s401.png",
                                                                  "panel_a.png")])]
H, GAP, LABEL, LEFT = 520, 8, 30, 230
BG, FG, ACCENT = (15, 16, 18), (225, 225, 225), (200, 160, 90)


def font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def fit(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGB")
    return im.resize((round(im.width * H / im.height), H))


def main() -> None:
    rows = [(name, [fit(p) for p in paths]) for name, paths in ROWS]
    widths = [max(r[1][i].width for r in rows) for i in range(len(COLS))]
    W = LEFT + sum(widths) + GAP * len(COLS)
    sheet = Image.new("RGB", (W, 50 + len(rows) * (H + LABEL + GAP)), BG)
    d = ImageDraw.Draw(sheet)
    d.text((10, 12), "Jekyll HEL style match: chain test (top) vs the pipeline drawer after the fix (bottom)",
           fill=FG, font=font(22))
    for r, (name, ims) in enumerate(rows):
        y = 50 + r * (H + LABEL + GAP)
        d.text((10, y + 10), name, fill=ACCENT, font=font(18))
        x = LEFT
        for i, im in enumerate(ims):
            sheet.paste(im, (x + (widths[i] - im.width) // 2, y))
            d.text((x + 4, y + H + 5), COLS[i], fill=FG, font=font(16))
            x += widths[i] + GAP
    dest = HERE / "style_match.jpg"
    sheet.save(dest, quality=90)
    print(dest)


if __name__ == "__main__":
    main()
