"""Step 07 -- clips: one take per beat, its person read against its reference.

THE ROUND IS THE UNIT, not the beat.  Run 10 measured 15.76 min a take of
which 8.3 was a MODEL SWAP: reading a take's face freed the engine, which
unloaded H3's DiT, its text encoder and both VAEs, and the next take
re-streamed 16 GB off the spinning disk the models live on.  So a round
renders every live beat's next take back to back with H3 resident, unloads
ONCE, reads every contact sheet in one Qwen3-VL session, and gates the lot;
the beats that failed climb a rung and ask for the next round.

Three frames of every take are read by the vision model into a trait card
(`studio.describe`) and compared with the reference sheet's card: DISTINCT_AT
or more traits apart is not the same person.  Such a take climbs seed x2 and
then a whole-take close-up (the FORM changes, the beat does not).  The terminal
rung never asks: it ships the BEST take of the beat capped at a short shot.  A
beat is dropped only when no take exists at all -- no time for a first render,
or the render itself failed.  Every take is kept under clips/takes/; the chosen
one is clips/<beat>.mp4, which is what the cut reads.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Callable

from scripts.trailer.build_clips import (SEED_BASE, bound_slots, is_complete, recipe_for,
                                         render_take, take_values)
from studio.clip_cache import is_current, sidecar_for, stored_fingerprint
from studio.describe import (DISTINCT_AT, TIMEOUT, TraitCard, describe, describe_frames,
                             differences, distance, known, patiently, reader, same_look,
                             shared, verifiable)
from studio.frames import frame_at, frame_times
from studio.ladder import Climb, Ladder, Rung
from studio.learnings import Learning, load
from studio.trailer_assemble import HEAD_TRIM, clip_seconds

STEP_ID = "07"
NAME = "clips"
RENDER_SECONDS = 16 * 60
"""The FALLBACK cycle, measured on run 10: 19 takes between 12:36 and 17:32,
15.76 min each.  It stays at the last measured truth until a run measures a
new one -- `render_seconds` below reads what the rounds of the last run
actually cost, and that is what the next plan is sized on.  Lowering this by
argument is how run 10 planned 25 setups and dropped six of them."""
SESSION_SECONDS = 4 * 60
"""One reader session: the unload, Qwen3-VL off the spinning disk, first sheet.

Run 10 paid this per TAKE (3.7 min measured) because every read freed the
engine first.  Paid once per round, it is the whole swap cost of the round.
Run 11 measures it -- the `read` learning below is that measurement."""
SHEET_SECONDS = 20.0
"""Each further contact sheet read in the same session, with the model already
resident.  Run 5's step 02 measured a resident read at about 4 s; this is that
with room, and run 11 replaces it with the truth."""
CYCLE, READ = "cycle", "read"
MEASURED = (CYCLE, READ)
"""Gates that record what a round COST rather than what it judged.  The
retrospect reads these to state the real cycle; they are not rungs."""
SHORT_SHOT = 0.6
"""A take whose face never bound may still carry a cut this short: too brief
to read a wrong face, long enough to keep the beat's place in the metre."""
RETRY_COST = RENDER_SECONDS + SESSION_SECONDS
"""What a reroll ROUND costs: one render and the reader session that must
follow it.  Run 6's rule -- a retry may cost this beat, never a later one --
is structural now: every beat's first take is rendered in round one, so a
reroll can only ever spend another reroll."""
LADDER = Ladder([Rung("reroll_seed", RETRY_COST, tries=1),
                 Rung("alternate_setup", RETRY_COST, tries=1)], terminal="short_shot")
"""One reroll: a seed moves the reading about half a trait (run 6, B12: 4.0
then 3.5), so the second retry is a framing the reader can see the face in."""
DROPPED = "drop_beat"


class TakeFailed(RuntimeError):
    """The renderer produced no video; not a gate, a fact about the machine."""


def read_seconds(sheets: int) -> float:
    """What reading `sheets` contact sheets costs in ONE session: the unload
    and the load once, then a sheet at a time while the reader is resident."""
    if sheets <= 0:
        return 0.0
    return SESSION_SECONDS + SHEET_SECONDS * (sheets - 1)


def take_cost(staged: int) -> float:
    """What adding one more take to a round costs: its render, and its share
    of the one reader session the round ends with.  A take rendered with no
    time left to read it ships ungated, which is worse than not rendering it."""
    return RENDER_SECONDS + read_seconds(staged + 1) - read_seconds(staged)


