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
`studio.plan_ladder` -- improve x2, model_tier x1 -- under
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
from studio import episode_home, gate_policy, judged_gate, plan_ladder, plan_provenance, plan_verdict, step_cli  # noqa: E402
from studio import plan_tags, step_attempts, step_caps  # noqa: E402
from studio.ladder import Ladder  # noqa: E402
from studio.learnings import Learning  # noqa: E402
from studio.judges import plan as plan_judge  # noqa: E402
from studio.judges import verdict as jv  # noqa: E402

STEP_ID = "02"
NAME = "plan"
GPU = False
GATE = "PLAN"
MAX_IMPROVE = 2
"""Tries of the `improve` rung: rounds in which every refusal so far goes back to the writer."""
PLAN_CHECK = "scripts/episode/plan_check.py"
CLIMBS = "plan.climbs"
"""The episode's climb count in attempts.json (owner 2026-10-18): the cap table's `climbs`.  A
climb is one pass of the ladder; a deferral's re-author is the next one.  It is spent at the
entry's FIRST WRITER CALL (D3), never at entry: an entry that writes nothing spends none."""
RESIGN = "plan.resign"
"""A stale flagged signature re-signed over the rows it carries; counted apart from the climbs."""
PARKED = "plan.parked"
"""The one park a tier-1 line buys at the last climb, marked so a relaunch goes on."""


def plan_of(ctx) -> Path:
    return episode_home.plan_path(ctx.book_dir, ctx.number)


def ran_downstream(ctx) -> bool:
    """A timeline beside the plan: this plan already ran; existence only."""
    return episode_home.has_timeline(ctx.book_dir, ctx.number)


def timeline_of_plan(ctx) -> bool:
    """`ran_downstream` sharpened for the aside's cure: a timeline beside the
    plan that was built FROM this plan.  A timeline of another plan (ep21,
    2026-10-08: the aside's own, left by the signed plan step 02 had lost) is
    no run of the stray draft on disk and must not keep the aside from its
    cure -- the ladder climbed the stray for an hour instead."""
    if not ran_downstream(ctx):
        return False
    try:        # through THE door: load_placed refuses a timeline of another plan
        episode_home.load_placed(ctx.book_dir, ctx.number, episode_home.load_plan(ctx.book_dir, ctx.number))
    except (Exception, SystemExit):     # noqa: BLE001 -- a refused draft, or a stale timeline, ran nowhere
        return False
    return True


def rendered(ctx) -> bool:
    """Takes on disk: the plan has been spent on.  The battery guards spend
    BEFORE a render; after it the take gates judge the takes, and the writer
    never rewrites a plan its takes were rendered from (ep13, 2026-09-27)."""
    return any((ctx.home / "takes" / "r2v").glob("T??.mp4"))


def done(ctx) -> bool:
    """plan.json exists AND it is signed, or the unit is GRANDFATHERED.

    Grandfathered: `placed.json` beside the plan.  The timeline is built from
    the plan, so a plan with a timeline already ran downstream -- it was judged
    by the owner before verdict files existed, and asking for a signature now
    would hold every finished episode behind a gate that did not exist when it
    was made."""
    plan = plan_of(ctx)
    return plan.exists() and (plan_verdict.current(plan) or grandfathered(ctx) or rendered(ctx))


def grandfathered(ctx) -> bool:
    """Ran downstream AND never signed: a legacy plan.  One whose signature went
    stale was edited after it was judged (ep12: skipped on 'output exists')."""
    return ran_downstream(ctx) and not (plan_of(ctx).parent / plan_verdict.FILE).exists()


def stale_approve(plan: Path) -> dict | None:
    """The APPROVE whose sha no longer matches the plan's bytes, or None."""
    doc = plan_verdict.read(plan)
    stale = (bool(doc) and doc.get("verdict") == plan_verdict.APPROVE
             and doc.get("plan_sha8") != plan_verdict.plan_sha8(plan))
    return doc if stale else None


