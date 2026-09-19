"""A series title card: ONE picture for the whole book, re-lettered per episode.

The art is drawn once, with no text (Krea2 spells badly and would redraw the
scene each time).  Each episode's words are drawn by Ideogram 4 alone on black
and screened over that picture, then read back by Qwen3-VL: a card is only
used when every line reads exactly, so a misspelt title never ships.
"""
from __future__ import annotations

import json
import re

PLATE_BOXES = ([60, 140, 940, 260], [300, 290, 700, 340], [120, 360, 880, 450])
"""Series, episode, chapter -- stacked in the card's upper sky (0-1000 grid)."""
PLATE_SIZES = ("large", "small, widely letter-spaced", "medium")


def plate_caption(lines: list[str]) -> str:
    """Ideogram 4's structured caption for the LETTERING ALONE on pure black.

    MEASURED 2026-09-18: Qwen-Image-Edit, asked to letter the art, drew the
    series name as "THE WAR OF / WHE THE WORLDS" on every seed.  Ideogram is
    the typography model; its plate is screened over the art, black vanishing."""
    elements = [{"type": "text", "bbox": box,
                 "desc": f'the words "{line}" (exact, no typos), {size}, centred, all caps, '
                         "plain classical Roman serif capitals, pale ivory with a faint warm glow"}
                for line, box, size in zip(lines, PLATE_BOXES, PLATE_SIZES)]
    return json.dumps({
        "aspect_ratio": "1:1", "scene": "A title lettering plate",
        "high_level_description": "Three centred lines of title lettering on a pure black ground.",
        "text_rules": "Render only the quoted words, exactly as written, horizontal.",
        "style_description": {"aesthetics": "classical title card lettering", "lighting": "flat",
                              "medium": "typography only", "color_palette": ["#000000", "#F1E6CC"]},
        "compositional_deconstruction": {"background": "Pure flat black, empty, no texture.",
                                         "elements": elements}}, ensure_ascii=False)


def screen_over(art, plate):
    """Lay the lettering plate on the art with a screen blend: black leaves the
    art untouched, ivory lights it.  No picture element is composited."""
    from PIL import Image, ImageChops
    return ImageChops.screen(art.convert("RGB"),
                             plate.convert("RGB").resize(art.size, Image.LANCZOS))


def chapter_name(raw: str) -> str:
    """'I. THE EVE OF THE WAR.' -> 'THE EVE OF THE WAR'."""
    name = re.sub(r"^\s*[IVXLC]+\.\s*", "", raw.strip())
    return name.rstrip(". ").upper()


def card_lines(series: str, number: int, chapter_title: str) -> list[str]:
    return [series.upper(), f"EPISODE {number}", chapter_name(chapter_title)]


def transcription(raw: str) -> str:
    """Qwen3-VL answers as a JSON list of strings with escaped newlines
    ('["THE WAR OF\\nTHE WORLDS"]'); read as plain text, the 'n' of each '\\n'
    glued itself to the next word and every line failed."""
    try:
        said = json.loads(raw)
    except ValueError:
        return raw.replace("\\n", "\n")
    return "\n".join(said) if isinstance(said, list) else str(said)


def _norm(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", transcription(text).upper()).strip()


def missing_lines(lines: list[str], ocr: str) -> list[str]:
    """Lines the transcription does not contain as a whole run of words."""
    read = f" {_norm(ocr)} "
    return [line for line in lines if f" {_norm(line)} " not in read]


def lines_read(lines: list[str], ocr: str) -> bool:
    return not missing_lines(lines, ocr)
