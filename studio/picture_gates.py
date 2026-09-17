"""The picture gates: free checks on plan.json for what the DRAWER and H3
measurably obey and ignore, calibrated on episode 10 and the judged fixtures.

Episode 10 (docs/analysis/ep10_dq_synthesis.md §C; the analyst reports in
the session scratchpad dq10/B, C, E, J) measured, plan word by plan word,
against the drawn cell and the rendered take:

  * SIZE: the size WORD lost to the at_rest span every time they disagreed.
    A head fraction phrase ("his head a third of the frame's height") sat in
    ep07's at_rests 20/26 and ep10's 0/34; ep07 drew MCU faces at 0.28-0.48
    and closes at 0.33-0.56, separated; ep10 drew MCUs at 0.20-0.59 over
    closes at 0.36-0.66.  Three MCUs written "from the TOP edge to the BOTTOM
    third" were drawn as closes (18, 27, 30).  G-SIZE is HARD.
  * SUN SPLIT: "LEFT half in sun, RIGHT half in shadow" on a sunlit face was
    drawn 0/6; the same split under a lamp 3/4; a practical with a place
    14/16.  What a sunlit face obeyed was an OBJECT's black ("the hat brim's
    black across his eyes").  G-SUNSPLIT is an advisory.
  * LIGHT SIDE: shots 16/17/18 said "sun from the right" from the threshold
    looking out, when the setup's sun is on the right only facing the porch;
    the drawer and H3 followed the setup and flipped it.  G-LIGHT-SIDE is an
    advisory with the shot numbers.
  * MOTION wording: a kept frame edge under a travel, a target noun in a head
    clause, a kept-clause holding a scale/blur/absence, a walk at the lens or
    by a figure in a wide -- the four shapes `episode_ref_official` L24-L27
    advise on in the built prompt, read here off the plan before anything is
    drawn.  G-MOTION is an advisory.

`faults(episode)` is the refusal; `advisories(episode)` is printed.  Nothing
here reads a picture, spends a credit or touches a GPU.
"""
from __future__ import annotations

import re

from studio import house_style as hs
from studio.episode_ref_official import (camera_clause, camera_parts, gaits, head_reposition,
                                         kept_edge, kept_scope, walk_advice)
from studio.episode_seq_board import HOLDS
from studio.episode_spec import Episode, Setup, Shot


def note(gate: str, where: str, why: str) -> str:
    return f"{gate} {where}: {why}"


# ---- G-SIZE: the head fraction is the size, not the span ------------------------

HEAD_FRACTION = {"close": ("half",), "medium_close": ("a third", "third"), "medium": ("a quarter", "quarter")}
"""The fraction of the frame's height a head takes at each size, in the words
ep05/07 wrote ("his head a third of the frame's height").  The sentence the
drawer obeys is the fraction; the size word in the panel head lost to the
at_rest span 7 times in 7 on ep10."""

FRACTION = re.compile(r"\b(?:half|(?:a |one |two |three |four )?(?:thirds?|quarters?|fifths?))"
                      r"(?: of)? the frame'?s? height\b", re.I)
"""Every form the good episodes wrote: "half the frame's height", "at half the
frame height", "a third of the frame's height", "at two thirds of the frame
height".  "the TOP half of the frame" is a region, not a head."""

FACE_FILLS = re.compile(r"\b(?:face|head|profile) fills\b", re.I)
"""A face that fills the frame IS a close's fraction: ep05's closes 1 and 16
carry no fraction phrase and looked right."""

HEAD_AS_CLOSE = re.compile(r"\bhead\b[^.]*\bTOP edge\b[^.]*\bBOTTOM third\b")
"""A head that runs from the TOP edge to the BOTTOM third is a close whatever
the size word says: ep10 shots 18, 27, 30 drew at face 0.51-0.59."""


def names_fraction(at_rest: str, size: str = "") -> bool:
    if FRACTION.search(at_rest or ""):
        return True
    return size == "close" and bool(FACE_FILLS.search(at_rest or ""))