def resigned(ctx) -> bool:
    """A stale APPROVE whose bytes moved ONLY through recorded cures
    (plan.cures.jsonl), over a battery that passes NOW, is re-signed with
    zero writer/critic calls (ep18: a mechanical repair lapsed the signature
    and the paid climb ran again on an already-clean plan, $1.05).  A FLAGGED
    signature is also re-signed over a battery that still refuses, when every
    row left is one it already carries (`carried`): one critic read, no writer
    round (Jekyll ep01 Kawajiri: climb 2 spent 10.7 min on one carried G-TWO
    row).  A broken chain or a new or tier-1 row answers False and the climb runs."""
    plan = plan_of(ctx)
    if not plan.exists() or (old := stale_approve(plan)) is None:
        return False
    cures = plan_provenance.chain(plan.parent, old.get("plan_sha8") or "",
                                  plan_verdict.plan_sha8(plan))
    if cures is None:
        return False
    rc, out = ctx.capture_script(PLAN_CHECK)
    if rc != 0 and not carried(old, out):
        return False
    resign(ctx, plan, old, cures, critic_rows(ctx, plan) if rc != 0 else [])
    return True


def carried(old: dict, out: str) -> bool:
    """Every row the battery still prints is one the flagged signature already carries (its gate id,
    at no greater a count), and none is tier 1 (a downstream builder repeats it)."""
    lines = refusal_lines(out)
    now = plan_ladder.gate_counts(plan_ladder.rows_in(lines))
    then = plan_ladder.gate_counts(plan_ladder.rows_in([str(f.get("note") or "") for f in old.get("faults") or []]))
    if not old.get("flagged") or not now or plan_tags.builder_lines(lines):
        return False
    return all(then.get(gate, 0) >= n for gate, n in now.items())


def critic_rows(ctx, plan: Path) -> list[dict]:
    """The critic reads the carried bytes once (no writer round) and its rows ride the new signature;
    a read that fails keeps the signature's own rows."""
    try:
        desk = plan_ladder.Desk(ctx, plan, writer=episode_writer)
        return [f.model_dump() for f in critic(ctx, desk).faults]
    except Exception as why:        # noqa: BLE001 -- a failed read never un-signs a carried plan
        ctx.log(f"{GATE} re-sign: the critic read failed ({str(why)[:160]}); the carried rows stand",
                step_id=STEP_ID, level="WARNING")
        return []


def resign(ctx, plan: Path, old: dict, cures: list[str], critic_faults: list[dict] | None = None) -> None:
    """The old signature carried forward over the cured bytes: same signer,
    same faults (plus the critic's read of a carried battery refusal), same flag -- only the note says
    what moved them.  Counted as `plan.resign`, never as a climb."""
    names = ", ".join(cures) or "none"
    plan_verdict.sign(plan, f"re-signed after mechanical cures: {names}",
                      signed_by=old.get("signed_by") or jv.OWNER,
                      faults=(old.get("faults") or []) + (critic_faults or []), flagged=bool(old.get("flagged")))
    if getattr(ctx, "home", None) is not None:
        step_attempts.spend(ctx.home, RESIGN)
    ctx.log(f"{GATE} re-signed: bytes moved only through recorded cures ({names})", step_id=STEP_ID)


def wants_rewrite(ctx) -> bool:
    return "--rewrite" in (getattr(ctx, "extra", None) or [])


def refusal_lines(out: str) -> list[str]:
    """What the gate printed, verbatim, less the advisories and the blanks."""
    return [line.rstrip() for line in out.splitlines()
            if line.strip() and "advisory:" not in line]


def battery(ctx, desk) -> list[str] | None:
    """plan_check's refusals for the draft as it stands, or None when it passes;
    a draft the contract refused is a refusal like the gate's -- but only while
    there is NO plan on disk to judge.  THE DISK IS THE TRUTH OF A STEP (ep15,
    2026-10-01): a failed improve left its refusals as `pending`, battery()
    answered with that ghost over a VALID plan on disk, and the ladder deferred
    the clean draft under the ghost's note for eleven passes."""
    if desk.pending is not None and not desk.plan.exists():
        return desk.pending
    pending, desk.pending = desk.pending, None
    rc, out = ctx.capture_script(PLAN_CHECK)
    if rc == 0:
        return None
    if pending:
        # ep22 (2026-10-07): the disk plan is refused AND the writer's draft was
        # refused by the contract -- both are the truth; dropping the contract
        # lines hid the real blocker from every rung, the learnings and the brain.
        return refusal_lines(out) + [line for line in pending if line not in out]
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


