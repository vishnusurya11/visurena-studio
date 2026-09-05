"""The ask, in three readings: a register's bars, the model's caption, the verifier's targets.

A trailer cue is a bar-indexed event list -- pulse in, hole, hit, stop, title
hit -- each pinned to a downbeat.  `ask_for` writes that list for a book's
`Tone` by choosing a register (nine rows, research 03 §4) and placing the
register's events on the bars of a `CueAsk`.  `caption_from` reads the same
list aloud in the music model's grammar: landmarks in section order, bound to
downbeats and entries, the two things the model places on the grid; bar and
second numbers are inert to it (03 §1.1) so the caption carries none.
`verify` reads the list back from a cut map and fills `measured` per event;
`plan_score` is the fraction that landed.  The audio the verifier is proved
on is synthesised from the ask itself, in `tests/synth_ask.py`.

The cut map is a dict -- `{"events": [{"t", "rank", "kind"}], "spans": [...]}`
-- the shape `studio/music_events.py` writes (design §2).  Event kinds are its
classes: section, hit, dropout, lift, drop, entry, phrase, harmony, accent.
Only that shape is depended on here.

Every constant that reaches the model is listed in `MODEL_TEXT` and is
affirmative (`studio/affirm.py`): a negated noun is still that noun.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

from studio.beatmap import WINDOW
from studio.cue_plan import AskedEvent, CueAsk
from studio.music_tone import EXECUTABLE_TAGS, VOCAL_DETAILS, Tone, head, lead_head

SECTION_TOL = 1.0
"""FLAG: bars either side of the asked bar within which a measured event
counts as landed.  The model lands a landmark within about a bar on a
metric seed (03 §1.1); the verify rows of the first music-first master
measure it."""

VERDICT_FLOOR = 0.85
"""FLAG: the weighted share of events that must land -- six of seven in 03
§2.1 -- typed until `plan_score` has rows from real cues."""

PULSE_DENSITY = 0.6
"""FLAG: the share of a window's beats that must carry an onset for the pulse
to count as present (design §9)."""

HOLE_BARS = 2
"""A hole is two bars: the line slot the caption asks for and `slots()` can
hold (a slot is at least one bar)."""

STOP_FALL_DB = 20.0
STOP_WITHIN = 0.10
FADE_SECONDS = 2.0
FADE_DB = 6.0
"""An ending that STOPS falls `STOP_FALL_DB` inside `STOP_WITHIN` seconds; a
fade loses `FADE_DB` over `FADE_SECONDS`, one window at a time (03 §5.2)."""

FORM_BARS = 32
"""The skeleton the register table is written against; every register's
placements are fractions of it so a form of any length keeps the shape."""

Ending = Literal["stop", "hard_stop", "soft_stop", "dead_stop"]


@dataclass(frozen=True)
class Register:
    """One row of 03 §4: how a genre's cue opens, builds, breaks and ends."""

    name: str
    bpm: tuple[int, int]
    mode: str
    intro_bars: int
    build: str
    holes: tuple[float, ...]
    ending: Ending
    silence_bars: int
    tail_seconds: float

    @property
    def pulse_entry(self) -> float:
        """Where the pulse enters, as a fraction of the form."""
        return self.intro_bars / FORM_BARS


BUILD = {
    "elegy": "one long rise and one wave, the drop being the lead alone an octave up",
    "gothic": "two waves, each a semitone rub higher, the braam being the hit",
    "romance": "one lift and one wave, the drop being the tune in full strings",
    "coming_of_age": "three plateaus, the register widening at each, the drop late",
    "tragedy": "two rises, the second at double subdivision an octave down",
    "procedural": "three plateaus, a hole before each, the pulse ticking in eighths",
    "detective": "three plateaus, a hole before each, a walking bass under the second",
    "comedy": "stop and start: three short plateaus, each cut off by a hole, the joke being the silence",
    "adventure": "three waves, horns in unison on the third, a braam at each act end",
}
"""The build shape per register, one clause the caption's Form line carries."""

