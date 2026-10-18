"""A drawn picture read back against the nouns its own prompt asked for.

The rule `studio/panel_content.py` established, applied to a reference sheet:
the vision model is never asked whether the picture is right (a VLM says yes);
it is asked to LIST what it sees, and the comparison with the prompt's must-
appear nouns is done here, in code.  Which nouns a prompt asks for is a small
deterministic extraction -- the heads of the phrases after "with", "holding",
"wearing", "carrying", the thing a capitalised word qualifies ("Gladstone bag"
asks for a bag; "England," or "Royal Navy" asks for nothing -- a picture cannot
show a name), and any word of a MUST list the caller passes -- so the same
prompt always asks for the same things and a test can say so.

The first real bible (2026-09-25) listed 39 "missing" nouns that were all
names, countries and ranks; since then a name is no noun.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from pydantic import BaseModel

from studio import comfy
from studio.panel_content import stem, subject_list, truthy

WORKFLOW = "image_qwen3vl_caption"
TOKENS = 1024
SEED = 11

TRIGGER = re.compile(r"\b(?:with|holding|wearing|carrying)\s+", re.I)
"""What follows a trigger word, up to the next trigger or its clause's end, is a phrase; its first
comma part is the asked-for thing, unless that part opens an adjective series (`asked_part`)."""
ARTICLES = frozenset({"a", "an", "the", "his", "her", "their", "its", "one", "two", "some"})
WORD = re.compile(r"[a-z]+")
CAPITALISED = re.compile(r"^[A-Z][a-z]+$")
LOWER = re.compile(r"^[a-z]+$")
SMALL = ARTICLES | {"and", "or", "of", "in", "on", "at", "by", "to", "for", "from", "as", "is",
                    "was", "are", "with", "who", "that", "which"}
"""What can follow a name without being the thing it qualifies."""

ASK = (
    "List what is in this picture. Output strict JSON with these keys.\n"
    '"seen": a list of the things in the picture, each a short plain noun phrase, '
    "everything you can name, including anything unexpected.\n"
    '"text": true if any letters, words, numbers or captions appear anywhere, else false.'
)


class LookReading(BaseModel):
    """One picture against its prompt: what was seen, which asked nouns were not."""
    seen: list[str]
    missing: list[str]
    text: bool


class Unreadable(ValueError):
    """The reader said something this shape cannot hold.  It raises, never defaults."""


def bare(part: str) -> list[str]:
    return [w for w in WORD.findall(part.lower()) if w not in ARTICLES]


BODY = frozenset({"face", "jaw", "chin", "cheek", "hand", "eye", "lip", "mouth", "nose", "forehead", "brow",
                  "skin", "shoulder", "neck", "figure", "build", "frame", "body", "limb", "arm", "leg", "finger",
                  "knuckle", "teeth", "tooth", "feature"})
"""A person's own body is on every figure sheet and is never a must-noun: the reader lists 'man' and
called a drawn face and jaw absent (Jekyll Kawajiri 2026-10-18).  The face is the identity and
SHEET-ROW rows' to judge; the must-nouns are what a person wears and holds."""


def lone(text: str) -> bool:
    return len(WORD.findall(text.lower())) == 1


def adjective(conj: str, last: bool, more: bool, after_lone: bool) -> bool:
    """A conjunct that only qualifies a later noun: a bare lone word before another conjunct
    ("white and comely hands"), or a lone last word that opens or continues a comma series
    ("lean, corded, knuckly pale hands"; "a full, broad, smooth face")."""
    if not last:
        return lone(conj)
    return len(bare(conj)) == 1 and more and after_lone


def heads_in(phrase: str) -> list[str]:
    """The head nouns of one trigger phrase: its first comma part, walked on through an adjective
    series to the noun it qualifies (Jekyll Kawajiri 2026-10-18: 'lean' and 'full' were asked)."""
    parts, heads, series = [p for p in phrase.split(",") if p.strip()], [], False
    for i, part in enumerate(parts):
        conjs, carried = re.split(r"\band\b", part, flags=re.I), False
        more = i + 1 < len(parts)
        after_lone = series or (more and lone(parts[i + 1]))
        for j, conj in enumerate(conjs):
            if not bare(conj):
                continue
            if adjective(conj, j == len(conjs) - 1, more, after_lone):
                carried = carried or j == len(conjs) - 1
                continue
            heads.append(bare(conj)[-1])
        if not carried:
            break
        series = True
    return heads


def phrases(prompt: str) -> list[str]:
    """Each trigger's phrase: to the next trigger in its clause, else to the clause's end."""
    out = []
    for clause in re.split(r"[.;:]", prompt or ""):
        found = list(TRIGGER.finditer(clause))
        out += [clause[m.end():(found[i + 1].start() if i + 1 < len(found) else len(clause))]
                for i, m in enumerate(found)]
    return out


