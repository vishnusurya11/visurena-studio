"""The master eye: the rubric a person used to fill, answered from measures.

Five fields, each one of the one bad episode's faults (`scripts/episode/eye_review.RUBRIC`),
each answered by a number beside a wall:

    shadow   take_look's p5 luma / near-black share, medians over the sampled frames
    faces    the largest face box at every CLOSE shot, as a share of frame height
    board    frame_match, each shot's last sampled frame against its own panel
    repeats  near-duplicate representative-frame pairs not explained by a shared setup
    story    the plan's turn verb among the actions the reader lists on the turn shot +-1

Plus the short read: FRAMES frames spread over the master, each read alone in
the panel vocabulary (`panel_content.ASK`) and judged in code against the shot
`placed.json` puts at that second; and the cross-take identity pass: every
face vector grouped by the character the plan casts there, each within DRIFT
of his own median, no two characters' medians within DRIFT of each other.

A judge LISTS and the code JUDGES.  `frames=`, `reader=` and `embed=` are
injected: a judge built without them reaches ffmpeg, ComfyUI and facenet, and
the test conftest trips on the second.  The rubric it writes carries
`flagged_by` and `evidence` on every `n`; it never writes `waived_because`.
Decision: architecture/decisions/2026-09-24_judges_replace_the_eye.md, section 2, MASTER.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from studio import frame_match as fm, identity_gate, look_gate as lg, panel_content as pc, panel_dq, plan_gates, take_look as tl
from studio.judges.verdict import Fault, Verdict, confidence

NAME, VERSION = "master_eye", "1"
FIELDS = ("shadow", "faces", "board", "repeats", "story")
MEASURED = ("shadow", "faces", "board", "repeats")
"""The fields a fault refuses on (-> recut); `story` flags and never climbs."""
FRAMES = 30
"""The short read: one frame every ~5 s of a 2-3 minute master, read alone."""
CLOSES = ("extreme_close", "close", "medium_close")
FACE_AT_CLOSE = 0.18
FACE_AT_MEDIUM_CLOSE = 0.12
FACES_FITTED_ON = "2026-09-25 one accepted episode, 7 close shots"
DRIFT_SHARE = 0.25
"""The share of a character's reads that must fall under DRIFT before it is a drift."""
"""The rubric's own words: at a close the face reads at a quarter of the frame
height.  The one bad episode drew three medium_close shots at 0.15-0.23."""
ON_BOARD = 0.50
"""frame_match cosine under which a frame is off its cell (take_coherence.ON_BOARD)."""
OFF_BOARD_SHARE = 0.50
"""The share of shots off their board that fails the field: the one bad
episode sat at 62 %, the shipped ones well under.  One episode wide; a wall
with a stated margin."""
REPEAT = 0.90
"""frame_match cosine at which two shots' representative frames are one picture."""
CAMERA = {"camera", "hold", "holds", "held", "locked", "frame", "push", "pushes", "pull", "pulls",
          "track", "tracks", "pan", "pans", "tilt", "tilts", "crane", "cranes", "dolly", "dollies",
          "truck", "trucks", "orbit", "orbits", "lens", "shot", "cut", "cuts", "in", "out", "back"}
STOP = {"the", "and", "then", "with", "his", "her", "their", "from", "into", "onto", "over",
        "under", "off", "for", "that", "this", "them", "him", "she", "him", "one", "two", "as",
        "at", "of", "to", "on", "by", "up", "it", "its", "is", "are", "was", "he", "a", "an"}
WORD = re.compile(r"[a-z]+")

Frames = Callable[[Path, list[float]], list[np.ndarray]]
Reader = Callable[[np.ndarray], str]
Embed = Callable[[np.ndarray], list[dict]]


@dataclass
class Read:
    """One sampled frame as the reader saw it, and where the cut put it."""
    at: float
    shot: int | None
    seen: pc.Seen | None = None
    framing: str = ""
    action: str = ""
    faces: list[dict] = field(default_factory=list)


# ---- where each frame sits ---------------------------------------------------------

def sample_times(seconds: float, count: int = FRAMES) -> list[float]:
    """`count` times spread evenly over the master, each mid-slot, none at the end."""
    return [round((i + 0.5) * seconds / count, 3) for i in range(count)]


def shot_at(placed: dict, at: float) -> int | None:
    """The placed shot whose window holds this second, or None in the tail."""
    for shot in placed.get("shots", []):
        if shot["t_start"] <= at < shot["t_end"]:
            return int(shot["index"])
    return None


