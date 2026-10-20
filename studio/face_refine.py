"""The face refine: policy (owner 2026-10-17, "I like face improvements a lot in wide
shots, go ahead"; decision architecture/decisions/2026-10-17-face-refine.md; widened to
every soft face 2026-10-19, owner: "why our fix skipped those shots? fix that").

A face under ~120 px of 768 draws its eye in 5-10 px, under one H3 token (32 px): the
pixels are not there, and no upscaler adds them (docs/audit/2026-10-16_model_tests, F0;
docs/audit/2026-10-19_face_blur/PLAN.md).  F2 re-renders a tracked crop of each soft
face through H3 with ONLY that person's sheet, at a denoise that follows the face's size;
assemble pastes the crop at cut scale, then the one upscale (owner 2026-10-18, 24caaeb).

This module is the pure half: which takes, who each face is, what it costs on the
episode clock, the crop's prompt, and the gate that keeps a refined crop or falls
back to the unrefined take.  No file, no GPU, no model.
"""
from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass

WORKFLOW = "video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg_facecrop_v2v_mickmumpitz"
"""F2's graph (comfy_studio, 2026-10-16): the narration take stack + H3InjectVideoLatent.
Never edited: the denoise is one of its inputs."""
DENOISE = 0.45
"""F2 at a 60 px face: T08 (55 px) and T18 (41 px) kept by the gate and liked by the owner."""
DENOISE_AT_PX = 60.0
DENOISE_PER_HALVING = 0.05
DENOISE_BAND = (0.40, 0.55)
"""ComfyUI-H3-FaceRefine (Carasibana, MIT) scales its denoise by face size: a smaller face
is magnified more into the crop and wants more redraw; a high denoise drifts the head.
Ours: +0.05 per halving of the face from the 0.45 point, held inside 0.40-0.55 (the
research plan's band to calibrate, docs/audit/2026-10-19_face_blur/PLAN.md arm A2)."""
NEVER = ("insert",)
SMALL_FACE_PX = 120.0
"""A face tracked under this many render pixels is soft, at any planned size: a 60-110 px
face of 768 draws a 5-10 px eye, the mush the owner saw on ep01 T05/T06/T13/T15
(docs/audit/2026-10-19_face_blur/pipeline_audit.md section 2).  It was 60 until
2026-10-19: six picks ended `no_faces` because their faces were 60-110 px."""

SECONDS_PER_FACE = 110.0
REF_FRAMES = 192
"""F2 on the 4090: 110 s of GPU for one face over a 192-frame take (51 s for 90)."""
CHECK_RESERVE_S = 550.0
"""A full take_dq re-measure (step_09.DQ_PASS_SECONDS): a refine must leave it its time."""

POS_WEIGHT = 0.3
MATCH_FLOOR = 0.0
"""A track whose best person scores under this is left unrefined (a stranger, an extra)."""