def render_seconds(rows: list[Learning]) -> float:
    """The cycle a take actually cost, as the runs of this book measured it.

    `RENDER_SECONDS` is a number a person typed; this is the machine's own
    answer, the median over every round that measured one, and the median so
    a single stalled round cannot resize the next plan."""
    took = [float(row.measured) for row in rows
            if row.step == STEP_ID and row.gate == CYCLE
            and isinstance(row.measured, (int, float))]
    return median(took) if took else float(RENDER_SECONDS)


def render_seconds_for(ctx) -> float:
    """This book's measured cycle, for step 06 to size its plan on."""
    return render_seconds(load(ctx.learnings_path))


def seed_for(index: int, rung: Rung, i: int) -> int:
    base = SEED_BASE + index * 7
    return base + 5000 * (i + 1) if rung.name == "alternate_setup" else base + 1000 * i


def reference_of(book: Path, refs: dict, bound: list[str]) -> tuple[str | None, TraitCard | None]:
    """The sheet a take's person is read against: its first bound character.
    Step 02 wrote the sheet's card; a refs.json without one is read now."""
    char = next((r for r in bound if r.startswith("char-")), None)
    if char is None:
        return None, None
    traits = (refs[char].get("identity") or {}).get("traits")
    return char, TraitCard(**traits) if traits else describe(book / refs[char]["rel_path"], seed=42)


def render_or_reuse(values: dict, bound: list[str], refs: dict, book: Path,
                    dest: Path) -> tuple[Path, bool]:
    """A finished take made from this exact recipe is reused; anything else
    renders.  The flag says which happened, so a reused take cannot pass
    itself off as a measurement of the cycle."""
    recipe = recipe_for(values, bound, refs, book)
    if is_complete(dest) and is_current(dest, recipe):
        return dest, False
    if dest.exists():
        dest.unlink()
    try:
        return render_take(values, bound, refs, book, dest), True
    except RuntimeError as exc:
        raise TakeFailed(str(exc)) from exc


def frames_of(video: Path, seconds: float, work: Path) -> list[Path]:
    """Three stills spread over the take, none inside the reference leak.

    Past HEAD_TRIM, not past `frame_times`' 1.0s default: the leak is 2.6s and
    a take is now barely longer than its shot, so sampling earlier would read
    the reference sheet itself and the gate would pass on its own answer."""
    work.mkdir(parents=True, exist_ok=True)
    return [frame_at(video, when, work / f"{when:.2f}.png")
            for when in frame_times(seconds, head=HEAD_TRIM)]


def timed_out(learn: Callable) -> Callable[[str], None]:
    """The learning a read that outlived TIMEOUT leaves behind."""
    return lambda what: learn(Learning(step=STEP_ID, gate="identity", measured=what,
                                       threshold=f"{TIMEOUT}s", action="accepted_on_timeout"))


def read_card(frames: list[Path], seed: int, learn: Callable, run: Callable | None = None) -> TraitCard:
    """The take's card, or an unseen one when the model outlives TIMEOUT.

    `run` is the ROUND'S reader: freed once, then resident for every sheet.

    Scarlet run 4: one call took 10:23 and its TimeoutError ended the run with
    19 beats unrendered.  Retry, then degrade and ship: the job is interrupted
    so it cannot hold the queue, the take ships flagged, the run goes on."""
    return patiently(lambda: describe_frames(frames, seed=seed, run=run), timed_out(learn))


def measure(video: Path, reference: TraitCard | None, work: Path, seed: int,
            learn: Callable = lambda row: None, run: Callable | None = None) -> dict:
    """What the vision model reads in the take, against the reference's card."""
    seconds = clip_seconds(video)
    if reference is None:
        return {"path": video, "seconds": seconds, "card": None, "similarity": None,
                "differs": [], "known": 0}
    card = read_card(frames_of(video, seconds, work), seed, learn, run)
    alike, apart = shared(card, reference), differences(card, reference)
    return {"path": video, "seconds": seconds, "card": card, "differs": apart, "known": known(card),
            "similarity": round(len(alike) / max(1, len(alike) + len(apart)), 3)}


def best_of(tries: list[dict]) -> dict | None:
    return max(tries, key=lambda t: -1.0 if t["similarity"] is None else t["similarity"],
               default=None)


