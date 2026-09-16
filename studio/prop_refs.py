"""The OBJECT reference: the third kind, beside the character and the location.

A book already binds its people (`char-<id>.png`, an identity bust and a
wardrobe card) and its places (`loc-<id>.png`, plus an empty plate per setup).
Its THINGS were bound by nothing -- `Setup.props` only ever named another
SETUP whose plate got reused, so an object that is not also a location could be
described and never shown.

MEASURED on episode 2, which drew nine props from words alone across six
independent sheets:

    violin          0.36x   a child's fiddle under a six-foot jaw -- and drawn
                            correctly at 63 cm in panel 1 of the SAME sheet
    grey shawl      3.00x   asked "two hands long", hung to the knee
    fingerprint     2.90x   asked "a thumbnail wide", drawn a palm across
    stick shaft     1.95x
    pencil          2.60x   on thickness
    coffee pot      0.55x   and drifting 1.5x inside one sheet
    poker             --    drawn AS the walking stick in one panel

The controlled comparison is the blue envelope, the one prop in the episode with
a picture -- and only by accident, because the commissionaire's bust happens to
show it in his hand against his chest.  It came back at 1.25x over ten panels
and three sheets.

THE BRICK.  gpt-image copies APPEARANCE and never ABSOLUTE SIZE.  The only thing
in a photograph that carries absolute size is a human body.  So a prop reference
is the object HELD IN A HAND or standing AGAINST A FIGURE, never alone on a
table, and the contract states three measures -- one overall against the body,
one cross-section, one detail -- because "a walking stick" is an adjective and
23 panels each guessed a different size from it.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field, model_validator

from studio.affirm import negations
from studio.episode_spec import slow_word

SLUG = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")

BODY = re.compile(
    r"\b(hip|waist|shoulder|chest|knee|elbow|head|hand|hands|palm|thumb|thumbnail|finger|fingers|"
    r"forearm|wrist|arm|boot|foot|fist|knuckle|span|body|man|woman|torso|jaw|nail|"
    r"height|tall|long as|wide as|thick as|deep as)\b", re.I)
"""A measure only survives into a drawing if it is stated against a BODY.

"about ninety centimetres" means nothing to a model with no ruler, and the
episode 2 numbers show what happens: nine props measured in words landed between
0.36x and 3.0x.  Every measure here names a part of a person, or compares
against one."""

FIELDS = ("overall", "cross_section", "detail", "material", "sits", "words")


class Prop(BaseModel):
    """One object the book names, with the three measures that fix its size."""

    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    first_chapter: int = 0

    overall: str
    """How big the WHOLE thing is against a body: "stands hip high on a six-foot
    man and reaches a little over half his own height"."""
    cross_section: str
    """How thick or wide it is: "its shaft is as thick as one finger"."""
    detail: str
    """The one feature that identifies it, sized: "a polished silver ball knob
    the size of a plum caps it"."""

    material: str = ""
    sits: str = ""
    """Where it rests when nobody is using it, as a noun in a place."""
    held_by: str = ""
    """The character whose hand it belongs in, when it has one."""
    words: str = ""
    """The EXACT letters this object carries, verbatim, or "" for the silent
    majority.  The board's standing law is that every surface stays wordless,
    and it earned that law: gpt-image GENERATES lettering as a coin-flip -- one
    seed and one blank card gave us both "Number 3 Lauriston Gardens." and
    "Vinisitien of 3 Lauriston Gardens".

    What the same measurement shows is that PROPAGATION from an attached picture
    is near-lossless, 6 of 6.  So an object may carry words on exactly the terms
    every other prop carries its size: there is a picture of it, the picture is
    indexed, and the words are stated beside the index.  Filling this in without
    drawing `rel_path` is the one way to get CRISTERION back."""

    @model_validator(mode="after")
    def _the_three_measures_are_present(self) -> "Prop":
        for name in ("overall", "cross_section", "detail"):
            if not (getattr(self, name) or "").strip():
                raise ValueError(f"a prop states three measures; {name!r} is empty. "
                                 f"An adjective is not a size: 'a walking stick' came back "
                                 f"the size of a lamp post across 23 panels")
        return self

    @model_validator(mode="after")
    def _the_overall_measure_names_a_body(self) -> "Prop":
        if not BODY.search(self.overall):
            raise ValueError(f"the overall measure must be stated against a BODY, not in units: "
                             f"{self.overall!r}. A model has no ruler; nine props measured in words "
                             f"landed between 0.36x and 3.0x")
        return self

    @model_validator(mode="after")
    def _every_string_is_affirmative_and_unhurried_by_nothing(self) -> "Prop":
        for name in FIELDS:
            said = getattr(self, name)
            if bad := negations(said):
                raise ValueError(f"{name!r} asks for an absence ({bad}); name what is there instead")
            if word := slow_word(said):
                raise ValueError(f"{name!r} names a pace ({word!r}); a prop has a size, never a speed")
        return self

    @model_validator(mode="after")
    def _the_id_is_a_slug(self) -> "Prop":
        if not SLUG.match(self.id):
            raise ValueError(f"a prop id is a lowercase slug like 'walking_stick', got {self.id!r}")
        return self


