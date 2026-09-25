"""The plan judge (episode 02_05): the critic LISTS, this module JUDGES.

`agents.plan_reader` hands back k readings of the plan in the closed shape
below (`PlanReading`): the turn it found (the shot, the two people, the
verb), where the question is answered, which of the chapter's rows each beat
shows or tells, and every claim the plan makes about the chapter (a count, a
posture, a prop, a place) with the chapter's own words behind it.  Nothing
here asks a model whether the plan is right.  Code holds the readings
against the plan and the brief:

- the turn is an action between two DIFFERENT named people, both in the
  turn shot's setup, on the shot the plan marks as its turn, with a verb from
  the acting vocabulary; two of the three readings must agree on it;
- the answer lands on a shot or a line the plan has;
- no chapter row is silently dropped: every row the brief lists is shown by
  a shot or told by a line;
- no claim without a span; a claim ANY reading lists without a span is
  invented (the union over readings, for recall), and a span the chapter's
  text does not contain is invented too.

A fault climbs `studio.plan_ladder`; the verdict signs `judge:plan@1`.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field

from studio import plan_gates
from studio.episode_spec import Episode
from studio.judges.verdict import Fault, Verdict, confidence
from studio.plan_gates import SPAN_MATCH, span_match

JUDGE, VERSION = "plan", "1"
K = 3
GATE_LINE = "G-READER"
ACTS_ON = re.compile(rf"^(?:{plan_gates.ACTS_ON})$", re.IGNORECASE)


# ---- the closed shape the critic lists in -------------------------------------------

class Turn(BaseModel):
    shot: int = -1              # -1: no turn found
    actor: str = ""             # an entity id of the plan's cast
    acted_on: str = ""
    verb: str = ""              # one word, as the plan's motion clause has it
    span: str = ""              # the chapter's words for this act


class Answer(BaseModel):
    kind: Literal["shot", "line", "none"] = "none"
    index: int = -1
    span: str = ""


class Coverage(BaseModel):
    event: int                  # the chapter row's number, as the prompt listed it
    shots: list[int] = Field(default_factory=list)   # shots that SHOW it
    lines: list[int] = Field(default_factory=list)   # lines that TELL it


class Claim(BaseModel):
    shot: int
    kind: Literal["count", "posture", "prop", "place"]
    claim: str
    span: str = ""              # empty: the reader found no chapter words for it


class PlanReading(BaseModel):
    turn: Turn
    answer: Answer
    coverage: list[Coverage] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)


# ---- the brief's side -----------------------------------------------------------------

def rows_of(brief: dict) -> list[str]:
    """The chapter's rows, one per scene as the brief lists them: what the plan
    must show or tell."""
    return [str(scene.get("summary") or "") for scene in (brief.get("scenes") or [])
            if scene.get("summary")]


def where(shot: int) -> str:
    return f"shot_{shot:02d}"


# ---- the turn ---------------------------------------------------------------------------

def majority(readings: list[PlanReading]) -> Turn | None:
    """The turn more than half the readings agree on (shot, actor, acted on), or None."""
    keys = Counter((r.turn.shot, r.turn.actor, r.turn.acted_on) for r in readings)
    (key, votes), = keys.most_common(1)
    if votes * 2 <= len(readings):
        return None
    return next(r.turn for r in readings if (r.turn.shot, r.turn.actor, r.turn.acted_on) == key)


def turn_people_faults(turn: Turn, cast: list[str]) -> list[Fault]:
    """Two different named people of the setup, and a verb one lays on the other."""
    out = []
    people = {turn.actor, turn.acted_on} - {""}
    if len(people) < 2 or not people <= set(cast):
        out.append(Fault(kind="story", where=where(turn.shot),
                         note="the turn is not an act between two named people of its setup",
                         evidence={"actor": turn.actor, "acted_on": turn.acted_on, "cast": list(cast)}))
    if not ACTS_ON.match(turn.verb.strip()):
        out.append(Fault(kind="story", where=where(turn.shot),
                         note=f"{turn.verb!r} is not a visible act of one person on another",
                         evidence={"verb": turn.verb}))
    return out


def turn_faults(plan: Episode, readings: list[PlanReading]) -> list[Fault]:
    """The agreed turn, on an existing shot, the one the plan marks, between two people."""
    agreed = majority(readings)
    if agreed is None:
        return [Fault(kind="story", where="turn", note=f"the {len(readings)} readings do not agree on the turn",
                      evidence={"turns": [r.turn.model_dump() for r in readings]})]
    shot = next((s for s in plan.shots if s.index == agreed.shot), None)
    if shot is None:
        return [Fault(kind="story", where=where(agreed.shot), note="no turn was read on a shot the plan has",
                      evidence={"read": agreed.shot})]
    marked = next((s.index for s in plan.shots if s.section == "turn"), None)
    out = []
    if marked != agreed.shot:
        out.append(Fault(kind="story", where=where(agreed.shot), evidence={"read": agreed.shot, "marked": marked},
                         note=f"the plan marks shot {marked} as its turn; the reading found it on shot {agreed.shot}"))
    return out + turn_people_faults(agreed, plan.setups[shot.setup].cast)


# ---- the answer, the coverage, the claims ------------------------------------------------

def answer_faults(plan: Episode, reading: PlanReading) -> list[Fault]:
    """The answer lands on a shot or a line the plan has."""
    answer = reading.answer
    if answer.kind == "none":
        return [Fault(kind="answer", where="answer", note="the question is answered nowhere in the plan")]
    count = len(plan.shots if answer.kind == "shot" else plan.lines)
    if not 0 <= answer.index < count:
        return [Fault(kind="answer", where=f"{answer.kind}_{answer.index}",
                      note=f"the answer was read on {answer.kind} {answer.index}, which the plan does not have",
                      evidence={"kind": answer.kind, "index": answer.index, "count": count})]
    return []


def coverage_faults(plan: Episode, rows: list[str], reading: PlanReading) -> list[Fault]:
    """Every chapter row shown by a shot or told by a line; a covering shot must exist."""
    shots = {s.index for s in plan.shots}
    read = {c.event: c for c in reading.coverage}
    out = []
    for i, row in enumerate(rows):
        cover = read.get(i)
        if cover is None or not (cover.shots or cover.lines):
            out.append(Fault(kind="coverage", where=f"row_{i}", note=f"silently dropped: {row[:80]}"))
        elif ghosts := [n for n in cover.shots if n not in shots]:
            out.append(Fault(kind="coverage", where=f"row_{i}", evidence={"shots": ghosts},
                             note=f"covered by shots the plan does not have: {ghosts}"))
    return out


def unfound(claim: Claim, chapter: str | None) -> bool:
    """A span the chapter's text does not contain, when there is a text to search."""
    return chapter is not None and bool(claim.span.strip()) and span_match(claim.span, chapter) < SPAN_MATCH


