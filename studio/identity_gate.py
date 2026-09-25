"""G4.7 -- are the faces on screen the cast the plan put there, and do they stay
the same person from a segment's first frame to its last?

Two halves.  The JUDGE (everything above `observe`) is pure arithmetic over face
observations and is always available.  The MEASURER is `studio/measure/faces.py`
(facenet-pytorch: MTCNN boxes + five landmarks, a VGGFace2 embedding), in the
`measures` dependency group; `observe` samples the take, embeds every face and
scores it against the cast bank.  `enabled()` still asks three things -- the
backend imports, the switch is not `off`, and there is a measurer to run -- and
`identity_dq` answers "not measured" when any is missing, so no take fails on
an identity the gate never read.  `detect=` and `embed=` are injectable, so a
test measures from recorded vectors and never loads the model.

RECALIBRATED on episode 10 (docs/calibration/identity.md, dq10/A): the gate
as first calibrated on ep01 would have hard-failed four GOOD ep10 takes on
drift (T06 0.60, T21 0.69, T29 0.43, T33 0.67 -- all the same person, all
pose) and caught no swap, because there was none.  READABLE, FRONTAL and the
drift statistic moved.  ARMED since the judges replaced the eye
(architecture/decisions/2026-09-24_judges_replace_the_eye.md §1.1): a
STRANGER or DRIFT finding is hard, and the take ladder climbs on it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SWITCH = "VISURENA_IDENTITY_GATE"
"""Set to `off` to silence a working backend; anything else leaves it to the import."""

ARMED = True
"""True: a STRANGER or DRIFT finding is hard.  It was False for one episode
after the last recalibration (four same-person takes read in a bad pose had
hard-failed on the first walls); the recalibrated walls were clean on that
episode, and the judges decision (2026-09-24) puts identity on the take
ladder, where a finding must refuse the rung, not print an advisory nobody
reads."""

READABLE = 0.15
"""CALIBRATION: face box height / frame height.  docs/calibration/identity.md -- faces at
8-10 % of frame height score 0.46-0.72 against their own sheet and are not
judgeable.  Was 0.12; ep10 T06's faces at 0.12-0.13 are the only frontal
faces that score under MATCH (0.56-0.60) for the right man, so the floor
moved to 0.15."""
FRONTAL = 0.35
"""CALIBRATION: nose offset from the eye midpoint in eye-distances.  Profiles
score 0.51-0.69 against their own sheet (iteration 3 T09 frame 3 at yaw 0.92).
Was 0.50; ep10 T29 f5 (yaw 0.44) and T33 f4 (0.43) are full profiles by eye
and dragged the first-vs-last pair to 0.43 and 0.67 for the same man."""
MATCH = 0.60
"""CALIBRATION: cosine to the character's cast sheet.  The right man measured
0.61-0.94 (0.72-0.94 when his sheet was among the take's refs)."""
STRANGER = 0.45
"""CALIBRATION: best cosine below this is nobody from the cast -- the four real
strangers on disk measured 0.43, 0.21, 0.03 and -0.04."""
DRIFT = 0.75
"""CALIBRATION: the cosine that says one character stayed one man WITHIN one
pinned segment.  With three or more readable frames it is the minimum cosine
of each frame to the run's MEDIAN embedding: ep10 same-person minimum 0.82-0.98
in every take (T06 0.84, T21 Lucy 0.88, T33 0.82).  With two frames it is the
pair itself: ep01 real pairs measured >= 0.81 and the one true slip (iteration
3 T09, two frames) 0.72.  The pair is the statistic most sensitive to pose --
ep10's same-person pairs read 0.60-0.69 whenever the head was pitched or
turned -- which is why it is used only when there is nothing else."""


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


def median_embedding(vecs: list[np.ndarray]) -> np.ndarray:
    """The coordinate-wise median of unit vectors, renormalised: the run's centre,
    which one bad pose cannot drag."""
    m = np.median(np.stack(vecs), axis=0)
    return m / (np.linalg.norm(m) or 1.0)


def run_drift(run: list[Face]) -> float | None:
    """One character's readable run in one segment: the minimum cosine to the
    run's median (n >= 3), the pair itself (n = 2), nothing (n < 2)."""
    if len(run) >= 3:
        m = median_embedding([f.vec for f in run])
        return round(min(float(f.vec @ m) for f in run), 3)
    if len(run) == 2 and run[0].k != run[-1].k:
        return round(float(run[0].vec @ run[-1].vec), 3)
    return None


def drift(faces: list[Face]) -> dict[str, float]:
    """Per character: the lowest run_drift over the segments he is readable in
    (across a cut the framing changes by design)."""
    out: dict[str, float] = {}
    for who in {identify(f) for f in readable(faces)} - {None}:
        for seg in sorted({f.seg for f in faces}):
            run = [f for f in readable(faces) if identify(f) == who and f.seg == seg and f.vec is not None]
            c = run_drift(run)
            if c is not None:
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


def _measurer_exists() -> bool:
    """Is there anything to run, or is `observe` still the placeholder?

    Asked by calling it, not by reading a flag somebody has to remember to
    change: when `observe` is written, this answers True by itself."""
    try:
        observe(None, [], {})
    except NotImplementedError:
        return False
    except Exception:
        pass
    return True


def enabled() -> bool:
    """True only when the face model imports, the switch is not `off`, AND there
    is a measurer to run.

    THE THIRD CLAUSE IS NOT DECORATION.  `observe` raises NotImplementedError,
    and `enabled` used to go True the moment `facenet_pytorch` imported -- so
    the documented install, on its own, turned every `take_dq` run from a quiet
    "identity: not measured" into a crash, on every take of every episode.
    Nothing would have caught it first: `tests/test_identity_gate.py` monkeypatches
    `observe` away, so all sixteen of its tests stay green over a gate that
    cannot run.

    It is self-retiring.  Write `observe` and this clause stops holding the gate
    shut, with no edit here."""
    return (os.environ.get(SWITCH, "").lower() != "off"
            and _backend() is not None
            and _measurer_exists())


def _frames(video, samples: int) -> list:
    """The frames to read: none for nothing, the list given, or `samples` off the file."""
    if video is None:
        return []
    if isinstance(video, (list, tuple)):
        return list(video)
    from studio.measure import faces
    return faces.sample_frames(Path(video), samples)


def observe(video, segments: list, sheets: dict, samples: int = 8,
            detect=None, embed=None, bank: dict | None = None) -> list[Face]:
    """Sampled faces of one take, scored against the cast sheets.

    `video` is a path or a list of RGB frames; `detect` / `embed` default to
    facenet through `measure.faces.embedder()` and are built only when there
    is a frame to read; `bank` may be handed in ready (vectors per character)
    instead of being embedded from `sheets`."""
    from studio.measure import faces
    frames = _frames(video, samples)
    if not frames:
        return []
    if detect is None or embed is None:
        detect, embed = faces.embedder()
    if bank is None:
        bank = faces.bank_of(sheets or {}, detect, embed)
    return faces.observe(frames, segments, bank, detect, embed)


def sample_starts(starts_s: list[float], seconds: float, samples: int = 8) -> list[int]:
    """Each segment's start as the index of the first sample read at or after it.
    ep12 T02: SegmentReports went in where sample indices belong (TypeError)."""
    from studio.measure import faces
    shares = faces.sample_shares(samples)
    out = []
    for s in starts_s:
        share = s / seconds if seconds else 0.0
        out.append(next((k for k, at in enumerate(shares) if at >= share), len(shares) - 1))
    return out


NOT_MEASURED = {"measured": False, "ok": True, "note": "not measured: face model not installed",
                "flags": [], "hard": [], "present": {}}


def identity_dq(video, segments: list, expected: list[str], refs: list[str],
                sheets: dict | None = None, **measure) -> dict:
    """The take's identity report, or the honest 'not measured' when the flag is
    off.  `measure` (detect=, embed=, bank=) reaches `observe` untouched.
    Armed, a hard finding fails the take; disarmed it rides in `flags` and `note`."""
    if not enabled():
        return dict(NOT_MEASURED)
    v = judge(observe(video, segments, sheets or {}, **measure), expected, refs)
    hard = v.hard if ARMED else []
    note = "" if ARMED or not v.hard else "advisory for one episode: " + "; ".join(v.hard)
    return {"measured": True, "ok": not hard, "note": note, "flags": v.flags, "hard": hard, "present": v.present}


def sheet_paths(book: Path, cast: list[str]) -> dict[str, Path]:
    """Where each character's cast sheet lives, for the measurer to embed."""
    return {who: book / "refs" / "characters" / f"char-{who}.png" for who in cast}
