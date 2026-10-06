"""Mechanical motion-head rebalancing from the camera catalog (G-MOVES, G-STILL,
G-AIM, G-ANCHOR, M2 -- the self-curing pipeline, AREA 2, 2026-10-05).

MEASURED: the old cure (`plan_cures.vary_heads`) could only produce PUSH and
LOCKED, so on ep18 it drove push_slow to share 0.30 and locked to 0.26 while
distinct moves stayed at 6 < MIN_MOVES 8; and "M2 shot N:" / "G-ANCHOR shot N:"
rows matched no cure and became hand edits.  This module renders heads from the
full catalog (8 legal templates keyed by shot size, never tilt_down/crane_down/
rack_focus), aims them at nouns `at_rest` provably holds, sizes the travel under
`plan_gates.cap_for`, and VERIFIES every candidate by replaying the real gate
predicates (`head_ok`) before writing it -- the G-CROWD-CLOSE "cure measures
like the checker" pattern.  $0, deterministic, book-neutral, no llm import.
"""
from __future__ import annotations

import re
from collections import Counter
from types import SimpleNamespace

from studio import cell_gates, episode_spec, plan_gates
from studio import episode_ref_official as ro

HEADS = {
    "locked": "The camera holds a locked-off frame",
    "push_slow": "The camera pushes in toward the {aim}, travelling {amount}, "
                 "across the whole shot",
    "pull_reveal": "The camera pulls back from the {aim}, travelling {amount}, "
                   "across the whole shot",
    "pan_to": "The camera pans from the {a} to the {b}, travelling {amount}, "
              "across the whole shot",
    "tilt_up": "The camera tilts up from the {a} to the {b}, travelling {amount}, "
               "across the whole shot",
    "track_lateral": "The camera tracks sideways to the right, past the {aim}, "
                     "travelling {amount}, across the whole shot",
    "follow": "The camera tracks behind the {aim}, travelling {amount}, "
              "across the whole shot",
    "crane_up": "The camera rises above the {aim}, travelling {amount}, "
                "across the whole shot",
}
"""docs/calibration/camera_catalog.md, affirmative and direction only.  Each
template round-trips to its own id through `plan_gates.MOVE_VERBS` first-match
(the regex round-trip lock in tests); the catalog's "slowly" is NOT copied (ep19:
the owner's no-slow rule is the contract, and a pushed/risen head broke it); `, travelling` sits in `cell_gates.ENDS`'
lookahead so a pan's {b} is captured cleanly; `SAID_AMOUNT` strips the travel
from the take prompt, per 'H3 obeys direction, not amount'."""

LOCKED = HEADS["locked"]

LEGAL = {
    "wide": ["pan_to", "crane_up", "pull_reveal", "tilt_up", "follow", "track_lateral", "locked"],
    "full": ["pan_to", "crane_up", "pull_reveal", "tilt_up", "follow", "track_lateral", "locked"],
    "medium": ["push_slow", "follow", "pull_reveal", "tilt_up", "pan_to", "track_lateral", "locked"],
    "medium_close": ["push_slow", "tilt_up", "pull_reveal", "locked"],
    "close": ["locked", "pull_reveal", "push_slow"],
    "extreme_close": ["locked", "pull_reveal"],
    "insert": ["locked", "track_lateral", "crane_up", "pull_reveal", "push_slow"],
}
"""Catalog order per size.  tilt_down/crane_down/rack_focus are the IGNORED set
(G-STILL), handheld and orbit are untested / one-per-episode: never offered."""

AMOUNT_LADDER = [("a hand's breadth", 1.0), ("a forearm", 2.5), ("a head's height", 3.0),
                 ("a short stride", 5.0), ("a stride", 10.0), ("two strides", 20.0)]
"""The rungs a cure may write, in `plan_gates.AMPLITUDE`'s own words and units."""

PROP_TOKEN_MIN = 4
"""A setup-prop-id token this long can collide with an aim noun (G-SOURCE)."""


def amount_for(cap: float, seconds: float) -> str:
    """The largest ladder rung under the shot's cap and its travel-rate wall."""
    wall = min(cap, plan_gates.TRAVEL_PER_SECOND * max(seconds, 0.5))
    fits = [phrase for phrase, units in AMOUNT_LADDER if units <= wall]
    return fits[-1] if fits else AMOUNT_LADDER[0][0]


def probe(shot: dict, motion: str | None = None) -> SimpleNamespace:
    """The namespace the REAL gates read: the same attrs as `Shot`."""
    return SimpleNamespace(
        index=shot.get("index", 0), size=shot.get("size") or "",
        motion=(shot.get("motion") or "") if motion is None else motion,
        camera=shot.get("camera") or "", at_rest=shot.get("at_rest") or "",
        frame=shot.get("frame") or "", faces=shot.get("faces") or [],
        extras=shot.get("extras") or 0, setup=shot.get("setup") or "",
        still=shot.get("still", False))