ID_DROP = 0.05
FLICKER_RATIO = 1.10
FLICKER_SLACK = 0.5
"""The gate's walls; calibrated on F2 (kept by eye) against F3 (refused by eye) on
ep01 T00/T22/T19 (docs/calibration/face_refine.md): face-region flicker pasted /
unpasted 0.81-0.95 on F2, 1.15-1.32 on F3; identity 0.15 -> 0.59 on F2's T00, never
down by more than 0.02 on either arm."""
SEAM_MAX = 18.0
"""The level change between the refined crop and the take where the paste's mask falls
(studio/face_gate.seam_and_flicker).  Through the hard feather it reads round 1's feather-band
seam again (the bench's 15 rows, within -1.3 / +0.8), so round 1's wall holds: kept rows 6.1-15.8,
refused 20.1-23.4.  Through a small face's soft mask the same crops read 6.1-16.3 and 19.8-25.1:
the soft paste spreads an edge, it does not hide one (docs/calibration/face_refine.md, fix round).
Round 2's first measure (mask x change averaged over the whole window outside the head, wall 10)
read a 13 px face 60 levels off as 2.5 and was withdrawn the same day."""
DRIFT_MAX = 35.0
"""Mean |refined - take| inside the face box (T8mars Parity Stitch's idea, ported): round 1's own
faces 11.6-31.6 (T07's child, a faceless blob given its face, the top); another row's refined face
against a take's face (64 px regions, 210 pairs) reads from 23.9, p5 32.4, median 48.9."""
OUTSIDE_MAX = 1.0
"""The most any pixel outside the face core's mask may move in the paste (levels; rounding only): the
take's hat, hair, collar and background are never the redraw's (owner 2026-10-19, ep01 iter2 warp)."""
BAND_WARP_MAX = 0.9
"""The band warp wall (px at 384, studio/face_gate.paste_check): flow from the take to the paste the Paster
makes, on the core's feather and out to 1.2 core radii, where the redraw's lines meet the take's.  The ep01
replay (docs/calibration/face_refine.md, face-warp round 2): this paste 0.27-0.67 on the 14 kept tracks;
the iter2 square paste read on its own band 0.46-1.19, round 1's ellipse 0.33-0.93.  A guard against a
gross misregistration: it refuses none of ep01's pastes.  One episode."""
TURN_MAX = 4.0
"""The most the redraw may turn the face (degrees; studio/face_gate.face_turn: the median change of MTCNN's
eye line, take -> redraw, over 12 crop pairs where both read one).  The face-core paste puts the redraw's
face in the take's head, so a re-posed face shows (ep01 T08: H3 turned the child's head; the paste showed
the redraw's eyes over the take's open mouth).  The ep01 replay: 0.9-2.84 on the faces kept by eye,
5.55-9.34 on T08's child, T09's Hyde (a tilt and a smirk), T26's Enfield (profile -> three-quarter) and
T01's Utterson (refused on its seam already).  One episode."""
CCIP_RISE = 0.03
CLIP_DROP = 0.05
"""The anime identity walls (PLAN_FINAL section 3): CCIP distance to the sheet may not rise by
more than 0.03 nor cross the same-character line (studio/anime_id.SAME_CHARACTER); clip_vision_h
cosine may not fall by more than 0.05.  Round 1: CCIP fell or held on all 15 faces (refined
0.011-0.064 to the own sheet, 0.152-0.324 to the other person's); clip rose on all 15."""


# ---- selection -----------------------------------------------------------------------

def soft(px: float | None) -> bool:
    """A tracked face too small to draw its eye; None (no face found) is not soft."""
    return px is not None and px < SMALL_FACE_PX


def denoise_for(px: float | None) -> float:
    """F2's denoise for a face of `px` render pixels: DENOISE at DENOISE_AT_PX, a little
    more for a smaller face, a little less for a bigger one, inside DENOISE_BAND."""
    if not px or px <= 0:
        return DENOISE
    lo, hi = DENOISE_BAND
    value = DENOISE + DENOISE_PER_HALVING * math.log2(DENOISE_AT_PX / px)
    return round(min(max(value, lo), hi), 3)


def warp_measure(dq: dict | None) -> dict:
    """The warp measure a dq record holds (studio/warp_gate.py); {} unmeasured."""
    return ((dq or {}).get("measures") or {}).get("warp") or {}


def warp_state(dq: dict | None) -> str:
    """G-WARP's state, recomputed from the logged numbers (a stored `fail` of an older
    gate does not stand); the stored state when no numbers were kept; '' unmeasured."""
    from studio import warp_gate
    m = warp_measure(dq)
    if "share" not in m:
        return str(m.get("state") or "")
    return warp_gate.verdict(m.get("S"), m.get("Se"), m["share"])


BARS = ("warp", "gait", "pulse", "frozen-whole", "lip-sync", "lag")
"""The hard rows F2 may be the cure of: the warp and the motion rows.  A failed identity,
clones, content, lettering, look or leak row still bars the take (ep01 T01: gait + unmeasurable)."""


