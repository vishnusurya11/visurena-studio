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


PHOTO_GRID = ("A PHOTOGRAPHIC FILM STILL copied from <image{{n}}> and not invented, in exactly its look: "
              "{lead} Natural depth of field, real skin and real cloth under real light. Match the "
              "palette, the grain and the light of <image{{n}}> exactly.")
"""A photoreal book's storyboard style line, `{n}` the slot it is anchored on.  Jekyll
ep01 (2026-10-13): the house line ("flat angular stylised 3d CGI ... NO photoreal skin")
painted a photoreal book's door panels."""


def atmosphere(book) -> str:
    """The book's declared ATMOSPHERE ("fog, damp haze"), a clause; '' when none.

    Jekyll ep01 (2026-10-13, LOOK.md cause 2): style A is built on fog and not one
    of 27 shots had any -- the take line's word wall cut it and nothing else said it.
    A book files it once in refs/look.json; the grid and the take both read it here."""
    return str(declared(book).get("atmosphere", "") or "").strip().rstrip(".").strip()


ATMOSPHERE_GRID = " The air is thick with {atmosphere} in every frame, softening the far distance."
"""The grid's atmosphere sentence: said as what the air holds, never as a blur asked for."""


DRAWN_GRID = ("DRAWN IN EXACTLY THE LOOK OF <image{{n}}>, copied from it and not invented: {lead} "
              "Match the palette, the line work and the light of <image{{n}}> exactly.")
"""A book that declares a look other than photoreal (an anime gothic, say): its own lead,
never the house's "angular stylised 3D" words nor the photoreal film-still line."""


def look_name(book) -> str:
    """The declared look's name in words ("anime gothic"); '' for the house."""
    return str(declared(book).get("look", "") or "").replace("_", " ").strip()


def drawn(book) -> bool:
    """A declared look that is not photoreal."""
    return bool(look_name(book)) and not photoreal(book)


def grid_style(book) -> str:
    """The grid's style template in the book's look; '' keeps the house line."""
    if not look_name(book):
        return ""
    lead = declared(book).get("lead", "").strip().replace("{", "{{").replace("}", "}}")
    air = atmosphere(book).replace("{", "{{").replace("}", "}}")
    line = (PHOTO_GRID if photoreal(book) else DRAWN_GRID).format(lead=lead)
    return line + (ATMOSPHERE_GRID.format(atmosphere=air) if air else "")


def grid_medium(book) -> str:
    """What one grid frame is called: a photoreal book's is a film still."""
    return "film still" if photoreal(book) else "illustration"


PANEL_HOUSE = "in the house art style"
PANEL_PHOTO = "as a photographic frame in the book's own photoreal look"
"""What a take is told its storyboard panel is drawn as (studio/take_refs.panel_definition).
Jekyll ep01: every photoreal panel was announced to H3 as "in the house art style".
Never the word "still": the take lint L2 STILLNESS refuses it (a still is what H3 holds)."""


def panel_look_words(photo: bool) -> str:
    return PANEL_PHOTO if photo else PANEL_HOUSE


def panel_look(book) -> str:
    """The panel's medium in this book's look: photoreal, a declared drawn look by name, or the house."""
    if drawn(book):
        return f"in the book's own {look_name(book)} look"
    return panel_look_words(photoreal(book))


def plan_look(book, look: str) -> str:
    """A plan's `look` words, unless the book declares its look: the declaration outranks
    a writer's look line (a stylised `look` would turn takes, places and plates house).
    Photoreal renders as `LIVE`; a drawn look heads the take line with its `take` words,
    else its own name."""
    if photoreal(book):
        return ""
    if drawn(book):
        return str(declared(book).get("take", "") or "").strip() or look_name(book).capitalize()
    return look


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
