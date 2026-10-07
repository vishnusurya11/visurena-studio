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
import re
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


CODE_SET_FIELDS = frozenset({"words_per_second"})
"""Contract fields the code sets, never the writer: the Draft mirrors every other one."""


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


def to_episode(draft: Draft, brief: dict | None = None) -> Episode:
    """The draft under the contract: named setups keyed by name, beds as rows,
    and the band's spoken rate, so the contract projects at the pace the writer
    was told (ep22, 2026-10-07: 2.5 in the brief, 3.0 in the contract, 106 s)."""
    doc = draft.model_dump()
    rate = ((brief or {}).get("band") or {}).get("words_per_second")
    if rate:
        doc["words_per_second"] = float(rate)
    setups: dict[str, dict] = {}
    for setup in doc.pop("setups"):
        name = setup.pop("name")
        if name in setups:
            raise ValueError(f"setup {name!r} is defined twice")
        setups[name] = setup
    return Episode.model_validate(structural_cures({**doc, "setups": setups}))


def structural_cures(doc: dict) -> dict:
    """The free one-number cures a merged draft gets BEFORE the contract judges it
    (ep22, 2026-10-07: 'the shot before the button names a beat of >= 1.0 s' refused
    three drafts a rung while `plan_cures.button_beat` sat unused one step later)."""
    from studio import plan_cures
    try:
        return plan_cures.button_beat(doc)
    except Exception:                       # a cure never turns a refusal into a crash
        return doc


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def refused_section(refusals: list[str] | None) -> str:
    """The refusals as the gate printed them, one per line; empty when there are none."""
    if not refusals:
        return ""
    return (f"\n\n{REFUSED}\nThe previous plan was refused by the free gates. Every line below "
            f"is a refusal, quoted as the gate printed it. Fix each one and return the whole "
            f"plan again.\n" + "\n".join(refusals))


PLAN_WIDE = "A refusal that names `plan` is a MEDIAN over every shot or setup"
"""ep22 (2026-10-07): G-FIRSTFRAME names the plan, 'keep every other word' kept
the plan, and four rungs judged the same 34 words a shot against 40."""


def plan_wide(refusals: list[str] | None) -> bool:
    return any(re.search(r"\bplan:", r) for r in refusals or [])


def previous_section(previous: dict | None, refusals: list[str] | None = None) -> str:
    """The plan the refusals are about, as JSON, with the one instruction that
    matters: change what the refusals name and keep the rest -- and when a
    refusal names the whole plan, change every row it measures."""
    if not previous:
        return ""
    scope = (f" {PLAN_WIDE}: lengthen or fix EVERY shot's or setup's field it names until the "
             f"median clears the floor; keep everything else as it is." if plan_wide(refusals) else "")
    return (f"\n\n{PREVIOUS}\n{json.dumps(previous, ensure_ascii=False)}\n"
            "Return this SAME plan with only the refused rows changed; keep every other "
            f"shot, line and word as it is.{scope}")


def prompt_for(brief: dict, refusals: list[str] | None = None, previous: dict | None = None) -> str:
    return (f"{load_skill()}\n\n--- THE BRIEF ---\n{plan_brief.render(brief)}"
            f"{previous_section(previous, refusals)}{refused_section(refusals)}\n\nReturn the plan.")


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
SHOT_FIELDS = ("shots",)
LINE_FIELDS = ("lines",)
PART_TABLE = (("THE FRAME", FRAME_FIELDS), ("THE SHOTS", SHOT_FIELDS), ("THE LINES", LINE_FIELDS))
"""The strict calls one draft takes, in order; each later part reads the earlier
ones.  Shots and lines are separate: the shots+lines grammar compiled but the
provider ground on it for 33 min (ep21, 2026-10-07); shots alone is 4k chars."""
PARTS = len(PART_TABLE)
"""Strict calls per draft; the tests count prompts and tokens by it."""
PART_FRAME, PART_SHOTS, PART_LINES = (f"--- PART {i + 1} OF {PARTS}: {name} ---" for i, (name, _) in enumerate(PART_TABLE))


def _cured(doc):
    """The free cures a part's raw text gets BEFORE the contract judges it (ep22,
    2026-10-07): luna wrote 'slowly' in three motions, the shots part was refused
    three times a rung, and `strip_slow` never got its turn because no draft landed."""
    if isinstance(doc, dict) and isinstance(doc.get("shots"), list):
        from studio import plan_cures
        doc = {**doc, "shots": [plan_cures.strip_slow({"shots": [s]})["shots"][0] if isinstance(s, dict) else s
                                for s in doc["shots"]]}
    return doc


