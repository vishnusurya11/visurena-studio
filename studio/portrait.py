"""The book's own portrait of a character, read off the SOURCE text.

THE RULE: a card's authority is the book first, then dress convention, then
invention (`cast_card`).  "The book" was `profile.physical`, the dossier's
prose about scenes -- and for Holmes it said "limited physical description"
while chapter 2 says over six feet, excessively lean, a thin hawk-like nose.
The card invented white hair and a full beard on top of it.

A portrait paragraph rarely names its subject: Doyle writes "he", and names
Gregson only in the paragraph after his portrait.  So the candidates are the
paragraphs around the first appearance that name the person or sit next to
one that does, and carry a word about looks.  The model
quotes the sentences about this one person; a quote that is not verbatim in
those paragraphs is refused, and a slot with no sentence behind it is
invention, not reading.  Silence is an honest answer: the dossier stays.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, model_validator

from studio import llm

TIER = "reasoning"
SPAN = 3
"""Chapters read from the first appearance on: the portrait comes early."""
CAP = 12
"""Paragraphs at most, so a long chapter is a few thousand tokens, not a book."""
LOOK = ("hair", "haired", "beard", "bearded", "moustache", "whiskers", "whiskered", "shaven",
        "tall", "short", "lean", "thin", "stout", "gaunt", "burly", "slim", "slender", "portly",
        "face", "faced", "eyes", "eyed", "nose", "chin", "brow", "cheek", "complexion",
        "sallow", "pale", "ruddy", "swarthy", "flaxen", "grey", "gray", "white", "dark",
        "hat", "cap", "bonnet", "coat", "dressed", "clad", "years", "elderly", "young",
        "old", "aged", "feet", "height", "figure", "frame", "built", "handsome", "plain")
SLOTS = ("age", "hair", "facial_hair", "headgear", "build", "complexion")


class Passage(BaseModel):
    chapter: int
    n: int
    text: str


class Portrait(BaseModel):
    sentences: list[str] = []
    """Verbatim sentences from the passages about how THIS person looks."""
    age: str = ""
    hair: str = ""
    facial_hair: str = ""
    headgear: str = ""
    build: str = ""
    complexion: str = ""

    @model_validator(mode="after")
    def _no_slot_without_a_sentence(self):
        if not self.sentences and any(getattr(self, slot) for slot in SLOTS):
            raise ValueError("a trait with no sentence behind it is invention")
        return self


RELATIONAL = ("my ", "his ", "her ", "our ", "their ", "your ")
"""An alias by relation to the speaker names whoever the speaker is with:
Watson's 'my companion' is Holmes in every paragraph Watson narrates, and
Watson's portrait came back six feet and hawk-nosed (Scarlet, 2026-09-04)."""


def names_of(character: dict) -> list[str]:
    """The name and its aliases, longest first so 'Mr. Holmes' wins over 'Holmes'."""
    name = character.get("name", "")
    names = {name, surname(name), *character.get("aliases", [])}
    return sorted((n for n in names if len(n) >= 3 and not n.lower().startswith(RELATIONAL)),
                  key=len, reverse=True)


def surname(name: str) -> str:
    """The capitalised last word, four letters or more: the analysis lists
    'Dr. Watson' and never 'Watson', and Stamford calls him 'Watson'."""
    last = name.split()[-1] if name.split() else ""
    return last if len(last) >= 4 and last[0].isupper() and last.isalpha() else ""


def mentions(text: str, names: list[str]) -> bool:
    if not names:
        return False
    pattern = "|".join(re.escape(n) for n in names)
    return re.search(rf"(?<![A-Za-z]){pattern}(?![A-Za-z])", text) is not None


def looks(text: str) -> bool:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return bool(words & set(LOOK))


def candidates(chapters: list[dict], names: list[str], first_chapter: int,
               span: int = SPAN, cap: int = CAP) -> list[Passage]:
    """Paragraphs about looks that name the person or sit next to one that does:
    Doyle's Holmes is 'he' the paragraph after his name, his Gregson is 'a
    tall, white-faced, flaxen-haired man' the paragraph before."""
    found: list[Passage] = []
    for chapter in chapters:
        if not first_chapter <= chapter["n"] < first_chapter + span:
            continue
        paras = chapter["paragraphs"]
        named = [mentions(p["text"], names) for p in paras]
        for i, para in enumerate(paras):
            around = named[max(i - 1, 0):i + 2]
            if any(around) and looks(para["text"]):
                found.append(Passage(chapter=chapter["n"], n=para["n"], text=para["text"]))
    return found[:cap]


def _plain(text: str) -> str:
    """Straight quotes, single spaces: the model's copy is not the typesetter's."""
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    return " ".join(text.split())


