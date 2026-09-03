"""Asking the music model for the book it is actually scoring.

The caption was one 109-word paragraph, byte-identical for every title but for
a pasted VISUAL palette -- "soot-black, gaslight amber and cold London grey" --
sitting in the slot a MUSIC palette belonged.  The two variables were conflated
because they share a word.  Genre, period, instrumentation and emotional arc
were never inputs, so a Victorian procedural and a gothic horror were the same
prompt separated by a seed, and the fitness metric that chose between takes had
no term referring to the book at all.

Measured consequences on the cue that shipped with A Study in Scarlet: the solo
violin the caption asked for is not in the file (2-8 kHz sits 21 dB below the
mids), the piece plays at ~105 BPM against a requested 92, and its loudness
peaks at 60% where the cut wants its climax at 85-90%.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

EXECUTABLE_TAGS = ("Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus",
                   "Bridge", "Instrumental", "Solo", "Outro")
"""The only section tags the model executes.

`[Build]`, `[Final Build]` and `[Hit]` are not among them.  The model falls
back to guessing from position, which is why "nine sections is about a hundred
seconds" delivered 78.5s, 101.75s, 114.0s, 114.55s and 139.75s -- a 78% spread
on what was documented as the one deterministic length control.
"""

ARC = [
    ("Intro", "a single sustained low note beneath room tone, almost nothing"),
    ("Verse", "the lead states its figure plainly, unhurried, alone"),
    ("Pre-Chorus", "a low pulse enters underneath and will not let the figure go"),
    ("Chorus", "the first full statement, the whole ensemble committed"),
    ("Instrumental", "the figure inverted, answered by a second instrument"),
    ("Bridge", "everything falls away to one instrument in a bare room"),
    ("Solo", "the lead alone, slower, exposed, the piece at its most naked"),
    ("Post-Chorus", "everything returns at once, accelerating, harder than before"),
    ("Outro", "a hard full stop, one beat of silence, one low impact, long decay"),
]
"""Nine executable sections carrying quiet -> build -> hit -> aftermath."""

SYLLABLES_PER_SECOND = 2.4
"""Content fill the model expects.  Below ~0.8x it finishes the sheet early and
noodles; the old plan ran 0.35x, which is the likely mechanism behind a cue
that came back 78.5s when 100s was asked for."""


@dataclass(frozen=True)
class Tone:
    """What this book should sound like, and why.

    Authored once per book, beside the reference sheets, for the same reason:
    it is a decision about the work that should not be re-made per render.
    """

    genre: str
    bpm: int
    key: str
    scale: str
    lead_instrument: str
    percussion: str
    sonics: str
    progression: str
    imagery: str
    instruments: str


def load_tone(book: Path) -> Tone:
    """The book's authored music tone.  Absent is an error, not a default."""
    path = book / "trailer" / "music" / "tone.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist; a cue cannot be tone-matched to a book "
            f"whose tone has never been written down")
    return Tone(**json.loads(path.read_text(encoding="utf-8")))


def sections_for(count: int) -> list[tuple[str, str]]:
    """`count` sections from the arc, all executable tags."""
    if count >= len(ARC):
        return list(ARC)
    keep = [0] + sorted(range(1, len(ARC) - 1))[:count - 2] + [len(ARC) - 1]
    return [ARC[i] for i in keep[:count]]


def lyrics_plan(sections: list[tuple[str, str]],
                intended_seconds: float = 100.0) -> str:
    """The tag-and-parenthetical sheet, padded to the fill the model expects.

    Parentheticals ARE submitted as lyric text, so they stay descriptive rather
    than sung -- but they must be long enough.  A sheet at a third of the
    expected fill leaves the model with nothing to do and it stops early.
    """
    target = SYLLABLES_PER_SECOND * intended_seconds / max(len(sections), 1)
    return "\n\n".join(f"[{tag}]\n({_pad(note, target)})" for tag, note in sections)


def _pad(note: str, target_syllables: float) -> str:
    """Lengthen a section note toward the fill the model expects."""
    tail = (" holding its shape, the room audible around it, nothing hurried, "
            "the same idea turned once more before it moves on")
    text = note
    while _syllables(text) < target_syllables:
        text += tail
    return text


def _syllables(text: str) -> int:
    return sum(len(word) // 3 + 1 for word in text.split())


def caption(tone: Tone) -> str:
    """MiniMax's three-heading caption grammar, written from this book's tone.

    Routes on GENRE, groove and instrumentation.  "Cinematic", "dark" and
    "epic" are modifiers, not genre families, and a caption that opens on them
    is asking for the average of everything.
    """
    return "\n\n".join([
        "### Global Metadata",
        f"Basic Attributes: bpm is {tone.bpm}. key is {tone.key}, and scale is "
        f"{tone.scale}. {tone.genre}.",
        f"Global Emotional Progression: {tone.progression}",
        f"Application Scenarios & Imagery: {tone.imagery}.",
        f"Sonics & Production Profile: {tone.sonics}.",
        "### Vocal Details",
        f"This piece is instrumental. The lead is {tone.lead_instrument}.",
        "### Arrangement",
        f"Instrument Lifecycle. Primary: {tone.lead_instrument}. "
        f"Secondary: {tone.instruments}.",
        f"Groove & Foundation Progression: {tone.percussion}. The pulse "
        f"doubles once at the turn and again into the final wave, then stops "
        f"dead on a downbeat.",
        "Embellishments, Textures & Spatial FX: a new colour introduced before "
        "each restatement of the figure; one beat of total silence before the "
        "last impact; the piece ends on a single low note left to die in the "
        "room. The density of events rises steadily through the final third so "
        "that the last quarter carries the most attacks of the whole piece, "
        "then stops.",
    ])
