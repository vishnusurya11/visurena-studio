"""LOOK-STATE -- does a drawn look picture show its look? (step 03, decision 2026-10-10)

List-then-judge, the house rule: the local VLM LISTS the figure's headwear,
hair colour, facial hair, top garment and dirt in a closed vocabulary; code
compares them with the look's markers.  The VLM never decides pass or fail.

    headwear, hair_colour, facial_hair   HARD  -- the three that lost to the staged sheet in WotW
    top, dirt                            advisory (a VLM reads dusty vs sooted badly at sheet scale)
    identity                             advisory until the bench fits it: facenet
                                         m = cos(look, base) - max cos(look, other cast sheet) <= 0

A look whose face changes (beard, grey) is judged on identity RELATIVELY: an
absolute wall was measured at 0.45-0.82 between strangers on this style.
Every reader is injectable; a judge built without one in a test trips the trap.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from studio import look_table as lt, panel_content as pc
from studio.continuity_spec import HARD_MARKERS, Markers
from studio.judges.verdict import Fault, Verdict

NAME, VERSION = "look_state", "1"
VOCAB = {"headwear": [v for v in Markers.model_fields["headwear"].annotation.__args__ if v],
         "hair_colour": [v for v in Markers.model_fields["hair_colour"].annotation.__args__ if v],
         "facial_hair": [v for v in Markers.model_fields["facial_hair"].annotation.__args__ if v],
         "top": [v for v in Markers.model_fields["top"].annotation.__args__ if v],
         "dirt": [v for v in Markers.model_fields["dirt"].annotation.__args__ if v]}
ASK = ("This is a character picture of ONE person. Answer each question with ONE of the allowed "
       "answers and nothing else. Output strict JSON with these keys.\n"
       + "\n".join(f'"{k}": one of {", ".join(v)}.' for k, v in VOCAB.items()))


def parse(said: str) -> dict[str, str]:
    """The reader's answer as markers; Unreadable when it holds no answer at all."""
    got = pc._loads(said or "")
    if not isinstance(got, dict):
        raise pc.Unreadable("the look-state read is not an object")
    out = {k: str(got.get(k, "")).lower().strip() for k in VOCAB}
    out = {k: (v if v in VOCAB[k] else "") for k, v in out.items()}
    if not any(out.values()):
        raise pc.Unreadable("the look-state read names no marker")
    return out


def marker_faults(seen: dict[str, str], want: Markers, where: str) -> list[Fault]:
    """One fault per stated marker the picture does not show; HARD on the head."""
    out = []
    for key, wanted in want.model_dump().items():
        got = seen.get(key, "")
        if wanted and got and lt.family(key, got) != lt.family(key, wanted):
            out.append(Fault(kind=f"look_{key}", where=where, evidence={"want": wanted, "seen": got},
                             severity="high" if key in HARD_MARKERS else "advisory"))
    return out


def cosine(a, b) -> float:
    import numpy as np
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(a @ b / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1.0))


def identity_margin(embed: Callable, look: Path, base: Path, others: list[Path]) -> float | None:
    """m = cos(look, base) - max cos(look, other); None when a face is unread."""
    vec, mine = embed(look), embed(base)
    rivals = [v for v in (embed(o) for o in others) if v is not None]
    if vec is None or mine is None:
        return None
    return cosine(vec, mine) - max((cosine(vec, r) for r in rivals), default=0.0)


def identity_fault(margin: float | None, where: str) -> list[Fault]:
    if margin is None or margin > 0:
        return []
    return [Fault(kind="look_identity", where=where, evidence={"margin": round(margin, 3)}, severity="advisory")]


def judge(picture: Path, want: Markers, reader: Callable, where: str = "",
          face_change: bool = False, embed: Callable | None = None, base: Path | None = None,
          others: list[Path] | None = None) -> Verdict:
    """The verdict on one look picture: HARD head markers refuse; the rest flag."""
    try:
        faults = marker_faults(parse(reader(Path(picture), ASK)), want, where)
    except pc.Unreadable as why:
        faults = [Fault(kind="unread", where=where, note=str(why), severity="advisory")]
    if face_change and embed is not None and base is not None:
        faults += identity_fault(identity_margin(embed, Path(picture), base, others or []), where)
    hard = any(f.severity == "high" for f in faults)
    return Verdict(judge=NAME, version=VERSION, passed=not hard, faults=faults,
                   confidence=0.0 if any(f.kind == "unread" for f in faults) else 1.0, reads=1)
