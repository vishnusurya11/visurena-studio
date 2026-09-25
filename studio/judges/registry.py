"""Names -> judges, for the bench and the ratchet.

Each wrapper re-judges a casebook row from the values the row already
carries (`machine`: the dq / content / panel json harvested beside the
artefact) through the SHIPPED verdict function and its constants, so a wall
moved in `take_zoom.py` moves the bench, and the ratchet sees it.  Nothing
here opens a picture or decodes a video.  Where the stored json keeps only
the gate's flags and not its inputs (people, clones, the VLM's list), the
stored flag is the verdict, and the wrapper says so in its values.

A judge returns {"refused": bool, "classes": [fault classes], "values": {}}.
Its `version` is the sha8 of the module it wraps: a changed wall is a
changed version, and the baseline records which one it was benched on.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from studio import face_end as fe, panel_content, panel_dq as pd, take_look as tl, take_verdict as tv, take_zoom as tz
from studio.casebook import Row

Judge = Callable[[Row], dict]


@dataclass(frozen=True)
class Entry:
    name: str
    kind: str
    classes: tuple[str, ...]
    version: str
    judge: Judge


def module_version(module) -> str:
    """The sha8 of the wrapped module's source: its constants are its version."""
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()[:8]


def refusal(refused: bool, classes: list[str], values: dict) -> dict:
    return {"refused": bool(refused), "classes": sorted(set(classes)) if refused else [], "values": values}


def gate_of(row: Row, name: str) -> dict | None:
    for g in (row.machine.get("take_dq") or {}).get("gates") or []:
        if g.get("name") == name:
            return g
    return None


def planned_of(row: Row) -> dict:
    return (row.machine.get("take_dq") or {}).get("planned") or {}


# ---- take judges ----------------------------------------------------------------

def zoom_judge(row: Row) -> dict:
    """`take_zoom.judge` per anchor segment against the shot's planned reach; the worst segment rules."""
    z = (row.machine.get("take_dq") or {}).get("zoom") or {}
    segs = [s for s in (z.get("segments") or [z]) if s.get("ratio") is not None]
    if not segs:
        return refusal(False, [], {"note": "not measured"})
    plans = list(planned_of(row).get("motions") or [planned_of(row).get("motion", "")])
    plans = plans + [plans[-1]] * len(segs)
    hard = []
    for s, plan in zip(segs, plans):
        said = tz.judge(s["ratio"], plan, s.get("measured", True), s.get("monotonic", True), s.get("camera"), tz.has_exit(plan))
        hard += said["hard"]
    return refusal(bool(hard), ["over_push"], {"ratio": z.get("ratio"), "hard": hard})


def face_from_note(g: dict) -> dict | None:
    """The face `face_end.verdict` read, rebuilt from the row it wrote: height, clipped, edges."""
    if g.get("value") is None:
        return None
    note = g.get("note", "")
    clipped = "clipped" in note
    edges = note.split("clipped", 1)[1].split()[0].split("/") if clipped else []
    return {"h": float(g["value"]), "clipped": clipped, "edges": edges}


def face_end_judge(row: Row) -> dict:
    g = gate_of(row, "face-at-end")
    if not g or g.get("note") == "not measured":
        return refusal(False, [], {"note": "not measured"})
    planned = planned_of(row)
    gate = fe.verdict(face_from_note(g), planned.get("size", ""), int(planned.get("faces") or 0))
    return refusal(gate.hard and not gate.ok, ["face_out"], {"h": g.get("value"), "note": gate.note})


LOOK = re.compile(r"p5 (\d+(?:\.\d+)?) black (\d+\.\d+) hue (\d+\.\d+)")
LOST = re.compile(r"black lost (\d+\.\d+)->(\d+\.\d+)")
ROSE = re.compile(r"hue rose (\d+\.\d+)->(\d+\.\d+)")
MEAN = re.compile(r"level mean (\d+)")


def look_from_note(g: dict) -> dict | None:
    """The measure `take_look.verdict` read, rebuilt from its own note."""
    m = LOOK.search(g.get("note", ""))
    if not m or g.get("value") is None:
        return None
    p5, black, hue = float(g["value"]), float(m.group(2)), float(m.group(3))
    lost, rose, mean = LOST.search(g["note"]), ROSE.search(g["note"]), MEAN.search(g["note"])
    return {"n": 2, "p5": p5, "near_black": black, "share": hue,
            "near_black_first": float(lost.group(1)) if lost else black, "near_black_last": float(lost.group(2)) if lost else black,
            "share_first": float(rose.group(1)) if rose else hue, "share_last": float(rose.group(2)) if rose else hue,
            "mean": float(mean.group(1)) if mean else 0.0}