def setup_ns(setup: dict | None) -> SimpleNamespace:
    """The one `Setup` attr the move gates read (`cap_for` -> `figures`)."""
    return SimpleNamespace(crowd=(setup or {}).get("crowd") or "")


def prop_tokens(setup: dict | None) -> set[str]:
    """Tokens of the setup's prop ids long enough to collide with an aim noun."""
    return {t for p in (setup or {}).get("props") or []
            for t in re.split(r"[_\W]+", str(p).lower()) if len(t) >= PROP_TOKEN_MIN}


def cell_aims(shot: dict, setup: dict | None = None) -> list[str]:
    """Aim nouns `at_rest` provably holds: one head noun per clause, the FOCUS
    clause first, and no setup-prop token the shot's pre-rewrite frame+motion
    does not already name (G-SOURCE: a cure never acquires a new unspanned claim)."""
    clauses = [c for c in re.split(r"[;.,]", shot.get("at_rest") or "") if c.strip()]
    clauses.sort(key=lambda c: "FOCUS" not in c)        # stable: FOCUS clause first
    prose = f"{shot.get('frame') or ''} {shot.get('motion') or ''}".lower()
    banned = {t for t in prop_tokens(setup) if not re.search(rf"\b{re.escape(t)}\b", prose)}
    out: list[str] = []
    for clause in clauses:
        noun = episode_spec.head_noun(clause)
        if noun and noun not in out and noun not in banned:
            out.append(noun)
    return [n for n in out if cell_gates.in_cell(n, probe(shot))]


def render_head(move: str, aims: list[str], travel: str) -> str | None:
    """The catalog template, filled; None when the cell lacks the aims it needs."""
    template = HEADS[move]
    if move == "locked":
        return LOCKED
    if "{a}" in template:
        return template.format(a=aims[0], b=aims[1], amount=travel) if len(aims) > 1 else None
    return template.format(aim=aims[0], amount=travel) if aims else None


def splice(motion: str, head: str) -> str:
    """The motion with `head` as its camera half: PREPENDED on an M2 motion
    (`camera_clause` proves it has no camera half, so every clause is an action
    that stays), else the `take_ladder.substitute` shape."""
    old_head, *rest = [c.strip() for c in (motion or "").split(";")]
    cam, subject = ro.camera_clause(old_head)
    kept = [old_head] if not cam else ([subject] if subject else [])
    return "; ".join([head] + [c for c in kept + rest if c])


def head_faults(shot, head: str, prev_id: str, next_id: str, setup) -> list[str]:
    """CURE-REPLAY: which REAL gate predicates refuse this candidate -- the
    cure measures like the checker, never a parallel implementation."""
    new_motion = splice(getattr(shot, "motion", "") or "", head)
    p = SimpleNamespace(**{**vars(shot), "motion": new_motion})
    out = []
    if plan_gates.move_id(p.motion, p.camera) in {prev_id, next_id}:
        out.append(f"the move repeats a neighbour ({prev_id!r}/{next_id!r}): twice running")
    if plan_gates.still_fault(p) is not None:
        out.append("G-STILL: the move renders still")
    if any(not cell_gates.in_cell(phrase, p) for _, phrase in cell_gates.aimed_at(head)):
        out.append("G-AIM: an aim noun at_rest does not hold")
    if cell_gates.anchored_truck(p):
        out.append("G-ANCHOR: a sideways truck or pan on an anchored person")
    got = plan_gates.amount(head)
    if got is not None and got > plan_gates.cap_for(p, setup)[0]:
        out.append(f"G-MOVE: travel {got} over the cap {plan_gates.cap_for(p, setup)[0]}")
    if "M2" in {c for c, _ in episode_spec.motion_faults(new_motion)}:
        out.append("M2: the head names no camera move")
    if word := episode_spec.slow_word(head):
        out.append(f"NO-SLOW: the head asks for a slow shot ({word!r})")
    return out


def head_ok(shot, head: str, prev_id: str, next_id: str, setup) -> bool:
    """A candidate head is written only when every replayed gate passes."""
    return not head_faults(shot, head, prev_id, next_id, setup)


def candidates(shot: dict, counts: Counter, prev_id: str, next_id: str,
               setup: dict | None, seconds: float, dialogue: bool = False) -> list[str]:
    """Every size-legal head the gates accept, least-used move first.  A
    dialogue shot only ever goes locked (the catalog: locked carries dialogue best)."""
    legal = ["locked"] if dialogue else LEGAL.get(shot.get("size") or "", ["locked"])
    aims = cell_aims(shot, setup)
    sns = setup_ns(setup)
    travel = amount_for(plan_gates.cap_for(probe(shot), sns)[0], seconds)
    heads = [render_head(m, aims, travel)
             for m in sorted(legal, key=lambda m: (counts.get(m, 0), legal.index(m)))]
    return [h for h in heads if h is not None and head_ok(probe(shot), h, prev_id, next_id, sns)]