def by_shot(reads: list[Read]) -> dict[int, list[Read]]:
    out: dict[int, list[Read]] = {}
    for read in reads:
        if read.shot is not None:
            out.setdefault(read.shot, []).append(read)
    return out


# ---- the reader ---------------------------------------------------------------------

def extra_fields(said: str) -> dict:
    """The reader's `framing` and `action`, when its answer holds them."""
    try:
        got = pc._loads(said)
    except pc.Unreadable:
        return {}
    if isinstance(got, list) and got:
        got = got[0] if isinstance(got[0], dict) else extra_fields(str(got[0]))
    if not isinstance(got, dict):
        return {}
    return {k: str(got.get(k) or "").lower().strip() for k in ("framing", "action")}


def read_frame(reader: Reader, frame: np.ndarray, at: float, shot: int | None) -> Read:
    """One frame, read alone; an unreadable answer is a Read with no `seen`."""
    said = reader(frame)
    said = said if isinstance(said, str) else str(said)
    read = Read(at=at, shot=shot, **extra_fields(said))
    try:
        read.seen = pc.parse(said)
    except pc.Unreadable:
        read.seen = None
    return read


# ---- the five fields ----------------------------------------------------------------

def shadow(stats: list[dict]) -> tuple[bool, dict]:
    """A true black somewhere in most frames: the medians over the sampled
    frames against look_gate's floor."""
    if not stats:
        return True, {"frames": 0, "note": "not measured"}
    p5 = round(float(np.median([s["p5"] for s in stats])), 2)
    near = round(float(np.median([s["near_black"] for s in stats])), 4)
    return (not lg.no_black_floor(p5, near),
            {"p5": p5, "near_black": near, "frames": len(stats),
             "wall": {"p5": lg.P5_FLOOR, "near_black": lg.BLACK_SHARE}})


def face_heights(reads: dict[int, list[Read]]) -> dict[int, float]:
    """Per shot, the tallest face box seen in any of its frames, as a share of height."""
    return {shot: round(max((f.get("h", 0.0) for r in rows for f in r.faces), default=0.0), 3)
            for shot, rows in reads.items()}


def face_wall(size: str) -> float:
    """The face-height floor for a planned size.  Measured 2026-09-25 on an
    accepted, published episode's master frames: medium closes read 0.145-0.227,
    closes 0.198-0.426 (one episode, seven shots -- thin; `fitted_on` carried)."""
    return FACE_AT_CLOSE if size in ("close", "extreme_close") else FACE_AT_MEDIUM_CLOSE


def faces(shots: list[dict], heights: dict[int, float]) -> tuple[bool, dict]:
    """At every close, the face above the floor its planned size sets."""
    rows = [{"shot": int(s["index"]), "size": s.get("size", ""), "h": heights.get(int(s["index"]), 0.0),
             "wall": face_wall(s.get("size", ""))}
            for s in shots if s.get("size") in CLOSES and int(s["index"]) in heights]
    under = [r for r in rows if r["h"] < r["wall"]]
    return not under, {"closes": rows, "under": [r["shot"] for r in under],
                       "wall": {"close": FACE_AT_CLOSE, "medium_close": FACE_AT_MEDIUM_CLOSE},
                       "fitted_on": FACES_FITTED_ON}


def board(last_vs_cell: dict[int, float]) -> tuple[bool, dict]:
    """Each shot's last sampled frame still resembles its own panel."""
    off = {shot: sim for shot, sim in last_vs_cell.items() if sim < ON_BOARD}
    share = round(len(off) / len(last_vs_cell), 3) if last_vs_cell else 0.0
    return share <= OFF_BOARD_SHARE, {"last_vs_cell": last_vs_cell, "off": off, "share": share,
                                      "wall": {"cell": ON_BOARD, "share": OFF_BOARD_SHARE}}


def near_pairs(reps: dict[int, np.ndarray], setups: dict[int, str]) -> list[dict]:
    """Every pair of shots whose representative frames read as one picture."""
    shots, out = sorted(reps), []
    for i, a in enumerate(shots):
        for b in shots[i + 1:]:
            cosine = round(float((reps[a] * reps[b]).sum()), 3)
            if cosine >= REPEAT:
                out.append({"a": a, "b": b, "cosine": cosine,
                            "shared_setup": bool(setups.get(a)) and setups.get(a) == setups.get(b)})
    return out


