#!/usr/bin/env python
"""Step 02 of the episode stage: the plan, judged before anything is voiced or drawn.

    uv run python scripts/episode/step_02_plan.py <codex_id> <n> [--rewrite]

    brief (02_01)  ->  write (02_02)  ->  battery + critic (02_03)  ->  ladder (02_04)
                                                                    ->  signed (02_05)

The brief is gathered off disk (`studio.plan_brief`); the writer is the
registered agent (`agents.episode_writer`); the judge is two-fold: the
battery (`plan_check`, launched as a script so it reads the draft exactly as
every later step will) and, once the battery passes, the critic
(`agents.plan_reader` lists, `studio.judges.plan` judges).  A fault climbs
`studio.plan_ladder` -- improve x2, fresh_brief x1, model_tier x1 -- under
`judged_gate.clear`, and ends in one of two terminals that ask nobody: a
critic fault keeps the best draft and signs it flagged; a battery that never
passed defers the unit (plan.deferred.json, no signature, an audit row).
The plan is written only through `episode_home.write_plan`; the signature is
`plan.verdict.json` beside it, bound to its sha8, signed `judge:plan@1`.

`--rewrite` authors a fresh plan over an unsigned one, and never over a plan
that already ran downstream (`placed.json` beside it).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents import episode_writer, plan_reader  # noqa: E402
from studio.deferral import Deferred  # noqa: E402
from studio import episode_home, gate_policy, judged_gate, plan_ladder, plan_verdict, step_cli  # noqa: E402
from studio.judges import plan as plan_judge  # noqa: E402

STEP_ID = "02"
NAME = "plan"
GPU = False
GATE = "PLAN"
MAX_IMPROVE = 2
"""Tries of the `improve` rung: rounds in which every refusal so far goes back to the writer."""
PLAN_CHECK = "scripts/episode/plan_check.py"


def plan_of(ctx) -> Path:
    return episode_home.plan_path(ctx.book_dir, ctx.number)


def ran_downstream(ctx) -> bool:
    """A timeline beside the plan: this plan already ran; existence only."""
    return episode_home.has_timeline(ctx.book_dir, ctx.number)


def done(ctx) -> bool:
    """plan.json exists AND it is signed, or the unit is GRANDFATHERED.

    Grandfathered: `placed.json` beside the plan.  The timeline is built from
    the plan, so a plan with a timeline already ran downstream -- it was judged
    by the owner before verdict files existed, and asking for a signature now
    would hold every finished episode behind a gate that did not exist when it
    was made."""
    plan = plan_of(ctx)
    return plan.exists() and (plan_verdict.current(plan) or grandfathered(ctx))


def grandfathered(ctx) -> bool:
    """Ran downstream AND never signed: a legacy plan.  One whose signature went
    stale was edited after it was judged (ep12: skipped on 'output exists')."""
    return ran_downstream(ctx) and not (plan_of(ctx).parent / plan_verdict.FILE).exists()


def wants_rewrite(ctx) -> bool:
    return "--rewrite" in (getattr(ctx, "extra", None) or [])


def refusal_lines(out: str) -> list[str]:
    """What the gate printed, verbatim, less the advisories and the blanks."""
    return [line.rstrip() for line in out.splitlines()
            if line.strip() and "advisory:" not in line]


def battery(ctx, desk) -> list[str] | None:
    """plan_check's refusals for the draft as it stands, or None when it passes;
    a draft the contract refused is a refusal like the gate's."""
    if desk.pending is not None:
        return desk.pending
    rc, out = ctx.capture_script(PLAN_CHECK)
    if rc == 0:
        return None
    lines = refusal_lines(out)
    ctx.log("plan_check refused:\n" + "\n".join(lines), step_id=STEP_ID, level="WARNING")
    return lines


def critic(ctx, desk):
    """The critic reads the plan as plain text; the same bytes get the same verdict."""
    key = plan_verdict.plan_sha8(desk.plan)
    if key not in desk.judged:
        brief, doc = desk.brief_(), episode_home.read_json(desk.plan)
        readings = plan_reader.read(plan_reader.plain_text(doc), plan_judge.rows_of(brief),
                                    chapter_text=brief.get("chapter_text"))
        desk.judged[key] = plan_judge.judge(doc, brief, readings)
    return desk.judged[key]


def judge(ctx, desk):
    """The battery first (free, deterministic); the critic only on a draft it let through."""
    refused = battery(ctx, desk)
    if refused is not None:
        return plan_ladder.battery_verdict(refused)
    return critic(ctx, desk)


def clear(ctx, desk) -> Path:
    """The judged gate over the plan: pass -> signed; fault -> the ladder; spent -> a terminal."""
    policy = gate_policy.of(ctx.stage, GATE)
    desk.battery_terminal = policy.battery_terminal or plan_ladder.DEFER
    rungs = judged_gate.Rungs(plan_ladder.ladder(MAX_IMPROVE), take=desk.take)
    signed = judged_gate.clear(ctx, GATE, judge=lambda: judge(ctx, desk), sign=desk.sign,
                               ladder=rungs, terminal=desk.terminal, policy=policy)
    ctx.log(f"{GATE}: {signed.name} written", step_id=STEP_ID)
    return signed


def deferred_note(aside: Path) -> str:
    """The terminal verdict's summary as the deferred file holds it."""
    return episode_home.read_json(aside).get("note", "deferred")


def run(ctx) -> None:
    plan = plan_of(ctx)
    desk = plan_ladder.Desk(ctx, plan, writer=episode_writer)
    if wants_rewrite(ctx) and ran_downstream(ctx):
        ctx.log("--rewrite refused: placed.json exists, this plan already ran downstream",
                step_id=STEP_ID, level="WARNING")
    elif wants_rewrite(ctx) or not plan.exists():
        desk.resume() or desk.write(None)
    if plan_verdict.current(plan) or grandfathered(ctx):
        return
    signed = clear(ctx, desk)
    if signed.name == plan_ladder.DEFERRED:
        raise Deferred(GATE, str(signed.relative_to(ctx.book_dir)).replace("\\", "/"), deferred_note(signed))


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
