"""One shape every judged step uses, so the six steps stay short.

    clear(ctx, gate, judge, sign, ladder, terminal)

The policy row must be `auto` (a human gate is `require`'s, not a judge's).
The judge reads the artefact as it stands: a pass is signed in the judge's
name; a fault takes the next rung the budget affords (the ladder re-renders,
the judge reads again, one learning per rung); when rungs or time run out the
terminal rung keeps what it keeps and never asks -- the verdict is signed
`flagged` with its faults listed, a terminal learning is written, and one row
goes to the book's audit sheet.  No verdict file exists while the ladder
climbs, so `require` can never refuse a fault a judge wrote.  A `shadow` on
the row runs a newer judge version on the final artefact and writes
`<verdict>.shadow.json` for the bench; it signs nothing.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from studio import audit_rows, gate_policy
from studio.gate_policy import Policy
from studio.judges.verdict import Verdict
from studio.ladder import Ladder, Rung
from studio.learnings import Learning

Judge = Callable[[], Verdict]
Sign = Callable[[Verdict], Path]
Take = Callable[[Rung, int, Verdict], None]
Terminal = Callable[[Verdict], Verdict | None]

LADDERS = "ladders"
"""The budget share a ladder climbs on when no step is open."""
MAX_REPEAT = 12
"""One (kind, where) returned more often than this is a broken measure, not a
verdict: ep12's panel judge wrote "landmark at shot_00" 531 times and signed."""


@dataclass
class Rungs:
    """A step's priced rungs (studio.ladder names and prices them) and how to
    take one: `take(rung, try, verdict)` re-renders for that cause; the judge
    reads again afterwards."""
    ladder: Ladder
    take: Take


def tries(ladder: Ladder) -> Iterator[tuple[Rung, int]]:
    for rung in ladder.rungs:
        for i in range(rung.tries):
            yield rung, i


def step_of(ctx) -> str:
    """The budget share the climb is charged to: the open step, else the ladders' own."""
    if ctx.budget.step is None:
        ctx.budget.start(LADDERS)
    return ctx.budget.step


def affordable(ctx, gate: str, rung: Rung, taken: int) -> bool:
    """Whether the budget pays for this rung.  A no DEFERS the run -- a budget
    learning, then a stop the next run resumes -- and never reaches the
    terminal: ep12's panels were signed keep_best at attempt 0, unjudged,
    because the share was already 2993 s overdrawn (root cause A2)."""
    step = step_of(ctx)
    if ctx.budget.can_afford(step, rung.cost_seconds):
        return True
    left = ctx.budget.remaining(step)
    ctx.learn(Learning(step=step, gate="budget", measured=left, threshold=rung.cost_seconds,
                       action="defer", attempt=taken))
    raise SystemExit(f"DEFERRED: {gate} needs {rung.cost_seconds:.0f} s for its '{rung.name}' rung and "
                     f"the run's {step} share has {left:.0f} s; nothing signed -- run again to resume")


def repeated(verdict: Verdict) -> str | None:
    """'kind at where xN' when one fault repeats past MAX_REPEAT, else None."""
    from collections import Counter
    counts = Counter((f.kind, f.where) for f in verdict.faults)
    (kind, where), n = counts.most_common(1)[0] if counts else (("", ""), 0)
    return f"{kind} at {where} x{n}" if n > MAX_REPEAT else None


def valid(verdict: Verdict, gate: str) -> Verdict:
    """The verdict, or a stop when it is a broken measure's output (root cause A3)."""
    if said := repeated(verdict):
        raise SystemExit(f"INVALID VERDICT: {gate}'s judge returned {said} -- a broken measure, "
                         f"not a signature; fix the judge before the gate can clear")
    return verdict


def climbed(ctx, gate: str, judge: Judge, rungs: Rungs, terminal: str) -> tuple[Verdict, list[str]]:
    """The verdict as it stands, then after every rung taken; the rungs taken."""
    verdict, taken = valid(judge(), gate), []
    for rung, i in tries(rungs.ladder):
        if verdict.passed or not affordable(ctx, gate, rung, len(taken)):
            break
        started = ctx.budget.clock()
        rungs.take(rung, i, verdict)
        taken.append(rung.name)
        ctx.learn(Learning(step=step_of(ctx), gate=gate, measured=len(verdict.faults),
                           action=rung.name, attempt=len(taken), note=verdict.summary(),
                           seconds=ctx.budget.clock() - started))
        verdict = valid(judge(), gate)
    return verdict, taken


def ended(ctx, gate: str, verdict: Verdict, name: str, terminal: Terminal, taken: int) -> Verdict:
    """Out of rungs or time: the terminal rung, which never asks.  It keeps
    what it keeps and hands back the verdict to sign flagged."""
    flagged = verdict.model_copy(update={"terminal": name})
    flagged = terminal(flagged) or flagged
    ctx.learn(Learning(step=step_of(ctx), gate=gate, measured=len(flagged.faults), action=name,
                       attempt=taken, terminal=True, note=flagged.summary()))
    return flagged


def sha8_of(signed: Path) -> str:
    doc = json.loads(signed.read_text(encoding="utf-8"))
    return next((str(doc[k]) for k in ("sha8", "plan_sha8", "pack_sha8") if k in doc), "")


def audited(ctx, gate: str, verdict: Verdict, signed: Path) -> Path:
    """The audit-sheet row a terminal rung leaves for the owner's look."""
    try:
        artefact = signed.resolve().relative_to(Path(ctx.book_dir).resolve()).as_posix()
    except ValueError:
        artefact = signed.name
    return audit_rows.append(ctx.book_dir, {
        "unit": ctx.unit, "gate": gate, "judge": verdict.signer, "sha8": sha8_of(signed),
        "artefact": artefact, "faults": [f.model_dump() for f in verdict.faults],
        "terminal": verdict.terminal})


def sidecar(signed: Path, verdict: Verdict) -> Path:
    """`<verdict>.shadow.json`: the shadow version's read, for the bench; no signature."""
    target = signed.with_suffix(".shadow.json")
    target.write_text(verdict.model_dump_json(indent=1), encoding="utf-8")
    return target


def clear(ctx, gate: str, judge: Judge, sign: Sign, ladder: Rungs, terminal: Terminal, *,
          policy: Policy | None = None, shadow: Judge | None = None) -> Path:
    """Judge; pass -> sign in the judge's name; fault -> the ladder; spent ->
    the terminal, signed flagged with a learning and an audit row."""
    policy = policy or gate_policy.of(ctx.stage, gate)
    if policy.state != "auto":
        raise SystemExit(f"{ctx.stage}/{gate} is {policy.state} in gates.yaml; a judge clears auto gates only")
    name = policy.terminal or ladder.ladder.terminal
    verdict, taken = climbed(ctx, gate, judge, ladder, name)
    if verdict.passed:
        # A PASS IS WRITTEN DOWN, so the publish lock (studio/publish_lock.py)
        # can tell a gate that passed from one that never ran.
        if hasattr(ctx, "learn"):       # a bare StageContext (a step run alone) keeps no learnings
            ctx.learn(Learning(step=step_of(ctx), gate=gate, measured=0, action="pass", attempt=len(taken)))
    else:
        verdict = ended(ctx, gate, verdict, name, terminal, len(taken))
    signed = sign(verdict)
    if verdict.terminal:
        audited(ctx, gate, verdict, signed)
    if policy.shadow and shadow:
        sidecar(signed, shadow())
    return signed