def contract_sentence(prop: Prop) -> str:
    """The verbatim sentence every sheet and take repeats about this object.

    The same job `physical` does for a character: the reference pins the
    instance, the words pin the category, and dropping either one lets it
    drift."""
    parts = [prop.material, prop.overall, prop.cross_section, prop.detail, prop.sits]
    said = f"{prop.name}: " + "; ".join(p.rstrip(". ") for p in parts if p and p.strip()) + "."
    # the letters ride in `physical`, the ONE sentence both the sheet and the take
    # repeat -- anywhere else and they reach the board and not the render
    return said + f' It carries the words "{prop.words}", spelled exactly so.' if prop.words else said


PLAIN = ("A plain even grey studio backdrop fills the frame behind them, one flat wall, "
         "soft frontal light, photoreal 35 mm film still, sharp focus on the object.")


def reference_prompt(prop: Prop, palette: str) -> str:
    """The picture that binds this object's SIZE.

    A body is in the frame because a body is the only thing in a photograph that
    carries absolute scale.  Held in a hand where the object has an owner;
    standing against a figure where it does not."""
    hold = (f"A man's bare hand holds {prop.name} exactly as described, the whole hand in frame "
            f"beside it so its size reads against the fingers and the palm.")
    stand = (f"{prop.name[0].upper()}{prop.name[1:]} stands in the frame with a man's bare hand "
             f"open flat beside it at the same distance from the camera, so its size reads "
             f"against the hand.")
    return " ".join([contract_sentence(prop), hold if prop.held_by else stand,
                     "The object is the subject of the photograph and fills the middle of the frame.",
                     PLAIN, palette])


def refs_row(prop: Prop) -> dict:
    """The `refs.json` row, in the same shape a character and a location use."""
    return {"ref_id": f"prop-{prop.id}", "kind": "prop", "entity_id": prop.id,
            "name": prop.name, "physical": contract_sentence(prop),
            "rel_path": f"refs/props/prop-{prop.id}.png",
            "overall": prop.overall, "cross_section": prop.cross_section, "detail": prop.detail,
            "material": prop.material, "sits": prop.sits, "held_by": prop.held_by,
            "words": prop.words,
            "aliases": list(prop.aliases), "first_chapter": prop.first_chapter}


def prop_from_row(row: dict) -> Prop:
    """The inverse of `refs_row`.  A row keys the object by `entity_id`, the way a
    character and a location row do, so the id has to be mapped back on the way in
    -- and the row then re-validates against the contract, which is the point of
    reading it back at all."""
    fields = {k: v for k, v in row.items() if k in Prop.model_fields}
    fields["id"] = row.get("entity_id", row.get("id", ""))
    return Prop(**fields)


GENERIC = re.compile(r"^(?:the|a|an|his|her|its|their|my|your|our)\s+([a-z-]+)$", re.I)
"""An alias of one article-or-pronoun and one common noun names a CATEGORY.

MEASURED on episodes 8 and 9: "his hat" -- Jefferson Hope's, in a Utah parlour
-- attached Watson's brown bowler card off the 221B hat stand to two Utah
sheets, and "the shawl" attached the grey shawl from the same hat stand to
three alkali-plain crag sheets.  A hat any man could wear is not this hat."""

PLACES = ("sitting-room", "sitting room", "hat stand", "221b")
"""Places a prop's own description can keep it in.  A prop described as
hanging "on the mahogany hat stand beside the sitting-room door" belongs to no
sheet whose setup lacks that door."""


