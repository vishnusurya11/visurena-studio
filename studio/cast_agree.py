"""Does this reference picture show what its caption claims, and one man only?

THE RULE.  `physical` in `refs.json` is the CAPTION OF THE PICTURE, and nothing
else in the repo may describe a character.  A character may not exist in
`refs.json` without a picture read back from that picture, and `physical` must
be positive, unconditional, and true of the picture in front of it.

The brick under it: MiniMax's own reference guide defines a `<Subject N>` as
"reusable visible content", and lists "Clothing, props, interfaces" and
"Scenes, backgrounds, or environments" among the things a Subject covers.  So
everything in a cast sheet is on offer for reuse -- the brick pillar behind
Stamford as much as his coat -- and everything the caption names but the
picture does not show is a thing the model is free to invent.  Hence four
faults, each one measured on the sheets on disk:

    R1 one writer        `char-stamford.prompt` says "fair side-whiskers" and
                         its `physical` says "round clean-shaven face"
    R2 no door that       `char-stamford` has no `identity` block: its sheet was
       skips the read-back made by `frames.py` from a hard-coded constant
    R3 positive          "no gloves" reached every Watson take prompt verbatim
    R4 unconditional     "on his head outdoors and in his left hand indoors"
                         is two mutually exclusive facts in the one sentence
                         marked `fully_preserved`

Free and model-free: PIL and numpy over files already on disk.  Nothing here
calls an API, spends a credit or touches the GPU.  The one predicate that
wants a face model (`face_fraction`, `one_man`) says "not measured" when none
is installed, the same honest shape as `studio/identity_gate`.
"""
from __future__ import annotations

import re
from pathlib import Path

from studio import cast_card, cast_refs, describe

NEGATIONS = re.compile(r"\b(no|not|never|without|nor|neither|lacks?|missing|absent)\b", re.I)
"""MiniMax's ref-mode rule, verbatim: "Do not introduce abstract terms,
negations ... Focus on concrete visual elements actually present ... rather
than what is absent."  `physical` is copied into `subject_definitions`
unchanged, so a negation in the caption is a negation in the prompt."""
CONDITIONALS = re.compile(r"\b(indoors?|outdoors?|when|whenever|if|else|otherwise"
                          r"|either|or in)\b", re.I)
"""A still picture has one state and a take has one state.  The state belongs
in `wardrobe[state]`, chosen by the setup, never in the invariant sentence."""

BACKDROP_LIMIT = 20.0
"""Mean per-channel std of the two outer side strips.  MEASURED on the sheets
on disk: watson 14.1, holmes 14.0, watson_lab 15.0, holmes_lab 13.0, and
STAMFORD 28.6 -- a brick pillar and the studio flat's edge double it."""
SIDE_STRIP = 0.12
SUBJECT = 45.0
"""Colour distance from the backdrop tone at which a pixel is the man, not the
wall.  MEASURED: at 45, `char-john_watson_lab.png`'s bottom row is 19.6 %
subject -- the bowler and the left hand run off the frame."""
FOOT = 24
"""Rows of air the lowest hand must stand above."""
CLEAR = 0.02
"""Film grain crosses any threshold somewhere; two per cent of the foot band
is grain, a fifth of it is a hand."""
BUST_FACE, CARD_FACE = 0.40, 0.15
"""Face-box height over frame height.  The bust exists to hand the reference
encoder a face; the card exists to hand it a wardrobe, and still has to be
recognisably the same man."""


# ---- the text ----------------------------------------------------------------

def positive(physical: str) -> list[str]:
    """The negating words in a physical description, in the order they appear."""
    return [m.group(1).lower() for m in NEGATIONS.finditer(physical or "")]


def unconditional(physical: str) -> list[str]:
    """The conditional words: every one is a second state smuggled into the
    invariant sentence."""
    return [m.group(1).lower() for m in CONDITIONALS.finditer(physical or "")]


# ---- the picture, measured -----------------------------------------------

