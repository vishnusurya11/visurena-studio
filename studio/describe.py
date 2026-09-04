"""A face read by a vision-language model into a TRAIT CARD, and cards compared.

THE RULE: two sheets read as different people when they differ in at least
DISTINCT_AT of the traits a viewer sees at trailer distance -- the rule
`cast_card.refuse_collision` applies to the prompt text, applied here to the
pixels.  A recogniser's cosine (SFace, 0.363) said only THAT two sheets read
alike, so its one rung was another seed, and Lestrade collided five times in
a row; a trait card says WHICH traits matched, so the next render can be told
to change exactly those.

The model is the local Qwen3-VL through comfy_studio's caption workflows.  It
is never asked yes/no (a VLM says yes); it is asked to describe, in a closed
vocabulary, and the comparison is done here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from pydantic import BaseModel, field_validator

from studio import comfy

IMAGE_WORKFLOW = "image_qwen3vl_caption"
VIDEO_WORKFLOW = "video_qwen3vl_caption"
TIMEOUT = 600.0
DISTINCT_AT = 3
"""Differ in this many seen traits and two faces are two people."""
VERIFIABLE_FROM = 4
"""A card that sees fewer traits than this cannot vouch for anyone."""

TRAITS: dict[str, tuple[str, ...]] = {
    "age": ("young", "middle-aged", "old", "unclear"),
    "hair_colour": ("black", "dark brown", "brown", "fair", "red", "grey", "white", "none", "unclear"),
    "hair_length": ("bald", "short", "medium", "long", "unclear"),
    "facial_hair": ("clean-shaven", "moustache", "beard", "whiskers", "unclear"),
    "headgear": ("none", "top hat", "bowler", "cap", "deerstalker", "helmet", "other hat", "unclear"),
    "complexion": ("pale", "fair", "sallow", "ruddy", "olive", "dark", "unclear"),
    "build": ("slight", "average", "stocky", "heavy", "unclear"),
}
SYNONYMS: dict[str, dict[str, tuple[str, ...]]] = {
    "age": {"old": ("elderly", "aged", "senior", "sixt", "sevent"),
            "young": ("youth", "twent", "teen", "boy", "girl"),
            "middle-aged": ("middle", "thirt", "fort", "fift")},
    "hair_colour": {"fair": ("blond", "sandy", "flaxen"), "brown": ("chestnut", "auburn"),
                    "red": ("ginger",), "grey": ("silver", "greying"), "none": ("bald",),
                    "dark brown": ("dark",)},
    "facial_hair": {"clean-shaven": ("none", "no facial hair", "shaven"),
                    "whiskers": ("sideburn", "muttonchop"), "beard": ("stubble",)},
    "headgear": {"none": ("bare", "no hat", "hatless"), "cap": ("flat cap", "cloth cap"),
                 "other hat": ("hat", "boater")},
    "complexion": {"pale": ("ashen", "white"), "ruddy": ("florid", "sunburn", "red"),
                   "dark": ("tan", "brown"), "fair": ("freckl", "light")},
    "build": {"slight": ("thin", "lean", "wiry", "slender"), "heavy": ("stout", "fat", "portly"),
              "stocky": ("broad", "muscular", "burly"), "average": ("medium",)},
}


def nearest(trait: str, value: str) -> str:
    """The vocabulary entry a free answer points at; raise when none does."""
    said = value.strip().lower()
    pool = sorted(TRAITS[trait], key=len, reverse=True)
    for entry in pool:
        if said == entry or entry in said:
            return entry
    for entry, marks in SYNONYMS.get(trait, {}).items():
        if any(mark in said for mark in marks):
            return entry
    raise ValueError(f"{trait}: {value!r} is not one of {TRAITS[trait]}")


class TraitCard(BaseModel):
    age: str
    hair_colour: str
    hair_length: str
    facial_hair: str
    headgear: str
    complexion: str
    build: str
    description: str = ""
    """The model's free prose, kept for the record and never compared."""

    @field_validator(*TRAITS, mode="before")
    @classmethod
    def _onto_vocabulary(cls, value, info):
        return nearest(info.field_name, str(value))


