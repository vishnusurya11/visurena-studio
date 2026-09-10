# Qwen3-TTS VoiceDesign — the instruction contract

Source of truth: the Qwen3-TTS release post (2026-01-21), "Voice Design"
samples. Everything below is quoted or measured, not inferred. When this file
and a memory disagree, this file wins.

## The five control types the model was shown

The blog demonstrates five distinct instruction SHAPES. They are not
interchangeable, and picking the wrong one is most of why a voice comes out
generic.

| type | shape | use it for |
|---|---|---|
| Acoustic Attribute Control | the 12-attribute sheet | a voice you want to specify exactly |
| Age Control | one sentence leading with age | a quick sketch |
| **Gradual Control** | the sheet, with values that CHANGE across the line | any line with a turn in it |
| Human-likeness | free prose, conversational | a voice that must sound unperformed |
| **Background Information** | Name / Voice Profile / Background / Presence / Personality | a CHARACTER, where region and history should shape the voice |

For a book cast, **Background Information is the default** and the
12-attribute sheet is the precision instrument. Use the sheet when a specific
register must be hit (to separate two voices that collided); use Background
Information when the character has a life the model can derive a voice from.

## The 12 attributes — exact names, exact order, lowercase

```
gender: Male.
pitch: Low male pitch with significant upward inflections for emphasis and excitement.
speed: Fast-paced delivery with deliberate pauses for dramatic effect.
volume: Loud and projecting, increasing notably during moments of praise and announcements.
age: Young adult to middle-aged adult.
clarity: Highly articulate and distinct pronunciation.
fluency: Very fluent speech with no hesitations.
accent: British English.
texture: Bright and clear vocal texture.
emotion: Enthusiastic and excited, especially when complimenting.
tone: Upbeat, authoritative, and performative.
personality: Confident, extroverted, and engaging.
```

That is a verbatim official example. Note what it is NOT: not `pace`, not
`timbre`, not `intonation`. `speed`, `texture`, `tone`. Order matters enough to
copy; age sits FIFTH, after volume, not beside gender.

`tone` and `emotion` are different attributes and must not be merged: emotion
is what the speaker feels, tone is the attitude the delivery projects. The
official example splits them — "Enthusiastic and excited" against "Upbeat,
authoritative, and performative".

## Gradual Control — the thing most instructions miss

Read the official values again. Almost none of them are static:

- *"Artificially high-pitched, **slightly lowering after the initial laugh**."*
- *"**Rapid during the laugh, then slowing** to a deliberate pace."*
- *"Loud laugh **transitioning to** a standard conversational level."*
- *"Forced amusement **shifting to** feigned resignation."*
- *"Begins conversational, **escalates quickly** to loud and forceful."*
- *"**Starts** measured, **then accelerates** rapidly during emotional outburst."*
- *"Shifts **abruptly from** neutral acceptance **to** intense resentment and anger."*

A line has a shape. An instruction that names one setting gets one setting
back — flat. **At least `pitch`, `speed`, `volume`, `emotion` and `tone` should
say what they do ACROSS the line** whenever the line has a turn in it. This is
the single highest-value change available to a cast sheet.

## Background Information — the format for a character

Verbatim official example:

```
Character Name: Marcus Cole
Voice Profile: A bright, agile male voice with a natural upward lift, delivering
  lines at a brisk, energetic pace. Pitch leans high with spark, volume projects
  clearly—near-shouting at peaks—to convey urgency and excitement. Speech flows
  seamlessly, fluently, each word sharply defined, riding a current of dynamic rhythm.
Background: Longtime broadcast booth announcer for national television, specializing
  in live interstitials and public engagement spots. His voice bridges segments,
  rallies action, and keeps momentum alive—from voter drives to entertainment news.
Presence: Late 50s, neatly groomed, dressed in a crisp shirt under studio lights.
  Moves with practiced ease, eyes locked on the script, energy coiled and ready.
Personality: Energetic, precise, inherently engaging. He doesn't just read—he propels.
  Behind the speed is intent: to inform fast, to move people to act.
```

**Why this is the right default for a book cast.** Every field maps onto a
dossier the analysis stage already wrote:

| Background Information field | dossier source |
|---|---|
| Character Name | `name` |
| Voice Profile | `profile.voice` + the register decisions |
| Background | `profile.motivation`, `arc`, `role_in_story`, region and era |
| Presence | `profile.physical` — body, age, build, health, dress |
| Personality | `profile.mental` |

`Presence` is where the BODY goes, and body is what a description of a voice
usually leaves out: a six-foot lean man does not resonate like a heavy one, a
wounded army surgeon does not breathe like a fit one, and a man who has spent
years in a desert does not sound like one who has spent them indoors. Say the
body and the model infers the instrument.

`Background` is where REGION and NATIONALITY go, and they must be stated as
FACTS OF THE PERSON, not only as an `accent:` line — where a man grew up, what
work shaped his mouth, and what century he speaks in.

## Accent

`accent:` is a real attribute and the blog uses it plainly: "British English",
"American English", "General American English", "标准普通话". Name it.

The repo's older `voice.DELIVERY` warns this model drifts American when an
accent is mentioned, and answers by refusing to mention one — that is wrong.
Not naming an accent does not leave it unset, it leaves it GUESSED. State it,
and in `Background` say where the person is FROM, so the accent has a reason.

## What is measured, on this install

- **A hertz anchor in `pitch` is honoured almost exactly.** Asked 95 / 115 /
  85 / 230 Hz across four characters; measured 95 / 110 / 82 / 241. The
  official examples do not use numbers, but numbers work here and are the only
  way to place a voice in the register deliberately.
- **A prose instruction averages; a sheet does not.** The repo's old
  three-sentence `voice_instruct` gave every character the same narrator at a
  different age.
- **The model renders exactly what it is told, including the mistake.** Holmes
  cast as "dry and thin with a reedy edge" came back at 238 Hz — higher than a
  young woman at 186 — and audibly nasal.
- **WORDS DIFFERING IS NOT VOICES DIFFERING.** Twenty-three sheets that
  differed on 9 of 12 attributes produced five voices of which **6 of 10 pairs
  measured above the 0.65 same-person floor** (Brigham Young vs Jefferson Hope
  0.79; Watson vs Holmes 0.70). Only the one woman separated. The cause: every
  male was cast between 82 and 110 Hz. A textual diff is not a gate.

## The rules

1. **Pick the shape first.** Background Information for a character; the
   12-attribute sheet when a register must be hit exactly.
2. **Use the official attribute names and order.** `speed`, `texture`, `tone`.
3. **Describe the ARC, not a setting**, on pitch, speed, volume, emotion, tone.
4. **Put the body in `Presence` and the region in `Background`.**
5. **Name the accent**, and give it a reason in the background.
6. **Spread the cast across the register on purpose.** Two men in the same
   80–110 Hz band with the same "strong chest resonance" are one man.
7. **Gate on MEASURED similarity, never on text.** Render the designs, take
   every pair, refuse anything at or above 0.65, recast the collision.
8. **Then listen** — `voice_qc` — because a voice that is distinct and wrong
   is still wrong.
