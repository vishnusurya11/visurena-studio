---
name: trailer-dialogue
description: Choosing the few lines a trailer can speak, placing them in the music's troughs, and whether to synthesise them at all.
---

# Dialogue

`studio/trailer_dialogue.py`.

## The budget is set by the music, not by taste

A cue's quiet troughs are the only places a line sits without fighting the bed.
Measured: Sherlock's cue holds **one** full line strictly, plus two sub-second
interjections and the over-black slot; Jekyll's holds four or five. Find the
budget AFTER `build_music.py`, never before.

**4-6 lines, 40-60 words, 10-14s of speech, ≤13% of runtime.** Three
independent derivations agree on 4-6.

Duck at most twice. `trailer_fitness()` selects a cue FOR its dynamic range;
ducking 12-15 dB six times punches six holes in the property you paid for.

## What survives with no scene around it

`line_value()` penalises, in order of importance:

- **Replies** — "Do you mean that you are on the right track?" is grammatically
  complete and semantically empty, because its meaning lives in the line
  before. This is the biggest signal and it is not in Lieu's taxonomy.
- **Unbound definite descriptions** — "The ring, man, the ring" sounds
  meaningful and means nothing to someone who has not read the book.
- **Leading pronouns**, causal connectives (a line with a "because" is an
  answer, and a trailer line is a question or a threat), numerals and
  addresses.

Dedupe first: near-duplicate re-drafts cut 673→370 and 650→257 lines. Without
it your top-N is the same line five times.

Split on sentence boundaries before scoring — "You have been in Afghanistan, I
perceive." is stored behind "How are you?" and the famous clause is the child.

## Score and risk are correlated

Emotional peak is what makes a line quotable AND what breaks TTS, so a single
ranked list hands you the worst possible slate. `synthesis_risk()` is
SUBTRACTED: exclamations, dialect elision, >3.2s, and high-arousal emotion tags.

Verified picks at zero risk: *"No data yet."* · *"Will you let me see your
face?"* · *"Man is not truly one, but truly two."*

## Engine

**IndexTTS-2**, and the deciding factor is not emotion — it is **duration
control**. Qwen3-TTS discards `instruct` on its cloning path, so the `emotion`
field has nothing to bind to; but the thing with no workaround is fitting a
line to a measured trough. Only ever compress (0.85-1.0x); expanding a read
produces the drawled cadence that is the audible signature of synthesis.

One seed per CHARACTER, not per line. Supply `reference_text` or you are in
x-vector mode. Normalise per character, not per line — 4.8 of the measured
7.1 dB spread is BETWEEN characters and is characterisation, not jitter.

## The over-black line should be a CARD, not a voice

At the stopdown there is no music, no picture, no room tone and no accent —
every masking mechanism is unavailable at once, and the audience is asked to
attend to one voice for three seconds. It is the most exposed three seconds a
synthetic voice could occupy. Put the sentence in type instead.

## The honest alternative

Woollen's *Schindler's List* had no voice-over and exactly two dialogue
snippets. Every other flaw in this pipeline is deniable — a dark grade is
"moody", an invented sign is below notice at 1.4s. **A synthetic voice is the
one component whose failure the viewer can name**, and naming it reclassifies
the whole piece. Ship three lines and A/B against the music-only cut before
widening.