def promote(take: Path, dest: Path) -> Path:
    """The chosen take under its beat's name, RECIPE AND ALL.

    The bytes alone made the promoted clip anonymous: run 10's assembler
    could not tell this run's B04 from the B04 of the plan before it, and
    cut 24% of the picture from stale files.  The sidecar is the identity.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(take.read_bytes())
    if sidecar_for(take).exists():
        sidecar_for(dest).write_bytes(sidecar_for(take).read_bytes())
    return dest


def clip_record(beat_id: str, chosen: dict, book: Path, dest: Path, reference: str | None,
                capped: float | None, tries: list[dict]) -> dict:
    return {"beat_id": beat_id, "rel_path": dest.relative_to(book).as_posix(),
            "seconds": chosen["seconds"], "seed": chosen["seed"],
            "similarity": chosen["similarity"], "differs": chosen["differs"],
            "known": chosen["known"], "reference": reference, "capped": capped,
            "fingerprint": stored_fingerprint(dest),
            "takes": [{"seed": t["seed"], "similarity": t["similarity"]} for t in tries]}


@dataclass
class Bind:
    """One beat across the rounds: what it binds to, what it has rendered,
    and where it stands on the identity ladder."""

    index: int
    beat: dict
    bound: list[str]
    reference_id: str | None
    reference: TraitCard | None
    climb: Climb
    tries: list[dict] = field(default_factory=list)
    stopped: bool = False

    @property
    def beat_id(self) -> str:
        return self.beat["beat_id"]

    @property
    def active(self) -> bool:
        """Whether this beat still wants a take in the next round."""
        return not self.stopped and not self.climb.done


def bind_for(ctx, index: int, beat: dict, refs: dict) -> Bind:
    """One beat's place on the identity ladder, before any take exists."""
    bound = bound_slots(beat, refs)
    reference_id, reference = reference_of(ctx.book_dir, refs, bound)
    return Bind(index, beat, bound, reference_id, reference,
                Climb(LADDER, STEP_ID, substep=beat["beat_id"], gate_name="identity"))


def drop_beat(ctx, bind: Bind, staged: int) -> None:
    """No time for this beat's FIRST take: it has no clip and never will."""
    bind.stopped = True
    ctx.learn(Learning(step=STEP_ID, substep=bind.beat_id, gate="budget",
                       measured=round(ctx.budget.remaining(STEP_ID)),
                       threshold=take_cost(staged), action=DROPPED, terminal=True))


def take_failed(ctx, bind: Bind, exc: Exception) -> None:
    """The renderer produced nothing: this beat asks for no more takes."""
    bind.stopped = True
    ctx.learn(Learning(step=STEP_ID, substep=bind.beat_id, gate="render",
                       measured=str(exc)[:80], terminal=True,
                       action="short_shot" if bind.tries else DROPPED))


def render_attempt(ctx, bind: Bind, rung: Rung, i: int, plan: dict, refs: dict,
                   style: str) -> dict | None:
    """One take for one beat; None when the renderer produced no video."""
    seed = seed_for(bind.index, rung, i)
    values = take_values(bind.beat, plan, refs, style, seed,
                         tightest="close" if rung.name == "alternate_setup" else None)
    ctx.tracker.log(f"{bind.beat_id} {rung.name} seed {seed}, {values['frames']} frames, "
                    f"{round(ctx.budget.remaining(STEP_ID))}s left", step_id=STEP_ID)
    started = ctx.budget.clock()
    try:
        take, fresh = render_or_reuse(values, bind.bound, refs, ctx.book_dir,
                                      ctx.out_dir / "clips/takes" / f"{bind.beat_id}-{seed}.mp4")
    except TakeFailed as exc:
        take_failed(ctx, bind, exc)
        return None
    return {"bind": bind, "rung": rung, "take": take, "seed": seed, "fresh": fresh,
            "seconds": ctx.budget.clock() - started}


def render_round(ctx, binds: list[Bind], plan: dict, refs: dict, style: str) -> list[dict]:
    """Every live beat's next take, rendered BACK TO BACK with H3 resident.

    Nothing here frees the engine: the unload belongs to the read that follows,
    once for the whole round."""
    staged: list[dict] = []
    for bind in [b for b in binds if b.active]:
        wanted = bind.climb.ask(ctx.budget, ctx.learn)
        if wanted is None:
            continue
        if bind.climb.attempts == 0 and not ctx.budget.can_afford(STEP_ID, take_cost(len(staged))):
            drop_beat(ctx, bind, len(staged))
            continue
        pending = render_attempt(ctx, bind, *wanted, plan, refs, style)
        if pending:
            staged.append(pending)
    return staged


def read_round(ctx, staged: list[dict]) -> None:
    """Every take of the round read in ONE session: the image models are
    unloaded once, here, and the reader answers the rest while resident."""
    started = ctx.budget.clock()
    session = reader(free=True)
    for pending in staged:
        bind = pending["bind"]
        pending["result"] = dict(
            measure(pending["take"], bind.reference,
                    ctx.out_dir / "work/identity" / pending["take"].stem,
                    pending["seed"], learn=ctx.learn, run=session), seed=pending["seed"])
        bind.tries.append(pending["result"])
    learn_read(ctx, sum(1 for p in staged if p["bind"].reference), ctx.budget.clock() - started)


