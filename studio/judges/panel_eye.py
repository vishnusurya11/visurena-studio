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

import json
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from studio import cell_gates, identity_gate, panel_content, panel_dq
from studio.judges import verdict as jv
from studio.judges.verdict import Fault, Verdict
from studio.measure import boxes, copy as cp, faces, keypoints, ocr

NAME, VERSION = "panel_eye", "1"
CAPTION = "image_qwen3vl_caption"
TIMEOUT = 120.0
SIZE_ASK = ('Answer with strict JSON and nothing else, two keys. "size": how much of the main '
            'figure the frame holds, one of ' + ", ".join(keypoints.ORDER) + '. "pictures": how many '
            'separate pictures are tiled side by side or stacked in this image, 1 when it is one picture.')
CLOSE = panel_dq.FACE_IS_THE_PICTURE
"""The sizes at which an unread panel is a fault."""
CALIBRATED = frozenset({"stacked", "tiled", "people", "clone", "clones", "missing", "blur", "text",
                        "lettering", "copy", "repeat", "unread", "banned"})
"""Fault kinds with a measured margin (decision §1.4); the rest are thin."""
CONTENT = (("unread", "unread"), ("missing", "missing"), ("lettering", "lettering"), ("posture", "posture"),
           ("hour", "hour"), ("landform", "landform"), ("banned", "banned"))
Unreadable = panel_content.Unreadable
_DEFAULT: dict = {}


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


def stored_faults(board: Path) -> list[Fault]:
    """The two machine gates' rows as faults with a where."""
    return dq_faults(rows_of(board, "panel_dq.json")) + content_faults(rows_of(board, "panel_content.json"))


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
                                    "max_new_tokens": 64}, TIMEOUT))


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


def keypoint_read(staged: str, run: Callable) -> np.ndarray | None:
    return person_of(keypoints.parse(run(keypoints.WORKFLOW, {"image_1": staged}, TIMEOUT)))


def posture_fault(pts: np.ndarray | None, prose: str, planned: int, where: str) -> Fault | None:
    """The shot lays, seats or crouches its one person; the keypoints disagree."""
    wanted = panel_content.asked_posture(prose)
    if wanted is None or planned != 1 or pts is None:
        return None
    seen = keypoints.posture(pts)
    if seen in ("unread", wanted):
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
    return [fault("lettering", where, note=f"{r['kind']}: {r['text']!r}", **r) for r in found]


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
        run, stage = run or comfy.run_text, stage or comfy.stage_image
    return {"run": run, "stage": stage, "reader": reader, "detect": detect, "embed": embed}


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
    pts = keypoint_read(staged, t["run"])
    read, unread = short_read(staged, t["run"], shot.get("size", ""), where)
    seen = face_rows(rgb, t["detect"], t["embed"])
    out = [framing(shot.get("size", ""), keypoints.shot_size(pts) if pts is not None else None, read, where),
           posture_fault(pts, prose, planned, where), copy_fault(path, refs, where), unread,
           hat_fault(staged, t["run"], seen, pts, size, where) if planned == 1 else None]
    out += clone_faults(seen, where) + landmark_faults(staged, t["run"], setup.get("described", ""), where)
    out += lettering_faults(path, t["reader"], list(shot.get("faces") or []), prose,
                            shot.get("size") == "insert", size[0], where)
    return [f for f in out if f], read is not None


def judge(home: Path, plan: dict, *, book: Path | None = None, run=None, stage=None, reader=None,
          detect=None, embed=None) -> Verdict:
    """The verdict over every panel of the board, as it stands."""
    board, t = Path(home) / "storyboard", tools(run, stage, reader, detect, embed)
    setups = plan.get("setups") or {}
    faults, reads, readable = stored_faults(board), 0, 0
    for shot in plan.get("shots") or []:
        path = board / f"{where_of(shot['index'])}.png"
        if not path.exists():
            continue
        setup = setups.get(shot.get("setup"), {}) or {}
        found, ok = read_panel(shot, setup, path, t, refs_of(book, shot, setup))
        faults, reads, readable = faults + found, reads + 1, readable + int(ok)
    faults += repeat_faults(board, plan, rows_of(board, "panel_content.json"))
    return Verdict(judge=NAME, version=VERSION, passed=not any(f.severity != "advisory" for f in faults),
                   faults=faults, confidence=jv.confidence(readable, reads), reads=reads)