def drawn_as_close(at_rest: str) -> bool:
    return bool(HEAD_AS_CLOSE.search(at_rest or ""))


def size_faults(episode: Episode) -> list[str]:
    out = []
    for s in episode.shots:
        if s.size not in ("close", "medium_close"):
            continue
        if not names_fraction(s.at_rest, s.size):
            out.append(note("G-SIZE", f"shot {s.index}",
                            f"a {s.size} whose at_rest names no head fraction; the size is "
                            f"'{HEAD_FRACTION[s.size][0]} the frame's height', not the span "
                            f"(ep07 20/26 at_rests, ep10 0/34), measured none against "
                            f"'{HEAD_FRACTION[s.size][0]}'"))
        if s.size == "medium_close" and drawn_as_close(s.at_rest):
            out.append(note("G-SIZE", f"shot {s.index}",
                            "a medium_close whose head runs from the TOP edge to the BOTTOM third: "
                            "that sentence is a close (ep10 shots 18, 27, 30 drew at face 0.51-0.59), "
                            "measured 'TOP edge to BOTTOM third' against 'a third'"))
    return out


# ---- G-SUNSPLIT: under a sun, the shadow gets an object -----------------------------

SPLIT = re.compile(
    r"\b(?:left|right) (?:half|side|cheek)\b[^.]*\b(?:sun|sunlit|lit|light|lamplight|warm)\b[^.]*"
    r"\b(?:right|left) (?:half|side|cheek)\b[^.]*\b(?:shadow|dark|black)\b"
    r"|\bone (?:cheek|side)\b[^.]*\bthe other\b[^.]*\b(?:shadow|dark|black)\b"
    r"|\b(?:left|right) side of (?:his|her|the) face in (?:shadow|darkness)\b"
    r"|\bsplits? (?:his|her|the) face into\b", re.I)
"""The plan's phrasings of a face split into a lit half and a dark half."""

CASTER = re.compile(r"\b(?:brim|post|jamb|lintel|hat|shutter|beam|rail)'?s? (?:black|shadow)\b", re.I)
"""A named shadow-caster: the one thing a sunlit face obeyed (Q18's hat brim,
Q20's porch post)."""


def splits_a_face(text: str) -> str:
    hit = SPLIT.search(text or "")
    return hit.group(0) if hit else ""


def names_caster(text: str) -> bool:
    return bool(CASTER.search(text or ""))


def under_a_sun(setup: Setup) -> bool:
    """The setup's own light clause names no practical: a sky source alone."""
    clause = hs.lit_clause(setup.described)
    return bool(clause) and not hs.PRACTICALS.search(clause)


def split_advisories(episode: Episode) -> list[str]:
    out = []
    for s in episode.shots:
        if not under_a_sun(episode.setups[s.setup]):
            continue
        text = " ".join((s.at_rest, s.frame, s.camera))
        if (hit := splits_a_face(text)) and not names_caster(text):
            out.append(note("G-SUNSPLIT", f"shot {s.index}",
                            f"{hit!r} splits a face under a sun -- drawn 0/6 on ep10; name the "
                            f"shadow-caster at a frame edge instead ('the hat brim's black across his eyes')"))
    return out


# ---- G-LIGHT-SIDE: the light clause names a frame side, flipped facing away ---------

FRAME_SIDE = re.compile(r"(?<!his )(?<!her )(?<!their )\b(left|right)\b(?!-hand)"
                        r"(?! (?:of|side|cheek|half|shoulder|arm|hand|eye|knee|wall))", re.I)
"""A FRAME side: "from the right", "at the left".  A body side ("his right
cheek", "the right side of his face", "the right-hand wall") is not one --
shot 16 said both in one sentence and the right cheek is frame-left."""

AWAY_CAMERA = re.compile(r"\b(?:on|at) the (?:porch|threshold|step)\b|\bfrom the porch looking down\b"
                         r"|\bahead of (?:him|her|them)\b|\bfacing away\b|\bback to the\b"
                         r"|\blooking (?:down|back|out)\b", re.I)
