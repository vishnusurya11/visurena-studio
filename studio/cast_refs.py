"""The cast row in `refs.json`: one invariant caption, one state sentence per
wardrobe state, and TWO pictures.

THE SPLIT.  `physical` was carrying a conditional -- "a brown bowler hat, on
his head outdoors and in his left hand indoors" -- into the one sentence a
take prompt marks `fully_preserved`, which tells the model two mutually
exclusive things about the most conspicuous object in the frame.  A still
picture has one state and a take has one state, so the repair is structural:

    physical    invariant, true in every setup, the caption of the BUST
    wardrobe    {"indoor": ..., "outdoor": ...}, chosen by `Setup.state`
    rel_path    the identity BUST, bare-headed, setup-independent
    cards       {"indoor": ..., "outdoor": ...}, the wardrobe-and-props CARDS

Six setups, two states (`review8/wardrobe/eye_labels.json`: criterion,
corridor, lab and bench indoors; cab and gateway outdoors), so the whole book
is three busts and five cards -- eight pictures, reused by the trailer, the
song and every future episode, instead of six setups x three people.

MiniMax's own guide: "One subject may be defined by multiple reference assets",
and its worked example binds one Samoyed to three pictures.  The practical H3
guide splits them the same way -- image 1 is the face and hairstyle, image 2
is "hairstyle, body proportions, wardrobe, and silhouette".
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import trailer_refs

STATES = ("indoor", "outdoor")
"""The wardrobe contract has exactly two states: the hat on the head and the
hat in the hand.  `Setup.state` says which one a setup is in."""
MAX_FACES = 2
REF_SLOTS = 8
"""`video_minimax_h3_r2v_turbo_ref8` has eight reference slots.  Two faces at
two pictures each, plus the plate and the storyboard strip, is six of eight.
Three faces would be 3 x 2 + 2 = 8 exactly, with no room for a second plate,
which is why MAX_FACES stays at 2."""
MODEL, SIZE, QUALITY = "gpt-image-2.5-sunburst", "1024x1536", "high"
"""Portrait, because `ref_image_size = "match"` delivers the reference at the
take's 768x1344 canvas and a landscape card spends most of its pixels on
backdrop at left and right.  `image_spend.ESTIMATES` prices 1024x1536 and
1536x1024 the same $0.08, so the ratio is a free improvement."""


def load(book: Path) -> dict:
    """The book's whole reference record."""
    return json.loads((Path(book) / "refs" / "refs.json").read_text(encoding="utf-8"))


def row(book: Path, who: str) -> dict:
    """One character's row, by the entity id the plan uses.

    A character the book has not bound is a hard error, never an invented
    body: `frames.py` inventing one is how "fair side-whiskers" entered a
    clean-shaven man's record (R2)."""
    for entry in load(book).get("refs", []):
        if entry.get("entity_id") == who and entry.get("kind", "character") == "character":
            return entry
    raise KeyError(f"{who} has no row in refs.json: bind him before you draw him")


def physical(row: dict) -> str:
    """The invariant caption: true in every setup, positive, unconditional."""
    return (row.get("physical") or "").strip()


def wardrobe(row: dict, state: str) -> str:
    """The state sentence, as a clause that follows "he": silence when this
    character is never in this state (Holmes is only ever indoors)."""
    return ((row.get("wardrobe") or {}).get(state) or "").strip()


def traits(row: dict) -> dict:
    """What the local reader saw when it looked at this character's own picture."""
    return (row.get("identity") or {}).get("traits") or {}


def characters(book: Path) -> Path:
    return Path(book) / "refs" / "characters"


def bust(book: Path, who: str) -> Path:
    """The identity picture: face, hair, head, bare-headed, setup-independent."""
    rel = row(book, who).get("rel_path")
    return Path(book) / rel if rel else characters(book) / f"char-{who}.png"


def card(book: Path, who: str, state: str) -> Path | None:
    """The wardrobe-and-props picture for this state, or None when there is none."""
    rel = (row(book, who).get("cards") or {}).get(state)
    if rel:
        return Path(book) / rel
    guess = characters(book) / f"char-{who}_{state}.png"
    return guess if guess.exists() else None


def cast_sheets(book: Path, who: str, state: str) -> list[Path]:
    """The pictures that define `who` in this wardrobe state: the identity BUST
    first, then the wardrobe-and-props CARD, both cited inside one `<Subject>`.

    The bust is always bare-headed.  A hat on the identity picture is the
    mechanism behind the oldest wardrobe bug in this episode -- Holmes wore the
    deerstalker in every lab cell and Watson his bowler, because the sheets
    wear them -- since a hat occludes the hairline, the most discriminative
    region for both the face embedder and H3's reference encoder."""
    face = bust(book, who)
    dressed = card(book, who, state)
    return [face] + ([dressed] if dressed and dressed.exists() else [])


def subject_text(row: dict, state: str) -> str:
    """The `<Subject>` sentence: the invariant caption, then this scene's state.

    Two statements, never a conditional -- nothing has to decide "if" at render
    time because the setup already declared which state it is in."""
    said = wardrobe(row, state)
    if not said:
        return physical(row)
    return f"{physical(row).rstrip('.')}; in this scene he {said}."


def sheet_prompts(row: dict) -> dict[str, str]:
    """Every picture this character needs, as {file stem: prompt}.

    One identity bust plus one card per state he is ever in.  Built from the
    row, never typed on a command line: a hand-typed variant prompt is how
    `char-sherlock_holmes_lab.prompt.txt` came to freeze an outdoor muffler
    round his throat in a heated laboratory."""
    sheet = row.get("sheet") or {}
    same = sheet.get("same", "")
    out = {row["ref_id"]: trailer_refs.bust_prompt(sheet.get("head", ""), same)}
    for state in STATES:
        if said := wardrobe(row, state):
            out[f"{row['ref_id']}_{state}"] = trailer_refs.card_prompt(
                f"He {said}. {sheet.get('garments', '')}".strip(),
                sheet.get("hands", ""), sheet.get("props", ""), same)
    return out
