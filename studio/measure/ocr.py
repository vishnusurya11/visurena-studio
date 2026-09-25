"""Lettering is a recognised string, judged -- not a box, not an ink share.

`panel_dq.inkiness` sees small bright marks and the VLM answers a `text` bool;
neither reads what the letters SPELL, so a cast label printed as a headline
passed the insert exemption.  EasyOCR (venv, CPU, weights cached under the
user profile) returns strings with a confidence; CRAFT hallucinates boxes on
letter-like shapes, so a box counts only with a recognised string.  The judge
names the string: a cast id is a leak, a plan word is the prompt bleeding
through, anything else is gibberish; an insert excuses gibberish and nothing
else.  The reader is injected (`reader=`); the import is lazy.
"""
from __future__ import annotations

import re

MIN_CONF = 0.5
"""Recogniser confidence a string needs."""
MIN_CHARS = 2
"""Alphabetic characters a string needs: one letter is a mark."""
MIN_HEIGHT = 8 / 1024
"""Box height as a share of the picture's width: 8 px at 1024."""
TOKEN = 4
"""A cast-id part or a plan word shorter than this cannot be matched inside a string."""


def default_reader(gpu: bool = False):
    """EasyOCR, English, built on first use; the GPU is left to the renders."""
    import easyocr
    engine = easyocr.Reader(["en"], gpu=gpu, verbose=False)
    return lambda path: engine.readtext(str(path))


def rows(results) -> list[dict]:
    """EasyOCR's (box, text, confidence) tuples as rows."""
    return [{"box": [[float(x), float(y)] for x, y in box], "text": str(text), "conf": float(conf)}
            for box, text, conf in results]


def read(image, reader=None) -> list[dict]:
    """Every string EasyOCR (or the injected reader) finds on the picture."""
    ask = reader if reader is not None else default_reader()
    return rows(ask(image))


def height(box: list) -> float:
    ys = [p[1] for p in box]
    return max(ys) - min(ys)


def letters(text: str) -> int:
    return sum(ch.isalpha() for ch in text)


def recognised(found: list[dict], width: int, min_conf: float = MIN_CONF) -> list[dict]:
    """The rows that carry a string: enough letters, confidence and height."""
    return [r for r in found if letters(r["text"]) >= MIN_CHARS and r["conf"] >= min_conf
            and height(r["box"]) >= MIN_HEIGHT * width]


def cast_tokens(cast_ids: list[str]) -> set[str]:
    """Each id whole, and each part of it long enough to mean something."""
    out = set()
    for cid in cast_ids:
        out.add(cid.lower())
        out |= {part for part in re.split(r"[^a-z0-9]+", cid.lower()) if len(part) >= TOKEN}
    return out


def plan_words(prose: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", (prose or "").lower()) if len(w) >= TOKEN}


def kind(text: str, cast: set[str], plan: set[str]) -> str:
    """cast_id | plan_word | gibberish, by whole words of the string."""
    said = text.lower()
    words = re.findall(r"[a-z]+", said)
    if said.strip().replace(" ", "_") in cast or any(w in cast for w in words):
        return "cast_id"
    if any(w in plan for w in words):
        return "plan_word"
    return "gibberish"


def lettering(found: list[dict], cast_ids: list[str], prose: str, insert: bool = False,
              width: int = 1024) -> list[dict]:
    """Every recognised string with its kind; an insert keeps only leaks."""
    cast, plan = cast_tokens(cast_ids), plan_words(prose)
    out = []
    for r in recognised(found, width):
        k = kind(r["text"], cast, plan)
        if insert and k == "gibberish":
            continue
        out.append({"text": r["text"], "kind": k, "conf": round(r["conf"], 2)})
    return out