def phrase_heads(prompt: str) -> list[str]:
    """The head noun of every phrase after a trigger word, conjuncts split on 'and'."""
    return [head for phrase in phrases(prompt) for head in heads_in(phrase)]


def qualified(word: str, after: str | None) -> str | None:
    """The plain thing a capitalised word qualifies ("Gladstone bag" -> bag), or
    None: a name at a clause end, before another name or before a small word
    is a name, and a picture shows no names."""
    if not CAPITALISED.match(word.strip(",;:")) or word[-1] in ",;:" or after is None:
        return None
    after = after.strip(",;:")
    return after if LOWER.match(after) and after not in SMALL else None


def capitalised_nouns(prompt: str) -> list[str]:
    """The things the capitalised words inside a sentence qualify."""
    found = []
    for sentence in re.split(r"[.!?]+", prompt or ""):
        words = sentence.split()
        for i, w in enumerate(words[1:], 1):
            noun = qualified(w, words[i + 1] if i + 1 < len(words) else None)
            if noun:
                found.append(noun)
    return found


def must_present(prompt: str, must) -> list[str]:
    """The MUST words this prompt actually says (singular or plural)."""
    return [m.lower() for m in must if re.search(rf"\b{re.escape(m)}s?\b", prompt or "", re.I)]


def nouns_of(prompt: str, must=()) -> list[str]:
    """The nouns a picture drawn from this prompt must show, first appearance order."""
    out: list[str] = []
    things = [n for n in phrase_heads(prompt) + capitalised_nouns(prompt) if n not in BODY and n[:-1] not in BODY]
    for noun in things + must_present(prompt, must):
        if noun not in out:
            out.append(noun)
    return out


def diff(seen: list[str], asked: list[str]) -> list[str]:
    """The asked nouns no seen phrase carries, by stem (a hat answers 'top hats')."""
    stems = {stem(w) for phrase in seen for w in WORD.findall(phrase.lower())}
    return [noun for noun in asked if stem(noun) not in stems]


def _loads(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    found = re.search(r"\{.*\}", text, re.S)
    if not found:
        raise Unreadable(f"no JSON in {text[:80]!r}")
    try:
        return json.loads(found.group(0))
    except json.JSONDecodeError as bad:
        raise Unreadable(str(bad)) from bad


def parse(said: str) -> tuple[list[str], bool]:
    """The reader's (seen, text), however the caption workflow wrapped the answer:
    a JSON ARRAY whose one element is a STRING of JSON is unwrapped once."""
    got = _loads(said)
    if isinstance(got, list) and got:
        got = _loads(got[0]) if isinstance(got[0], str) else got[0]
    if not isinstance(got, dict) or "seen" not in got:
        raise Unreadable(f"the reader's answer has no 'seen' list: {said[:80]!r}")
    return subject_list(got["seen"]), truthy(got.get("text", False))


def question(asked: list[str]) -> str:
    """The one question: list, then say which of the asked nouns are absent."""
    return ASK + f'\n"absent": which of these asked nouns you cannot find in the picture: {asked}.'


def vlm_reader(picture: Path, question_text: str) -> str:
    """The default reader: the local vision model through the caption workflow."""
    return comfy.run_text(WORKFLOW, {"image_1": comfy.stage_image(Path(picture)), "prompt": question_text,
                                     "seed": SEED, "max_new_tokens": TOKENS})


def absent_of(said: str) -> set[str] | None:
    """The stems of what the reader called ABSENT, or None when its answer holds no such list."""
    try:
        got = _loads(said)
        if isinstance(got, list) and got:
            got = _loads(got[0]) if isinstance(got[0], str) else got[0]
    except Unreadable:
        return None
    named = got.get("absent") if isinstance(got, dict) else None
    if not isinstance(named, list):
        return None
    return {stem(w) for item in named for w in WORD.findall(str(item).lower())}


def read(picture: Path, prompt: str, reader: Callable | None = None, must=()) -> LookReading:
    """One picture read against its prompt; `reader(picture, question) -> str` is injectable.
    The question asks which nouns are ABSENT, and the answer is read: a noun the reader neither
    lists nor calls absent is not missing (Jekyll Kawajiri 2026-10-18: Utterson's drawn band,
    listed as 'hat', absent [])."""
    asked = nouns_of(prompt, must)
    said = (reader or vlm_reader)(Path(picture), question(asked))
    seen, text = parse(said)
    missing, absent = diff(seen, asked), absent_of(said)
    if absent is not None:
        missing = [noun for noun in missing if stem(noun) in absent]
    return LookReading(seen=seen, missing=missing, text=text)