def restore_climb(ctx, desk) -> bool:
    """A killed climb's checkpoint is restored (C3_verdict #1) unless the plan
    is signed, ran downstream, or a rewrite was asked: then it is retired."""
    plan = desk.plan
    if wants_rewrite(ctx) or plan_verdict.current(plan) or ran_downstream(ctx) or rendered(ctx):
        desk.retire_climb()
        return False
    restored = desk.restore(lambda: judge(ctx, desk))
    if restored:
        ctx.log(f"the climb resumes from its checkpoint: {desk.rungs_done} rung(s) done", step_id=STEP_ID)
    return restored


def clear(ctx, desk) -> Path:
    """The judged gate over the plan: pass -> signed; fault -> the ladder; spent -> a terminal."""
    policy = gate_policy.of(ctx.stage, GATE)
    desk.battery_terminal = policy.battery_terminal or plan_ladder.DEFER
    rungs = judged_gate.Rungs(climb_ladder(ctx, desk), take=desk.take)
    try:
        signed = judged_gate.clear(ctx, GATE, judge=lambda: judge(ctx, desk), sign=desk.sign,
                                   ladder=rungs, terminal=desk.terminal, policy=policy)
    except plan_ladder.BuilderOverClock as why:
        signed = over_clock(ctx, desk, policy, str(why))
    ctx.log(f"{GATE}: {signed.name} written", step_id=STEP_ID)
    retire_aside(ctx, signed)
    return signed


def climb_ladder(ctx, desk) -> Ladder:
    """One climb of the episode's `climbs` (persisted): the last never defers -- it keeps the
    best draft, flagged -- and one past it takes no writer round at all (owner 2026-10-18)."""
    cap, n = step_caps.cap("plan"), climb_number(ctx, desk)
    if n >= cap.climbs:
        desk.battery_terminal = plan_ladder.KEEP_BEST
    if n <= cap.climbs:
        return plan_ladder.ladder_after(desk.rungs_done, MAX_IMPROVE)
    ctx.log(f"CAP plan: {cap.climbs}/{cap.climbs} climbs spent, no writer round; the best draft is kept",
            step_id=STEP_ID, level="WARNING")
    return Ladder([], plan_ladder.KEEP_BEST)


def climb_number(ctx, desk) -> int:
    """This climb's number: the one `enter_climb` captured before the first draft; a desk that never
    entered (a bare ladder) counts as it always did -- a climb resumed from its checkpoint is the one
    already counted."""
    if desk.climb is not None:
        return desk.climb
    if desk.rungs_done or (ctx.home / plan_ladder.CLIMB).exists():
        return max(1, step_attempts.count(ctx.home, CLIMBS))
    return step_attempts.spend(ctx.home, CLIMBS)


def enter_climb(ctx, desk) -> None:
    """Capture this entry's climb number ONCE, before `first_draft` (which would make climb 1 look like
    climb 2), and spend it at the entry's first writer call -- not at entry (D3: attempts.json read
    plan.climbs 3 against a cap of 2 when an entry wrote nothing).  A resumed climb is already counted."""
    counted = bool(desk.rungs_done or (ctx.home / plan_ladder.CLIMB).exists())
    spent = step_attempts.count(ctx.home, CLIMBS)
    desk.climb = max(1, spent) if counted else spent + 1
    if not counted:
        desk.on_write = lambda: step_attempts.spend(ctx.home, CLIMBS)


def climbs_spent(ctx) -> bool:
    return step_attempts.count(ctx.home, CLIMBS) >= step_caps.cap("plan").climbs


def aside_draft(ctx, plan: Path) -> bool:
    """The deferred draft put back as it is; False when there is none or the contract refuses it."""
    aside = ctx.home / plan_ladder.DEFERRED
    draft = episode_home.read_json(aside).get("draft") if aside.exists() else None
    if not draft:
        return False
    try:
        episode_home.write_plan(plan, draft)
    except SystemExit:
        return False
    return True


