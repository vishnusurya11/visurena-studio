"""G-DEAD: no dead footage in a master that ships, and the free cure for it.

Jekyll ep01 (2026-10-13, docs/audit/2026-10-13_jekyll_ep01_review/MOTION.md cause 3):
29 % of the picture was near dead -- two still panels held 6+ s, three takes that
FAILED the take gate shipped anyway, and a still sat beside a frozen take.  A
terminal is not a pass (memory: a terminal is not a pass).

    still       the cut holds the shot's panel (stills.json)
    failed      the take's DQ record did not pass
    near_dead   it passed, but its whole frame is static past NEAR_DEAD
    alive       everything else

A still past STILL_LIMIT_S and a failed take are DEAD; a still or a failed take
beside another is a dead run (a short still too).  The cure is $0 and needs no clock: the dead shot leaves the
cut and its live, non-dialogue neighbours cover its seconds, slowed at most
MAX_STRETCH.  What that cannot cure refuses the master -- the ladder retakes it.
"""
from __future__ import annotations

STILL_LIMIT_S = 2.5
"""A held panel longer than this reads as a frozen picture: Jekyll's two were 6.4 s."""
NEAR_DEAD = 0.45
"""Whole-frame static share (the take gate's `frozen-whole` value) at or over which a
passed take is REPORTED near dead (Jekyll ep01 T19 0.63, T23 0.48, "near frozen" by eye).
It does NOT count toward a dead run: MEASURED 2026-10-13 on the owner-liked WotW
ep01-03 (69 takes), 15 read >= 0.45 and ep01 opens on two in a row at 1.00 (T00, T01:
Mars in space) -- static share cannot tell a calm shot from a dead one."""
MAX_STRETCH = 1.5
"""How much slower a neighbour may play to cover a cut shot's seconds."""
DEAD_RUN = ("still", "failed")
"""What counts toward two-in-a-row: the measurably dead, never `near_dead` (see NEAR_DEAD)."""


def static_share(record: dict | None) -> float:
    gate = next((g for g in (record or {}).get("gates", []) if g.get("name") == "frozen-whole"), {})
    return float(gate.get("value") or 0.0)


VOICE_ROWS = frozenset({"lip-sync", "tail", "lag"})
"""A take failing only these is a live picture with a voice fault: G-TAIL's own terminal
(keep_best flagged) answers it, never G-DEAD (Jekyll ep01 v2 T14, 2026-10-14)."""


def voice_only(record: dict) -> bool:
    failing = {g.get("name") for g in record.get("gates", []) if g.get("hard") and not g.get("ok")}
    return bool(failing) and failing <= VOICE_ROWS


TRULY_DEAD = frozenset({"frozen-at-start", "frozen-share", "frozen-whole"})
"""The rows that make a take dead footage whatever the ladder kept (owner option A, 2026-10-18)."""


def failing_rows(record: dict) -> list[str]:
    return [g.get("name") for g in (record or {}).get("gates", []) if g.get("hard") and not g.get("ok")]


def state_of(index: int, stills: dict, record: dict | None, kept: bool = False) -> str:
    """still | failed | flagged | near_dead | alive, for one take of the cut.  `kept`: the take
    ladder's terminal kept its best at the cap -- a failed take with no frozen row is admitted
    FLAGGED (owner option A, Jekyll Kawajiri ep01 2026-10-18)."""
    if index in stills:
        return "still"
    if record is not None and not record.get("passed", True) and not voice_only(record):
        return "flagged" if kept and not TRULY_DEAD & set(failing_rows(record)) else "failed"
    return "near_dead" if static_share(record) >= NEAR_DEAD else "alive"


def flag_line(index: int, record: dict) -> str:
    """What the log says of an admitted, flagged take: its failing rows."""
    rows = [g for g in (record or {}).get("gates", []) if g.get("hard") and not g.get("ok")]
    return f"FLAGGED T{index:02d}: kept best at the cap -- " + "; ".join(
        f"{g.get('name')}: {str(g.get('note') or '')[:90]}" for g in rows)


def is_dead(state: str, seconds: float) -> bool:
    return state == "failed" or (state == "still" and seconds > STILL_LIMIT_S)


def faults(order: list[tuple[int, float]], states: dict[int, str]) -> list[str]:
    """G-DEAD's refusals over the cut as it would ship."""
    out = [f"G-DEAD T{i:02d}: {'a failed take' if states.get(i) == 'failed' else f'a still held {s:.1f} s'}"
           for i, s in order if is_dead(states.get(i, "alive"), s)]
    for (a, _), (b, _) in zip(order, order[1:]):
        if states.get(a) in DEAD_RUN and states.get(b) in DEAD_RUN:
            out.append(f"G-DEAD T{a:02d}+T{b:02d}: two near-dead shots in a row ({states[a]}, {states[b]})")
    return out


def stretch(seconds: float, room: float) -> float:
    """How much slower a take plays to fill `seconds` from `room` seconds of footage."""
    return round(seconds / room, 4) if room and seconds > room else 1.0


def coverers(order: list[tuple[int, float]], k: int, states: dict, dialogue: set, cut: list) -> list[int]:
    """The live, non-dialogue shots either side of position k that are still in the cut."""
    left = [i for i, _ in order[:k] if i not in cut][-1:]
    right = [i for i, _ in order[k + 1:] if i not in cut][:1]
    return [i for i in left + right if states.get(i) == "alive" and i not in dialogue]


def cut_one(index: int, give: float, near: list[int], seconds: dict, room: dict) -> dict | None:
    """The new seconds of the neighbours covering `give`, or None when none can."""
    for group in ([near] if len(near) > 1 else []) + [[n] for n in near]:
        new = {n: round(seconds[n] + give / len(group), 4) for n in group}
        if all(new[n] / max(room.get(n, 0.0), 1e-6) <= MAX_STRETCH for n in group):
            return new
    return None


def cut_plan(order: list[tuple[int, float]], states: dict, room: dict, dialogue: set) -> dict:
    """{"cut": [take], "seconds": {neighbour: new seconds}}: every dead shot the
    free cure can take out; a dialogue shot is never cut and never slowed."""
    seconds, cut = dict(order), []
    for k, (index, own) in enumerate(order):
        if not is_dead(states.get(index, "alive"), own) or index in dialogue:
            continue
        new = cut_one(index, seconds[index], coverers(order, k, states, dialogue, cut), seconds, room)
        if new:
            cut.append(index)
            seconds.update(new)
    changed = {i: s for i, s in seconds.items() if i not in cut and s != dict(order)[i]}
    return {"cut": cut, "seconds": changed}


def apply(order: list[tuple[int, float]], plan: dict) -> list[tuple[int, float]]:
    """The cut's order with the plan's shots removed and its neighbours' seconds."""
    return [(i, plan["seconds"].get(i, s)) for i, s in order if i not in plan["cut"]]
