"""A series title card: ONE picture for the whole book, re-lettered per episode.

The art is drawn once, with no text (a text-to-image model spells badly and
would redraw the scene each time).  Each episode's words are then EDITED onto
that picture by Qwen-Image-Edit, and read back by Qwen3-VL: a card is only used
when every line reads exactly, so a misspelt title never ships.
"""
from __future__ import annotations

import json
import re

# MEASURED 2026-09-18: "an elegant Victorian serif" drew the series name as
# ornamental flourishes that read as gibberish ("TEWNITS"); plain Roman
# capitals spell.  The episode and chapter lines read at the first try.
LETTER_STYLE = ("Keep the picture exactly as it is. Add clean title lettering centred in the "
                "clear dark sky, in plain bold classical Roman serif capitals like carved "
                "stone lettering, simple letterforms with even spacing, pale ivory with a "
                "faint warm glow, every letter complete and clearly legible, with wide margins "
                "inside the frame edges. Letter exactly these three lines and these words "
                "only, top to bottom: ")


def chapter_name(raw: str) -> str:
    """'I. THE EVE OF THE WAR.' -> 'THE EVE OF THE WAR'."""
    name = re.sub(r"^\s*[IVXLC]+\.\s*", "", raw.strip())
    return name.rstrip(". ").upper()


def card_lines(series: str, number: int, chapter_title: str) -> list[str]:
    return [series.upper(), f"EPISODE {number}", chapter_name(chapter_title)]


def letter_prompt(lines: list[str]) -> str:
    # MEASURED: left to wrap, the series name came back "THE WAR OF / WHE THE WORLDS".
    sizes = ("large, all on ONE single line", "small and widely letter-spaced", "medium")
    said = "; ".join(f'"{line}" ({size})' for line, size in zip(lines, sizes))
    return LETTER_STYLE + said + "."


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
