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
    """A reference sheet prompt, THE PERSON FIRST.

    Order matters more than content here.  With the style block leading, seven
    characters came back as the same Victorian gentleman: the palette and the
    period dominated, and the description trailing at the end barely
    registered.  Naming who this is before saying how to photograph them is
    what separates them.
    """
    return " ".join([physical.strip(), SHEET_FRAME, STYLE, palette, NO_TYPE])


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


CAPABILITY = re.compile(
    r"\b(?:is |are |was |were )?(?:able to|capable of|can|could)\b", re.I)
"""A capability is not an appearance.  Holmes shipped with 'able to travel
rapidly, conduct close physical examinations, follow a suspect, handcuff a
cabman' as his physical description -- four verbs and not one picture."""

NARRATION = re.compile(
    r"\b(?:while|during|after|before|then he|then she|and then)\b", re.I)
"""A sentence that places something in TIME is telling a story, and a reference
sheet is a single moment with no time in it."""

ACTION_VERB = re.compile(
    r"\b(?:pricks?|covers?|travels?|follows?|handcuffs?|restrains?|collects?"
    r"|breaks?|walks?|carries|carried|helps?|conducts?|examines?)\b", re.I)


def is_photographable(sentence: str) -> bool:
    """True when this sentence describes how someone LOOKS.

    Three refusals before the appearance test, because the appearance test is
    a bag of words and a bag of words cannot tell "he has dark hair" from "he
    followed the dark-haired man down the street".
    """
    clean = sentence.strip().rstrip(".")
    lowered = clean.lower()
    if not clean or any(lowered.startswith(o) for o in META_OPENERS):
        return False
    if any(word in lowered for word in ABSENCE):
        return False
    if CAPABILITY.search(clean) or NARRATION.search(clean) or ACTION_VERB.search(clean):
        return False
    return any(re.search(r"\b" + re.escape(w) + r"\b", lowered)
               for w in APPEARANCE)


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
        if not is_photographable(clean):
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
    """A visual brief: what the book calls someone, what it says, what they wore.

    Three layers, in decreasing order of authority -- the book's own epithets,
    its physical description where one exists, then period costume and
    invented distinguishing marks.  The last layer is there because four
    characters Stevenson never describes came back as one man four times, and
    an honest invention beats an accidental clone.
    """
    tags = epithets(character.get("aliases", []), character.get("name", ""))
    physical = visual_description((character.get("profile") or {}).get("physical", ""))
    lead = f"{character.get('name', 'A person')}, {', '.join(tags[:3])}." if tags else ""
    dress = costume_for(tags)
    # Invented marks are a FALLBACK, never an addition.  Appended to a real
    # description they contradict it -- Hyde is "a small young man" and got
    # "a short greying beard"; Lanyon is "noticeably balder" and got
    # "close-cropped black hair".  The book always wins where it speaks.
    marks = "" if physical else distinguishing_marks(
        character.get("id") or character.get("name", "x"))
    return " ".join(part for part in (lead, physical, dress, marks) if part).strip()


COSTUME: tuple[tuple[tuple[str, ...], str], ...] = (
    (("butler", "manservant", "valet", "footman"),
     "dressed in plain black household livery"),
    (("maid", "housemaid", "servant girl", "housekeeper", "cook"),
     "dressed in a plain dark servant's dress with a white apron and cap"),
    (("policeman", "officer", "constable", "inspector", "detective"),
     "in police uniform, a dark tunic with a high collar and custodian helmet"),
    (("lawyer", "solicitor", "attorney", "trustee", "notary"),
     "dressed in a sober black professional suit and high collar"),
    (("doctor", "physician", "surgeon", "medical"),
     "dressed in a good dark coat and waistcoat, a professional man"),
    (("murderer", "little man", "small man", "wanderer", "fugitive"),
     "in clothes that fit him badly, ill-kempt"),
    (("hunter", "trapper", "miner", "sailor", "labourer"),
     "in worn outdoor working clothes"),
)
"""Role to period DRESS -- clothing and nothing else.

Deliberately says nothing about hair, age or face, so it can be added to
a description the book supplies without contradicting it.

This is dress CONVENTION, not a claim about the text: a Victorian butler wore
livery whether or not his author mentions it.  It exists because character
COLLISION survived the epithets -- "the solemn butler" and "the lawyer" both
came back as the same gentleman in the same frock coat, since the style block
dominates and the epithet gave the model a role it did not translate into an
image.  Naming the clothes does translate.
"""


def costume_for(tags: list[str]) -> str:
    """The period dress implied by a character's epithets, if any."""
    joined = " ".join(tags).lower()
    for keywords, dress in COSTUME:
        if any(word in joined for word in keywords):
            return dress
    return ""


BUILDS = ("tall and spare", "short and heavy-set", "of middling height and thickset",
          "long-limbed and stooping", "compact and upright", "gaunt and narrow-shouldered")
HAIR = ("dark hair going grey at the temples", "thinning sandy hair",
        "a full head of iron-grey hair", "close-cropped black hair",
        "receding brown hair", "white hair swept back")
FACE = ("clean-shaven", "with full side-whiskers", "with a trimmed moustache",
        "with a short greying beard", "clean-shaven with a heavy jaw",
        "with bushy eyebrows and a lined face")


def distinguishing_marks(entity_id: str) -> str:
    """A stable, arbitrary set of features to tell same-role characters apart.

    Jekyll and Lanyon are both doctors, so costume alone leaves them identical.
    These are invented, and openly so -- the book supplies nothing, and two
    indistinguishable men on screen is a worse falsehood than two distinct
    invented ones.  Derived from the id so a character looks the same in the
    trailer, the song and the episode.
    """
    seed = sum(ord(ch) * (index + 1) for index, ch in enumerate(entity_id))
    return (f"{BUILDS[seed % len(BUILDS)]}, {HAIR[(seed // 7) % len(HAIR)]}, "
            f"{FACE[(seed // 13) % len(FACE)]}")


def all_locations(scenes: list[dict]) -> list[str]:
    """Every place the book goes, in order of first appearance.

     drew places from a SAMPLE of
    twelve scenes and then capped the result at eight.  A Study in Scarlet has
    thirteen and got six, which deleted 141 of its 411 authored setups --
    every one in Utah -- before any ranking ran.  A place with no plate cannot
    be bound, so no score can rescue it.

    A book has a finite number of places.  Plate all of them.
    """
    seen: list[str] = []
    for scene in scenes:
        where = (scene.get("slug") or {}).get("location_id")
        if where and where not in seen:
            seen.append(where)
    return seen
