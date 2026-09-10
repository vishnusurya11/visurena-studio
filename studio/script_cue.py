"""The music, asked FROM the page instead of the page being read out of the music.

This reverses the old dependency, and the reversal is the whole point.  Run 19
derived its shot list from whatever the music generator emitted: the cue's six
sections were dealt to the three movements by count, section 0 happened to run
0.73 s, and the trailer's first act was 1% of its runtime.  A trailer cue's
three-act shape is a story template somebody else already put in -- reading
structure out of it gives you their story, not this book's.

Professional practice is the other way round.  When a custom cue is
commissioned the composer is sent "what you want the music to be doing in each
part of the trailer, the vibe, emotion, tone, energy, pacing" and then "an
outline of the trailer" (Derek Lieu).  The page IS that outline: every beat
already carries a `hear` line -- "the watch stops dead under the line",
"everything stops. one hit, then silence", "the music's biggest hit" -- and
those lines are landmarks, written in seconds, that this module puts on bars.
"""
from __future__ import annotations

import re

from studio.cue_plan import AskedEvent, CueAsk
from studio.music_tone import caption
from studio.trailer_script import TrailerScript

STOP_WORDS = ("stops", "stop", "silence", "silent", "cuts out", "drops out",
              "falls away", "drops away", "nothing")
HIT_WORDS = ("hit", "impact", "slam", "stab", "boom", "crash", "snap")
PULSE_WORDS = ("pulse", "enters", "begins", "ticking", "builds", "riser")
"""What a `hear` line is telling the score to do.  The page writes for a
player, not for a parser, so the reading is deliberately literal: the words
that survive are the ones a composer would act on."""


def bpm_for(page: TrailerScript, beats_per_bar: int = 4) -> int:
    """A tempo whose bar is close to the page's own average beat length, so a
    written beat lands near a bar line rather than across one."""
    mean = page.seconds / max(1, len(page.beats))
    return max(60, min(160, round(60 * beats_per_bar / mean)))


def bars_for(page: TrailerScript, bar: float) -> int:
    """Bars that cover the page, rounded up: the cue may run past the picture
    and be cut, and may never come up short of it."""
    return max(8, -(-int(page.seconds * 100) // int(bar * 100)))


def bar_of(page: TrailerScript, beat, bar: float) -> int:
    """The bar a beat starts on."""
    return int(page.at(beat) / bar)


def event_kind(beat) -> str | None:
    """What this beat asks the score for, read off its own `hear` line."""
    if beat.function == "title":
        return "title_hit"
    heard = (beat.hear or "").lower()
    if any(w in heard for w in STOP_WORDS):
        return "stop" if beat.function in ("turn", "button") else "hole"
    if any(w in heard for w in HIT_WORDS):
        return "hit"
    if any(w in heard for w in PULSE_WORDS):
        return "pulse_in"
    return None


def events_for(page: TrailerScript, bar: float) -> list[AskedEvent]:
    """Every landmark the page wrote, on the bar it falls on.  One event per
    bar: two landmarks inside one bar are one moment to a listener."""
    found: dict[int, str] = {}
    for beat in page.beats:
        kind = event_kind(beat)
        if kind:
            found.setdefault(bar_of(page, beat, bar), kind)
    return [AskedEvent(kind=kind, bar=at) for at, kind in sorted(found.items())]


def ask_for(page: TrailerScript, beats_per_bar: int = 4) -> CueAsk:
    """The cue this page needs: its length, its acts, and its landmarks."""
    bpm = bpm_for(page, beats_per_bar)
    bar = round(60.0 / bpm * beats_per_bar, 4)
    bars = bars_for(page, bar)
    default = CueAsk.for_bars(bars, bar, bpm)
    written = events_for(page, bar)
    title = next((e.bar for e in written if e.kind == "title_hit"), default.title_bar)
    return default.model_copy(update={"events": written or default.events,
                                      "title_bar": title})


def heard_lines(page: TrailerScript) -> str:
    """The page's own sound direction, in order, for the caption to carry."""
    return "\n".join(f"{page.at(b):5.1f}s  {b.hear}" for b in page.beats if b.hear)


def brief(page: TrailerScript, tone=None) -> str:
    """The composer's brief: what the music does in each part of the trailer.

    Written to the page, not to a genre template -- this is the text a trailer
    house sends with its outline when it commissions a cue."""
    ask = ask_for(page)
    if tone is not None:
        # MEASURED: a 200-word prose brief asking for 58 s came back 25.03 s.
        # The six-section caption is what set the length on every cue that
        # measured near its ask, so the page's moments are added to it.
        return (f"{caption(tone)}\n\nTHE MOMENTS THIS CUE IS WRITTEN FOR, in the "
                f"order the picture plays them:\n{heard_lines(page)}")
    return (f"A {page.seconds:.0f}-second trailer cue for '{page.title}', "
            f"{page.genre}, at {ask.bpm} BPM in 4/4.\n"
            f"The trailer has three acts: it opens quiet for "
            f"{page.movement_seconds()['M1']:.0f}s, builds through "
            f"{page.movement_seconds()['M2']:.0f}s, and takes its last "
            f"{page.movement_seconds()['M3']:.0f}s to the biggest moment of the "
            f"piece.\nWhat the music does, moment by moment, as the picture was "
            f"written:\n{heard_lines(page)}")


def spoken_windows(page: TrailerScript) -> list[tuple[float, float]]:
    """Where the trailer SPEAKS, so the bed can leave the line room.

    Not a duck: the trade's own move is that the music STOPS on the downbeat so
    the line lands ("cymbal sucks").  Run 19 ducked a bed under four lines and
    the owner still heard no dialogue."""
    return [(page.at(b), round(page.at(b) + b.seconds, 2))
            for b in page.beats if b.line]


def caption_words(text: str) -> int:
    return len(re.findall(r"\S+", text))
