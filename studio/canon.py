"""The look the world already knows a character by.

`cast_card` is built on the rule that a model draws OBJECTS, and invents an
object only for a slot the book leaves empty.  The rule has a hole: the book
is silent about the face of Sherlock Holmes because in 1887 nobody needed
telling, and the audience of a trailer has seen that face ten thousand times.
Silence in the text is not licence.  The rotation gave Holmes a walrus
moustache, a brown bowler and forty years (Scarlet run 7), and the run before
it white hair worn long -- a different man, with every clip conditioned on him.

Authority order, corrected: the book's own words (`portrait`), then the
character's KNOWN look (this module), then dress convention, then invention.
The known look is asked of the model once per character in the card's own
closed vocabulary, so a slot is a pool phrase or empty; `known` is false for
anyone without a public face, and then nothing changes -- invention stays
for the Stamfords.  The slots it fills are `stated`, so a render OWES them
and a sheet that draws a beard on Holmes is refused, not shipped.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, model_validator

from studio import cast_card, llm
from studio.portrait import SLOTS, readings, stated

TIER = "canon"
"""The model that knows the canon, thinking: measured 2026-09-04, luna at effort
none agreed with itself three times on a bearded, sandy, forty-five-year-old
Watson; at high it gave the late-twenties moustached one three of three."""
ASKS = 3
"""Measured on Watson (2026-09-05): a short pointed beard, then nothing, then
a thin waxed moustache -- the model was guessing, and one guess would have
been asserted on every clip.  Holmes came back clean-shaven, dark, late
twenties three times of three.  Agreement is what knowledge looks like from
outside; a slot the asks disagree on is left empty."""


class Canon(BaseModel):
    known: bool = False
    """Whether a faithful adaptation is expected to keep this face."""
    source: str = ""
    """Where the look comes from: the wider canon, its illustrators, a century of depiction."""
    age: str = ""
    hair: str = ""
    facial_hair: str = ""
    headgear: str = ""
    build: str = ""
    complexion: str = ""

    @model_validator(mode="after")
    def _unknown_carries_nothing(self):
        if not self.known and any(getattr(self, slot) for slot in SLOTS):
            raise ValueError("a look for a character nobody knows is invention")
        return self


def prompt_for(character: dict, book: dict) -> str:
    """Closed vocabulary, the time of this book, and permission to say no."""
    name = character.get("name", character.get("id", ""))
    aliases = ", ".join(a for a in character.get("aliases", []) if a != name)
    also = f" (also called {aliases})" if aliases else ""
    pools = "\n".join(f"  {slot}: {' | '.join(cast_card.POOLS[slot])}"
                      for slot in SLOTS if slot in cast_card.POOLS)
    return (f"{name}{also} is a character in \"{book.get('title', '')}\" by "
            f"{book.get('author', '')}.  Does this character have a widely recognised "
            f"appearance -- from the author's other works, from illustrations that became "
            f"canonical, or from a long history of faithful depiction -- that a reader would "
            f"expect an adaptation to keep?  If not (a minor figure, a face no tradition "
            f"fixed, a name you are not certain of), answer known=false and leave every "
            f"slot empty.  If so, give the look AT THE TIME OF THIS BOOK: for each slot pick "
            f"exactly one phrase from its list, or leave it empty where the tradition is "
            f"silent or varies; `build` is a few words of your own.  Name where the look "
            f"comes from in `source`.\n{pools}")


def _reading(slot: str, phrase: str) -> tuple:
    """What a phrase says, so 'bare head' and 'a bare head' agree."""
    if not phrase:
        return ()
    read = readings(slot, phrase)
    return tuple(sorted(read.items())) if read else (phrase.lower(),)


def _majority(slot: str, answers: list[Canon]) -> str:
    """The phrase most answers read the same way, when more than half do."""
    said = [_reading(slot, getattr(a, slot)) for a in answers]
    best = max(set(said), key=said.count)
    if said.count(best) * 2 <= len(answers) or not best:
        return ""
    return next(getattr(a, slot) for a in answers if _reading(slot, getattr(a, slot)) == best)


def agree(answers: list[Canon]) -> Canon:
    """One look from several asks: known by majority, each slot by majority
    reading, build and source from the first answer that knows."""
    knowing = [a for a in answers if a.known]
    if len(knowing) * 2 <= len(answers):
        return Canon()
    slots = {slot: _majority(slot, answers) for slot in SLOTS if slot != "build"}
    return Canon(known=True, source=knowing[0].source, build=knowing[0].build, **slots)


def _one(character: dict, book: dict) -> Canon:
    """A single answer; an invalid one is not knowing."""
    try:
        return llm.structured(TIER, prompt_for(character, book), Canon)
    except Exception:
        return Canon()


def ask(character: dict, book: dict) -> Canon:
    """The look ASKS independent answers agree on."""
    return agree([_one(character, book) for _ in range(ASKS)])


def load_book(book_dir) -> dict:
    """Title and author from the source metadata; empty when the book has none."""
    path = Path(book_dir) / "source/book.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def canons_for(book_dir, characters: dict[str, dict]) -> dict[str, Canon]:
    """One known look per character, asked once per book and kept in refs/canon.json."""
    path = Path(book_dir) / "refs/canon.json"
    kept = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    book = None
    for char_id, doc in characters.items():
        if char_id not in kept:
            book = load_book(book_dir) if book is None else book
            if not book:
                return {c: Canon() for c in characters}
            kept[char_id] = ask(doc, book).model_dump()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding="utf-8")
    return {c: Canon(**kept[c]) for c in characters}


def known_look(look: Canon) -> dict[str, str]:
    """The card slots the known look fills, in pool phrases; nothing for a stranger."""
    return stated(look) if look.known else {}