def first_draft(ctx, desk) -> None:
    """The draft a climb judges: past the episode's climbs the aside's draft as it is, no
    writer round; else the aside edited by the reasoner, or a fresh draft (its seconds and tokens
    are a learnings row, the wall is not moved)."""
    if climbs_spent(ctx) and aside_draft(ctx, desk.plan):
        ctx.log("the plan's climbs are spent: the aside's draft is judged as it is", step_id=STEP_ID)
        return
    started, desk.usage = desk.now(), {}
    try:
        desk.resume() or desk.write(None)
    finally:
        note_draft(ctx, desk, desk.now() - started)
        desk.usage = None


def note_draft(ctx, desk, seconds: float) -> None:
    """One learnings row `draft`: what the first draft cost in seconds and tokens (a bare ctx keeps none)."""
    if not hasattr(ctx, "learn"):
        return
    used = desk.usage or {}
    ctx.learn(Learning(step=STEP_ID, gate=GATE, measured=used.get("total_tokens", 0), action="draft",
                       seconds=seconds, note=f"{used.get('input_tokens', 0)} in, {used.get('output_tokens', 0)} out tokens"))


def tier_one_left(plan: Path) -> list[str]:
    """The tier-1 lines (a downstream builder repeats them) on a kept, flagged plan."""
    doc = plan_verdict.read(plan) or {}
    if not doc.get("flagged"):
        return []
    return plan_tags.builder_lines([str(f.get("note") or "") for f in doc.get("faults") or []])


def park_once(ctx, plan: Path) -> None:
    """At the last climb a kept draft that still carries a tier-1 line parks the unit ONCE,
    naming the line; the next launch goes on with the signed draft."""
    if not climbs_spent(ctx) or step_attempts.marked(ctx.home, PARKED):
        return
    lines = tier_one_left(plan)
    if not lines:
        return
    step_attempts.mark(ctx.home, PARKED)
    raise Deferred(GATE, str(plan_verdict.verdict_path(plan).relative_to(ctx.book_dir)).replace("\\", "/"),
                   "the plan's climbs are spent and a tier-1 line remains: " + "; ".join(lines)[:300])


def over_clock(ctx, desk, policy, why: str) -> Path:
    """The ONE climb past a spent ceiling a BUILDER line buys (C3_verdict #5
    (iv)): <= 3 rungs; still carrying one, the terminal raises SAFETY."""
    ctx.log(f"{GATE}: the clock is spent and the best plan carries a builder line ({why[:160]}); "
            f"one climb past the ceiling", step_id=STEP_ID, level="WARNING")
    desk.over_clock = True
    rungs = judged_gate.Rungs(plan_ladder.ladder_over_clock(MAX_IMPROVE), take=desk.take)
    return judged_gate.clear(ctx, GATE, judge=lambda: judge(ctx, desk), sign=desk.sign,
                             ladder=rungs, terminal=desk.terminal, policy=policy)


def retire_aside(ctx, signed: Path) -> None:
    """A signature retires the aside: a plan.deferred.json left beside a signed
    plan is history, and the next launch's cure_aside_first would restore it
    over the plan (ep19 launch07: a day-old 12-shot aside replaced the signed
    21-shot plan and the climb ran again)."""
    aside = ctx.home / plan_ladder.DEFERRED
    if signed.name != plan_ladder.DEFERRED and aside.exists():
        aside.unlink()
        ctx.log("the aside is retired: the plan is signed", step_id=STEP_ID)


def deferred_note(aside: Path) -> str:
    """The terminal verdict's summary as the deferred file holds it."""
    return episode_home.read_json(aside).get("note", "deferred")


