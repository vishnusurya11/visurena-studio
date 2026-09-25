"""Synthetic negatives: faults drawn into clean pictures, for judges that read
the PIXELS.

Legitimate for lettering, copies, stacked pictures, a gutter, a re-saved
reference: the corruption IS the fault.  Never for a render behaviour
(freeze, slide, drift, over-push, lip lag): a corrupted file would test the
detector against a fake and the ratchet would then protect a number that
never saw a real one.  Every row made here is `verdict_by: synthetic` and
reports in its own column of the bench (decision 2026-09-24 section 1.4).

PIL and numpy only; no model, no GPU.
"""
from __future__ import annotations

import io
from datetime import date

from PIL import Image, ImageDraw, ImageFont

from studio.casebook import Row

SOURCE = "studio/synth_faults.py"
GUTTER = (255, 255, 255)


def paste_text(img: Image.Image, word: str, at: tuple[int, int] | None = None,
               fill=(255, 255, 255), back=(0, 0, 0)) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """A word lettered onto the picture in a plain box; returns the copy and the box [x, y, w, h]."""
    out = img.convert("RGB").copy()
    draw, font = ImageDraw.Draw(out), ImageFont.load_default()
    x, y = at or (out.width // 10, out.height // 10)
    left, top, right, bottom = draw.textbbox((x, y), word, font=font)
    box = (left - 2, top - 2, right - left + 4, bottom - top + 4)
    draw.rectangle([box[0], box[1], box[0] + box[2] - 1, box[1] + box[3] - 1], fill=back)
    draw.text((x, y), word, fill=fill, font=font)
    return out, box


def duplicate_crop(img: Image.Image, box: tuple[int, int, int, int], to: tuple[int, int]) -> Image.Image:
    """One crop of the picture pasted again elsewhere: the copies fault."""
    x, y, w, h = box
    out = img.convert("RGB").copy()
    out.paste(out.crop((x, y, x + w, y + h)), to)
    return out


def tile_two(a: Image.Image, b: Image.Image, gutter: int = 6, color=GUTTER) -> Image.Image:
    """Two panels side by side with a pale gutter between: two pictures in one frame."""
    a, b = a.convert("RGB"), b.convert("RGB")
    out = Image.new("RGB", (a.width + gutter + b.width, max(a.height, b.height)), color)
    out.paste(a, (0, 0))
    out.paste(b, (a.width + gutter, 0))
    return out


def draw_gutter(img: Image.Image, axis: str = "y", width: int = 6, color=GUTTER) -> Image.Image:
    """A pale, even line across the middle: `y` stands upright, `x` lies across."""
    out = img.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    if axis == "y":
        x = out.width // 2 - width // 2
        draw.rectangle([x, 0, x + width - 1, out.height - 1], fill=color)
    else:
        y = out.height // 2 - width // 2
        draw.rectangle([0, y, out.width - 1, y + width - 1], fill=color)
    return out


def resave_reference(img: Image.Image, quality: int = 60) -> Image.Image:
    """The picture round-tripped through JPEG: a handed-back reference, not a drawing."""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def row(codex: str, unit: str, kind: str, path: str, fault_class: str,
        region: tuple[int, int, int, int] | None = None) -> Row:
    """The casebook row for a synthetic fault: its own column, never the owner's."""
    return Row(codex=codex, unit=unit, kind=kind, path=path, verdict="fault", fault_class=fault_class,
               verdict_by="synthetic", verdict_at=date.today().isoformat(), source=SOURCE,
               region=list(region) if region else None)
