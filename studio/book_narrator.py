"""The book's narrator: chosen ONCE, before episode 1, and never by a gate.

Jekyll & Hyde ep01 (docs/audit/2026-10-13_jekyll_ep01_review): a third-person
book had no narrator.  The writer wrote `narrator`, G-SPEAKER refused it five
rounds running and printed the cast as its menu, and the writer took
`henry_jekyll` -- the wrong man, in the wrong person, at an octave too high.
No rule, judge or person decided "Jekyll narrates".

DECISION (2026-10-13, the owner said "decide, don't ask"): a third-person book
gets a DEDICATED narrator voice row, `narrator` -- a calm, low storyteller who
is no character of the cast and never on camera -- declared in
`refs/narrator.json` before its first episode.  A first-person book declares
its "I" (a cast member).  A book that declares nothing keeps the narrator its
PUBLISHED episodes share (WotW's `unnamed_first_person_narrator`, Scarlet's
`john_watson`): a shipped episode is a decision the owner shipped.  A book with
neither has no narrator, and the plan STOPS; it never asks the writer to pick.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

FILE = Path("refs") / "narrator.json"
DEDICATED = "narrator"
"""A third-person book's storyteller: a voice row (cast/narrator/), never a cast member."""

UNSET = ("NARRATOR: this book has no declared narrator (refs/narrator.json) and no published "
         "episode establishes one, so the plan stops. The narrator is chosen once for the book, "
         "before episode 1: a third-person book takes the dedicated 'narrator' voice row; a "
         "first-person book declares its 'I'. A gate never picks one.")


class Narrator(BaseModel):
    """refs/narrator.json: who tells this book, in which person, and how he sounds."""
    speaker: str = Field(min_length=1)
    person: Literal["first", "third"]
    on_camera: bool = False
    voice: str = ""
    """What the VOICE lane casts: register and manner, never a model id."""
    decided: str = ""
    why: str = ""


def path_of(book) -> Path:
    return Path(book) / FILE


def declared(book) -> Narrator | None:
    """The book's declaration, or None when it has made none."""
    path = path_of(book)
    return Narrator.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def published_narrators(book) -> list[set[str]]:
    """The narration speakers of every published episode (a youtube.json beside its plan)."""
    out = []
    for plan in sorted(Path(book).glob("episodes/ep*/plan.json")):
        if (plan.parent / "youtube.json").exists():
            doc = json.loads(plan.read_text(encoding="utf-8"))
            out.append({l.get("speaker") for l in doc.get("lines") or [] if l.get("kind") == "narration"})
    return out


def established(book) -> str:
    """The one speaker EVERY published episode narrates with; '' when none or several."""
    sets = [s for s in published_narrators(book) if s]
    common = set.intersection(*sets) if sets else set()
    return next(iter(common)) if len(common) == 1 else ""


def narrator(book) -> str:
    """The declaration's speaker, else the established one; '' means unset."""
    found = declared(book)
    return found.speaker if found else established(book)


def require(book) -> str:
    """The book's narrator, or a STOP before any writer is asked."""
    who = narrator(book)
    if not who:
        raise SystemExit(UNSET)
    return who


def dedicated(voice: str, why: str, decided: str = "") -> Narrator:
    """The declaration of a third-person book: the dedicated storyteller, off camera."""
    return Narrator(speaker=DEDICATED, person="third", on_camera=False, voice=voice, decided=decided, why=why)


def declare(book, doc: Narrator) -> Path:
    """Write refs/narrator.json once; the decision is the book's, not an episode's."""
    path = path_of(book)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc.model_dump(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
