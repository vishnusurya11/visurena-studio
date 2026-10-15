"""SHEET-ROW -- does a base sheet show what its row says? (refs/04, owner 2026-10-15)

Jekyll ep01 v2: the girl's row said a small knitted woollen bonnet and a plain grey
pinafore; her sheet drew a black lace bonnet, a black pinafore and hollow solid-black
eyes.  LOOK's look-back asked only for the prompt's NOUNS (a bonnet, a pinafore: both
there), so it passed, and the takes split between the words and the picture.

List-then-judge, the house rule: the local VLM LISTS the headwear, its colour and
material, the main garment's colour and the eyes in a closed vocabulary; code compares
them with the row's own words (the look table's base layers and markers).  A row that
names no colour or material judges nothing on it; a cel knit read as plain cloth is not
a contradiction -- only ANOTHER distinct material is.  Every fault is HARD; an unread
answer is an `unread` row (advisory in LOOK, as every unread there).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from studio import look_table as lt, panel_content as pc
from studio.continuity_spec import Layers, Markers
from studio.judges.verdict import Fault, Verdict

NAME, VERSION = "sheet_row", "1"
COLOURS = {"black": "black", "grey": "grey", "gray": "grey", "charcoal": "grey", "silver": "grey",
           "slate": "grey", "white": "white", "ivory": "white", "cream": "white", "red": "red",
           "crimson": "red", "scarlet": "red", "maroon": "red", "burgundy": "red", "brown": "brown",
           "tan": "brown", "beige": "brown", "khaki": "brown", "fawn": "brown", "blue": "blue",
           "navy": "blue", "green": "green", "yellow": "yellow", "gold": "yellow", "purple": "purple",
           "violet": "purple", "pink": "pink", "orange": "orange"}
"""Colour word -> family.  A compound ("dark-red", "light-brown") reads its colour part."""
DISTINCT = ("knitted", "lace", "felt", "straw", "silk", "fur", "leather", "metal")
MATERIAL_WORDS = {"knit": "knitted", "knitted": "knitted", "crocheted": "knitted", "lace": "lace",
                  "lacy": "lace", "felt": "felt", "straw": "straw", "silk": "silk", "silken": "silk",
                  "fur": "fur", "leather": "leather", "metal": "metal", "steel": "metal", "brass": "metal"}
EYES = ("irises", "small", "hollow", "closed", "hidden")
"""`hollow` is the fault: LARGE round eyes drawn empty black.  `small` is a cel adult's dark dot or slit,
which a first whole-sheet replay read as `solid_black` on 4 of 7 correct Jekyll sheets (2026-10-15)."""
SAME_MATERIAL = {"silk": "felt"}
"""A silk top hat and a felt hat are one read at sheet scale (replay: Jekyll, Lanyon)."""
ADVISORY_KEYS = frozenset({"headwear"})
"""The hat's KIND only flags here: the replay read Hyde's wide-brimmed wideawake as a top hat and the
bobby's bell helmet as a cap; LOOK-STATE already judges the kind by family on every look picture."""
HOLLOW = re.compile(r"\b(blank|empty|hollow|pupilless|irisless|solid[- ]black|black) eyes\b", re.I)
VOCAB = {"headwear": [v for v in Markers.model_fields["headwear"].annotation.__args__ if v],
         "headwear_colour": sorted(set(COLOURS.values())) + ["none"],
         "headwear_material": list(DISTINCT) + ["cloth", "none"],
         "top_colour": sorted(set(COLOURS.values())),
         "eyes": list(EYES)}
NL = chr(10)
EYE_OPTIONS = ("irises (coloured irises or pupils are drawn in the eyes), small (small dark dots or narrow slits), "
               "hollow (large eyes filled completely solid black, with no white, no iris and no highlight), "
               "closed, hidden")
ASK = ("This is a character picture of ONE person. Answer each question with ONE of the allowed "
       "answers and nothing else. Output strict JSON with these keys.\n"
       '"headwear": what is on the head, one of ' + ", ".join(VOCAB["headwear"]) + ".\n"
       '"headwear_colour": its main colour, one of ' + ", ".join(VOCAB["headwear_colour"]) + ".\n"
       '"headwear_material": what it is made of, one of ' + ", ".join(VOCAB["headwear_material"]) + ".\n"
       '"top_colour": the main colour of the outermost garment on the body (dress, pinafore, coat), '
       "one of " + ", ".join(VOCAB["top_colour"]) + "." + NL + '"eyes": one of ' + EYE_OPTIONS + ".")
EYES_ASK = ('This is the head of ONE drawn person. Answer with strict JSON {"eyes": X} where X is one of: '
            + EYE_OPTIONS + ".")
"""Asked of the HEAD crop as well as the whole sheet; `hollow` stands only when both reads agree.
Replays (2026-10-15): the whole sheet read the redrawn girl's blue eyes hollow on one load and
irises on another; the head crop read Poole's white pupilled eyes hollow where the sheet read small;
the lace girl read hollow on both."""
HEAD_SHARE = 0.22
"""The top of a standing figure that holds the head (a child's head is ~1/5 of her height)."""
KINDS = frozenset({"row_headwear_colour", "row_headwear_material", "row_top_colour", "row_eyes"})


def colour_of(words: str) -> str:
    """The family of the first colour word in `words`; '' when it names none."""
    for word in re.findall(r"[a-z]+", (words or "").lower()):
        if word in COLOURS:
            return COLOURS[word]
    return ""


def material_of(words: str) -> str:
    """The first DISTINCT material `words` name ('' for wool, cloth or nothing)."""
    for word in re.findall(r"[a-z]+", (words or "").lower()):
        if word in MATERIAL_WORDS:
            return MATERIAL_WORDS[word]
    return ""


