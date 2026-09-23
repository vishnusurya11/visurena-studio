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

Six setups, two states (`docs/calibration/wardrobe_eye_labels.json`: criterion,
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


SHEET_KEYS = ("same", "head", "garments", "hands", "props")
"""What a row must say before a card can be drawn from it.

MEASURED building episode 9: the three Utah lead rows had no `sheet` block, so
`sheet_prompts` built their cards from the wardrobe sentence alone -- 235-253
words against Watson's 307-312, and no "the same black beard" clause to hold
the face -- and said nothing about it.  A thin prompt is not a prompt."""
PRONOUNS = tuple(trailer_refs.PERSONS)


def pronouns(row: dict) -> str:
    """Which words the card template says about this person: the row's
    `pronouns`, or "he" for a row written before the field existed."""
    said = row.get("pronouns")
    if said is None:
        return "he"
    trailer_refs.person(said)
    return said


def sheet_missing(row: dict) -> list[str]:
    """What this row has not said yet, in SHEET_KEYS order; [] when complete.

    `pronouns` is REQUIRED on a row whose cards are not yet drawn.  A row with a
    card on record is old -- its pictures already exist, drawn as "he" -- and
    keeps the default; a row still waiting for its first card is being authored
    now, and the template must not guess who it is drawing."""
    sheet = row.get("sheet") or {}
    missing = [key for key in SHEET_KEYS if not (sheet.get(key) or "").strip()]
    if "pronouns" not in row and not any((row.get("cards") or {}).values()):
        missing.append("pronouns")
    return missing


def sheet_prompts(row: dict) -> dict[str, str]:
    """Every picture this character needs, as {file stem: prompt}.

    One identity bust plus one card per state they are ever in.  Built from the
    row, never typed on a command line: a hand-typed variant prompt is how
    `char-sherlock_holmes_lab.prompt.txt` came to freeze an outdoor muffler
    round his throat in a heated laboratory.  A row that has not said enough is
    REFUSED, naming what is missing, never quietly drawn thin."""
    if missing := sheet_missing(row):
        raise ValueError(f"{row.get('entity_id', '?')}: no prompt can be built, the row's "
                         f"sheet block is missing {', '.join(missing)}")
    sheet, who = row["sheet"], pronouns(row)
    same, subject = sheet["same"], trailer_refs.person(who)["Subject"]
    out = {row["ref_id"]: trailer_refs.bust_prompt(sheet["head"], same, who)}
    for state in STATES:
        if said := wardrobe(row, state):
            out[f"{row['ref_id']}_{state}"] = trailer_refs.card_prompt(
                f"{subject} {said}. {sheet['garments']}", sheet["hands"], sheet["props"],
                same, who)
    return out


def casts_from_sheets(book: Path) -> bool:
    """Does this book cast from ONE SHEET per character (refs/characters/<who>/
    sheet.png) rather than a bust plus a wardrobe card per state?"""
    return any(characters(book).glob("*/sheet.png"))


def sheet_unbound(book: Path, who: str) -> list[str]:
    """Why a one-sheet character is not ready to be staged; [] when bound:
    it has a row in refs.json, and its sheet is on disk."""
    try:
        row(book, who)
    except KeyError as missing:
        return [str(missing).strip('"')]
    if not (characters(book) / who / "sheet.png").exists():
        return [f"{who}: no sheet on disk at refs/characters/{who}/sheet.png"]
    return []


def bound(book: Path, who: str, state: str) -> list[str]:
    """Why this character is NOT ready in this state; [] when bound.

    A book that casts from ONE SHEET per character is bound by its sheets
    (`sheet_unbound`). The rest of this rule is the bust-and-card casting of
    the Scarlet book, and applied to WotW it failed every plan -- 7, 18, 6 and
    24 hard faults on ep06-09 -- so plan_check exited 1 on every episode and
    the exit code stopped meaning anything (audit 2026-09-22, item 3).

    Three facts, each one a fault measured on episode 9: the row has said what
    the cards must show (`sheet`), the row RECORDS a card for this state that is
    on disk (a file the row does not name is a picture nobody wrote a prompt
    for), and the bust has a read-back -- `cast_cards --check` passed it, and it
    has not been redrawn since (`cast_bust --redraw` clears the read-back)."""
    if casts_from_sheets(book):
        return sheet_unbound(book, who)
    try:
        r = row(book, who)
    except KeyError as missing:
        return [str(missing).strip('"')]
    out = [f"{who}: no sheet block on the row (missing {', '.join(m)})"
           for m in [sheet_missing(r)] if m]
    out += card_unbound(book, who, r, state)
    if not traits(r):
        out.append(f"{who}: no read-back on the row: cast_cards --check never passed this "
                   f"bust, or it was redrawn since")
    return out


def card_unbound(book: Path, who: str, r: dict, state: str) -> list[str]:
    """The one reason a state's card is not bound, or none."""
    named = (r.get("cards") or {}).get(state)
    if not named:
        guess = characters(book) / f"char-{who}_{state}.png"
        aside = f"; {guess.name} is on disk and unrecorded" if guess.exists() else ""
        return [f"{who}: no {state} card bound on the row (cards[{state}] is empty{aside})"]
    if not (Path(book) / named).exists():
        return [f"{who}: cards[{state}] names {named} and it is not on disk"]
    return []


def chapter_refusal(book: Path, chapter: int) -> str | None:
    """Why the cast rows on disk may NOT be used for this chapter, or None.

    refs.json holds one chapter's clothes per character; cast_rows.py rewrites
    it per episode and stamps the chapter, and nothing read the stamp -- so a
    retake of episode 8 under chapter 9's rows would dress the wife for a
    journey she has not taken yet (audit 2026-09-22, item 9)."""
    stamped = load(book).get("chapter")
    if stamped is None:
        return "refs.json names no chapter: rebind it with scripts/refs/cast_rows.py"
    if int(stamped) != int(chapter):
        return (f"refs.json holds chapter {stamped}'s cast, not chapter {chapter}'s: run "
                f"scripts/refs/cast_rows.py <book> {chapter} <cast...> first")
    return None