def repeats(pairs: list[dict]) -> tuple[bool, dict]:
    """A repeat is a near-duplicate pair the setup does not explain."""
    unexplained = [p for p in pairs if p["cosine"] >= REPEAT and not p.get("shared_setup")]
    return not unexplained, {"pairs": unexplained, "count": len(unexplained), "wall": REPEAT}


def root(word: str) -> str:
    """A verb's root, enough to pair the plan's "catches" with the reader's
    "catching": ing / ies / es / ed / s stripped once, never under three letters."""
    for suffix, tail in (("ing", ""), ("ies", "y"), ("es", ""), ("ed", ""), ("s", "")):
        if word.endswith(suffix) and len(word) - len(suffix) + len(tail) >= 3:
            return word[:-len(suffix)] + tail
    return word


def agree(a: str, b: str) -> bool:
    """Two roots are one verb when either is the other's prefix ("run"/"runn")."""
    return len(a) >= 3 and len(b) >= 3 and (a.startswith(b) or b.startswith(a))


def content_words(text: str) -> list[str]:
    """The prose's own words, camera and stop words removed, at the root."""
    return [root(w) for w in WORD.findall((text or "").lower())
            if len(w) >= 3 and w not in CAMERA and w not in STOP]


ACTING = re.compile(r"\b(" + plan_gates.ACTS_ON + r")\b", re.I)


def turn_verbs(shot: dict) -> list[str]:
    """What the turn shot says happens: the ACTING verbs of its prose (the
    catalog of hand verbs a turn is made of), never every content word -- on
    the first real read every word of a motion clause was a 'verb' and nothing
    the reader listed could match it."""
    prose = f"{shot.get('motion', '')} {shot.get('frame', '')}"
    found = {m.group(1).lower() for m in ACTING.finditer(prose)}
    return sorted({root(w) for w in found if w not in CAMERA})   # "the camera holds" is not an act


def listed_actions(reads: dict[int, list[Read]], turn: int) -> list[str]:
    """Every action the reader listed on the turn shot and its neighbours."""
    return [r.action for shot in (turn - 1, turn, turn + 1) for r in reads.get(shot, []) if r.action]


def story(turn_shot: dict | None, reads: dict[int, list[Read]]) -> tuple[bool, dict]:
    """The turn lands as an ACTION on screen: the plan's verb among the listed ones.
    CANNOT TELL IS AN n (root cause 2026-09-26, A3): ep12's story field was y
    on a turn shot whose prose named no act, and that y shipped the episode."""
    if turn_shot is None:
        return False, {"note": "cannot tell: no turn shot in the plan"}
    verbs, turn = turn_verbs(turn_shot), int(turn_shot["index"])
    listed = listed_actions(reads, turn)
    if not verbs:
        return False, {"turn_shot": turn, "verbs": [], "listed": listed,
                      "note": "cannot tell: the turn shot's prose names no acting verb"}
    seen = {w for action in listed for w in content_words(action)}
    hit = sorted({v for v in verbs if any(agree(v, s) for s in seen)})
    return bool(hit), {"turn_shot": turn, "verbs": verbs, "listed": listed, "matched": hit}


# ---- the short read and the identity pass --------------------------------------------

def content_faults(read: Read, shot: dict, setup: dict) -> list[str]:
    """One frame judged as its panel would be: people, copies, lettering, hour, posture."""
    if read.seen is None:
        return []
    return pc.faults(read.seen, frame=f"{shot.get('frame', '')} {shot.get('at_rest', '')}",
                     planned=len(shot.get("faces") or []), crowd=bool((setup.get("crowd") or "").strip()),
                     flat=False, night=panel_dq.at_night(setup.get("described", "")),
                     size=shot.get("size", ""), extras=int(shot.get("extras", 0) or 0))


def who_is(face: dict, shot: dict) -> str | None:
    """Which character a face vector belongs to: the reader's say, else the one
    face the plan casts in the shot; two cast and no say is nobody."""
    if face.get("who"):
        return str(face["who"])
    cast = shot.get("faces") or []
    return str(cast[0]) if len(cast) == 1 else None


def unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return v / (np.linalg.norm(v) or 1e-9)


