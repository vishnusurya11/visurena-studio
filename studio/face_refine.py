"""The wide-shot face refine: policy (owner 2026-10-17, "I like face improvements a
lot in wide shots, go ahead"; decision architecture/decisions/2026-10-17-face-refine.md).

A wide or full take draws its faces at 25-40 px of 768: the pixels are not there,
and no upscaler adds them (docs/audit/2026-10-16_model_tests, F0).  F2 re-renders a
tracked crop of each face through H3 at denoise 0.45 with ONLY that person's sheet;
assemble pastes the crop into the master AFTER the 4x upscale (pasted into the 768
take the new detail averages away again).

This module is the pure half: which takes, who each face is, what it costs on the
episode clock, the crop's prompt, and the gate that keeps a refined crop or falls
back to the unrefined take.  No file, no GPU, no model.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass

WORKFLOW = "video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg_facecrop_v2v_mickmumpitz"
"""F2's graph (comfy_studio, 2026-10-16): the narration take stack + H3InjectVideoLatent."""
DENOISE = 0.45
REFINE_SIZES = ("wide", "full")
NEVER = ("insert",)
SMALL_FACE_PX = 60.0
"""A face under this many render pixels gets the refine at any planned size."""

SECONDS_PER_FACE = 110.0
REF_FRAMES = 192
"""F2 on the 4090: 110 s of GPU for one face over a 192-frame take (51 s for 90)."""
CHECK_RESERVE_S = 550.0
"""A full take_dq re-measure (step_09.DQ_PASS_SECONDS): a refine must leave it its time."""

POS_WEIGHT = 0.3
MATCH_FLOOR = 0.0
"""A track whose best person scores under this is left unrefined (a stranger, an extra)."""

ID_DROP = 0.05
SEAM_MAX = 18.0
FLICKER_RATIO = 1.10
FLICKER_SLACK = 0.5
"""The gate's walls; calibrated on F2 (kept by eye) against F3 (refused by eye) on
ep01 T00/T22/T19 (docs/calibration/face_refine.md): face-region flicker pasted /
unpasted 0.81-0.95 on F2, 1.15-1.32 on F3; seam 7.3-9.2 on F2 (F3 2.0-2.7: the
seam wall guards a regression, it does not separate these two); identity 0.15 ->
0.59 on F2's T00, never down by more than 0.02 on either arm."""


# ---- selection -----------------------------------------------------------------------

def face_px(dq: dict | None, height: int) -> float | None:
    """take_dq's face-at-end share, in render pixels; None when unmeasured."""
    row = next((g for g in (dq or {}).get("gates", []) if g.get("name") == "face-at-end"), None)
    value = (row or {}).get("value")
    return None if value is None else float(value) * height


def wants(sizes: list[str], px: float | None) -> bool:
    """A wide or full shot always; any other shot but an insert when its face is small."""
    if any(s in NEVER for s in sizes):
        return False
    return any(s in REFINE_SIZES for s in sizes) or (px is not None and px < SMALL_FACE_PX)


def warp_state(dq: dict | None) -> str:
    """G-WARP's state in a dq record (studio/warp_gate.py), '' unmeasured."""
    return str((((dq or {}).get("measures") or {}).get("warp") or {}).get("state") or "")


def passed_but_warp(dq: dict) -> bool:
    """The dq passed, or its only hard failures are G-WARP's (F2 is the warp's last cure)."""
    failed = {g.get("name") for g in dq.get("gates", []) if g.get("hard") and not g.get("ok")}
    return bool(dq.get("passed")) or failed == {"warp"}


def warp_routed(dq: dict, taken: int) -> bool:
    """G-WARP sends this take to F2: a warn, an unreadable face, or a fail past its retakes."""
    from studio import warp_gate
    return warp_gate.cure(warp_state(dq), taken) == "refine"


def eligible(card: dict, sizes: list[str], dq: dict | None, height: int, taken: int = 0) -> bool:
    """The take shows a planned face, passed its dq (but for G-WARP), and wants the
    refine by its size or by G-WARP; `taken` is its retakes so far."""
    if not card.get("faces") or not dq or not passed_but_warp(dq) or any(s in NEVER for s in sizes):
        return False
    if not dq.get("passed") and not warp_routed(dq, taken):
        return False
    return wants(sizes, face_px(dq, height)) or warp_routed(dq, taken)


