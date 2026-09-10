---
name: trailer-casting
description: Cast a voice for every character in a book from a twelve-line sheet, re-perform its feelings from the one designed clip, gate every clip by listening to it with Whisper, and file the result under the character at book level. Use when building or fixing character voices, emotion takes, or the cast folder.
---

# Casting

`studio/voice_design.py` + `studio/voice_qc.py` + `studio/cast_home.py`.
Outputs under `library/<book>/cast/<character>/`, **not** under a production.

## The brick — a character is ONE THING, cast ONCE, and CHECKED BY LISTENING

Three rules, each of which was learned by a failure on a real file.

### 1. A voice is a SHEET of decisions, never a paragraph of prose

Qwen3-TTS VoiceDesign's Multi-Attribute Control takes a LABELLED SHEET, one
attribute per line, and the shape is the point: prose lets the model average,
a sheet cannot. The repo's old `voice.voice_instruct` wrote three sentences
capped at 40 words and every character came back as the same narrator at a
different age.

**Every line must name something a microphone can capture.** Measured
2026-09-09 on 19 clips: "dry and thin with a reedy edge" rendered Holmes at
**238 Hz — higher than Lucy Ferrier at 186 and level with a seventy-year-old
woman at 242** — and audibly nasal. It rendered exactly what it was told.
Rewritten to "low and deep, a bass-baritone around 95 Hz" it came back at
**95 Hz**. The hertz number is honoured almost exactly: asked 95/115/85/230,
got 95/110/82/241 across four characters.

So: a frequency, a word rate, a resonance, a direction of pitch movement.
Not "sentences arriving already finished". `Personality` says how it is
DELIVERED, never what the character is like — "decent, loyal, plain-spoken"
has no acoustic correlate and renders nothing.

**Never compare to another character.** Watson's pitch read "sitting lower
than his companion"; the model renders one voice at a time and has never
heard Holmes. Anchor to a number.

**Age is an attribute.** The first sheet omitted it entirely, and age moves
timbre further than almost anything else.

**Accent is named, and named hard**, in one constant per accent
(`RP`, `LONDON`, `FRONTIER`, `PULPIT`) so a single edit re-accents everyone
who shares it. `voice.DELIVERY` records that this model drifts American when
an accent is mentioned and answers by refusing to mention one — but not
naming an accent leaves it GUESSED, not unset. State it and negate the drift:
"British, NOT American. No American vowels."

### 2. Design ONCE; a feeling is an EDIT of that clip, never a new design

