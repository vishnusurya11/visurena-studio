"""Did the voice say the line, or did it say something else?

A generative TTS can return confident, well-formed audio of THE WRONG WORDS,
and nothing upstream notices: the file exists, it is the right length, its
loudness is in range, and the pipeline moves on.  Brigham Young's `whisper`
edit came back hallucinated and every other gate in this repo passed it,
because every other gate measures the SIGNAL and none of them measures the
CONTENT.

So the gate is the obvious one nobody had built: listen to the clip, and check
it against the line it was asked to say.  Whisper transcribes, the words are
normalised, and the two are compared by word error rate.  A clip that fails is
not a clip to ship -- it is re-rendered with a new seed or dropped.

TWO FAILURES ARE CAUGHT HERE, and they look different:

  WRONG WORDS   the transcript disagrees with the line.  Caught by `error_rate`.
  RUNAWAY       the model kept going: Lucy's third angry iteration ran 9.36 s
                against a 4.38 s original.  A transcript can still match while
                the tail babbles, so length is checked separately.

The transcriber is injected so the contract can be tested without a model and
without a GPU: `check(clip, line, transcribe=fake)` is a free, offline test.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MAX_ERROR_RATE = 0.20
"""How wrong a transcript may be and still count as the same line.

Not zero: Whisper punctuates differently, spells numbers out, and hears
"Ferrier" as "Ferrar".  Measured on the first 30-clip run, a good clip sits
under 0.10 and a hallucination sits far above 0.5, so the boundary is wide and
the exact value is not load-bearing."""

MAX_STRETCH = 1.8
"""How much longer than its source an edited clip may run before it is called a
runaway.  An emotion edit legitimately changes pace -- a grieving read is
slower than a calm one -- so this is deliberately loose; it exists to catch
9.36 s against 4.38 s, not to police delivery."""

WPS_MAX = 3.8
"""Words per second of SPEECH (trailing room excluded) over which a line is rushed.

MEASURED on episode 10's thirty lines: mean 3.02 (episode 9: 3.17), and the
ones the ear flagged as rushed -- l01 4.20, l10 4.11, l29 4.00 (Lucy's six-word
button in 1.50 s, also the loudest line), l25 3.79, l28 3.74.  3.8 keeps the
three that were heard as rushed out and the two that were not in."""

TRAIL_S = 0.05
"""Trailing room under which a line has nowhere to release.  MEASURED: the
episode's median trail is 0.05 s; fourteen of thirty lines had less."""

RELEASE_DB = 30.0
"""How far under its peak the last 50 ms must sit for the line to have
ended.  l14 ("young.") and l05 were at -25 and -30 dB with 0.00 s of room:
the last consonant is cut off, and a listener hears the edit."""

APOSTROPHE = re.compile(r"['‘’ʼ]")
FILLER = re.compile(r"[^\w\s]")


class NoTranscriber(RuntimeError):
    """Asked to listen with nothing to listen with."""


@dataclass(frozen=True)
class Verdict:
    """What the gate heard, and whether it passed."""
    clip: str
    intended: str
    heard: str
    error_rate: float
    seconds: float
    stretch: float
    passed: bool
    why: str
    wps: float = 0.0
    abrupt: bool = False

    def line(self) -> str:
        """One row for a log or a report."""
        mark = "ok  " if self.passed else "FAIL"
        return (f"{mark} {Path(self.clip).name:38} wer {self.error_rate:.2f} "
                f"{self.seconds:5.2f}s  {self.why}")


def normalised(text: str) -> list[str]:
    """The words, stripped of everything a transcript is allowed to differ on.

    Apostrophes are DELETED rather than spaced, and deleted BEFORE the ascii
    fold: folding drops a curly apostrophe entirely, so "it’s" would become
    "its" while "it's" stayed two characters longer, and the two spellings of
    one word counted as an error."""
    bare = APOSTROPHE.sub("", text)
    flat = unicodedata.normalize("NFKD", bare).encode("ascii", "ignore").decode()
    words = FILLER.sub(" ", flat.lower()).split()
    return [spelling(HONORIFICS.get(word, word)) for word in number_words(words)]


UNITS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
         "nineteen")
TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy", 80: "eighty",
        90: "ninety"}


