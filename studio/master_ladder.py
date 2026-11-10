"""The master's ladder: retake_shot x1 (through the take ladder, then a
recut) -> flag.  No free recut rung: step 11 runs on a master newer than every
cut input, so a recut re-made the same bytes (ep12 iter5 == iter7; speed plan #7).

A fault on a MEASURED rubric field (shadow, faces, board, repeats) climbs;
a story fault, the short read's and the identity pass's faults ride along on
whatever the climb produces and are flagged at the end.  A verdict with no
measured fault has no rung to take: the ladder is empty and `judged_gate.clear`
goes straight to the terminal, which keeps the master as it is and signs the
rubric flagged.  Nothing here asks a person anything.

`retake=` is injectable: the take ladder (`studio/take_ladder.py`) is the
rung's body when it exists, and a test hands in a fake.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable

from studio import episode_home, judged_gate, plan_gates, step_attempts, stillness
from studio.judges import master_eye
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung

RETAKE_SECONDS = 9 * 60.0
"""One shot through the take ladder, 4-9 GPU minutes; the floor of its price."""
TERMINAL = "flag"
LADDER = Ladder([Rung("retake_shot", RETAKE_SECONDS, tries=1)], TERMINAL)
EMPTY = Ladder([], TERMINAL)

Recut = Callable[[], None]
Retake = Callable[[int, Verdict], object]
"""A retake answers whether it changed anything: a bool, a RungResult (`.changed`), or None
for a legacy retake, which is taken to have changed."""


class Round:
    """Whether the rung just taken moved a take: the recut and the second master eye need it."""

    def __init__(self) -> None:
        self.changed = True


def changed_by(result: object) -> bool:
    """A retake answer as a bool: None is a legacy retake that always recut."""
    return True if result is None else bool(getattr(result, "changed", result))


def retake_seconds(home) -> float:
    """What one master retake costs: the measured seconds per booked round, never under the floor."""
    rounds, spent = step_attempts.count(home, "retakes"), step_attempts.seconds(home, "retakes")
    return max(RETAKE_SECONDS, spent / rounds) if rounds else RETAKE_SECONDS


def recuttable(v: Verdict) -> bool:
    """Whether a measured fault names a shot a retake can move (a shadow fault names none)."""
    return worst_shot(v) is not None


def fingerprint(home, shot: int) -> tuple[str, str, str]:
    """(the take, heads.json, stills.json) sha8s: what the cut READS that a retake can move.  Not
    shots.json: every render rewrites its record (seed, tries, render_s), and ep03 T04's record changed
    while keep_best put the old draw back -- the master was recut, upscaled and judged for the same bytes."""
    room = Path(home) / "takes" / "r2v"
    return sha8_of(room / f"T{shot:02d}.mp4"), sha8_of(Path(home) / "heads.json"), sha8_of(room / "stills.json")


def sha8_of(path: Path) -> str:
    digest = hashlib.sha256()
    if path.exists():
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
    return digest.hexdigest()[:8]


def named_shots(v: Verdict) -> list[int]:
    """Every shot a measured field's evidence names, most named first."""
    counts: dict[int, int] = {}
    for f in v.faults:
        if f.kind not in master_eye.MEASURED:
            continue
        for shot in shots_in(f.evidence):
            counts[shot] = counts.get(shot, 0) + 1
    return sorted(counts, key=lambda s: (-counts[s], s))


def shots_in(evidence: dict) -> list[int]:
    """The shot numbers a field's evidence points at: `under`, `off`, `pairs`."""
    out = [int(s) for s in evidence.get("under", [])]
    out += [int(s) for s in (evidence.get("off") or {})]
    out += [int(p[k]) for p in evidence.get("pairs", []) for k in ("a", "b")]
    return out


def worst_shot(v: Verdict) -> int | None:
    named = named_shots(v)
    return named[0] if named else None


def ladder_for(v: Verdict, seconds: float = RETAKE_SECONDS) -> Ladder:
    """The master ladder priced at `seconds` a retake; empty when no shot is named."""
    return Ladder([Rung("retake_shot", seconds, tries=1)], TERMINAL) if recuttable(v) else EMPTY


def rungs(v: Verdict, recut: Recut, retake: Retake, moved: Round | None = None,
          seconds: float = RETAKE_SECONDS) -> judged_gate.Rungs:
    """The priced rungs for this verdict, and how each is taken.  A retake that moved a
    take is followed by a recut; one that changed nothing is said and takes none."""
    moved = moved if moved is not None else Round()

    def take(rung: Rung, _i: int, current: Verdict) -> judged_gate.RungResult:
        shot = worst_shot(current)
        moved.changed = shot is not None and changed_by(retake(shot, current))
        if moved.changed:
            recut()
            return judged_gate.RungResult(True)
        print(f"CAP master: retake of T{shot or 0:02d} changed no take, no recut", flush=True)
        return judged_gate.RungResult(False, f"retake of T{shot or 0:02d} changed no take")
    return judged_gate.Rungs(ladder_for(v, seconds), take)


