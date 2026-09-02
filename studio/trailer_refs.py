"""Reference sheets, which belong to the BOOK and not to any one trailer.

The trailer, the song and the episode all draw the same faces from
library/<book>/refs/.  That is the whole point of putting them there: a
character who looks one way in the trailer and another in episode one is two
characters as far as the audience is concerned.

Prompts are built from analysis/, so a reference is answerable to the book --
`profile.physical` is what the text says the person looks like, not what a
model imagined.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio.trailer_spec import RefSheet

STYLE = (
    "Cinematic live-action photograph, anamorphic widescreen, natural film grain, "
    "photoreal, no stylisation, no illustration."
)
SHEET_FRAME = (
    "Full-body character reference on a plain neutral mid-grey backdrop, even soft "
    "studio light, no cast shadows, neutral expression, facing camera, sharp focus, "
    "full figure head to feet in frame."
)
PLATE_FRAME = (
    "Establishing wide plate of an empty location, no people, no figures, "
    "deep focus, even natural light."
)
NO_TYPE = "No text, no lettering, no signage, no watermark, no subtitles."


def character_prompt(physical: str, palette: str) -> str:
    """A reference sheet prompt: house style, sheet framing, then the person."""
    return " ".join([STYLE, palette, SHEET_FRAME, physical.strip(), NO_TYPE])


def location_prompt(described: str, palette: str) -> str:
    """A plate prompt.  Emptiness is stated because a plate with a figure in it
    binds that figure into every shot restaged from it."""
    return " ".join([STYLE, palette, PLATE_FRAME, described.strip(), NO_TYPE])


def physical_of(character: dict) -> str:
    """What the book says this person looks like, or their name as a floor."""
    physical = (character.get("profile") or {}).get("physical") or ""
    return physical.strip() or f"{character.get('name', 'a person')}, period-appropriate dress."


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ref_id_for(kind: str, entity_id: str) -> str:
    """Stable ref id.  Ids are the join between analysis, plan and job."""
    return f"{'char' if kind == 'character' else 'loc'}-{entity_id}"


META_OPENERS = (
    "the dossier gives", "the dossier identifies", "the dossier does not",
    "the dossier provides", "the text describes", "the narrative describes",
    "repeatedly described as", "is described as", "described as",
    "the source gives", "no precise", "the dossier",
)
"""Analysis prose talks ABOUT the text.  A camera cannot photograph "the
dossier identifies Watson as an army surgeon" -- at best it is ignored, at
worst the model renders a document.  A shot prompt needs what is visible."""


SENTENCE_END = re.compile(r"(?<![A-Z])(?<!Dr)(?<!Mr)(?<!Mrs)(?<!St)\.\s+")
"""Sentence boundaries that survive titles.  A naive split on ". " turns
"Dr. Watson" into two sentences and leaves "Watson." as a fragment -- the same
abbreviation bug that once ended a sentence at "Mrs."."""

VISUAL_LIMIT = 220
"""Keep the tag short.  The reference image carries the identity; this text
only has to pin the category, and a long biography dilutes it."""


APPEARANCE = (
    "hair", "face", "facial", "eyes", "beard", "moustache", "whisker", "skin",
    "tall", "short", "small", "little", "thin", "lean", "gaunt", "stout",
    "build", "figure", "limb", "hand", "hands", "shoulder", "stature", "height",
    "dressed", "dress", "clothes", "clothing", "coat", "hat", "worn", "wears",
    "wearing", "pale", "dark", "fair", "aged", "years old", "nose", "chin",
    "brow", "complexion", "posture", "bearing", "stoop",
)

ABSENCE = ("no description", "no confirmed", "no precise", "gives no", "does not provide",
           "not provide", "no physical", "without description", "unspecified",
           "or distinguishing physical features", "or other distinguishing")
"""A sentence that says a description is MISSING is worse than none at all --
it hands the model the vocabulary of a face while telling it nothing.  Several
of these books genuinely never describe a character, and the right answer is
silence plus the reference image."""
"""Words that mean a sentence is describing a BODY rather than a biography.

The analysis field is a life summary -- "served with the Berkshires in
Afghanistan, was wounded by a Jezail bullet at Maiwand" is true, sourced, and
completely unphotographable.  A shot prompt needs the half that a camera can
see."""


def visual_description(physical: str, limit: int = VISUAL_LIMIT) -> str:
    """The sentences of a profile that describe how someone LOOKS.

    Meta-narrative openers are dropped, then anything with no appearance word
    in it.  Returning "" is an honest answer -- some characters simply have no
    description in the book -- and the caller falls back to the reference
    image, which is what carries identity anyway.
    """
    kept: list[str] = []
    for sentence in SENTENCE_END.split(physical.replace(chr(10), " ")):
        clean = sentence.strip().rstrip(".")
        lowered = clean.lower()
        if not clean or any(lowered.startswith(o) for o in META_OPENERS):
            continue
        if any(word in lowered for word in ABSENCE):
            continue
        if not any(word in lowered for word in APPEARANCE):
            continue
        kept.append(clean)
        if len(". ".join(kept)) >= limit:
            break
    return (". ".join(kept) + ".") if kept else ""


VOID_EPITHETS = ("the latter", "our friend", "our old friend", "the former",
                 "a friend", "his friend", "the other", "the man", "the fellow",
                 "the person", "my gentleman", "the young man", "this fellow")
"""Epithets that name a relationship rather than a person.  "our old friend"
describes no one; "the solemn butler" describes someone completely."""


def epithets(aliases: list[str], name: str) -> list[str]:
    """The descriptive names a book uses for someone, as description.

    This is the fix for CHARACTER COLLISION.  Where a book never describes
    anyone -- Stevenson never says what Utterson looks like -- generating
    refs from the profile alone produced four indistinguishable Victorian
    gentlemen for Hyde, Utterson, Poole and Enfield.

    But the book DID say: "the solemn butler", "the lawyer", "a little man",
    "a maid servant".  An epithet is the author describing a character in the
    fewest words they thought necessary, and it separates them instantly.
    """
    # Only an alias IDENTICAL to the name is redundant.  Sharing a word with
    # it is not: an unnamed character's "name" may itself be an epithet -- the
    # housemaid is called "the maid" -- and filtering on shared words then
    # discarded "a maid servant", which is the one alias that adds anything.
    spoken = name.lower().strip(".,")
    found: list[str] = []
    for alias in aliases:
        clean = alias.strip().rstrip(".")
        lowered = clean.lower()
        if not lowered.startswith(("a ", "an ", "the ")):
            continue
        if lowered in VOID_EPITHETS or lowered == spoken:
            continue
        if clean not in found:
            found.append(clean)
    return found


def described_as(character: dict) -> str:
    """One line combining what the book calls someone with how it describes them."""
    tags = epithets(character.get("aliases", []), character.get("name", ""))
    physical = visual_description((character.get("profile") or {}).get("physical", ""))
    lead = f"{character.get('name', 'A person')}, {', '.join(tags[:3])}." if tags else ""
    return " ".join(part for part in (lead, physical) if part).strip()
