"""The Prism contract: a style card, a model guide, a subject set.  The pydantic models ARE the spec."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

STYLE_ID = r"^(anime|live)_[a-z0-9]+(_[a-z0-9]+)*$"
FAMILY_OF = {"anime": "anime", "live": "live_action"}
FILLER = re.compile(r"\b(masterpiece|best quality|8k|4k|ultra detailed|highly detailed|trending on artstation)\b", re.I)
PARTS = ("{style}", "{subject}")
KNOWN_PARTS = {"style", "subject", "camera", "recap"}
LENS_MM = re.compile(r"\b\d+\s?mm\b", re.I)
KINDS = {"character": 1, "location": 1, "scene": 3}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Lineage(Strict):
    titles: list[str] = Field(min_length=1)
    studios: list[str] = []
    directors: list[str] = []
    era: str = ""


class Traits(Strict):
    line: str
    shading: str
    palette: str
    lighting: str
    faces: str
    backgrounds: str
    texture: str
    camera: str


class ModelWords(Strict):
    """One model's own style text, when the shared `style_words` do not carry the look on it."""
    style: str
    recap: str = ""
    notes: str = ""
    captions: dict[str, str] = {}
    """Whole captions by subject id, from the model vendor's own prompt upsampler; rendered as written."""


class Verdict(Strict):
    status: Literal["researched", "tested", "locked", "rejected"] = "researched"
    best_model: str | None = None
    notes: str = ""


class Style(Strict):
    id: str = Field(pattern=STYLE_ID)
    name: str
    family: Literal["anime", "live_action"]
    summary: str
    lineage: Lineage
    traits: Traits
    style_words: str
    avoid: list[str] = []
    confusable_with: list[str] = []
    sources: list[str] = Field(min_length=1)
    added: str
    run: str
    models: dict[str, ModelWords] = {}
    verdict: Verdict = Verdict()

    @field_validator("style_words")
    @classmethod
    def a_style_sentence(cls, words: str) -> str:
        if not 15 <= len(words.split()) <= 90:
            raise ValueError(f"style_words holds {len(words.split())} words; 15-90 carry a look")
        if FILLER.search(words):
            raise ValueError(f"style_words carries filler {FILLER.search(words).group(0)!r}")
        return words

    @model_validator(mode="after")
    def id_names_family(self) -> "Style":
        if FAMILY_OF[self.id.split("_", 1)[0]] != self.family:
            raise ValueError(f"{self.id} is not family {self.family}")
        return self


class ModelGuide(Strict):
    id: str
    label: str
    workflow: str
    values: dict[str, Any] = {}
    prompt_key: str = "prompt"
    seed_key: str = "seed"
    prefix_key: str = "filename_prefix"
    template: str
    form: str = ""
    """The model's trained caption form in words (what its writer follows); `template` only joins the parts."""
    max_words: int
    negative_supported: bool
    captions_only: bool = False
    """Plan only the (style, subject) pairs that hold a whole caption for this model."""
    own_words_only: bool = False
    """Plan only the styles whose card carries this model's own words (never the shared fallback)."""
    names_work: str = ""
    findings: list[str] = []
    system_prompt: str
    sources: list[str] = []

    @field_validator("template")
    @classmethod
    def all_three_parts(cls, template: str) -> str:
        missing = [p for p in PARTS if p not in template]
        unknown = set(re.findall(r"{(\w+)}", template)) - KNOWN_PARTS
        if missing or unknown:
            raise ValueError(f"template lacks {missing} / names unknown {sorted(unknown)}")
        return template


class Subject(Strict):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    kind: Literal["character", "location", "scene"]
    title: str
    prose: str
    camera: str
    seed: int
    forms: dict[str, str] = {}
    """A model's own subject text (style-neutral, its camera inside), in that model's caption form."""

    @field_validator("camera")
    @classmethod
    def no_lens_numbers(cls, camera: str) -> str:
        if LENS_MM.search(camera):
            raise ValueError("a camera line frames in words; lens millimetres pull Krea2 photographic")
        return camera


class SubjectSet(Strict):
    story: str
    subjects: list[Subject]

    @model_validator(mode="after")
    def the_five(self) -> "SubjectSet":
        kinds = {k: sum(s.kind == k for s in self.subjects) for k in KINDS}
        if kinds != KINDS:
            raise ValueError(f"a subject set is {KINDS}; got {kinds}")
        if len({s.id for s in self.subjects}) != len(self.subjects):
            raise ValueError("subject ids repeat")
        return self


def read_style(path: Path) -> Style:
    return Style.model_validate_json(Path(path).read_text(encoding="utf-8"))


def write_style(style: Style, folder: Path) -> Path:
    path = Path(folder) / f"{style.id}.json"
    path.write_text(json.dumps(style.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_styles(folder: Path) -> list[Style]:
    return [read_style(p) for p in sorted(Path(folder).glob("*.json"))]


def load_guides(folder: Path) -> dict[str, ModelGuide]:
    guides = [ModelGuide.model_validate_json(p.read_text(encoding="utf-8")) for p in sorted(Path(folder).glob("*.json"))]
    return {g.id: g for g in guides}


def load_subjects(path: Path) -> SubjectSet:
    return SubjectSet.model_validate_json(Path(path).read_text(encoding="utf-8"))
