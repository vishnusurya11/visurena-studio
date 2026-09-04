"""The adapt ladder every trailer step climbs when a gate fails.

A rung changes the FORM of an attempt (another seed, an alternate setup for
the same beat, the next line with the same function) and never its
FUNCTION.  The terminal rung is a fallback that always exists -- card,
instrumental, music-only, onset grid, unbound, dropped -- so a run can end
without asking.  Retries are gated on the step's time budget; the first try
is the normal path and is never gated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from studio.learnings import Learning
from studio.run_budget import Budget

Gate = Callable[[Any], tuple[bool, Any, Any]]
"""result -> (passed, measured, threshold)"""


@dataclass
class Rung:
    name: str
    cost_seconds: float
    tries: int = 1


@dataclass
class Ladder:
    rungs: list[Rung]
    terminal: str


@dataclass
class Outcome:
    result: Any
    rungs: list[str] = field(default_factory=list)
    terminal: bool = False


def _tries(ladder: Ladder):
    for rung in ladder.rungs:
        for i in range(rung.tries):
            yield rung, i


def climb(ladder: Ladder, step: str, attempt: Callable[[Rung, int], Any], gate: Gate,
          budget: Budget, learn: Callable[[Learning], None], gate_name: str = "gate",
          substep: str = "") -> Outcome:
    """Try, gate, climb; go terminal when rungs or time run out.  `substep`
    names what is being climbed for (a character, a beat) on every learning."""
    taken: list[str] = []
    for n, (rung, i) in enumerate(_tries(ladder)):
        if n > 0 and not budget.can_afford(step, rung.cost_seconds):
            learn(Learning(step=step, substep=substep, gate="budget",
                           measured=budget.remaining(step), threshold=rung.cost_seconds,
                           action=ladder.terminal, attempt=n, terminal=True))
            return Outcome(None, taken, terminal=True)
        result = attempt(rung, i)
        ok, measured, threshold = gate(result)
        if ok:
            return Outcome(result, taken)
        taken.append(rung.name)
        learn(Learning(step=step, substep=substep, gate=gate_name, measured=measured,
                       threshold=threshold, action=rung.name, attempt=n + 1))
    learn(Learning(step=step, substep=substep, gate=gate_name, action=ladder.terminal,
                   attempt=len(taken), terminal=True))
    return Outcome(None, taken, terminal=True)
