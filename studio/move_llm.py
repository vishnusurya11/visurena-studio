"""The LLM escape for camera heads no mechanical candidate cures (AREA 2).

`move_rebalance` returns a shot `unfixed` when every size-legal move collides
with its neighbours or `at_rest` yields no clean aim noun.  This module asks
the workhorse tier for ONE head per such shot -- a single guarded structured
call through `studio.llm.structured` (guard_spend runs inside the caller) --
validates the answer with a strict pydantic contract, then re-verifies it with
the SAME `move_rebalance.head_ok` replay.  One re-ask carrying the exact failed
predicate names; a second failure returns None and the fault row stays uncured
for the writer -- bounded, never a loop.  `caller` is the `_agent` test seam.
"""
from __future__ import annotations

import re
from collections import Counter

from pydantic import BaseModel, field_validator
from strands.types.exceptions import StructuredOutputException

from studio import cell_gates, llm, plan_gates
from studio import move_rebalance as mr
from studio import episode_ref_official as ro

TIER = "workhorse"
MAX_HEAD_WORDS = 30
HEAD_SHAPE = re.compile(r"^The camera [a-z]")
BANNED_MOVES = ("tilt_down", "crane_down", "rack_focus", "orbit", "handheld")
"""The IGNORED set H3 renders still, plus the untested / one-per-episode pair."""


class MotionHead(BaseModel):
    """One camera-move head.  The validator raises ValueError, which the caller
    surfaces as StructuredOutputException and `llm.re_ask` quotes back."""
    head: str

    @field_validator("head")
    @classmethod
    def _lawful(cls, got: str) -> str:
        got = got.strip()
        if not HEAD_SHAPE.match(got):
            raise ValueError('the head must start "The camera " followed by its verb')
        if ";" in got:
            raise ValueError("one sentence only: no semicolons")
        if len(got.split()) > MAX_HEAD_WORDS:
            raise ValueError(f"{len(got.split())} words; the wall is {MAX_HEAD_WORDS}")
        if got != mr.LOCKED and "across the whole shot" not in got:
            raise ValueError('a travelling head ends "across the whole shot" '
                             "(only the locked-off phrasing is exempt)")
        return got


PROMPT = """You rewrite ONE camera-move head for one shot of a storyboard plan. Answer with the head only.

THE SHOT
size: {size}
frame: {frame}
at_rest -- the only things that exist in the picture: {at_rest}
action clauses that stay (do not restate or contradict them): {rest_clauses}
dialogue on this shot: {yes_no}

THE RULES -- each is a hard gate; a head that breaks one is refused:
- ONE sentence, no semicolons. It MUST start "The camera ".
- Use exactly one of these moves, in this affirmative, direction-only phrasing: {legal_moves}
- Never use these moves: {banned_moves} -- the render model ignores them, or the neighbouring shots already carry them ({prev_id}, {next_id}).
- Every noun the move starts on or aims at MUST be a word quoted from at_rest above. A move toward what is not drawn invents it.
{anchored_line}- Say the travel as "travelling {max_amount}", and end the sentence with "across the whole shot" (a locked-off head needs neither).
- No stillness words (still, holds still, motionless, frozen), no "keeps the ..." clause, no walking-pace words on the camera."""


def kept_clauses(motion: str) -> str:
    """The clauses the new head leaves in place: everything on an M2 motion,
    the subject half and the rest clauses otherwise (`splice`'s own shape)."""
    old_head, *rest = [c.strip() for c in (motion or "").split(";")]
    cam, subject = ro.camera_clause(old_head)
    kept = [old_head] if not cam else ([subject] if subject else [])
    return "; ".join(c for c in kept + rest if c) or "none"


