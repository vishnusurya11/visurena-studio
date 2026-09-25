"""LOOK -- the sheet judge (refs/04).  Measures list, code judges, and the
verdict is a pass or, at the terminal rung, a flag; never a park.

The rows, per decision 2026-09-24 (judges replace the eye) §2, LOOK:

    must_noun    look_back: a noun the prompt asked for that no seen phrase carries   HARD
    lettering    EasyOCR: any RECOGNISED string on a sheet (no insert exemption)      HARD
    extra_limb   DWPose: more wrists or ankles than two per head                       HARD
    lookalike    trait cards fewer than DISTINCT_AT traits apart                       HARD
    identity     facenet sheet-vs-sheet cosine at or above STRANGER                    HARD
    style        DINOv3 cosine to the pack's own place pictures under STYLE_OUTLIER    flag
    voice        the cast voice sheet's nearest rival at or above SAME_SPEAKER         flag
    unread       a read that would not parse, or a card that cannot vouch             flag

A HARD row fails the verdict and the sheet ladder climbs; a flag rides in the
faults beside the pass (two books of style evidence is a flag's worth; a
redraw cures no voice).  Confidence is the share of reads that were readable.

Every reader is injectable and the defaults are lazy: `reader(picture,
question) -> str` (the local VLM; the trait card is asked through the same
reader with `describe.prompt_for()`), `embed(picture) -> vec | None` (facenet,
the largest face), `ocr(picture) -> EasyOCR results`, `keypoints(picture) ->
DWPose frames`, `style_embed(picture) -> vec` (DINOv3).  A judge built without
injection in a test trips the ComfyUI trap in tests/conftest.py.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from studio import cast_home, describe, identity_gate, look_back
from studio.judges import verdict as jv
from studio.judges.verdict import Fault, Verdict
from studio.measure import faces, keypoints as kp, ocr

NAME, VERSION = "look", "1"
HARD = frozenset({"must_noun", "lettering", "extra_limb", "lookalike", "identity"})
STYLE_OUTLIER = 0.5
"""DINOv3 cosine to the mean of the pack's place pictures under which a sheet is
another style.  Two books of evidence (refused 3D sheets vs an approved pack);
a flag, never a refusal, until the bench has more."""
PLACES = "locations"
CHARACTERS = "characters"


def kind_of(path: str) -> str:
    """refs/<kind>/<entity>/<name>.png -> kind."""
    parts = path.split("/")
    return parts[1] if len(parts) >= 4 else ""


def entity_of(path: str) -> str:
    parts = path.split("/")
    return parts[2] if len(parts) >= 4 else ""


def picture_of(book_dir, row: dict) -> Path:
    return Path(book_dir or ".") / row["path"]


# ---- the readers, lazy ---------------------------------------------------------

def face_embedder() -> Callable:
    """facenet over a whole sheet: the vector of its largest face, None without one."""
    from PIL import Image
    detect, embed = faces.embedder()

    def one(picture) -> np.ndarray | None:
        rgb = np.asarray(Image.open(picture).convert("RGB"))
        found = detect(rgb)
        return embed(rgb, faces.largest(found)["box"]) if found else None
    return one


def dino_sheet(picture) -> np.ndarray:
    from PIL import Image
    from studio import take_leak
    return take_leak.dino_embed(np.asarray(Image.open(picture).convert("RGB")))


DEFAULTS: dict[str, Callable[[], Callable]] = {
    "reader": lambda: look_back.vlm_reader, "embed": face_embedder,
    "ocr": lambda: ocr.default_reader(), "keypoints": lambda: kp.estimate, "style_embed": lambda: dino_sheet}


class Tools:
    """The five readers, each built on first use when not injected."""

    def __init__(self, **given):
        self.given = {k: v for k, v in given.items() if v is not None}

    def __call__(self, name: str) -> Callable:
        if name not in self.given:
            self.given[name] = DEFAULTS[name]()
        return self.given[name]


@dataclass
class Reads:
    """What a pass over the rows collected."""
    faults: list[Fault] = field(default_factory=list)
    cards: dict[str, describe.TraitCard] = field(default_factory=dict)
    faces: dict[str, np.ndarray] = field(default_factory=dict)
    styles: dict[str, np.ndarray] = field(default_factory=dict)
    reads: int = 0
    readable: int = 0


# ---- per-row rows ----------------------------------------------------------------

def read_nouns(picture: Path, prompt: str, reader, must, acc: Reads, where: str) -> None:
    """The look-back: the prompt's nouns the picture does not show."""
    acc.reads += 1
    try:
        reading = look_back.read(picture, prompt, reader=reader, must=must)
    except look_back.Unreadable as bad:
        acc.faults.append(Fault(kind="unread", where=where, note=str(bad)[:120]))
        return
    acc.readable += 1
    if reading.missing:
        acc.faults.append(Fault(kind="must_noun", where=where, evidence={"missing": reading.missing}))


