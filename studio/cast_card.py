"""Eight slots per character, chosen so no two people share the same objects.

THE RULE THIS IS BUILT ON: a model draws OBJECTS.  A phrase moves the output
exactly as far as it changes the list of things that must be drawn.

    "a custodian helmet"        adds an object                 obeyed
    "a heavy jaw"               modifies one already there     mostly ignored
    "shorter than Henry Jekyll" names something not in frame    never obeyed

Everything below follows from that.  `distinguishing_marks` hashed the
character id -- stable, and completely blind, because a hash cannot know that
Holmes has already taken "dark hair swept back".  It also spent its three
choices on build, hair and face, which are adjectives on objects the prior
already has an opinion about.

MEASURED on the shipped sheets, SFace: Watson x Holmes 0.540, Lestrade x
Holmes 0.464, against a same-person line of 0.363.  A controlled A/B moved the
worst pair to 0.187 by changing nothing but the object list.
"""
from __future__ import annotations

import re

HEADGEAR = ("a black silk top hat", "a brown bowler hat", "a tweed deerstalker",
            "a soft cloth cap", "a wide-brimmed felt hat", "a bare head",
            "a custodian helmet", "a straw boater", "a fur travelling cap",
            "a flat tweed cap", "a tall beaver hat", "a knitted watch cap",
            "a straw bonnet tied with ribbon", "a plain cotton sun bonnet",)
FACIAL_HAIR = ("clean-shaven", "a thin waxed moustache", "a heavy walrus moustache",
               "a full dark beard", "grey side-whiskers", "a short pointed beard",
               "muttonchop whiskers", "a close-trimmed grey beard",
               "a long untrimmed beard", "a drooping grey moustache",
               "a stubbled unshaven jaw", "an imperial beard and moustache",)
"""Ordered from the least added to the most: `distinguish._move` walks the
pool from the current phrase, and the first step off a known face's
clean-shaven must be a moustache, not a full dark beard."""
GARMENT = ("a charcoal frock coat", "a bottle-green velvet jacket",
           "a fawn tweed overcoat", "a black caped ulster",
           "a rust-brown corduroy coat", "a dove-grey morning coat",
           "a navy pea jacket", "a russet riding coat",
           "a slate-blue shawl and plain dress",
            "a dark green hunting jacket", "a grey astrakhan coat",
            "a worn leather work coat",)
NECKWEAR = ("a stiff wing collar and black stock", "a soft turned-down collar",
            "a loosely knotted red neckerchief", "a bare throat above a collarless shirt",
            "a white cravat pinned with a stud", "a clerical black tie",
            "a checked muffler", "a leather cord at the throat",
            "a lace collar",
            "a black silk scarf", "a high starched collar",
            "an open shirt with the collar unbuttoned",)

MODEL_TEXT = (HEADGEAR, FACIAL_HAIR, GARMENT, NECKWEAR)


ROLE_ITEMS = {
    "headgear": {"policeman": ("a custodian helmet",)},
    "neckwear": {"clergyman": ("a clerical black tie",)},
}
"""Costume that states a job.  A custodian helmet on Sherlock Holmes is not a
distinguishing feature, it is a different character -- and the first run of
this module put one on him."""

FEMALE_ONLY = ("a slate-blue shawl and plain dress", "a lace collar",
               "a straw bonnet tied with ribbon", "a plain cotton sun bonnet")
"""Never assigned to a man, and never to an unknown: 'person' must not quietly
mean 'put them in a gown'.  Watson's own description carries no pronoun, so
inference returned 'person', and he was rendered in a dress at seventy."""

TIER_ONE = ("headgear", "facial_hair", "garment", "neckwear")
"""Slots that add a separate thing to draw.  These are near-always obeyed, and
no two characters may share one."""

AGE = ("in his early twenties", "in his late twenties", "about thirty-five",
       "about forty", "about forty-five", "about fifty", "about fifty-five",
       "about sixty", "about seventy")
