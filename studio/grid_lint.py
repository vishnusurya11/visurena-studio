"""The grid prompt lint: deterministic, $0, regex and set logic only.

Every rule is a class the Jekyll ep01 audit found in a DRAWN grid prompt
(docs/audit/2026-10-15_jekyll_ep01_ref_audit/02_prompts.md, P14-P16, G1-G5):

  P14   "picture" standing for the door's panels ("a match on the picture of the
        blistered door", "its picture streaked black"): a door "picture" grows a
        painting or a placard;
  P15   an unstaged person pasted as his raw dossier row after "In it:", or said
        by a line that is long or names somebody else (the doctor, Utterson);
  P16   a woman, a girl or a boy said as "the person in <imageN>";
  CASE  a lowered first letter of an upper-case word ("tHE FOCUS");
  CURE  a cure sentence glued in as a noun phrase ("opens on only the named");
  WEARS a body word in a "wears:" list ("compact; upright; heavy jaw");
  SLOT  a bracketed description after a slot ("<image1> (light-brown top hat)"):
        the sheet and its wears line are the one description.

Craft ruling A21 (2026-10-21), each a class the builder no longer writes:
  ROOM  "this exact room" on an outdoor setup;   WORN  a slot's coat named in the prose, absent from its
  "wears:" line;   STOP  a doubled full stop;   AIR  "thick with thin";   SHEET  "seen from several angles";
  TWIN  the walk-on clause counting the panel's own staged people;   FOCUS  a face filling the framing
  under a FOCUS that is no face.

grids.py runs it as a hard wall before any grid is posted (and in --prompts).

`warnings` never refuses (craft ruling 2026-10-21):
  NEG   a no / not / never / without outside UNWRITTEN: the grid samples at cfg 1.0, the negative
        prompt is never read, and a negated noun is still that noun to the drawer (A20);
  LONG  a prompt over LONG_WORDS words (A22).
"""
from __future__ import annotations

import re

from studio.storyboard_grid import DOUBLE_STOP, GROUP_COUNTS, PHYSIQUE, UNWRITTEN, face_focus

P14 = (re.compile(r"\b(?:door|door's|panels?|brown|blistered)\s+picture\b", re.I),
       re.compile(r"\bpicture\s+of\s+the\s+(?:\w+\s+){0,2}(?:door|panels?)\b", re.I),
       re.compile(r"\bpicture\s+(?:fill|streaked)\b", re.I))
RAW_ROW = re.compile(r"In it:[^\n]*?\ba [a-z][a-z .']+ \([^)]{80,}\)")
WHO_LINE = re.compile(r"In it: (.*?)\.[ \t]*$", re.M)
SAID_BY_SLOT = re.compile(r"(?:the hands of )?the \w+ in <image\d+>|the same \w+ again|\d+ unnamed .*")
META = re.compile(r"\b(?:described as|associated with|access to|residence|presented as|dossier|"
                  r"the child's father|doctor)\b", re.I)
PERSON = re.compile(r"\bthe person in <image(\d+)>", re.I)
CASE = re.compile(r"\b[a-z][A-Z]{2,}\b")
CURE = re.compile(r"\bopens on only the named\b", re.I)
WEARS = re.compile(r"\bwears: ([^\n]*?)\.(?:\s|$)")
SLOT = re.compile(r"<image\d+>\s*\(")
SHORT = 30


def p14(text: str) -> list[str]:
    return [f"P14 'picture' for a scene noun: {m.group(0)!r}" for rule in P14 for m in rule.finditer(text)]


def named_in(entry: str, names: list[str]) -> str:
    """The first name token or dossier phrase an entry carries, or ''."""
    if meta := META.search(entry):
        return meta.group(0)
    hits = (re.search(rf"\b{re.escape(n)}\b", entry, re.I) for n in names)
    return next((m.group(0) for m in hits if m), "")


def unstaged_fault(entry: str, names: list[str]) -> str:
    """Why a who-line entry with no slot is not a short layers line naming nobody, or ''."""
    if len(entry.split()) >= SHORT:
        return f"P15 unstaged line of {len(entry.split())} words: {entry[:60]!r}"
    if hit := named_in(entry, names):
        return f"P15 unstaged line names {hit!r}: {entry[:60]!r}"
    return ""


def p15(text: str, names: list[str]) -> list[str]:
    out = [f"P15 raw row after 'In it:': {m.group(0)[:80]!r}" for m in RAW_ROW.finditer(text)]
    for line in WHO_LINE.finditer(text):
        for entry in (e.strip() for e in line.group(1).split("; ")):
            if entry and not SAID_BY_SLOT.fullmatch(entry) and (why := unstaged_fault(entry, names)):
                out.append(why)
    return out


def p16(text: str, nouns: dict[int, str]) -> list[str]:
    return [f"P16 a {nouns[int(m.group(1))]} is 'the person in <image{m.group(1)}>'"
            for m in PERSON.finditer(text) if nouns.get(int(m.group(1))) in ("woman", "girl", "boy")]