def read_card(picture: Path, reader, acc: Reads, where: str) -> None:
    """The trait card, asked through the same reader with describe's own prompt."""
    acc.reads += 1
    try:
        card = describe.parse_card(reader(picture, describe.prompt_for()))
    except ValueError as bad:
        acc.faults.append(Fault(kind="unread", where=where, note=str(bad)[:120]))
        return
    if not describe.verifiable(card):
        acc.faults.append(Fault(kind="unread", where=where, evidence={"known": describe.known(card)},
                                note="the card cannot vouch: too few traits seen"))
        return
    acc.readable += 1
    acc.cards[where] = card


def width_of(picture: Path) -> int:
    from PIL import Image
    with Image.open(picture) as im:
        return im.size[0]


def read_lettering(picture: Path, reader, acc: Reads, where: str) -> None:
    """Any recognised string is lettering; a box alone is not."""
    found = ocr.read(picture, reader=reader)
    if not found:
        return
    strings = [r["text"] for r in ocr.recognised(found, width_of(picture))]
    if strings:
        acc.faults.append(Fault(kind="lettering", where=where, evidence={"strings": strings}))


def read_limbs(picture: Path, estimate, acc: Reads, where: str) -> None:
    for frame in kp.parse(estimate(picture)):
        extra = kp.extra_limbs(frame)
        if extra:
            acc.faults.append(Fault(kind="extra_limb", where=where, evidence={"counts": kp.limbs(frame)},
                                    note="; ".join(extra)))


def voice_fault(book_dir, who: str, where: str) -> Fault | None:
    """The cast voice sheet's measured gate, re-read: a rival at or above SAME_SPEAKER."""
    if book_dir is None:
        return None
    sheet = cast_home.sheet_path(book_dir, who)
    if not sheet.exists():
        return None
    from studio.voice_ear import SAME_SPEAKER
    gates = (json.loads(sheet.read_text(encoding="utf-8")).get("gates") or {})
    nearest = gates.get("nearest_similarity")
    if nearest is not None and float(nearest) >= SAME_SPEAKER:
        return Fault(kind="voice", where=where, evidence={"nearest": gates.get("nearest"), "similarity": nearest,
                                                          "wall": SAME_SPEAKER})
    return None


def read_row(book_dir, row: dict, tools: Tools, must, acc: Reads) -> None:
    """Every row of one judged sheet; a character's face rows only on a character."""
    where, picture = row["path"], picture_of(book_dir, row)
    if book_dir is not None and not Path(picture).exists():
        # pack.jsonl is a log: a row whose picture is gone is a superseded view
        # (a state the bible no longer keeps), not a promise.  Nothing to read;
        # the sheets step is what refuses a BOUND picture that is missing.
        # (No book at all is a stub read: every reader is injected, nothing is opened.)
        return
    read_nouns(picture, row.get("prompt", ""), tools("reader"), must, acc, where)
    read_lettering(picture, tools("ocr"), acc, where)
    if kind_of(where) == CHARACTERS:
        read_card(picture, tools("reader"), acc, where)
        read_limbs(picture, tools("keypoints"), acc, where)
        vec = tools("embed")(picture)
        if vec is not None:
            acc.faces[where] = np.asarray(vec, dtype=float)
        voice = voice_fault(book_dir, entity_of(where), where)
        if voice:
            acc.faults.append(voice)
    if (style := style_of(picture, tools)) is not None:
        acc.styles[where] = style



