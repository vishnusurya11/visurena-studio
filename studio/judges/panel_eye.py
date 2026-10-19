"""The panel eye: the judge that signs EYE_PANELS (episode/08), in place of a
person looking at storyboard/contact.png.

It LISTS faults and code judges the list.  Its reads, per panel:

- the stored machine rows as they stand (`panel_dq.json` incl. stacked by
  thirds; `panel_content.json`, the list-then-judge rows) -> one Fault per
  failed row, with a WHERE that names the panel;
- the measures of C5: hats worn AND held (GroundingDINO + the detected head +
  DWPose wrists), a copy of a staged reference (pHash / SSIM), posture and
  framing by keypoint, clones (facenet pairwise; structural under READABLE),
  lettering as a recognised string (EasyOCR), a landmark the place never
  named, a repeat inside one setup (equal subjects + a copy);
- ONE short VLM read (size, pictures) as the second vote on framing and on a
  tiled board.  A malformed answer raises `Unreadable`, never a default; an
  unread close is a fault (the face is the picture), an unread wide is not,
  and both count against confidence.

Calibrated rows refuse; thin rows (hat, landmark, posture) refuse on the
cheap rungs and are flagged at the terminal; framing has no owner positive
yet, so a single vote is advisory and only the two votes together refuse.
Every reader is injectable (`run=`, `stage=`, `reader=`, `detect=`, `embed=`);
the defaults are ComfyUI, EasyOCR and facenet, built once.
"""
from __future__ import annotations

import re
import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image
from pydantic import Field

from studio import cell_gates, identity_gate, panel_content, panel_dq
from studio.judges import verdict as jv
from studio.judges.verdict import Fault, Verdict
from studio.measure import boxes, copy as cp, faces, keypoints, ocr

NAME, VERSION = "panel_eye", "1"
CAPTION = "image_qwen3vl_caption"
SCORED_BOXES = False
"""Whether the installed box workflow is a SCORED open-vocabulary detector.
Measured 2026-09-25 on a finished episode: the LayerMask ObjectDetectorMask
route returns a mask for every word asked (225 "bridge" boxes on one panel,
39 "gasworks"), so hats and landmarks read as 587 false faults over 23 panels
and the asks (27 words x 23 panels = 621 GPU jobs) took 70 minutes.  Until a
node emits boxes WITH scores and labels, the hat and landmark measures are
not measured: no ask, no fault, `not_measured` in the evidence."""
TIMEOUT = 900.0
"""Per ask.  One GPU serves every stage and every session: on the first real run
a 120 s wait died behind another episode's render still on the queue, and the
whole judge crashed on one panel.  A queued ask waits; a dead one is `unread`."""
SIZE_ASK = ('Answer with strict JSON and nothing else, two keys. "size": how much of the main '
            'figure the frame holds, one of ' + ", ".join(keypoints.ORDER) + '. "pictures": how many '
            'separate pictures are tiled side by side or stacked in this image, 1 when it is one picture.')
CLOSE = panel_dq.FACE_IS_THE_PICTURE
"""The sizes at which an unread panel is a fault."""
CALIBRATED = frozenset({"stacked", "seam", "tiled", "people", "clone", "clones", "missing", "blur", "text",
                        "lettering", "copy", "repeat", "unread", "banned", "twin"})
"""Fault kinds with a measured margin (decision §1.4); the rest are thin.
'twin' (G-TWIN, 2026-10-05) has a measured contract -- figures vs distinct,
judged in code -- so it refuses rather than flags-as-thin."""
CONTENT = (("unread", "unread"), ("twin", "twin"), ("missing", "missing"), ("lettering", "lettering"),
           ("posture", "posture"), ("hour", "hour"), ("landform", "landform"), ("banned", "banned"))
ADVISORY_BODY = ("body", "orphan_limb")
"""Kinds not in CALIBRATED on purpose: they join it only after P06's E1 eval reaches recall >= 0.6 and
precision >= 0.8 (decision D8); until then they are listed, never a wall."""
UNREAD = "unread_for_time"
READERS = ("keypoints", "size", "faces", "lettering")
"""The readers whose seconds the evidence names."""
Unreadable = panel_content.Unreadable
_DEFAULT: dict = {}