def anchored_line(shot: dict) -> str:
    """The G-ANCHOR warning, only when a sideways truck WOULD fire on this shot."""
    truck = "The camera tracks sideways to the right, past it"
    probe = mr.probe(shot, motion=mr.splice(shot.get("motion") or "", truck))
    if not cell_gates.anchored_truck(probe):
        return ""
    return (f"- Never a sideways track or pan: this is a {shot.get('size')} of a "
            "person anchored to scenery; push in, rise, or hold.\n")


def head_prompt(shot: dict, setup: dict | None, counts: dict, prev_id: str,
                next_id: str, dialogue: bool = False) -> str:
    """The spec's one-shot contract, built from the shot's own words; the
    legal moves list least-used first, so the model leans the same way the
    mechanical cure does."""
    legal = mr.LEGAL.get(shot.get("size") or "", ["locked"])
    legal = sorted(legal, key=lambda m: (counts.get(m, 0), legal.index(m)))
    cap = plan_gates.cap_for(mr.probe(shot), mr.setup_ns(setup))[0]
    return PROMPT.format(
        size=shot.get("size") or "", frame=shot.get("frame") or "",
        at_rest=shot.get("at_rest") or "", rest_clauses=kept_clauses(shot.get("motion") or ""),
        yes_no="yes" if dialogue else "no",
        legal_moves="; ".join(f"{m}: {mr.HEADS[m]}" for m in legal),
        banned_moves=", ".join(BANNED_MOVES), prev_id=prev_id or "none",
        next_id=next_id or "none", anchored_line=anchored_line(shot),
        max_amount=mr.amount_for(cap, 2.0))


def _asked(prompt: str, caller) -> str | None:
    """One guarded structured call; OverBudget and ContentFiltered are never
    retried (transient_retries=0) -- the row goes to the writer instead."""
    try:
        got = llm.structured(TIER, prompt, MotionHead, retries=3,
                             transient_retries=0, _agent=caller)
    except (llm.OverBudget, llm.ContentFiltered, StructuredOutputException):
        return None
    return got.head


def fallback_head(shot: dict, setup: dict | None, counts: dict, prev_id: str,
                  next_id: str, caller=None, dialogue: bool = False) -> str | None:
    """A verified head from the workhorse tier, or None after one re-ask."""
    prompt = head_prompt(shot, setup, counts or {}, prev_id, next_id, dialogue)
    sns, p = mr.setup_ns(setup), mr.probe(shot)
    head = _asked(prompt, caller)
    if head is None:
        return None
    why = mr.head_faults(p, head, prev_id, next_id, sns)
    if not why:
        return head
    again = _asked(llm.re_ask(prompt, RuntimeError("; ".join(why))), caller)
    if again is not None and mr.head_ok(p, again, prev_id, next_id, sns):
        return again
    return None


def cure_unfixed(doc: dict, unfixed: list[int], setups: dict,
                 caller=None) -> tuple[dict, list[int]]:
    """Each unfixed shot gets at most one call + one re-ask; accepted heads
    splice in exactly as the mechanical cure's do, and the still-unfixed
    indices come back for the writer path."""
    shots = doc.get("shots") or []
    order = [s["index"] for s in shots]
    by = {s["index"]: s for s in shots}
    ids = plan_gates.move_ids([mr.probe(s) for s in shots])
    counts: Counter = Counter(ids)
    talk, baseline = mr.dialogue_shots(doc), mr.contract_errors(doc)
    still: list[int] = []
    for i in sorted(i for i in unfixed if i in by):
        k = order.index(i)
        head = fallback_head(by[i], (setups or {}).get(by[i].get("setup")) or {}, counts,
                             ids[k - 1] if k else "",
                             ids[k + 1] if k + 1 < len(ids) else "", caller,
                             dialogue=i in talk)
        if head is None or mr.write_lawful(doc, by[i], [head], baseline) is None:
            still.append(i)
            continue
        counts[ids[k]] -= 1
        ids[k] = plan_gates.move_id(by[i]["motion"], by[i].get("camera") or "")
        counts[ids[k]] += 1
    return doc, still
