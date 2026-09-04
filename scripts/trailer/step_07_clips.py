"""Step 07 -- clips: one take per beat, its person read against its reference.

The slow step: ~11 min per take on the local GPU, so the budget is read
before every render.  Three frames of every take are read by the vision
model into a trait card (`studio.describe`) and compared with the reference
sheet's card: DISTINCT_AT or more traits apart is not the same person.
Such a take climbs seed x2 and then a whole-take close-up (the FORM changes,
the beat does not).  The terminal rung never asks: it ships the BEST take of
the beat capped at a short shot.  A beat is dropped only when no take
exists at all -- no time for a first render, or the render itself failed.
Every take is kept under clips/takes/; the chosen one is clips/<beat>.mp4,
which is what the cut reads.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from scripts.trailer.build_clips import (SEED_BASE, bound_slots, is_complete, recipe_for,
                                         render_take, take_values)
from studio.clip_cache import is_current
from studio.describe import (DISTINCT_AT, TIMEOUT, TraitCard, describe, describe_frames,
                             differences, distance, known, patiently, same_look, shared, verifiable)
from studio.identity_gate import HEAD_LEAK_SECONDS, frame_at, frame_times
from studio.ladder import Ladder, Rung, climb
from studio.learnings import Learning
from studio.trailer_assemble import clip_seconds

STEP_ID = "07"
NAME = "clips"
RENDER_SECONDS = 11 * 60
SHORT_SHOT = 0.6
"""A take whose face never bound may still carry a cut this short: too brief
to read a wrong face, long enough to keep the beat's place in the metre."""
LADDER = Ladder([Rung("reroll_seed", RENDER_SECONDS, tries=2),
                 Rung("alternate_setup", RENDER_SECONDS, tries=1)], terminal="short_shot")
DROPPED = "drop_beat"


class TakeFailed(RuntimeError):
    """The renderer produced no video; not a gate, a fact about the machine."""


def seed_for(index: int, rung: Rung, i: int) -> int:
    base = SEED_BASE + index * 7
    return base + 5000 * (i + 1) if rung.name == "alternate_setup" else base + 1000 * i


def need_seconds(beat_id: str, plan: dict) -> float:
    """The longest shot the cut wants from this beat, past the reference leak."""
    longest = max((s["seconds"] for s in plan["shots"] if s["beat_id"] == beat_id), default=0.0)
    return longest + HEAD_LEAK_SECONDS


def reference_of(book: Path, refs: dict, bound: list[str]) -> tuple[str | None, TraitCard | None]:
    """The sheet a take's person is read against: its first bound character.
    Step 02 wrote the sheet's card; a refs.json without one is read now."""
    char = next((r for r in bound if r.startswith("char-")), None)
    if char is None:
        return None, None
    traits = (refs[char].get("identity") or {}).get("traits")
    return char, TraitCard(**traits) if traits else describe(book / refs[char]["rel_path"], seed=42)


def render_or_reuse(values: dict, bound: list[str], refs: dict, book: Path, dest: Path) -> Path:
    """A finished take made from this exact recipe is reused; anything else renders."""
    recipe = recipe_for(values, bound, refs, book)
    if is_complete(dest) and is_current(dest, recipe):
        return dest
    if dest.exists():
        dest.unlink()
    try:
        return render_take(values, bound, refs, book, dest)
    except RuntimeError as exc:
        raise TakeFailed(str(exc)) from exc


def frames_of(video: Path, seconds: float, work: Path) -> list[Path]:
    """Three stills spread over the take, none inside the head leak."""
    work.mkdir(parents=True, exist_ok=True)
    return [frame_at(video, when, work / f"{when:.2f}.png") for when in frame_times(seconds)]


def timed_out(learn: Callable) -> Callable[[str], None]:
    """The learning a read that outlived TIMEOUT leaves behind."""
    return lambda what: learn(Learning(step=STEP_ID, gate="identity", measured=what,
                                       threshold=f"{TIMEOUT}s", action="accepted_on_timeout"))


def read_card(frames: list[Path], seed: int, learn: Callable) -> TraitCard:
    """The take's card, or an unseen one when the model outlives TIMEOUT.

    Scarlet run 4: one call took 10:23 and its TimeoutError ended the run with
    19 beats unrendered.  Retry, then degrade and ship: the job is interrupted
    so it cannot hold the queue, the take ships flagged, the run goes on."""
    return patiently(lambda: describe_frames(frames, seed=seed), timed_out(learn))