def passed_but_warp(dq: dict) -> bool:
    """The dq passed, or every hard failure is a row the face refine may follow."""
    failed = {g.get("name") for g in dq.get("gates", []) if g.get("hard") and not g.get("ok")}
    return bool(dq.get("passed")) or failed <= set(BARS)


TRACKED_HIGH = 0.8


def readable(card: dict, dq: dict | None) -> bool:
    """Every planned face is tracked by the warp gate, for most of the take, at SMALL_FACE_PX
    or more AT ITS SMALLEST: the tracker need not run.  Never the track's median (a push-in from
    80 to 300 px reads 190 there); a record holding medians alone is left to the tracker.
    MTCNN misses small faces, so fewer tracks than faces proves nothing."""
    from studio import warp_gate
    m = warp_measure(dq)
    tracks = m.get("tracks") or []
    height = warp_gate.smallest_face(m)
    return (bool(tracks) and len(tracks) >= len(card.get("faces") or [None]) and m.get("share", 0) >= TRACKED_HIGH
            and height is not None and height >= SMALL_FACE_PX)


def soft_faces(card: dict, dq: dict | None) -> int:
    """The faces a take's refine is priced for: its planned faces less the warp tracks readable
    at their smallest (a close-up's big face costs no GPU), at least one."""
    tracks = warp_measure(dq).get("tracks") or []
    seen = sum(1 for t in tracks if t.get("min_px") is not None and t["min_px"] >= SMALL_FACE_PX)
    return max(len(card.get("faces") or []) - seen, 1)


def retake_owed(dq: dict, taken: int) -> bool:
    """G-WARP's one seed retake comes first: the refine would be spent on bytes the retake replaces."""
    from studio import warp_gate
    m = warp_measure(dq)
    return warp_gate.cure(warp_state(dq), taken, warp_gate.smallest_track(m)) == "seed"


def eligible(card: dict, sizes: list[str], dq: dict | None, taken: int = 0) -> bool:
    """A take the tracker looks at: a planned face not already readable, no insert, no hard
    failure outside BARS, no warp retake owed.  The plan size is not read (ep01 T26 is a
    medium with a 64 px face) and neither is face-at-end (T06 pushes in from 60 px)."""
    if not card.get("faces") or not dq or any(s in NEVER for s in sizes):
        return False
    return passed_but_warp(dq) and not retake_owed(dq, taken) and not readable(card, dq)


