"""The face replay's rows and counts (2026-10-21_ep02_proof DESIGN 4.1, package P6).

scripts/proof/face_replay.py runs the REAL step-09 face path (face_refine.refine, face_list_note,
tiny_face.rung) and the step-10 paste on a sandbox copy of an episode AS IT WAS AT ITS FIRST
MASTER, with no repair window.  This module is its pure half:

- which file each take index held at the first master: the newest of T<nn>.mp4 and
  attempts/T<nn>_fail*.mp4 rendered by the master's own time (a repair's draw is newer; the take
  it displaced kept its render time when it was moved), and the older files its attempts;
- the first-pass attempts.json and ladder.json: every `face_refine.*` and `tiny_face.*` round and
  every ladder round after the master taken out, so the real counters read as they did;
- the recorded crops, keyed by the sha256 of their `_src` bytes: a crop the first pass asks for
  whose bytes match is `exact`; any other is `unrecorded`, counted, never guessed;
- one row per (take, person) with the DESIGN 4.1 columns, the pre-registered kill (unrecorded over
  50 % of the first-pass crop requests: Q1/Q2 are REAL-RUN), decision agreement with the repair,
  the outside-the-face invariant, the SR-1 GPU estimate and the eye noise band."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np

TINY_PX, BIG_PX = 40.0, 120.0
KILL_SHARE = 0.5
REFINE_KEYS = ("face_refine.", "tiny_face.")
RETAKES = "retakes"
SRC = re.compile(r"^(T\d\d_p\d+)_src\.mp4$")


def read_json(path: Path, default):
    """A named record, or `default` when it is not on disk."""
    import json
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).is_file() else default


def tier(px: float | None) -> str | None:
    """tiny under 40 px, mid 40-120, big over 120 (DESIGN 4.1)."""
    if px is None:
        return None
    return "tiny" if px < TINY_PX else ("mid" if px <= BIG_PX else "big")


def candidates(room: Path, index: int) -> list[Path]:
    """Every file that was ever take `index`: the kept one and its archived draws."""
    named = [Path(room) / f"T{index:02d}.mp4", *sorted((Path(room) / "attempts").glob(f"T{index:02d}_fail*.mp4"))]
    return [p for p in named if p.is_file()]


def iter1_take(room: Path, index: int, cutoff: float) -> tuple[Path | None, list[Path]]:
    """(the file take `index` held at the master made at `cutoff`, the older files: its attempts then)."""
    before = sorted((p for p in candidates(room, index) if p.stat().st_mtime <= cutoff), key=lambda p: p.stat().st_mtime)
    return (before[-1], before[:-1]) if before else (None, [])


def first_pass_ladder(ladder: dict, cutoff: float) -> dict:
    """ladder.json with only the rounds run by the master's time."""
    return {**ladder, "rounds": [r for r in ladder.get("rounds") or [] if float(r.get("at") or 0) <= cutoff]}


def first_pass_attempts(doc: dict, ladder: dict, cutoff: float) -> dict:
    """attempts.json as the first pass reads it: no refine or tiny-face round, the retakes rounds
    counted from the ladder's rounds run by the master's time."""
    out = {k: v for k, v in doc.items() if not k.startswith(REFINE_KEYS)}
    if RETAKES in out:
        out[RETAKES] = {**out[RETAKES], "rounds": len(first_pass_ladder(ladder, cutoff)["rounds"])}
    return out


def sha256_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recorded_crops(refine_dir: Path) -> dict[str, Path]:
    """sha256 of each recorded `_src` crop -> the render the engine returned for it (both on disk)."""
    out = {}
    for src in sorted(Path(refine_dir).glob("T[0-9][0-9]_p*_src.mp4")):
        render = src.with_name(f"{SRC.match(src.name).group(1)}.mp4")
        if render.is_file():
            out[sha256_of(src)] = render
    return out


def kill(classes: list[str]) -> dict:
    """The pre-registered kill: unrecorded over half the first-pass crop requests (or none asked)."""
    n, miss = len(classes), sum(c == "unrecorded" for c in classes)
    share = round(miss / n, 3) if n else 1.0
    return {"requests": n, "unrecorded": miss, "share": share, "real_run": n == 0 or share > KILL_SHARE}


def eye_of(p: dict | None) -> float | None:
    """The drawn-eye score a person shipped with: the redraw's when kept, else the take's own."""
    if not p:
        return None
    m = p.get("measures") or {}
    return m.get("eye_ref") if p.get("kept") else m.get("eye_src")


def person_of(doc: dict, take: str, who) -> dict | None:
    return next((p for p in (doc.get(take) or {}).get("people") or [] if p.get("who") == who), None)


def row(take: str, p: dict | None, status: str, flags: dict, eyes: tuple) -> dict:
    """One (take, person) row with the DESIGN 4.1 columns."""
    m, px = (p or {}).get("measures") or {}, (p or {}).get("min_px") or (p or {}).get("face_px")
    return {"take": take, "who": (p or {}).get("who"), "px": px, "tier": tier(px), "selected": flags["selected"],
            "refined": p is not None, "accepted": bool((p or {}).get("kept")), "why": (p or {}).get("why") or status,
            "eye_cel_iter1": eyes[0], "eye_cel_replay": eyes[1], "eye_cel_iter3": eyes[2],
            "outside_moved": flags["outside"], "flicker": m.get("flick_ref"), "id_ref": m.get("id_ref"),
            "match": flags["match"], "iter1_basis": flags["basis"]}