HAIR = ("dark hair swept back", "receding sandy hair", "close-cropped grey hair",
        "a bald crown with grey at the temples", "long black hair",
        "wavy chestnut hair", "thinning red hair", "white hair worn long",
        "fair hair parted in the middle")
COMPLEXION = ("a pale indoor complexion", "a florid weathered face",
              "a sallow complexion", "a sun-darkened face",
              "a ruddy open face", "an ashen complexion",
              "a freckled fair complexion", "an olive complexion",
              "a lined and sunburnt face")

TIER_TWO = ("age", "hair", "complexion")
"""Properties with their own vocabulary.  Obeyed when Tier One agrees."""

IDENTITY = ("facial_hair", "hair")
"""The slots that make a face someone else when invented.  On a character
the audience already knows (`canon`), where the book and the known look
leave one of these empty, invention ADDS nothing: clean-shaven, and the
plainest hair of that age.  Scarlet run 7 gave Watson a full dark beard and
Holmes a walrus moustache; neither was a Watson or a Holmes nobody had
described, each was a different man.  The card lists them as `neutral`:
run 8 left them movable for a proven collision, Lestrade's sheet collided
with Watson's, and the rung made him seventy, white-haired and bearded; then
asserted, the gate refused three brown-haired Watsons over an invented
'fair'.  A neutral slot is owed as NOTHING ADDED (grey, white, bald, long,
a beard), not as a phrase; no rung moves it; what the render drew within
that is adopted.  A known face that reads like another known face is
accepted as written, as two people the book makes alike are."""

POOLS = {"headgear": HEADGEAR, "facial_hair": FACIAL_HAIR, "garment": GARMENT,
         "neckwear": NECKWEAR, "age": AGE, "hair": HAIR,
         "complexion": COMPLEXION}


GENERIC = {'a', 'an', 'the', 'and', 'with', 'his', 'her', 'worn', 'in', 'at',
           'of', 'no', 'man', 'face', 'hair', 'complexion', 'about'}


FEMALE_MARKS = ('she', 'her', 'hers', 'girl', 'woman', 'daughter', 'sister',
                'wife', 'lady', 'miss', 'mrs', 'madame', 'mother', 'widow')
MALE_MARKS = ('he', 'his', 'him', 'boy', 'man', 'son', 'brother', 'husband',
              'sir', 'mr', 'father', 'gentleman')
NO_BEARD = 'clean-shaven'


OLD_MARKS = ("old", "older", "elderly", "aged", "grey-haired", "white-haired",
             "venerable", "veteran")
YOUNG_MARKS = ("young", "girl", "boy", "child", "youth", "youthful", "lad")

BANDED = {
    "young": {"age": ("in his early twenties", "in his late twenties",
                      "about thirty"),
              "hair": ("dark hair swept back", "wavy chestnut hair",
                       "fair hair parted in the middle", "long black hair"),
              "facial_hair": ("clean-shaven", "a thin waxed moustache",
                              "a stubbled unshaven jaw")},
    "middle": {"age": ("about thirty-five", "about forty", "about forty-five",
                       "about fifty"),
               "hair": ("dark hair swept back", "receding sandy hair",
                        "wavy chestnut hair", "fair hair parted in the middle",
                        "thinning red hair", "long black hair")},
    "old": {"age": ("about sixty", "about seventy", "about fifty-five"),
            "hair": ("a bald crown with grey at the temples",
                     "close-cropped grey hair", "white hair worn long",
                     "thinning red hair"),
            "facial_hair": ("a close-trimmed grey beard", "grey side-whiskers",
                            "a drooping grey moustache", "a long untrimmed beard")},
}
"""What is plausible at each end of life, plainest first: `neutral` hands a
known face the first of its band nobody has, and long black hair on Watson
(Scarlet, 2026-09-04) is not nothing added.

A bald crown with grey at the temples on a young woman, and late twenties on
"the old farmer", are not near misses -- they are different people.  Nor is
white hair worn long at about forty: Holmes drew it from the rotation
(Scarlet run 6), so grey, white and bald are the old band's alone.  Invention
is allowed where the book is silent; it is not allowed to contradict what the
book does say.
"""


