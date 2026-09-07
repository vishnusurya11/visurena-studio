"""Asking the music model for the book it is scoring, in the form a trailer has.

Two things were wrong at once, and each was measured.

THE MODEL SANG THE STAGE DIRECTIONS.  `lyrics_plan` sent nine `[Tag]` lines
each followed by a parenthetical arrangement note, on the belief that a
parenthetical stays descriptive.  Three delivered cues were separated with
demucs and transcribed with whisper: each has a vocal stem 3-4 LU ABOVE the
rest of the mix, singing "the lead states its figure plainly and alone,
unhurried, no accompaniment" almost verbatim, in order.  In the training
corpus a parenthetical is a SUNG backing line; the one documented exception is
the single word `(instrumental)`.  So the sheet carries tags and sung words
only, and the section prose lives in the caption's Arrangement timeline --
which is what the vendor's own caption skill says to do.

THE CUE WAS A SONG.  The shipped cue reached -15 LUFS at 8 s and held it to
97 s, put its loudness peak at 52%, had every structural hit inside the first
third, no pre-title stop, and ended in a fade.  A trailer cue is a STAIRCASE
WITH HOLES: three plateaus, each louder, denser and higher than the last, a
hole before every step, the deepest hole and the tallest step five seconds
from the end.  The caption asks for that shape by name, section by section.

Underneath both: one tonal centre, one pulse, and a sequence of one-way moves
-- a new colour, a doubled subdivision, a lifted chord, a widened register --
each audibly irreversible.  Mood is which mode the centre is heard in;
excitement is how many of those clicks happen per minute.

Every string here is AFFIRMATIVE (`studio/affirm.py`): a negated noun is still
that noun in the prompt, and this pipeline measured it three times.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from pathlib import Path

from studio.affirm import negations

EXECUTABLE_TAGS = ("Intro", "Verse", "Pre-Chorus", "Chorus", "Post-Chorus",
                   "Bridge", "Instrumental", "Solo", "Outro")
"""The nine tags the open-weights README names.  The local node validates
nothing, so `[Build]`, `[Final Build]` and `[Hit]` reached the model as unknown
lowercase tokens and the length control went with them (78.5-139.75 s on one
"nine section" sheet)."""

SHEET_TAGS = ("Intro", "Verse", "Pre-Chorus", "Chorus", "Bridge",
              "Pre-Chorus", "Chorus", "Post-Chorus", "Outro")
"""The staircase, in the model's own vocabulary.

`[Chorus]` twice because the model was trained on songs: one chorus at 44%
became the peak and `[Post-Chorus]` at 78% an afterthought (MEASURED: loudest
tenth 40-50%, 60-80% six dB quieter).  The second `[Chorus]` is the drop.
`[Pre-Chorus]` twice because it is the only tag whose learned meaning is "rise
into the next section".  `[Bridge]` is the half-time pull-back and the
dialogue slot; `[Post-Chorus]` is the final wave; `[Outro]` is stop, title hit
and tail.  `[Solo]` and `[Instrumental]` are left out: they mean thin and
moderate, and act three must be neither -- the shipped cue's HF/mid ratio
dipped 19 dB in its `[Solo]` tenth, exactly where the cut wants density.
"""

MODES = ("aeolian", "dorian", "phrygian", "harmonic_minor", "major",
         "mixolydian", "lydian", "whole_tone", "octatonic", "open_fifth")
MINOR_MODES = ("aeolian", "dorian", "phrygian", "harmonic_minor",
               "octatonic", "whole_tone")
CENTRES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
LYRICS_MODES = ("instrumental", "vocalise", "refrain", "whisper")

STRONG_PULSE = ("pizzicato", "snare", "bass drum", "taiko", "clock", "watch",
                "timpani", "piano", "bodhran", "handclap", "woodblock", "bell")
"""Carriers the model can play in time.  A pulse made only of struck objects
gave neither the model nor the beat tracker a metre to hold: 84 asked,
89-189 delivered across eight seeds of one caption."""

HOSTED_CHARS = 2000
"""The HOSTED API's documented prompt cap, recorded because it is the number
people quote.  It does NOT bind this studio: the submission path is the local
ComfyUI node, whose only limit is 5000 tokens for caption and lyrics together
(`nodes_minimax_music.py`, MEASURED) -- about 20 000 characters."""

TRAILER_GENRE = ("Epic trailer music, a massive hybrid orchestra, thunderous taiko drums, "
                 "huge orchestral hits and low brass braams")
TRAILER_MOOD = ("epic", "dramatic", "thunderous", "massive")
TRAILER_ARC = ("a whisper that becomes a war: a quiet intro, drums arriving and doubling, "
               "a silent hole, then the whole orchestra, brass and drums at maximum "
               "intensity, bigger with every eight bars, to one enormous final hit")
TRAILER_MIX = ("a modern wide trailer mix, full symphonic strings and horns, low brass "
               "braams, sub-bass under every impact, taiko and processed percussion, a "
               "riser sweeping into each downbeat, wide stereo, a long hall tail, "
               "mastered loud, huge, loud, dramatic")
"""What every book's cue IS, before the book colours it.

