"""The music bed, per span of the episode rather than one drone for all of it.

OWNER 2026-09-14, after watching episode 5: "make sure audio is not too loud the
BG ... different types based on the context of background thrilling .. normal ..
or something".

MEASURED on the shipped `ep05/cut/master_r2v.mp4` before anything changed:

    speech                               -13.2 LUFS
    bed alone, in an un-ducked gap       -28.0 LUFS   (15 LU under the voice)
    bed inside the voice band 300-3400   -34.9 LUFS   (22 LU under)

By the numbers it is not loud.  What makes it READ as loud is that it never
stops and never changes: one solo violin in D minor, the same phrase shape, for
160 seconds, under a breakfast, a joke, a boast, a flashback and a murder.  A
constant is a thing the ear gives up filtering, and then every scene it lies
under sounds the same temperature.

So both halves of the note are answered by one mechanism: a bed PER SPAN, and
every tone quieter than the single bed was.

THE INSTRUMENT STAYS THE VIOLIN, because Holmes plays one -- the owner's choice
on 2026-09-13, and the episodes have already drawn him with it.  What changes
between tones is the register, the bow, the spacing and what stands underneath.

NO TONE NAMES A VOICE, NOT EVEN TO FORBID ONE.  `music_tone`'s docstring records
what that costs: three delivered trailer cues came back with a vocal stem 3-4 LU
above the mix singing their own stage directions, because a style carrying vocal
descriptors makes the model add one, and a negation is a summons.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

VIOLIN = ("Solo violin, unaccompanied except where stated, recorded at night in a large "
          "panelled room in gaslit Victorian London, an underscore that sits far beneath "
          "everything else and stays there")
"""The one sentence every tone shares, so five beds sound like one instrument in
one room and not like five different records."""


@dataclass(frozen=True)
class Tone:
    style: str
    """Descriptive prose, for YuE2, which was chosen for exactly this control."""
    tags: str
    """A comma-separated tag list, for ACE-Step, which is the default engine."""
    bpm: int
    key: str
    lufs: float
    """Where THIS tone sits.  Measured per generation like the old single bed:
    the level is the constant and the gain is computed from what arrives."""


TONES = {
 "plain": Tone(
    style=(f"{VIOLIN}. In D minor at 56 BPM, played low and quiet on the G and D strings "
           "with long bowed notes far apart and plenty of air between the phrases, a little "
           "rosin near the bridge, never hurried and never rising to a finish. A cello holds "
           "one long note underneath. Ordinary, domestic, patient, almost absent."),
    tags=("sparse solo violin underscore, long low bowed notes on the G and D strings, "
          "wide spaces between phrases, one sustained cello drone underneath, Victorian "
          "London, patient, domestic, unresolved, cinematic, minimal, quiet"),
    bpm=56, key="D minor", lufs=-31.0),
 "light": Tone(
    style=(f"{VIOLIN}. In D major at 76 BPM, played high and dry with short separated "
           "strokes off the string, the phrases small and turning back on themselves, a "
           "pizzicato double bass marking time far underneath. Wry, brisk, unbothered, the "
           "sound of somebody being quietly amused."),
    tags=("light solo violin underscore, short dry spiccato strokes off the string, small "
          "phrases turning back on themselves, distant pizzicato double bass keeping time, "
          "Victorian London, wry, brisk, amused, cinematic, minimal, quiet"),
    bpm=76, key="D major", lufs=-30.5),
 "uneasy": Tone(
    style=(f"{VIOLIN}. In D minor at 60 BPM, one figure repeating with a semitone that "
           "will not resolve, played close to the bridge so the tone is thin and glassy, "
           "the phrases arriving a little before you expect them. A double bass holds a "
           "low note that does not move. Watchful, wrong, withheld."),
    tags=("uneasy solo violin underscore, one repeating figure on an unresolved semitone, "
          "played sul ponticello thin and glassy, a motionless low double bass drone, "
          "Victorian London, watchful, withheld, tension, cinematic, minimal, quiet"),
    bpm=60, key="D minor", lufs=-29.0),
 "grave": Tone(
    style=(f"{VIOLIN}. In C minor at 48 BPM, played very low on the G string with a wide "
           "slow bow and long silences between the phrases, each one falling and stopping. "
           "A cello and a double bass hold one note far underneath. Heavy, still, final, "
           "the sound of a thing that cannot be taken back."),
    tags=("grave solo violin underscore, very low on the G string, wide bow, long silences "
          "between falling phrases, sustained cello and double bass far underneath, "
          "Victorian London, heavy, final, funereal, cinematic, minimal, quiet"),
    bpm=48, key="C minor", lufs=-29.0),
 "thrilling": Tone(
    style=(f"{VIOLIN}. In D minor at 92 BPM, a tight repeating figure on the D and A "
           "strings driving forward without pause, the bow short and hard at the frog, "
           "rising a step at a time. A cello doubles it an octave below and a bass drum "
           "marks the far distance. Urgent, arriving, the floor going out."),
    tags=("driving solo violin ostinato, tight repeating figure on the D and A strings, "
          "short hard bow at the frog, rising stepwise, cello doubling an octave below, "
          "a distant bass drum, Victorian London, urgent, cinematic, tension"),
    bpm=92, key="D minor", lufs=-27.5),
}
"""Every tone sits at or below -25.6, the level two shipped episodes were judged
at, so the whole episode gets quieter and the loudest is kept for the twenty
seconds that earn it."""

DEFAULT = "plain"
"""What an episode with no `beds` block gets -- which is what episodes 1 to 5
shipped, one tone end to end."""

CROSSFADE_S = 2.0
"""How long one tone takes to become the next.  A cut between two beds is an
edit the viewer hears; two seconds is under a phrase and over a click."""


@dataclass(frozen=True)
class Span:
    start: float
    end: float
    tone: str

    @property
    def seconds(self) -> float:
        return round(self.end - self.start, 3)


def tone_style(name: str) -> str:
    """The prose handed to the music model for this tone."""
    if name not in TONES:
        raise ValueError(f"{name!r} is not a bed tone; say one of {tuple(TONES)}")
    return TONES[name].style


def tone_lufs(name: str) -> float:
    if name not in TONES:
        raise ValueError(f"{name!r} is not a bed tone; say one of {tuple(TONES)}")
    return TONES[name].lufs


def spans(beds: list[dict], at: dict[int, float], total: float) -> list[Span]:
    """The episode cut into contiguous tone spans, covering every second of it.

    `beds` is authored in the plan -- `[{"from_shot": 0, "tone": "plain"}, ...]`
    -- because TONE IS A JUDGEMENT AND `section` IS NOT.  "friction" covers both
    a comic invasion of six street boys and a man's hand closing on a woman's
    wrist, so a tone derived from the section label would be confidently wrong
    about one of them."""
    if not beds:
        return [Span(0.0, round(total, 3), DEFAULT)]
    marks = []
    for entry in beds:
        tone, shot = entry["tone"], entry["from_shot"]
        if tone not in TONES:
            raise ValueError(f"{tone!r} is not a bed tone; say one of {tuple(TONES)}")
        if shot not in at:
            raise ValueError(f"bed span names shot {shot}, which this episode does not have")
        marks.append((shot, tone))
    if marks != sorted(marks, key=lambda m: m[0]):
        raise ValueError("bed spans are written in story order; these are out of order")
    marks[0] = (marks[0][0], marks[0][1])
    starts = [0.0] + [at[shot] for shot, _ in marks[1:]]
    ends = starts[1:] + [round(total, 3)]
    return [Span(round(a, 3), round(b, 3), tone)
            for a, b, (_, tone) in zip(starts, ends, marks)]


@dataclass(frozen=True)
class BedPlan:
    spans: list[Span]
    needed: list[str]
    seconds: dict[str, float]


def bed_plan(beds: list[dict], at: dict[int, float], total: float) -> BedPlan:
    """What actually has to be generated: ONE pass per distinct tone, long
    enough for that tone's LONGEST span.

    A tone used twice is generated once and laid twice.  Generating per span
    would pay the GPU twice for the same request and -- worse -- return two
    different performances of one tone, which a viewer hears as two different
    pieces of music arriving for no reason."""
    cut = spans(beds, at, total)
    longest: dict[str, float] = {}
    for span in cut:
        longest[span.tone] = max(longest.get(span.tone, 0.0), span.seconds)
    return BedPlan(cut, sorted(longest), {k: round(v + CROSSFADE_S, 3)
                                          for k, v in longest.items()})


def compose(cut: list[Span], files: dict[str, "Path"], out: "Path", rate: int = 44100) -> "Path":
    """The spans laid into ONE track of exactly the episode's length.

    Places and fades only -- each file is already at its own tone's level, so
    re-normalising here would undo the thing the tones exist for.

    A BUTT-JOINT BETWEEN TWO BEDS IS A CLICK AND A SUDDEN CHANGE OF ROOM, which
    a viewer reads as a mistake rather than as scoring, so every seam is an
    equal-power crossfade of `CROSSFADE_S`.  Equal-power and not linear: two
    uncorrelated beds summed with linear fades dip about 3 dB in the middle of
    the join, which is audible as a hole exactly where attention is.

    A tone used twice is read from ONE file -- episode 6's `uneasy` covers shots
    10-14 and again 20-22.  Generating it twice would pay the GPU twice and
    return two different performances of one tone, heard as two unrelated pieces
    of music arriving for no reason.

    A file shorter than its span is looped rather than left to run out: a hole of
    digital silence in the middle of an episode is worse than a repeat."""
    import numpy as np
    import soundfile as sf

    if not cut:
        raise ValueError("no spans to compose: an episode needs at least one bed span")
    missing = sorted({s.tone for s in cut} - set(files))
    if missing:
        raise ValueError(f"no bed file for {', '.join(missing)}")

    fade = int(CROSSFADE_S * rate)
    total = int(round(cut[-1].end * rate))
    track = np.zeros(total + fade, dtype=np.float32)

    loaded: dict[str, np.ndarray] = {}
    for tone, path in files.items():
        audio, got = sf.read(str(path), dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if got != rate:
            index = np.linspace(0, len(audio) - 1, int(len(audio) * rate / got))
            audio = np.interp(index, np.arange(len(audio)), audio).astype(np.float32)
        loaded[tone] = audio

    for n, span in enumerate(cut):
        start = int(round(span.start * rate))
        # Every span but the first reaches BACK by one crossfade, so the two
        # beds overlap across the seam instead of meeting at a point.
        head = fade if n else 0
        want = int(round(span.end * rate)) - start + head
        audio = loaded[span.tone]
        if len(audio) < want:
            audio = np.tile(audio, int(np.ceil(want / max(len(audio), 1))))
        piece = np.array(audio[:want], dtype=np.float32)
        if head:
            ramp = np.sqrt(np.linspace(0.0, 1.0, head, dtype=np.float32))
            piece[:head] *= ramp
        if n + 1 < len(cut):
            ramp = np.sqrt(np.linspace(1.0, 0.0, fade, dtype=np.float32))
            piece[-fade:] *= ramp
        at = start - head
        track[at:at + len(piece)] += piece

    sf.write(str(out), track[:total], rate)
    return out
