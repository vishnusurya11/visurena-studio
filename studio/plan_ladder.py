"""The plan ladder (episode 02_05), and its two terminals by cause.

    improve x2  ->  fresh_brief x1  ->  [battery still refusing] model_tier x1  ->  terminal

A rung re-drafts the plan through the writer: `improve` hands back every
refusal so far (the battery's lines and the critic's, one REFUSED block);
`fresh_brief` starts over from a freshly gathered brief with no history;
`model_tier` asks another tier, and only while no draft has yet passed the
battery.  Every rung costs no GPU second, so the budget never refuses one.

The terminal is by cause.  A critic fault (the battery passed at least
once): the BEST draft -- the battery-clean one the critic faulted least --
goes back into plan.json and is signed flagged in the judge's name.  A
battery refusal (no draft ever passed): the unit is DEFERRED -- the draft is
set aside as plan.deferred.json with its faults and the pass count, plan.json
is gone so the next pass authors again, and nothing is signed.  Neither
terminal asks anyone.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path

import re

from pydantic import ValidationError
from strands.types.exceptions import StructuredOutputException

from studio import episode_home, episode_spec, llm, plan_brief, plan_verdict
from studio.judges import plan as plan_judge
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung

IMPROVE, FRESH_BRIEF, MODEL_TIER, DEFER = "improve", "fresh_brief", "model_tier", "defer"
MODEL_TIER_NAME = "canon"
"""The tier the model_tier rung asks: the one that reasons.  The "reasoning"
tier is the workhorse model with reasoning off (models.yaml, the owner's cost
choice), and a rung that changes nothing is no rung."""
"""The tier the model_tier rung writes on; a yaml row, never a model name."""
DEFERRED = "plan.deferred.json"
BATTERY = "battery"
"""The fault kind plan_check's refusals are carried as; the critic's kinds are its own."""


def ladder(improves: int = 2) -> Ladder:
    return Ladder([Rung(IMPROVE, 0.0, tries=improves), Rung(FRESH_BRIEF, 0.0), Rung(MODEL_TIER, 0.0)],
                  "keep_best")


def battery_verdict(lines: list[str]) -> Verdict:
    """The battery's refusals as one verdict: a fault per line, kind `battery`."""
    faults = [Fault(kind=BATTERY, where="plan", note=line) for line in lines] or \
             [Fault(kind=BATTERY, where="plan", note="plan_check refused without a line")]
    return Verdict(judge=plan_judge.JUDGE, version=plan_judge.VERSION, passed=False,
                   faults=faults, confidence=1.0, reads=1)


def is_battery(verdict: Verdict) -> bool:
    return any(f.kind == BATTERY for f in verdict.faults)


def contract_refusals(bad: ValidationError) -> list[str]:
    """The contract's refusals, one per line, as the gate prints its own."""
    return episode_spec.refusal_lines(bad)


CONTRACT_LINE = re.compile(r"CONTRACT [^\n\[]+")
"""A contract refusal inside the gateway's message (pydantic appends ` [type=...]`)."""


def refused_lines(spent: StructuredOutputException) -> list[str]:
    """What a spent re-ask carried: the contract's refusals off the pydantic cause
    (a field rule refusing inside the schema has no CONTRACT text of its own),
    else the CONTRACT lines in the message; none for a provider failure."""
    cause = spent.__cause__
    while cause is not None and not isinstance(cause, ValidationError):
        cause = cause.__cause__
    if cause is not None:
        return contract_refusals(cause)
    return contract_lines(str(spent))


def contract_lines(said: str) -> list[str]:
    """The contract lines a spent re-ask carried; none for a provider failure."""
    return [m.group(0).strip() for m in CONTRACT_LINE.finditer(said)]


def merged(so_far: list[str], fresh: list[str]) -> list[str]:
    """EVERY refusal so far, not only this round's: each draft is written from scratch."""
    return so_far + [line for line in fresh if line not in so_far]


class Caller:
    """A structured caller on another tier, built on first use so that no test
    ever constructs a provider client."""

    def __init__(self, tier: str):
        self.tier = tier
        self._inner = None

    def __call__(self, prompt: str, structured_output_model=None):
        if self._inner is None:
            self._inner = llm._NativeStructuredCaller(self.tier)   # the gateway's one-request engine
        return self._inner(prompt, structured_output_model)


def defer(plan: Path, verdict: Verdict) -> Path:
    """The draft set aside, never signed: plan.deferred.json holds it with its
    faults and the pass count; plan.json is gone so the next pass authors again."""
    aside = plan.with_name(DEFERRED)
    passes = (json.loads(aside.read_text(encoding="utf-8")).get("passes", 0) if aside.exists() else 0) + 1
    draft = episode_home.read_json(plan) if plan.exists() else None
    doc = {"plan_sha8": plan_verdict.plan_sha8(plan) if plan.exists() else "", "verdict": "DEFERRED",
           "passes": passes, "signed_by": verdict.signer, "faults": [f.model_dump() for f in verdict.faults],
           "note": verdict.summary(), "date": _date.today().isoformat(), "draft": draft}
    aside.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    if plan.exists():
        plan.unlink()
    return aside