def choose(shot: dict, counts: Counter, prev_id: str, next_id: str,
           setup: dict | None, seconds: float, dialogue: bool = False) -> str | None:
    """The first accepted candidate, or None."""
    return next(iter(candidates(shot, counts, prev_id, next_id, setup, seconds, dialogue)), None)


def contract_errors(doc: dict) -> set[str]:
    """The Episode contract's refusals, as comparable strings (empty = valid).
    A partial doc's missing fields show up in both measurements and cancel."""
    from pydantic import ValidationError
    try:
        episode_spec.Episode(**doc)
    except ValidationError as why:
        return {f"{e.get('loc')}: {e.get('msg')}" for e in why.errors()}
    except Exception as why:    # noqa: BLE001 -- any refusal is a refusal
        return {f"{type(why).__name__}: {why}"}
    return set()


def write_lawful(doc: dict, shot: dict, heads: list[str], baseline: set[str]) -> str | None:
    """Splice the first head that leaves the FULL contract no worse than
    `baseline`; every refused head is undone (ep19: "shots.1 'motion' asks for
    a slow shot").  The written head, or None with the motion untouched."""
    old = shot.get("motion") or ""
    for head in heads:
        shot["motion"] = splice(old, head)
        if not contract_errors(doc) - baseline:
            return head
    shot["motion"] = old
    return None


def dialogue_shots(doc: dict) -> set[int]:
    """The shots a dialogue line lands on (locked-only in a rewrite)."""
    return {line["shot"] for line in doc.get("lines") or []
            if line.get("kind") == "dialogue"}


def shot_seconds_of(doc: dict, rate: float = 3.0) -> dict[int, float]:
    """Projected seconds per shot, with the checker's own constants.  Lazy
    import: `plan_cures` imports this module back for its dispatch wrapper."""
    from studio import plan_cures
    return plan_cures._shot_secs(doc, rate)


def share_carriers(ids: list[str], order: list[int], talk: set[int]) -> list[int]:
    """Enough carriers of the top-share id that the survivors fit the wall,
    dialogue shots last (they can only go locked)."""
    if not ids:
        return []
    top = max(sorted(set(ids)), key=ids.count)
    excess = ids.count(top) - int(plan_gates.MAX_MOVE_SHARE * len(ids))
    carriers = [i for i, mid in zip(order, ids) if mid == top]
    carriers.sort(key=lambda i: (i in talk, i))
    return carriers[:max(excess, 0)]


def rewrite_set(doc: dict, ids: list[str], indices: list[int]) -> set[int]:
    """Fault-row shots + top-share carriers + the later shot of each
    twice-running pair + distinct-floor fillers; a dialogue shot already
    locked is left alone (nothing a rewrite could change)."""
    order = [s["index"] for s in doc.get("shots") or []]
    talk = dialogue_shots(doc)
    out = {i for i in indices if i in order}
    out |= set(share_carriers(ids, order, talk))
    out |= {order[k] for k in range(1, len(ids)) if ids[k] == ids[k - 1]}
    counts = Counter(ids)
    pool = sorted((i for i in order if i not in out and i not in talk),
                  key=lambda i: (-counts[ids[order.index(i)]], i))
    for i in pool:
        if len(set(ids)) + len(out) >= plan_gates.MIN_MOVES:
            break
        out.add(i)
    return {i for i in out if not (i in talk and ids[order.index(i)] == "locked")}


def rebalance(doc: dict, indices: list[int]) -> tuple[dict, list[int]]:
    """Every shot in the rewrite set gets the least-used legal verified head,
    first-wins ascending, counts updated after each accept -- a pure function
    of the doc, so two runs are byte-identical.  Shots no mechanical candidate
    cures come back as `unfixed` for the llm escape (`studio.move_llm`)."""
    shots = doc.get("shots") or []
    order = [s["index"] for s in shots]
    by = {s["index"]: s for s in shots}
    ids = plan_gates.move_ids([probe(s) for s in shots])
    counts = Counter(ids)
    secs, talk = shot_seconds_of(doc), dialogue_shots(doc)
    setups, baseline = doc.get("setups") or {}, contract_errors(doc)
    unfixed: list[int] = []
    for i in sorted(rewrite_set(doc, list(ids), indices)):
        k = order.index(i)
        heads = candidates(by[i], counts, ids[k - 1] if k else "",
                           ids[k + 1] if k + 1 < len(ids) else "",
                           setups.get(by[i].get("setup")), secs.get(i, 2.0), i in talk)
        if write_lawful(doc, by[i], heads, baseline) is None:
            unfixed.append(i)
            continue
        new_id = plan_gates.move_id(by[i]["motion"], by[i].get("camera") or "")
        counts[ids[k]] -= 1
        counts[new_id] += 1
        ids[k] = new_id
    return doc, unfixed
