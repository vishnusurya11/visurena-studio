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

import json
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


ENCE_STEMS = ("defen", "offen", "preten", "licen")
"""The `-ence`/`-ense` pairs, by stem: defence/defense, ...  A word list, like
-re: a rule would fold `fence`, `hence` and `pence` (ep14 line 24)."""


WORD_PAIRS = {"cheque": "check", "cheques": "checks", "kerb": "curb", "kerbs": "curbs",
              "gaol": "jail", "gaols": "jails", "gaoler": "jailer", "plough": "plow",
              "ploughed": "plowed", "waggon": "wagon", "waggons": "wagons"}
"""Whole-word British/American pairs no rule covers (Jekyll Kawajiri ep01: "a cheque" heard
"a check" eight times, WER 0.25, the record step refused)."""


def spelling(word: str) -> str:
    """One canonical spelling for a word two dialects write differently."""
    if word in WORD_PAIRS:
        return WORD_PAIRS[word]
    for stem in ENCE_STEMS:
        if word.startswith(stem + "ce"):
            return stem + "se" + word[len(stem) + 2:]
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


LONG_SEAM_SLACK = 2
LONG_SEAM_FLOOR = 7
"""A long word heard as two may differ by two letters: a NAME the ear has no
word for comes back as the nearest pair ("Enfield" -> "and field", Jekyll ep01
line 12, both tries). Still one error, never zero."""


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
    shorter = min(len(joined), len(want))
    slack = LONG_SEAM_SLACK if shorter >= LONG_SEAM_FLOOR else SEAM_SLACK
    return shorter >= SEAM_FLOOR and letters_apart(joined, want) <= slack


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


def heard_as(heard: str, lexicon: dict[str, str]) -> str:
    """The transcript with a book's known mishearings read as the names they
    are (Jekyll ep01 l12: "And Field" for "Enfield"); whole phrases only."""
    for wrong, right in lexicon.items():
        heard = re.sub(rf"\b{re.escape(wrong)}\b", right, heard, flags=re.IGNORECASE)
    return heard


def ear_lexicon(book: Path) -> dict[str, str]:
    """The book's filed mishearings, `cast/ear_lexicon.json`; none when absent."""
    path = Path(book) / "cast" / "ear_lexicon.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _plain_words(text: str) -> list[str]:
    """The words as written, lower-cased and unpunctuated -- NO spelling fold, so the
    pair the fold does not already cover is still visible."""
    flat = unicodedata.normalize("NFKD", APOSTROPHE.sub("", text)).encode("ascii", "ignore").decode()
    return FILLER.sub(" ", flat.lower()).split()


def differing_pair(heard: str, intended: str) -> tuple[str, str] | None:
    """(heard word, intended word) when the two lines differ in exactly one word, else None."""
    said, meant = _plain_words(heard), _plain_words(intended)
    odd = [(a, b) for a, b in zip(said, meant) if a != b]
    return odd[0] if len(said) == len(meant) and len(odd) == 1 else None


def phoneme_equal(a: str, b: str) -> bool:
    """Do two spellings share a pronunciation in CMUdict?  A word the dictionary lacks
    (a book's name) is never equal: it cannot be proved the ear is wrong."""
    import cmudict
    table = cmudict.dict()
    one, two = table.get(a.lower()), table.get(b.lower())
    return bool(one and two and any(p in two for p in one))


def file_homophone(book: Path, heard: str, intended: str) -> bool:
    """A stable wrong transcript whose one differing word is a homophone of the line's
    (Jekyll ep01 l11: 'check' for 'cheque') is filed in the book's ear lexicon, heard
    word -> line word.  True when filed; the global fold and the other pairs stay alone."""
    pair = differing_pair(heard, intended)
    if pair is None or not phoneme_equal(*pair):
        return False
    path = Path(book) / "cast" / "ear_lexicon.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**ear_lexicon(book), pair[0]: pair[1]}, indent=1), encoding="utf-8")
    return True


def heard_on_master(pcm: bytes, listen: Callable[[], str], cache: Path, model: str = "") -> str:
    """What the ear heard in one 24 kHz window of the master, listened to ONCE: the key is
    the sha256 of the window's PCM plus the model id; a miss listens and files the text."""
    import hashlib
    key = hashlib.sha256(pcm + (model or MODEL).encode("utf-8")).hexdigest()
    cache = Path(cache)
    seen = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    if key not in seen:
        seen[key] = listen()
        cache.write_text(json.dumps(seen), encoding="utf-8")
    return seen[key]


def with_lexicon(listen: Callable[[Path], str], lexicon: dict[str, str]) -> Callable[[Path], str]:
    """An ear that reads the book's names before anything scores it."""
    return lambda clip: heard_as(listen(clip), lexicon)


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


PACE_MIN_WORDS = 5
"""Under this a line has no pace to measure: WPS_MAX was fitted on episode 10's
lines of six words and more, and a three-word question spends its time on three
short words (ep13's 'What are we?' at 0.69 s, refused as rushed on every roll)."""


def words_per_second(text: str, seconds: float) -> float:
    """The pace of the line, from the words it was given and the seconds measured;
    0 (not measured) for a line under PACE_MIN_WORDS."""
    words = len(normalised(text))
    if seconds <= 0 or words < PACE_MIN_WORDS:
        return 0.0
    return words / seconds


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


def cpu_transcriber() -> Callable[[Path], str]:
    """Local whisper when importable, ComfyUI's otherwise: the ear before the router."""
    try:
        return transcriber()
    except NoTranscriber:
        return comfy_transcriber()


def any_transcriber() -> Callable[[Path], str]:
    """The ear the device router picks (owner 2026-10-18: GPU when idle, CPU when
    rendering): the CPU ear above, unchanged, or the GPU worker with it behind
    (studio/routed_whisper)."""
    from studio import routed_whisper
    return routed_whisper.routed(cpu_transcriber)
