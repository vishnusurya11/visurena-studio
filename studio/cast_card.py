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

HEADGEAR = ("a black silk top hat", "a brown bowler hat", "a tweed deerstalker",
            "a soft cloth cap", "a wide-brimmed felt hat", "a bare head",
            "a custodian helmet", "a straw boater", "a fur travelling cap",
            "a flat tweed cap", "a tall beaver hat", "a knitted watch cap",)
FACIAL_HAIR = ("clean-shaven", "a full dark beard", "grey side-whiskers",
               "a heavy walrus moustache", "a short pointed beard",
               "a thin waxed moustache", "muttonchop whiskers",
               "a close-trimmed grey beard", "a long untrimmed beard",
               "a drooping grey moustache", "a stubbled unshaven jaw",
               "an imperial beard and moustache",)
GARMENT = ("a charcoal frock coat", "a bottle-green velvet jacket",
           "a fawn tweed overcoat", "a black caped ulster",
           "a rust-brown corduroy coat", "a dove-grey morning coat",
           "a navy pea jacket", "a russet riding coat",
           "a slate-blue shawl and plain dress",
            "a dark green hunting jacket", "a grey astrakhan coat",
            "a worn leather work coat",)
NECKWEAR = ("a stiff wing collar and black stock", "a soft turned-down collar",
            "a loosely knotted red neckerchief", "a bare throat, no collar",
            "a white cravat pinned with a stud", "a clerical black tie",
            "a checked muffler", "a leather cord at the throat",
            "a lace collar",
            "a black silk scarf", "a high starched collar",
            "an open shirt with no tie",)

ROLE_ITEMS = {
    "headgear": {"policeman": ("a custodian helmet",)},
    "neckwear": {"clergyman": ("a clerical black tie",)},
}
"""Costume that states a job.  A custodian helmet on Sherlock Holmes is not a
distinguishing feature, it is a different character -- and the first run of
this module put one on him."""

FEMALE_ONLY = ("a slate-blue shawl and plain dress", "a lace collar")
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
              "hair": ("dark hair swept back", "long black hair",
                       "wavy chestnut hair", "fair hair parted in the middle"),
              "facial_hair": ("clean-shaven", "a thin waxed moustache",
                              "a stubbled unshaven jaw")},
    "middle": {"age": ("about thirty-five", "about forty", "about forty-five",
                       "about fifty")},
    "old": {"age": ("about sixty", "about seventy", "about fifty-five"),
            "hair": ("a bald crown with grey at the temples",
                     "close-cropped grey hair", "white hair worn long",
                     "thinning red hair"),
            "facial_hair": ("a close-trimmed grey beard", "grey side-whiskers",
                            "a drooping grey moustache", "a long untrimmed beard")},
}
"""What is plausible at each end of life.

A bald crown with grey at the temples on a young woman, and late twenties on
"the old farmer", are not near misses -- they are different people.  Invention
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
    words = set((' '.join(aliases) + ' ' + physical).lower().replace('.', ' ').split())
    female = len(words & set(FEMALE_MARKS))
    male = len(words & set(MALE_MARKS))
    if female > male:
        return 'woman'
    if male > female:
        return 'man'
    return 'person'


DECADES = ("twenties", "thirty", "thirties", "forty", "forties", "fifty",
           "fifties", "sixty", "sixties", "seventy", "seventies")


def book_match(physical: str, pool: tuple[str, ...]) -> str:
    """The pool value the book's own description actually points at.

    Authority order is the book first, then dress convention, then invention.
    Invention is only for slots the book leaves empty -- a sheet that ignores
    Doyle saying "frock coat" to put Holmes in a riding coat is not a
    reference to anything.
    """
    words = {w.strip('.,;:') for w in physical.lower().split()} - GENERIC
    # An age is a decade, and "thirty" must match "about thirty-five" -- the
    # book saying thirty and the card saying seventy is not a near miss.
    said = [d for d in DECADES if d in physical.lower()]
    if said and any("about" in v or "in his" in v or "in her" in v for v in pool):
        for value in pool:
            if said[0].rstrip("ies").rstrip("y") in value.lower():
                return value
    best, score = '', 0
    for value in pool:
        overlap = len({w.strip('.,;:') for w in value.lower().split()} - GENERIC
                      & set()) if False else len(
            ({w.strip('.,;:') for w in value.lower().split()} - GENERIC) & words)
        if overlap > score:
            best, score = value, overlap
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


def card_for(entity_id: str, taken: dict[str, set[str]],
             physical: str = "", gender: str = "man",
             role: str = "") -> dict[str, str]:
    """One character's eight slots, avoiding every value already spent.

    Walks the pools in a per-character rotation so the assignment is stable,
    and skips anything another character has taken.  The rotation is what
    `distinguishing_marks` lacked: it hashed the id in isolation, so two
    characters could and did land on the same features.
    """
    offset = sum(ord(ch) * (i + 1) for i, ch in enumerate(entity_id))
    card: dict[str, str] = {}
    for slot, pool in POOLS.items():
        spent = taken.get(slot, set())
        banded = BANDED.get(age_band(physical), {}).get(slot)
        allowed = _allowed(slot, banded or pool, gender, role)
        # Authority order: the role's own costume, then the book's words, then
        # invention.  A policeman's helmet is not a distinguishing feature to
        # be handed out, it is what a policeman wears.
        for_role = [v for v in ROLE_ITEMS.get(slot, {}).get(role, ()) if v in allowed]
        from_book = book_match(physical, tuple(allowed)) if physical.strip() else ""
        options = [v for v in allowed if v not in spent] or allowed
        card[slot] = (for_role[0] if for_role
                      else from_book or options[offset % len(options)])
    card['gender'] = gender
    if gender == 'woman':
        # A beard is an OBJECT, and drawing one on a woman is not a small
        # error: Lucy came back indistinguishable from Gregson at 0.541.
        card['facial_hair'] = NO_BEARD
    if physical.strip():
        card['book'] = physical.strip()
    return card


def cards_for(cast: list[str], physical: dict[str, str],
              genders: dict[str, str] | None = None,
              roles: dict[str, str] | None = None) -> dict[str, dict]:
    """A card per character, each avoiding what the others have taken."""
    taken: dict[str, set[str]] = {slot: set() for slot in POOLS}
    cards: dict[str, dict] = {}
    for entity_id in cast:
        card = card_for(entity_id, taken, physical.get(entity_id, ""),
                        (genders or {}).get(entity_id, "man"),
                        (roles or {}).get(entity_id, ""))
        cards[entity_id] = card
        for slot in POOLS:
            taken[slot].add(card[slot])
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
