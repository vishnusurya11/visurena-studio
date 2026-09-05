"""Step 01 -- story: derive the structure, judge three fields, write story.json.

Lead, figure, turn and resolution are properties of the screenplay and come
from code (`studio.trailer_story`).  Narrator, register and thesis are the
only judged fields of the whole run, and the contract (`StorySpec`) is the
gate: a violation is quoted back to the model, and after three tries the
step ships `register=procedural, thesis=null` with the narrator read from
the source's pronouns.  Nothing here asks a question.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from studio import llm
from studio.ladder import Ladder, Rung, climb
from studio.learnings import Learning
from studio.trailer_stage_spec import VOCAL_REGISTERS, Register, StorySpec
from studio.trailer_story import figure_of, lead_of, people_in, resolution_scenes, turn_of

STEP_ID = "01"
NAME = "story"
TIER = "reasoning"
LEAD_SHARE_FLOOR = 0.25
FIRST_PERSON = re.compile(r"\bI\b")
LADDER = Ladder([Rung("agent_call", cost_seconds=60, tries=3)], terminal="procedural")


class Judgement(BaseModel):
    """What the model is allowed to decide; everything else is derived."""

    narrator: str = Field(description="character id of the narrating character, or 'omniscient'")
    register_: Register = Field(alias="register")
    thesis: str | None = Field(default=None, description="<= 7 syllables, present tense, "
                               "no names; null when the story has no refrain")
    setting: str = Field(default="", max_length=80,
                         description="period and place in one line, e.g. '1881 London'")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


def derive(scenes: list[dict]) -> dict:
    lead = lead_of(scenes)
    figure = figure_of(scenes, lead)
    turn = turn_of(scenes, lead)
    resolution = sorted(resolution_scenes(scenes, lead, figure))
    return {"lead": lead, "figure": figure, "turn_scene": turn["number"] if turn else 1,
            "resolution_scenes": resolution, "restricted_scenes": resolution}


def lead_share(scenes: list[dict], lead: str | None) -> float:
    if not scenes or not lead:
        return 0.0
    return sum(lead in people_in(sc) for sc in scenes) / len(scenes)


def narrator_by_pronouns(text: str, lead: str, floor: float = 0.02) -> str:
    """First-person density decides: the lead narrates, or nobody does."""
    words = len(text.split())
    if not words:
        return "omniscient"
    return lead if len(FIRST_PERSON.findall(text)) / words >= floor else "omniscient"


def source_text(book_dir: Path, limit: int = 200_000) -> str:
    chunks: list[str] = []
    for path in sorted((book_dir / "source/chapters").glob("*.json")):
        chunks += [p["text"] for p in json.loads(path.read_text(encoding="utf-8"))["paragraphs"]]
        if sum(map(len, chunks)) > limit:
            break
    return " ".join(chunks)[:limit]


def prompt_for(screenplay: dict, derived: dict, violation: str | None) -> str:
    registers = ", ".join(Register.__args__)  # type: ignore[attr-defined]
    quoted = f"\n\nYour previous answer was refused: {violation}. Fix exactly that." if violation else ""
    return (f"Book: {screenplay['title']}\nLogline: {screenplay['logline']}\n"
            f"Spine: {screenplay.get('spine', '')}\nLead: {derived['lead']}; "
            f"figure: {derived['figure']}; turn at scene {derived['turn_scene']}.\n\n"
            f"Decide four things for a trailer.\nnarrator: the character id who tells "
            f"this story, or 'omniscient'.\nregister: one of {registers}.\nthesis: the "
            f"story's one-line refrain in at most 7 syllables, present tense, naming "
            f"nobody -- or null. A sung refrain only fits {sorted(VOCAL_REGISTERS)}.\n"
            f"setting: period and place in one line, e.g. '1881 London'."
            + quoted)


def to_spec(derived: dict, judged: Judgement) -> StorySpec:
    return StorySpec(**derived, narrator=judged.narrator, register=judged.register_,
                     thesis=judged.thesis, setting=judged.setting)


CLAUSE = re.compile(r"\s*(?:[,;:]|\band\b|\bbut\b|\bthat\b|\bwho\b|\bwhich\b"
                    r"|\bwhere\b|\bwhen\b)\s*")
"""Where a sentence can be cut and still mean something on a card."""


def clauses(text: str) -> list[str]:
    """The pieces a refrain can be cut back to, shortest first."""
    parts = [p.strip(" ,;:.") for p in CLAUSE.split(text or "")]
    return sorted({p for p in parts if p}, key=lambda p: (len(p.split()), p))


def thesis_from(refused: str | None, derived: dict) -> str | None:
    """A refused refrain cut back to the shortest clause the contract takes.

    Run 10 shipped `thesis: null` because the model answered in eight
    syllables and this function preferred silence to arithmetic -- and the
    thesis is the one sentence the trailer can put on a card or read as
    voice-over (R11).  The contract does the accepting, so the rules live in
    one place: length is fixed by cutting, a name is not.
    """
    for clause in clauses(refused or ""):
        try:
            StorySpec(**derived, narrator="omniscient", register="procedural", thesis=clause)
            return clause
        except ValidationError:
            continue
    return None


def fallback(derived: dict, book_dir: Path, refused: str | None = None) -> StorySpec:
    narrator = narrator_by_pronouns(source_text(book_dir), derived["lead"] or "omniscient")
    return StorySpec(**derived, narrator=narrator, register="procedural",
                     thesis=thesis_from(refused, derived))


def judge(screenplay: dict, derived: dict, ctx) -> StorySpec:
    """Climb the judgement ladder: each refusal is quoted back to the model."""
    violation: dict = {"text": None, "thesis": None}

    def attempt(rung, i):
        return llm.structured(TIER, prompt_for(screenplay, derived, violation["text"]), Judgement)

    def gate(judged):
        try:
            to_spec(derived, judged)
            return True, None, "StorySpec"
        except ValidationError as exc:
            violation["text"] = exc.errors()[0]["msg"]
            violation["thesis"] = judged.thesis
            return False, violation["text"], "StorySpec"

    outcome = climb(LADDER, STEP_ID, attempt, gate, ctx.budget, ctx.learn, gate_name="judgement")
    if outcome.terminal:
        return fallback(derived, ctx.book_dir, violation["thesis"])
    return to_spec(derived, outcome.result)


def run(codex_id: str, ctx) -> None:
    screenplay = json.loads((ctx.book_dir / "screenplay/feature/screenplay.json")
                            .read_text(encoding="utf-8"))
    derived = derive(screenplay["scenes"])
    share = lead_share(screenplay["scenes"], derived["lead"])
    if share < LEAD_SHARE_FLOOR:
        ctx.learn(Learning(step=STEP_ID, gate="lead_share", measured=round(share, 3),
                           threshold=LEAD_SHARE_FLOOR, action="flagged", terminal=True))
    spec = judge(screenplay, derived, ctx)
    ctx.out_dir.mkdir(parents=True, exist_ok=True)
    (ctx.out_dir / "story.json").write_text(spec.model_dump_json(indent=2, by_alias=True),
                                            encoding="utf-8")
    print(f"[{STEP_ID}] lead {spec.lead} ({share:.0%}), figure {spec.figure}, "
          f"turn sc{spec.turn_scene}, {spec.register}, thesis={spec.thesis!r}")
