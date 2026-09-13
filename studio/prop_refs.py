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

FIELDS = ("overall", "cross_section", "detail", "material", "sits")


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
    return f"{prop.name}: " + "; ".join(p.rstrip(". ") for p in parts if p and p.strip()) + "."


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
            "aliases": list(prop.aliases), "first_chapter": prop.first_chapter}


def prop_from_row(row: dict) -> Prop:
    """The inverse of `refs_row`.  A row keys the object by `entity_id`, the way a
    character and a location row do, so the id has to be mapped back on the way in
    -- and the row then re-validates against the contract, which is the point of
    reading it back at all."""
    fields = {k: v for k, v in row.items() if k in Prop.model_fields}
    fields["id"] = row.get("entity_id", row.get("id", ""))
    return Prop(**fields)


def props_in(text: str, rows: list[dict]) -> list[dict]:
    """The bound props this text names, by name or alias, each once, in row order.

    Read from the PROSE rather than from a declared list: `Setup.props` was `[]`
    on all six setups of episode 2 while its panels named nine objects between
    them, and a field that can disagree with the prose is exactly the fault the
    cast gate exists to catch."""
    low = (text or "").lower()
    out = []
    for row in rows:
        names = [row.get("name", "")] + list(row.get("aliases") or [])
        if any(n and re.search(r"(?<![a-z])" + re.escape(n.lower()) + r"(?![a-z])", low)
               for n in names):
            out.append(row)
    return out
