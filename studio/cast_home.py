"""One character, one folder.

A character's identity was scattered across four places that only a human knew
were the same person: the dossier in `analysis/characters/<id>.json`, the
reference image in `refs/characters/char-<id>.png`, the voice in
`trailer/main/voice/refs/<id>.wav`, and the emotion clips somewhere under a
production.  Nothing linked them, so nothing could ask "is this character
ready?" -- and a voice built for the trailer could not be reused by the
audiobook, because it was filed under the trailer.

The brick is that a character is ONE THING and belongs in ONE PLACE, at BOOK
level, above any production that borrows it:

    library/<book>/cast/<character>/
        character.json        the dossier
        portrait.png          the face every shot binds to
        voice/
            voice.json        the casting sheet and how it was made
            design.wav        the voice as cast
            angry.wav ...     the same voice, re-performed
            voice_qc.json     what each clip was heard to say

That is also the layout an unattended run needs: `ready(book, character)` can
answer in one stat call, instead of four lookups nobody wrote.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

CAST = "cast"
CARD = "character.json"
PORTRAIT = "portrait.png"
VOICE = "voice"
SHEET = "voice.json"
QC = "voice_qc.json"
DESIGN = "design.wav"


def home(book_dir: Path | str, character: str) -> Path:
    """Where everything about this character lives."""
    return Path(book_dir) / CAST / character


def card(book_dir: Path | str, character: str) -> Path:
    """The dossier: who they are, what they do, what they say."""
    return home(book_dir, character) / CARD


def portrait(book_dir: Path | str, character: str) -> Path:
    """The reference image every shot binds their face to."""
    return home(book_dir, character) / PORTRAIT


def voice_dir(book_dir: Path | str, character: str) -> Path:
    """Every clip of this character speaking."""
    return home(book_dir, character) / VOICE


def clip(book_dir: Path | str, character: str, tag: str = "design") -> Path:
    """One take: `design` as cast, or a feeling re-performed from it."""
    return voice_dir(book_dir, character) / f"{tag}.wav"


def sheet_path(book_dir: Path | str, character: str) -> Path:
    """The casting sheet and the calls that produced the clips."""
    return voice_dir(book_dir, character) / SHEET


def qc_path(book_dir: Path | str, character: str) -> Path:
    """What the gate heard each clip say."""
    return voice_dir(book_dir, character) / QC


def cast_of(book_dir: Path | str) -> list[str]:
    """Every character with a home, in name order."""
    root = Path(book_dir) / CAST
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def ready(book_dir: Path | str, character: str) -> dict[str, bool]:
    """What this character has and has not got yet.

    The question an unattended run has to answer before it casts a shot or
    speaks a line, and the reason the folder exists."""
    return {"card": card(book_dir, character).exists(),
            "portrait": portrait(book_dir, character).exists(),
            "voice": clip(book_dir, character).exists(),
            "checked": qc_path(book_dir, character).exists()}


def missing(book_dir: Path | str) -> dict[str, list[str]]:
    """Who is short of what, across the whole cast."""
    short: dict[str, list[str]] = {}
    for character in cast_of(book_dir):
        gaps = [what for what, got in ready(book_dir, character).items() if not got]
        if gaps:
            short[character] = gaps
    return short


def settle(source: Path, dest: Path, move: bool = False) -> bool:
    """Put one file in its home, without overwriting what is already there."""
    if not source.exists() or dest.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), dest) if move else shutil.copy2(source, dest)
    return True


def gather(book_dir: Path | str, move: bool = False) -> dict[str, list[str]]:
    """Collect a book's scattered character files into their homes.

    Copies by default: the old paths still have readers, and a migration that
    breaks the pipeline to tidy it is a bad trade."""
    book = Path(book_dir)
    brought: dict[str, list[str]] = {}
    for dossier in sorted((book / "analysis/characters").glob("*.json")):
        who = dossier.stem
        got = []
        if settle(dossier, card(book, who), move):
            got.append(CARD)
        if settle(book / f"refs/characters/char-{who}.png", portrait(book, who), move):
            got.append(PORTRAIT)
        if got:
            brought[who] = got
    return brought


def write_sheet(book_dir: Path | str, character: str, body: dict) -> Path:
    """Record how this voice was made, beside the voice itself."""
    dest = sheet_path(book_dir, character)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return dest
