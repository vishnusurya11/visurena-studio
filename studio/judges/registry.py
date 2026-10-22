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
Its `standing` says what the bench may read into it: `shipped`, or why not.

A NEW VLM second-opinion reader is registered through `vlm_entry` (fleet H
ruling A20): it may flag, never refuse -- and so never remove a flag another
judge raised -- until its calibration record meets PREREG B1 rule 4 (one-sided
Clopper-Pearson lower bounds of 0.80 on sensitivity and specificity, over 30
owner faults and 30 owner passes) AND the owner says go.  The VLM refusals
that exist today (panel_content) are untouched: demoting them is the owner's.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from studio import (face_end as fe, intervals, panel_content, panel_dq as pd, stillness as st, take_look as tl,
                    take_verdict as tv, take_zoom as tz, warp_gate as wg)
from studio.casebook import Row
from studio.measure import mouth

Judge = Callable[[Row], dict]


@dataclass(frozen=True)
class Entry:
    name: str
    kind: str
    classes: tuple[str, ...]
    version: str
    judge: Judge
    standing: str = "shipped"


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


CROSS_STAGE = {"frozen-whole": "hold_extra_pushes"}
"""A take wall whose HARD rows a plan cure feeds (craft ruling A26): the plan's `hold_extra_pushes` locks a
shot, and the take gate's frozen-whole row on it is demoted "locked on the grammar".  QC prints both counts as
one known pair; whether holds should move is the shot-framework panel's question, so nothing is muted here."""

GATE_CLASS = {"frozen-at-start": "frozen_start", "frozen-share": "frozen_share", "foreign": "foreign_picture",
              "cut-landing": "cut_early", "drift": "off_board", "coherence off-board": "off_board",
              "last-vs-cell": "off_board", "cut": "cut_early", "churn": "blur_warp", "zoom": "over_push",
              "face-at-end": "face_out", "look": "no_black_floor", "post-cut": "cut_early", "pulse": "pulse",
              "lip-sync": "lip_lag", "identity": "identity_drift", "wardrobe": "wardrobe", "jump": "cut_early",
              "held": "anchored_slide", "tail": "invented_speech"}
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


def measure_of(row: Row, name: str) -> dict | None:
    return ((row.machine.get("take_dq") or {}).get("measures") or {}).get(name)


DEMOTED = ("(planned still)", "ADVISORY", "locked on the grammar")
"""A frozen-whole note that says the row was exempt or demoted; older dq records wrote "(locked on the grammar)"
beside HARD and signed the take a pass all the same (Scarlet ep01, eight takes)."""


def stillness_judge(row: Row) -> dict:
    """`stillness.is_still` on the stored frozen-whole share and the take's seconds; a planned still is exempt
    and a row the grammar demoted to an advisory refuses nothing."""
    g, seconds = gate_of(row, "frozen-whole"), (row.machine.get("take_dq") or {}).get("seconds")
    if not g or g.get("value") is None or seconds is None:
        return refusal(False, [], {"note": "not measured"})
    note = g.get("note", "")
    exempt = any(word in note for word in DEMOTED)
    still = st.is_still({"static_share": float(g["value"])}, float(seconds), exempt)
    return refusal(still, ["frozen_share"], {"static_share": g["value"], "seconds": seconds})


def warp_judge(row: Row) -> dict:
    """`warp_gate.row` on the stored G-WARP measure: HARD on S over its wall only, the state recomputed."""
    m = measure_of(row, "warp")
    if not m or "share" not in m:
        return refusal(False, [], {"note": "not measured"})
    gate = wg.row(m)
    return refusal(gate.hard and not gate.ok, ["blur_warp"], {"S": m.get("S"), "note": gate.note})


def mouth_lag_judge(row: Row) -> dict:
    """`mouth.row` on the stored mouth-to-voice lag: out of tolerance is a flag (production keeps it advisory)."""
    got = measure_of(row, "lag")
    if not got or not got.get("measured"):
        return refusal(False, [], {"note": "not measured"})
    gate = mouth.row(got)
    return refusal(not gate.ok, ["lip_lag"], {"lag_frames": got.get("lag_frames"), "note": gate.note})


# ---- new VLM readers: flag only until calibrated (A20) ----------------------------

VETO_LOWER, VETO_N = 0.80, 30
"""PREREG B1 rule 4: both one-sided CP lower bounds >= 0.80, on >= 30 owner faults and >= 30 owner passes."""


def may_refuse(calibration: dict | None) -> bool:
    """A VLM reader's record clears rule 4 and carries the owner's go."""
    c = calibration or {}
    if c.get("faults", 0) < VETO_N or c.get("passes", 0) < VETO_N or c.get("owner_go") is not True:
        return False
    return (intervals.cp_lower(c["caught"], c["faults"]) >= VETO_LOWER
            and intervals.cp_lower(c["cleared"], c["passes"]) >= VETO_LOWER)


def flag_only(judge: Judge) -> Judge:
    """The reader's word kept as flags in its values; its refusal never stands."""
    def flagged(row: Row) -> dict:
        said = judge(row)
        values = dict(said.get("values") or {})
        values["flags"] = sorted(set(said.get("classes") or [])) if said.get("refused") else []
        return refusal(False, [], values)
    return flagged


def vlm_entry(name: str, kind: str, classes: tuple, version: str, judge: Judge,
              calibration: dict | None = None) -> Entry:
    """A new VLM second opinion's entry: flag only unless its calibration may refuse."""
    if may_refuse(calibration):
        return Entry(name, kind, classes, version, judge, "veto: calibrated past B1 rule 4, owner go")
    return Entry(name, kind, classes, version, flag_only(judge), "flag only: uncalibrated VLM reader (A20)")


# ---- panel judges ---------------------------------------------------------------

PANEL_CLASS = {"people": "extra_people", "clone": "copies", "missing": "missing_people", "blur": "blur_warp",
               "text": "lettering", "stacked": "stacked_pictures", "tiled": "stacked_pictures",
               "seam": "stacked_pictures"}


def panel_dq_judge(row: Row) -> dict:
    """The measured walls re-applied (sharp, ink, tiled); the counted flags (people, clone, missing,
    stacked) as stored, since the row keeps their verdict and not their inputs."""
    r = row.machine.get("panel_dq")
    if not r:
        return refusal(False, [], {"note": "not measured"})
    flags = [f for f in r.get("flags", []) if f in ("people", "clone", "missing", "stacked", "seam")]
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
    "stillness": Entry("stillness", "take", ("frozen_share",), module_version(st), stillness_judge,
                       "uncertified, log only: the flow core under-reads 33-58 % on a dark, flat frame (fleet H skeptic F1)"),
    "warp_gate": Entry("warp_gate", "take", ("blur_warp",), module_version(wg), warp_judge,
                       "shipped; fitted on 27 clips with no owner labels"),
    "mouth_lag": Entry("mouth_lag", "take", ("lip_lag",), module_version(mouth), mouth_lag_judge,
                       "advisory: production never refuses on it; no mouth reader passes the exam (2026-10-21)"),
}


def names() -> list[str]:
    return list(JUDGES)


def get(name: str) -> Entry:
    if name not in JUDGES:
        raise KeyError(f"no judge named {name!r}; the registry knows {names()}")
    return JUDGES[name]
