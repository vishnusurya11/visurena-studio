"""G-LINEAGE (C2_verdict #9, ADVISORY): is a cast row's new sheet the same man as
its earlier staged versions?

A same-man redraw on one row was a different man twice in Scarlet: Brigham Young
ep08 against ep10 (head cosine 0.16-0.24, near the cross-person median 0.19) and
Jefferson Hope ep07 against ep09-14 (0.45, the cross-person p95).  Same-man
versions score 0.80-0.96; a separate `_young` row holds about 0.6.

The instrument: the head crop (the top 35 % of a full-body sheet, scaled to 1024),
MTCNN at p > 0.95, the VGGFace2 cosine of the largest face.  A pair under MATCH on
a row with no age-up marker writes an advisory line to `audit/lineage.jsonl`.  It
never refuses: MATCH is calibrated on Scarlet's photoreal sheets only, and the
WotW stylized faces are unmeasured (H8: hard only after their distribution)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

MATCH = 0.60
HEAD_SHARE = 0.35
DETECT_P = 0.95
SIDE = 1024


def head_crop(rgb: np.ndarray) -> np.ndarray:
    """The head region of a sheet: the top 35 % of a full-body (tall) sheet, the
    whole of a bust, scaled so its longer side is 1024."""
    from PIL import Image
    h, w = rgb.shape[:2]
    if h > w * 1.2:
        rgb = rgb[: int(h * HEAD_SHARE)]
    h, w = rgb.shape[:2]
    scale = SIDE / max(h, w)
    return np.asarray(Image.fromarray(rgb).resize((round(w * scale), round(h * scale))))


def head_vector(path: Path, detect, embed):
    """The largest confident face of the head crop as a unit vector, or None."""
    from PIL import Image
    from studio.measure import faces as F
    rgb = head_crop(np.asarray(Image.open(path).convert("RGB")))
    found = [f for f in (detect(rgb) or []) if f["score"] > DETECT_P]
    return embed(rgb, F.largest(found)["box"]) if found else None


def vector_fn():
    """head_vector with the CPU facenet loaded once, for a run that scores many sheets."""
    from studio.measure import faces as F
    detect, embed = F.embedder()
    return lambda path: head_vector(path, detect, embed)


def versions(staged: Path, who: str) -> list[Path]:
    """The row's own content-addressed staged versions (char-<who>[_indoor|_outdoor]_<sha8>.png);
    never another row's (`<who>_young`, `<who>_cabman`), never an unhashed name."""
    pattern = re.compile(rf"char-{re.escape(who)}(?:_(?:indoor|outdoor))?_[0-9a-f]{{8}}\.png")
    return sorted(p for p in Path(staged).glob(f"char-{who}*.png") if pattern.fullmatch(p.name))


def age_up(who: str, row: dict) -> bool:
    """A row that is SUPPOSED to differ: one declared `age_up`, or a `_young` /
    `_child` row -- unless the suffix is simply the person's name (Brigham Young's
    row is `brigham_young`, named "Brigham Young"; the young Drebber's row is
    named "Enoch Drebber, young")."""
    row = row or {}
    if row.get("age_up"):
        return True
    own_name = who.replace("_", " ").title() == (row.get("name") or "").strip()
    return bool(re.search(r"_(young|child)$", who)) and not own_name


def advisories(who: str, new: str, scores: dict[str, float], age_up: bool) -> list[str]:
    """One line per earlier version the new one scores under MATCH against."""
    kind = "age-up noted" if age_up else "different man?"
    return [f"G-LINEAGE {who}: {new} vs {old} head cos {cos:.2f} < {MATCH} -- {kind} (advisory)"
            for old, cos in sorted(scores.items()) if cos < MATCH]


def check(book: Path, who: str, new: Path, earlier: list[Path], row: dict, vector) -> list[str]:
    """Score `new` against every earlier version; append each line under MATCH to
    audit/lineage.jsonl.  An unreadable head is skipped.  Never raises a refusal."""
    from studio.measure import faces as F
    mine = vector(Path(new))
    if mine is None:
        return []
    scores = {Path(p).name: round(F.cosine(mine, v), 3) for p in earlier if (v := vector(Path(p))) is not None}
    lines = advisories(who, Path(new).name, scores, age_up(who, row))
    audit = Path(book) / "audit" / "lineage.jsonl"
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open("a", encoding="utf-8") as out:
        for old, cos in sorted(scores.items()):
            if cos < MATCH:
                out.write(json.dumps({"who": who, "new": Path(new).name, "old": old, "cos": cos,
                                      "age_up": age_up(who, row), "advisory": True}) + "\n")
    return lines
