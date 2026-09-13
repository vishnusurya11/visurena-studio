"""G4.7 -- are the faces on screen the cast the plan put there, and do they stay
the same person from a segment's first frame to its last?

Two halves.  The JUDGE (everything above `observe`) is pure arithmetic over face
observations and is always available.  The MEASURER needs a face model
(facenet-pytorch: MTCNN boxes + a VGGFace2 embedding), which is NOT in this
venv, so it sits behind a feature flag: `enabled()` is False, `identity_dq`
returns "not measured", and no take fails on an identity the gate never read.

To turn it on:  uv add torchvision==0.29.0
                uv pip install --no-deps facenet-pytorch==2.6.0
                uv sync --all-groups      (uv add strips the music/voice groups)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SWITCH = "VISURENA_IDENTITY_GATE"
"""Set to `off` to silence a working backend; anything else leaves it to the import."""

READABLE = 0.12
"""CALIBRATION: face box height / frame height.  review8/identity.md -- faces at
8-10 % of frame height score 0.46-0.72 against their own sheet and are not
judgeable; at 12 % and above the score separates the right man from a stranger."""
FRONTAL = 0.50
"""CALIBRATION: nose offset from the eye midpoint in eye-distances.  Profiles
score 0.51-0.69 against their own sheet (iteration 3 T09 frame 3 at yaw 0.92)."""
MATCH = 0.60
"""CALIBRATION: cosine to the character's cast sheet.  The right man measured
0.61-0.94 (0.72-0.94 when his sheet was among the take's refs)."""
STRANGER = 0.45
"""CALIBRATION: best cosine below this is nobody from the cast -- the four real
strangers on disk measured 0.43, 0.21, 0.03 and -0.04."""
DRIFT = 0.75
"""CALIBRATION: cosine between the first and last readable frame of one character
WITHIN one pinned segment.  Real pairs measured >= 0.81; the one true identity
slip (iteration 3 T09) measured 0.72."""


@dataclass
class Face:
    """One observed face: where it sat, how big, and how it scored against the cast."""
    k: int                      # sample index within the take (0 = first frame)
    h: float                    # box height as a fraction of frame height
    scores: dict[str, float]    # cosine to each cast member's sheet(s)
    vec: np.ndarray | None = None
    yaw: float = 0.0            # nose offset from the eye midpoint, in eye-distances
    seg: int = 0                # the pinned segment the frame belongs to

    @property
    def best(self) -> str:
        return max(self.scores, key=self.scores.get)

    @property
    def cos(self) -> float:
        return self.scores[self.best]


@dataclass
class Verdict:
    present: dict[str, int] = field(default_factory=dict)   # who was seen, in how many frames
    flags: list[str] = field(default_factory=list)
    hard: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.hard


def readable(faces: list[Face]) -> list[Face]:
    """Faces a viewer can read identity from: big enough and not a profile."""
    return [f for f in faces if f.h >= READABLE and f.yaw <= FRONTAL]


def identify(face: Face) -> str | None:
    """The cast member this face is, or None when it is nobody from the cast."""
    if face.cos < STRANGER:
        return None
    return face.best


def strangers(faces: list[Face]) -> list[Face]:
    """Readable faces that match nobody in the cast."""
    return [f for f in readable(faces) if identify(f) is None]


def weak(faces: list[Face]) -> list[Face]:
    """Identified, but below MATCH: advisory, look at the frame."""
    return [f for f in readable(faces) if identify(f) is not None and f.cos < MATCH]


def unreferenced(faces: list[Face], refs: list[str]) -> list[str]:
    """Cast members on screen whose cast sheet was NOT among the take's refs."""
    seen = {identify(f) for f in readable(faces)} - {None}
    return sorted(who for who in seen if not any(who in r for r in refs))


def uncast(faces: list[Face], expected: list[str]) -> list[str]:
    """Cast members on screen the plan did not put in this take."""
    seen = {identify(f) for f in readable(faces)} - {None}
    return sorted(seen - set(expected))


def drift(faces: list[Face]) -> dict[str, float]:
    """Per character: the lowest cosine between the first and last frame he is
    readable in within one segment (across a cut the framing changes by design)."""
    out: dict[str, float] = {}
    for who in {identify(f) for f in readable(faces)} - {None}:
        for seg in sorted({f.seg for f in faces}):
            run = [f for f in readable(faces) if identify(f) == who and f.seg == seg and f.vec is not None]
            if len(run) >= 2 and run[0].k != run[-1].k:
                c = round(float(run[0].vec @ run[-1].vec), 3)
                out[who] = min(out.get(who, 1.0), c)
    return out


def judge(faces: list[Face], expected: list[str], refs: list[str]) -> Verdict:
    """STRANGER and DRIFT are hard; WEAK, UNCAST and UNREFERENCED are advisory."""
    v = Verdict()
    for f in readable(faces):
        who = identify(f)
        if who:
            v.present[who] = v.present.get(who, 0) + 1
    for f in strangers(faces):
        v.hard.append(f"STRANGER frame {f.k}: best {f.best} {f.cos:.2f} < {STRANGER}")
    for f in weak(faces):
        v.flags.append(f"WEAK frame {f.k}: {f.best} {f.cos:.2f} < {MATCH}")
    for who in uncast(faces, expected):
        v.flags.append(f"UNCAST {who}: on screen, not in the plan's faces")
    for who in unreferenced(faces, refs):
        v.flags.append(f"UNREFERENCED {who}: on screen, cast sheet not in refs")
    for who, c in drift(faces).items():
        if c < DRIFT:
            v.hard.append(f"DRIFT {who}: first vs last frame {c:.2f} < {DRIFT}")
    v.flags = v.hard + v.flags
    return v


# ---- the measurer, behind the flag -------------------------------------------

def _backend():
    """The face model, or None when the library is not installed."""
    try:
        from facenet_pytorch import MTCNN, InceptionResnetV1
    except Exception:
        return None
    return (MTCNN, InceptionResnetV1)


def enabled() -> bool:
    """True only when the face model imports AND the switch is not `off`."""
    return os.environ.get(SWITCH, "").lower() != "off" and _backend() is not None


def observe(video, segments: list, sheets: dict, samples: int = 8) -> list[Face]:
    """Sampled faces of one take, scored against the cast sheets.  Needs the backend."""
    raise NotImplementedError("identity measuring needs facenet-pytorch; see this module's docstring")


NOT_MEASURED = {"measured": False, "ok": True, "note": "not measured: face model not installed",
                "flags": [], "hard": [], "present": {}}


def identity_dq(video, segments: list, expected: list[str], refs: list[str],
                sheets: dict | None = None) -> dict:
    """The take's identity report, or the honest 'not measured' when the flag is off."""
    if not enabled():
        return dict(NOT_MEASURED)
    v = judge(observe(video, segments, sheets or {}), expected, refs)
    return {"measured": True, "ok": v.ok, "note": "", "flags": v.flags, "hard": v.hard, "present": v.present}


def sheet_paths(book: Path, cast: list[str]) -> dict[str, Path]:
    """Where each character's cast sheet lives, for the measurer to embed."""
    return {who: book / "refs" / "characters" / f"char-{who}.png" for who in cast}