def drift_faults(vectors: dict[str, list[np.ndarray]]) -> list[Fault]:
    """Each character within DRIFT of his own median, over every take he is in."""
    out = []
    for who, vecs in vectors.items():
        if len(vecs) < 2:
            continue
        median = unit(np.median(np.stack([unit(v) for v in vecs]), axis=0))
        cosines = sorted(float(unit(v) @ median) for v in vecs)
        below = [c for c in cosines if c < identity_gate.DRIFT]
        # one hard-lit frame off the median is not a drift (an accepted episode read
        # one of six at 0.658); at least two reads and a quarter of them must be off
        if len(below) >= 2 and len(below) / len(cosines) >= DRIFT_SHARE:
            out.append(Fault(kind="identity", where=who, note="drift from own median",
                             evidence={"min_cosine": round(cosines[0], 3), "below": len(below),
                                       "wall": identity_gate.DRIFT, "reads": len(vecs),
                                       "fitted_on": FACES_FITTED_ON}))
    return out


def collapse_faults(vectors: dict[str, list[np.ndarray]]) -> list[Fault]:
    """No two characters' medians within DRIFT of each other."""
    medians = {who: unit(np.median(np.stack([unit(v) for v in vecs]), axis=0))
               for who, vecs in vectors.items() if vecs}
    names, out = sorted(medians), []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            cosine = round(float(medians[a] @ medians[b]), 3)
            if cosine >= identity_gate.DRIFT:
                out.append(Fault(kind="identity", where=f"{a}+{b}", note="two characters collapse",
                                 evidence={"cosine": cosine, "wall": identity_gate.DRIFT}))
    return out


def identity(reads: dict[int, list[Read]], shots: dict[int, dict]) -> list[Fault]:
    """The cross-take facenet pass over every face vector the frames gave."""
    vectors: dict[str, list[np.ndarray]] = {}
    for index, rows in reads.items():
        for read in rows:
            for face in read.faces:
                who = who_is(face, shots.get(index, {}))
                if who and face.get("vec") is not None:
                    vectors.setdefault(who, []).append(np.asarray(face["vec"], dtype=float))
    return drift_faults(vectors) + collapse_faults(vectors)


# ---- the pictures --------------------------------------------------------------------

def signatures(frames: list[np.ndarray]) -> list[np.ndarray]:
    return [fm.signature(Image.fromarray(np.asarray(f).astype(np.uint8))) for f in frames]