def number_words(words: list[str]) -> list[str]:
    """A numeral Whisper wrote for a number word is that word (ep11: "9. From
    Seven" for "Nine from seven" scored 0.17; "7 from 5" for "Seven from five"
    0.33).  Digits 0-99 become their words; a hyphenated "twenty-nine" is two."""
    out = []
    for word in words:
        if word.isdigit() and int(word) < 100:
            n = int(word)
            out += [UNITS[n]] if n < 20 else [TENS[n - n % 10]] + ([UNITS[n % 10]] if n % 10 else [])
        else:
            out += word.split("-") if "-" in word and word.replace("-", "").isalpha() else [word]
    return out



SPELLINGS = (
    # -our- is regular, with its derived forms; the {3,} guard keeps `our`,
    # `four`, `hour`, `your`, `pour`, `tour` and `sour` intact
    (re.compile(r"^(.{3,}?)our(s|ed|ing|able|ful|less)?$"), r"\1or\2"),
    (re.compile(r"^(.{2,}?)is(e|ed|es|ing|er|ers|ation|ations)$"), r"\1iz\2"),
    (re.compile(r"^(.{3,}?)ll(ed|ing|er|ers)$"), r"\1l\2"),
    (re.compile(r"^grey(s|er|est|ish|hound|hounds)?$"), r"gray\1"),
)
"""BRITISH AND AMERICAN ARE ONE SPELLING HERE, because the script is Victorian
British prose and the transcriber writes American.

Episode 4's QC failed a perfectly read line on "discoloured" against
"discolored"; eleven chapters remain and every colour, neighbour, grey and
realise in them would do it again.

The fold does not have to be correct English -- it is applied to BOTH sides, so
it only has to be CONSISTENT.  What it must not do is collapse two genuinely
DIFFERENT words into one and hide a real mistake.  Hence the guards: `.{3,}?`
before -our keeps `our`, `four`, `hour` and `pour` whole, and `pored`/`poured`
and `floor`/`flour` stay two words apart.

-RE IS A WORD LIST, NOT A RULE.  A `-re` -> `-er` regex eats `before`, `there`,
`where` and `here`, which are not dialect spellings at all."""

RE_STEMS = ("cent", "theat", "met", "lit", "fib", "sab", "calib",
            "somb", "spect", "lust", "scept", "och", "manoeuv")
"""The `-re`/`-er` pairs, by stem: centre/center, theatre/theater, ..."""

BUT_NOT_ISE = {"wise", "rise", "promise", "premise", "surprise", "advise", "devise",
               "revise", "arise", "noise", "raise", "praise", "poise", "cruise",
               "guise", "louse", "mise", "demise", "paradise", "exercise", "franchise",
               "chastise", "disguise", "supervise", "improvise", "merchandise"}
"""Words ending -ise that are not the British spelling of -ize.  `wise` became
`iz`, and `promise` and `rise` with it."""


def spelling(word: str) -> str:
    """One canonical spelling for a word two dialects write differently."""
    for stem in RE_STEMS:
        for tail, into in (("re", "er"), ("res", "ers"), ("red", "ered"), ("ring", "ering")):
            if word == stem + tail:
                return stem + into
    if word in BUT_NOT_ISE:
        return word
    for pattern, into in SPELLINGS:
        if pattern.match(word):
            return pattern.sub(into, word)
    return word


HONORIFICS = {"dr": "doctor", "mr": "mister", "mrs": "missus", "st": "saint"}
"""Whisper writes "Dr. Watson" for a clip that said "Doctor Watson"; the line
was right and the gate called it 0.40 wrong.  Both spellings are one word."""


SEAM_SLACK = 1
"""Characters of slack allowed at a join, and only at a join."""

SEAM_FLOOR = 6
"""The shorter form must be this long before a letter of slack is small enough
to mean a seam: "a" + "to" is one letter from "at", and is not a split word."""


def letters_apart(said: str, want: str) -> int:
    """Levenshtein distance over CHARACTERS of two single words."""
    row = list(range(len(want) + 1))
    for i, ch in enumerate(said, start=1):
        nxt = [i]
        for j, wanted in enumerate(want, start=1):
            nxt.append(min(row[j] + 1, nxt[j - 1] + 1, row[j - 1] + (ch != wanted)))
        row = nxt
    return row[-1]