REGISTERS = {
    "elegy": Register("elegy", (60, 72), "aeolian", 8, BUILD["elegy"], (20 / 32,), "stop", 2, 10.0),
    "gothic": Register("gothic", (60, 80), "phrygian", 6, BUILD["gothic"], (18 / 32,), "hard_stop", 2, 8.0),
    "romance": Register("romance", (60, 84), "major", 8, BUILD["romance"], (24 / 32,), "soft_stop", 1, 8.0),
    "coming_of_age": Register("coming_of_age", (96, 116), "mixolydian", 4, BUILD["coming_of_age"],
                              (18 / 32,), "stop", 2, 6.0),
    "tragedy": Register("tragedy", (80, 96), "harmonic_minor", 4, BUILD["tragedy"], (18 / 32,),
                        "hard_stop", 2, 8.0),
    "procedural": Register("procedural", (84, 108), "aeolian", 4, BUILD["procedural"],
                           (10 / 32, 18 / 32), "hard_stop", 2, 6.0),
    "detective": Register("detective", (84, 100), "aeolian", 4, BUILD["detective"],
                          (10 / 32, 18 / 32), "hard_stop", 2, 8.0),
    "comedy": Register("comedy", (100, 132), "major", 2, BUILD["comedy"],
                       (7 / 32, 15 / 32, 23 / 32, 26 / 32), "dead_stop", 1, 4.0),
    "adventure": Register("adventure", (100, 132), "major", 4, BUILD["adventure"], (18 / 32,),
                          "hard_stop", 2, 6.0),
}
"""The nine rows of 03 §4 against the 32-bar skeleton.  Holes are the
zero-indexed bar of the row's first hole bar (bars 11-12 -> 10/32).

FLAG romance: the table gives a four-bar intro; the paragraph under it names
romance, with elegy, as a register whose pulse enters LATE.  The prose is
the rule the table was written from, so romance takes elegy's eight bars
here until a romance cue is rendered and listened to."""

DEFAULT_REGISTER = "detective"
"""A genre naming none of the nine gets the detective row: it is the §2.1
exemplar, the one register with a measured cue behind it."""

KEYWORDS = {
    "thriller": "procedural", "procedural": "procedural", "suspense": "procedural",
    "detective": "detective", "mystery": "detective", "comedy": "comedy", "comic": "comedy",
    "farce": "comedy", "adventure": "adventure", "swashbuckl": "adventure", "romance": "romance",
    "romantic": "romance", "gothic": "gothic", "horror": "gothic", "elegy": "elegy",
    "elegiac": "elegy", "tragedy": "tragedy", "tragic": "tragedy", "coming-of-age": "coming_of_age",
    "coming of age": "coming_of_age",
}
"""Substrings of `genre`, then of `mood`, that name a register."""


def form_for(tone: Tone) -> Register:
    """The register this tone's genre names, else the one its mood names, else the default."""
    for text in (tone.genre, " ".join(tone.mood)):
        lowered = text.lower()
        for word, name in KEYWORDS.items():
            if word in lowered:
                return REGISTERS[name]
    return REGISTERS[DEFAULT_REGISTER]


def beats_per_bar(tone: Tone) -> int:
    """The top of the time signature: 4 in 4/4, 3 in 3/4, 6 in 6/8."""
    return int(tone.time_signature.split("/")[0])


def beats_per_bar_of(ask: CueAsk) -> int:
    """Read back off the ask: a bar of `bar` seconds at `bpm` holds this many beats."""
    return max(1, round(ask.bar * ask.bpm / 60.0))


def ask_for(tone: Tone, bars: int) -> CueAsk:
    """A CueAsk for `bars` bars of this tone, its events placed by the register."""
    register = form_for(tone)
    bar = round(60.0 / tone.bpm * beats_per_bar(tone), 4)
    base = CueAsk.for_bars(bars, bar=bar, bpm=tone.bpm)
    title_bar = bars - max(2, math.ceil(register.tail_seconds / bar))
    events = placed_events(base, register, title_bar)
    return base.model_copy(update={"events": events, "title_bar": title_bar})


def placed_events(base: CueAsk, register: Register, title_bar: int) -> list[AskedEvent]:
    """The register's landmarks on this form's bars, in bar order.

    The pulse enters at least one bar before the hit: the story quota puts the
    first hit at a quarter of the form, exactly where an eight-bar intro
    (elegy, romance) would have the pulse arrive, and a pulse that enters ON
    the impact leaves the verse with nothing walking.  FLAG: the late-pulse
    registers may want the quota's M1 share widened instead.
    """
    hit = next(e.bar for e in base.events if e.kind == "hit")
    stop = title_bar - register.silence_bars
    pulse = min(max(1, round(register.pulse_entry * base.bars)), hit - 1)
    if not 0 < pulse < hit < stop < title_bar:
        raise ValueError(f"{base.bars} bars is too few for the {register.name} register: "
                         f"pulse {pulse}, hit {hit}, stop {stop}, title {title_bar}")
    holes = [round(f * base.bars) for f in register.holes]
    holes = [b for b in holes if pulse < b != hit and b + HOLE_BARS <= stop]
    events = [AskedEvent(kind="pulse_in", bar=pulse), AskedEvent(kind="hit", bar=hit),
              AskedEvent(kind="stop", bar=stop), AskedEvent(kind="title_hit", bar=title_bar)]
    events += [AskedEvent(kind="hole", bar=b) for b in holes]
    return sorted(events, key=lambda e: (e.bar, e.kind != "hole"))


