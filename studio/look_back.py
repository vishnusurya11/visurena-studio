"""A drawn picture read back against the nouns its own prompt asked for.

The rule `studio/panel_content.py` established, applied to a reference sheet:
the vision model is never asked whether the picture is right (a VLM says yes);
it is asked to LIST what it sees, and the comparison with the prompt's must-
appear nouns is done here, in code.  Which nouns a prompt asks for is a small
deterministic extraction -- the heads of the phrases after "with", "holding",
"wearing", "carrying", any capitalised word inside a sentence, and any word of
a MUST list the caller passes -- so the same prompt always asks for the same
things and a test can say so.

Advisory this pass (decision 2026-09-24, D8): there is no calibration yet, so
a miss is logged and nothing is refused.
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

PHRASE = re.compile(r"\b(?:with|holding|wearing|carrying)\s+([^,.;:]+)", re.I)
"""What follows a trigger word up to the next punctuation: the asked-for thing."""
ARTICLES = frozenset({"a", "an", "the", "his", "her", "their", "its", "one", "two", "some"})
WORD = re.compile(r"[a-z]+")
CAPITALISED = re.compile(r"^[A-Z][a-z]+$")

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


def phrase_heads(prompt: str) -> list[str]:
    """The head noun of every phrase after a trigger word, conjuncts split on 'and'."""
    heads = []
    for phrase in PHRASE.findall(prompt or ""):
        for part in re.split(r"\band\b", phrase, flags=re.I):
            words = [w for w in WORD.findall(part.lower()) if w not in ARTICLES]
            if words:
                heads.append(words[-1])
    return heads


def capitalised_nouns(prompt: str) -> list[str]:
    """A capitalised word that does not open its sentence names a thing."""
    found = []
    for sentence in re.split(r"[.!?]+", prompt or ""):
        words = sentence.split()
        found += [w.strip(",;:").lower() for w in words[1:] if CAPITALISED.match(w.strip(",;:"))]
    return found


def must_present(prompt: str, must) -> list[str]:
    """The MUST words this prompt actually says (singular or plural)."""
    return [m.lower() for m in must if re.search(rf"\b{re.escape(m)}s?\b", prompt or "", re.I)]


def nouns_of(prompt: str, must=()) -> list[str]:
    """The nouns a picture drawn from this prompt must show, first appearance order."""
    out: list[str] = []
    for noun in phrase_heads(prompt) + capitalised_nouns(prompt) + must_present(prompt, must):
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


def read(picture: Path, prompt: str, reader: Callable | None = None, must=()) -> LookReading:
    """One picture read against its prompt; `reader(picture, question) -> str` is injectable."""
    asked = nouns_of(prompt, must)
    seen, text = parse((reader or vlm_reader)(Path(picture), question(asked)))
    return LookReading(seen=seen, missing=diff(seen, asked), text=text)