def one_sound(joined: str, want: str) -> bool:
    """Is `joined` the same sound as `want`, written across a seam?

    Exactly, or within one character when both are long enough for one
    character to be a seam rather than the word: the transcriber writes
    "carriage is" for "carriages", and the `s` it moved is the whole
    difference (ep08 line 9, measured).
    """
    if joined == want:
        return True
    return (min(len(joined), len(want)) >= SEAM_FLOOR
            and letters_apart(joined, want) <= SEAM_SLACK)


def distance(said: list[str], meant: list[str]) -> int:
    """Levenshtein distance over WORDS, where JOINING OR SPLITTING A WORD COSTS 1.

    A transcriber merges and splits compounds constantly, and plain Levenshtein
    charges two errors for it: "under lines" heard as "underlines" is a deletion
    plus a substitution.  Episode 4 lost a QC pass to exactly that, on a line
    that was read correctly.  One sound written as one word or two is one
    difference, so it costs one."""
    prev2: list[int] | None = None
    row = list(range(len(meant) + 1))
    for i, word in enumerate(said, start=1):
        nxt = [i]
        for j, want in enumerate(meant, start=1):
            best = min(row[j] + 1, nxt[j - 1] + 1, row[j - 1] + (word != want))
            # said[i-1] is meant[j-2] + meant[j-1] run together
            if j >= 2 and one_sound(word, meant[j - 2] + want):
                best = min(best, row[j - 2] + 1)
            # said[i-2] + said[i-1] run together is meant[j-1]
            if i >= 2 and prev2 is not None and one_sound(said[i - 2] + word, want):
                best = min(best, prev2[j - 1] + 1)
            nxt.append(best)
        prev2, row = row, nxt
    return row[-1]


def error_rate(heard: str, intended: str) -> float:
    """Word error rate of a transcript against the line it should be."""
    meant = normalised(intended)
    if not meant:
        return 0.0
    return distance(normalised(heard), meant) / len(meant)


def seconds_of(clip: Path) -> float:
    """How long the clip runs, read off the file itself."""
    import soundfile as sf

    info = sf.info(str(clip))
    return float(info.frames) / float(info.samplerate)


def _mono(clip: Path):
    """(samples as one channel, rate) of a clip."""
    import soundfile as sf

    audio, rate = sf.read(str(clip), dtype="float32", always_2d=True)
    return audio.mean(axis=1), rate


ROOM_FLOOR_DB = -50.0
"""Under this, relative to the clip's peak, a sample is room and not voice.
MEASURED on ep10: at -60 dB the PCM dither at the end of l29 (0.09 s of
audible room) counts as sound and the trail reads 0.000 s; at -50 it reads
0.056 s.  l14's trail is 0.000 s at every floor."""


def tail_room(clip: Path) -> float:
    """Seconds of room (ROOM_FLOOR_DB under the clip's peak) after the last sound."""
    import numpy as np

    mono, rate = _mono(Path(clip))
    peak = float(np.abs(mono).max()) if len(mono) else 0.0
    if peak < 1e-4:
        return len(mono) / rate
    loud = np.flatnonzero(np.abs(mono) >= peak * 10 ** (ROOM_FLOOR_DB / 20))
    return round((len(mono) - 1 - int(loud[-1])) / rate, 4)


def ends_abruptly(clip: Path) -> bool:
    """Is the last consonant cut off?  The last 50 ms still peak within
    RELEASE_DB of the clip's peak AND under TRAIL_S of room after them.  The
    window's PEAK and not its RMS: that is the number the ear measured (l14
    -25 dB, l05 -30 dB), and a consonant is a peak.  A silent clip is not
    abrupt: there is nothing in it to cut."""
    import numpy as np

    mono, rate = _mono(Path(clip))
    peak = float(np.abs(mono).max()) if len(mono) else 0.0
    if peak < 1e-4 or tail_room(clip) >= TRAIL_S:
        return False
    last = mono[-max(int(rate * 0.05), 1):]
    level = 20 * np.log10(max(1e-9, float(np.abs(last).max())) / peak)
    return level > -RELEASE_DB


def words_per_second(text: str, seconds: float) -> float:
    """The pace of the line, from the words it was given and the seconds measured."""
    if seconds <= 0:
        return 0.0
    return len(normalised(text)) / seconds


