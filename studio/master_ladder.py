"""The master's ladder: recut x2 (free) -> retake_shot x1 (through the take
ladder) -> flag.

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

from typing import Callable

from studio import judged_gate
from studio.judges import master_eye
from studio.judges.verdict import Verdict
from studio.ladder import Ladder, Rung

RECUT_SECONDS = 0.0
"""A recut is ffmpeg over takes already on disk: no GPU."""
RETAKE_SECONDS = 9 * 60.0
"""One shot through the take ladder, 4-9 GPU minutes; the ceiling's worst case."""
TERMINAL = "flag"
LADDER = Ladder([Rung("recut", RECUT_SECONDS, tries=2), Rung("retake_shot", RETAKE_SECONDS, tries=1)], TERMINAL)
EMPTY = Ladder([], TERMINAL)

Recut = Callable[[], None]
Retake = Callable[[int, Verdict], None]


def recuttable(v: Verdict) -> bool:
    """Whether any fault is on a field a recut or a retake can move."""
    return any(f.kind in master_eye.MEASURED for f in v.faults)


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


def rungs(v: Verdict, recut: Recut, retake: Retake) -> judged_gate.Rungs:
    """The priced rungs for this verdict, and how each is taken.  A retake is
    followed by a recut: the new take is nothing until it is in the master."""
    def take(rung: Rung, _i: int, current: Verdict) -> None:
        if rung.name == "retake_shot":
            shot = worst_shot(current)
            if shot is not None:
                retake(shot, current)
        recut()
    return judged_gate.Rungs(LADDER if recuttable(v) else EMPTY, take)


def once(first: Verdict, again: Callable[[], Verdict]) -> Callable[[], Verdict]:
    """The verdict already read, then fresh reads: the ladder is built from the
    first read and the gate must not pay for it twice."""
    served = []

    def judge() -> Verdict:
        if not served:
            served.append(first)
            return first
        return again()
    return judge


def flag(v: Verdict) -> Verdict:
    """The terminal rung: the master stays as it is; the rubric is signed flagged."""
    return v


def retake_through_take_ladder(ctx, shot: int, v: Verdict) -> None:
    """One round of the take ladder over the named shot, under the render flag
    the RENDER row earns; the take gates run on it, then the master is recut
    and read again.  Loaded when asked: the step imports nothing of step 09."""
    from scripts.episode import step_09_shoot
    from studio import gate_policy, take_ladder
    faults = [f for f in v.faults if f.kind in master_eye.MEASURED]
    take_ladder.retake(ctx, [shot], take_ladder.why_of("retake_shot", faults),
                       step_09_shoot.approved(gate_policy.of(ctx.stage, "RENDER")))