def look_judge(row: Row) -> dict:
    g = gate_of(row, "look")
    m = look_from_note(g) if g else None
    if m is None:
        return refusal(False, [], {"note": "not measured"})
    gate = tl.verdict(m, bool(planned_of(row).get("daylight")))
    return refusal(gate.hard and not gate.ok, ["no_black_floor"], {"p5": m["p5"], "note": gate.note})


GATE_CLASS = {"frozen-at-start": "frozen_start", "frozen-share": "frozen_share", "foreign": "foreign_picture",
              "cut-landing": "cut_early", "drift": "off_board", "coherence off-board": "off_board",
              "last-vs-cell": "off_board", "cut": "cut_early", "churn": "blur_warp", "zoom": "over_push",
              "face-at-end": "face_out", "look": "no_black_floor", "post-cut": "cut_early", "pulse": "pulse",
              "lip-sync": "lip_lag", "identity": "identity_drift", "wardrobe": "wardrobe", "jump": "cut_early",
              "held": "anchored_slide"}
GATE_FIELDS = ("name", "value", "ok", "hard", "note", "penalty")


def take_verdict_judge(row: Row) -> dict:
    """`take_verdict.score` over the stored gate rows: PASS means every hard gate is ok."""
    stored = (row.machine.get("take_dq") or {}).get("gates") or []
    if not stored:
        return refusal(False, [], {"note": "not measured"})
    gates = [tv.Gate(**{k: g.get(k) for k in GATE_FIELDS}) for g in stored]
    score, passed = tv.score(gates)
    failing = [g.name for g in gates if g.hard and not g.ok]
    return refusal(not passed, [GATE_CLASS.get(n, "unknown") for n in failing], {"score": score, "failing": failing})


# ---- panel judges ---------------------------------------------------------------

PANEL_CLASS = {"people": "extra_people", "clone": "copies", "missing": "missing_people", "blur": "blur_warp",
               "text": "lettering", "stacked": "stacked_pictures", "tiled": "stacked_pictures"}


def panel_dq_judge(row: Row) -> dict:
    """The measured walls re-applied (sharp, ink, tiled); the counted flags (people, clone, missing,
    stacked) as stored, since the row keeps their verdict and not their inputs."""
    r = row.machine.get("panel_dq")
    if not r:
        return refusal(False, [], {"note": "not measured"})
    flags = [f for f in r.get("flags", []) if f in ("people", "clone", "missing", "stacked")]
    flags += ["blur"] if float(r.get("sharp", 1.0)) < pd.SHARP_FLOOR else []
    flags += ["text"] if float(r.get("ink", 0.0)) > pd.INK else []
    flags += ["tiled"] if float(r.get("tiled", 0.0)) > pd.TILED else []
    return refusal(bool(flags), [PANEL_CLASS[f] for f in flags], {"flags": flags})


CONTENT_CLASS = (("copies of another", "copies"), ("figure(s) for", "extra_people"), ("missing", "missing_people"),
                 ("lettering", "lettering"), ("posture", "posture"), ("hour", "hour"), ("landform", "landform"),
                 ("banned", "landform"), ("unread", "unknown"))


def content_classes(faults: list[str]) -> list[str]:
    out = []
    for fault in faults:
        for word, name in CONTENT_CLASS:
            if word in fault and not (name == "extra_people" and "missing" in fault):
                out.append(name)
    return out or (["unknown"] if faults else [])


def panel_content_judge(row: Row) -> dict:
    """The content gate's stored row: a listed-then-judged verdict the wrapper cannot re-run without the VLM."""
    r = row.machine.get("panel_content")
    if r is None:
        return refusal(False, [], {"note": "not measured"})
    faults = list(r.get("faults") or [])
    return refusal(not r.get("passed", True), content_classes(faults), {"faults": len(faults), "version": panel_content.__name__})


# ---- the registry ---------------------------------------------------------------

JUDGES = {
    "take_zoom": Entry("take_zoom", "take", ("over_push",), module_version(tz), zoom_judge),
    "face_end": Entry("face_end", "take", ("face_out",), module_version(fe), face_end_judge),
    "take_look": Entry("take_look", "take", ("no_black_floor",), module_version(tl), look_judge),
    "take_verdict": Entry("take_verdict", "take", tuple(sorted(set(GATE_CLASS.values()))), module_version(tv), take_verdict_judge),
    "panel_dq": Entry("panel_dq", "panel", tuple(sorted(set(PANEL_CLASS.values()))), module_version(pd), panel_dq_judge),
    "panel_content": Entry("panel_content", "panel", ("copies", "extra_people", "missing_people", "lettering", "posture", "hour", "landform"),
                           module_version(panel_content), panel_content_judge),
}


def names() -> list[str]:
    return list(JUDGES)


def get(name: str) -> Entry:
    if name not in JUDGES:
        raise KeyError(f"no judge named {name!r}; the registry knows {names()}")
    return JUDGES[name]