def _pixels(path: Path):
    """One picture as a float RGB array."""
    import numpy as np
    from PIL import Image

    return np.asarray(Image.open(path).convert("RGB"), dtype=float)


SHOULDER = 0.60
"""How far down the frame the backdrop is still backdrop.

A BUST FRAMES HEAD AND SHOULDERS, so the shoulders reach the side edges near the
bottom by construction, and a broad man's reach them sooner.  Reading the whole
strip therefore measures the MAN and calls him a second room.  MEASURED on
`char-john_rance.png`, drawn against a plainly flat grey seamless:

    top third    left std  7.3   right std  7.8
    middle       left std  5.0   right std 12.7
    bottom third left std 38.8   right std 39.1     <- his tunic
    whole strip  left std 32.7   right std 39.2     -> refused at 20.0

The same complaint stands against `char-unnamed_retired_marine_sergeant.png`
(35.3, whose record says "broad, thick-set, heavy square shoulders") and
`char-stamford.png` (28.6): the fault scales with how wide the character is,
which is a property of the person and not of the plate."""


def side_strips(path: Path, frac: float = SIDE_STRIP, down: float = SHOULDER):
    """The two outer vertical strips of the frame ABOVE THE SHOULDER LINE.

    The backdrop is measured at the edges because that is where a sheet keeps
    what it should not have: the brick pillars behind Stamford stand at both
    sides of frame, with the man himself down the middle.  It is measured only
    in the upper part because below that the edges are the subject."""
    import numpy as np

    pixels = _pixels(path)
    width = max(int(pixels.shape[1] * frac), 1)
    tall = max(int(pixels.shape[0] * down), 1)
    top = pixels[:tall]
    return np.concatenate([top[:, :width], top[:, -width:]], axis=1)


def backdrop_std(path: Path, frac: float = SIDE_STRIP) -> float:
    """Mean per-channel standard deviation of the side strips: the number."""
    strips = side_strips(path, frac).reshape(-1, 3)
    return round(float(strips.std(axis=0).mean()), 1)


def plain_backdrop(path: Path, limit: float = BACKDROP_LIMIT) -> bool:
    """True when the side strips are one flat tone."""
    return backdrop_std(path) < limit


def backdrop_tone(path: Path):
    """The colour of the backdrop: the median of the side strips."""
    import numpy as np

    return np.median(side_strips(path).reshape(-1, 3), axis=0)


def bottom_share(path: Path, margin: int = FOOT, distance: float = SUBJECT) -> float:
    """The share of the bottom `margin` rows that is subject rather than backdrop."""
    import numpy as np

    pixels = _pixels(path)
    foot = pixels[-max(margin, 1):]
    far = np.sqrt(((foot - backdrop_tone(path)) ** 2).sum(axis=2))
    return round(float((far > distance).mean()), 4)


HAND_BAND = 0.45
"""How much of the foot band's OUTER THIRDS may be subject before a hand is
running off the frame.

THE CENTRE OF THAT BAND IS THIGHS, BY DESIGN.  A card is framed "head to
mid-thigh" -- the prompt says so -- so the body reaches the bottom edge down the
middle of every correct card.  Reading the whole width therefore fails all of
them.  Measured over every card on disk:

    card                        whole   outer thirds   centre
    g_lestrade_indoor           0.471          0.320    0.773
    john_rance_indoor           0.330          0.155    0.678
    john_watson_indoor          0.291          0.112    0.649
    sherlock_holmes_indoor      0.339          0.151    0.712
    tobias_gregson_indoor       0.338          0.140    0.732
    marine_sergeant_indoor      0.683          0.640    0.767

Five well-framed cards sit at 0.112-0.320 in the outer thirds; the one the cast
gate has always complained about sits at 0.640.  Hands hang OUTBOARD and legs
run CENTRAL, so the outer thirds are where the question actually lives."""


