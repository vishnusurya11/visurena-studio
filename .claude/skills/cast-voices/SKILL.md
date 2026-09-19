---
name: cast-voices
description: Write a Qwen3-TTS VoiceDesign instruction for every character in a book — grounded in region, nationality, body and speech from the dossier — assign each a register nobody else holds, render, gate on measured similarity, and file it under the character at book level. Use when casting or recasting voices for a title.
---

# Cast the voices

**Cast just in time (owner, 2026-09-18).** Cast only the speakers the episode
being built needs, and reuse every voice already filed under `cast/`. Don't
cast the whole book up front. Voices are still FILED at book level, as below,
so episode 5 reuses episode 1's narrator. WotW ep01 cast three (narrator,
Ogilvy, wife); ep02 added only Henderson and the newspaper boy.

Casting is a BOOK-level stage, run once after the screenplay and before any
production. `library/<book>/` holds `trailer/`, `video/`, `audiobook/` and
`publish/` as siblings, and all four need the same Holmes. A voice cast inside
the trailer is filed under the trailer, so the episode builds its own and gets
a different person.

Read `subskills/10-casting/VOICEDESIGN.md` before writing a single instruction.
It carries the official schema, the five control types, and every number this
install has measured. This file is the procedure; that one is the contract.

## Run it

```
uv run python scripts/cast/cast_voices.py <codex_id>
uv run python scripts/cast/cast_voices.py <codex_id> --only sherlock_holmes,john_watson
uv run python scripts/cast/cast_voices.py <codex_id> --recast   # collisions only
```

Free. Local GPU, no credits. ~25 s per design clip on a 4090, plus one LLM
call per character to write the instruction.

## The five steps, and why each exists

### 1. Assign the register BEFORE anything is written

`studio/voice_register.py`. Sort the cast by how much of the book they carry,
split by gender, spread across the band that gender uses (male 75–175 Hz,
female 170–265), and interleave so the two biggest parts land furthest apart.

**This step is the whole reason the first cast failed.** Twenty-three sheets
written independently, each differing from the others on nine of twelve
attributes, produced five voices of which **six of ten pairs measured at or
above the 0.65 same-person floor** — Brigham Young against Jefferson Hope at
0.79, Watson against Holmes at 0.70. Every male had been written into the
82–110 Hz band, because "a deep, authoritative man" is the honest answer for
four different men when each is considered alone. A voice written in isolation
cannot avoid a voice it has never been told about.

So the slot is handed to the writer, not chosen by it, and the writer is told
who already holds which.

### 2. Write the instruction from the dossier

`studio/voice_persona.py`. One `VoiceInstruction` per character, in both
official shapes:

- **Background Information** — `Character Name / Voice Profile / Background /
  Presence / Personality`. The default for a character. `Background` carries
  REGION, NATIONALITY and the work that shaped the mouth; `Presence` carries
  THE BODY. Both come off the dossier the analysis stage already wrote:

  | field | dossier source |
  |---|---|
  | Voice Profile | `profile.voice` + the assigned register |
  | Background | `profile.motivation`, `arc`, `role_in_story`, setting, era |
  | Presence | `profile.physical` — age, height, build, health, dress |
  | Personality | `profile.mental` |

- **The 12-attribute sheet** — official names, official order: `gender, pitch,
  speed, volume, age, clarity, fluency, accent, texture, emotion, tone,
  personality`.

The contract refuses three things, each of which shipped once:

| refusal | why |
|---|---|
| `pitch` with no hertz number | asked 95/115/85/230, measured 95/110/82/241 — it is the only way to place a voice on purpose |
| fewer than 3 of pitch/speed/volume/emotion/tone describing a CHANGE | the blog calls it Gradual Control; a sheet of fixed settings renders flat |
| no accent named | not naming it leaves it guessed, not unset |

### 3. Render the identity clip

`audio_qwen3tts_design`, one clip per character, the same passage for everyone
so the VOICE is the only variable. Cached by character — re-running never
re-invents a voice, because re-designing gives a different person
(QwenLM/Qwen3-TTS#80).

### 4. Gate on MEASURED similarity, never on text

`voice.similarity` — resemblyzer GE2E cosine, every pair. **At or above 0.65
is the same person: recast the lighter part into a free slot and re-render.**

A textual diff is not a gate and never was. Nine-of-twelve attributes differing
produced voices measuring 0.79 apart. Only the audio settles it.

### 5. Listen

`studio/voice_qc.py` — Whisper transcribes each clip and scores word error rate
against the line it was asked to say, plus a runaway-length check. Every other
gate in this repo measures the SIGNAL; only this one measures the CONTENT, and
a generative TTS returns confident audio of the wrong words. First run over 30
clips: **14 failed**, and the owner had caught one by ear.

## Where it lands

```
library/<book>/cast/<character>/
    character.json          the dossier
    portrait.png            the face
    voice/
        voice.json          instruction, both shapes, register, provenance
        design.wav          the voice as cast
        <feeling>.wav       re-performances of that one clip
        voice_qc.json       what the gate heard each take say
```

`cast_home.ready(book, character)` answers "is this character usable?" in one
call — card, portrait, voice, checked.

## Failure ladder

| symptom | do this |
|---|---|
| two voices measure ≥ 0.65 | recast the lighter part into a free slot, re-render, re-measure |
| a clip fails the listen gate | re-render with the next seed; three failures means the text is the problem |
| the voice ignores the asked register | check `pitch` actually carries a number; prose alone drifts |
| everything sounds flat | the sheet is static — apply Gradual Control to pitch, speed, volume |
| the accent is wrong | name it AND give it a reason in `Background`; an unexplained accent drifts American |

## Never

- Never cast inside a production folder.
- Never re-run VoiceDesign to get an emotion — design once, edit that clip.
- Never accept a textual difference as evidence two voices differ.
- Never ship a clip nothing has listened to.