def invented(readings: list[PlanReading], chapter: str | None, shots: set[int]) -> dict[tuple[int, str], Claim]:
    """The union over readings of every claim with no span, a span the chapter
    lacks, or a shot the plan lacks."""
    out: dict[tuple[int, str], Claim] = {}
    for reading in readings:
        for claim in reading.claims:
            if not claim.span.strip() or unfound(claim, chapter) or claim.shot not in shots:
                out.setdefault((claim.shot, claim.claim), claim)
    return out


def claim_note(claim: Claim, chapter: str | None, shots: set[int]) -> tuple[str, dict]:
    if not claim.span.strip():
        note, evidence = f"{claim.kind} {claim.claim!r} has no chapter span", {}
    elif unfound(claim, chapter):
        note = f"{claim.kind} {claim.claim!r}: span {claim.span[:60]!r} is not in the chapter"
        evidence = {"match": span_match(claim.span, chapter or ""), "wall": SPAN_MATCH}
    else:
        note, evidence = f"{claim.kind} {claim.claim!r}", {}
    if claim.shot not in shots:
        note += f" on shot {claim.shot}, which the plan does not have"
    return note, evidence


def claim_faults(plan: Episode, readings: list[PlanReading], chapter: str | None) -> list[Fault]:
    shots = {s.index for s in plan.shots}
    out = []
    for (shot, _), claim in invented(readings, chapter, shots).items():
        note, evidence = claim_note(claim, chapter, shots)
        out.append(Fault(kind="invented", where=where(shot), note=note, evidence=evidence))
    return out


# ---- the verdict ------------------------------------------------------------------------

def judge(plan: Episode | dict, brief: dict, readings: list[PlanReading], k: int = K) -> Verdict:
    """The readings held against the plan and the brief; confidence is the
    share of the k asks that came back readable."""
    plan = plan if isinstance(plan, Episode) else Episode.model_validate(plan)
    if not readings:
        faults = [Fault(kind="unread", where="plan", note="no reading came back")]
    else:
        faults = (turn_faults(plan, readings) + answer_faults(plan, readings[0])
                  + coverage_faults(plan, rows_of(brief), readings[0])
                  + claim_faults(plan, readings, brief.get("chapter_text")))
    reads = max(k, len(readings))
    return Verdict(judge=JUDGE, version=VERSION, passed=not faults, faults=faults,
                   confidence=confidence(len(readings), reads), reads=len(readings))


def lines(verdict: Verdict) -> list[str]:
    """The faults as gate lines, the format the writer already reads refusals in."""
    return [f"{GATE_LINE} {f.where.replace('_', ' ')}: {f.note}" for f in verdict.faults]
