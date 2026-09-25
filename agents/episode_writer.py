"""Episode writer -- one unit of story as a plan (`episode_spec.Episode`), step 02_02.

The brief (`studio.plan_brief`) is everything on disk the plan is written from;
the skill is the desk's rules; the contract is what the plan must satisfy.
When `plan_check` refuses a draft, its refusals come back here verbatim in a
REFUSED section and the writer is asked again (step 02_04, at most twice).
Book-neutral: nothing here names a book, a character or an episode.

THE DRAFT SHAPE.  The contract's `setups` is a dict and its `beds` a list of
bare dicts; both leave a non-false `additionalProperties` in the JSON schema,
and a provider's strict structured outputs refuse exactly that (measured
offline with the SDK's own strict conversion, 2026-09-24).  So the model
returns a `Draft` -- the same fields, setups as a NAMED LIST, beds as typed
rows -- and `to_episode` folds it into the contract, whose rules then judge it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from studio import canvas, llm, plan_brief
from studio.episode_spec import Episode, Line, Setup, Shot

TIER = "local"
SKILL_PATH = Path(__file__).parent / "skills" / "episode_writer.md"
REFUSED = "--- REFUSED, fix these ---"
"""The heading of the section that quotes plan_check's refusals back, verbatim."""


class NamedSetup(Setup):
    name: str
    """The key the shots name this setup by (`Shot.setup`)."""


class Bed(BaseModel):
    from_shot: int = Field(ge=0)
    tone: str


class Draft(BaseModel):
    """`Episode` in a strict-schema-safe shape; every field of the contract, no rule of it."""
    number: int = Field(ge=1)
    title: str
    question: str = ""
    where: str = ""
    light: str = ""
    palette: str = ""
    look: str = ""
    aspect: Literal["9:16", "1:1"] = canvas.DEFAULT
    answer: str = ""
    protagonist: str
    setups: list[NamedSetup]
    shots: list[Shot]
    lines: list[Line]
    beds: list[Bed] = Field(default_factory=list)


def to_episode(draft: Draft) -> Episode:
    """The draft under the contract: named setups keyed by name, beds as rows."""
    doc = draft.model_dump()
    setups: dict[str, dict] = {}
    for setup in doc.pop("setups"):
        name = setup.pop("name")
        if name in setups:
            raise ValueError(f"setup {name!r} is defined twice")
        setups[name] = setup
    return Episode.model_validate({**doc, "setups": setups})


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def refused_section(refusals: list[str] | None) -> str:
    """The refusals as the gate printed them, one per line; empty when there are none."""
    if not refusals:
        return ""
    return (f"\n\n{REFUSED}\nThe previous plan was refused by the free gates. Every line below "
            f"is a refusal, quoted as the gate printed it. Fix each one and return the whole "
            f"plan again.\n" + "\n".join(refusals))


def prompt_for(brief: dict, refusals: list[str] | None = None) -> str:
    return (f"{load_skill()}\n\n--- THE BRIEF ---\n{plan_brief.render(brief)}"
            f"{refused_section(refusals)}\n\nReturn the plan.")


def write(brief: dict, refusals: list[str] | None = None, usage: dict | None = None,
          _agent=None) -> Episode:
    """One plan for one unit: the draft from the model, the contract's rules on the way back."""
    draft = llm.structured(TIER, prompt_for(brief, refusals), Draft, usage=usage, _agent=_agent)
    return to_episode(draft)
