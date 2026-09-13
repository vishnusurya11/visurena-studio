"""Does the music bed SING?  The gate that should have existed already.

Episode 3 shipped with its bed singing invented English verse under the
narration for 101 of 157.8 seconds -- 64 % of it.  Nothing caught it, because
nothing between `assemble.bed()` and the mix ever listened: the prompt said "no
vocals" and that was taken as proof.  It has now been measured as insufficient
TWICE, on two different models, for two different reasons:

  * MiniMax Music 3 sang its own stage directions, because a parenthetical is a
    sung backing line in that corpus (`music_tone`, the trailer).
  * YuE2 sang invented verse, because YuE2 HAS no instrumental token -- an empty
    lyrics field is the only instrumental -- and it was handed MiniMax's
    exception by a docstring that credited the finding to the wrong model.

A prompt is an intention.  This is the measurement.

THE FIRST VERSION OF THIS FILE WAS ALSO A NO-OP.  It expected whisper SEGMENTS
(`no_speech_prob`, `compression_ratio`), and both of the studio's transcribers
return a PLAIN STRING, so its `isinstance(heard, list)` guard was always False
and it approved every bed without hearing one.  The lesson is the same one that
put the singing in the episode: a check that cannot fail is not a check.  Hence
`UNVERIFIED` -- being unable to listen is its own answer here, never silence.

THE JUDGEMENT IS THE VOCABULARY.  Whisper on an instrumental returns a tiny
stock of filler -- "Thank you.", "You", "Mm-hmm." -- or one phrase looped
("I'm sorry, but I'm sorry, but ..."), however long the file runs.  Sung verse
returns many DISTINCT words.  That separates them with no per-segment metadata:
episode 1 and 2's clean beds transcribed to under 5 distinct words; episode 3's
to more than 25.
"""
from __future__ import annotations

import re
from pathlib import Path

DISTINCT_WORDS = 12
"""Distinct words at or above which a transcript is a lyric, not an artefact.
MEASURED: clean beds 1-5, the singing bed 25+.  The gap is wide enough that the
exact threshold does not matter; it is set near the bottom of it."""

MIN_WORDS = 8
"""Below this there is nothing to judge, whatever the vocabulary."""

UNVERIFIED = "the bed could not be listened to, so it is unverified"
"""Being unable to measure is NOT a pass.  The caller decides what to do about
it, but it never reads as silence."""


def words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", (text or "").lower())


def distinct_words(text: str) -> int:
    """How big a vocabulary the transcript has.  A loop of one phrase, repeated
    two hundred times, is still that phrase's handful of words."""
    return len(set(words(text)))


def sings_text(text: str | None) -> bool:
    """Is somebody singing words in this bed?"""
    heard = words(text)
    return len(heard) >= MIN_WORDS and distinct_words(text) >= DISTINCT_WORDS


def refuse_text(text: str | None) -> str:
    """The reason not to use this bed: "" to go ahead, `UNVERIFIED` when unheard."""
    if text is None:
        return UNVERIFIED
    if sings_text(text):
        return (f"the bed sings: {' '.join(words(text)[:24])}...\n"
                f"  a music model given any lyric-shaped string writes a song to fit. "
                f"YuE2's instrumental is an EMPTY lyrics field; ACE-Step's is `[inst]`.")
    return ""


def listen(bed: Path, transcribe=None) -> str | None:
    """The bed's transcript, or None when no ear was reachable.

    `transcribe` is injected in tests; the default reaches for local whisper and
    falls back to ComfyUI's.  NOTE that the ComfyUI path queues behind whatever
    the GPU is doing, so a bed made while takes render will wait its turn."""
    try:
        if transcribe is None:
            from studio import voice_qc

            transcribe = voice_qc.any_transcriber()
        heard = transcribe(Path(bed))
    except Exception:                     # noqa: BLE001 -- any failure is "unheard"
        return None
    return heard if isinstance(heard, str) else None


def refuse(bed: Path, transcribe=None) -> str:
    """The reason not to use this bed, or "" to go ahead."""
    return refuse_text(listen(bed, transcribe))


def refused_name(bed: Path) -> Path:
    """A free name to keep a refused bed under.

    A model that sings once tends to sing again, so the second refusal met a
    `bed.sings.wav` that already existed and raised FileExistsError -- killing
    the assemble after four minutes of GPU. `take_dq.next_fail` wrote the rule
    down: disk knows. Read the name off what is there, never off a counter."""
    bed = Path(bed)
    first = bed.with_suffix(".sings.wav")
    if not first.exists():
        return first
    k = 2
    while bed.with_suffix(f".sings{k}.wav").exists():
        k += 1
    return bed.with_suffix(f".sings{k}.wav")