def selected(cards: list[dict], sizes: dict[int, str], dqs: dict[int, dict],
             taken: dict[int, int] | None = None) -> list[int]:
    """The take indices the refine tracks, in take order; each track under SMALL_FACE_PX is refined."""
    out = []
    for c in cards:
        i = int(c["index"])
        shot_sizes = [sizes[s] for s in c.get("shots") or [c["index"]] if s in sizes]
        if eligible(c, shot_sizes, dqs.get(i), (taken or {}).get(i, 0)):
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
    id_*: facenet cosine to the sheet at the crop's face (None unread); seam: the paste's mean
    level change outside the head; flick_*: frame-to-frame difference of the face region;
    faces_*: the most faces any one sampled crop shows (inside the window, overlaps merged);
    change: mean |refined - source crop| per pixel; drift: the same inside the face box;
    eye_*: the drawn-eye score (logged); ccip_*: CCIP distance to the sheet; clip_*: clip_vision_h
    cosine to the sheet (None unread); outside / band_warp / core_flow: the paste's (studio/face_gate.
    paste_measures; a row without band_warp was decided before them and is regated before a cut)."""
    id_src: float | None
    id_ref: float | None
    seam: float
    flick_src: float
    flick_ref: float
    faces_src: int
    faces_ref: int
    change: float | None = None
    drift: float | None = None
    eye_src: float | None = None
    eye_ref: float | None = None
    ccip_src: float | None = None
    ccip_ref: float | None = None
    clip_src: float | None = None
    clip_ref: float | None = None
    outside: float | None = None
    band_warp: float | None = None
    core_flow: float | None = None
    turn: float | None = None


def paste_refusals(m: Measures) -> list[str]:
    """The paste moved the take outside the face core, warped the band where it meets the take, or
    pasted a face the redraw turned (core_flow is logged, never a wall: it did not part T08 from the rest)."""
    out = []
    if m.outside is not None and m.outside > OUTSIDE_MAX:
        out.append(f"outside the face moved {m.outside:.1f} > {OUTSIDE_MAX}")
    if m.band_warp is not None and m.band_warp > BAND_WARP_MAX:
        out.append(f"band warp {m.band_warp:.2f} > {BAND_WARP_MAX}")
    if m.turn is not None and m.turn > TURN_MAX:
        out.append(f"the redraw turned the face {m.turn:.1f} deg > {TURN_MAX}")
    return out


def face_refusal(src: int, ref: int) -> str:
    """A clone (a crop with more faces than the source ever showed, at least the
    one the track was cut round) or a lost face; '' when the count holds."""
    if ref > max(src, 1) or (src >= 1 and ref == 0):
        return f"faces {ref} != {src}"
    return ""


def facenet_fell(m: Measures) -> bool:
    return m.id_src is not None and (m.id_ref is None or m.id_ref < m.id_src - ID_DROP)


def clip_fell(m: Measures) -> bool:
    return m.clip_src is not None and m.clip_ref is not None and m.clip_ref < m.clip_src - CLIP_DROP


def ccip_refusal(m: Measures) -> str:
    """The refined face moved away from its sheet by CCIP, or became another character; '' else."""
    from studio.anime_id import SAME_CHARACTER
    if m.ccip_src is None or m.ccip_ref is None:
        return ""
    if m.ccip_ref > m.ccip_src + CCIP_RISE or m.ccip_src < SAME_CHARACTER <= m.ccip_ref:
        return f"ccip {m.ccip_ref:.3f} vs {m.ccip_src:.3f} (+{CCIP_RISE}, same-character {SAME_CHARACTER:.3f})"
    return ""


def identity_refusal(m: Measures) -> str:
    """CCIP rules when read (anime-trained); else facenet and clip must BOTH fall to refuse, and
    with clip unread facenet alone decides, as before round 2."""
    if said := ccip_refusal(m):
        return said
    if facenet_fell(m) and (m.clip_src is None or clip_fell(m)):
        clip = "" if m.clip_src is None else f"; clip {m.clip_ref:.3f} < {m.clip_src:.3f} - {CLIP_DROP}"
        return f"identity {m.id_ref} < {m.id_src} - {ID_DROP}{clip}"
    return ""


def refusals(m: Measures) -> list[str]:
    """Every wall the refined crop breaks, named with its numbers."""
    out = []
    if m.change is not None and m.change < SAME_MAX:
        out.append(f"the refined crop is its source (change {m.change:.2f} < {SAME_MAX})")
    if said := identity_refusal(m):
        out.append(said)
    if m.drift is not None and m.drift > DRIFT_MAX:
        out.append(f"drift {m.drift:.1f} > {DRIFT_MAX}")
    if m.seam > SEAM_MAX:
        out.append(f"seam {m.seam:.1f} > {SEAM_MAX}")
    out += paste_refusals(m)
    if m.flick_ref > m.flick_src * FLICKER_RATIO + FLICKER_SLACK:
        out.append(f"flicker {m.flick_ref:.2f} > {m.flick_src:.2f} x {FLICKER_RATIO} + {FLICKER_SLACK}")
    if said := face_refusal(m.faces_src, m.faces_ref):
        out.append(said)
    return out


def decide(m: Measures) -> tuple[bool, str]:
    """(kept, why): kept only when no wall is broken; else the unrefined take."""
    said = refusals(m)
    return (not said, "; ".join(said) or "kept")
