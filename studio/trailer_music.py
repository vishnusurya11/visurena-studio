"""The cue, which is the timeline.

Three measured facts about MiniMax Music 3 shape everything here:

1.  SECTION COUNT sets length, not any duration field -- the text encoder is
    an autoregressive model that decides the structure before diffusion runs,
    and `build_prompt()` contains no duration token at all.  ~11.1s a section.
2.  `duration` is a SECOND SEED.  Changing it re-rolls the whole composition
    (waveform correlation between takes at 30/60/150 was -0.03).  So it is
    pinned, and iteration happens on seed alone.
3.  CAPTION PROSE sets dynamic shape.  One word decided it: a cue told
    "relentless throughout" came back at 4.0 LU range with 3 stopdowns; the
    same plan told "starts near-silent... hard full stop" came back at 9.7 LU
    with 9.  A trailer needs the second one -- Lieu's rule is that the stops
    are what make the fast parts feel fast.

Vocals are excluded by SAYING NOTHING ABOUT VOICES, never by negating them.
Negation ("no vocals, no backing vocals") reliably produces humming.
"""
from __future__ import annotations

SECONDS_PER_SECTION = 11.1
"""Measured mean across cues: 96.08s/9 and 99.87s/9."""

PINNED_DURATION = 150
"""Never vary this.  It is a seed, not a ceiling."""

SECTIONS: list[tuple[str, str]] = [
    ("Intro", "a single sustained low note, room tone"),
    ("Verse", "low strings ostinato enters, quiet"),
    ("Build", "a solo violin rises over the ostinato"),
    ("Pre-Chorus", "taiko hits land on the downbeats"),
    ("Chorus", "full brass swell, strings high"),
    ("Bridge", "drop away to near silence, one instrument"),
    ("Final Build", "everything returns, accelerating"),
    ("Hit", "one impact, then silence"),
    ("Outro", "a single low note, fading"),
]
"""Nine sections ~= 100s.  The [Bridge] near-silence is where a line over
black goes, and [Hit] is what the title card is cut to."""


def section_count_for(seconds: float) -> int:
    """How many sections to ask for to land near a target length."""
    return max(1, round(seconds / SECONDS_PER_SECTION))


def lyrics_plan(sections: list[tuple[str, str]] | None = None) -> str:
    """The tag-only lyric plan.  Parentheticals ARE submitted as lyric text --
    normalize_lyrics only lowercases the [tags] -- so they stay terse."""
    return "\n\n".join(f"[{tag}]\n({note})" for tag, note in (sections or SECTIONS))


def caption(palette: str, bpm: int = 92, key: str = "D minor") -> str:
    """A caption in MiniMax's own label grammar, narrating the arc.

    Note it says "entirely instrumental" and then stops -- it never lists the
    voices it does not want.
    """
    return (
        f"Global Metadata: Cinematic Orchestral, Epic Soundtrack, dark orchestral "
        f"trailer cue. {bpm} BPM, {key}. {palette} "
        "Arrangement: starts near-silent with a single sustained low note and room "
        "tone. Low strings ostinato enters underneath. A solo violin rises over it. "
        "Taiko hits land on the downbeats from the halfway point and brass swells "
        "beneath them. The whole arrangement drops away to near silence for one "
        "passage, then returns accelerating, rising to a hard full stop with one "
        "beat of total silence, then a single low impact and a long decay. "
        "Entirely instrumental."
    )