class EyeVerdict(Verdict):
    """The verdict with the eye's own books: reads, cache_hits, seconds per reader, unread_for_time."""
    evidence: dict = Field(default_factory=dict)


# ---- the stored rows -------------------------------------------------------------

def where_of(shot: int) -> str:
    return f"shot_{int(shot):02d}"


def shot_of(where: str) -> int:
    return int(str(where).rsplit("_", 1)[-1])


def fault(kind: str, where: str, note: str = "", **evidence) -> Fault:
    """A fault that says whether its row is calibrated."""
    return Fault(kind=kind, where=where, note=note,
                 evidence={**evidence, "calibrated": kind in CALIBRATED})


def rows_of(board: Path, name: str) -> list[dict]:
    path = Path(board) / name
    return list(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else []


def dq_faults(rows: list[dict]) -> list[Fault]:
    """Every flag of every failed panel_dq row."""
    keep = ("sharp", "ink", "tiled", "cast_faces", "planned")
    return [fault(flag, where_of(r["shot"]), source="panel_dq", **{k: r[k] for k in keep if k in r})
            for r in rows if not r.get("passed", True) for flag in r.get("flags") or []]


def content_kind(text: str, row: dict) -> str:
    """The class of one panel_content fault line."""
    for word, kind in CONTENT:
        if word in text:
            return kind
    if "figure(s) for" in text:
        return "clones" if row.get("lookalikes") else "people"
    return "content"


def content_faults(rows: list[dict]) -> list[Fault]:
    return [fault(content_kind(text, r), where_of(r["shot"]), note=text, source="panel_content")
            for r in rows if not r.get("passed", True) for text in r.get("faults") or []]


def advisory(kind: str, where: str, note: str, **evidence) -> Fault:
    """A listed fault that changes no verdict (an uncalibrated detector)."""
    return fault(kind, where, note, **evidence).model_copy(update={"severity": "advisory"})


def answer_faults(rows: list[dict]) -> list[Fault]:
    """panel_content's optional anatomy answers (contract K9: ok / fading / floating / cannot_tell)
    as advisory `body` and `orphan_limb` rows; the paid read already made them, no second ask."""
    out = []
    for r in rows:
        for key, kind in (("body", "body"), ("limb_attached", "orphan_limb")):
            if str(r.get(key) or "ok") not in ("ok", "cannot_tell"):
                out.append(advisory(kind, where_of(r["shot"]), f"{key} reads {r[key]!r}", source="panel_content", answer=r[key]))
    return out


def stored_faults(board: Path) -> list[Fault]:
    """The two machine gates' rows as faults with a where."""
    content = rows_of(board, "panel_content.json")
    return dq_faults(rows_of(board, "panel_dq.json")) + content_faults(content) + answer_faults(content)


# ---- the short read ----------------------------------------------------------------

def parse_size(said: str) -> dict:
    """{"size", "pictures"} from the reader's answer, however wrapped; a missing
    or foreign value is Unreadable."""
    got = panel_content._loads(said if isinstance(said, str) else str(said))
    if isinstance(got, list) and got:
        got = panel_content._loads(got[0]) if isinstance(got[0], str) else got[0]
    if not isinstance(got, dict) or "size" not in got or "pictures" not in got:
        raise Unreadable(f"the size read has no size or pictures: {str(said)[:80]!r}")
    size = str(got["size"]).lower().strip().replace(" ", "_").replace("-", "_")
    if size not in keypoints.ORDER:
        raise Unreadable(f"size {size!r} is not one of {keypoints.ORDER}")
    try:
        return {"size": size, "pictures": int(got["pictures"])}
    except (TypeError, ValueError) as bad:
        raise Unreadable(str(bad)) from bad


def size_read(staged: str, run: Callable, seed: int = 11) -> dict:
    return parse_size(run(CAPTION, {"image_1": staged, "prompt": SIZE_ASK, "seed": seed,
                                    "max_new_tokens": 128}, TIMEOUT))   # the Qwen3_VQA node floor


def framing(planned: str, measured: str | None, read: dict | None, where: str) -> Fault | None:
    """Two votes two steps off refuse; the keypoint vote alone is advisory; the
    read alone is never the wall."""
    by_key = keypoints.size_fault(measured or "", planned) if measured else None
    by_read = keypoints.size_fault(read["size"], planned) if read else None
    if not by_key:
        return None
    severity = "normal" if by_read else "advisory"
    return Fault(kind="framing", where=where, severity=severity, note=by_key,
                 evidence={"planned": planned, "keypoints": measured, "read": read["size"] if read else None,
                           "calibrated": False})


# ---- the measures ------------------------------------------------------------------

def person_of(frames: list[dict]) -> np.ndarray | None:
    """The most-seen person of the first frame, or None."""
    found = keypoints.people(frames[0]) if frames else []
    return max(found, key=lambda p: int((p[:, 2] >= keypoints.CONF).sum())) if found else None


def keypoint_frames(staged: str, run: Callable) -> list[dict]:
    return keypoints.parse(run(keypoints.WORKFLOW, {"image_1": staged}, TIMEOUT))


def keypoint_read(staged: str, run: Callable) -> np.ndarray | None:
    return person_of(keypoint_frames(staged, run))


def orphan_faults(frames: list[dict] | None, shot: dict, where: str) -> list[Fault]:
    """A limb with no body, from the DWPose frame already read: an orphan wrist, too many wrists per
    head, or declared extras that the pose found nobody for.  Advisory until calibrated."""
    if frames is None:
        return []
    why = keypoints.orphan_frame(frames[0]) if frames else []
    if int(shot.get("extras") or 0) > 0 and not (frames and keypoints.people(frames[0])):
        why = [*why, f"{shot['extras']} extras declared and the pose found nobody"]
    return [advisory("orphan_limb", where, "; ".join(why), source="dwpose")] if why else []


UNPOSED = ("insert", "extreme_close", "close", "medium_close")
"""Framings that crop the body: no posture can be read from them."""
TOP_DOWN = re.compile(r"\blooking down\b|\bhigh angle\b|\bfrom above\b", re.I)
"""A camera straight above a lying man gives the same 2D keypoints as a man standing."""


def posture_fault(pts: np.ndarray | None, prose: str, planned: int, where: str,
                  size: str = "") -> Fault | None:
    """The shot lays, seats or crouches its one person; the keypoints disagree.
    Judged by eye on ep13's board: sitting on the ground reads 'low', a top-down
    lying man reads 'standing', and a chest-up frame has no legs to read."""
    wanted = panel_content.asked_posture(prose)
    if wanted is None or planned != 1 or pts is None or size in UNPOSED or TOP_DOWN.search(prose):
        return None
    seen = keypoints.posture(pts)
    if seen in ("unread", wanted) or (wanted == "sitting" and seen == "low"):
        return None
    return fault("posture", where, note=f"posture {seen!r}: the shot asks for {wanted}", asked=wanted, seen=seen)


def face_rows(rgb: np.ndarray, detect: Callable, embed: Callable) -> list[dict]:
    """Every detected face with its height (a share of the frame), its facenet
    vector when readable and its structural signature otherwise."""
    h, w = rgb.shape[:2]
    out = []
    for f in detect(rgb):
        x1, y1, x2, y2 = f["box"]
        share = (y2 - y1) / h
        crop = Image.fromarray(rgb).crop((int(x1), int(y1), int(max(x1 + 1, x2)), int(max(y1 + 1, y2))))
        vec = embed(rgb, f["box"]) if share >= identity_gate.READABLE else None
        out.append({"h": round(share, 3), "cx": (x1 + x2) / 2 / w, "cy": (y1 + y2) / 2 / h,
                    "vec": vec, "sig": faces.structure(crop)})
    return out


def clone_faults(seen: list[dict], where: str) -> list[Fault]:
    return [fault("clones", where, note=f"faces {p['i']} and {p['j']} are one man ({p['by']})",
                  cosine=p["cosine"], by=p["by"]) for p in faces.clone_pairs(seen)]


def hat_fault(staged: str, run: Callable, seen: list[dict], pts, size: tuple[int, int], where: str) -> Fault | None:
    """A hat worn and a hat held on the one planned person."""
    found = boxes.parse(run(boxes.WORKFLOW, {"image_1": staged, "prompt": "hat",
                                             "threshold": boxes.BOX_THRESHOLD}, TIMEOUT))
    if not found or not seen:
        return None
    aspect = size[0] / size[1]
    heads = [boxes.head_box(f, aspect) for f in seen]
    wrists = keypoints.wrists(pts) if pts is not None else []
    states = boxes.hats(boxes.normalised(found, size), heads, wrists, max(f["h"] for f in seen))
    why = boxes.hat_fault(states)
    return fault("hat", where, note=why, hats=states) if why else None


def lettering_faults(path: Path, reader: Callable, cast: list[str], prose: str, insert: bool,
                     width: int, where: str) -> list[Fault]:
    found = ocr.lettering(ocr.read(path, reader), cast, prose, insert=insert, width=width)
    return [fault("lettering", where, note=f"{r['kind']}: {r['text']!r}", found=r["kind"],
                  **{k: v for k, v in r.items() if k != "kind"}) for r in found]


def landmark_faults(staged: str, run: Callable, place: str, where: str) -> list[Fault]:
    """MAJOR words the place never names, asked one by one; a box is an invention."""
    have = cell_gates.landmarks(place)
    asked = [w for w in cell_gates.MAJOR if w not in have and not (cell_gates.KIN.get(w, set()) & have)]

    def detect(image, word):
        return boxes.parse(run(boxes.WORKFLOW, {"image_1": image, "prompt": word,
                                                "threshold": boxes.BOX_THRESHOLD}, TIMEOUT))
    found = boxes.detect_words(staged, asked, detect)
    return [fault("landmark", where, note=f"{word} drawn where the place names none", boxes=len(found[word]))
            for word in boxes.invented(found, place)]


def copy_fault(path: Path, refs: list[Path], where: str) -> Fault | None:
    best = cp.against(path, refs) if refs else None
    if not best or not best["copy"]:
        return None
    return fault("copy", where, note=f"a staged reference handed back: {Path(best['path']).name}",
                 phash=best["phash"], ssim=best["ssim"], of=Path(best["path"]).name)


def repeat_faults(board: Path, plan: dict, content: list[dict]) -> list[Fault]:
    """Two panels of one setup that list the same subjects and are one picture."""
    subjects = {r["shot"]: tuple(r.get("subjects") or ()) for r in content}
    setup_of = {int(s["index"]): s["setup"] for s in plan.get("shots") or []}
    shots = sorted(i for i in subjects if (board / f"{where_of(i)}.png").exists())
    out = []
    for k, a in enumerate(shots):
        for b in shots[k + 1:]:
            if setup_of.get(a) != setup_of.get(b) or not subjects[a] or subjects[a] != subjects[b]:
                continue
            row = cp.compare(board / f"{where_of(a)}.png", board / f"{where_of(b)}.png")
            if cp.is_copy(row):
                out.append(fault("repeat", where_of(b), note=f"repeats {where_of(a)}", of=where_of(a), **row))
    return out


# ---- the tools and the judge -------------------------------------------------------

def is_json(text: str) -> bool:
    try:
        json.loads(text.strip())
    except ValueError:
        return False
    return True


def cached_run(name: str, values: dict, timeout: float = 600.0) -> str:
    """A ComfyUI text read through the vlm cache; only a JSON answer is kept,
    so a garbled one is asked again (speed plan #5)."""
    from studio import comfy
    return comfy.cached_text(name, values, readable=is_json, timeout=timeout)


def tools(run=None, stage=None, reader=None, detect=None, embed=None) -> dict:
    """The five readers, the injected ones kept and the rest built once:
    ComfyUI for the workflows, EasyOCR for strings, facenet for faces."""
    if detect is None or embed is None:
        _DEFAULT.setdefault("pair", faces.embedder())
        detect, embed = detect or _DEFAULT["pair"][0], embed or _DEFAULT["pair"][1]
    if reader is None:
        reader = _DEFAULT.setdefault("reader", ocr.default_reader())
    if run is None or stage is None:
        from studio import comfy
        run, stage = run or cached_run, stage or comfy.stage_image
    return {"run": run, "stage": stage, "reader": reader, "detect": detect, "embed": embed}


LOOSE = ("wide", "full", "medium", "medium_close")
"""Sizes whose background is the room; a close or an insert shows too little of it."""


def room_of(home: Path, book: Path | None, name: str, setup: dict) -> Path | None:
    """What the setup's grids were told the room is: the anchor cell when cut,
    else the place picture (studio/grid_room)."""
    from studio import grid_room
    room = grid_room.room_path(home, name)
    if room.exists():
        return room
    if book is None:
        return None
    try:
        from studio import pack_refs
        return pack_refs.location_view(book, setup.get("location") or "", view=setup.get("view") or "")
    except Exception:
        return None


def place_faults(home: Path, plan: dict, book: Path | None) -> list[Fault]:
    """panel_place: a loose panel that is the staged room's MIRROR (ep14's
    Waterloo drew the rails on the right where the plate has them left).
    ADVISORY: it never fails the verdict and takes no rung until calibrated
    over five episodes (docs/calibration/panel_place.md)."""
    from studio.measure import place
    board, setups, out = Path(home) / "storyboard", plan.get("setups") or {}, []
    rooms = {name: room_of(home, book, name, setup) for name, setup in setups.items()}
    for shot in plan.get("shots") or []:
        panel, room = board / f"{where_of(shot['index'])}.png", rooms.get(shot.get("setup"))
        if shot.get("size") not in LOOSE or room is None or not panel.exists():
            continue
        read = place.versus(place.load(panel), place.load(room))
        if place.mirrored(read):
            out.append(Fault(kind="place", where=panel.stem, severity="advisory",
                             note=f"the room's mirror: profile {read['prof_same']:+.2f}, light "
                                  f"{read['side_panel']:+.2f} vs {read['side_ref']:+.2f}",
                             evidence={**read, "room": room.name, "calibrated": False}))
    return out


def refs_of(book: Path | None, shot: dict, setup: dict) -> list[Path]:
    """The pictures the grid staged for this shot: its cast's sheets and the
    setup's place picture, when the book is at hand."""
    if book is None:
        return []
    out = [p for who in shot.get("faces") or [] if (p := Path(book) / "refs" / "characters" / who / "sheet.png").exists()]
    try:
        from studio import pack_refs
        out.append(pack_refs.location_view(book, setup.get("location") or "", view=setup.get("view") or ""))
    except Exception:          # a setup with no place picture stages none
        pass
    return [p for p in out if Path(p).exists()]


def asked(ask: Callable, default, stats: dict | None = None):
    """One detector ask that may die on the shared GPU queue: a timeout or an
    unreadable answer is a missing measure, never a crash of the whole judge.
    The rows that needed it read "not measured" and the calibrated rows stand.
    The failure is counted (`failed`): a read that had one is never kept."""
    try:
        return ask()
    except (Unreadable, TimeoutError) as why:          # comfy.StillRunning is a TimeoutError
        if stats is not None:
            stats["failed"] = stats.get("failed", 0) + 1
        return default


def metered(t: dict, reader: str, ask: Callable):
    """`ask()`, its seconds booked to `reader` in the judge's stats (when it keeps any)."""
    stats, began = t.get("stats"), time.monotonic()
    try:
        return ask()
    finally:
        if stats is not None:
            stats["seconds"][reader] = round(stats["seconds"].get(reader, 0.0) + time.monotonic() - began, 3)


def short_read(staged: str, run: Callable, planned_size: str, where: str) -> tuple[dict | None, Fault | None]:
    """The one VLM read, or the reason it could not be read -- a fault only
    when the face is the picture."""
    try:
        return size_read(staged, run), None
    except Unreadable as why:
        return None, fault("unread", where, note=str(why)) if planned_size in CLOSE else None


def read_panel(shot: dict, setup: dict, path: Path, t: dict, refs: list[Path]) -> tuple[list[Fault], bool]:
    """Every measured fault of one panel, and whether its short read was readable."""
    where, planned = path.stem, len(shot.get("faces") or [])
    prose = f"{shot.get('frame', '')} {shot.get('at_rest', '')}"
    rgb = np.asarray(Image.open(path).convert("RGB"))
    size = (rgb.shape[1], rgb.shape[0])
    staged = t["stage"](path)
    frames = metered(t, "keypoints", lambda: asked(lambda: keypoint_frames(staged, t["run"]), None, t.get("stats")))
    pts = person_of(frames) if frames else None
    read, unread = metered(t, "size", lambda: short_read(staged, t["run"], shot.get("size", ""), where))
    seen = metered(t, "faces", lambda: face_rows(rgb, t["detect"], t["embed"]))
    out = [framing(shot.get("size", ""), keypoints.shot_size(pts) if pts is not None else None, read, where),
           posture_fault(pts, prose, planned, where, shot.get("size", "")), copy_fault(path, refs, where), unread,
           asked(lambda: hat_fault(staged, t["run"], seen, pts, size, where), None, t.get("stats"))
           if planned == 1 and SCORED_BOXES else None]
    out += clone_faults(seen, where) + orphan_faults(frames, shot, where)
    if SCORED_BOXES:
        out += asked(lambda: landmark_faults(staged, t["run"], setup.get("described", ""), where), [], t.get("stats"))
    out += metered(t, "lettering", lambda: lettering_faults(path, t["reader"], list(shot.get("faces") or []), prose,
                                                            shot.get("size") == "insert", size[0], where))
    return [f for f in out if f], read is not None


CACHE = "eye_cache"
"""storyboard/eye_cache/<key>.json: one panel's read, kept while nothing it reads moved (P2)."""


@lru_cache(maxsize=None)
def workflow_sha(name: str) -> str:
    """The identity of a VL workflow: the sha of its JSON on disk, "absent" when it is not there."""
    import hashlib
    from studio import comfy
    try:
        hit = next(iter(comfy.WORKFLOWS.glob(f"*/{name}.json")), None)
        return hashlib.sha256(hit.read_bytes()).hexdigest()[:12] if hit else "absent"
    except OSError:
        return "absent"


def ask_sha() -> str:
    """What the reads ASK: SIZE_ASK, the caption workflow and DWPose by name and by file.  Reworded
    asks or a swapped workflow make every cached read stale (ep01: the key held none of them)."""
    import hashlib
    parts = [SIZE_ASK, CAPTION, keypoints.WORKFLOW, workflow_sha(CAPTION), workflow_sha(keypoints.WORKFLOW)]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]


