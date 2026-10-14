"""A labelled contact sheet of a folder of square pictures: contact.py <folder> <glob> <out.jpg> [cols]."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

folder, pattern, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 6
files = sorted(folder.glob(pattern))
cell = 256
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell, rows * cell), (15, 16, 18))
draw = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB")
    im.thumbnail((cell, cell))
    x, y = (i % cols) * cell, (i // cols) * cell
    sheet.paste(im, (x, y))
    draw.text((x + 4, y + 4), f.stem, fill=(255, 255, 0))
sheet.save(out, quality=85)
print(out, len(files))
