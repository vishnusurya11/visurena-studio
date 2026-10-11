"""A look's words cut into LAYERS, and the closed-vocabulary MARKERS read off them.

Retro 2026-10-10 (A §5 cause 4): the narrator's row was his dossier body
("Dark brown hair ... shaven cheeks and chin") plus his ch22 look ("ash-grey
... sixteen days of grey-brown beard").  A row with two heads lets every gate
that reads it allow both, and the drawer gets both.  So the text is cut into
clauses, each clause given a layer by its own words (a clause with none
continues the clause before it in the same sentence), and:

  * the body keeps no head layer the look restates (`row_text`);
  * the look's restated head is written FIRST -- a detail buried
    mid-sentence is dropped (SKILL: Pictures);
  * a look that restates nothing leaves the row byte-for-byte as it was.

Markers are what the judges compare, never prose (`studio.continuity_spec`).
"""
from __future__ import annotations

import re
from typing import NamedTuple

HEAD = ("hair", "face", "headwear")
"""The head layers, in the order a row writes them: the ones that lost to the sheet."""

WORDS = {
    "headwear": re.compile(r"\b(?:hats?|hatless|bare-?headed|boater|bowler|derby|cap|bonnet|helmet|"
                           r"hood|turban|deerstalker|top-hat|toque)\b", re.I),
    "face": re.compile(r"\b(?:beard\w*|m(?:ou|u)stach\w*|whiskers?|side-?whiskers|(?:clean-)?shaven|"
                       r"stubble|goatee|sideburns?|gaunt)\b", re.I),
    "hair": re.compile(r"\b(?:hair|haired|bald\w*|curls?|ringlets|plaits?|forelock)\b", re.I),
}
SENTENCE = re.compile(r"(?<=[.!?])\s+")
SPLIT = re.compile(r"(;\s*|,\s+)")


class Clause(NamedTuple):
    layer: str
    text: str
    sep: str


class Sentence(NamedTuple):
    clauses: list[Clause]
    end: str


def layer_of(clause: str) -> str:
    """The head layer a clause's own words name, or '' when it names none."""
    return next((name for name in ("headwear", "face", "hair") if WORDS[name].search(clause)), "")


def sentence_of(text: str) -> Sentence:
    """One sentence cut into clauses; a clause naming no layer continues the last."""
    end = text[-1] if text[-1:] in ".!?" else ""
    bits = SPLIT.split(text[:len(text) - len(end)])
    out, layer = [], "rest"
    for i in range(0, len(bits), 2):
        layer = layer_of(bits[i]) or layer
        out.append(Clause(layer, bits[i], bits[i + 1] if i + 1 < len(bits) else ""))
    return Sentence(out, end)


def parse(text: str) -> list[Sentence]:
    return [sentence_of(s) for s in SENTENCE.split((text or "").strip()) if s.strip()]


def render(sentences: list[Sentence]) -> str:
    """The sentences back as prose; a sentence keeps its own separators and end."""
    out = []
    for s in sentences:
        body = "".join(c.text + c.sep for c in s.clauses[:-1]) + s.clauses[-1].text
        out.append(body.rstrip(",; ") + s.end)
    return " ".join(out)


def keep(sentences: list[Sentence], wanted) -> list[Sentence]:
    """Only the clauses whose layer `wanted(layer)` accepts; empty sentences go."""
    kept = [Sentence([c for c in s.clauses if wanted(c.layer)], s.end) for s in sentences]
    return [s for s in kept if s.clauses]


def layers_in(sentences: list[Sentence]) -> set[str]:
    return {c.layer for s in sentences for c in s.clauses}


def body_of(physical: str) -> str:
    """The invariant body: the dossier's physical with no hair, beard or hat."""
    return render(keep(parse(physical), lambda layer: layer not in HEAD))


def head_first(look: list[Sentence], layers: list[str]) -> str:
    """The look's clauses of `layers`, hair first, as one leading sentence."""
    parts = [c.text.strip() for name in layers for s in look for c in s.clauses if c.layer == name]
    text = "; ".join(parts)
    return (text[:1].upper() + text[1:] + ".") if text else ""


def restates(look: list[Sentence], name: str) -> bool:
    """Does the look's own `name` layer state a marker?  'Hair matted' says
    nothing about colour, so the body's dark brown stands."""
    words = render(keep(look, lambda layer: layer == name)) if name in layers_in(look) else ""
    return bool(words) and bool(first_of(TABLES[name], words))