def style_of(picture, tools: Tools):
    """The style vector, or None when it cannot be measured: the embedding
    workflow is a placeholder until a node emits one (first real run: ComfyUI
    rejected the graph and the whole LOOK judge died on it), and a dead ask on
    the shared GPU is a missing measure, never a crash.  A row without a style
    is simply not compared; the calibrated rows stand."""
    try:
        vec = tools("style_embed")(picture)
    except (RuntimeError, TimeoutError, ValueError) as why:
        return None
    return None if vec is None else np.asarray(vec, dtype=float)

def read_bound(book_dir, row: dict, tools: Tools, acc: Reads) -> None:
    """A row already signed: read only what the new rows are compared against."""
    where, picture = row["path"], picture_of(book_dir, row)
    if book_dir is not None and not Path(picture).exists():
        return                                        # a logged row whose picture is gone: not bound to anything
    if kind_of(where) == CHARACTERS:
        try:
            card = describe.parse_card(tools("reader")(picture, describe.prompt_for()))
            if describe.verifiable(card):
                acc.cards[where] = card
        except ValueError:
            pass
        vec = tools("embed")(picture)
        if vec is not None:
            acc.faces[where] = np.asarray(vec, dtype=float)
    if (style := style_of(picture, tools)) is not None:
        acc.styles[where] = style


# ---- the pairwise rows -------------------------------------------------------------

def lookalikes(judged: list[str], cards: dict[str, describe.TraitCard]) -> list[Fault]:
    """A judged sheet whose card sits under DISTINCT_AT from any card read before it."""
    out, seen = [], [p for p in cards if p not in judged]
    for where in judged:
        for other in seen:
            if where in cards and describe.same_look(cards[where], cards[other]):
                out.append(Fault(kind="lookalike", where=where, evidence={
                    "other": other, "distance": describe.distance(cards[where], cards[other]),
                    "wall": describe.DISTINCT_AT, "shared": describe.shared(cards[where], cards[other])}))
        if where in cards:
            seen.append(where)
    return out


def identities(judged: list[str], vectors: dict[str, np.ndarray]) -> list[Fault]:
    """A judged face at or above STRANGER to any face read before it is the same man."""
    out, seen = [], [p for p in vectors if p not in judged]
    for where in judged:
        for other in seen:
            if where in vectors and (c := faces.cosine(vectors[where], vectors[other])) >= identity_gate.STRANGER:
                out.append(Fault(kind="identity", where=where, evidence={
                    "other": other, "cosine": round(c, 3), "wall": identity_gate.STRANGER}))
        if where in vectors:
            seen.append(where)
    return out


def style_outliers(judged: list[str], styles: dict[str, np.ndarray]) -> list[Fault]:
    """A judged sheet far from the mean of the pack's own place pictures; nothing
    to judge against without a place picture."""
    places = [v for p, v in styles.items() if kind_of(p) == PLACES]
    if not places:
        return []
    centre = np.mean(np.stack(places), axis=0)
    out = []
    for where in judged:
        if kind_of(where) != PLACES and where in styles:
            c = faces.cosine(styles[where], centre)
            if c < STYLE_OUTLIER:
                out.append(Fault(kind="style", where=where, evidence={
                    "cosine": round(c, 3), "wall": STYLE_OUTLIER, "places": len(places)}))
    return out


def judge(book_dir, rows: list[dict], *, bound: list[dict] = (), must=(), reader=None, embed=None,
          ocr=None, keypoints=None, style_embed=None) -> Verdict:
    """The verdict over `rows` (pack rows: path, prompt, seed), compared against
    `bound` rows already signed.  Pass when no HARD fault is listed."""
    tools = Tools(reader=reader, embed=embed, ocr=ocr, keypoints=keypoints, style_embed=style_embed)
    acc = Reads()
    for row in bound:
        read_bound(book_dir, row, tools, acc)
    for row in rows:
        read_row(book_dir, row, tools, must, acc)
    judged = [r["path"] for r in rows]
    faults = acc.faults + lookalikes(judged, acc.cards) + identities(judged, acc.faces) + style_outliers(judged, acc.styles)
    return Verdict(judge=NAME, version=VERSION, passed=not any(f.kind in HARD for f in faults), faults=faults,
                   confidence=jv.confidence(acc.readable, acc.reads), reads=acc.reads)
