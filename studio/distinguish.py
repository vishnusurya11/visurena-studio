"""The distinguish rung: rewrite a card on exactly the traits its sheet
shared with a bound character.

`cast_card` writes the prompt in OBJECTS (a bowler, a walrus moustache);
`describe` reads the render back in coarse TRAITS (bowler, moustache).  This
module is the bridge: each card slot is read the way the model will read it,
and a slot whose reading matched the other character is moved to a phrase
that reads differently.  Nothing else on the card changes, so the character
stays the person the book describes.
"""
from __future__ import annotations

from studio import cast_card
from studio.describe import TraitCard, nearest

SLOT_TRAIT = {"hair": "hair_colour", "facial_hair": "facial_hair", "headgear": "headgear",
              "age": "age", "complexion": "complexion"}
"""Card slot -> the trait the model reads it as.  Build has no slot; see BUILD."""
BUILD = {"slight": "a slight wiry frame", "average": "an average frame",
         "stocky": "a broad stocky frame", "heavy": "a heavy stout frame"}


def coarse(slot: str, phrase: str) -> str:
    """How the model will read one card phrase."""
    return nearest(SLOT_TRAIT[slot], phrase)


def _move(slot: str, current: str, avoid: str, taken: set[str]) -> str:
    """The next pool phrase after the current one that reads as not `avoid`."""
    pool = cast_card.POOLS[slot]
    start = pool.index(current) if current in pool else 0
    for step in range(1, len(pool) + 1):
        candidate = pool[(start + step) % len(pool)]
        if coarse(slot, candidate) != avoid and candidate not in taken:
            return candidate
    return current


def distinguish(card: dict, matched: list[str], other: TraitCard,
                taken: dict[str, set[str]] | None = None) -> dict:
    """The card with every matched trait moved off the other character's value."""
    new = dict(card)
    for slot, trait in SLOT_TRAIT.items():
        if trait in matched:
            new[slot] = _move(slot, card[slot], getattr(other, trait), (taken or {}).get(slot, set()))
    if "build" in matched:
        new["build"] = next(phrase for value, phrase in BUILD.items() if value != other.build)
    return new