def judge(rate: float, stretch: float, wps: float = 0.0, abrupt: bool = False) -> tuple[bool, str]:
    """The verdict in words: what went wrong, or that nothing did."""
    if rate > MAX_ERROR_RATE:
        return False, f"said something else (wer {rate:.2f} > {MAX_ERROR_RATE})"
    if stretch > MAX_STRETCH:
        return False, f"ran away ({stretch:.2f}x its source > {MAX_STRETCH})"
    if abrupt:
        return False, f"cut off (last 50 ms within {RELEASE_DB:.0f} dB of peak, under {TRAIL_S} s of room)"
    if wps > WPS_MAX:
        return False, f"rushed ({wps:.2f} words/s > {WPS_MAX})"
    return True, "said the line"


def check(clip: Path, intended: str, transcribe: Callable[[Path], str] | None = None,
          source: Path | None = None) -> Verdict:
    """Listen to one clip and rule on it against the line it was asked to say."""
    clip = Path(clip)
    listen = transcribe or transcriber()
    heard = listen(clip)
    rate = error_rate(heard, intended)
    seconds = seconds_of(clip)
    stretch = seconds / seconds_of(source) if source else 1.0
    wps = words_per_second(intended, seconds - tail_room(clip))
    abrupt = ends_abruptly(clip)
    passed, why = judge(rate, stretch, wps, abrupt)
    return Verdict(str(clip), intended, heard, rate, seconds, stretch, passed, why,
                   round(wps, 2), abrupt)


WHISPER_ROOT = ("D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/ComfyUI"
                "/models/whisper")
MODEL = "large-v3-turbo"
DEVICE = "cpu"
"""Where the ear runs.  The CPU, on purpose: the repo venv's torch is CPU-only,
and a listen on the CPU never enters ComfyUI's single queue, so a DQ can run
while a take renders instead of behind it.  MEASURED (ep10 DQ, F3): every
take_dq and qc listen used to go through `comfy_transcriber` and wait on the
render in front of it."""
_HEARD = {}


def whisper_options(device: str) -> dict:
    """What `transcribe` is called with: half precision only where it exists."""
    return {"language": "en", "fp16": device != "cpu"}


def transcriber(model: str = MODEL, device: str = DEVICE) -> Callable[[Path], str]:
    """The real ear: local Whisper in THIS process, loaded once and kept.

    Import is deferred and the model cached module-side, because the gate is
    called once per clip and a 30-clip run must not load the weights 30 times.
    """
    key = (model, device)
    if key not in _HEARD:
        try:
            import whisper
        except ImportError as why:  # pragma: no cover - environment, not logic
            raise NoTranscriber(
                "openai-whisper is not importable here; `uv sync --all-groups`, "
                "run the gate under ComfyUI's python, or pass transcribe=") from why
        _HEARD[key] = whisper.load_model(model, device=device, download_root=WHISPER_ROOT)
    engine = _HEARD[key]

    def listen(clip: Path) -> str:
        return engine.transcribe(str(clip), **whisper_options(device))["text"].strip()

    return listen


def report(verdicts: list[Verdict]) -> str:
    """Every clip, worst first, so a failure is the first thing read."""
    ordered = sorted(verdicts, key=lambda v: (v.passed, -v.error_rate))
    failed = [v for v in verdicts if not v.passed]
    head = f"{len(verdicts) - len(failed)}/{len(verdicts)} clips said their line"
    return "\n".join([head, *(v.line() for v in ordered)])


def comfy_transcriber(workflow: str = "audio_whisper_transcribe", run=None) -> Callable[[Path], str]:
    """The same ear, reached through ComfyUI when whisper is not importable here.

    The repo venv carries no whisper; ComfyUI's does, behind a workflow whose
    first text output is the clean transcript.  `run` is injectable so the
    gate can be tested without a server."""
    from studio import comfy

    def listen(clip: Path) -> str:
        values = {"audio_path": comfy.stage_image(Path(clip)), "return_timestamps": False}
        texts = run(values) if run else _texts(comfy, workflow, values)
        return next((t.strip() for t in texts if t.strip() and not t.strip().startswith("{")), "")

    return listen


def _texts(comfy, workflow: str, values: dict) -> list[str]:
    template, inject = comfy.load_workflow(workflow)
    record = comfy.wait_record(comfy.submit(comfy.apply_inject(template, inject, values)),
                               timeout=300)
    return comfy.texts_of(record)


def any_transcriber() -> Callable[[Path], str]:
    """Local whisper when importable, ComfyUI's otherwise."""
    try:
        return transcriber()
    except NoTranscriber:
        return comfy_transcriber()
