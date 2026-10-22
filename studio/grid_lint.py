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

grids.py runs it as a hard wall before any grid is posted (and in --prompts).

`warnings` never refuses (craft ruling 2026-10-21):
  NEG   a no / not / never / without outside UNWRITTEN: the grid samples at cfg 1.0, the negative
        prompt is never read, and a negated noun is still that noun to the drawer (A20);
  LONG  a prompt over LONG_WORDS words (A22).
"""
from __future__ import annotations

import re

from studio.storyboard_grid import PHYSIQUE, UNWRITTEN

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


def faults(text: str, nouns: dict[int, str] | None = None, names: list[str] | None = None) -> list[str]:
    """Every fault in one grid prompt; [] is clean.  `nouns` {slot: man|woman|girl|boy},
    `names` the book's name tokens an unstaged line may not carry."""
    out = p14(text) + p15(text, names or []) + p16(text, nouns or {}) + wears(text)
    out += [f"CASE garbled capital {m.group(0)!r}" for m in CASE.finditer(text)]
    out += [f"CURE glued as a noun phrase: {m.group(0)!r}" for m in CURE.finditer(text)]
    out += [f"SLOT bracketed description after a slot at {m.start()}" for m in SLOT.finditer(text)]
    return out


NEGATION = re.compile(r"\b(?:no|not|never|without)\b(?:\s+[\w'-]+){0,2}", re.I)


def negations(text: str) -> list[str]:
    """Each negation with the two words after it, the fixed UNWRITTEN sentence aside."""
    return [m.group(0) for m in NEGATION.finditer(text.replace(UNWRITTEN, " "))]


LONG_WORDS = 350
"""A22: the word count a grid prompt is named over (ep01 ran 408-1,064, median 470; Qwen's own
rewriter writes under 200).  A warning: the 1,000-token refusal was an unmeasured vendor number."""


def warnings(text: str) -> list[str]:
    """What the lint names and never refuses; [] says nothing."""
    said, n = negations(text), len(text.split())
    out = [f"NEG {len(said)} negations the drawer reads as nouns (cfg 1.0 reads no negative): "
           + ", ".join(repr(x) for x in said)] if said else []
    return out + ([f"LONG {n} words, over the {LONG_WORDS}-word line"] if n > LONG_WORDS else [])
