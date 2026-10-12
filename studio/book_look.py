"""The book's declared look: which local renderer draws its refs pictures, and with what words.

Owner 2026-10-11 ("book look, not house look"): every picture follows the BOOK.
The title plates learned it (`book_title.plate_request`); the refs drawers -- the
base sheet, a fresh look, a place master -- still drew every book in WotW's
Krea2 + Cinematic LoRA look.  A book declares its look ONCE, by the owner's
ruling, in `library/<book>/refs/look.json`:

    {"look": "photoreal", "lead": "<the book's own words>. ", "tail": " No text ...",
     "decision": "<date> <ruling>", "by": "owner"}

A photoreal book draws on Krea2 turbo with no LoRA, its lead first; a book with
no declaration (or a malformed one) keeps the house look, as before.
"""
from __future__ import annotations

import json
from pathlib import Path

FILE = "refs/look.json"
PHOTOREAL_T2I = "image_krea2_turbo_t2i"
ASPECTS = {"1:1 (Square)": 1.0, "2:3 (Portrait Photo)": 2 / 3, "3:2 (Photo)": 1.5,
           "3:4 (Portrait Standard)": 0.75, "4:3 (Standard)": 4 / 3, "9:16 (Portrait Widescreen)": 9 / 16,
           "16:9 (Widescreen)": 16 / 9, "21:9 (Ultrawide)": 21 / 9}
"""The ResolutionSelector's own choices (ComfyUI object_info, 2026-10-12)."""


def declared(book) -> dict:
    """The book's look.json, or {} -- a missing or malformed file declares nothing."""
    try:
        said = json.loads((Path(book) / FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return said if isinstance(said, dict) else {}


def photoreal(book) -> bool:
    return declared(book).get("look") == "photoreal"


def aspect_for(width: int, height: int) -> str:
    """The selector's choice nearest the asked shape."""
    ratio = width / height
    return min(ASPECTS, key=lambda name: abs(ASPECTS[name] - ratio))


def t2i(book, prompt: str, *, width: int, height: int, seed: int, prefix: str) -> tuple[str, dict]:
    """(workflow, inject values) for one text-to-image refs picture in the book's look."""
    if not photoreal(book):
        from studio import refs_pack
        return refs_pack.T2I, {"prompt": refs_pack.styled(prompt), "seed": seed, "width": width,
                               "height": height, "filename_prefix": prefix}
    said = declared(book)
    return PHOTOREAL_T2I, {"prompt": f"{said.get('lead', '')}{prompt}{said.get('tail', '')}", "seed": seed,
                           "aspect_ratio": aspect_for(width, height), "megapixels": 2,
                           "refine_prompt": False, "enable_lora": False, "filename_prefix": prefix}
