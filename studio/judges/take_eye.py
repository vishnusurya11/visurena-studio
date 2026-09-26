"""The take eye: `judge:take_eye@1`, a judge over the kept takes.

It reads what the machine already measured and wrote beside each take --
`T??.dq.json` (the dq rows, with C8's pass-through, rotation, leak,
last-vs-panel, cut-vote and lag rows among them) and `T??.content.json` (the
reader's list, judged against the plan) -- and lists every failing row as a
Fault with a `where` and its evidence.  Two more reads are injectable, so no
test opens a video: `clones=` (facenet pairs within one frame, C5's
`measure.faces`) and `reader=` (the framing / action second vote,
`take_content.second_vote`).  Code judges the list; nobody is asked "is it
right".

A row is a fault when it is HARD, or advisory with a cure the ladder owns
(lag -> shorter take, leak -> head cut, rotation -> move type).  Other
advisory rows already cost the take its points and are not the eye's
business.  A row that failed on the kept take AND on another attempt of it
`repeated` on a fresh seed, which the ladder reads to skip the seed rung.
Confidence is the share of reads that were readable, a count.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from studio import take_content
from studio.judges.verdict import Fault, Verdict, confidence

NAME, VERSION = "take_eye", "1"
CURABLE_ADVISORY = frozenset({"lag", "leak", "rotation"})
"""Advisory rows the ladder has a rung for; every other advisory row is points off, not a fault."""
HARD_CONTENT = frozenset({"content", "clones", "identity", "unread"})
GEOMETRY = frozenset({"pass-through", "held", "cut-vote", "cut", "jump", "cut-landing", "foreign",
                      "frozen-at-start", "frozen-share", "frozen-whole", "coherence off-board", "last-vs-cell",
                      "last-vs-panel", "drift", "face-at-end", "zoom", "rotation"})
"""The fault kinds a still may answer on a narration shot (decision §1.2, EYE-takes terminal)."""

Reader = Callable[[Path], dict | None]
Clones = Callable[[Path], list | None]


def where(index: int) -> str:
    return f"T{index:02d}"


def index_of(take: Path) -> int:
    return int(Path(take).stem[1:3])


def read_json(path: Path) -> dict | None:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def machine(take: Path) -> tuple[dict, dict]:
    """The two machine verdicts beside the take; a take without both is
    refused, not judged: a gate that never ran has passed nothing."""
    dq, content = read_json(Path(take).with_suffix(".dq.json")), read_json(Path(take).with_suffix(".content.json"))
    if dq is None or content is None:
        raise SystemExit(f"REFUSED: {Path(take).name} has no dq or content verdict to judge from")
    return dq, content


def failed_rows(doc: dict) -> list[dict]:
    return [g for g in doc.get("gates") or [] if not g.get("ok", True)]


def other_attempts(dq: dict) -> list[dict]:
    """The record's attempts other than the kept file."""
    return [a for a in dq.get("attempts") or [] if a.get("file") != dq.get("file")]


def repeated_rows(dq: dict) -> set[str]:
    """Rows failing on the kept take that also failed on another attempt of it."""
    now = {g["name"] for g in failed_rows(dq)}
    return {g["name"] for a in other_attempts(dq) for g in failed_rows(a)} & now


def leak_evidence(dq: dict, name: str) -> dict:
    if name != "leak":
        return {}
    got = (dq.get("measures") or {}).get("leak") or {}
    return {"frames": got.get("frames"), "covers": bool(got.get("covers"))}


def dq_faults(index: int, dq: dict) -> list[Fault]:
    """Every HARD row that failed, and every curable advisory row, as faults."""
    repeated = repeated_rows(dq)
    out = []
    for g in failed_rows(dq):
        if not g.get("hard") and g["name"] not in CURABLE_ADVISORY:
            continue
        out.append(Fault(kind=g["name"], where=where(index), severity="normal" if g.get("hard") else "low",
                         note=g.get("note", ""),
                         evidence={"value": g.get("value"), "penalty": g.get("penalty", 0.0),
                                   "repeated": g["name"] in repeated, **leak_evidence(dq, g["name"])}))
    return out