def row_text(physical: str, worn: str) -> str:
    """A row's `physical`: ONE head.  The look's restated head layers lead and
    replace the body's; a look restating none keeps the old bytes."""
    body, look = parse(physical), parse(worn)
    replaced = [name for name in HEAD if name in layers_in(body) and restates(look, name)]
    if not replaced:
        return f"{physical.strip()} Wearing: {worn.strip()}" if worn.strip() else physical.strip()
    lead = head_first(look, replaced)
    rest = render(keep(look, lambda layer: layer not in replaced))
    kept = render(keep(body, lambda layer: layer not in replaced))
    return " ".join(p for p in (lead, kept, f"Wearing: {rest}" if rest else "") if p)


def layer_text(physical: str, worn: str, name: str) -> str:
    """One layer's words: the look's when it states a marker, else the body's."""
    look = parse(worn)
    if restates(look, name):
        return render(keep(look, lambda layer: layer == name))
    return render(keep(parse(physical), lambda layer: layer == name))


HEADWEAR = (("none", r"hatless|bare-?headed"), ("boater", r"boater|straw hat"), ("bowler", r"bowler|derby"),
            ("top_hat", r"top-?hat|silk hat"), ("felt_hat", r"felt hat"), ("cap", r"\bcap\b"),
            ("bonnet", r"bonnet"), ("helmet", r"helmet"), ("hood", r"\bhood\b"), ("other_hat", r"\bhats?\b"))
HAIR = (("grey", r"gr[ae]y|silver"), ("white", r"white"), ("bald", r"bald"),
        ("red", r"\bred\b|ginger|auburn|copper"), ("fair", r"fair|blond|flaxen|golden|tow"),
        ("dark", r"dark|black|raven"), ("brown", r"brown|chestnut"))
FACIAL = (("beard", r"beard"), ("moustache", r"m(?:ou|u)stach|whisker"), ("stubble", r"stubble"),
          ("none", r"shaven|beardless"))
TOP = (("shirtless", r"shirtless|bare to the waist|naked"), ("dress", r"\bdress\b|gown|frock"),
       ("uniform", r"uniform|tunic"), ("nightshirt", r"nightshirt|nightgown"),
       ("suit_jacket", r"\bsuit\b|jacket"), ("coat", r"\bcoat\b|overcoat|greatcoat|cape|cloak"),
       ("waistcoat", r"waistcoat"), ("shirt", r"\bshirt|blouse|shirtsleeves"))
DIRT = (("bloodied", r"blood"), ("sooted", r"soot|smoke|blackened"),
        ("muddy", r"\bmud|\bclay\b|\bearth\b|slime"), ("dusty", r"\bdust|plaster|grit"),
        ("wet", r"soaked|\bwet\b|drenched|dripping"))


TABLES = {"headwear": HEADWEAR, "hair": HAIR, "face": FACIAL}


def first_of(table, text: str) -> str:
    """The first marker of a closed table whose pattern the text matches, or ''."""
    return next((marker for marker, pattern in table if re.search(pattern, text or "", re.I)), "")


def markers_of(physical: str, worn: str) -> dict[str, str]:
    """The row's markers: one head (the look's layer, else the body's), the
    look's top garment, and the look's dirt."""
    top = render(keep(parse(worn), lambda layer: layer not in HEAD))
    return {"headwear": first_of(HEADWEAR, layer_text(physical, worn, "headwear")),
            "hair_colour": first_of(HAIR, layer_text(physical, worn, "hair")),
            "facial_hair": first_of(FACIAL, layer_text(physical, worn, "face")),
            "top": first_of(TOP, top), "dirt": first_of(DIRT, worn)}


HAIR_FAMILY = {"dark": "dark", "brown": "dark", "grey": "grey", "white": "grey",
               "fair": "fair", "red": "red", "bald": "bald"}
"""Hair colours a reader confuses are one family: dark brown is read 'brown'
or 'dark', ash-grey is read 'grey' or 'white'."""
SEEN_HAIR = re.compile(r"\b([a-z-]+)[- ]haired\b|\b([a-z-]+) hair\b|\bbald\b", re.I)


def seen_hair(said: str) -> str:
    """The hair colour family a reader's list names, '' when it names none."""
    for m in SEEN_HAIR.finditer(said or ""):
        colour = first_of(HAIR, m.group(0))
        if colour:
            return HAIR_FAMILY[colour]
    return ""


HEADWEAR_FAMILY = {"felt_hat": "brimmed", "other_hat": "brimmed"}
"""Hats a reader confuses are one family: it names a battered felt hat
`other_hat` 7 times in 8 (C2_verdict #4).  Every other marker, bowler included,
is its own family until real bowler looks have been read (H7)."""


def family(key: str, marker: str) -> str:
    """The family LOOK-STATE and G-LOOK-PANEL compare: hair colour and headwear
    by family, every other marker as itself."""
    table = {"hair_colour": HAIR_FAMILY, "headwear": HEADWEAR_FAMILY}.get(key, {})
    return table.get(marker, marker)