def age_band(physical: str) -> str:
    """young / old / middle, from the words the book uses about this person."""
    words = set(physical.lower().replace(",", " ").replace(".", " ").split())
    if words & set(OLD_MARKS):
        return "old"
    if words & set(YOUNG_MARKS):
        return "young"
    return "middle"


def infer_gender(name: str, aliases: list[str], physical: str) -> str:
    """woman / man / person, from the words the book itself uses.

    There is no gender field in the analysis, and guessing from a name is how
    you misgender someone.  The aliases and the prose say it outright -- Lucy
    Ferrier is "the girl" and "his daughter" -- and where they do not, the
    honest answer is "person" rather than the majority class.
    """
    words = set(re.findall(r"[a-z']+", (' '.join(aliases) + ' ' + physical).lower()))
    female = len(words & set(FEMALE_MARKS))
    male = len(words & set(MALE_MARKS))
    if female > male:
        return 'woman'
    if male > female:
        return 'man'
    return 'person'


DECADES = ("twenties", "thirty", "thirties", "forty", "forties", "fifty",
           "fifties", "sixty", "sixties", "seventy", "seventies")


# The words that name a slot's OBJECT.  A pool phrase is an attribute on an
# object ("a brown bowler hat"), and the book asserts the object only when it
# names it: Watson "as brown as a nut" is not a hat, Hope's "long rifle" is
# not long hair, "tall" is not a tall beaver hat (Scarlet run 7, every one of
# them asserted, so the render owed an adjective spent on something else).
OBJECT = {
    "headgear": {"hat", "cap", "helmet", "bonnet", "hood", "bowler", "topper",
                 "deerstalker", "boater", "bareheaded", "hatless"},
    "facial_hair": {"moustache", "mustache", "beard", "bearded", "whiskers",
                    "shaven", "unshaven", "stubble", "stubbled"},
    "garment": {"coat", "overcoat", "jacket", "cloak", "ulster", "dress", "shawl",
                "waistcoat", "uniform", "gown", "suit", "frock", "tweed", "robe"},
    "neckwear": {"collar", "cravat", "tie", "necktie", "muffler", "scarf",
                 "neckerchief", "stock"},
    "hair": {"hair", "haired", "bald", "curls", "locks"},
    "age": {"year", "years", "aged", "old", "young", "youth", "elderly"},
    "complexion": {"complexion", "face", "faced", "cheek", "cheeks", "skin",
                   "countenance"},
}
# Naming the object alone ("he wore a hat") asserts no KIND of it.
BARE = {"hat", "cap", "coat", "jacket", "collar", "tie", "hair", "haired", "beard",
        "moustache", "mustache", "face", "faced", "complexion", "year", "years",
        "old", "young"}


def names_object(physical: str, slot: str) -> bool:
    """Whether the book's words name the thing this slot is about at all."""
    if slot not in OBJECT:
        return True
    return bool(OBJECT[slot] & set(re.findall(r"[a-z]+", physical.lower())))


def _overlap(physical: str, value: str) -> set[str]:
    words = {w.strip('.,;:') for w in physical.lower().split()} - GENERIC
    return ({w.strip('.,;:') for w in value.lower().split()} - GENERIC) & words