def content_faults(index: int, content: dict, repeated: bool = False) -> list[Fault]:
    """The content gate's faults, each HARD; an unread take is a fault of its own kind."""
    return [Fault(kind="unread" if text.startswith("unread") else "content", where=where(index), note=text,
                  evidence={"hard": True, "repeated": repeated})
            for text in content.get("faults") or []]


def clone_faults(index: int, pairs: list | None) -> list[Fault]:
    return [Fault(kind="clones", where=where(index), evidence=dict(p),
                  note=f"two faces read as one man ({p.get('by', '')} {p.get('cosine', '')})")
            for p in pairs or []]


def vote_faults(index: int, said: dict, size: str, motion: str) -> list[Fault]:
    """The reader's framing and action against the plan: low faults, a second vote."""
    votes = (("framing", take_content.framing_vote(said.get("framing", ""), size)),
             ("action", take_content.action_vote(said.get("action", ""), motion)))
    return [Fault(kind=kind, where=where(index), note=why, severity="low", evidence={"second_vote": True})
            for kind, why in votes if why]


def planned(plan, index: int) -> tuple[str, str]:
    """(size, motion) of the take's first shot -- a take is named by it."""
    if plan is None:
        return "", ""
    try:
        shot = plan.shot(index)
    except StopIteration:
        return "", ""
    return str(shot.size), shot.motion


def voted(take: Path, index: int, plan, reader: Reader | None) -> tuple[list[Fault], int, int]:
    """(faults, reads, readable) of the second vote; nothing without a reader."""
    if reader is None:
        return [], 0, 0
    said = reader(take)
    if not said:
        return [], 1, 0
    return vote_faults(index, said, *planned(plan, index)), 1, 1


def one_take(take: Path, plan, reader: Reader | None, clones: Clones | None) -> tuple[list[Fault], int, int]:
    """(faults, reads, readable) for one kept take."""
    index = index_of(take)
    dq, content = machine(take)
    faults = dq_faults(index, dq) + content_faults(index, content, bool(other_attempts(dq)))
    reads, readable = 1, int(not any(f.kind == "unread" for f in faults))
    more, r, ok = voted(take, index, plan, reader)
    faults, reads, readable = faults + more, reads + r, readable + ok
    if clones is not None:
        pairs = clones(take)
        faults, reads, readable = faults + clone_faults(index, pairs), reads + 1, readable + (pairs is not None)
    return faults, reads, readable


def judge(takes: list[Path], *, plan=None, reader: Reader | None = None,
          clones: Clones | None = None, embed=None) -> Verdict:
    """The verdict over the kept takes: pass when no take lists a fault."""
    clones = clones or (clones_by(embed) if embed is not None else None)
    faults, reads, readable = [], 0, 0
    for take in sorted(Path(t) for t in takes):
        more, r, ok = one_take(take, plan, reader, clones)
        faults, reads, readable = faults + more, reads + r, readable + ok
    return Verdict(judge=NAME, version=VERSION, passed=not faults, faults=faults,
                   confidence=confidence(readable, reads), reads=reads)


def clones_by(embed, detect=None) -> Clones:
    """Clone pairs per sampled frame through `measure.faces` (C5): every face
    observed, then `clone_pairs` within each frame.  `detect` defaults to the
    facenet detector, built on the first take; no test reaches it."""
    def read(take: Path) -> list | None:
        from studio import identity_gate
        from studio.measure import faces

        det = detect or faces.embedder()[0]
        by_frame: dict[int, list[dict]] = {}
        for f in identity_gate.observe(take, [], {}, detect=det, embed=embed, bank={}):
            by_frame.setdefault(f.k, []).append({"h": f.h, "vec": f.vec, "sig": None})
        return [p | {"frame": k} for k, fs in by_frame.items() for p in faces.clone_pairs(fs)]
    return read


def facenet_clones(take: Path) -> list | None:
    """The production clone reader: facenet on the CPU, or `None` (cannot
    tell) when the library is not installed."""
    try:
        from studio.measure import faces
        detect, embed = faces.embedder()
    except ImportError:
        return None
    return clones_by(embed, detect)(take)