def wears(text: str) -> list[str]:
    return [f"WEARS body word {hit.group(0)!r} in {m.group(1)[:60]!r}"
            for m in WEARS.finditer(text) if (hit := PHYSIQUE.search(m.group(1)))]


BOUND = re.compile(r"The \w+ in <image(\d+)> wears: ([^\n]*?)\.(?:\s|$)")
GARMENT = r"<image{n}>'s (?:[\w-]+ ){{0,2}}?(coat|overcoat|jacket|cloak|waistcoat)\b"
TWIN = re.compile(r"\bThe (\w+) (?:[\w ]*? )?(\w+) are \w+ different individuals\b")
GENERIC = {"men", "women", "people", "figures", "them"}
"""How the pair a panel stages is counted ("the two men"); "two constables" are walk-ons (`Shot.extras`)."""
FACE_FILL = re.compile(r"Framing: [^.\n]*\b(?:head and shoulders fill|the face fills|the eyes fill|the head sits)\b")
AIR = re.compile(r"\bthick with (?:an? )?thin\b", re.I)


def worn(text: str) -> list[str]:
    """WORN: a garment the prose gives a slot ("<image2>'s coat collar") that its wears line lacks."""
    return [f"WORN <image{m.group(1)}>'s {g} is named and not in its wears line" for m in BOUND.finditer(text)
            for g in dict.fromkeys(re.findall(GARMENT.format(n=m.group(1)), text)) if g not in m.group(2)]


def panel_faults(text: str, people: set[str] | None = None) -> list[str]:
    """TWIN and FOCUS, read one panel (paragraph) at a time."""
    out = []
    for para in text.split("\n\n"):
        staged = {n for n in re.findall(r"<image(\d+)>", para) if people is None or n in people}
        if (m := TWIN.search(para)) and 0 < GROUP_COUNTS.get(m.group(1).lower(), 99) <= len(staged) \
                and m.group(2).lower() in GENERIC:
            out.append(f"TWIN walk-on clause on the panel's own staged people: {m.group(0)!r}")
        if FACE_FILL.search(para) and not face_focus(para):
            out.append(f"FOCUS the framing fills with a face the FOCUS is not: {para[:48]!r}")
    return out


def wording(text: str, outdoors: bool = False) -> list[str]:
    """ROOM, STOP, AIR and SHEET (craft ruling A21)."""
    out = ["ROOM a place under the sky called 'this exact room'"] if outdoors and "this exact room" in text else []
    out += [f"STOP doubled full stop at {m.start()}" for m in DOUBLE_STOP.finditer(text)]
    out += [f"AIR oxymoron {m.group(0)!r}" for m in AIR.finditer(text)]
    return out + (["SHEET 'seen from several angles' on a one-figure crop"] if "seen from several angles" in text else [])


def faults(text: str, nouns: dict[int, str] | None = None, names: list[str] | None = None,
           outdoors: bool = False) -> list[str]:
    """Every fault in one grid prompt; [] is clean.  `nouns` {slot: man|woman|girl|boy},
    `names` the book's name tokens an unstaged line may not carry, `outdoors` the setup's."""
    out = p14(text) + p15(text, names or []) + p16(text, nouns or {}) + wears(text)
    out += [f"CASE garbled capital {m.group(0)!r}" for m in CASE.finditer(text)]
    out += [f"CURE glued as a noun phrase: {m.group(0)!r}" for m in CURE.finditer(text)]
    out += [f"SLOT bracketed description after a slot at {m.start()}" for m in SLOT.finditer(text)]
    people = {str(k) for k in nouns} if nouns else None
    return out + worn(text) + panel_faults(text, people) + wording(text, outdoors)


NEGATION = re.compile(r"\b(?:no|not|never|without)\b(?:\s+[\w'-]+){0,2}", re.I)


def negations(text: str) -> list[str]:
    """Each negation with the two words after it, the builder's fixed sentences aside (UNWRITTEN, the
    layout's lettering, the binding's dress: wave-2 review, NEG fired on 22 of 22 ep01 grids from them)."""
    return [m.group(0) for m in NEGATION.finditer(FIXED_NEG.sub(" ", text.replace(UNWRITTEN, " ")))]


FIXED_NEG = re.compile(r",? (?:with )?no lettering anywhere|are never dressed alike(?: and never wear the same hat, "
                       r"in any panel, without exception)?|and in no other panel\. A panel that names nobody has "
                       r"nobody in it")


LONG_WORDS = 350
"""A22: the word count a grid prompt is named over (ep01 ran 408-1,064, median 470; Qwen's own
rewriter writes under 200).  A warning: the 1,000-token refusal was an unmeasured vendor number."""


def warnings(text: str) -> list[str]:
    """What the lint names and never refuses; [] says nothing."""
    said, n = negations(text), len(text.split())
    out = [f"NEG {len(said)} negations the drawer reads as nouns (cfg 1.0 reads no negative): "
           + ", ".join(repr(x) for x in said)] if said else []
    return out + ([f"LONG {n} words, over the {LONG_WORDS}-word line"] if n > LONG_WORDS else [])