The model routes on the first sentence and on the Sonics line.  Sixteen cues
over runs 9-12 opened on the book's `genre` -- "Period orchestral chamber
score with folk violin, a small acoustic ensemble of 1881 London" -- with
"one ribbon microphone ... an 1890s parlour session" for Sonics, and every
ladder rung changed form and seed but never the sound; the user rejected the
SOUND twice ("random music", "shit music").  A trailer's genre and its mix
are the same for A Study in Scarlet as for Dracula, so they live here, and
`Tone.genre`, `mix_space` and `era_reference` are the colour laid on them.

MEASURED 2026-09-06 (4-bar phrase means, four seeds each): the head
"Cinematic hybrid orchestral trailer music ... coloured by a Victorian
detective mystery" came back FLAT -- quiet-to-loud spread 3.6, 1.5, 13.4,
13.8 dB, tracked at 80, 63, 190, 77 BPM against 100 asked -- and the user
heard it: "not dramatic enough for trailer".  The head "Epic trailer music,
massive hybrid orchestral, thunderous taiko ... huge, loud, dramatic" with
the progression "a whisper that becomes a war" came back with BOTH registers
-- spread 13.2, 17.9, 7.9, 6.9 dB -- at 86, 100, 96, 97 BPM.  The arc
(`studio/cue_arc.py`) is an edit that sorts the render's phrases by level;
what the caption must deliver is material at both extremes, and the model
routes on intensity words.  So the mood opens on `TRAILER_MOOD`, the
progression on `TRAILER_ARC`, and the book's words follow as colour.
"""

CAPTION_WORDS = (250, 700)
CAPTION_CHARS = 4100
"""What this caption is allowed to be.