@dataclass
class Desk:
    """One unit's climb: the brief, the refusals so far, the drafts that passed
    the battery with their verdicts, and the critic's verdict per sha8."""
    ctx: object
    plan: Path
    writer: object
    battery_terminal: str = DEFER
    brief: dict | None = None
    refusals: list[str] = field(default_factory=list)
    pending: list[str] | None = None        # the contract's refusals of a draft that was never written
    drafts: list[tuple[dict, Verdict]] = field(default_factory=list)
    judged: dict[str, Verdict] = field(default_factory=dict)
    agent: object | None = None             # the reasoner, once a rule miss handed it the climb

    def brief_(self, fresh: bool = False) -> dict:
        if self.brief is None or fresh:
            self.brief = plan_brief.build(self.ctx.book_dir, self.ctx.number)
        return self.brief

    def refused_plan(self) -> dict | None:
        """The plan on disk the battery refused: what an improve rung edits."""
        return episode_home.read_json(self.plan) if self.plan.exists() else None

    def escalate(self) -> None:
        """The reasoner writes from here on.  Episode 13 (2026-09-25): four rungs on
        the cheap tier failed the CONTRACT; the reasoner's one rung passed it."""
        if self.agent is None:
            self.agent = Caller(MODEL_TIER_NAME)

    def resume(self) -> bool:
        """A deferred draft edited under its own refusal lines by the reasoner --
        it passed the CONTRACT once; the battery's lines are what is left."""
        aside = self.plan.with_name(DEFERRED)
        doc = json.loads(aside.read_text(encoding="utf-8")) if aside.exists() else {}
        if not doc.get("draft"):
            return False
        self.escalate()
        self.refusals = [f["note"] for f in doc.get("faults", []) if f.get("note")]
        self.write(self.refusals, previous=doc["draft"])
        return True

    def write(self, refusals: list[str] | None, agent=None, previous: dict | None = None) -> None:
        """One draft through write_plan, editing `previous` when there is one; a
        draft the CONTRACT refuses is a pending refusal for the next rung, not a crash."""
        agent = agent or self.agent
        kwargs = {"_agent": agent} if agent is not None else {}
        try:
            episode = self.writer.write(self.brief_(), refusals, previous=previous, **kwargs)
        except ValidationError as bad:
            self.pending = contract_refusals(bad)
            return
        except StructuredOutputException as spent:
            self.pending = refused_lines(spent)
            if not self.pending:
                raise                                 # a provider failure, not a refusal
            return
        self.pending = None
        episode_home.write_plan(self.plan, episode.model_dump())

    def remember(self, verdict: Verdict) -> None:
        """The draft on disk with its verdict, when the battery let it through."""
        if self.plan.exists() and not is_battery(verdict):
            self.drafts.append((episode_home.read_json(self.plan), verdict))

    def take(self, rung: Rung, i: int, verdict: Verdict) -> None:
        """One rung: remember the draft it faulted, then draft again."""
        self.remember(verdict)
        self.refusals = merged(self.refusals, refusal_lines_of(verdict))
        if is_battery(verdict):
            self.escalate()                       # a rule miss: the reasoner edits from here
        if rung.name == IMPROVE:
            self.write(self.refusals, previous=self.refused_plan())
        elif rung.name == FRESH_BRIEF:
            self.brief_(fresh=True)
            self.refusals = []
            self.write(None)
        elif rung.name == MODEL_TIER and not self.drafts:
            self.write(self.refusals, previous=self.refused_plan())

    def terminal(self, verdict: Verdict) -> Verdict:
        """By cause: no draft ever passed the battery -> defer; else the best
        draft back in plan.json and its verdict, flagged."""
        self.remember(verdict)
        if not self.drafts:
            return verdict.model_copy(update={"terminal": self.battery_terminal})
        doc, best = min(self.drafts, key=lambda pair: len(pair[1].faults))
        episode_home.write_plan(self.plan, doc)
        return best.model_copy(update={"terminal": verdict.terminal})

    def sign(self, verdict: Verdict) -> Path:
        """A pass or a keep_best is signed in the judge's name; a defer is set aside."""
        if verdict.terminal == DEFER:
            return defer(self.plan, verdict)
        return plan_verdict.sign(self.plan, verdict.summary(), signed_by=verdict.signer,
                                 faults=[f.model_dump() for f in verdict.faults], flagged=bool(verdict.terminal))


def refusal_lines_of(verdict: Verdict) -> list[str]:
    """What goes back to the writer: the battery's lines as printed, the critic's as gate lines."""
    if is_battery(verdict):
        return [f.note for f in verdict.faults]
    return plan_judge.lines(verdict)