def hands_clear(path: Path, margin: int = FOOT, limit: float = HAND_BAND) -> bool:
    """True when the bottom corners are clear -- no hand running off the frame.

    "Both hands entirely inside the frame" is the card's whole job: a hand that
    leaves the frame is a hand the model may draw any way it likes.  It is asked
    at the SIDES because that is where hands hang; the middle of the bottom edge
    is the thighs the framing asks for."""
    import numpy as np

    pixels = _pixels(path)
    foot = pixels[pixels.shape[0] - margin:]
    far = np.sqrt(((foot - backdrop_tone(path)) ** 2).sum(axis=2)) > SUBJECT
    third = max(pixels.shape[1] // 3, 1)
    outer = np.concatenate([far[:, :third], far[:, -third:]], axis=1)
    return float(outer.mean()) <= limit


# ---- the picture, where a face model is installed -------------------------

def detector():
    """The face-box reader, or None when no face model is installed.

    Same shape as `identity_gate._backend`: the structural predicates above are
    always available, and the ones that need a model say "not measured"
    instead of passing silently."""
    try:                                       # pragma: no cover - not installed here
        from facenet_pytorch import MTCNN
    except Exception:
        return None
    return lambda path: _mtcnn_boxes(MTCNN(keep_all=True), path)   # pragma: no cover


def _mtcnn_boxes(model, path: Path) -> list[tuple[float, float, float, float]]:
    """(x, y, w, h) per detected face."""    # pragma: no cover - needs the model
    from PIL import Image

    boxes, _ = model.detect(Image.open(path).convert("RGB"))
    return [] if boxes is None else [(x1, y1, x2 - x1, y2 - y1) for x1, y1, x2, y2 in boxes]


def faces_in(path: Path, detect=None) -> list[tuple[float, float, float, float]]:
    """Every face box in one picture; empty when no model is installed."""
    read = detect or detector()
    return list(read(path)) if read else []


def one_man(path: Path, detect=None) -> bool:
    """Exactly one face in the frame.

    The cast sheet is the one picture that must not contain a crowd, because
    `retention_analysis` marks it `fully_preserved` and there is no way to say
    "preserve the man, discard the room behind him" without a negation."""
    return len(faces_in(path, detect)) == 1


def face_fraction(path: Path, detect=None) -> float:
    """The tallest face box's height over the frame height."""
    boxes = faces_in(path, detect)
    if not boxes:
        return 0.0
    return round(max(h for _, _, _, h in boxes) / _pixels(path).shape[0], 3)


def face_ok(path: Path, kind: str, detect=None) -> bool:
    """True when the face is big enough for this kind of picture to copy."""
    floor = BUST_FACE if kind == "bust" else CARD_FACE
    return face_fraction(path, detect) >= floor


# ---- the text against the picture's own read-back -------------------------

SLOTS = ("facial_hair", "headgear", "hair_colour", "hair_length", "complexion", "build")
"""The trait slots the read-back and the caption both have an opinion about."""
ASSERTS_NONE = ("headgear",)
"""A caption that names no hat is CLAIMING a bare head, because the bust is
bare-headed by rule.  Silence in every other slot is silence, not a claim."""
BUILD_WORDS = {"build", "figure", "lath", "thin", "lean", "spare", "stout",
               "stocky", "portly", "heavy-set", "thickset", "burly", "slight"}
OBJECTS = dict(cast_card.OBJECT, build=BUILD_WORDS,
               hair_colour=cast_card.OBJECT["hair"], hair_length=cast_card.OBJECT["hair"])
"""Which words mean a clause is talking about a slot's OBJECT at all --
`cast_card.OBJECT`, so the vocabulary has one writer.  Without it "dark hair
swept back" reads as a dark complexion."""


def clause_for(slot: str, text: str) -> str:
    """The clauses of a description that talk about one slot's object."""
    words = OBJECTS.get(slot, set())
    parts = re.split(r"[;,.]", text or "")
    return " ".join(p.strip() for p in parts
                    if words & set(re.findall(r"[a-z]+", p.lower())))


def reading(slot: str, text: str) -> str:
    """The vocabulary value this text names for one slot, or '' for silence."""
    said = clause_for(slot, text)
    if not said:
        return "none" if slot in ASSERTS_NONE else ""
    try:
        return describe.nearest(slot, said)
    except ValueError:
        return "none" if slot in ASSERTS_NONE else ""


def alike(slot: str, said: str, seen: str) -> bool:
    """True when the sheet reader would call these two readings the same thing.
    A deerstalker reads as a cap and pale reads as fair (`describe.NEIGHBOURS`)."""
    return said == seen or frozenset((said, seen)) in describe.NEIGHBOURS


def agrees(physical: str, wardrobe: dict, traits: dict) -> list[str]:
    """The trait slots where the text and the picture's own read-back disagree.

    The text a picture is read against is its caption PLUS its state sentences:
    the hat is on the card, never in the invariant caption."""
    said_text = " ".join([physical or ""] + list((wardrobe or {}).values()))
    out = []
    for slot in SLOTS:
        seen = (traits or {}).get(slot)
        if not seen or seen == "unclear":
            continue
        said, shown = reading(slot, said_text), describe.nearest(slot, seen)
        if said and not alike(slot, said, shown):
            out.append(f"{slot}: the text says {said}, the picture says {shown}")
    return out


# ---- the whole check -----------------------------------------------------

def text_complaints(row: dict) -> list[str]:
    """Everything wrong with one character's words."""
    out = [f"physical negates ({w!r}): name what IS there instead (R3)"
           for w in positive(row.get("physical", ""))]
    out += [f"physical is conditional ({w!r}): the state belongs in wardrobe[state] (R4)"
            for w in unconditional(row.get("physical", ""))]
    if row.get("prompt"):
        out.append("prompt is stored beside physical (R1): it is derived by "
                   "character_prompt(physical, palette), never kept")
    traits = cast_refs.traits(row)
    if not traits:
        return out + ["no read-back: this sheet never passed the cast gate"]
    # `identity.traits` is the BUST's read-back, and the bust is bare-headed by
    # rule, so it is read against the invariant caption ALONE: a bowler named in
    # a state sentence must not excuse a bowler worn on the identity picture.
    return out + agrees(row.get("physical", ""), {}, traits)


FLOOR_LENGTH = re.compile(
    r"\b(?:skirt|dress|gown|nightgown|cassock|robe|petticoat|greatcoat|cloak|habit)\b"
    r"[^.;]{0,60}?\bto the (?:floor|ground|boot|boots|ankle|ankles|instep|hem)\b"
    r"|\bfloor[- ]length\b|\bfull[- ]length (?:skirt|dress|gown|habit)\b"
    r"|\b(?:bombazine|crinoline|bustle) (?:dress|gown|skirt)\b", re.I)
"""A contract that says the garment reaches the floor.

Anchored to a GARMENT word and a HEM word together, so "the key light spills to
the floor" is lighting and not a hem."""


def floor_length(row: dict | None) -> bool:
    """Does this character's own contract say the garment reaches the floor?

    `hands_clear` reads the bottom OUTER THIRDS, and its calibration table is
    six cards that are all men in jackets and trousers (0.112-0.320, against the
    0.640 it was built to catch).  A floor-length dress is WIDE AT THE HEM and
    fills those corners because that is what the garment does -- measured at
    0.736 on Madame Charpentier and 0.812-0.843 on Mrs Sawyer, all three with
    both hands plainly inside the frame and nothing cut off.

    So the instrument says where it does not apply, rather than being softened
    for everyone.  A man whose hand runs off the frame still fails at exactly
    the threshold he always did."""
    if not row:
        return False
    said = " ".join([*(row.get("sheet") or {}).values(),
                     *(row.get("wardrobe") or {}).values()])
    return bool(FLOOR_LENGTH.search(said))


def picture_complaints(path: Path, kind: str, detect=None, row: dict | None = None) -> list[str]:
    """Everything wrong with one picture, measured."""
    if not Path(path).exists():
        return [f"{Path(path).name}: the row names this picture and it is not on disk"]
    out = []
    if not plain_backdrop(path):
        out.append(f"{path.name}: backdrop std {backdrop_std(path)} over {BACKDROP_LIMIT}; "
                   f"the frame holds more than one flat wall")
    if kind == "card" and not hands_clear(path):
        if floor_length(row):
            # NOT SILENCE.  An unmeasured check that reads as a pass is this
            # repo's most-found fault; the row says which rule stood down.
            out.append(f"{path.name}: bottom corners {bottom_share(path):.1%} subject, "
                       f"NOT MEASURED -- the contract says the garment reaches the floor, "
                       f"so the outer thirds cannot answer for the hands")
        else:
            out.append(f"{path.name}: the bottom {FOOT} rows are {bottom_share(path):.1%} "
                       f"subject; a hand or a hat runs off the frame")
    read = detect or detector()
    if read:                                              # pragma: no cover - needs a model
        out += _face_complaints(path, kind, read)
    return out


def _face_complaints(path: Path, kind: str, detect) -> list[str]:
    """The two predicates that need a face model."""   # pragma: no cover
    out = []
    if not one_man(path, detect):
        out.append(f"{path.name}: {len(faces_in(path, detect))} faces; a cast sheet holds one")
    if not face_ok(path, kind, detect):
        floor = BUST_FACE if kind == "bust" else CARD_FACE
        out.append(f"{path.name}: face {face_fraction(path, detect):.2f} of frame "
                   f"height, under {floor} for a {kind}")
    return out


def promise_complaints(book: Path, who: str) -> list[str]:
    """R5 -- a wardrobe state that promises clothes must have a picture that shows
    them, and a drawn card must have a line that describes it.

    `check` measured each state's card `if card:`, so a state with a written
    wardrobe line and no card on disk was skipped in SILENCE.  That silence is
    where three parts of this book drifted apart: `Setup.state` calls the cab
    outdoor, `wardrobe["outdoor"]` promises Watson a brown bowler, and no
    `char-john_watson_outdoor.png` was ever drawn -- so `cast_sheet` falls
    through to the bust, which is bare-headed by rule.

    Nothing looked wrong only because the wardrobe line reaches neither the sheet
    prompt nor the take prompt.  Connect any one of the three and the words
    contradict the picture; that is the mechanism behind episode 3's `_bench`
    muffler.  A promise nobody can keep should not be written down."""
    row = cast_refs.row(book, who)
    said = row.get("wardrobe") or {}
    out = []
    for state in cast_refs.STATES:
        line, found = (said.get(state) or "").strip(), cast_refs.card(book, who, state)
        # `cast_refs.card` returns a row-named path WITHOUT checking it exists, so
        # that `picture_complaints` can say "the row names this picture and it is
        # not on disk".  A promise is kept by a picture, not by a filename.
        card = found if found and Path(found).exists() else None
        if line and not card:
            out.append(f"{who} wardrobe[{state}] promises {line[:40]!r} and no card shows it: "
                       f"the bust is what gets passed, and the bust is bare-headed (R5)")
        elif card and not line:
            out.append(f"{who} has a {state} card and no wardrobe line: a picture no prompt "
                       f"can describe (R5)")
    return out


def check(book: Path, who: str, detect=None) -> list[str]:
    """Every complaint about one character's text and pictures.

    An empty list means the caption and the picture are the same statement."""
    row = cast_refs.row(book, who)
    out = text_complaints(row)
    out += promise_complaints(book, who)
    out += picture_complaints(cast_refs.bust(book, who), "bust", detect, row)
    for state in cast_refs.STATES:
        card = cast_refs.card(book, who, state)
        if card:
            out += picture_complaints(card, "card", detect, row)
    return out