The vendor's caption-rewriter skill defaults to "approximately 250-450 English
words".  That band was written for a SONG caption, which carries genre, mood
and production and stops.  This one additionally carries a nine-section
trailer form -- the thing whose absence made the last cue "not exciting at
all" -- and the trailer's own genre, mood, progression and mix
(`TRAILER_GENRE`, `TRAILER_MOOD`, `TRAILER_ARC`, `TRAILER_MIX`, about 100
words), so it lands near 650 words (the ask-written form, `cue_ask.caption_from`,
near 675) and stays far inside the node's real cap.
The ceiling exists so a caption cannot grow unnoticed; the exact count is
asserted in `test_music_tone.py::test_the_caption_size_is_recorded_and_capped`.
"""


@dataclass(frozen=True)
class Tone:
    """What this book should sound like, and why.

    Authored once per book beside the reference sheets, for the same reason:
    it is a decision about the work that should not be re-made per render.
    """

    genre: str
    tonal_centre: str
    mode: str
    mood: tuple[str, ...]
    bpm: int
    time_signature: str
    tempo_plan: str
    chord_plan: str
    pulse_carriers: tuple[str, ...]
    signature_sound: str
    lead_instrument: str
    supporting_instruments: str
    register_arc: str
    dynamics_arc: str
    mix_space: str
    era_reference: str
    imagery: str
    hit: str
    lyrics_mode: str = "instrumental"
    refrain: str | None = None
    vocalise: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _check_vocabulary(self)
        _check_affirmative(self)
        _check_pulse(self)
        _check_voice(self)

    @property
    def key(self) -> str:
        """What `Basic Attributes: key is ...` says: the centre, held all cue."""
        return self.tonal_centre

    @property
    def scale(self) -> str:
        """The mode, told to the model in the two words it was trained on."""
        return "minor" if self.mode in MINOR_MODES else "major"

    @property
    def percussion_palette(self) -> str:
        """The closed roster, read off the carriers so the two cannot drift.

        A closed list occupies the slot a drum kit would fill: the shipped
        caption said "no drum kit and no taiko at any point" and came back at
        105 BPM with a heavy pulse.
        """
        return ", ".join(self.pulse_carriers)


def texts_of(tone: Tone) -> list[tuple[str, str]]:
    """(field name, string) for every string this tone will send to a model."""
    found: list[tuple[str, str]] = []
    for field in fields(tone):
        value = getattr(tone, field.name)
        if isinstance(value, str):
            found.append((field.name, value))
        elif isinstance(value, tuple):
            found += [(field.name, item) for item in value]
    return found


def _check_affirmative(tone: Tone) -> None:
    """Every field names what plays.  A negated noun is still that noun."""
    for name, text in texts_of(tone):
        found = negations(text)
        if found:
            raise ValueError(
                f"{name} asks for an absence ({found[0]!r}): {text[:80]!r}. "
                f"Name what occupies that place instead.")


def _check_vocabulary(tone: Tone) -> None:
    """One centre, one named mode, one lyric mode, three mood words."""
    if tone.mode not in MODES:
        raise ValueError(f"mode {tone.mode!r} is not one of {MODES}")
    if tone.tonal_centre not in CENTRES:
        raise ValueError(f"tonal_centre {tone.tonal_centre!r} is not one of {CENTRES}")
    if tone.lyrics_mode not in LYRICS_MODES:
        raise ValueError(f"lyrics_mode {tone.lyrics_mode!r} is not one of {LYRICS_MODES}")
    if len(tone.mood) != 3:
        raise ValueError(f"mood is three adjectives, not {len(tone.mood)}")


def _check_pulse(tone: Tone) -> None:
    """At least two carriers, one of them a thing the model plays in time."""
    if len(tone.pulse_carriers) < 2:
        raise ValueError("pulse_carriers needs at least two, in order of entry")
    joined = " ".join(tone.pulse_carriers).lower()
    if not any(word in joined for word in STRONG_PULSE):
        raise ValueError(f"pulse_carriers needs one of {STRONG_PULSE}: a pulse the "
                         f"model and the beat tracker can both hold")


def _check_voice(tone: Tone) -> None:
    """A refrain exists exactly when one is sung."""
    sung = tone.lyrics_mode == "refrain"
    if sung and not (tone.refrain or "").strip():
        raise ValueError("lyrics_mode 'refrain' needs a refrain to sing")
    if not sung and (tone.refrain or "").strip():
        raise ValueError(f"a refrain with lyrics_mode {tone.lyrics_mode!r} is never sung")


def load_tone(book: Path) -> Tone:
    """The book's authored music tone.  Absent is an error, not a default."""
    path = book / "trailer" / "music" / "tone.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist; a cue cannot be tone-matched to a book "
            f"whose tone has never been written down")
    return from_json(json.loads(path.read_text(encoding="utf-8")), path)


def from_json(data: dict, path: Path | None = None) -> Tone:
    """A Tone from a tone.json body, with v1 files told what they are."""
    wanted = {field.name for field in fields(Tone)}
    missing = sorted(wanted - set(data) - {"lyrics_mode", "refrain", "vocalise"})
    if missing:
        raise ValueError(
            f"{path or 'tone.json'} is a v1 tone: it has no {', '.join(missing)}. "
            f"Rewrite it in Tone v2 (see .claude/skills/trailer/subskills/03-music).")
    listed = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items()}
    return Tone(**{k: v for k, v in listed.items() if k in wanted})


# --- the caption: three headings, and the staircase named section by section -