def verify(found: Portrait, passages: list[Passage]) -> Portrait:
    """The portrait, or ValueError naming the first sentence not in the book."""
    book = _plain(" ".join(p.text for p in passages))
    for sentence in found.sentences:
        if _plain(sentence) not in book:
            raise ValueError(f"not in the book: {sentence[:80]!r}")
    return found


def prompt_for(name: str, passages: list[Passage], violation: str | None = None) -> str:
    slots = ", ".join(SLOTS)
    text = "\n\n".join(f"[ch {p.chapter} para {p.n}] {p.text}" for p in passages)
    head = (f"From the passages below, quote every sentence that describes how {name} "
            f"LOOKS -- face, hair, build, age, dress -- verbatim, unchanged.  Only sentences "
            f"about {name}; other people in the same paragraph are not {name}.  Then fill "
            f"{slots} with a short phrase each, ONLY where a quoted sentence says so; leave "
            f"a slot empty when the book is silent.  Never infer from period or reputation.")
    if violation:
        head += f"\nYour last answer was refused: {violation}.  Quote exactly."
    return f"{head}\n\n{text}"


def ask(character: dict, chapters: list[dict], tries: int = 2) -> Portrait:
    """The portrait the book gives, or an empty one when it gives none.

    Retry within the frame, then degrade and ship: two foreign quotes and the
    book is treated as silent, which the dossier then covers."""
    passages = candidates(chapters, names_of(character), int(character.get("first_chapter") or 1))
    if not passages:
        return Portrait()
    name, violation = character.get("name", character.get("id", "")), None
    for _ in range(tries):
        try:
            return verify(llm.structured(TIER, prompt_for(name, passages, violation), Portrait),
                          passages)
        except ValueError as refused:
            violation = str(refused)
    return Portrait()


def load_chapters(book_dir) -> list[dict]:
    """The source chapters in order; none when the book has no source on disk."""
    folder = Path(book_dir) / "source/chapters"
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json"))]


def portraits_for(book_dir, characters: dict[str, dict]) -> dict[str, Portrait]:
    """One portrait per character, asked once per book and kept in refs/portraits.json."""
    path = Path(book_dir) / "refs/portraits.json"
    kept = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    chapters = None
    for char_id, doc in characters.items():
        if char_id not in kept:
            chapters = load_chapters(book_dir) if chapters is None else chapters
            if not chapters:
                return {c: Portrait() for c in characters}
            kept[char_id] = ask(doc, chapters).model_dump()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding="utf-8")
    return {c: Portrait(**kept[c]) for c in characters}


def readings(slot: str, phrase: str) -> dict[str, str]:
    """What the model reads a phrase as, per trait the slot carries."""
    from studio import describe, distinguish
    read = {}
    for trait in distinguish.SLOT_TRAITS.get(slot, ()):
        try:
            read[trait] = describe.nearest(trait, phrase)
        except ValueError:
            pass
    return {trait: value for trait, value in read.items() if value != "unclear"}


def snap(slot: str, phrase: str) -> str:
    """The book's words when the model reads them whole, else the pool phrase
    that reads the same, else nothing.

    Gregson is 'flaxen-haired'; a card that draws its hair from the rotation
    says 'dark hair swept back' beside the quoted sentence, and the model
    obeys whichever it likes (run 6).  A phrase the vocabulary cannot read
    states nothing: the fidelity gate reads every card slot, and 'frightened
    face' is not a complexion.  Build has no reading and is kept as written;
    an age is always the pool's, the card says 'A man {age}'."""
    from studio import cast_card, distinguish
    traits = distinguish.SLOT_TRAITS.get(slot, ())
    if not traits:
        return phrase
    # Lucy: 'fair face, cheek more ruddy, pale-faced' -- three readings in one
    # slot is no reading.  The first phrase the model reads is the card.
    phrase, read = next(((part, readings(slot, part)) for part in
                         (p.strip() for p in phrase.split(",")) if readings(slot, part)), ("", {}))
    if not read:
        return ""
    if len(read) == len(traits) and slot != "age":
        return phrase
    options = [option for option in cast_card.POOLS[slot]
               if all(distinguish.coarse(slot, option, t) == v for t, v in read.items())]
    words = set(re.findall(r"[a-z]+", phrase.lower()))
    return max(options, key=lambda o: len(words & set(re.findall(r"[a-z]+", o))), default="")


def stated(found: Portrait) -> dict[str, str]:
    """The card slots the book itself fills."""
    snapped = {slot: snap(slot, getattr(found, slot).replace(";", ","))
               for slot in SLOTS if getattr(found, slot)}
    return {slot: phrase for slot, phrase in snapped.items() if phrase}


def physical_text(found: Portrait, dossier: str) -> str:
    """What the card reads as 'the book': its sentences, else the dossier."""
    return " ".join(found.sentences) if found.sentences else dossier
