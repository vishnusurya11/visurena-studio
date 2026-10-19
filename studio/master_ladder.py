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

import hashlib
import time
from pathlib import Path
from typing import Callable

from studio import judged_gate, step_attempts
from studio.judges import master_eye
from studio.judges.verdict import Verdict
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


def fingerprint(home, shot: int) -> tuple[str, str]:
    """(the named take sha8, shots.json sha8): what a retake can change."""
    room = Path(home) / "takes" / "r2v"
    return tuple(sha8_of(room / name) for name in (f"T{shot:02d}.mp4", "shots.json"))


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

    def take(rung: Rung, _i: int, current: Verdict) -> None:
        shot = worst_shot(current)
        moved.changed = shot is not None and changed_by(retake(shot, current))
        if moved.changed:
            recut()
        else:
            print(f"CAP master: retake of T{shot or 0:02d} changed no take, no recut", flush=True)
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
    """The terminal rung: the master stays as it is; the rubric is signed flagged."""
    return v


def retake_through_take_ladder(ctx, shot: int, v: Verdict) -> bool:
    """One round of the take ladder over the named shot, under the render flag
    the RENDER row earns; True when it changed the take or shots.json (then the master
    is recut and read again), False when it was refused or left the bytes (K11 mirrored).
    Loaded when asked: the step imports nothing of step 09."""
    from scripts.episode import step_09_shoot
    from studio import gate_policy, take_ladder
    faults = [f for f in v.faults if f.kind in master_eye.MEASURED]
    if take_ladder.refuse_spent(ctx, len(faults)):       # the episode's 2 retake rounds: keep the master
        return False
    began, before = time.time(), fingerprint(ctx.home, shot)
    take_ladder.retake(ctx, [shot], take_ladder.why_of("retake_shot", faults),
                       step_09_shoot.approved(gate_policy.of(ctx.stage, "RENDER")))
    if fingerprint(ctx.home, shot) == before:
        return False
    step_attempts.spend(ctx.home, take_ladder.RETAKES, time.time() - began)
    return True
