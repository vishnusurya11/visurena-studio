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


DEAD_DBFS = -60.0
"""A 1-second window under this carries no music; a listener hears a dropout.

MEASURED on episode 6's five delivered tones: plain is dead at 24-25 s, light at
35-40, uneasy at 0-4 AND 18-21, grave at 26-30, thrilling at 18.  Laid from
sample 0, that put 24 of the episode's 159.6 seconds under -60 dBFS -- and
`uneasy`, which opens with five seconds of nothing, is used TWICE."""


def live_blocks(mono, rate: int, floor: float = DEAD_DBFS) -> tuple[list[int], int]:
    """The 50 ms blocks of `mono` that carry music, and the block size."""
    import numpy as np

    step = max(rate // 20, 1)                       # 50 ms
    blocks = len(mono) // step
    live = [i for i in range(blocks)
            if 20 * np.log10(max(1e-9, float(np.sqrt(
                (mono[i * step:(i + 1) * step] ** 2).mean())))) > floor]
    return live, step


def trim_to_music(path, floor: float = DEAD_DBFS):
    """(samples, rate) with the silent head and tail cut off, channels kept.

    `is_dead` cannot find this: it measures the WHOLE generation against its
    target, and a file with a six-second silent tail still integrates on target.
    A per-file loudness check is blind to a hole inside the file."""
    import soundfile as sf

    audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
    live, step = live_blocks(audio.mean(axis=1), rate, floor)
    if not live:
        return audio, rate
    return audio[live[0] * step:(live[-1] + 1) * step], rate


def live_seconds(path, floor: float = DEAD_DBFS) -> float:
    """How many seconds of MUSIC a generation holds, first live block to last.

    MEASURED on episode 10: `light` came back as a 27.7 s file with 10.4 s of
    music in it, -76 dBFS from 11 s on, and integrated -30.5 LUFS against a
    -30.5 target -- on target by the whole-file number and 38 % music by this
    one.  It was laid three times over shots 23-27."""
    import soundfile as sf

    audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
    live, step = live_blocks(audio.mean(axis=1), rate, floor)
    if not live:
        return 0.0
    return round((live[-1] + 1 - live[0]) * step / rate, 3)


def looped(audio, want: int, fade: int):
    """`audio` carried to `want` samples by looping, every tile boundary an
    equal-power crossfade of `fade` samples.

    `np.tile` is a butt joint.  MEASURED on episode 10's master: `uneasy`'s
    trimmed end is its eight-second decrescendo and the tile restarted it at
    its opening bar, at 167.83 s, in the only eleven seconds with nobody
    speaking -- -36.1 to -27.1 LUFS across the joint, spectral flux eleven
    times the local median.  Four of six spans looped; five seams hid under
    speech and the sixth did not.

    Sine/cosine and not sqrt: both are equal-power, but sqrt's slope is
    infinite at zero, and on two tiles of ONE tone -- which are correlated --
    that puts a step at the very start of the fade."""
    import numpy as np

    if len(audio) >= want:
        return audio[:want]
    n = len(audio)
    fade = max(1, min(fade, n // 2))
    up = np.sin(np.linspace(0.0, np.pi / 2, fade, dtype=np.float32))[:, None]
    out = np.zeros((want + n, audio.shape[1]), dtype=np.float32)
    at = 0
    while at < want:
        piece = np.array(audio, dtype=np.float32)
        if at:
            piece[:fade] *= up
        if at + n - fade < want:                    # another tile follows
            piece[-fade:] *= up[::-1]
        out[at:at + n] += piece
        at += n - fade
    return out[:want]


@dataclass(frozen=True)
class Span:
    start: float
    end: float
    tone: str

    @property
    def seconds(self) -> float:
        return round(self.end - self.start, 3)


def tones_for(book) -> dict[str, Tone]:
    """The house tones with the book's own `audio/bed_tones.json` laid over them:
    any tone's style, tags, bpm, key or lufs replaced, or a new tone added.
    Root cause 2026-09-26: every WotW bed was the Holmes violin, "Victorian London"."""
    import json
    from dataclasses import replace
    path = Path(book) / "audio" / "bed_tones.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    out = dict(TONES)
    for name, fields in doc.items():
        out[name] = replace(out[name], **fields) if name in out else Tone(**fields)
    return out


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
    digital silence in the middle of an episode is worse than a repeat.  And the
    loop's own seams get the same crossfade (`looped`): episode 10's tail seam
    at 167.83 s was a butt joint between a decrescendo and an opening bar."""
    import numpy as np
    import soundfile as sf

    if not cut:
        raise ValueError("no spans to compose: an episode needs at least one bed span")
    missing = sorted({s.tone for s in cut} - set(files))
    if missing:
        raise ValueError(f"no bed file for {', '.join(missing)}")

    # TRIMMED TO ITS MUSIC, AND STILL IN STEREO.  This used to read the file
    # whole and `mean(axis=1)` it: episode 6 shipped 24 of 159.6 seconds with no
    # bed at all (uneasy opens on five seconds of nothing and is used twice),
    # and mono-summing cost each tone 3.3-5.1 dB of the level it had just been
    # verified at -- unequally, by L/R correlation, so the designed 3.5 LU arc
    # became 5.5 LU and episode 6 is the only one of six with a mono bed.
    loaded: dict[str, np.ndarray] = {}
    width = 1
    for tone, path in files.items():
        audio, got = trim_to_music(path)
        if got != rate:
            index = np.linspace(0, len(audio) - 1, int(len(audio) * rate / got))
            audio = np.stack([np.interp(index, np.arange(len(audio)), audio[:, c])
                              for c in range(audio.shape[1])], axis=1).astype(np.float32)
        loaded[tone] = audio
        width = max(width, audio.shape[1])
    for tone, audio in loaded.items():
        if audio.shape[1] < width:
            loaded[tone] = np.repeat(audio, width, axis=1)

    fade = int(CROSSFADE_S * rate)
    total = int(round(cut[-1].end * rate))
    track = np.zeros((total + fade, width), dtype=np.float32)


    for n, span in enumerate(cut):
        start = int(round(span.start * rate))
        # Every span but the first reaches BACK by one crossfade, so the two
        # beds overlap across the seam instead of meeting at a point.
        head = fade if n else 0
        want = int(round(span.end * rate)) - start + head
        piece = np.array(looped(loaded[span.tone], want, fade), dtype=np.float32)
        if head:
            ramp = np.sqrt(np.linspace(0.0, 1.0, head, dtype=np.float32))
            piece[:head] *= ramp[:, None]
        if n + 1 < len(cut):
            ramp = np.sqrt(np.linspace(1.0, 0.0, fade, dtype=np.float32))
            piece[-fade:] *= ramp[:, None]
        at = start - head
        track[at:at + len(piece)] += piece

    sf.write(str(out), track[:total] if width > 1 else track[:total, 0], rate)
    return out


DEAD_UNDER = 12.0
"""How far under its target a bed must sit to be a failed generation, in dB.

MEASURED on episode 6's first assemble, five tones in one pass: plain -30.8,
light -30.5, uneasy -28.8, thrilling -27.3 -- all within 0.2 dB of target -- and
grave -58.0 against a -29.0 target.  Four good rolls and one empty one from the
same prose in the same minute: a silent return is a dice roll, not a bad ask.

TWELVE, because `BED_MAX_LIFT_DB` is 6.0: anything the level pass can actually
recover is not dead, and twice that is clear of any bed worth keeping.  The real
failure was 29 dB under."""


def is_dead(loudness: float | None, target: float) -> bool:
    """Is this generation empty rather than merely quiet?

    `None` is NOT dead.  No loudnorm pass means "not measured", which is a
    different thing from "measured and empty", and treating one as the other is
    the fault this repo has found thirteen times."""
    if loudness is None:
        return False
    return loudness < target - DEAD_UNDER