def gate_take(ctx, bind: Bind, result: dict) -> tuple[bool, float | int | None, int]:
    """Is the person in this take the person on the sheet."""
    if bind.reference is None:
        return True, None, DISTINCT_AT
    if not verifiable(result["card"]):
        ctx.learn(Learning(step=STEP_ID, substep=bind.beat_id, gate="identity",
                           measured=result["known"], threshold="verifiable",
                           action="accepted_unverifiable"))
        return True, None, DISTINCT_AT
    return (same_look(result["card"], bind.reference),
            distance(result["card"], bind.reference), DISTINCT_AT)


def settle_round(ctx, staged: list[dict]) -> None:
    """The round's verdicts: a take that binds ends its climb, one that does
    not takes a rung and asks for the next round."""
    for pending in staged:
        bind = pending["bind"]
        ok, measured, threshold = gate_take(ctx, bind, pending["result"])
        bind.climb.settle(pending["rung"], pending["result"], ok, measured, threshold,
                          pending["seconds"], ctx.learn)


def learn_read(ctx, sheets: int, seconds: float) -> None:
    """What the round's ONE reader session cost, against what it was priced at."""
    if sheets:
        ctx.learn(Learning(step=STEP_ID, gate=READ, measured=round(seconds, 1),
                           threshold=read_seconds(sheets), action="session",
                           seconds=round(seconds, 1), note=f"{sheets} sheet(s)"))


def learn_cycle(ctx, staged: list[dict], seconds: float, number: int) -> None:
    """What a take cost this round, render and its share of the read: the
    number the NEXT plan is sized on, measured instead of assumed."""
    fresh = sum(1 for pending in staged if pending["fresh"])
    if fresh:
        ctx.learn(Learning(step=STEP_ID, gate=CYCLE, measured=round(seconds / fresh, 1),
                           threshold=RENDER_SECONDS, action=f"round_{number}", attempt=number,
                           seconds=round(seconds, 1), note=f"{fresh} take(s)"))


def chosen_of(bind: Bind) -> tuple[dict | None, float | None]:
    """The take this beat ships and the cap it ships under.  A climb that
    never bound ships its best take short; a beat with no take ships nothing."""
    outcome = bind.climb.outcome
    if outcome is not None and not outcome.terminal:
        return outcome.result, None
    return best_of(bind.tries), (SHORT_SHOT if bind.tries else None)


def promoted(ctx, bind: Bind) -> dict | None:
    """The beat's chosen take under the beat's own name, or None when it has none."""
    chosen, capped = chosen_of(bind)
    if chosen is None:
        return None
    dest = promote(chosen["path"], ctx.out_dir / "clips" / f"{bind.beat_id}.mp4")
    return clip_record(bind.beat_id, chosen, ctx.book_dir, dest, bind.reference_id,
                       capped, bind.tries)


def write_clips(ctx, binds: list[Bind]) -> None:
    """clips.json: the take every beat ships, and the beats that ship none."""
    clips, dropped = [], []
    for bind in binds:
        record = promoted(ctx, bind)
        (clips if record else dropped).append(record or bind.beat_id)
    (ctx.out_dir / "clips.json").write_text(json.dumps(
        {"clips": clips, "dropped": dropped}, indent=2), encoding="utf-8")
    print(f"[{STEP_ID}] {len(clips)} takes, {len(dropped)} dropped {dropped}, "
          f"{sum(1 for c in clips if c['capped'])} capped short")


def run(codex_id: str, ctx) -> None:
    plan = json.loads((ctx.out_dir / "plan.json").read_text(encoding="utf-8"))
    refs_doc = json.loads((ctx.book_dir / "refs/refs.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    binds = [bind_for(ctx, index, beat, refs) for index, beat in enumerate(plan["beats"])]
    number = 0
    while any(bind.active for bind in binds):
        number += 1
        started = ctx.budget.clock()
        ctx.tracker.log(f"round {number}: {sum(b.active for b in binds)} beat(s) climbing, "
                        f"{round(ctx.budget.remaining(STEP_ID))}s left", step_id=STEP_ID)
        staged = render_round(ctx, binds, plan, refs, refs_doc["palette"])
        if not staged:
            break
        read_round(ctx, staged)
        settle_round(ctx, staged)
        learn_cycle(ctx, staged, ctx.budget.clock() - started, number)
    write_clips(ctx, binds)