def once(first: Verdict, again: Callable[[], Verdict], moved: Round | None = None) -> Callable[[], Verdict]:
    """The verdict already read, then fresh reads: the ladder is built from the
    first read and the gate must not pay for it twice.  When the rung moved nothing the
    master is the same bytes, so the last verdict stands and no eye is paid for."""
    served = []

    def judge() -> Verdict:
        if not served:
            served.append(first)
            return first
        if moved is not None and not moved.changed:
            return served[-1]
        served.append(again())
        return served[-1]
    return judge


def flag(v: Verdict) -> Verdict:
    """The terminal rung: the master stays as it is; the rubric is signed flagged -- unless a fault on the
    block list stands (G-PEOPLE, owner 2026-10-28; scaffold words, hair no row allows, a long leak, owner
    2026-10-30: studio/ship_block), which refuses."""
    from studio import ship_block
    if wrong := ship_block.master_blocks(v.faults):
        said = "; ".join(ship_block.block_text(where, rows) for where, rows in wrong.items())
        raise SystemExit(f"REFUSED: G-PEOPLE: a fault on the ship-block list (a wrong person, scaffold words, hair "
                         f"no row allows, a long leak) stands at {said} after the master ladder's "
                         "rounds; it never ships flagged -- retake those shots")
    return v


def refuse_frozen(ctx, shot: int) -> bool:
    """The take the governing repair froze is never retaken from the master (incident 2, 2026-10-19):
    its KEPT line is said and the master stays flagged."""
    from studio import take_ladder
    line = take_ladder.kept_frozen(ctx.home, shot, "no master retake")
    if line:
        print(line, flush=True)
        if hasattr(ctx, "log"):
            ctx.log(line, level="WARNING")
    return bool(line)


def retake_through_take_ladder(ctx, shot: int, v: Verdict) -> bool:
    """One round of the take ladder over the named shot, its INPUT changed first (the cure its
    master faults route to), under the render flag the RENDER row earns; True when the cut's inputs
    moved (then the master is recut and read again), False when refused or left the bytes (K11).
    Loaded when asked: the step imports nothing of step 09."""
    from scripts.episode import step_09_shoot
    from studio import gate_policy, take_ladder
    if refuse_frozen(ctx, shot):                         # an owner's repair froze the delivered take
        return False
    if take_ladder.refuse_spent(ctx, len(faults_on(v, shot))):   # the episode's 2 retake rounds
        return False
    doc, why = cured_plan(ctx.home, shot, faults_on(v, shot))
    if doc is None:                                      # nothing a render can change holds the fault
        owe_panel(ctx.home, shot, faults_on(v, shot))
        return refuse_noop(ctx, shot, why)
    began, before, kept = time.time(), fingerprint(ctx.home, shot), as_it_was(ctx.home, shot)
    episode_home.write_plan(Path(ctx.home) / "plan.json", doc)
    take_ladder.retake(ctx, [shot], why, step_09_shoot.approved(gate_policy.of(ctx.stage, "RENDER")))
    if fingerprint(ctx.home, shot) == before:
        put_back(ctx.home, shot, kept)
        return refuse_noop(ctx, shot, "kept its earlier draw (keep_best ranked it over the cure's roll)")
    step_attempts.spend(ctx.home, take_ladder.RETAKES, time.time() - began)
    return True


# ---- which input a master fault can change -------------------------------------------------------

FIELD_CURE = {"board": "move_type", "faces": "push_slow"}
"""What a measured master field can change on a take.  `board` (the last frame off its panel): the
take ladder's move-type table for last-vs-cell.  `faces` (a small face at a close): a push toward it --
H3 obeys the cell and the camera verb, never an amount, and a seed reroll never grew a face (ep03 T04:
0.093 of the height on two draws).  `repeats` and `shadow` live in the panels and the grade: no render
moves them, so no retake is ordered for them."""


def faults_on(v: Verdict, shot: int) -> list[Fault]:
    """The measured master faults whose evidence names this shot."""
    return [f for f in v.faults if f.kind in master_eye.MEASURED and shot in shots_in(f.evidence)]


def spoken(doc: dict, shot: int) -> bool:
    return any(line.get("kind") == "dialogue" and line.get("shot") == shot for line in doc.get("lines") or [])