def prompt_for() -> str:
    """Describe, in a closed vocabulary; never a yes/no."""
    allowed = "\n".join(f'  "{trait}": one of {list(pool)}' for trait, pool in TRAITS.items())
    return ("Describe the one person in this image for a casting sheet.  Answer with a "
            "single JSON object and nothing else, with exactly these keys:\n" + allowed +
            '\n  "description": two sentences of plain prose about their face, hair and clothes.\n'
            'Use "unclear" for any trait the image does not show plainly.  Judge what is '
            "visible; do not guess from the period or the clothing.")


def unwrap(text: str) -> str:
    """The answer itself: PreviewAny reports the VQA node's output, a LIST of
    strings, as pretty JSON, so the card arrives as a string inside a list."""
    try:
        outer = json.loads(text)
    except ValueError:
        return text
    if not isinstance(outer, list):
        return text
    return "\n".join(s for s in outer if isinstance(s, str))


def parse_card(text: str) -> TraitCard:
    """The first {...} object in the model's answer, as a card."""
    found = re.search(r"\{.*\}", unwrap(text), re.DOTALL)
    if not found:
        raise ValueError(f"no JSON object in the answer: {text[:120]!r}")
    return TraitCard(**json.loads(found.group(0)))


def _ask(name: str, images: dict[str, Path], seed: int, run: Callable) -> TraitCard:
    """One caption call, retried once with the next seed if the answer will not parse."""
    staged = {slot: comfy.stage_image(path) for slot, path in images.items()}
    for attempt in range(2):
        values = {"prompt": prompt_for(), "temperature": 0.1, "seed": seed + attempt, **staged}
        try:
            return parse_card(run(name, values, TIMEOUT))
        except ValueError as failure:
            last = failure
    raise last


def describe(image: Path, seed: int = 42, run: Callable | None = None) -> TraitCard:
    """The trait card of the face in one still."""
    return _ask(IMAGE_WORKFLOW, {"image_1": Path(image)}, seed, run or comfy.run_text)


def describe_frames(frames: list[Path], seed: int = 42, run: Callable | None = None) -> TraitCard:
    """The trait card of the person seen across three sampled frames of a clip."""
    images = {f"frame_{i + 1}": Path(f) for i, f in enumerate(frames[:3])}
    return _ask(VIDEO_WORKFLOW, images, seed, run or comfy.run_text)


def differences(a: TraitCard, b: TraitCard) -> list[str]:
    """The traits both cards can see that disagree."""
    return [trait for trait in TRAITS
            if "unclear" not in (getattr(a, trait), getattr(b, trait))
            and getattr(a, trait) != getattr(b, trait)]


def shared(a: TraitCard, b: TraitCard) -> list[str]:
    """The traits both cards can see that agree."""
    return [trait for trait in TRAITS
            if "unclear" not in (getattr(a, trait), getattr(b, trait))
            and getattr(a, trait) == getattr(b, trait)]


def known(card: TraitCard) -> int:
    """How many traits the card can vouch for."""
    return sum(getattr(card, trait) != "unclear" for trait in TRAITS)


def verifiable(card: TraitCard) -> bool:
    """Enough seen to judge; a distant or turned-away figure is not."""
    return known(card) >= VERIFIABLE_FROM


def same_look(a: TraitCard, b: TraitCard) -> bool:
    return len(differences(a, b)) < DISTINCT_AT


def closest(card: TraitCard, bound: dict[str, TraitCard]) -> tuple[str | None, list[str]]:
    """The bound card this one is most like, and what still separates them."""
    if not bound:
        return None, []
    who = min(bound, key=lambda name: len(differences(card, bound[name])))
    return who, differences(card, bound[who])
