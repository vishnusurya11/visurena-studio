"""Style A x 6 scenes on the Studio dark (#0f1012): samples_sheet.jpg beside this file."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SCENES = [("1_door_walk", "1. ch1 Sunday walk, the door"), ("2_trampling", "2. ch1 Hyde and the child"),
          ("3_fireside", "3. ch3 Jekyll's fireside"), ("4_carew", "4. ch4 the Carew murder"),
          ("5_lanyon", "5. ch6 Lanyon stricken"), ("6_cabinet_door", "6. ch8 the cabinet door")]
CELL, PAD, LEFT, TOP = 640, 16, 260, 64
BG, INK = (15, 16, 18), (230, 230, 230)


def font(px: int):
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", px)


def main() -> None:
    sheet = Image.new("RGB", (LEFT + len(SCENES) * (CELL + PAD) + PAD, TOP + CELL + PAD), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD, TOP + CELL // 2 - 30), "A. Photoreal gothic", font=font(26), fill=INK, anchor="lm")
    draw.text((PAD, TOP + CELL // 2 + 14), "(Krea2 turbo t2i, no LoRA)", font=font(17), fill=(160, 160, 160), anchor="lm")
    for j, (name, label) in enumerate(SCENES):
        x = LEFT + j * (CELL + PAD)
        draw.text((x + CELL // 2, TOP // 2), label, font=font(26), fill=INK, anchor="mm")
        pic = Image.open(HERE / "A" / f"{name}.png").convert("RGB").resize((CELL, CELL), Image.LANCZOS)
        sheet.paste(pic, (x, TOP))
    sheet.save(HERE / "samples_sheet.jpg", quality=90)


if __name__ == "__main__":
    main()