AWAY_FRAME = re.compile(r"\bfacing (?:away|into the room)\b|\bturned back on the\b|\bgoing away\b"
                        r"|\bback to the (?:door|porch|window|gate)\b", re.I)
"""The heuristic for a shot that faces AWAY from the setup's own view: the
CAMERA stands on the landmark's ground (the porch, the threshold) or ahead of
a figure coming toward it, or the FRAME says the subject has turned back or
is going away.  ep10: 16, 17, 18, 19, 20 on the doorway; 4, 5 on the path.
The camera's markers are read on `camera` alone: "Medium at the porch step"
is where the SUBJECT stands (shot 6, camera on the path facing it), and "two
long strides from the step" is a distance, not a position."""

SELF_PLACED = re.compile(r"\bbehind the camera\b|\bfrom above\b|\bis the light\b|\boverhead\b", re.I)
"""A light with its place stated and no side to state: not an omission."""


def light_clause(camera: str) -> str:
    return camera_parts(camera)[1]


def frame_side(text: str) -> str:
    hit = FRAME_SIDE.search(text or "")
    return hit.group(1).lower() if hit else ""


def setup_side(setup: Setup) -> str:
    return frame_side(hs.lit_clause(setup.described))


def faces_away(shot: Shot) -> bool:
    return bool(AWAY_CAMERA.search(shot.camera) or AWAY_FRAME.search(shot.frame))


def flipped(side: str) -> str:
    return {"left": "right", "right": "left"}[side]


def side_advice(shot: Shot, setup: Setup) -> str:
    """Why this shot's light clause is on the wrong side, or nothing."""
    clause = light_clause(shot.camera)
    if not clause:
        return ""
    side = frame_side(clause)
    if not side:
        if shot.faces and shot.size in ("close", "medium_close") and not SELF_PLACED.search(clause):
            return f"{clause!r} lights a face and names no frame side (left/right); the drawer obeys the side it is given"
        return ""
    want = setup_side(setup)
    if want and faces_away(shot) and side != flipped(want):
        return (f"{clause!r} names the {side}; the shot faces away from {setup.landmark or 'the landmark'} "
                f"and the setup's light is on the {want} facing it, so the frame side is the {flipped(want)}")
    return ""


def light_side_advisories(episode: Episode) -> list[str]:
    return [note("G-LIGHT-SIDE", f"shot {s.index}", why)
            for s in episode.shots if (why := side_advice(s, episode.setups[s.setup]))]


# ---- G-MOTION: the wording H3 ignores, read off the plan --------------------------------

def travels(motion: str) -> bool:
    cam, _ = camera_clause((motion or "").split(";")[0])
    return bool(cam) and not HOLDS.search(cam)


def motion_advice(shot: Shot) -> list[str]:
    body = shot.motion
    out = []
    if hit := kept_edge(body, travels(body)):
        out.append(f"KEPT EDGE {hit!r} under a camera travel -- a push removes the edge, a "
                   f"pull-back moves it inward; keep a thing in the MIDDLE of the frame, or hold")
    if hit := head_reposition(body):
        out.append(f"REPOSITION {hit!r} names the thing looked at; obeyed as a whole-body turn 3/3 "
                   f"-- say what the face keeps ('his eyes stay on the lens')")
    if hit := kept_scope(body):
        out.append(f"KEPT SCOPE {hit!r} -- a kept-clause holds a sharp static edge object, not a "
                   f"scale, a blur or an absence")
    if why := walk_advice(body, shot.size == "wide"):
        out.append(f"WALK {why}")
    return out


def motion_advisories(episode: Episode) -> list[str]:
    return [note("G-MOTION", f"shot {s.index}", why) for s in episode.shots for why in motion_advice(s)]


# ---- the verdict ----------------------------------------------------------------------

def faults(episode: Episode) -> list[str]:
    """Every picture reason this plan should not be drawn: G-SIZE."""
    return size_faults(episode)


def advisories(episode: Episode) -> list[str]:
    """Printed beside the plan, never counted: the sun split, the light side,
    the motion wording."""
    return split_advisories(episode) + light_side_advisories(episode) + motion_advisories(episode)
