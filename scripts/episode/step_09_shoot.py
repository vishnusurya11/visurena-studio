#!/usr/bin/env python
"""Step 09 -- shoot: the takes, their two machine gates, the strip, the judge.

    uv run python scripts/episode/step_09_shoot.py <codex_id> <n> [--retake=3,4 --why="..."] [--last]

Refuses unless the panels carry all three verdicts (panel_dq.json,
panel_content.json, a current eye).  The render approval is the RENDER row
of gates.yaml (auto, decision 2026-09-24-episode-department) and the
episode's time ceiling: `can_afford` before the render, never a flag typed
by hand.  Then two lanes (studio/take_overlap.py, decision
2026-10-14-gpu-never-waits-for-checks): scripts/episode/takes_r2v.py --from-refs
--no-ends renders back to back while take_dq.py --cpu-only measures each take
as it lands, and a dq-borne cure is queued as the early round behind the first
renders; then the GPU window (take_dq's serial pass, take_content_check.py),
take_strip.py.  A take that passes its dq and is wide, full or small-faced is
owed a FACE REFINE (09_07, owner 2026-10-17): its face crops re-render on the GPU
lane right behind the renders (studio/take_overlap.Refines), and whatever the
ladder leaves owed is refined once after it -- the first thing cut for time.
A take whose refine refused a planned 20-40 px face then draws ONCE on the
1024 graph (09_08, scripts/episode/tiny_face.py), kept only if every take gate
passes it.
Then the EYE_TAKES row: `judge:take_eye@1` reads the kept takes and signs
takes/r2v/eye_<sha8>.json -- pass, or flagged at the take ladder's terminal
rung (keep_best, or a still from the passed panel); it climbs seed -> move
type -> shorter take -> head cut -> replan cell first, each a batched retake
round.  Nobody is asked.  One GPU, one stage: every GPU script waits for the
queue.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode.step_08_panels import panel_refusals  # noqa: E402
from studio import episode_clock, episode_home, eye_verdict, gate_policy, judged_gate, step_caps, step_cli, take_currency, take_ladder  # noqa: E402
from studio.judges import take_eye  # noqa: E402
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, Budget  # noqa: E402

STEP_ID = "09"
NAME = "shoot"
GPU = True
TAKES = Path("takes") / "r2v"
RENDER = "render"
"""The approval kind takes_r2v.py demands on its argv."""
GATE = "EYE_TAKES"
REFINE = "scripts/episode/face_refine.py"
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
    """The dq verdict exists, was measured on EXACTLY these bytes, and owes no
    GPU row (a CPU-lane verdict's deferred leak is measured after the renders)."""
    path = t.with_suffix(".dq.json")
    if not path.exists():
        return False
    doc = episode_home.read_json(path)
    return isinstance(doc, dict) and not doc.get("deferred") and doc.get("take_sha8") == sha8(t)


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
            and not stale_takes(ctx) and not reset_since_verdict(ctx, takes))


def reset_since_verdict(ctx, takes: list[Path]) -> bool:
    """The owner's retry stamped the clock AFTER the verdict was signed: a
    terminal signed on a spent clock (ep19 2026-10-07 18:19Z: keep_best at
    attempt 0 over four frozen takes and two hard cuts) is re-judged with the
    fresh one instead of read as done and sent to publish."""
    from datetime import datetime
    from studio import run_budget
    stamp = run_budget.clock_reset_at(ctx.home)
    target = eye_verdict.path(ctx.home / TAKES, eye_verdict.fingerprint(takes))
    if not stamp or not target.exists():
        return False
    return datetime.fromtimestamp(target.stat().st_mtime).isoformat(timespec="seconds") < stamp


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


def signed_for(ctx, room: Path) -> Path | None:
    """The eye verdict already signed for EXACTLY these takes' bytes (every sha8 equal to the verdict's
    files) and not older than the owner's retry stamp; else None.  Re-entry keeps it: no eye read, no
    duplicate audit row (ep01: the eye re-read 28 panels for 2 changed)."""
    takes = takes_of(room)
    if not takes or reset_since_verdict(ctx, takes) or not eye_verdict.passed(room, takes):
        return None
    return eye_verdict.path(room, eye_verdict.fingerprint(takes))


def judge_takes(ctx, flag: str) -> Path:
    """The EYE_TAKES row: the take eye over the kept takes, the take ladder
    under the ceiling, a still or keep_best at the end; signed in the judge's name.
    A verdict already signed for these bytes stands (signed_for)."""
    room = ctx.home / TAKES
    if kept := signed_for(ctx, room):
        print(f"EYE_TAKES: the signed verdict {kept.name} names these takes; kept, not re-judged", flush=True)
        return kept
    plan = episode_home.load_plan(ctx.book_dir, ctx.number)
    return judged_gate.clear(
        ctx, GATE,
        judge=lambda: timed_judge(ctx, lambda: take_eye.judge(takes_of(room), plan=plan, clones=CLONES)),
        sign=lambda v: eye_verdict.sign_verdict(room, takes_of(room), v),
        ladder=take_ladder.rungs(ctx, plan, flag, records_of(room)),
        terminal=take_ladder.terminal_for(ctx, plan, draws=take_ladder.recorded_draw))


def round_zero(room: Path) -> bool:
    """No kept take yet: the episode's FIRST render.  The ceiling binds
    retakes; round 0 runs regardless (ep15, 2026-10-01: the plan fight spent
    the whole ceiling before one take existed, and the refusal left the
    terminals nothing to keep -- a unit that can never finish)."""
    return not takes_of(room)


DQ_PASS_SECONDS = 550.0
"""A full take_dq re-measure, priced (Jekyll HEL ep01: 548 s over 23 takes)."""