def selected(cards: list[dict], sizes: dict[int, str], dqs: dict[int, dict], height: int,
             taken: dict[int, int] | None = None) -> list[int]:
    """The take indices the refine works on, in take order."""
    out = []
    for c in cards:
        i = int(c["index"])
        shot_sizes = [sizes[s] for s in c.get("shots") or [c["index"]] if s in sizes]
        if eligible(c, shot_sizes, dqs.get(i), height, (taken or {}).get(i, 0)):
            out.append(i)
    return sorted(out)


# ---- the clock -----------------------------------------------------------------------

def price(faces: int, frames: int) -> float:
    """GPU seconds a take's refine is priced at."""
    return SECONDS_PER_FACE * max(faces, 0) * max(frames, 0) / REF_FRAMES


def cut(budget, step: str, seconds: float) -> bool:
    """The refine is the FIRST thing cut for time: it runs only while the reserve
    holds it AND a full measuring pass after it.  A check is never cut for a refine."""
    if budget is None:
        return False
    return not budget.leaves_reserve(step, seconds + CHECK_RESERVE_S)


# ---- the cast a take staged ------------------------------------------------------------

@dataclass(frozen=True)
class Subject:
    name: str
    picture: int
    said: str


@dataclass(frozen=True)
class Person:
    k: int
    who: str
    name: str
    said: str
    sheet: str


SUBJECT = re.compile(r"^<Subject (\d+)> is (.+?) in <Picture (\d+)>: (.*)$", re.M)
SHEET = re.compile(r"(?:^|/)characters/([^/]+)/")


def subjects(prompt: str) -> dict[int, Subject]:
    """`<Subject k> is NAME in <Picture j>: definition` lines of a take prompt."""
    return {int(k): Subject(name, int(j), said.strip()) for k, name, j, said in SUBJECT.findall(prompt)}


def cast_of(prompt: str, refs: list[str]) -> list[Person]:
    """Every staged person whose picture is a character sheet, in subject order."""
    out = []
    for k, s in subjects(prompt).items():
        ref = refs[s.picture - 1] if 0 < s.picture <= len(refs) else ""
        if found := SHEET.search(ref):
            out.append(Person(k, found.group(1), s.name, s.said, ref))
    return out


def pronoun(said: str) -> str:
    """His or her, off the definition's own 'defines this man/girl alone'."""
    found = re.search(r"defines this (\w+)", said)
    return "her" if found and found.group(1) in ("woman", "girl", "lady") else "his"


SIDES = {"LEFT": 0.2, "CENTRE": 0.5, "CENTER": 0.5, "RIGHT": 0.8}


AT_SIDE = re.compile(r"\bat the (LEFT|RIGHT|CENTRE|CENTER)\b")


def positions(prompt: str) -> dict[int, float]:
    """Horizontal priors (share of the width): "at the LEFT/CENTRE/RIGHT" in a
    sentence of the shot text that names exactly one subject, its first saying.
    A direction of travel ("walk on to the RIGHT") is no position: Jekyll ep01
    T22 put Utterson on Enfield's face that way."""
    text = prompt.split("detailed_description:", 1)[-1]
    out: dict[int, float] = {}
    for sentence in re.split(r"(?<=[.;])\s+", text):
        named = set(re.findall(r"<Subject (\d+)>", sentence))
        side = SIDES[found.group(1)] if (found := AT_SIDE.search(sentence)) else None
        if len(named) == 1 and side is not None:
            out.setdefault(int(named.pop()), side)
    return out


def style_line(prompt: str) -> str:
    """The take's look line: the first line of its detailed description."""
    text = prompt.split("detailed_description:", 1)[-1].strip()
    return text.splitlines()[0].strip() if text else ""


# ---- matching ------------------------------------------------------------------------

def match_score(identity: float, x: float, prior: float | None) -> float:
    """Identity against the sheet, plus agreement with the plan's side when it has one."""
    if prior is None:
        return identity
    return identity + POS_WEIGHT * (1.0 - 2.0 * abs(x - prior))