# --- the caption: the ask read aloud in the model's grammar ------------------

FORM_TAGS = ("Intro", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Post-Chorus", "Outro")
"""The seven sections the ask is told in, each one of `EXECUTABLE_TAGS`."""
assert set(FORM_TAGS) <= set(EXECUTABLE_TAGS)

LEVEL_TEXT = {"low": "quiet and close", "mid": "at speaking level", "high": "at full weight"}
PULSE_TEXT = {True: "the pulse on every beat"}
DENSITY_TEXT = {"sparse": "one figure at a time", "building": "a new layer every four bars, each staying",
                "dense": "the densest bars of the piece"}
"""A section's texture, read off `AskedSection.level`, `pulse`, `density`.
A section whose pulse is still says so through its landmark (the intro's
carrier once a beat, the verse's entry), so the pulse clause is spoken only
where the pulse walks."""

EVENT_TEXT = {
    "pulse_in": "on the downbeat {carrier} takes up the figure and walks it",
    "hole": "everything falls silent on a downbeat, {lead} plays two bars alone, "
            "then the full ensemble returns on the downbeat",
    "hit": "one hard impact on the downbeat, the whole ensemble at once",
    "stop": "a full stop on one downbeat, the room silent",
    "title_hit": "two bars of total silence, then the loudest event of the piece decaying alone "
                 "into stillness: {hit}",
}
"""One affirmative clause per landmark (03 §1.2): each is bound to a downbeat
or an entry, the two things the model places on the grid."""

COUNT_WORDS = {1: "once", 2: "twice", 3: "three times", 4: "four times"}
INTRO_TEXT = "{signature} alone over a held low note, {carrier} once a beat, everything else still"
RISE_TEXT = "a rising sweep into the downbeat"
BRIDGE_TEXT = "this happens {count}"
FORM_HEAD = "Structure: {build}."
PREAMBLE = ("Instrument Lifecycle. Supporting: {supporting}. "
            "Percussion: the complete percussion section is {percussion}.\n"
            "Harmony: {chords}.\n"
            "Groove & Foundation Progression: {tempo}.\n")

MODEL_TEXT = (BUILD, LEVEL_TEXT, PULSE_TEXT, DENSITY_TEXT, EVENT_TEXT, COUNT_WORDS,
              (INTRO_TEXT, RISE_TEXT, BRIDGE_TEXT, FORM_HEAD, PREAMBLE))
"""Every constant in this module that reaches the music model verbatim."""


def texture(ask: CueAsk, movement: str) -> str:
    """The asked texture of one movement's section: level, pulse if it walks, density."""
    section = next(s for s in ask.sections if s.movement == movement)
    clauses = [LEVEL_TEXT[section.level]]
    if section.pulse:
        clauses.append(PULSE_TEXT[True])
    return ", ".join(clauses + [DENSITY_TEXT[section.density]])


def carrier(tone: Tone, index: int) -> str:
    """The pulse carrier that enters `index`-th, the last one when there are fewer."""
    return tone.pulse_carriers[min(index, len(tone.pulse_carriers) - 1)]


def form_text(ask: CueAsk, tone: Tone) -> str:
    """The seven sections in order, each carrying its texture and its landmark."""
    holes = sum(1 for e in ask.events if e.kind == "hole")
    body = {
        "Intro": INTRO_TEXT.format(signature=tone.signature_sound, carrier=carrier(tone, 0)),
        "Verse": f"{EVENT_TEXT['pulse_in'].format(carrier=carrier(tone, 1))}, {texture(ask, 'M1')}",
        "Pre-Chorus": RISE_TEXT,
        "Chorus": f"{EVENT_TEXT['hit']}, {texture(ask, 'M2')}",
        "Bridge": (f"{EVENT_TEXT['hole'].format(lead=lead_head(tone))}, "
                   f"{BRIDGE_TEXT.format(count=COUNT_WORDS.get(holes, 'once'))}"),
        "Post-Chorus": f"{texture(ask, 'M3')}, {tone.register_arc}, {EVENT_TEXT['stop']}",
        "Outro": EVENT_TEXT["title_hit"].format(hit=tone.hit),
    }
    head_line = FORM_HEAD.format(build=form_for(tone).build)
    return " ".join([head_line] + [f"{tag}: {body[tag]}." for tag in FORM_TAGS])


def preamble(tone: Tone) -> str:
    """Instruments, harmony and groove -- the Arrangement heading's first lines."""
    return PREAMBLE.format(supporting=tone.supporting_instruments,
                           percussion=tone.percussion_palette, chords=tone.chord_plan,
                           tempo=tone.tempo_plan)


def caption_from(ask: CueAsk, tone: Tone) -> str:
    """The three-heading caption, its Arrangement written from the ask."""
    return "\n\n".join([
        "### Global Metadata", head(tone),
        "### Vocal Details", VOCAL_DETAILS[tone.lyrics_mode].format(lead=lead_head(tone)),
        "### Arrangement", preamble(tone) + form_text(ask, tone)])


# --- measurement: what the cue actually did, per window ----------------------

def section_level(times: np.ndarray, db: np.ndarray, start: float, end: float) -> float:
    """The window's median level against the whole cue's median, in dB."""
    inside = db[(times >= start) & (times < end)]
    if len(inside) == 0:
        raise ValueError(f"the window {start}-{end}s holds no envelope samples")
    return float(np.median(inside) - np.median(db))


def pulse_present(onset_times: list[float], start: float, end: float, beat: float,
                  floor: float = PULSE_DENSITY) -> bool:
    """True when at least `floor` of the window's beats carry an onset."""
    expected = (end - start) / beat
    found = sum(1 for t in onset_times if start <= t < end)
    return expected > 0 and found >= floor * expected


def onset_density(onset_times: list[float], start: float, end: float, bar: float) -> float:
    """Onsets per bar inside the window."""
    bars = (end - start) / bar
    if bars <= 0:
        raise ValueError(f"the window {start}-{end}s holds no bars")
    return sum(1 for t in onset_times if start <= t < end) / bars


def ending_kind(times: np.ndarray, db: np.ndarray, hard_out: float) -> Literal["stop", "fade", "run_on"]:
    """How the cue leaves `hard_out`: a cliff, a slope, or the same level."""
    at = min(int(round(hard_out / WINDOW)), len(db) - 1)
    before = float(np.median(db[max(0, at - 8):max(1, at)]))
    soon = db[at + 1:at + 1 + int(STOP_WITHIN / WINDOW)]
    if len(soon) and before - float(soon.min()) >= STOP_FALL_DB:
        return "stop"
    span = db[at:at + int(FADE_SECONDS / WINDOW)]
    if len(span) > 2 and before - float(span[-1]) >= FADE_DB and float(np.mean(np.diff(span) <= 0)) >= 0.7:
        return "fade"
    return "run_on"


# --- verify: the ask read back from the cut map ------------------------------

KINDS = {"pulse_in": ("entry", "lift", "hit"), "hole": ("dropout", "drop"),
         "hit": ("hit", "lift"), "stop": ("dropout", "drop"), "title_hit": ("hit",)}
"""Which cut-map classes answer each asked landmark."""


def bar_time(ask: CueAsk, bar: int, metre=None) -> float:
    """Where `bar` begins: the measured downbeat when the grid has one, else nominal."""
    downbeats = list(getattr(metre, "downbeats", None) or [])
    if bar < len(downbeats):
        return float(downbeats[bar])
    return bar * ask.bar


def match_event(target: float, candidates: list[float], tolerance: float) -> float | None:
    """The candidate nearest `target` within `tolerance`, or None."""
    near = [t for t in candidates if abs(t - target) <= tolerance + 1e-6]
    return min(near, key=lambda t: abs(t - target)) if near else None


def verify(ask: CueAsk, cut_map: dict, metre=None) -> CueAsk:
    """The ask with `measured` filled per event from the cut map, or left None."""
    tolerance = SECTION_TOL * ask.bar
    events = []
    for event in ask.events:
        times = [float(m["t"]) for m in cut_map.get("events", [])
                 if m.get("kind") in KINDS[event.kind]]
        measured = match_event(bar_time(ask, event.bar, metre), times, tolerance)
        events.append(event.model_copy(update={"measured": measured}))
    return ask.model_copy(update={"events": events})


WEIGHTS = {"title_hit": 2.0, "stop": 2.0}
"""The stop and the title hit are the two events the card is cut to."""


def plan_score(verified: CueAsk) -> float:
    """The weighted share of asked events that were measured."""
    total = sum(WEIGHTS.get(e.kind, 1.0) for e in verified.events)
    landed = sum(WEIGHTS.get(e.kind, 1.0) for e in verified.events if e.measured is not None)
    return round(landed / total, 4) if total else 0.0


def verdict(score: float, floor: float = VERDICT_FLOOR) -> bool:
    """Whether this cue delivered enough of its ask to ship."""
    return score >= floor