def book_match(physical: str, pool: tuple[str, ...], slot: str = "") -> str:
    """The pool value the book's own description actually points at.

    Authority order is the book first, then dress convention, then invention.
    Invention is only for slots the book leaves empty -- a sheet that ignores
    Doyle saying "frock coat" to put Holmes in a riding coat is not a
    reference to anything.  A match needs the object named (`OBJECT`) and one
    attribute of it in the book's words, not the bare noun.
    """
    # An age is a decade, and "thirty" must match "about thirty-five" -- the
    # book saying thirty and the card saying seventy is not a near miss.
    said = [d for d in DECADES if d in physical.lower()]
    if said and any("about" in v or "in his" in v or "in her" in v for v in pool):
        for value in pool:
            if said[0].rstrip("ies").rstrip("y") in value.lower():
                return value
    if not names_object(physical, slot):
        return ""
    best, score = '', 0
    for value in pool:
        overlap = _overlap(physical, value)
        if len(overlap) > score and overlap - BARE:
            best, score = value, len(overlap)
    return best


def _allowed(slot: str, pool: tuple[str, ...], gender: str,
             role: str) -> list[str]:
    """The pool minus anything this character has no right to wear."""
    reserved = {item for by_role in ROLE_ITEMS.get(slot, {}).values()
                for item in by_role}
    mine = set(ROLE_ITEMS.get(slot, {}).get(role, ()))
    options = [v for v in pool if v not in reserved or v in mine]
    if gender != "woman":
        options = [v for v in options if v not in FEMALE_ONLY]
    else:
        options = [v for v in options if v in FEMALE_ONLY] or options
    return options


def neutral(slot: str, physical: str, taken: dict[str, set[str]] | None = None) -> str:
    """What invention may add to a known face: nothing -- clean-shaven, and
    the plainest hair of the band that no other card already reads as."""
    if slot == "facial_hair":
        return NO_BEARD
    options = BANDED[age_band(physical)]["hair"]
    spent = (taken or {}).get("hair", set())
    return next((h for h in options if h not in spent), options[0])


def card_for(entity_id: str, taken: dict[str, set[str]],
             physical: str = "", gender: str = "man",
             role: str = "", stated: dict[str, str] | None = None,
             known: bool = False) -> dict[str, str]:
    """One character's eight slots, avoiding every value already spent.

    `stated` is what the book says outright (`portrait.stated`) or the look
    the world knows (`canon.known_look`): it outranks the role, the book
    match and the rotation alike.  `known` is a face the audience would
    recognise: its IDENTITY slots are never invented, only left neutral.

    Walks the pools in a per-character rotation so the assignment is stable,
    and skips anything another character has taken.  The rotation is what
    `distinguishing_marks` lacked: it hashed the id in isolation, so two
    characters could and did land on the same features.
    """
    offset = sum(ord(ch) * (i + 1) for i, ch in enumerate(entity_id))
    card: dict = {}
    asserted: list[str] = []
    neutral_slots: list[str] = []
    for slot, pool in POOLS.items():
        spent = taken.get(slot, set())
        banded = BANDED.get(age_band(physical), {}).get(slot)
        allowed = _allowed(slot, banded or pool, gender, role)
        # Authority order: the role's own costume, then the book's words, then
        # invention.  A policeman's helmet is not a distinguishing feature to
        # be handed out, it is what a policeman wears.
        for_role = [v for v in ROLE_ITEMS.get(slot, {}).get(role, ()) if v in allowed]
        from_book = book_match(physical, tuple(allowed), slot) if physical.strip() else ""
        options = [v for v in allowed if v not in spent] or allowed
        card[slot] = (for_role[0] if for_role
                      else from_book or options[offset % len(options)])
        if known and slot in IDENTITY and not (for_role or from_book):
            card[slot] = neutral(slot, physical, taken)
            neutral_slots.append(slot)
        if from_book and not for_role:
            asserted.append(slot)
    card.update(stated or {})
    card['gender'] = gender
    if gender == 'woman':
        # A beard is an OBJECT, and drawing one on a woman is not a small
        # error: Lucy came back indistinguishable from Gregson at 0.541.
        card['facial_hair'] = NO_BEARD
        asserted.append('facial_hair')
        card['age'] = card['age'].replace('in his ', 'in her ')
    if physical.strip():
        card['book'] = physical.strip()
    # The slots the book (or the person's sex) filled are the ones a render
    # OWES; the rest were invented to tell the cast apart, and the render
    # decides them (Scarlet run 7: Holmes unbound over invented sandy hair).
    card['asserted'] = sorted(set(asserted) | set(stated or {}))
    card['neutral'] = sorted(set(neutral_slots) - set(stated or {}))
    return card


