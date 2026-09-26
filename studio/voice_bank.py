"""A voice bank per character: one timbre, several emotions, from the book.

WHY.  `voice.clone_line` has ONE reference per character and no emotional
control, so every line comes out at the same temperature -- Holmes stating a
deduction and Hope naming the hour of his revenge read identically.  A trailer
lives on exactly that difference.

THE SHAPE, which the installed IndexTTS2 node supports natively: it takes a
speaker reference (`ref_audio`) for the TIMBRE and a SEPARATE emotion
reference (`emotion_audio`) for the delivery, with `emotion_alpha` for how far
to push it.  So the bank is built once per character -- Qwen3-TTS speaks a
long sentence in that character's own register, once per emotion -- and then
every trailer line is said with the timbre of the calm clip and the feeling of
whichever emotion the beat calls for.

The sentences are not the trailer's lines.  They are long on purpose: a
reference clip has to carry the voice, and a two-word line carries nothing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

TIMBRE = "calm"
"""The read with nothing pushed.  Its clip is the TIMBRE anchor: the speaker
reference, carrying the voice rather than a mood."""

EMOTIONS = (TIMBRE, "curious", "cold", "urgent", "grieving", "threatening")
"""What a TRAILER needs, not what the engine happens to name.

An earlier draft used IndexTTS2's slider vocabulary -- Happy, Angry, Sad,
Afraid -- which was choosing by the tool instead of the job: `happy` is nearly
useless in a detective mystery, and `curious` (the lead enjoying a problem, and
the whole register the book gives Holmes) has no slider at all.  Neither engine
constrains us: Qwen3-TTS takes a free-text instruct, and IndexTTS2's emotion
REFERENCE route accepts any clip.  Only its sliders are a closed set, and we
are not using them."""

BASELINE = {
    "calm": (
        "I have looked at this a long while, and I know now what it is. "
        "There is no hurry in it, and there never was. The thing has "
        "already happened, and no amount of turning it over will make it "
        "happen differently. So I will sit with it a moment longer, and "
        "then I will get up, and I will do what needs doing. What is done "
        "is done, and whatever is left of it will keep until the morning "
        "comes."),
    "curious": (
        "I have looked at this a long while, and I know now what it is. No "
        "-- wait. There is something here I did not see before, and the "
        "more I look at it the less it agrees with the rest. Why that way "
        "round? Why there, of all the places it could have been? Somebody "
        "went to a great deal of trouble over this, and people do not take "
        "trouble for nothing. I should very much like to know what for."),
    "cold": (
        "I have looked at this a long while, and I know now what it is. I "
        "knew before you opened your mouth. Do not trouble yourself to "
        "explain it to me; the explanation is of no interest, and it would "
        "only be a worse version of what I can already see. You may sit "
        "down, or you may stand. It makes no difference to me either way. "
        "We both know how this ends."),
    "urgent": (
        "I have looked at this a long while, and I know now what it is. It "
        "has to be now, before the hour turns. Get up. Do not stop to ask "
        "me why and do not stop to gather anything, because there is no "
        "time for it and there will be less time in a minute. Every second "
        "we stand here is a second we cannot buy back. Move. Move now, and "
        "I will explain it to you on the road."),
    "grieving": (
        "I have looked at this a long while, and I know now what it is. It "
        "is gone. There is nothing left of it but this, and this is not "
        "very much to be left with. I keep expecting to turn around and "
        "find it where it was, and it is never where it was. I would give "
        "the rest of what I have, all of it, to hold one hour of it back "
        "again. One hour would be enough."),
    "threatening": (
        "I have looked at this a long while, and I know now what it is. You "
        "will answer for it. Not tonight, perhaps, and not tomorrow, and "
        "you may sleep well enough in the meantime for all I care. But you "
        "will answer, and when it comes you will know my face before I have "
        "said a word. I have waited a long time already. I can wait a "
        "little longer."),
}
"""The SAME passage for every character, so the only variable is the voice.

Each one opens on the identical sentence -- "I have looked at this a long
while, and I know now what it is" -- and then turns.  That shared opening is
the baseline: laid side by side, two characters' calm clips differ only in
timbre, and one character's calm and angry clips differ only in feeling.  The
turn is what an emotion reference has to carry, and it is what a one-shot
engine (IndexTTS2, Fish) replicates onto a new line.

Long on purpose.  A reference clip has to give the engine somewhere to move:
sentences that start and stop, a phrase that lands harder than the one before
it, a place to breathe.  Forty words of even prose gives it one colour to copy.