def representative(reads: dict[int, list[Read]], sigs: dict[float, np.ndarray]) -> dict[int, np.ndarray]:
    """Per shot, the signature of its middle sampled frame."""
    return {shot: sigs[rows[len(rows) // 2].at] for shot, rows in reads.items() if rows}


def last_vs_panel(home: Path, reads: dict[int, list[Read]], sigs: dict[float, np.ndarray]) -> dict[int, float]:
    """Each shot's last sampled frame against `storyboard/shot_NN.png`, where one exists."""
    out = {}
    for shot, rows in reads.items():
        panel = Path(home) / "storyboard" / f"shot_{shot:02d}.png"
        if rows and panel.is_file():
            cell = fm.signature(fm.load(panel))
            out[shot] = round(float((sigs[rows[-1].at] * cell).sum()), 3)
    return out


def read_all(pics: list[np.ndarray], times: list[float], placed: dict, reader: Reader, embed: Embed) -> list[Read]:
    """Every sampled frame: read by the reader, its faces embedded."""
    out = []
    for pic, at in zip(pics, times):
        read = read_frame(reader, pic, at, shot_at(placed, at))
        read.faces = list(embed(pic) or [])
        out.append(read)
    return out


# ---- the judge -----------------------------------------------------------------------

def measures(home: Path, master: Path, plan: dict, placed: dict, *, frames: Frames, reader: Reader,
             embed: Embed, count: int = FRAMES) -> dict:
    """Every number the rubric is answered from, keyed by field, plus the reads."""
    times = sample_times(float(placed["duration_s"]), count)
    pics = frames(master, times)
    reads = read_all(pics, times, placed, reader, embed)
    grouped, sigs = by_shot(reads), dict(zip(times, signatures(pics)))
    shots = {int(s["index"]): s for s in plan.get("shots", [])}
    setups = {i: s.get("setup", "") for i, s in shots.items()}
    turn = next((s for s in shots.values() if s.get("section") == "turn"), None)
    return {"shadow": shadow([tl.stats(np.asarray(p, dtype=float)) for p in pics]),
            "faces": faces(list(shots.values()), face_heights(grouped)),
            "board": board(last_vs_panel(home, grouped, sigs)),
            "repeats": repeats(near_pairs(representative(grouped, sigs), setups)),
            "story": story(turn, grouped),
            "reads": reads, "grouped": grouped, "shots": shots}


def field_faults(m: dict) -> list[Fault]:
    """One fault per rubric field answered n, carrying the measure's numbers."""
    # story is the taste field: it flags, it never refuses (decision §2, "errs toward")
    return [Fault(kind=name, where="master", evidence=m[name][1], severity="low" if name == "story" else "normal")
            for name in FIELDS if not m[name][0]]


def read_faults(m: dict, plan: dict) -> list[Fault]:
    """The short read's faults, one per frame that disagrees with its shot."""
    setups, out = plan.get("setups") or {}, []
    for shot, rows in m["grouped"].items():
        spec = m["shots"].get(shot, {})
        setup = setups.get(spec.get("setup", ""), {}) if isinstance(setups, dict) else {}
        for read in rows:
            if got := content_faults(read, spec, setup):
                out.append(Fault(kind="content", where=f"shot_{shot:02d}", evidence={"at": read.at, "faults": got}))
    return out


def verdict_of(m: dict, plan: dict) -> Verdict:
    reads = m["reads"]
    faults = field_faults(m) + read_faults(m, plan) + identity(m["grouped"], m["shots"])
    return Verdict(judge=NAME, version=VERSION, passed=not faults, faults=faults,
                   confidence=confidence(sum(r.seen is not None for r in reads), len(reads)), reads=len(reads))


def judge(home: Path, master: Path, plan: dict, placed: dict, *, frames: Frames, reader: Reader,
          embed: Embed, count: int = FRAMES) -> Verdict:
    """The master judged: pass, or every fault listed with its numbers."""
    return verdict_of(measures(home, master, plan, placed, frames=frames, reader=reader, embed=embed,
                               count=count), plan)


def read(home: Path, master: Path, plan: dict, placed: dict, *, frames: Frames, reader: Reader,
         embed: Embed, count: int = FRAMES) -> tuple[Verdict, dict]:
    """(verdict, measures): the step keeps the measures to fill the rubric's y fields."""
    m = measures(home, master, plan, placed, frames=frames, reader=reader, embed=embed, count=count)
    return verdict_of(m, plan), m


# ---- the rubric, in the judge's pen ------------------------------------------------------

def faults_by_field(v: Verdict) -> dict[str, dict]:
    """The evidence behind every field this verdict answers n."""
    return {f.kind: f.evidence for f in v.faults if f.kind in FIELDS}


def evidence_for(name: str, v: Verdict, m: dict | None) -> dict:
    flagged = faults_by_field(v)
    if name in flagged:
        return flagged[name]
    return (m or {}).get(name, (True, {}))[1]


def rubric(v: Verdict, digest: str = "", master: str = "", contact: str = "", every: float = 0.0,
           count: int = 0, measures: dict | None = None) -> dict:
    """eye_review's rubric filled by the judge: y with its numbers, n with
    `flagged_by` and `evidence`; `waived_because` stays empty, always."""
    from scripts.episode import eye_review as er
    doc = er.blank_rubric(digest, master, contact, every, count or v.reads)
    flagged = faults_by_field(v)
    for name in FIELDS:
        cell = doc["rubric"][name]
        cell["answer"] = "n" if name in flagged else "y"
        cell["evidence"] = evidence_for(name, v, measures)
        if name in flagged:
            cell["flagged_by"] = v.signer
    doc.update(notes=v.summary(), reviewed_by=v.signer, terminal=v.terminal,
               reviewed_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               faults=[f.model_dump() for f in v.faults])
    return doc


def owner_answered(doc: dict) -> bool:
    """Whether a person, not a judge, has written in this rubric."""
    if str(doc.get("reviewed_by", "")).startswith("judge:"):
        return False
    return any(str(cell.get("answer", "")).strip() for cell in doc.get("rubric", {}).values())


def write_rubric(home: Path, digest: str, v: Verdict, measures: dict | None = None, *,
                 master: str = "", contact: str = "", every: float = 0.0) -> Path:
    """review/eye_<sha8>.json in the judge's pen; a rubric a person answered is
    never written over."""
    target = Path(home) / "review" / f"eye_{digest}.json"
    if target.exists() and owner_answered(json.loads(target.read_text(encoding="utf-8"))):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = rubric(v, digest, master, contact, every, measures=measures)
    target.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return target