NOT_GARMENT = re.compile(r"\b(boots?|shoes?|slippers?|gloves?|stockings?|socks?|hat|cap|bonnet|scarf)\b", re.I)
CLAUSE = re.compile(r",|;|\band\b|\bover\b|\bwith\b|\bunder\b", re.I)


def garment_colours(top: str) -> set[str]:
    """The colour families the row gives the body's garments, footwear and headwear left out:
    'a grey pinafore over a dark-red blouse, and black boots' -> {grey, red}."""
    return {c for c in (colour_of(part) for part in CLAUSE.split(top or "") if not NOT_GARMENT.search(part)) if c}


def wants(layers: Layers, markers: Markers) -> dict[str, str]:
    """What the row says, in the reader's vocabulary; '' is 'not said'."""
    return {"headwear": markers.headwear, "headwear_colour": colour_of(layers.headwear),
            "headwear_material": material_of(layers.headwear), "top_colour": "|".join(sorted(garment_colours(layers.top))),
            "eyes": "" if HOLLOW.search(f"{layers.face} {layers.other}") else "irises"}


def parse(said: str) -> dict[str, str]:
    """The reader's list, each answer kept only inside its vocabulary; Unreadable when empty."""
    from studio.judges.look_state import unwrap
    got = unwrap(said)
    if not isinstance(got, dict):
        raise pc.Unreadable("the sheet-row read is not an object")
    out = {k: str(got.get(k, "")).lower().strip() for k in VOCAB}
    out = {k: (v if v in VOCAB[k] else "") for k, v in out.items()}
    if not any(out.values()):
        raise pc.Unreadable("the sheet-row read names nothing")
    return out


def differs(key: str, want: str, seen: str) -> bool:
    """Whether the picture contradicts the row on one key.  Unsaid or unread is no
    contradiction; a material contradicts only as ANOTHER distinct material; an eye
    contradicts only as the large hollow eye the row never asked for."""
    if not want or not seen or seen == "none" and key != "headwear":
        return False
    if key == "headwear":
        return lt.family(key, seen) != lt.family(key, want)
    if key == "headwear_material":
        return seen in DISTINCT and SAME_MATERIAL.get(seen, seen) != SAME_MATERIAL.get(want, want)
    if key == "eyes":
        return seen == "hollow"
    return seen not in want.split("|")


def faults_of(seen: dict[str, str], want: dict[str, str], where: str) -> list[Fault]:
    """One HARD fault per key the picture contradicts; `missing` names the row's word
    the sheet ladder's defining-state rung puts first."""
    return [Fault(kind=f"row_{key}", where=where, severity="advisory" if key in ADVISORY_KEYS else "high",
                  evidence={"want": want[key], "seen": seen.get(key, ""), "missing": want[key].split("|")})
            for key in VOCAB if differs(key, want.get(key, ""), seen.get(key, ""))]


def head_box(a) -> tuple[int, int, int, int] | None:
    """(left, top, right, bottom) of the figure's head on a sheet over a plain or graded
    backdrop: per-row backdrop from the side columns, the figure where it departs from it."""
    import numpy as np
    side = np.concatenate([a[:, :16], a[:, -16:]], axis=1).astype(int)
    fg = np.abs(a.astype(int) - np.median(side, axis=1)[:, None, :]).sum(axis=2) > 60
    rows = np.where(fg.mean(axis=1) > 0.01)[0]
    if rows.size == 0:
        return None
    top, height = int(rows[0]), int(rows[-1] - rows[0] + 1)
    band = fg[top: top + max(1, int(height * HEAD_SHARE))]
    cols = np.where(band.any(axis=0))[0]
    return int(cols[0]), top, int(cols[-1]) + 1, top + band.shape[0]


def head_crop(picture: Path) -> Path:
    """The head of the sheet's figure, padded square, written to a temp file; the picture
    itself when it cannot be read or holds no figure."""
    import tempfile
    import numpy as np
    from PIL import Image
    if not Path(picture).exists():
        return Path(picture)
    a = np.asarray(Image.open(picture).convert("RGB"))
    box = head_box(a)
    if box is None:
        return Path(picture)
    left, top, right, bottom = box
    pad = max(right - left, bottom - top) // 4
    import hashlib
    tag = hashlib.sha256(str(Path(picture).resolve()).encode()).hexdigest()[:8]
    out = Path(tempfile.gettempdir()) / "sheet_row" / f"{tag}_head.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a[max(0, top - pad):bottom + pad, max(0, left - pad):right + pad]).save(out)
    return out


def eyes_of(picture: Path, reader: Callable) -> str:
    """The eyes, read on the head crop; '' when the answer names none."""
    try:
        return parse(reader(head_crop(Path(picture)), EYES_ASK)).get("eyes", "")
    except pc.Unreadable:
        return ""


def judge(picture: Path, layers: Layers, markers: Markers, reader: Callable, where: str = "") -> Verdict:
    """The verdict on one base sheet against its row: every contradiction refuses."""
    try:
        whole = parse(reader(Path(picture), ASK))
        head = eyes_of(picture, reader)
        eyes = "hollow" if whole["eyes"] == head == "hollow" else (head or whole["eyes"]).replace("hollow", "")
        seen = {**whole, "eyes": eyes}
        faults = faults_of(seen, wants(layers, markers), where)
    except pc.Unreadable as why:
        faults = [Fault(kind="unread", where=where, note=str(why), severity="advisory")]
    unread = any(f.kind == "unread" for f in faults)
    return Verdict(judge=NAME, version=VERSION, passed=not any(f.severity == "high" for f in faults),
                   faults=faults, confidence=0.0 if unread else 1.0, reads=1)