def assign(scores: dict[tuple[int, str], float], tracks: list[int], people: list[str]) -> dict[int, str]:
    """The one-to-one track -> person map with the best total; a pair under the floor is dropped."""
    best, best_total = {}, float("-inf")
    for chosen in itertools.permutations(tracks, min(len(tracks), len(people))):
        for order in itertools.permutations(people, len(chosen)):
            total = sum(scores.get(pair, float("-inf")) for pair in zip(chosen, order))
            if total > best_total:
                best, best_total = dict(zip(chosen, order)), total
    return {t: who for t, who in best.items() if scores.get((t, who), float("-inf")) >= MATCH_FLOOR}


# ---- the crop's prompt -------------------------------------------------------------------

def crop_prompt(person: Person, style: str, seconds: float) -> str:
    """F2's prompt: one person, the face of their sheet, the guide's head motion."""
    his = pronoun(person.said)
    said = re.sub(r"<Picture \d+>", "<Picture 1>", person.said)
    return (f"subject_definitions:\n<Subject 1> is {person.name} in <Picture 1>: {said}\n"
            f"<Audio 1> is the take's complete audio track and runs silent for its whole length.\n\n"
            f"summary:\n[reference generation + audio reuse] One {seconds:.2f}-second close-up of <Subject 1>'s "
            f"head and shoulders, redrawn from the guide video with the face of <Picture 1>.\n\n"
            f"detailed_description:\n{style}\n"
            f"[Shot 1] A close-up of <Subject 1>'s face at the CENTRE, {his} head half the frame's height; "
            f"sharp angular black ink linework on the eyes, brows, nose and mouth; the face of <Picture 1>; "
            f"the head moves exactly as in the guide video.\n\noverall_soundscape: Open air.\n\nnon_diegetic_music: N/A")


# ---- the gate ------------------------------------------------------------------------------

SAME_MAX = 0.5
"""Mean |refined - source| per pixel under which the refine changed nothing.  The
collect bug (Kawajiri POC, 2026-10-18) filed the source crop as refined: 0.0; the
real F2 render of the same crop measured 11.4.  A refine that returns its input
passes every other wall, so this one is first."""


def saved_node(graph: dict) -> str:
    """The id of the graph's one Save* node: where its render is reported."""
    found = [k for k, n in graph.items() if str(n.get("class_type", "")).startswith("Save")]
    if len(found) != 1:
        raise ValueError(f"expected one Save node, found {found}")
    return found[0]


@dataclass(frozen=True)
class Measures:
    """One refined crop against the take it came from, at window scale.
    id_*: facenet cosine to the sheet at the crop's face (None unread); seam: mean
    level difference in the feather band; flick_*: frame-to-frame difference of the
    face region; faces_*: the most faces any one sampled crop shows (inside the
    window, overlaps merged); change: mean |refined - source crop| per pixel."""
    id_src: float | None
    id_ref: float | None
    seam: float
    flick_src: float
    flick_ref: float
    faces_src: int
    faces_ref: int
    change: float | None = None


def face_refusal(src: int, ref: int) -> str:
    """A clone (a crop with more faces than the source ever showed, at least the
    one the track was cut round) or a lost face; '' when the count holds."""
    if ref > max(src, 1) or (src >= 1 and ref == 0):
        return f"faces {ref} != {src}"
    return ""


def refusals(m: Measures) -> list[str]:
    """Every wall the refined crop breaks, named with its numbers."""
    out = []
    if m.change is not None and m.change < SAME_MAX:
        out.append(f"the refined crop is its source (change {m.change:.2f} < {SAME_MAX})")
    if m.id_src is not None and (m.id_ref is None or m.id_ref < m.id_src - ID_DROP):
        out.append(f"identity {m.id_ref} < {m.id_src} - {ID_DROP}")
    if m.seam > SEAM_MAX:
        out.append(f"seam {m.seam:.1f} > {SEAM_MAX}")
    if m.flick_ref > m.flick_src * FLICKER_RATIO + FLICKER_SLACK:
        out.append(f"flicker {m.flick_ref:.2f} > {m.flick_src:.2f} x {FLICKER_RATIO} + {FLICKER_SLACK}")
    if said := face_refusal(m.faces_src, m.faces_ref):
        out.append(said)
    return out


def decide(m: Measures) -> tuple[bool, str]:
    """(kept, why): kept only when no wall is broken; else the unrefined take."""
    said = refusals(m)
    return (not said, "; ".join(said) or "kept")
