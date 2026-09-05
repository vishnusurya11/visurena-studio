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


def owed(card: dict) -> list[str]:
    """The reliable traits the render owes: those of the slots the book
    asserted (`cast_card` records them); every one when the card predates
    the field.  Scarlet run 7: Holmes's card said 'receding sandy hair' from
    the rotation, the render put dark hair under his bowler four times, and
    the lead went unbound over an invention."""
    if "asserted" not in card:
        return list(RELIABLE)
    return [trait for slot in card["asserted"] for trait in SLOT_TRAITS.get(slot, ())
            if trait in RELIABLE]


def disobeyed(card: dict, reading: TraitCard) -> list[str]:
    """The owed traits the render ignored: seen, and more than a notch
    from what the card asked for."""
    asked = expected(card)
    return [trait for trait in owed(card) if trait in differences(asked, reading)
            and frozenset((getattr(asked, trait), getattr(reading, trait))) not in NEIGHBOURS]


def _drawn(slot: str, reading: TraitCard) -> str | None:
    """The pool phrase closest to what the render drew in one slot: the most
    traits matched, exact before partial; None when nothing was read."""
    seen = {t: getattr(reading, t) for t in SLOT_TRAITS[slot] if getattr(reading, t) != "unclear"}
    if not seen:
        return None
    score = lambda phrase: sum(coarse(slot, phrase, t) == v for t, v in seen.items())
    best = max(cast_card.POOLS[slot], key=score)
    return best if score(best) else None


def adopt(card: dict, reading: TraitCard) -> dict:
    """The card rewritten to what the render drew on the slots the book left
    to invention, so the text and the sheet say the same thing downstream."""
    new = dict(card)
    for slot, traits in SLOT_TRAITS.items():
        if slot in card.get("asserted", ()) or not any(t in RELIABLE for t in traits):
            continue
        if any(coarse(slot, card[slot], t) != getattr(reading, t) != "unclear" for t in traits):
            new[slot] = _drawn(slot, reading) or card[slot]
    return new


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


def movable(matched: list[str], card: dict) -> list[str]:
    """The matched traits a rung may still move: the RELIABLE ones on a slot
    the book did not assert.  Age, complexion and build are read off the
    sheet but not expressed by it (age follows the hair colour, build read
    'average' seven of seven): a rung that moves them changes the person
    and not the reading -- Scarlet run 8 walked Lestrade from thirty-five
    to seventy that way.  `figure` has no slot and never moves."""
    slot_of = {trait: slot for slot, traits in SLOT_TRAITS.items() for trait in traits}
    asserted = set(card.get("asserted", ()))
    return [trait for trait in matched
            if trait in RELIABLE and trait in slot_of and slot_of[trait] not in asserted]


def distinguish(card: dict, matched: list[str], other: TraitCard,
                taken: dict[str, set[str]] | None = None) -> dict:
    """The card with every matched trait moved off the other character's value
    -- except on a slot the book or the known look asserted: moving Holmes
    off clean-shaven to tell him from Watson puts back the beard the card
    exists to refuse.  Two people the book makes alike stay alike."""
    new = dict(card)
    moving = set(movable(matched, card))
    for slot, traits in SLOT_TRAITS.items():
        avoid = {t: getattr(other, t) for t in traits if t in moving}
        if avoid:
            new[slot] = _move(slot, card[slot], avoid, (taken or {}).get(slot, set()))
    if "book" in card:
        new["book"] = unsaid(card, new)
    return new
