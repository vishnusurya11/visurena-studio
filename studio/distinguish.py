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
from studio.describe import NEIGHBOURS, TraitCard, differences, nearest

SLOT_TRAITS: dict[str, tuple[str, ...]] = {
    "hair": ("hair_colour", "hair_length"), "facial_hair": ("facial_hair",),
    "headgear": ("headgear",), "age": ("age",), "complexion": ("complexion",)}
"""Card slot -> the traits the model reads it as.  A hair phrase carries a
colour AND a length (Scarlet run 6: Lestrade shared hair_length with Hope on
two rungs and nothing could move it).  Build has no slot; see BUILD."""
BUILD = {"slight": "a slight wiry frame", "average": "an average frame",
         "stocky": "a broad stocky frame", "heavy": "a heavy stout frame"}
RELIABLE = ("hair_colour", "hair_length", "facial_hair", "headgear")
"""The traits the render-and-read channel expresses.  Scarlet run 4's seven
sheets: complexion read 'fair' on seven different card phrases, build
'average' on all seven, age followed the hair colour; hair, facial hair and
headgear came back as written, within a notch, on six or seven of seven."""


def coarse(slot: str, phrase: str, trait: str | None = None) -> str:
    """How the model will read one card phrase, as one of the slot's traits."""
    return nearest(trait or SLOT_TRAITS[slot][0], phrase)


def expected(card: dict) -> TraitCard:
    """The card a faithful render reads back as."""
    seen = {trait: coarse(slot, card[slot], trait)
            for slot, traits in SLOT_TRAITS.items() for trait in traits}
    build = next((value for value, phrase in BUILD.items() if phrase == card.get("build")), "unclear")
    figure = {"man": "man", "woman": "woman"}.get(card.get("gender"), "unclear")
    return TraitCard(figure=figure, build=build, **seen)


def disobeyed(card: dict, reading: TraitCard) -> list[str]:
    """The reliable traits the render ignored: seen, and more than a notch
    from what the card asked for."""
    asked = expected(card)
    return [trait for trait in RELIABLE if trait in differences(asked, reading)
            and frozenset((getattr(asked, trait), getattr(reading, trait))) not in NEIGHBOURS]


def _move(slot: str, current: str, avoid: dict[str, str], taken: set[str]) -> str:
    """The next pool phrase after the current one that reads as none of `avoid`."""
    pool = cast_card.POOLS[slot]
    start = pool.index(current) if current in pool else 0
    for step in range(1, len(pool) + 1):
        candidate = pool[(start + step) % len(pool)]
        if candidate not in taken and all(coarse(slot, candidate, t) != v for t, v in avoid.items()):
            return candidate
    return current


def unsaid(card: dict, new: dict) -> str:
    """The book's own sentence, or nothing once a slot it asserts has moved.

    The sheet prompt ends with the book's words; a card moved to 'a full
    beard' that still ends 'with a heavy walrus moustache' tells the model
    two things and it obeys whichever it likes."""
    book = card.get("book", "")
    moved = [slot for slot in cast_card.POOLS if new.get(slot) != card.get(slot)]
    if any(cast_card.book_match(book, cast_card.POOLS[slot]) == card[slot] for slot in moved):
        return ""
    return book


def distinguish(card: dict, matched: list[str], other: TraitCard,
                taken: dict[str, set[str]] | None = None) -> dict:
    """The card with every matched trait moved off the other character's value."""
    new = dict(card)
    for slot, traits in SLOT_TRAITS.items():
        avoid = {t: getattr(other, t) for t in traits if t in matched}
        if avoid:
            new[slot] = _move(slot, card[slot], avoid, (taken or {}).get(slot, set()))
    if "build" in matched:
        new["build"] = next(phrase for value, phrase in BUILD.items() if value != other.build)
    if "book" in card:
        new["book"] = unsaid(card, new)
    return new
