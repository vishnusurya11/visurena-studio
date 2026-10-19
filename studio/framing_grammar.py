"""The anime-TV framing grammar: plan gates on shot size, length and camera.

OWNER 2026-10-17, after the part-2 framing tests (docs/audit/2026-10-16_model_tests,
research 05_camera_framing.md): "I like the face improvements a lot in wide
shots, and reframe. Go ahead with changes."  The brick (05 section 7): the frame
holds a face large enough to read, and a CUT is the only thing that changes size
-- H3 obeys a move's direction and ignores its amount, so a push is no size control;
a cut to a panel drawn at the new size is.

Every gate reads plan fields only, and every length the VOICE (`plan_gates.
projected_place`: the measured seconds where a line is recorded, the series rate
where not -- one ruler for the checker and every cure).  Faults print in the
battery's one format: `G-<GATE> <where>: <why>, measured <got> against <wall>`.
Hard on a plan that declares `grammar: anime_tv` and is not yet drawn; advice on
every older plan (`plan_check.grammar_gate`).  $0, no picture read.
"""
from __future__ import annotations

import re

from studio import face_floor
from studio.plan_gates import OVER_SHOULDER, fault, head_of, move_verb

FACE_SIZES = ("extreme_close", "close", "medium_close")
"""Planned sizes whose face is a quarter of the frame or more (G-SIZE asks a close
for half, a medium close for a third)."""
FACE_SHARE = 0.55
"""Shots carrying a face at a FACE_SIZE, as a share of the cut (05 section 2.2).
ep01 today: 6 of 23 (0.26) -- every other face 3.5-15 % of the frame."""
MAX_WIDES = 2
"""Wides an episode holds: the opener and one more (05 section 2.2)."""
WIDE_S, OPENER_WIDE_S = 4.0, 5.0
"""A wide's seconds; the opening wide's.  D1/D6: a wide's men read 3.6-4.8 % of the
frame however it is framed, so a wide sets the world and cuts closer."""
MEDIUM_S = 7.0
"""A medium's seconds: past it the line splits across a reverse or an insert."""
FULL_S = 5.0
"""A full shot's seconds -- ADVISORY (05 section 2.3; the owner set no number)."""
INSERT_S = (1.0, 3.0)
"""An impact insert's seconds (D2: the boots insert read as anime at 10.1 s only
because the voice held it; long lines split across insert plus reaction)."""
MAX_PUSHES = 2
"""Pushes an episode (05 section 2.6; ep01 pushed on 6 shots, D4 pushed on its own)."""
LOCKED_SHARE = 0.5
"""The locked-off share of the cut: 'mostly locked' (05: 60 %, the actor or the
air carries the verb -- ep02 T01/T05/T14/T22 held, and a bare hold froze 81 %)."""
TWO_SHOT_SIZE = "medium"
"""A two-person reaction (D3)."""
PAYOFF_SIZE = "close"
"""The payoff line (D5)."""
OTS_TIGHTEST = "medium_close"
"""An over-the-shoulder shot is never tighter (D4: 2/2 seeds opened wide and pushed)."""

UNSUPPORTED = re.compile(r"\bsilhouett\w*|\bblack shapes? against\b|\bdutch\b|\bcanted\b"
                         r"|\btilted (?:horizon|frame)\b|\bslanting horizon\b", re.I)
"""A shot asked of H3 or the grid in WORDS that both ignore (D1, D6, D7: 0 of 4).  Not
'at a slant': the replay's one hit was a table surface (Scarlet ep01 shot 17)."""
EYES = re.compile(r"\beyes?\b", re.I)
SHOT_TEXT = ("frame", "motion", "camera", "at_rest", "end")


def band() -> dict:
    """Every number these gates measure, for the writer's brief (walls follow the
    brief: a number the writer is not told costs a ladder rung)."""
    return {"face_share": FACE_SHARE, "face_sizes": list(FACE_SIZES), "max_wides": MAX_WIDES,
            "wide_seconds": WIDE_S, "opener_wide_seconds": OPENER_WIDE_S, "medium_seconds": MEDIUM_S,
            "insert_seconds": list(INSERT_S), "max_pushes": MAX_PUSHES, "locked_share": LOCKED_SHARE,
            "two_shot_size": TWO_SHOT_SIZE, "payoff_size": PAYOFF_SIZE, "ots_tightest": OTS_TIGHTEST,
            "unsupported": ["silhouette", "Dutch / canted angle", "eye close-up"],
            "face_floor_px": face_floor.FLOOR_PX, "face_px_by_size": dict(face_floor.FACE_PX)}


def cut(episode) -> list:
    """The shots in the cut (an Episode, or anything with `.shots`)."""
    omit = set(getattr(episode, "omit", None) or [])
    return [s for s in episode.shots if s.index not in omit]


def verb(shot) -> str:
    """The catalog verb of the shot's camera head (`locked` when it holds)."""
    from studio.episode_ref_official import camera_clause
    return move_verb(camera_clause(head_of(shot.motion))[0])


def face_shot(shot) -> bool:
    return shot.size in FACE_SIZES and bool(shot.faces)


def face_faults(episode) -> list[str]:
    """G-FACES: at least FACE_SHARE of the cut holds a face at close or medium close."""
    shots = cut(episode)
    got = round(sum(face_shot(s) for s in shots) / len(shots), 2) if shots else 0.0
    if got >= FACE_SHARE:
        return []
    return [fault("G-FACES", "plan", "share of the shots with a face at close or medium_close", got, FACE_SHARE)]