def pushed(doc: dict, shot: int) -> tuple[str, str]:
    """(the shot's motion as a push toward its face, '') or ('', why it may not): a spoken line's camera
    never travels; a locked grammar shot is never pushed (G-PUSH); a push already pushes."""
    from studio import take_ladder
    s = take_ladder.shot_doc(doc, shot)
    if spoken(doc, shot):
        return "", "a spoken take's camera never travels and a seed cannot grow a face; the panel owns its framing"
    if doc.get("grammar") and stillness.locked(s["motion"]):
        return "", "a locked grammar shot is never pushed (G-PUSH); the panel owns its framing"
    if plan_gates.move_id(s["motion"], "") == "push_slow":
        return "", "it already pushes in; the panel owns its framing"
    return take_ladder.headed("push_slow", s["motion"], s.get("at_rest", "")), ""


def off_board(doc: dict, shot: int) -> tuple[str, str]:
    """(the shot's motion under the take ladder's move-type cure for last-vs-cell, why when it is the same)."""
    from studio import take_ladder
    edited = take_ladder.move_type(copy.deepcopy(doc), shot, [Fault(kind="last-vs-cell", where=f"T{shot:02d}")])
    return take_ladder.shot_doc(edited, shot)["motion"], "the move-type table has no other move for it"


def cured_motion(doc: dict, shot: int, kinds: set[str]) -> tuple[str, str, str]:
    """(the cured motion, the cure, why none): board first, then faces."""
    kind = next((k for k in FIELD_CURE if k in kinds), None)
    if kind is None:
        return "", "", "lives in the panels or the grade; no render moves it"
    motion, why = off_board(doc, shot) if kind == "board" else pushed(doc, shot)
    return motion, f"{kind} -> {FIELD_CURE[kind]}", why


def cured_plan(home, shot: int, faults: list[Fault]) -> tuple[dict | None, str]:
    """(the plan with this shot's input changed, the retake's `why`) or (None, why nothing can)."""
    from studio import take_ladder
    path, kinds = Path(home) / "plan.json", {f.kind for f in faults}
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    named = ", ".join(sorted(kinds)) or "no measured fault"
    if not any(s.get("index") == shot for s in doc.get("shots") or []):
        return None, f"{named}: shot {shot} is not in the plan"
    motion, cure, why = cured_motion(doc, shot, kinds)
    if not motion or motion == take_ladder.shot_doc(doc, shot)["motion"]:
        return None, f"{named}: {why}"
    take_ladder.shot_doc(doc, shot)["motion"] = motion
    return doc, f"retake_shot: {cure}"


def refuse_noop(ctx, shot: int, what: str) -> bool:
    """A retake that would buy (or bought) no new bytes, said where the run's log reads it."""
    line = f"NO-OP master: T{shot:02d} {what}; no recut, the master flags"
    print(line, flush=True)
    if hasattr(ctx, "log"):
        ctx.log(line, level="WARNING")
    return False


def owe_panel(home, shot: int, faults: list[Fault]) -> list[dict]:
    """One "panel cure owed" row per field no render can move, in the take ladder's cures_owed.jsonl,
    never twice: the frame is the panel's to change (the board, not the camera)."""
    from studio import take_ladder
    path = Path(home) / take_ladder.OWED
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen = {(r["take"], r["fault"]) for r in map(json.loads, lines)}
    rows = [{"take": shot, "shot": shot, "field": "frame", "fault": kind,
             "row": f"panel cure owed: shot {shot} frame (master {kind})"}
            for kind in sorted({f.kind for f in faults}) if (shot, kind) not in seen]
    if rows:
        with open(path, "a", encoding="utf-8") as out:
            out.writelines(json.dumps(r) + "\n" for r in rows)
    return rows


def as_it_was(home, shot: int) -> tuple[str | None, float | None]:
    """(plan.json's text, the take's mtime) before a retake: what a retake that changed nothing puts back."""
    plan, take = Path(home) / "plan.json", Path(home) / "takes" / "r2v" / f"T{shot:02d}.mp4"
    return (plan.read_text(encoding="utf-8") if plan.exists() else None,
            take.stat().st_mtime if take.exists() else None)


def put_back(home, shot: int, kept: tuple[str | None, float | None]) -> None:
    """The kept take was drawn from the old words, so the old words go back (else every currency
    check reads it stale); and its bytes under their old time -- keep_best's swap re-dated them, and
    step 10's `done` would read the unchanged take as newer than the master and recut it."""
    text, stamp = kept
    if text is not None:
        (Path(home) / "plan.json").write_text(text, encoding="utf-8")
    take = Path(home) / "takes" / "r2v" / f"T{shot:02d}.mp4"
    if stamp is not None and take.exists():
        os.utime(take, (stamp, stamp))