STAIRCASE = (
    "Structure: three waves, each louder, denser and higher, silence before "
    "every step. "
    "Intro: {signature} alone over a held low note. "
    "Verse: one low figure repeating to the last bar, a new colour every four "
    "bars, every layer staying, its last two bars silent. "
    "Pre-Chorus: a rising sweep into the downbeat. "
    "Chorus: one hard impact there, the whole ensemble at once. "
    "Bridge: one dry instrument two bars, then half-time, a heavy accent every "
    "two beats. "
    "Pre-Chorus: each bar higher, a longer sweep. "
    "Chorus: the drop, heavier, a low accent on every second downbeat after a "
    "short accent on the eighth before it, the lead calling a bar and the low "
    "ensemble answering. "
    "Post-Chorus: the densest bars of the piece, {register}, a hard stop on a "
    "downbeat. "
    "Outro: two full bars of total silence, {hit}, the loudest event of the "
    "piece, one low note decaying alone for eight seconds."
)
"""Twelve excitement mechanics, one clause each.

Ostinato, a layered entry every four bars, the hole at the end of the verse,
riser into each impact, the half-time drop, rising register, the syncopated
low accent, call-and-response, the density staircase, the pre-title stop, the
title hit and the tail.  The shipped cue followed exactly one of them (rising
register) because the old caption asked for nothing propulsive -- it asked for
a chamber piece to get louder.
"""

VOCAL_DETAILS = {
    "instrumental": "This piece is instrumental throughout. The lead melodic "
                    "role belongs to {lead}.",
    "vocalise": "A low choir, close and dry, holds open vowels through the "
                "chorus, the bridge and the final wave, one syllable to the "
                "pulse. Every other section belongs to {lead}.",
    "refrain": "One low voice, close and dry, sings a single English line in "
               "each chorus and twice in the final wave, the words few and "
               "held long. Every other section belongs to {lead}.",
    "whisper": "One voice speaks a single line in the bridge, unpitched and "
               "close to the microphone. Every other section belongs to {lead}.",
}
"""What the voice does, said as what it does.

Voices are excluded by describing an instrumental lead and saying nothing
else about them -- the caption already said "This piece is instrumental" on
the cues that came back singing, and it was the LYRICS field that sang.
"""


def lead_head(tone: Tone) -> str:
    """The lead instrument in the fewest words that name it.

    It is stated in full in the first sentence, where the model reads the
    genre; Vocal Details only has to point back at it, and the shipped caption
    spent 40 of its words saying the same clause twice.
    """
    return tone.lead_instrument.split(",")[0].strip()


def head(tone: Tone) -> str:
    """Global Metadata: the trailer's genre coloured by the book's, the lead,
    tempo, key, metre, mood -- each once; the trailer's mix, then the book's."""
    return (
        f"Basic Attributes: {TRAILER_GENRE}, coloured by {tone.genre}; the lead "
        f"voice riding above the orchestra is {tone.lead_instrument}. "
        f"tempo is around {tone.bpm} BPM, held from the first bar to the last. "
        f"key is {tone.key}, and scale is {tone.scale}. "
        f"time signature is {tone.time_signature}. "
        f"mood is {', '.join(TRAILER_MOOD + tone.mood)}.\n"
        f"Global Emotional Progression: {TRAILER_ARC}. {tone.dynamics_arc}\n"
        f"Application Scenarios & Imagery: a film trailer for {tone.imagery}.\n"
        f"Sonics & Production Profile: {TRAILER_MIX}; {tone.mix_space}; "
        f"{tone.era_reference}.")


def arrangement(tone: Tone) -> str:
    """Instruments, harmony, groove, then the section-by-section staircase."""
    return (
        f"Instrument Lifecycle. Supporting: {tone.supporting_instruments}. "
        f"Percussion: the complete percussion section is {tone.percussion_palette}, at "
        f"least one striking on every second beat from the first bar to the last, "
        f"softer under the quiet sections.\n"
        f"Harmony: {tone.chord_plan}.\n"
        f"Groove & Foundation Progression: {tone.tempo_plan}.\n"
        + STAIRCASE.format(signature=tone.signature_sound,
                           register=tone.register_arc, hit=tone.hit))


