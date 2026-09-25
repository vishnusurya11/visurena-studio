#!/usr/bin/env python
"""Step 02 of the episode stage: the plan, gated before anything is voiced or drawn.

    uv run python scripts/episode/step_02_plan.py <codex_id> <n> [--rewrite]

    brief (02_01)  ->  write (02_02)  ->  checks (02_03)  ->  improve (02_04, at most 2)
                                                          ->  lock (02_05)  ->  OWNER PLAN

The brief is gathered off disk (`studio.plan_brief`); the writer is the
registered agent (`agents.episode_writer`); the gate is `plan_check`, launched
as a script so it reads the draft exactly as every later step will; a refusal
is quoted back verbatim; a draft the gate still refuses after MAX_IMPROVE
rounds parks the unit.  The plan is written only through
`episode_home.write_plan`.  Then the PLAN signature: `plan.verdict.json` beside
the plan, bound to its sha8, written by `scripts/episode/sign_plan.py`.

`--rewrite` authors a fresh plan over an unsigned one, and never over a plan
that already ran downstream (`placed.json` beside it).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import episode_writer  # noqa: E402
from studio import episode_home, plan_brief, plan_verdict, step_cli  # noqa: E402
from studio.escalate import Escalation  # noqa: E402
from pydantic import ValidationError  # noqa: E402

STEP_ID = "02"
NAME = "plan"
GPU = False
MAX_IMPROVE = 2
"""Rounds in which the gate's refusals go back to the writer, after the first draft."""
PLAN_CHECK = "scripts/episode/plan_check.py"
REFUSED_ASIDE = "plan.refused.json"


def plan_of(ctx) -> Path:
    return episode_home.plan_path(ctx.book_dir, ctx.number)


def ran_downstream(ctx) -> bool:
    """A timeline beside the plan: this plan already ran; existence only."""
    return episode_home.has_timeline(ctx.book_dir, ctx.number)


def unit_file(ctx, name: str) -> str:
    """A signature's place, relative to the book, as the call-sheet prints it."""
    return f"episodes/{ctx.unit}/{name}"


def done(ctx) -> bool:
    """plan.json exists AND it is signed, or the unit is GRANDFATHERED.

    Grandfathered: `placed.json` beside the plan.  The timeline is built from
    the plan, so a plan with a timeline already ran downstream -- it was judged
    by the owner before verdict files existed, and asking for a signature now
    would park every finished episode behind a gate that did not exist when it
    was made."""
    plan = plan_of(ctx)
    return plan.exists() and (plan_verdict.current(plan) or ran_downstream(ctx))


def wants_rewrite(ctx) -> bool:
    return "--rewrite" in (getattr(ctx, "extra", None) or [])


def refusal_lines(out: str) -> list[str]:
    """What the gate printed, verbatim, less the advisories and the blanks."""
    return [line.rstrip() for line in out.splitlines()
            if line.strip() and "advisory:" not in line]


def set_aside(plan: Path) -> Path:
    """A refused draft moves out of plan.json's place so the next run authors again."""
    aside = plan.with_name(REFUSED_ASIDE)
    if aside.exists():
        aside.unlink()
    plan.rename(aside)
    return aside


def draft(ctx, plan: Path, brief: dict, refusals: list[str] | None) -> tuple[int, str]:
    """One round: the writer's plan through write_plan, then the gate on it.

    A draft the CONTRACT refuses is a refusal like the gate's, not a crash:
    ep12's first draft said 'slowly' on four shots, the Episode validators
    raised inside the agent's parse, and the step died before this loop could
    quote the refusal back to the writer."""
    try:
        episode = episode_writer.write(brief, refusals)
    except ValidationError as bad:
        return 1, contract_refusals(bad)
    episode_home.write_plan(plan, episode.model_dump())
    return ctx.capture_script(PLAN_CHECK)


def contract_refusals(bad: ValidationError) -> str:
    """The contract's refusals, one per line, as the gate prints its own."""
    return "\n".join(f"CONTRACT {'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in bad.errors())


def author(ctx, plan: Path) -> None:
    """Brief -> write -> check, improving on the gate's refusals at most MAX_IMPROVE times."""
    brief = plan_brief.build(ctx.book_dir, ctx.number)
    refusals = None
    for round_no in range(MAX_IMPROVE + 1):
        rc, out = draft(ctx, plan, brief, refusals)
        if rc == 0:
            ctx.log(f"plan_check clean on round {round_no}; plan locked at {plan.name}", step_id=STEP_ID)
            return
        refusals = refusal_lines(out)
        ctx.log(f"plan_check refused round {round_no}:\n" + "\n".join(refusals),
                step_id=STEP_ID, level="WARNING")
    if plan.exists():   # every round may have died on the contract before writing one
        set_aside(plan)
    raise Escalation("PLAN", unit_file(ctx, "plan.json"),
                     f"the writer could not satisfy plan_check after {MAX_IMPROVE} rounds; "
                     f"refusals in the log")


def run(ctx) -> None:
    plan = plan_of(ctx)
    if wants_rewrite(ctx) and ran_downstream(ctx):
        ctx.log("--rewrite refused: placed.json exists, this plan already ran downstream",
                step_id=STEP_ID, level="WARNING")
    elif wants_rewrite(ctx) or not plan.exists():
        author(ctx, plan)
    if plan_verdict.current(plan) or ran_downstream(ctx):
        return
    raise Escalation("PLAN", unit_file(ctx, "plan.verdict.json"), "read the plan and sign")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