def dq_flags(ctx) -> list[str]:
    """`--ceiling-spent` only when re-measuring would eat the downstream reserve:
    then a take's verdict on the same bytes stands under moved measuring code.
    Past the 5 h ceiling with room under 6 h the checks run (owner 2026-10-14)."""
    budget = getattr(ctx, "budget", None)
    return ["--ceiling-spent"] if budget is not None and budget.checks_cut(STEP_ID, DQ_PASS_SECONDS) else []


def first_wall_line(seconds: float) -> str:
    """The CAP line when the first renders ran past the `takes` wall (120 min), else ''."""
    wall = step_caps.wall_s("takes")
    return step_caps.cap_line("takes", 1, 1, seconds, 0) + " -- first renders over the wall" if seconds >= wall else ""


def say_first_wall(ctx, began: float) -> None:
    """After the lanes (the safe boundary): say an overrun; the ladder's retakes read the cap table."""
    if line := first_wall_line(time.time() - began):
        print(line, flush=True)
        ctx.log(line, step_id=STEP_ID, level="WARNING")


def shoot(ctx, flag: str) -> None:
    """The two lanes (decision 2026-10-14-gpu-never-waits-for-checks): the
    renders back to back, each take's CPU check as it lands, a dq-borne cure
    queued as the early round right behind the first renders."""
    from studio import take_overlap
    extra = tuple(getattr(ctx, "extra", None) or [])
    take_overlap.shoot(ctx, ["--from-refs", "--no-ends", flag], extra=extra, early=True,
                       check_flags=tuple(dq_flags(ctx)), refine=take_overlap.Refines(ctx))


def gpu_window(ctx) -> None:
    """Once the lanes are idle: the serial dq pass (cache hits, a dying check's
    takes, a deferred leak measured with the embedder), then the VL content
    read in one model load.  Never between renders."""
    take_ladder.measured(ctx, "scripts/episode/take_dq.py", "take_dq", ".dq.json", *dq_flags(ctx))
    take_ladder.measured(ctx, "scripts/episode/take_content_check.py", "take_content", ".content.json")


def inputs_wall(ctx) -> None:
    """After take_dq --attempts and the ladder: each kept take's staged picture
    names, then STOP on any take whose graph staged a superseded or redrawn
    picture (G-TAKE-INPUTS).  Jekyll HEL ep01 iter4: T06 was kept on the lace
    sheet's 95 and nothing printed which sheet it ran with."""
    from scripts.episode.assemble import stills_of
    from studio import take_inputs
    room = ctx.home / TAKES
    audited = take_inputs.audit(list(records_of(room).values()), ctx.book_dir, ctx.number,
                                skip=set(stills_of(room, ctx.book_dir)))
    for i, v in sorted(audited.items()):
        print(f"T{i:02d} staged {', '.join(v.staged) or 'nothing'} | {v.said()}", flush=True)
    print(take_inputs.count_line(audited), flush=True)
    take_inputs.wall(audited, who="step 09 stops: G-TAKE-INPUTS")


def refine_rest(ctx) -> None:
    """09_07 after the ladder: every selected take still owed a face refine (a
    retake, a swapped attempt) in ONE GPU run -- or none, cut first, when the
    clock's reserve needs the time (logged and recorded in refine.json)."""
    from scripts.episode import face_refine as cli
    from studio import face_refine
    owed = cli.owed(ctx.book_dir, ctx.number)
    if not owed:
        return
    price = sum(owed.values())
    if face_refine.cut(getattr(ctx, "budget", None), STEP_ID, price):
        cli.record_cut(ctx.home / TAKES, sorted(owed), price, ctx.book_dir, ctx.number)
        ctx.log(f"REFINE CUT: the clock's reserve needs {price:.0f} s; takes {sorted(owed)} keep their faces",
                step_id=STEP_ID, level="WARNING")
        return
    ctx.run_script(REFINE, *map(str, sorted(owed)), gpu=True)


def tiny_face_rung(ctx, flag: str) -> None:
    """09_08 after the refine: a take whose refine refused a planned 20-40 px face draws once on the
    1024 graph (scripts/episode/tiny_face.py); a kept draw changed bytes, so the eye signs again,
    its inputs are walled and its new bytes refined.  Never a loop: one pass, one draw per take."""
    from scripts.episode import tiny_face
    judge = lambda take: take_eye.judge([take], plan=episode_home.load_plan(ctx.book_dir, ctx.number),  # noqa: E731
                                        clones=CLONES)
    if tiny_face.rung(ctx, flag, judge, tuple(dq_flags(ctx))):
        judge_takes(ctx, flag)
        inputs_wall(ctx)
        refine_rest(ctx)


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
    elif not ok:
        # FIRSTS ARE NEVER REFUSED, ONLY REPEATS (C3_verdict #5 (i)): `cost` is
        # the takes MISSING on disk; they render, the ladder's retakes are
        # terminal at a spent clock.  Refusing here parked a half-rendered
        # round 0 forever (step 09 raised with 10 of 24 takes on disk).
        ctx.log(f"the missing takes want {cost:.0f} s and the ceiling leaves {left:.0f} s -- they "
                f"render anyway (firsts); every retake is terminal", step_id=STEP_ID, level="WARNING")
    began = time.time()
    shoot(ctx, flag)
    say_first_wall(ctx, began)
    gpu_window(ctx)
    ctx.run_script("scripts/episode/take_strip.py", clock="strip")
    if not takes_of(ctx.home / TAKES):
        raise SystemExit(f"REFUSED: no takes under {TAKES.as_posix()}/ after the render")
    judge_takes(ctx, flag)
    inputs_wall(ctx)
    refine_rest(ctx)
    tiny_face_rung(ctx, flag)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
