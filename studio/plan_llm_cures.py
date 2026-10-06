"""The one llm plan cure: a single shot's position fields rewritten on the
workhorse tier (G-TWICE, and G-GHOST fields the strip guard refused).

The model's answer is never trusted: a CODE-SIDE PROBE re-runs both
plan_gates detectors on a one-shot clone, holds each field to a word budget,
and runs the style lints (negations, slow words) before anything lands in the
doc.  A failing probe is re-asked with its own fault lines, up to ASKS times;
after that the shot keeps its original fields and the battery re-flags it
(the existing DEFER terminal stands -- never a crash, never a hand edit).
`guard_spend` fires inside the real caller; `_agent` is the FakeModel test
seam (studio/llm.py) -- no test may call a paid API.
"""
from __future__ import annotations

import re
from types import SimpleNamespace

from pydantic import BaseModel
from strands.types.exceptions import StructuredOutputException

from studio import llm

TIER = "workhorse"
ASKS = 3
WORD_BAND = (0.6, 1.4)
"""Each returned field stays within 40% of the original field's words: a
rewrite is clause surgery, never a fresh composition."""


class ShotPositions(BaseModel):
    """One shot's three drawn-surface fields, rewritten to one position per person."""
    frame: str
    at_rest: str
    end: str


PROMPT = """You are fixing ONE shot of a storyboard plan. An image model draws every person the text asserts, so a person described in two places is drawn TWICE, and a named person's body part implies that whole person standing in frame.

THE SHOT (size: {size}):
faces (the ONLY people who may appear): {faces_with_descriptions}
people who must NOT appear or be referenced by name or body part: {ghost_names}
frame: {frame}
at_rest: {at_rest}
end: {end}

THE FAULTS, as the gate printed them:
{fault_lines}

Rewrite ONLY the fields frame, at_rest and end so that:
1. Each person in faces holds exactly ONE position per picture: frame+at_rest describe one picture (the first frame) and may place each person once; end describes one later picture and may place each person once. Delete or merge every second location for the same person; keep the position that the shot's motion arrives at.
2. No body part (shoulder, hand, arm, back, head) of anyone outside faces is mentioned; do not add any new person, limb or object.
3. Keep everything else byte-identical where possible: the shot size opening, the head-fraction clause ('his head a quarter of the frame's height'), UPPERCASE frame-edge words (LEFT, RIGHT, upper RIGHT), light clauses, and 'THE FOCUS OF THE PICTURE IS' openings stay exactly as written.
4. Style rules the lint enforces downstream: no stillness words (stays, holds, waits, pauses, still, motionless, frozen, unchanged); no 'slow' or 'slowly'; every walk, climb or ride keeps its pace phrase ('at a normal walking pace'); never write what is absent ('no', 'without', 'empty of') -- name what occupies the place instead; the end field's last clause names something that moves or a position reached by a mover, never a bare layout.
5. Each field stays within 40% of its current word count.

Return frame, at_rest and end in full."""


def shot_indices(rows: list[str]) -> list[int]:
    """The faulted shot numbers, exactly as plan_repair collects them."""
    return sorted({int(m.group(1)) for r in rows for m in [re.search(r"shot (\d+)", r)] if m})


def prompt_for(shot: dict, faces: list[str], ghost_names: list[str],
               fault_lines: list[str]) -> str:
    """The one-shot rewrite ask, from the shot's own words and the gate's own lines."""
    return PROMPT.format(size=shot.get("size") or "",
                         faces_with_descriptions=", ".join(faces) or "nobody",
                         ghost_names=", ".join(ghost_names) or "every cast member outside faces",
                         frame=shot.get("frame") or "", at_rest=shot.get("at_rest") or "",
                         end=shot.get("end") or "", fault_lines="\n".join(fault_lines))


def _clone(shot: dict, got: ShotPositions) -> SimpleNamespace:
    """The shot with the rewrite's three fields, for a one-shot probe episode."""
    return SimpleNamespace(index=shot.get("index"), faces=list(shot.get("faces") or []),
                           cuts=[SimpleNamespace(**c) for c in shot.get("cuts") or []],
                           motion=shot.get("motion") or "", camera=shot.get("camera") or "",
                           frame=got.frame, at_rest=got.at_rest, end=got.end)