Character-neutral on purpose: no name, no period, no plot.  A passage that
mentions a hansom cannot be reused for the next book."""

DELIVERY = {
    "calm": (
        "evenly and unhurried, as a statement of fact. The pitch sits in "
        "the middle of the range and stays there. Let the pauses between "
        "sentences be real pauses, unbothered, with a full breath in them, "
        "and let the ends of the sentences fall rather than lift."),
    "curious": (
        "lightly and quickly, as though following a thought that is still "
        "arriving. The pitch lifts at the questions and does not fully come "
        "back down. Let the pace change inside the passage, a pause where "
        "something is noticed and then a run of words once it is, and let a "
        "little pleasure show through, because this is a man enjoying "
        "himself."),
    "cold": (
        "flat and precise, giving nothing away. Every word is placed "
        "deliberately and none is leaned on. The pitch is level and "
        "slightly low, the pace is even, the volume is moderate throughout, "
        "and the pauses are exact rather than felt. Nothing lifts at the "
        "ends of the sentences. There is no warmth in it and no heat "
        "either."),
    "urgent": (
        "quickly and pressed, the words close together with no room between "
        "them. The breath is short and taken mid-phrase rather than at the "
        "ends. The pitch is raised and level, the consonants are hard, and "
        "every sentence pushes into the next one without settling."),
    "grieving": (
        "low and unsteady, carrying weight the words never name. The pace "
        "drags behind the beat and the pitch sits under its usual place. "
        "Let the breath catch once, somewhere it was not planned, and let "
        "the voice thin out at the ends of the sentences as though it is "
        "running out of the will to finish them."),
    "threatening": (
        "quietly and deliberately, with the threat under the words rather "
        "than in them. The volume stays low, lower than the room needs, and "
        "the pace is slow and even, which is what makes it frightening. The "
        "pitch sits at the bottom of the range. Let the pauses run slightly "
        "too long, and let the last sentence land softer than the one "
        "before it."),
    "shouting": (
        "as a shout, at the top of the voice, calling out over noise to someone who must "
        "hear it now. The pitch jumps high and stays high, the volume is loud, "
        "the vowels are open and pushed, the consonants hit hard, and the breath "
        "is taken fast and loud between the phrases. Nothing is held back."),
    "hushed": (
        "barely above a whisper, close to the listener, so no one else will hear. "
        "The breath is audible and the voice is thin and soft, the pitch low and "
        "level, the pace slow and careful, and the ends of the phrases fall away "
        "into the breath."),
    "exultant": (
        "with a sudden burst of joy and disbelief, as though the thing just "
        "happened in front of you. The pitch leaps up and rings, the volume is "
        "raised, the pace quickens, and the words tumble out with a laugh "
        "caught behind them."),
}
"""How each one is SPOKEN, in the words a director gives an actor.

Delivery, never adjectives: pace, pitch, breath, attack, where a word lands.
An earlier draft said "hard and clipped" and stopped there -- three words is a
LABEL, and a label gives the engine nothing to act on.  These say what the
mouth and the breath actually do."""


def bank_text(speaker: dict, emotion: str) -> str:
    """The passage this character reads for `emotion`.

    The SAME words for every character, deliberately.  An earlier draft used
    each character's own quotes, which sounds right and is wrong for this job:
    when the content differs, a comparison between two voices measures the
    content.  Holding the words fixed makes the voice the only variable, and
    holding them fixed ACROSS emotions makes the feeling the only variable in
    the other direction -- which is exactly what an emotion reference is for.
    """
    del speaker                      # the identity is the instruct's business
    return BASELINE.get(emotion, BASELINE[TIMBRE])


def instruct(speaker: dict, emotion: str) -> str:
    """The delivery note Qwen conditions on: who is speaking, and how.

    `voice.voice_instruct` already builds the who -- sex, age, role and the
    book's own line about how they speak, in 15-40 words -- and it learned the
    hard way to never name an accent."""
    from studio.voice import DELIVERY as NEUTRAL, voice_instruct
    who = voice_instruct(speaker).replace(NEUTRAL, "").strip()
    return f"{who} Speak this {DELIVERY.get(emotion, DELIVERY[TIMBRE])}."


def clip_path(out_dir: Path, speaker_id: str, emotion: str) -> Path:
    return Path(out_dir) / f"{speaker_id}-{emotion}.wav"


def build(speaker: dict, out_dir: Path, render: Callable,
          emotions: tuple[str, ...] = EMOTIONS) -> dict[str, Path]:
    """One clip per emotion for this character, rendered once and kept."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    bank = {}
    for emotion in emotions:
        out = clip_path(out_dir, speaker["id"], emotion)
        out.parent.mkdir(parents=True, exist_ok=True)     # the renderer writes here
        if not out.exists():
            render(bank_text(speaker, emotion), instruct(speaker, emotion), out)
        bank[emotion] = out
    return bank


def timbre_of(bank: dict[str, Path]) -> Path:
    """The clip a line's TIMBRE comes from: the calm read, or the first there."""
    return bank.get(TIMBRE) or next(iter(bank.values()))


def emotion_for(function: str, why: str = "", written: str | None = None) -> str:
    """Which emotion a line wants: what the PAGE said, or a guess if it said nothing.

    The guess is a fallback and a poor one.  MEASURED: it read Hope's revenge
    declaration as grieving and three of Holmes' deductions as urgent, because
    "escalation" contains "escalat".  A page that names its own emotions never
    reaches this code."""
    if written:
        return written
    text = f"{function} {why}".lower()
    if any(w in text for w in ("threat", "revenge", "avenger", "answer for")):
        return "threatening"
    if any(w in text for w in ("grief", "lost", "taken", "mourn", "buried")):
        return "grieving"
    if any(w in text for w in ("turn", "escalat", "pursuit", "chase", "hunt")):
        return "urgent"
    if any(w in text for w in ("deduc", "method", "evidence", "reason", "question")):
        return "cold"
    return TIMBRE
