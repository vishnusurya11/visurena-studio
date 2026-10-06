#!/usr/bin/env python
"""Step 09 -- shoot: the takes, their two machine gates, the strip, the judge.

    uv run python scripts/episode/step_09_shoot.py <codex_id> <n> [--retake=3,4 --why="..."] [--last]

Refuses unless the panels carry all three verdicts (panel_dq.json,
panel_content.json, a current eye).  The render approval is the RENDER row
of gates.yaml (auto, decision 2026-09-24-episode-department) and the
episode's time ceiling: `can_afford` before the render, never a flag typed
by hand.  Then wraps, in order: scripts/episode/takes_r2v.py --from-refs
--no-ends (the slow one), take_dq.py, take_content_check.py, take_strip.py.
Then the EYE_TAKES row: `judge:take_eye@1` reads the kept takes and signs
takes/r2v/eye_<sha8>.json -- pass, or flagged at the take ladder's terminal
rung (keep_best, or a still from the passed panel); it climbs seed -> move
type -> shorter take -> head cut -> replan cell first, each a batched retake
round.  Nobody is asked.  One GPU, one stage: every GPU script waits for the
queue.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode.step_08_panels import panel_refusals  # noqa: E402
from studio import episode_clock, episode_home, eye_verdict, gate_policy, judged_gate, step_cli, take_currency, take_ladder  # noqa: E402
from studio.judges import take_eye  # noqa: E402
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, Budget  # noqa: E402

STEP_ID = "09"
NAME = "shoot"
GPU = True
TAKES = Path("takes") / "r2v"
RENDER = "render"
"""The approval kind takes_r2v.py demands on its argv."""
GATE = "EYE_TAKES"
CLONES = take_eye.facenet_clones
"""The judge's clone reader; a test injects its own."""


def takes_of(take_dir: Path) -> list[Path]:
    """The kept takes (never a displaced attempt)."""
    return sorted(Path(take_dir).glob("T??.mp4"))


def sha8(path: Path) -> str:
    """The first eight hex digits of the file's sha256: take_dq.take_sha8's
    rule, inlined -- that module's model loads are heavy."""
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def dq_current(t: Path) -> bool:
    """The dq verdict exists and was measured on EXACTLY these bytes."""
    path = t.with_suffix(".dq.json")
    if not path.exists():
        return False
    doc = episode_home.read_json(path)
    return isinstance(doc, dict) and doc.get("take_sha8") == sha8(t)


def content_current(t: Path) -> bool:
    """The content verdict exists and is no older than the take.  Content
    records carry no sha; its only writer (take_content_check) always
    re-reads the frames, so mtime is the honest bound."""
    path = t.with_suffix(".content.json")
    return path.exists() and path.stat().st_mtime >= t.stat().st_mtime


def judged(takes: list[Path]) -> bool:
    """Whether every kept take carries both machine verdicts, measured on the
    bytes that are there NOW.  Existence alone let a retaken T??.mp4 outlive
    its pre-retake verdicts (qc: T00, T14, T18-T21 'unjudged')."""
    return all(dq_current(t) and content_current(t) for t in takes)


def card_pictures(c: dict, book: Path, number: int) -> list[Path]:
    from scripts.episode import takes_r2v
    return takes_r2v.card_pictures(c, book, number)


def stale_takes(ctx) -> list[int]:
    """Takes that are not the take their card in prompts.json would render now.
    ep12: shot 16 was re-planned and the runner skipped step 09 on existence."""
    path = ctx.home / TAKES / "prompts.json"
    cards = episode_home.read_json(path) if path.exists() else []
    return [int(c["index"]) for c in cards
            if not take_currency.is_current(c.get("prompt") or "", ctx.home / TAKES / f"T{int(c['index']):02d}.mp4",
                                            pictures=card_pictures(c, ctx.book_dir, ctx.number),
                                            canvas=episode_canvas(ctx))]


def episode_canvas(ctx) -> tuple[int, int]:
    """This episode's (W, H), read off the plan.  ep14 (2026-09-30): seven
    portrait takes passed done() into a square master; the canvas is part of
    what a rendered take must prove."""
    from studio import canvas as cv
    plan = ctx.home / "plan.json"
    aspect = (episode_home.read_json(plan).get("aspect") or cv.DEFAULT) if plan.exists() else cv.DEFAULT
    return cv.size(aspect)


def done(ctx) -> bool:
    takes = takes_of(ctx.home / TAKES)
    return (bool(takes) and judged(takes) and eye_verdict.passed(ctx.home / TAKES, takes)
            and not stale_takes(ctx))


def approved(policy: gate_policy.Policy) -> str:
    """The render flag, earned from the RENDER row: registered auto with its
    decision id, so no person types it and the ceiling is the brake."""
    if policy.state != "auto":
        raise SystemExit(f"REFUSED: RENDER is {policy.state} in gates.yaml; nobody signs a render by hand")
    return f"--approved={RENDER}"


