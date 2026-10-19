"""G-FACE-FLOOR: a face the plan cares about is planned big enough for H3 to draw its eyes.

THE BRICK (docs/audit/2026-10-19_face_blur, PLAN section 1 and prevent_at_render section 1):
H3's VAE is 16x and its transformer groups 2x2 cells, so one token covers 32 px of a 768
take.  A face under FLOOR_PX (3 tokens) has an eye under half a VAE cell; the model paints
an average -- the mushy eye no upscaler restores, because it was never in the latent.  A
CUT to a closer size is the one plan-time lever (a push is no size control: framing_grammar).

THE PROJECTION (`FACE_PX`) is ep01's measurement, never a guess: per planned size, the
median of the smallest confident face of each delivered take (tests/fixtures/
ep01_face_heights.json, face_yolov8m on 3 frames a take).  Wide 28, full 67, medium 82:
all under the floor.  The owner's blurry takes T01/T06/T08 sit there.

THE CURE (`cure`) is free and deterministic: a wide or full shot whose face MATTERS (a
line in the voice of someone in it, or a reaction) steps ONE size closer, wide -> full ->
medium, with its frame's size word and its at_rest scale rewritten -- the drawer obeys the
at_rest's fraction, not the size word (picture_gates G-SIZE, ep10: 7 of 7) -- unless the
step breaks the staging or a grammar rule (`blocker`).  Establishing wides, inserts and
back views are never touched.  `advisories` lists every faced shot still under the floor:
each is a guaranteed face-refine candidate.  Advice only: it never refuses a plan and never
calls the writer (cap every loop).  $0, microseconds.
"""
from __future__ import annotations

import re

from studio.panel_dq import back_view
from studio.picture_gates import FRACTION

TAKE_PX = 768
"""The take's short edge the projection is measured on (H3 ref2va, 768x768)."""
FACE_PX = {"wide": 28, "full": 67, "medium": 82, "medium_close": 152, "close": 266, "extreme_close": 266}
"""Projected smallest face (px on a 768 take) per planned size: ep01's measured medians.
extreme_close has no ep01 take; it is held to the close's."""
FLOOR_PX = 96
"""Three tokens of face: the least on which H3 can draw an eye (prevent_at_render, A)."""
STEP = {"wide": "full", "full": "medium"}
"""One notch closer.  A medium two-shot is the grammar's reaction size (G-TWO), so the
ladder stops there; a medium under the floor is left to the face refine."""
LEAD = re.compile(r"^\s*(?:wide|full)(?:[- ]shot)?\b", re.I)
NEW_LEAD = {"full": "Full shot", "medium": "Medium shot"}
SCALE = {"full": "two thirds of the frame's height",
         "medium": "cut at the waist, the head a quarter of the frame's height"}
"""The new size's at_rest scale, in the words the good episodes wrote (picture_gates.HEAD_FRACTION;
ep01's full T06 'his figure ... two thirds of the frame's height' drew 79 px)."""
APPENDED = {"full": " The figures stand two thirds of the frame's height, head to boots.",
            "medium": " The figures are cut at the waist, each head a quarter of the frame's height."}
HEADISH = re.compile(r"\b(?:head|face|profile)s?\b", re.I)
PERSON = re.compile(r"\b(?:figures?|man|woman|men|women|boy|girl|child|he|she|his|her|their)\b", re.I)
BELOW_WAIST = re.compile(r"\b(?:boots?|feet|foot|legs?|knees?|shoes?|toes?|ankles?|heels?|kneel\w*|"
                         r"lies|lying|sprawl\w*|trampl\w*|head to (?:toe|boot|foot)\w*)\b(?!-)", re.I)
"""Staging a medium cuts out: the body under the waist, or a body on the ground.  Not a
costume compound ('knee-length coat', ep01 shot 6's far Hyde)."""


def projected_px(size: str) -> float | None:
    """The face height this size draws on a TAKE_PX take; None for a faceless size."""
    return FACE_PX.get(size)


def cut(doc: dict) -> list[dict]:
    omit = set(doc.get("omit") or [])
    return [s for s in doc["shots"] if s["index"] not in omit]


def prose(shot: dict) -> str:
    return " ".join(str(shot.get(k) or "") for k in ("frame", "camera", "at_rest"))


def faced(shot: dict) -> bool:
    """A shot that shows a face at all: faces planned, not an insert, not from behind."""
    return bool(shot.get("faces")) and shot.get("size") != "insert" and not back_view(prose(shot))


def own_voice(doc: dict, shot: dict) -> bool:
    """A line on this shot spoken (or told, or thought) by someone in it."""
    return any(l.get("shot") == shot["index"] and l.get("kind") != "narration"
               and l.get("speaker") in shot["faces"] for l in doc.get("lines") or [])


def face_matters(doc: dict, shot: dict) -> bool:
    """A speaking or reacting face: the shot the eye is read on."""
    return faced(shot) and (shot.get("section") == "reaction" or own_voice(doc, shot))