def caption(tone: Tone) -> str:
    """MiniMax's three-heading caption grammar, written from this book's tone.

    Routes on GENRE and on a named lead instrument in the first sentence.
    The genre is the TRAILER'S (`TRAILER_GENRE`, a noun the corpus tags
    music with) and the book's `genre` colours it; a caption that opens on
    the book's ensemble is asking for that ensemble's music, and sixteen
    cues asked for an 1881 parlour.
    """
    return "\n\n".join([
        "### Global Metadata", head(tone),
        "### Vocal Details",
        VOCAL_DETAILS[tone.lyrics_mode].format(lead=lead_head(tone)),
        "### Arrangement", arrangement(tone)])


# --- the lyric sheet: tags, and words that are meant to be sung --------------

VOICED = {"instrumental": (), "vocalise": ("Chorus", "Bridge", "Post-Chorus"),
          "refrain": ("Chorus", "Post-Chorus"), "whisper": ("Bridge",)}
"""Which sections carry a voice, by lyric mode.

`[Intro]` and `[Verse]` stay voiceless in every mode because a spoken line
never sits under a sung word, and those are the sections where `05-dialogue`
puts its first window.  The `[Bridge]` carries a voice only where the voice IS
the pull-back: one held vowel, or one whispered line over near-silence.
"""


def sung_lines(tone: Tone, tag: str) -> list[str]:
    """The words sung under one tag, or nothing when the section is played."""
    if tag not in VOICED[tone.lyrics_mode]:
        return []
    if tone.lyrics_mode == "refrain":
        return [tone.refrain] * (2 if tag == "Post-Chorus" else 1)
    words = list(tone.vocalise) or ["Ah..."]
    if tone.lyrics_mode == "whisper":
        return words[:1]
    return words if tag != "Bridge" else ["Ah...", words[-1]]


def lyrics_plan(tone: Tone) -> str:
    """The lyric sheet: nine tags, and only words that are meant to be sung.

    Every non-tag line is sung.  A section with nothing to sing carries the
    one documented marker, `(instrumental)` -- the form the vendor's own
    reference instrumental render uses.
    """
    blocks = []
    for tag in SHEET_TAGS:
        lines = sung_lines(tone, tag) or ["(instrumental)"]
        blocks.append("\n".join([f"[{tag}]"] + lines))
    return "\n\n".join(blocks)


# --- what was actually sent, recorded beside what came back ------------------

def caption_stamp(text: str, lyrics: str = "", duration: int = 0) -> str:
    """A short hash of the recipe that produced a cue: caption, sheet, length.

    Caption and lyrics are ONE conditioning block in the node -- `build_prompt`
    puts both between `<|im_start|>` and `<|audio_start|>` and the
    unconditioned branch replaces the lot -- so the stamp covers both.  Without
    it `build_music` skipped any seed whose file already existed, so rewriting
    the caption and re-running kept every cue the OLD recipe made and printed a
    success line.
    """
    return hashlib.sha256(f"{text}\n{lyrics}\n{duration}".encode("utf-8")).hexdigest()[:16]


def _stamp_path(cue: Path) -> Path:
    return cue.with_suffix(".caption.txt")


def recipe_path(cue: Path) -> Path:
    """Where the exact caption and sheet that made this audio are kept."""
    return cue.with_suffix(".caption.json")


def stamp_cue(cue: Path, stamp: str, text: str = "", lyrics: str = "") -> None:
    """Record which recipe produced this audio, beside the audio.

    cue-3002's stamp matches no committed caption times any committed
    tone.json, so the text that produced the shipped cue cannot be recovered
    from git.  The full recipe is written out now, not just its digest.
    """
    _stamp_path(cue).write_text(stamp, encoding="utf-8")
    recipe_path(cue).write_text(
        json.dumps({"stamp": stamp, "caption": text, "lyrics": lyrics}, indent=1),
        encoding="utf-8")


def cue_is_current(cue: Path, stamp: str) -> bool:
    """True only when this file was rendered from THIS recipe."""
    path = _stamp_path(cue)
    if not cue.exists() or not path.exists():
        return False
    return path.read_text(encoding="utf-8").strip() == stamp


MODEL_TEXT = (STAIRCASE, VOCAL_DETAILS)
"""Every constant in this module that reaches the music model verbatim."""