def report(ctx) -> None:
    """A rendered plan is judged in REPORT mode: the battery runs, its refusals
    are logged, nothing is rewritten (ten-agent debate 2026-09-27: G-STILL would
    have named ep13's shots 9, 18 and 19, all visible on the master)."""
    rc, out = ctx.capture_script(PLAN_CHECK)
    said = "\n".join(refusal_lines(out)) if rc else "clean"
    ctx.log(f"the plan's takes are rendered: battery in report mode, no rewrite:\n{said}",
            step_id=STEP_ID, level="WARNING")


def cure_aside_first(ctx, plan: Path) -> None:
    """A draft an earlier run deferred is cured under today's code -- mechanical
    cures only, $0 -- before any paid round judges the plan on disk (ep19
    launch04: the aside passed every gate, the stale plan.json paid the writer,
    and the episode crossed its $3 wall)."""
    if not (ctx.home / plan_ladder.DEFERRED).exists() or plan_verdict.current(plan) or timeline_of_plan(ctx):
        return
    if not episode_home.read_json(ctx.home / plan_ladder.DEFERRED).get("draft"):
        ctx.log("the aside holds no draft (the climb never wrote a plan): nothing to cure", step_id=STEP_ID)
        return
    rc, out = ctx.capture_script("scripts/episode/plan_repair.py", "--from-aside", "--no-llm")
    ctx.log("aside cured before any paid round:\n" + out[-800:], step_id=STEP_ID,
            level="WARNING" if rc else "INFO")


def narrator_or_stop(ctx) -> str:
    """The book's narrator, or the STOP before any writer is asked (Jekyll ep01,
    2026-10-13: an unset narrator let a refusal loop pick a cast member)."""
    from studio import book_narrator
    try:
        return book_narrator.require(ctx.book_dir)
    except SystemExit as why:
        ctx.log(str(why), step_id=STEP_ID, level="ERROR")
        raise


def run(ctx) -> None:
    # CLOCKED (five-hour plan fix 6): ep14 spent 3.3 h in this step and
    # timing.jsonl never saw a second of it.
    from studio import episode_clock
    with episode_clock.timed(ctx.book_dir, ctx.number, "plan"):
        plan = plan_of(ctx)
        if not wants_rewrite(ctx) and resigned(ctx):
            return      # BEFORE the aside is read: ep19 launch07 (2026-10-07 15:10Z) restored
                        # a day-old aside over a plan whose signature a recorded cure had lapsed
        narrator_or_stop(ctx)
        if not wants_rewrite(ctx):
            cure_aside_first(ctx, plan)
        desk = plan_ladder.Desk(ctx, plan, writer=episode_writer)
        restored = restore_climb(ctx, desk)
        enter_climb(ctx, desk)
        if wants_rewrite(ctx) and ran_downstream(ctx):
            ctx.log("--rewrite refused: placed.json exists, this plan already ran downstream",
                    step_id=STEP_ID, level="WARNING")
        elif not restored and (wants_rewrite(ctx) or not plan.exists()):
            first_draft(ctx, desk)
        if plan_verdict.current(plan) or grandfathered(ctx):
            return
        if resigned(ctx):
            return
        if rendered(ctx):
            report(ctx)
            return
        signed = clear(ctx, desk)
    if signed.name == plan_ladder.DEFERRED:
        # THE CURE TABLE BEFORE THE DEFERRAL SURFACES (2026-10-01): 97% of
        # ep14-15's plan hours were paid rewrites of MECHANICAL faults whose
        # cures are template arithmetic.  plan_repair runs them in seconds on
        # the aside's best draft; a clean battery re-enters the judge in the
        # SAME run, and only CREATIVE faults ever cost another writer round.
        rc, out = ctx.capture_script("scripts/episode/plan_repair.py", "--from-aside")
        ctx.log("plan_repair:\n" + out[-800:], step_id=STEP_ID,
                level="WARNING" if rc else "INFO")
        if rc == 0:
            fresh = plan_ladder.Desk(ctx, plan_of(ctx), writer=episode_writer)
            enter_climb(ctx, fresh)
            signed = clear(ctx, fresh)
    if signed.name == plan_ladder.DEFERRED:
        raise Deferred(GATE, str(signed.relative_to(ctx.book_dir)).replace("\\", "/"), deferred_note(signed))
    park_once(ctx, plan_of(ctx))


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