def alike(slot: str, value: str) -> set[str]:
    """Every pool phrase the sheet reader would call the same as this one.
    A slot with no reading is alike only to itself."""
    from studio.distinguish import SLOT_TRAITS, coarse
    traits = SLOT_TRAITS.get(slot, ())
    if not traits:
        return {value}
    seen = tuple(coarse(slot, value, t) for t in traits)
    return {v for v in POOLS[slot] if tuple(coarse(slot, v, t) for t in traits) == seen} | {value}


def cards_for(cast: list[str], physical: dict[str, str],
              genders: dict[str, str] | None = None,
              roles: dict[str, str] | None = None,
              stated: dict[str, dict[str, str]] | None = None,
              known: set[str] | None = None) -> dict[str, dict]:
    """A card per character, each avoiding what the others have taken."""
    # The book's words are reserved before anyone invents: Gregson's stated
    # "receding sandy hair" arrived after the rotation had given it to Holmes.
    taken: dict[str, set[str]] = {slot: set() for slot in POOLS}
    for said in (stated or {}).values():
        for slot in POOLS:
            if slot in said:
                taken[slot] |= alike(slot, said[slot])
    cards: dict[str, dict] = {}
    for entity_id in cast:
        card = card_for(entity_id, taken, physical.get(entity_id, ""),
                        (genders or {}).get(entity_id, "man"),
                        (roles or {}).get(entity_id, ""),
                        (stated or {}).get(entity_id),
                        entity_id in (known or set()))
        cards[entity_id] = card
        for slot in POOLS:
            taken[slot] |= alike(slot, card[slot])
    return cards


def differences(first: dict, second: dict) -> int:
    """How many slots two cards disagree in."""
    return sum(first.get(slot) != second.get(slot)
               for slot in TIER_ONE + TIER_TWO)


def refuse_collision(cards: dict[str, dict], minimum: int = 3) -> None:
    """Refuse a cast where any pair is too alike to tell apart.

    Every pair must differ in at least `minimum` slots AND in at least one
    Tier One slot.  Free, textual, and the only gate that runs before a single
    GPU second -- which matters because a face recogniser passed the Jekyll
    cast at 0.291 while human readers called them near-identical.  What
    collided there was age, hair, costume and light, not face geometry.
    """
    names = sorted(cards)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            shared_tier_one = all(cards[first][slot] == cards[second][slot]
                                  for slot in TIER_ONE)
            if differences(cards[first], cards[second]) < minimum or shared_tier_one:
                raise ValueError(
                    f"{first} and {second} differ in only "
                    f"{differences(cards[first], cards[second])} slots; they "
                    f"will render as the same person")


def render_card(card: dict[str, str]) -> str:
    """The card as a sheet prompt: objects first, no comparatives.

    A comparative names something that is not in the frame, so it is never
    obeyed -- and worse, Jekyll's sheet carried Hyde's description while Hyde's
    carried Jekyll's, the two characters most at risk of collision each
    describing the other.
    """
    noun = {"woman": "A woman", "person": "A person"}.get(card.get("gender"), "A man")
    age = card["age"]
    if card.get("gender") == "woman":
        age = age.replace("in his", "in her")
    beard = ("" if card.get("gender") == "woman"
             else f"{card['facial_hair']}, ")
    build = f"{card['build']}, " if card.get("build") else ""
    parts = [f"{noun} {age}, {build}{card['complexion']}, {card['hair']},",
             f"{beard}wearing {card['headgear']},",
             f"{card['garment']} and {card['neckwear']}."]
    if card.get("book"):
        parts.append(card["book"])
    return " ".join(parts)