def _word_rows(got: ShotPositions, shot: dict) -> list[str]:
    """The word budget: each field within WORD_BAND of the original, frame and
    at_rest never empty."""
    out = []
    for field in ("frame", "at_rest", "end"):
        n, was = len(getattr(got, field).split()), len((shot.get(field) or "").split())
        if field in ("frame", "at_rest") and n == 0:
            out.append(f"{field} came back empty")
        elif was and not (WORD_BAND[0] * was <= n <= WORD_BAND[1] * was):
            out.append(f"{field} is {n} words against the shot's {was}; stay within 40%")
    return out


def _style_rows(got: ShotPositions) -> list[str]:
    """The downstream lints, run up front: negations and slow words."""
    from studio import episode_spec
    from studio.affirm import negations
    out = []
    for field in ("frame", "at_rest", "end"):
        text = getattr(got, field)
        if bad := negations(text):
            out.append(f"{field} asks for an absence ({bad}); name what occupies the place")
        if word := episode_spec.slow_word(text):
            out.append(f"{field} asks for a slow shot ({word!r}); name the amount or a normal pace")
    return out


def probe(shot: dict, got: ShotPositions, names: dict[str, str]) -> list[str]:
    """Why the rewrite is refused, IN CODE: both detectors re-run on a one-shot
    probe episode, the word budget, the style lints -- never the model's own
    judgement of itself.  [] accepts."""
    from studio import plan_gates
    episode = SimpleNamespace(shots=[_clone(shot, got)])
    return (plan_gates.ghost_limb_faults(episode, names)
            + plan_gates.double_position_faults(episode, names)
            + _word_rows(got, shot) + _style_rows(got))


def _cured_shot(shot: dict, fault_lines: list[str], names: dict[str, str],
                caller) -> ShotPositions | None:
    """Up to ASKS probed asks; None keeps the original fields (the battery
    re-flags and the DEFER terminal stands -- never a crash)."""
    faces = list(shot.get("faces") or [])
    ghosts = sorted({e for e in names.values() if e not in faces})
    prompt = prompt_for(shot, faces, ghosts, fault_lines)
    asked = prompt
    for _ in range(ASKS):
        try:
            got = llm.structured(TIER, asked, ShotPositions, transient_retries=0, _agent=caller)
        except StructuredOutputException as spent:
            asked = llm.re_ask(prompt, spent)
            continue
        why = probe(shot, got, names)
        if not why:
            return got
        asked = llm.re_ask(prompt, RuntimeError("; ".join(why)))
    return None


def one_position(doc: dict, rows: list[str], names: dict[str, str], caller=None) -> dict:
    """G-TWICE's cure (and ghost fields the strip guard refused): each faulted
    shot rewritten once through the workhorse tier, accepted only on a clean
    probe.  OverBudget keeps the shot as-is with the row printed as remaining."""
    by = {s.get("index"): s for s in doc.get("shots") or []}
    for index in shot_indices(rows):
        shot = by.get(index)
        if shot is None:
            continue
        lines = [r for r in rows if re.search(rf"\bshot {index}\b", r)] or rows
        try:
            got = _cured_shot(shot, lines, names, caller)
        except llm.OverBudget as over:
            print(f"  one_position shot {index} remains: {str(over)[:140]}")
            continue
        if got is not None:
            shot["frame"], shot["at_rest"], shot["end"] = got.frame, got.at_rest, got.end
    return doc


def rewriter(doc: dict, names: dict[str, str], caller=None):
    """ghost_limbs' guard fallback: a (shot_index, field) callable closing
    over `one_position` and the live doc."""
    def rewrite(shot_index: int, field: str) -> None:
        one_position(doc, [f"G-GHOST shot {shot_index}: {field} carries a ghost body-part "
                           f"clause too large to strip; rewrite the position fields"],
                     names, caller=caller)
    return rewrite