def distinctive(alias: str, row: dict) -> bool:
    """Does this alias name THE object rather than its category?

    Article + one noun is a category -- unless the noun is the object's own id
    ("the fingerprint", "the violin"): a book with one fingerprint has no
    category to confuse it with."""
    found = GENERIC.match((alias or "").strip())
    return not found or found.group(1).lower() == (row.get("entity_id") or "").lower()


def named_by(text: str, row: dict) -> str:
    """The name or alias of this row that the text uses, "" if none; the row's
    own name first, then its aliases in order."""
    low = (text or "").lower()
    for n in [row.get("name", "")] + list(row.get("aliases") or []):
        if n and re.search(r"(?<![a-z])" + re.escape(n.lower()) + r"(?![a-z])", low):
            return n
    return ""


def kept_elsewhere(row: dict, text: str, setup=None) -> str:
    """The place the row's description keeps this prop in, when neither the
    setup's description nor this text names it; "" when the place is here."""
    said = f"{row.get('sits', '')} {row.get('physical', '')}".lower()
    here = f"{getattr(setup, 'described', '') or ''} {text or ''}".lower()
    kept = [p for p in PLACES if p in said]
    return ", ".join(kept) if kept and not any(p in here for p in kept) else ""


def declared(row: dict, setup=None) -> bool:
    """Does the setup declare this prop by id or name?"""
    props = list(getattr(setup, "props", None) or [])
    return row.get("entity_id") in props or row.get("name") in props


def refusal(text: str, row: dict, setup=None) -> str:
    """Why this text does NOT attach this row, or "" when it does.

    The setup that declares the prop attaches it by any name.  Otherwise the
    name used has to be the object's own, and the object's own place has to be
    this place."""
    used = named_by(text, row)
    if not used or declared(row, setup):
        return ""
    if not distinctive(used, row):
        return (f"named only by {used!r}, a category and not this object; say a distinctive name "
                f"or declare {row.get('entity_id')} in Setup.props")
    if place := kept_elsewhere(row, text, setup):
        return f"its own description keeps it at the {place}, which this setup lacks"
    return ""


def props_in(text: str, rows: list[dict], setup=None) -> list[dict]:
    """The bound props this text names by a DISTINCTIVE name or alias, each once,
    in row order -- or by any name, when `setup.props` declares the prop.

    Read from the PROSE rather than from a declared list alone: `Setup.props`
    was `[]` on all six setups of episode 2 while its panels named nine objects
    between them, and a field that can disagree with the prose is exactly the
    fault the cast gate exists to catch.  `refusals` says what was left out."""
    return [row for row in rows if named_by(text, row) and not refusal(text, row, setup)]


def refusals(text: str, rows: list[dict], setup=None) -> list[tuple[dict, str]]:
    """Every row the text names and `props_in` leaves out, with the reason."""
    out = []
    for row in rows:
        if named_by(text, row) and (why := refusal(text, row, setup)):
            out.append((row, why))
    return out


def lettered(rows: list[dict]) -> list[dict]:
    """The rows that carry words, in row order.

    Kept apart from `props_in` because the two questions are different: that one
    asks WHICH objects this sheet shows, this one asks which of them the wordless
    law has to step aside for."""
    return [r for r in rows if (r.get("words") or "").strip()]


def undrawn(refs: list[dict], book) -> list[str]:
    """Every bible row whose picture is not on disk, said plainly.

    MEASURED, episode 7.  A `terrier` prop row was written into refs.json, and
    the note written beside it says why: "it appears alive, drinking and dead
    across three shots, so its identity has to hold like a character's."
    `refs/props/prop-terrier.png` was never drawn, and `seq_boards.draw_setup`
    filters the reference list by `.exists()` -- so the one prop whose identity
    was declared to need binding is the one prop that was dropped, on three
    paid sheets, without a word.

    The rule is narrow.  It does not ask that every prop have a reference; most
    do not need one.  It asks that a row SOMEBODY WROTE point at a file that is
    there.  Declaring a reference and not drawing it is never intentional."""
    from pathlib import Path

    book = Path(book)
    out = []
    for row in refs:
        rel = row.get("rel_path")
        if not rel:
            out.append(f"{row.get('entity_id', '?')} ({row.get('kind', '?')}) names no picture at all")
        elif not (book / rel).exists():
            out.append(f"{row.get('entity_id', '?')} ({row.get('kind', '?')}) declares {rel}, "
                       f"which is not on disk")
    return out
