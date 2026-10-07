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

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from studio import canvas, llm, plan_brief
from studio.episode_spec import Episode, Line, Setup, Shot, refusal_lines

TIER = "local"
SKILL_PATH = Path(__file__).parent / "skills" / "episode_writer.md"
REFUSED = "--- REFUSED, fix these ---"
"""The heading of the section that quotes plan_check's refusals back, verbatim."""
PREVIOUS = "--- YOUR PREVIOUS PLAN ---"
"""The heading over the plan the refusals are about: the writer EDITS it.  A
refusal names rows; a rewrite from nothing fixes them and trips other rules
(episode 13, 2026-09-25: four passes, five rungs each, a different rule every
rung)."""
CONTRACT_RETRIES = 3
"""How many times the writer edits its own draft under the contract before the
refusal reaches the ladder."""


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
    omit: list[int] = Field(default_factory=list)
    """The contract's omitted shots; a writer's first draft omits none."""


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


def previous_section(previous: dict | None) -> str:
    """The plan the refusals are about, as JSON, with the one instruction that
    matters: change what the refusals name and keep the rest."""
    if not previous:
        return ""
    return (f"\n\n{PREVIOUS}\n{json.dumps(previous, ensure_ascii=False)}\n"
            "Return this SAME plan with only the refused rows changed; keep every other "
            "shot, line and word as it is.")


def prompt_for(brief: dict, refusals: list[str] | None = None, previous: dict | None = None) -> str:
    return (f"{load_skill()}\n\n--- THE BRIEF ---\n{plan_brief.render(brief)}"
            f"{previous_section(previous)}{refused_section(refusals)}\n\nReturn the plan.")


def contract_lines_of(bad: Exception) -> list[str]:
    """The contract's refusals of a draft, one per line."""
    if isinstance(bad, ValidationError):
        return refusal_lines(bad)
    return [f"CONTRACT setups: {bad}"]


# THE DRAFT IN TWO PARTS (2026-10-07).  Since 2026-10-06 17:27Z every provider
# behind OpenRouter refuses the strict grammar of the WHOLE Draft ("compiled
# grammar is too large"), and the loose path cannot answer (reasoning is
# mandatory for the model and eats the output budget).  Probed with 20-token
# calls: the frame (scalars, setups, beds) compiles, the body (shots, lines)
# compiles, the whole does not.  So one draft is two strict calls, the body
# reading the frame, merged into the one Draft the contract judges.

FRAME_FIELDS = ("number", "title", "question", "where", "light", "palette", "look", "aspect",
                "answer", "protagonist", "setups", "beds", "omit")
BODY_FIELDS = ("shots", "lines")
PART_FRAME = "--- PART 1 OF 2: THE FRAME ---"
PART_BODY = "--- PART 2 OF 2: THE BODY ---"
PARTS = 2
"""Strict calls per draft; the tests count prompts and tokens by it."""


def _part_model(name: str, fields: tuple[str, ...]):
    from pydantic import create_model
    return create_model(name, **{k: (Draft.model_fields[k].annotation, Draft.model_fields[k]) for k in fields})


PartFrame = _part_model("PartFrame", FRAME_FIELDS)
PartBody = _part_model("PartBody", BODY_FIELDS)


def part_prompt(base: str, heading: str, fields: tuple[str, ...], so_far: dict | None) -> str:
    """The writer's prompt plus which fields this part returns and what the
    earlier part already fixed (the body's shots name the frame's setups)."""
    given = f"\nThe frame, already written -- its setups are the only setups a shot may name:\n" \
            f"{json.dumps(so_far, ensure_ascii=False)}\n" if so_far else "\n"
    return f"{base}\n\n{heading}\nReturn ONLY these fields of the plan now: {', '.join(fields)}.{given}"


def write_parts(brief: dict, asked, shown, usage: dict | None, _agent) -> Draft:
    """Two strict calls, the body after the frame; usage is the sum of both."""
    base, u1, u2 = prompt_for(brief, asked, shown), {}, {}
    frame = llm.structured(TIER, part_prompt(base, PART_FRAME, FRAME_FIELDS, None), PartFrame, usage=u1, _agent=_agent)
    body = llm.structured(TIER, part_prompt(base, PART_BODY, BODY_FIELDS, frame.model_dump()), PartBody,
                          usage=u2, _agent=_agent)
    if usage is not None:
        for k in ("input_tokens", "output_tokens", "total_tokens"):
            usage[k] = usage.get(k, 0) + u1.get(k, 0) + u2.get(k, 0)
        usage["tier"] = TIER
    return Draft.model_validate({**frame.model_dump(), **body.model_dump()})


def write(brief: dict, refusals: list[str] | None = None, usage: dict | None = None,
          _agent=None, previous: dict | None = None) -> Episode:
    """One plan for one unit: the draft from the model, edited under the contract
    up to CONTRACT_RETRIES times with the refused draft shown; the last refusal
    is raised for the ladder."""
    asked, shown = refusals, previous
    for _ in range(CONTRACT_RETRIES):
        draft = write_parts(brief, asked, shown, usage, _agent)
        try:
            return to_episode(draft)
        except ValueError as bad:
            refused, shown = bad, draft.model_dump()
            asked = list(refusals or []) + contract_lines_of(bad)
    raise refused