_REF_SHA: dict = {}


def ref_sha(path: Path) -> str:
    """A reference's bytes, hashed once per (size, mtime): a re-cut of identical pixels is the same ref."""
    import hashlib
    p = Path(path)
    if not p.is_file():
        return ""
    st = p.stat()
    memo = (str(p), st.st_size, st.st_mtime_ns)
    if memo not in _REF_SHA:
        _REF_SHA[memo] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    return _REF_SHA[memo]


def read_key(shot: dict, setup: dict, path: Path, refs: list[Path]) -> str:
    """What one panel's read depends on: its bytes, its shot's size/faces/frame/at_rest, the setup's
    words, its references' bytes, the asks (ask_sha), the judge's version and switches (timeline debate
    2026-10-18, P2: Jekyll ep01's eye re-read unchanged bytes, 46 of 08's 66 min)."""
    import hashlib
    h = hashlib.sha256(Path(path).read_bytes())
    words = {k: shot.get(k) for k in ("size", "faces", "frame", "at_rest")}
    stats = [(Path(r).name, ref_sha(r)) for r in refs]
    h.update(json.dumps([words, setup.get("described", ""), stats, VERSION, SCORED_BOXES, ask_sha()],
                        sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def cache_file(shot: dict, setup: dict, path: Path, refs: list[Path]) -> Path:
    return Path(path).parent / CACHE / f"{read_key(shot, setup, path, refs)}.json"


def load_hit(hit: Path) -> tuple[list[Fault], bool] | None:
    try:
        doc = json.loads(hit.read_text(encoding="utf-8"))
        return [Fault(**f) for f in doc["faults"]], bool(doc["ok"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def bump(t: dict, name: str) -> None:
    if t.get("stats") is not None:
        t["stats"][name] += 1


def cached_read(shot: dict, setup: dict, path: Path, t: dict, refs: list[Path]) -> tuple[list[Fault], bool]:
    """read_panel once per key.  A read is kept only when every ask answered: an Unreadable or a
    TimeoutError is a transient failure, asked again next time."""
    hit = cache_file(shot, setup, path, refs)
    if (kept := load_hit(hit)) is not None:
        bump(t, "cache_hits")
        return kept
    stats = t.get("stats") or {}
    failed = stats.get("failed", 0)
    found, ok = read_panel(shot, setup, path, t, refs)
    bump(t, "reads")
    if ok and stats.get("failed", 0) == failed:
        hit.parent.mkdir(exist_ok=True)
        hit.write_text(json.dumps({"faults": [f.model_dump() for f in found], "ok": ok}), encoding="utf-8")
    return found, ok


def new_stats() -> dict:
    return {"reads": 0, "cache_hits": 0, "failed": 0, "seconds": {k: 0.0 for k in READERS}, "unread_for_time": []}


def deadline_left(wall_s: float, booked_s: float) -> float:
    """What is left of the panel_checks wall after the step's booked seconds (contract K3)."""
    return max(0.0, wall_s - booked_s)


def unread_marker(board: Path) -> Path:
    return Path(board) / "eye_unread.json"


def mark_unread(board: Path, unread: list[str]) -> None:
    """storyboard/eye_unread.json lists the panels the wall left unread; step 08 refuses to sign
    the board while it exists, so the next window reads them before any take."""
    marker = unread_marker(board)
    if unread:
        marker.write_text(json.dumps(unread), encoding="utf-8")
    elif marker.exists():
        marker.unlink()


def timing_note(evidence: dict) -> str:
    """The timing.jsonl note: the three counts, then the whole evidence as json."""
    return (f"reads={evidence['reads']} cache_hits={evidence['cache_hits']} "
            f"unread={len(evidence['unread_for_time'])}|{json.dumps(evidence, sort_keys=True)}")


def order_of(items: list[tuple]) -> list[tuple]:
    """Uncached panels first (the newest picture first: the rewound ones), cached last."""
    return sorted(items, key=lambda i: (i[3].exists(), -i[2].stat().st_mtime_ns))


def unread_faults(unread: list[str]) -> list[Fault]:
    return [fault(UNREAD, where, note="not read before the panel_checks wall; read in the next window") for where in unread]


def planned_panels(board: Path, plan: dict, book: Path | None) -> list[tuple]:
    """(shot, setup, path, cache file, refs) of every panel on disk."""
    setups, out = plan.get("setups") or {}, []
    for shot in plan.get("shots") or []:
        path = board / f"{where_of(shot['index'])}.png"
        if path.exists():
            setup = setups.get(shot.get("setup"), {}) or {}
            refs = refs_of(book, shot, setup)
            out.append((shot, setup, path, cache_file(shot, setup, path, refs), refs))
    return out


def judge(home: Path, plan: dict, *, book: Path | None = None, run=None, stage=None, reader=None,
          detect=None, embed=None, deadline: float | None = None, clock: Callable = time.monotonic) -> EyeVerdict:
    """The verdict over every panel of the board, as it stands.  With `deadline` (seconds) it stops
    taking NEW reads at the wall: the panels left are faults (`unread_for_time`), never passed."""
    board, t = Path(home) / "storyboard", tools(run, stage, reader, detect, embed)
    t["stats"], began = new_stats(), clock()
    faults, reads, readable = stored_faults(board), 0, 0
    from studio import comfy
    with comfy.model_kept():    # ~30 reads, ONE VL load (five-hour plan fix 5; ~9.7 s a reload)
        for shot, setup, path, hit, refs in order_of(planned_panels(board, plan, book)):
            reads += 1
            if not hit.exists() and deadline is not None and clock() - began >= deadline:
                t["stats"]["unread_for_time"].append(path.stem)
                continue
            found, ok = cached_read(shot, setup, path, t, refs)
            faults, readable = faults + found, readable + int(ok)
    return finish(board, plan, (home, book), t["stats"], faults, (reads, readable), clock() - began)


def finish(board: Path, plan: dict, where: tuple, stats: dict, faults: list[Fault],
           counts: tuple[int, int], spent_s: float) -> EyeVerdict:
    """The board-wide checks, the unread panels as faults, the books in the evidence."""
    home, book = where
    unread = sorted(stats["unread_for_time"])
    faults += repeat_faults(board, plan, rows_of(board, "panel_content.json")) + place_faults(home, plan, book)
    faults += unread_faults(unread)
    mark_unread(board, unread)
    if unread:
        from studio import step_caps
        print(step_caps.cap_line("panel_checks", 1, 1, spent_s, len(faults)), flush=True)
    evidence = {k: stats[k] for k in ("reads", "cache_hits", "seconds", "unread_for_time")}
    return EyeVerdict(judge=NAME, version=VERSION, passed=not any(f.severity != "advisory" for f in faults),
                      faults=faults, confidence=jv.confidence(counts[1], counts[0]), reads=counts[0],
                      evidence=evidence)