def measure(video: Path, reference: TraitCard | None, work: Path, seed: int,
            learn: Callable = lambda row: None) -> dict:
    """What the vision model reads in the take, against the reference's card."""
    seconds = clip_seconds(video)
    if reference is None:
        return {"path": video, "seconds": seconds, "card": None, "similarity": None,
                "differs": [], "known": 0}
    card = read_card(frames_of(video, seconds, work), seed, learn)
    alike, apart = shared(card, reference), differences(card, reference)
    return {"path": video, "seconds": seconds, "card": card, "differs": apart, "known": known(card),
            "similarity": round(len(alike) / max(1, len(alike) + len(apart)), 3)}


def best_of(tries: list[dict]) -> dict | None:
    return max(tries, key=lambda t: -1.0 if t["similarity"] is None else t["similarity"],
               default=None)


def promote(take: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(take.read_bytes())
    return dest


def clip_record(beat_id: str, chosen: dict, book: Path, dest: Path, reference: str | None,
                capped: float | None, tries: list[dict]) -> dict:
    return {"beat_id": beat_id, "rel_path": dest.relative_to(book).as_posix(),
            "seconds": chosen["seconds"], "seed": chosen["seed"],
            "similarity": chosen["similarity"], "differs": chosen["differs"],
            "known": chosen["known"], "reference": reference, "capped": capped,
            "takes": [{"seed": t["seed"], "similarity": t["similarity"]} for t in tries]}


def bind_beat(ctx, index: int, beat: dict, plan: dict, refs: dict, style: str) -> dict | None:
    """Climb the identity ladder for one beat; None means the beat is dropped."""
    book, beat_id = ctx.book_dir, beat["beat_id"]
    if not ctx.budget.can_afford(STEP_ID, RENDER_SECONDS):
        ctx.learn(Learning(step=STEP_ID, gate="budget", measured=round(ctx.budget.remaining(STEP_ID)),
                           threshold=RENDER_SECONDS, action=DROPPED, terminal=True))
        return None
    bound = bound_slots(beat, refs)
    reference_id, reference = reference_of(book, refs, bound)
    tries: list[dict] = []

    def attempt(rung: Rung, i: int) -> dict:
        seed = seed_for(index, rung, i)
        values = take_values(beat, plan, refs, style, seed,
                             tightest="close" if rung.name == "alternate_setup" else None)
        take = render_or_reuse(values, bound, refs, book,
                               ctx.out_dir / "clips/takes" / f"{beat_id}-{seed}.mp4")
        result = dict(measure(take, reference, ctx.out_dir / "work/identity" / take.stem, seed,
                              learn=ctx.learn), seed=seed)
        tries.append(result)
        return result

    def gate(result: dict):
        if reference is None:
            return True, None, DISTINCT_AT
        if not verifiable(result["card"]):
            ctx.learn(Learning(step=STEP_ID, gate="identity", measured=result["known"],
                               threshold="verifiable", action="accepted_unverifiable"))
            return True, None, DISTINCT_AT
        return same_look(result["card"], reference), distance(result["card"], reference), DISTINCT_AT

    try:
        outcome = climb(LADDER, STEP_ID, attempt, gate, ctx.budget, ctx.learn, gate_name="identity",
                        substep=beat_id)
        chosen, capped = (best_of(tries), SHORT_SHOT) if outcome.terminal else (outcome.result, None)
    except TakeFailed as exc:
        chosen, capped = best_of(tries), SHORT_SHOT
        ctx.learn(Learning(step=STEP_ID, gate="render", measured=str(exc)[:80],
                           action=DROPPED if chosen is None else "short_shot", terminal=True))
    if chosen is None:
        return None
    dest = promote(chosen["path"], ctx.out_dir / "clips" / f"{beat_id}.mp4")
    return clip_record(beat_id, chosen, book, dest, reference_id, capped, tries)


def run(codex_id: str, ctx) -> None:
    plan = json.loads((ctx.out_dir / "plan.json").read_text(encoding="utf-8"))
    refs_doc = json.loads((ctx.book_dir / "refs/refs.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    clips, dropped = [], []
    for index, beat in enumerate(plan["beats"]):
        ctx.tracker.log(f"{beat['beat_id']} [{index + 1}/{len(plan['beats'])}] "
                        f"{round(ctx.budget.remaining(STEP_ID))}s left", step_id=STEP_ID)
        record = bind_beat(ctx, index, beat, plan, refs, refs_doc["palette"])
        (clips if record else dropped).append(record or beat["beat_id"])
    (ctx.out_dir / "clips.json").write_text(json.dumps(
        {"clips": clips, "dropped": dropped}, indent=2), encoding="utf-8")
    print(f"[{STEP_ID}] {len(clips)} takes, {len(dropped)} dropped {dropped}, "
          f"{sum(1 for c in clips if c['capped'])} capped short")