def establishing(doc: dict, shot: dict) -> bool:
    """A wide that sets a place: the cut's opener, its setup's first shot in the cut, or one
    carrying its setup's geometry (G-SCALE's 'establishing wide')."""
    if shot.get("size") != "wide":
        return False
    shots = cut(doc)
    first = next((s["index"] for s in shots if s["setup"] == shot["setup"]), None)
    geo = ((doc.get("setups") or {}).get(shot["setup"], {}).get("geometry") or "").strip()
    return shot["index"] in (shots[0]["index"], first) or bool(geo and geo in (shot.get("at_rest") or ""))


def verb_of(shot: dict) -> str:
    """The catalog verb of the shot's camera head (`locked` when it holds)."""
    from studio.episode_ref_official import camera_clause
    from studio.plan_gates import head_of, move_verb
    return move_verb(camera_clause(head_of(shot.get("motion") or ""))[0])


def orphans_crowd(doc: dict, shot: dict, new: str) -> bool:
    """Would this step leave its setup's crowd with no wide/full shot and no extras (G-CROWD-ORPHAN)?"""
    crowd = ((doc.get("setups") or {}).get(shot["setup"], {}).get("crowd") or "").strip()
    if not crowd or new in ("wide", "full") or shot.get("extras"):
        return False
    rest = [s for s in doc["shots"] if s["setup"] == shot["setup"] and s["index"] != shot["index"]]
    return not any(s.get("size") in ("wide", "full") or s.get("extras") for s in rest)


def blocker(doc: dict, shot: dict) -> str:
    """Why this shot may not step one size closer ('' when it may)."""
    from studio.move_rebalance import LEGAL
    from studio.plan_gates import CAP, amount, head_of
    new = STEP[shot["size"]]
    if shot.get("cuts"):
        return "its sub-shots carry their own sizes"
    if new == "medium" and BELOW_WAIST.search(f"{shot.get('frame', '')} {shot.get('at_rest', '')}"):
        return "the staging needs the body below the waist, which a medium cuts"
    if (verb := verb_of(shot)) not in LEGAL[new]:
        return f"its move ({verb}) is no {new}'s move"
    if (amount(head_of(shot.get("motion") or "")) or 0.0) > CAP[new]:
        return f"its camera travel is over a {new}'s move cap"
    if orphans_crowd(doc, shot, new):
        return "the setup's crowd would lose its last wide or full shot"
    return ""


def steppable(doc: dict, shot: dict) -> bool:
    """A wide or full whose face matters and which sets no place."""
    return shot.get("size") in STEP and face_matters(doc, shot) and not establishing(doc, shot)


def new_frame(frame: str, new: str) -> str:
    """The frame's leading size word made the new size's (no lead: the words stand)."""
    return LEAD.sub(NEW_LEAD[new], frame or "", count=1)


def new_at_rest(at_rest: str, new: str) -> str:
    """Every person-scale fraction made the new size's; with none, the scale appended."""
    text, hits = at_rest or "", 0
    for m in reversed(list(FRACTION.finditer(text))):
        clause = re.split(r"[.;:]", text[:m.start()])[-1]
        if HEADISH.search(clause) or not PERSON.search(clause):
            continue
        text, hits = text[:m.start()] + SCALE[new] + text[m.end():], hits + 1
    return text if hits else text.rstrip() + APPENDED[new]


def step(shot: dict) -> str:
    """Move the shot one size closer, in place; the moved row."""
    old, new = shot["size"], STEP[shot["size"]]
    shot.update(size=new, frame=new_frame(shot.get("frame"), new), at_rest=new_at_rest(shot.get("at_rest"), new))
    return (f"G-FACE-FLOOR shot {shot['index']}: moved {old} -> {new}, its face projected "
            f"{FACE_PX[old]} px -> {FACE_PX[new]} px on a {TAKE_PX} take, against the {FLOOR_PX} px floor")


def cure(doc: dict) -> tuple[dict, list[str]]:
    """One pass: every steppable shot the grammar lets step moves ONE notch.  (doc, moved rows)."""
    moved = [step(s) for s in cut(doc) if steppable(doc, s) and not blocker(doc, s)]
    return doc, moved


def refine_candidates(doc: dict) -> list[int]:
    """Every faced shot projected under the floor: the face refine's guaranteed takes."""
    return [s["index"] for s in cut(doc) if faced(s) and (projected_px(s["size"]) or 0) < FLOOR_PX]


def advisories(doc: dict) -> list[str]:
    """G-FACE-FLOOR, ADVISORY: each refine candidate, with why it was not moved."""
    from studio.plan_gates import fault
    by = {s["index"]: s for s in doc["shots"]}
    return [fault("G-FACE-FLOOR", f"shot {i}", f"a {by[i]['size']} with a face projects under the floor on a "
                  f"{TAKE_PX} px take ({why_left(doc, by[i])}) -- a face-refine candidate (advisory)",
                  FACE_PX[by[i]["size"]], FLOOR_PX) for i in refine_candidates(doc)]


def why_left(doc: dict, shot: dict) -> str:
    """Why the cure leaves this shot under the floor."""
    if shot["size"] not in STEP:
        return f"a {shot['size']} is the ladder's last step"
    if establishing(doc, shot):
        return "an establishing wide"
    if not face_matters(doc, shot):
        return "no line of its own and no reaction"
    return blocker(doc, shot) or f"the free cure steps it to {STEP[shot['size']]}"