def wide_faults(episode, secs: dict[int, float]) -> list[str]:
    """G-WIDE: at most MAX_WIDES wides, each WIDE_S long (the opener OPENER_WIDE_S)."""
    shots = cut(episode)
    wides = [s for s in shots if s.size == "wide"]
    out = [fault("G-WIDE", "plan", "wide shots in the cut", len(wides), MAX_WIDES)] if len(wides) > MAX_WIDES else []
    for s in wides:
        wall = OPENER_WIDE_S if shots and s.index == shots[0].index else WIDE_S
        if secs.get(s.index, 0.0) > wall + 1e-6:
            out.append(fault("G-WIDE", f"shot {s.index}", "a wide's seconds -- cut closer, or split its line",
                             round(secs[s.index], 2), wall))
    return out


def medium_faults(episode, secs: dict[int, float]) -> list[str]:
    """G-MEDIUM: a medium holds at most MEDIUM_S; past it the line splits."""
    return [fault("G-MEDIUM", f"shot {s.index}", "a medium's seconds -- split the line across a reverse "
                  "or an insert", round(secs[s.index], 2), MEDIUM_S)
            for s in cut(episode) if s.size == "medium" and secs.get(s.index, 0.0) > MEDIUM_S + 1e-6]


def full_advisories(episode, secs: dict[int, float]) -> list[str]:
    """A full shot past FULL_S (advisory)."""
    return [fault("G-FULL", f"shot {s.index}", "a full shot's seconds (advisory)", round(secs[s.index], 2), FULL_S)
            for s in cut(episode) if s.size == "full" and secs.get(s.index, 0.0) > FULL_S + 1e-6]


def insert_faults(episode, secs: dict[int, float]) -> list[str]:
    """G-INSERT: an insert is an impact of INSERT_S seconds."""
    low, high = INSERT_S
    return [fault("G-INSERT", f"shot {s.index}", "an insert's seconds -- an impact holds one to three; "
                  "a long line splits across the insert and a reaction", round(secs[s.index], 2), f"{low}-{high}")
            for s in cut(episode) if s.size == "insert" and not low - 1e-6 <= secs.get(s.index, 0.0) <= high + 1e-6]


def push_faults(episode) -> list[str]:
    """G-PUSH: past MAX_PUSHES, every further push is named."""
    pushes = [s.index for s in cut(episode) if verb(s) == "push_slow"]
    return [fault("G-PUSH", f"shot {i}", "a push past the episode's two -- hold it locked and let the actor "
                  "carry the beat", len(pushes), MAX_PUSHES) for i in pushes[MAX_PUSHES:]]


def amount_faults(episode) -> list[str]:
    """G-PUSH: a camera head names an amount H3 ignores (0 of 16 governed)."""
    from studio.episode_ref_official import AMOUNT
    return [fault("G-PUSH", f"shot {s.index}", f"the camera head names an amount ({hit.group(0)!r}) the "
                  "model ignores; name the direction only", hit.group(0), "no amount")
            for s in cut(episode) if (hit := AMOUNT.search(head_of(s.motion)))]


def locked_faults(episode) -> list[str]:
    """G-LOCKED: the camera is mostly locked off."""
    shots = cut(episode)
    got = round(sum(verb(s) == "locked" for s in shots) / len(shots), 2) if shots else 0.0
    if got >= LOCKED_SHARE:
        return []
    return [fault("G-LOCKED", "plan", "locked-off share of the shots", got, LOCKED_SHARE)]


def over_shoulder(shot) -> bool:
    return bool(OVER_SHOULDER.search(f"{shot.frame} {getattr(shot, 'camera', '')} {head_of(shot.motion)}"))


def ots_faults(episode) -> list[str]:
    """G-OTS: an over-the-shoulder shot tighter than OTS_TIGHTEST."""
    return [fault("G-OTS", f"shot {s.index}", "an over-the-shoulder shot tighter than a medium close "
                  "(the model opens wider and pushes)", s.size, OTS_TIGHTEST)
            for s in cut(episode) if over_shoulder(s) and s.size in ("close", "extreme_close")]


def two_shot_faults(episode) -> list[str]:
    """G-TWO: a reaction holding two or more faces is a locked medium two-shot."""
    return [fault("G-TWO", f"shot {s.index}", "a two-person reaction is a locked medium two-shot",
                  f"{s.size}/{verb(s)}", f"{TWO_SHOT_SIZE}/locked")
            for s in cut(episode) if s.section == "reaction" and len(s.faces) >= 2
            and (s.size != TWO_SHOT_SIZE or verb(s) != "locked")]


def payoff_faults(episode) -> list[str]:
    """G-PAYOFF: a payoff shot carrying a dialogue line is a locked close."""
    spoken = {l.shot for l in episode.lines if l.kind == "dialogue"}
    return [fault("G-PAYOFF", f"shot {s.index}", "the payoff line is a locked close",
                  f"{s.size}/{verb(s)}", f"{PAYOFF_SIZE}/locked")
            for s in cut(episode) if s.section == "payoff" and s.index in spoken
            and (s.size != PAYOFF_SIZE or verb(s) != "locked")]


def unsupported_hit(seg) -> str:
    """The unsupported shot this segment asks for in words, or ''."""
    said = " ".join(str(getattr(seg, k, "") or "") for k in SHOT_TEXT)
    if hit := UNSUPPORTED.search(said):
        return hit.group(0)
    if getattr(seg, "size", "") == "extreme_close" and (seg.faces or EYES.search(said)):
        return "an eye close-up"
    return ""


def unsupported_faults(episode) -> list[str]:
    """G-UNSUPPORTED: a silhouette, a Dutch angle or an eye close-up asked in words."""
    return [fault("G-UNSUPPORTED", f"shot {s.index}", "asked in words, which the grid and the model ignore; "
                  "unsupported until a panel route draws it", hit, "a panel route")
            for s in cut(episode) for seg in [s] + list(getattr(s, "cuts", None) or [])
            if (hit := unsupported_hit(seg))]
