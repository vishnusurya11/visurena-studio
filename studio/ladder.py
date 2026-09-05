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


@dataclass
class Climb:
    """One ladder, advanced ONE ATTEMPT AT A TIME so many climbs share a round.

    `climb` below is this loop driven to the end for a single subject, which is
    right when an attempt is cheap and self-contained.  A step 07 attempt is
    not: rendering unloads the vision model and reading unloads the video
    model, so a per-subject loop pays a 16 GB model swap between every attempt
    and its gate.  Asked a round at a time, twelve beats render back to back
    with one model resident and are gated together -- same rungs, same
    learnings, one swap instead of twelve.
    """

    ladder: Ladder
    step: str
    substep: str = ""
    gate_name: str = "gate"
    attempts: int = 0
    rungs: list[str] = field(default_factory=list)
    outcome: Outcome | None = None

    @property
    def done(self) -> bool:
        return self.outcome is not None

    def ask(self, budget: Budget, learn: Callable[[Learning], None]):
        """The (rung, try) this climb wants next, or None when it ends here --
        out of rungs, or out of the time a retry costs."""
        plan = list(_tries(self.ladder))
        if self.attempts >= len(plan):
            learn(Learning(step=self.step, substep=self.substep, gate=self.gate_name,
                           action=self.ladder.terminal, attempt=len(self.rungs), terminal=True))
            return self._end()
        rung, i = plan[self.attempts]
        if self.attempts > 0 and not budget.can_afford(self.step, rung.cost_seconds):
            learn(Learning(step=self.step, substep=self.substep, gate="budget",
                           measured=budget.remaining(self.step), threshold=rung.cost_seconds,
                           action=self.ladder.terminal, attempt=self.attempts, terminal=True))
            return self._end()
        return rung, i

    def settle(self, rung: Rung, result: Any, ok: bool, measured: Any, threshold: Any,
               seconds: float, learn: Callable[[Learning], None]) -> None:
        """This attempt's verdict: passing ends the climb, failing takes a rung."""
        self.attempts += 1
        if ok:
            self.outcome = Outcome(result, self.rungs)
            return
        self.rungs.append(rung.name)
        learn(Learning(step=self.step, substep=self.substep, gate=self.gate_name,
                       measured=measured, threshold=threshold, action=rung.name,
                       attempt=self.attempts, seconds=seconds))

    def _end(self) -> None:
        """Out of rungs or out of time: the terminal rung, which never asks."""
        self.outcome = Outcome(None, self.rungs, terminal=True)
        return None


def climb(ladder: Ladder, step: str, attempt: Callable[[Rung, int], Any], gate: Gate,
          budget: Budget, learn: Callable[[Learning], None], gate_name: str = "gate",
          substep: str = "") -> Outcome:
    """Try, gate, climb; go terminal when rungs or time run out.  `substep`
    names what is being climbed for (a character, a beat) on every learning."""
    one = Climb(ladder, step, substep, gate_name)
    while not one.done:
        wanted = one.ask(budget, learn)
        if wanted is None:
            break
        started = budget.clock()
        result = attempt(*wanted)
        ok, measured, threshold = gate(result)
        one.settle(wanted[0], result, ok, measured, threshold, budget.clock() - started, learn)
    return one.outcome
