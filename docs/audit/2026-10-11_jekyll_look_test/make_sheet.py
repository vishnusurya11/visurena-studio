"""3 styles x 4 subjects on the Studio dark (#0f1012): style_sheet.jpg beside this file."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
STYLES = [("A", "A. Photoreal gothic (Krea2, no LoRA)"), ("B", "B. WotW painterly (cinematic 2x neutral tile)"),
          ("C", "C. Dark ink gothic (Krea2 + darkbrush LoRA)")]
SUBJECTS = [("1_jekyll", "Jekyll"), ("2_hyde", "Hyde"), ("3_utterson", "Utterson"), ("4_door", "The door (ch1)")]
CELL, PAD, LEFT, TOP = 720, 16, 300, 70
BG, INK = (15, 16, 18), (230, 230, 230)


def font(px: int):
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", px)


def main() -> None:
    w = LEFT + len(SUBJECTS) * (CELL + PAD) + PAD
    h = TOP + len(STYLES) * (CELL + PAD) + PAD
    sheet = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(sheet)
    for j, (_, label) in enumerate(SUBJECTS):
        draw.text((LEFT + j * (CELL + PAD) + CELL // 2, TOP // 2), label, font=font(34), fill=INK, anchor="mm")
    for i, (style, label) in enumerate(STYLES):
        y = TOP + i * (CELL + PAD)
        words = label.split(" (")
        draw.text((PAD, y + CELL // 2 - 30), words[0], font=font(30), fill=INK, anchor="lm")
        draw.text((PAD, y + CELL // 2 + 20), "(" + words[1], font=font(19), fill=(160, 160, 160), anchor="lm")
        for j, (name, _) in enumerate(SUBJECTS):
            pic = Image.open(HERE / style / f"{name}.png").convert("RGB").resize((CELL, CELL), Image.LANCZOS)
            sheet.paste(pic, (LEFT + j * (CELL + PAD), y))
    sheet.save(HERE / "style_sheet.jpg", quality=90)


if __name__ == "__main__":
    main()
