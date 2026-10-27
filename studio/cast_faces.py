"""G-CAST -- no two BASE sheets of a book's cast are one face.

Jekyll ep03 (retro 2026-10-27, finding 1): the MASTER judge ended flagged on
"identity at gabriel_john_utterson+henry_jekyll: two characters collapse"
(frame medians 0.808 against a wall of 0.75).  Nothing compared the base sheets
to each other, so the fault surfaced at the last gate, where no retake can fix
it.  This is the master's measure read at sheet time: the same embedder
(facenet VGGFace2 over the sheet's largest face, `look.face_embedder`), the
same cosine and the same wall (`identity_gate.DRIFT`, which
`master_eye.collapse_faults` refuses at).  A pair at or above it that holds a
sheet being judged is a HARD fault on that sheet and the sheet ladder climbs; a
pair of two sheets already signed is reported in REPORT, never refused -- a
signed sheet is the owner's.

MEASURED 2026-10-27 on Jekyll's seven bound base sheets (portrait, faces 8-9 %
of the sheet's height): Jekyll-Utterson 0.550, the cast's highest pair
Utterson-Enfield 0.712, nothing at the wall.  On full-figure sheets facenet
does not see the collapse the master saw in the takes' close faces; the gate
agrees with the master by construction and catches a sheet that IS one face
(a redraw on another's seed, a copied picture), not a likeness by hair and jaw.

Each sheet is embedded once: its vector is kept in REPORT under its path with
the sha8 of its bytes, and read again only when the bytes change.
"""
from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from studio import identity_gate
from studio.judges.verdict import Fault
from studio.measure import faces

KIND = "cast_collapse"
WALL = identity_gate.DRIFT
"""The master judge's collapse wall: the two gates agree on what one face is."""
REPORT = "refs/work/cast_faces.json"
"""Every base sheet's vector (by path, with its sha8) and every pair's cosine."""
BASE = "sheet.png"

Embed = Callable[[Path], "np.ndarray | None"]


def base_sheets(book_dir: Path, entities: Iterable[str]) -> dict[str, str]:
    """{who: relpath} of every bound character's base sheet on disk."""
    out = {}
    for who in sorted(entities):
        rel = f"refs/characters/{who}/{BASE}"
        if (Path(book_dir) / rel).is_file():
            out[who] = rel
    return out


def sha8_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def load_report(book_dir: Path) -> dict:
    path = Path(book_dir) / REPORT
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def vector_of(book_dir: Path, rel: str, embed: Embed, kept: dict) -> np.ndarray | None:
    """The sheet's face vector: the kept one while its bytes are unchanged, else embedded now."""
    sha8 = sha8_of(Path(book_dir) / rel)
    row = kept.get(rel) or {}
    if row.get("sha8") != sha8:
        vec = embed(Path(book_dir) / rel)
        row = {"sha8": sha8, "vec": None if vec is None else np.asarray(vec, dtype=float).tolist()}
        kept[rel] = row
    return None if row["vec"] is None else np.asarray(row["vec"], dtype=float)


def vectors(book_dir: Path, sheets: dict[str, str], embed: Embed, kept: dict) -> dict[str, np.ndarray]:
    """{who: vector} for every base sheet with a face; a faceless sheet is never paired."""
    out = {}
    for who, rel in sheets.items():
        vec = vector_of(book_dir, rel, embed, kept)
        if vec is not None:
            out[who] = vec
    return out


def pair_scores(vecs: dict[str, np.ndarray]) -> list[dict]:
    """Every pair once, {a, b, cosine}, highest cosine first."""
    pairs = [{"a": a, "b": b, "cosine": round(faces.cosine(vecs[a], vecs[b]), 3)}
             for a, b in combinations(sorted(vecs), 2)]
    return sorted(pairs, key=lambda p: -p["cosine"])


def later(pair: dict, judged: list[str]) -> str:
    """The pair's sheet the fault names: the one judged, the later-judged when both are."""
    mine = [who for who in (pair["a"], pair["b"]) if who in judged]
    return max(mine, key=judged.index)


def collapses(pairs: list[dict], sheets: dict[str, str], judged: Iterable[str]) -> list[Fault]:
    """A HARD fault per pair at or above WALL that holds a judged sheet, on that sheet."""
    judged, out = list(judged), []
    for pair in [p for p in pairs if p["cosine"] >= WALL and {p["a"], p["b"]} & set(judged)]:
        who = later(pair, judged)
        other = pair["b"] if who == pair["a"] else pair["a"]
        out.append(Fault(kind=KIND, where=sheets[who], evidence={
            "other": sheets[other], "a": pair["a"], "b": pair["b"], "cosine": pair["cosine"], "wall": WALL},
            note=f"two characters collapse: {pair['a']} and {pair['b']} read as one face at sheet time"))
    return out


def write_report(book_dir: Path, kept: dict, pairs: list[dict]) -> Path:
    path = Path(book_dir) / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"wall": WALL, "pairs": pairs, "sheets": kept}, indent=1), encoding="utf-8")
    return path


def default_embed() -> Embed:
    """The LOOK judge's facenet over a whole sheet, built on first use."""
    from studio.judges import look
    return look.face_embedder()


def faults(book_dir: Path, entities: Iterable[str], judged: Iterable[str], embed: Embed | None = None) -> list[Fault]:
    """G-CAST over the bound cast: every base sheet embedded (once), every pair scored
    and reported, a pair over the wall that holds a judged entity faulted."""
    sheets = base_sheets(book_dir, entities)
    if len(sheets) < 2:
        return []                                    # one face is never a pair: no model loaded
    kept = load_report(book_dir).get("sheets") or {}
    vecs = vectors(book_dir, sheets, embed or lazy(default_embed), kept)
    pairs = pair_scores(vecs)
    write_report(book_dir, kept, pairs)
    return collapses(pairs, sheets, judged)


def lazy(build: Callable[[], Embed]) -> Embed:
    """An embedder built only when a sheet is not already kept: a warm cast loads no model."""
    held: list = []

    def embed(picture: Path):
        if not held:
            held.append(build())
        return held[0](picture)
    return embed