def _part_model(name: str, fields: tuple[str, ...]):
    from pydantic import create_model, model_validator
    return create_model(name, __validators__={"_cure_first": model_validator(mode="before")(classmethod(lambda cls, v: _cured(v)))},
                        **{k: (Draft.model_fields[k].annotation, Draft.model_fields[k]) for k in fields})


PartFrame = _part_model("PartFrame", FRAME_FIELDS)
PartShots = _part_model("PartShots", SHOT_FIELDS)
PartLines = _part_model("PartLines", LINE_FIELDS)
PART_MODELS = (PartFrame, PartShots, PartLines)


def part_prompt(base: str, heading: str, fields: tuple[str, ...], so_far: dict | None) -> str:
    """The writer's prompt plus which fields this part returns and what the
    earlier parts already fixed (shots name the frame's setups; lines name shots)."""
    given = (f"\nAlready written, and fixed -- a shot may name only these setups, a line only these shots:\n"
             f"{json.dumps(so_far, ensure_ascii=False)}\n") if so_far else "\n"
    return f"{base}\n\n{heading}\nReturn ONLY these fields of the plan now: {', '.join(fields)}.{given}"


def write_parts(brief: dict, asked, shown, usage: dict | None, _agent,
                keep: dict | None = None, start: int = 0) -> Draft:
    """PARTS strict calls in order from `start`, each reading the merged earlier
    parts (`keep` holds the parts a contract refusal did not name); usage is the
    sum of the calls made."""
    base, so_far, spent = prompt_for(brief, asked, shown), dict(keep or {}), []
    for i, ((name, fields), model) in enumerate(zip(PART_TABLE, PART_MODELS)):
        if i < start:
            continue
        heading, one = f"--- PART {i + 1} OF {PARTS}: {name} ---", {}
        part = llm.structured(TIER, part_prompt(base, heading, fields, so_far or None), model, usage=one, _agent=_agent)
        so_far.update(part.model_dump())
        spent.append(one)
    if usage is not None:
        for k in ("input_tokens", "output_tokens", "total_tokens"):
            usage[k] = usage.get(k, 0) + sum(u.get(k, 0) for u in spent)
        usage["tier"] = TIER
    return Draft.model_validate(so_far)


_PART_OF_FIELD = {"shots": 1, "lines": 2}
_LINES_RULES = re.compile(r"\b(turn|button|dialogue|dial|line|lines|narration|voices?)\b", re.I)


def parts_to_re_ask(refusals: list[str]) -> int:
    """The first part a contract refusal re-asks (every later part follows, as
    they read it): a named field's part, a lines-only rule's lines part, else
    everything (ep22, 2026-10-07: 175 calls re-asking three parts for one rule)."""
    if not refusals:
        return 0
    first = PARTS
    for line in refusals:
        named = re.search(r"CONTRACT (setups|shots|lines)\b", line)
        if named:
            first = min(first, _PART_OF_FIELD.get(named.group(1), 0))
        elif re.search(r"\bprojects to \d+ s\b", line):
            first = min(first, 1)                       # the runtime is the shots' words and the lines'
        elif _LINES_RULES.search(line):
            first = min(first, 2)
        else:
            first = 0
    return first if first < PARTS else 0


def write(brief: dict, refusals: list[str] | None = None, usage: dict | None = None,
          _agent=None, previous: dict | None = None) -> Episode:
    """One plan for one unit: the draft from the model, edited under the contract
    up to CONTRACT_RETRIES times with the refused draft shown; the last refusal
    is raised for the ladder."""
    asked, shown, keep, start = refusals, previous, None, 0
    for _ in range(CONTRACT_RETRIES):
        draft = write_parts(brief, asked, shown, usage, _agent, keep=keep, start=start)
        try:
            return to_episode(draft, brief)
        except ValueError as bad:
            refused, shown = bad, draft.model_dump()
            lines = contract_lines_of(bad)
            asked = list(refusals or []) + lines
            start = parts_to_re_ask(lines)
            keep = {k: v for (_, fields) in PART_TABLE[:start] for k in fields for v in [shown[k]]}
    raise refused