Re-running VoiceDesign **re-invents** the voice (QwenLM/Qwen3-TTS#80), so an
emotion bank built by re-designing has no reason to sound like the same person
twice. Design one identity clip, then re-perform it.

The two engines, and why each has the job it has:

| engine | job | why |
|---|---|---|
| Qwen3-TTS VoiceDesign | invents the voice | free-text sheet, so hertz and words-per-minute are specifiable |
| Step-Audio-EditX | re-performs the feeling | takes finished audio + one tag, holds timbre; Apache 2.0 |

EditX cannot design — it has no voice-description input, only 14 emotion tags
and 32 style tags. Qwen cannot hold identity across calls. Neither replaces
the other.

**CustomVoice is not a route.** Its nine speakers are learned token embeddings
added by speaker-specific fine-tuning, and the checkpoint ships with **no
speaker encoder** — verified in `config.json`: `spk_id` has nine names and
there is no encoder to turn a wav into an embedding. A designed voice cannot
be made into a CustomVoice speaker without training.

### 3. LISTEN to every clip before you ship it

**This is the gate nothing else in the repo performs.** Every other check
measures the SIGNAL — the file exists, the length is right, the loudness is in
band — and none measures the CONTENT. A generative TTS returns confident,
well-formed audio of THE WRONG WORDS and every signal gate passes it.

`voice_qc.check(clip, line)` transcribes with local Whisper
(`large-v3-turbo`), normalises both texts, and compares by **word error rate**.
Two distinct failures:

- **WRONG WORDS** — `error_rate` above `MAX_ERROR_RATE` (0.20). A good clip
  measures under 0.10; a hallucination measures above 0.5, so the boundary is
  wide and its exact value is not load-bearing.
- **RUNAWAY** — the transcript can match while the tail babbles, so length is
  checked separately against the source clip (`MAX_STRETCH` 1.8). Deliberately
  loose: a grieving read is legitimately slower than a calm one.

MEASURED 2026-09-09, first run of the gate over 30 clips: **14 failed, and
every one of them was an EditX edit — all 5 VoiceDesign clips passed at wer
0.00.** The transcripts name the cause: *"Assistant corresponding to the
text"*, *"Assistance corresponding to the hour has come when you must
answer"* — EditX was speaking its own instruction prompt aloud, the chat
template leaking into the decoded audio. Brigham Young failed 5 of 5. The
owner had noticed ONE bad clip by ear; the gate found fourteen.

The transcriber is injected (`check(..., transcribe=fake)`) so the contract
tests offline, free, with no GPU.

## When it runs — after the SCREENPLAY, before any production

Casting is not a trailer step and must never be one. `library/<book>/` holds
`trailer/`, `video/`, `audiobook/` and `publish/` as SIBLINGS, and all four
need the same Holmes — the same face and the same voice. A character cast
inside the trailer is filed under the trailer, so the episode builds its own
and gets a different person, which is Brick 1's failure at a larger scale:
identity that is rebuilt per production is not bound, it is re-guessed.

    A1 intake -> A2 extract -> A3 consolidate -> A4 SCREENPLAY
                                                      |
                                                 CASTING (here)
                                                      |
              +---------------+---------------+-------+-------+
           trailer          song          episode          feature

So `step_02_refs.py`, which rendered reference sheets INSIDE the trailer run,
is the wrong shape: it belongs here, and the trailer's step 02 becomes a BIND
— load the cast, refuse to start if a speaker on the page has none, render
nothing.

## Where it lives — `library/<book>/cast/<character>/`

```
library/<book>/cast/<character>/
    character.json          the dossier
    portrait.png            the face every shot binds to
    voice/
        voice.json          the sheet, and every call that made a take
        design.wav          the voice as cast
        angry.wav  sad.wav  the same voice, re-performed
        voice_qc.json       what the gate heard each take say
```

**Book level, above any production.** A voice cast for the trailer must be
reusable by the audiobook and the episode; filed under `trailer/main/voice/`
it is not. `cast_home.ready(book, character)` answers "is this character
usable?" in one call — card, portrait, voice, checked — which is the question
an unattended run has to ask before it casts a shot or speaks a line, and it
could not be asked while identity was scattered across `analysis/characters/`,
`refs/characters/` and a production folder.

`cast_home.gather(book)` collects the scattered files. It **copies** rather
than moves: the old paths still have 17 readers across 6 files, and a
migration that breaks the pipeline to tidy it is a bad trade.

## The recipe

1. **Cast** — one sheet per character in `voice_design.CAST`, twelve
   attributes, every line acoustic. `distinctions(a, b)` counts how many of
   the twelve two characters were cast differently on; the closest pair in
   Scarlet differs on 9.
2. **Design** — `audio_qwen3tts_design` with `voice_design.instruct(who)`,
   one identity clip, ~20-25 s each on a 4090.
3. **Edit** — Step-Audio-EditX per feeling, from the design clip only.
4. **Listen** — `voice_qc.check` every clip, design and edit alike. Write
   `voice_qc.json` beside the audio.
5. **File** — `cast_home` paths. Never write a voice into a production folder.

## Open, not solved

- **EditX speaks its own prompt** — 14/30 clips said the instruction rather
  than the line: *"Assistant corresponding to the text"*, against a builder
  whose prefix reads "Make the following audio more {emotion}. The text
  corresponding to the audio is: ...". TWO HYPOTHESES TESTED AND BOTH
  CLEARED. (a) The wrapper: `_tts_engine` is a `ComfyUIModelWrapper` around a
  `StepAudioEditXEngineWrapper` around the real `StepAudioTTS`, and
  `edit_single`'s unpack error comes from the middle layer — but calling the
  real impl directly returns a correct `(tensor, 24000)` and STILL leaks.
  (b) The token range: `tts.py:359-364` subtracts 65536 unconditionally, so
  text tokens would decode as garbage — measured, **0 of 135/205/270
  generated tokens fall below 65536**. The model emits valid audio codes that
  decode to the prompt read aloud. Next suspect is the INPUT encode: VQ02 via
  FunASR-Paraformer, which downloads at first call; if the model cannot read
  the input clip, narrating the instruction is exactly the failure it would
  produce. Verify the audio tokens before blaming the decoder.
- **Iteration count is fixed at render time** and should not be. Lucy's third
  angry pass ran 9.36 s against 4.38 s; Holmes's stayed at 3.24 s against
  3.10 s. The gate now catches it; the renderer should stop before it.
- **Only 5 of 23 characters have voices**, and only 3 emotions of the 14
  emotions and 32 styles EditX offers were tried.
- **Which accent phrasing actually reads British** is unmeasured — four takes
  sit in `cast/sherlock_holmes/` awaiting a human ear. No metric settles it.
