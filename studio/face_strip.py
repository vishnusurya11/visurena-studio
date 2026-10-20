"""The face contact strip at QC (deadline retro 2026-10-20, item 4, package D).

Step 11 cuts up to PER_TIER face crops per face-size tier out of the MASTER (what the viewer sees,
after the paste and the one upscale) and lays them in one strip, review/faces_<sha8>.png.  The
master eye reads each crop (studio/judges/master_eye.FACE_ASK), and review/face_labels_<sha8>.json
keeps every crop with the eye's word and an empty `owner` cell for the owner's good / bad.  That
file is the label source any later face metric is calibrated on (gates_that_see: 4 of 15 refines
better by a metric, 8 of 15 by the owner's eye).  Nothing here is a wall: log only (owner veto
list V3, 2026-10-20, not vetoed).

The tiers are cut-scale px, the face list's own scale (studio/face_refine.face_list): the take's
smallest tracked face, or the master detector's smallest box scaled to the cut where the list
measured none.  A listed take (a soft face no paste covered) is shown first in its tier; one that
nothing measured gets the `unmeasured` row rather than being dropped.  Crops are CPU work: one
ffmpeg grab per take at the middle of its window, the detector on that frame.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

from studio import edit_gate, episode_home
from studio.face_refine import LIST_PX

TIERS = (("tiny", 0.0, 60.0), ("small", 60.0, LIST_PX), ("medium", LIST_PX, 240.0), ("large", 240.0, math.inf))
"""Cut-scale px.  60 was the refine's wall before 2026-10-19 (ep01's blur class sat under it), 120 is
LIST_PX (the refine's eligibility constant), 240 is twice it.  Fitted on ep01 alone; display rows."""
UNMEASURED = "unmeasured"
"""The row for a listed take whose face neither the list nor the master detector measured."""
PER_TIER = 4
CELL = 384
"""A cell's side.  The ep01 replay (2026-10-20) at 192 shrank a 300 px master face 3x and hid the blur
the strip is for; at 384 a face under 256 master px (64 cut px) is shown larger than it is, never smaller."""
CAPTION = 18
MARGIN = 0.25
"""The crop's border around the face box, as a share of the box's longer side (hair and chin show)."""
BACK = (15, 16, 18)
"""The studio dark, #0f1012: an empty cell and the letterbox."""
CUT_HEIGHT = 768
"""The render height the face list's px are measured at, where a record does not say."""

Frames = Callable[[Path, list[float]], list[np.ndarray]]
Detect = Callable[[np.ndarray], list]


def tier_of(px: float | None) -> str | None:
    """The tier a cut-scale face size falls in; None for an unmeasured face."""
    if px is None:
        return None
    return next(name for name, lo, hi in TIERS if lo <= px < hi)


def candidates(face: dict, records: list[dict]) -> list[dict]:
    """One row per take: the face list's smallest face (cut px), listed, pasted.  With no list
    (a step 09 before 2026-10-20), every take the cut holds, measured by the detector alone."""
    rows = face.get("takes") or {f"T{int(r['index']):02d}": {} for r in records}
    listed = set(face.get("listed") or [])
    return [{"take": take, "index": int(take[1:]), "px": row.get("smallest_px"), "listed": take in listed,
             "pasted": bool(row.get("pasted"))} for take, row in rows.items()]


def take_times(placed: dict, records: list[dict], dead: dict | None = None) -> dict[int, float]:
    """take -> the master second at the middle of its window, in the cut the master was made from."""
    cut, kept = edit_gate.dead_view(placed, records, dead)
    fps = edit_gate.FPS
    return {int(r["take"]): round((r["start"] + r["n"] / 2) / fps, 3) for r in edit_gate.segment_plan(cut, kept, fps)}


def cut_height(records: list[dict]) -> float:
    return float(next((r["height"] for r in records if r.get("height")), CUT_HEIGHT))


def smallest_box(boxes: list) -> list[float] | None:
    """The detector's smallest face box (the face list names the smallest face too)."""
    found = [[float(v) for v in b] for b in boxes or []]
    return min(found, key=lambda b: b[3] - b[1]) if found else None


def square(box: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    """A square around the box, MARGIN wider on each side, kept inside the frame."""
    side = max(box[2] - box[0], box[3] - box[1]) * (1 + 2 * MARGIN)
    cx, cy, half = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, min(side, width, height) / 2
    x0, y0 = min(max(cx - half, 0), width - 2 * half), min(max(cy - half, 0), height - 2 * half)
    return int(x0), int(y0), int(round(x0 + 2 * half)), int(round(y0 + 2 * half))


def fitted(picture: Image.Image, side: int = CELL) -> Image.Image:
    """The picture inside a side x side cell, letterboxed on the studio dark."""
    scale = side / max(picture.size)
    shown = picture.resize((max(1, round(picture.size[0] * scale)), max(1, round(picture.size[1] * scale))),
                           Image.LANCZOS)
    cell = Image.new("RGB", (side, side), BACK)
    cell.paste(shown, ((side - shown.size[0]) // 2, (side - shown.size[1]) // 2))
    return cell


def crop(frame: np.ndarray, box: list[float] | None) -> Image.Image:
    """The face cell: the squared box, or the whole frame when no face was found."""
    rgb = Image.fromarray(np.asarray(frame).astype(np.uint8)).convert("RGB")
    return fitted(rgb.crop(square(box, *rgb.size)) if box else rgb)


def located(row: dict, frame: np.ndarray, at: float, detect: Detect, cut_h: float) -> dict:
    """The row with its master frame's smallest face: its box, its master px, its cut px (`shown_px`,
    the face as the crop shows it; the take's `px` where the list measured none)."""
    box, height = smallest_box(detect(frame)), np.asarray(frame).shape[0]
    master_px = round(box[3] - box[1], 1) if box else None
    shown_px = round(master_px * cut_h / height, 1) if box else None
    px = row["px"] if row["px"] is not None else shown_px
    tier = tier_of(px) or (UNMEASURED if row["listed"] else None)
    return {**row, "px": px, "master_px": master_px, "shown_px": shown_px, "tier": tier, "at": at, "box": box,
            "kind": "face" if box else "frame", "cell": crop(frame, box)}


def rank(row: dict) -> tuple:
    """Listed first, then the smallest face, then the take's order."""
    return (not row["listed"], row["px"] if row["px"] is not None else math.inf, row["index"])


def picks(rows: list[dict]) -> list[dict]:
    """Up to PER_TIER rows per tier, in tier order then rank."""
    out = []
    for tier in [name for name, _lo, _hi in TIERS] + [UNMEASURED]:
        out += sorted((r for r in rows if r["tier"] == tier), key=rank)[:PER_TIER]
    return out


def caption(row: dict) -> str:
    """`T06 49px shown 76 pasted LISTED`: the take's smallest face, the shown face (cut px), its state."""
    px = "?" if row["px"] is None else f"{row['px']:.0f}"
    shown = "" if row.get("shown_px") is None else f" shown {row['shown_px']:.0f}"
    return f"{row['take']} {px}px{shown}" + (" pasted" if row["pasted"] else "") + (" LISTED" if row["listed"] else "")


def compose(rows: list[dict]) -> Image.Image:
    """One line per tier, PER_TIER cells wide, each cell captioned under its picture."""
    tiers = list(dict.fromkeys(r["tier"] for r in rows))
    sheet = Image.new("RGB", (CELL * PER_TIER, max(1, len(tiers)) * (CELL + CAPTION)), BACK)
    pen = ImageDraw.Draw(sheet)
    for line, tier in enumerate(tiers):
        for col, row in enumerate(r for r in rows if r["tier"] == tier):
            x, y = col * CELL, line * (CELL + CAPTION)
            sheet.paste(row["cell"], (x, y))
            pen.text((x + 4, y + CELL + 3), f"{tier} {caption(row)}", fill=(220, 220, 220))
    return sheet


def crop_name(sha8: str, row: dict) -> str:
    return f"faces_{sha8}/{row['tier']}_{row['take']}.png"


def save(home: Path, sha8: str, rows: list[dict]) -> list[dict]:
    """Each cell as review/faces_<sha8>/<tier>_<Tnn>.png, the strip beside them; the rows, cells dropped."""
    review = Path(home) / "review"
    (review / f"faces_{sha8}").mkdir(parents=True, exist_ok=True)
    for row in rows:
        row["cell"].save(review / crop_name(sha8, row))
    compose(rows).save(review / strip_name(sha8))
    return [{**{k: v for k, v in r.items() if k != "cell"}, "crop": crop_name(sha8, r)} for r in rows]


def strip_name(sha8: str) -> str:
    return f"faces_{sha8}.png"


def build(home: Path, master: Path, sha8: str, face: dict, placed: dict, records: list[dict],
          frames: Frames, detect: Detect, dead: dict | None = None) -> list[dict]:
    """The strip for THESE master bytes: one frame per take, its smallest face, the picks saved."""
    times = take_times(placed, records, dead)
    rows = [r for r in candidates(face, records) if r["index"] in times]
    pics = frames(master, [times[r["index"]] for r in rows]) if rows else []
    cut_h = cut_height(records)
    chosen = picks([located(r, p, times[r["index"]], detect, cut_h) for r, p in zip(rows, pics)])
    return save(home, sha8, chosen) if chosen else []


# ---- the owner's labels -----------------------------------------------------------------------

LABELS = ("good", "bad")
HOW = ("owner: open the strip, write good or bad in each crop's `owner` (2-3 min); `eye` is the master "
       "eye's read (clear / soft / warped / none), log only until these labels calibrate it")
KEPT = ("crop", "take", "tier", "px", "shown_px", "master_px", "listed", "pasted", "at", "kind", "eye")


def labels_path(home: Path, sha8: str) -> Path:
    return Path(home) / "review" / labels_name(sha8)


def labels_name(sha8: str) -> str:
    return f"face_labels_{sha8}.json"


def agreement(rows: list[dict]) -> dict:
    """How often the eye agrees with the owner, over the crops the owner labelled (clear = good)."""
    done = [r for r in rows if r.get("owner") in LABELS and r.get("eye")]
    agree = sum((r["eye"] == "clear") == (r["owner"] == "good") for r in done)
    return {"labelled": len(done), "agree": agree}


def write_labels(home: Path, sha8: str, rows: list[dict]) -> Path:
    """review/face_labels_<sha8>.json: every crop, the eye's word, the owner's label kept across rewrites."""
    path = labels_path(home, sha8)
    old = episode_home.read_json(path) if path.exists() else {}
    owner = {c.get("crop"): c.get("owner", "") for c in old.get("crops") or []}
    crops = [{**{k: r.get(k, "") for k in KEPT}, "owner": owner.get(r["crop"], "")} for r in rows]
    doc = {"sha8": sha8, "strip": strip_name(sha8), "how": HOW, "labels": list(LABELS),
           "crops": crops, "agreement": agreement(crops)}
    return episode_home.write_json(path, doc)


def line(strip: dict, sha8: str) -> str:
    """`FACE STRIP (log only): 13 crops, eye soft T01 T26, warped none; labels review/face_labels_x.json`."""
    crops = strip.get("crops") or []
    if not crops:
        return "FACE STRIP: no crops (no detector, or no take in the cut)"
    words = {k: " ".join(strip.get(k) or []) or "none" for k in ("soft", "warped")}
    return (f"FACE STRIP (log only): {len(crops)} crops, eye soft {words['soft']}, warped {words['warped']}; "
            f"strip review/{strip_name(sha8)}, owner labels review/{labels_name(sha8)}")