def opened(ctx) -> Budget:
    """The step's budget share: the context's own budget when it carries one
    (opened through open_step where the context has it), else a fresh one."""
    if hasattr(ctx, "open_step"):
        ctx.open_step(STEP_ID)
        return ctx.budget
    budget = getattr(ctx, "budget", None) or Budget(EPISODE_CEILING_SECONDS, EPISODE_SHARES)
    budget.start(STEP_ID)
    return budget


def share_missing(room: Path, shots: list[dict]) -> float:
    """The share of the plan's shots that still have no take: what a render
    round would actually draw.  ep14 (2026-09-28): a resume with all 30 takes
    on disk was refused for the price of rendering them again."""
    if not shots:
        return 1.0
    missing = [s for s in shots if not (Path(room) / f"T{int(s['index']):02d}.mp4").exists()]
    return len(missing) / len(shots)


def affordable(ctx) -> tuple[bool, float, float]:
    """(can the render run, what it costs, what the ceiling leaves this step).
    The cost is the step's norm scaled to the takes still to render; the
    ladder prices its own rungs."""
    budget = opened(ctx)
    norm = episode_clock.stage_norm("takes", episode_clock.conditions(ctx.book_dir, ctx.number))
    plan = ctx.home / "plan.json"
    shots = episode_home.read_json(plan).get("shots") or [] if plan.exists() else []
    cost = norm * share_missing(ctx.home / TAKES, shots)
    return budget.can_afford(STEP_ID, cost), cost, budget.remaining(STEP_ID)


def records_of(room: Path) -> dict[int, dict]:
    path = room / "shots.json"
    return {r["index"]: r for r in episode_home.read_json(path)} if path.exists() else {}


def timed_judge(ctx, read):
    """One eye pass, stamped in timing.jsonl (five-hour plan fix 6: ~2.6 h of
    ep14's eye reads were invisible to the clock)."""
    from studio import episode_clock
    with episode_clock.timed(ctx.book_dir, ctx.number, "take_eye"):
        return read()


def judge_takes(ctx, flag: str) -> Path:
    """The EYE_TAKES row: the take eye over the kept takes, the take ladder
    under the ceiling, a still or keep_best at the end; signed in the judge's name."""
    room = ctx.home / TAKES
    plan = episode_home.load_plan(ctx.book_dir, ctx.number)
    return judged_gate.clear(
        ctx, GATE,
        judge=lambda: timed_judge(ctx, lambda: take_eye.judge(takes_of(room), plan=plan, clones=CLONES)),
        sign=lambda v: eye_verdict.sign_verdict(room, takes_of(room), v),
        ladder=take_ladder.rungs(ctx, plan, flag, records_of(room)),
        terminal=take_ladder.terminal_for(ctx, plan))


def round_zero(room: Path) -> bool:
    """No kept take yet: the episode's FIRST render.  The ceiling binds
    retakes; round 0 runs regardless (ep15, 2026-10-01: the plan fight spent
    the whole ceiling before one take existed, and the refusal left the
    terminals nothing to keep -- a unit that can never finish)."""
    return not takes_of(room)


def run(ctx) -> None:
    if why := panel_refusals(ctx.home):
        raise SystemExit("REFUSED: the takes wait on the panels: " + "; ".join(why))
    flag = approved(gate_policy.of(ctx.stage, "RENDER"))
    ok, cost, left = affordable(ctx)
    if not ok and cost <= 0:
        # NOTHING LEFT TO RENDER: the pass only measures and judges, which is
        # exactly what a spent ceiling demands (terminals, not renders) -- a
        # zero-cost refusal would park the unit forever (ep15, 2026-10-01).
        ctx.log(f"ceiling leaves {left:.0f} s and the takes want 0 s -- judging only",
                step_id=STEP_ID, level="WARNING")
    elif not ok and round_zero(ctx.home / TAKES):
        ctx.log(f"the takes want {cost:.0f} s and the ceiling leaves {left:.0f} s -- ROUND 0 "
                f"renders anyway: the terminals need a best take to keep", step_id=STEP_ID,
                level="WARNING")
    elif not ok:
        raise SystemExit(f"REFUSED: the takes want {cost:.0f} s and the episode ceiling leaves "
                         f"{left:.0f} s; a run over the ceiling takes terminal rungs, not renders")
    extra = getattr(ctx, "extra", None) or []
    ctx.run_script("scripts/episode/takes_r2v.py", "--from-refs", "--no-ends", flag,
                   *extra, gpu=GPU, clock="takes")
    take_ladder.measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json")
    take_ladder.measured(ctx, "scripts/episode/take_content_check.py", "take_content", ".content.json")
    ctx.run_script("scripts/episode/take_strip.py", clock="strip")
    if not takes_of(ctx.home / TAKES):
        raise SystemExit(f"REFUSED: no takes under {TAKES.as_posix()}/ after the render")
    judge_takes(ctx, flag)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