CANNED_COLUMNS = ("accepted", "eye_cel_replay", "flicker", "id_ref")
"""What a gate decided on a canned render: never evidence (DESIGN 2.4), so blank on an unrecorded row."""


def uncanned(r: dict) -> dict:
    """An unrecorded row keeps what the first pass ASKED (take, person, size) and drops what the gate
    decided on the canned grey render it was served."""
    if r["match"] != "unrecorded":
        return r
    return {**r, **dict.fromkeys(CANNED_COLUMNS), "why": f"unrecorded: the gate read a canned render ({r['why']})"}


def take_rows(index: int, replay: dict, iter1: dict, iter3: dict, selected: set[int], matches: dict,
              outside: dict) -> list[dict]:
    """The rows of one take: one per person the replay refined, else one saying why none was."""
    take = f"T{index:02d}"
    entry = replay.get(take) or {}
    people = entry.get("people") or [None]
    out = []
    for p in people:
        who = (p or {}).get("who")
        basis = "first pass" if person_of(iter1, take, who) else "overwritten"
        flags = {"selected": index in selected, "outside": outside.get((take, who)), "basis": basis,
                 "match": matches.get((take, who))}
        eyes = (eye_of(person_of(iter1, take, who)), eye_of(p), eye_of(person_of(iter3, take, who)))
        out.append(uncanned(row(take, p, entry.get("status") or "not_selected", flags, eyes)))
    return out


def agreement(replay: dict, repair: dict, takes: list[str]) -> dict:
    """Take-level decision agreement (status) with what the repair decided on each named take."""
    out = [{"take": t, "replay": (replay.get(t) or {}).get("status"), "repair": (repair.get(t) or {}).get("status")}
           for t in takes]
    out = [{**r, "agree": r["replay"] is not None and r["replay"] == r["repair"]} for r in out]
    return {"n": len(out), "agree": sum(r["agree"] for r in out), "rows": out}


def people_of(entry: dict | None) -> list[str]:
    return sorted(str(p.get("who")) for p in (entry or {}).get("people") or [])


def selection_agreement(replay: dict, repair: dict, takes: list[str]) -> dict:
    """Did the first pass track each take for the same people the repair decided?  This needs no
    render: it is the selection, the tracker and the matcher, all real code on the take's bytes."""
    out = [{"take": t, "replay": people_of(replay.get(t)), "repair": people_of(repair.get(t))} for t in takes]
    out = [{**r, "agree": r["take"] in replay and r["replay"] == r["repair"]} for r in out]
    return {"n": len(out), "agree": sum(r["agree"] for r in out), "rows": out}


def sr1_inputs(replay: dict, real: dict) -> dict:
    """SR-1's per-take inputs: the replay's priced crops (its own engine clock is no clock), and a
    measured gpu_busy_s only from the real record of the same take bytes."""
    out = {}
    for take, entry in replay.items():
        if take[:1] == "T" and take[1:].isdigit():
            said = {"gpu_s_priced": entry.get("gpu_s_priced")}
            known = real.get(take) or {}
            if known.get("take_sha8") == entry.get("take_sha8") and known.get("gpu_busy_s") is not None:
                said["gpu_busy_s"] = known["gpu_busy_s"]
            out[take] = said
    return out


def outside_moved(before: np.ndarray, after: np.ndarray, allowed: np.ndarray) -> float:
    """The share of pixels OUTSIDE the allowed face core that the paste changed (the invariant is 0)."""
    changed = np.any(np.asarray(before) != np.asarray(after), axis=-1)
    outside = ~np.asarray(allowed, bool)
    return float((changed & outside).sum() / outside.sum()) if outside.any() else 0.0


def sr1_estimate(entries: dict, takes: list[str]) -> dict:
    """SR-1's GPU seconds: each take's measured gpu_busy_s, else its priced gpu_s_priced, said apart."""
    measured = {t: float(entries[t]["gpu_busy_s"]) for t in takes if (entries.get(t) or {}).get("gpu_busy_s") is not None}
    priced = {t: float(entries[t]["gpu_s_priced"]) for t in takes
              if t not in measured and (entries.get(t) or {}).get("gpu_s_priced") is not None}
    unknown = [t for t in takes if t not in measured and t not in priced]
    return {"takes": len(takes), "measured_s": round(sum(measured.values()), 1), "measured_takes": len(measured),
            "priced_s": round(sum(priced.values()), 1), "priced_takes": len(priced), "unknown_takes": unknown,
            "estimate_s": round(sum(measured.values()) + sum(priced.values()), 1)}


def noise_band(first: list[float], again: list[float], plus: list[float], minus: list[float]) -> dict:
    """The eye measure's noise: its largest change read twice on the same crops, and one frame either way."""
    repeat = max((abs(a - b) for a, b in zip(first, again)), default=0.0)
    shift = max((abs(a - b) for side in (plus, minus) for a, b in zip(first, side)), default=0.0)
    return {"repeat": round(float(repeat), 3), "shift": round(float(shift), 3)}
