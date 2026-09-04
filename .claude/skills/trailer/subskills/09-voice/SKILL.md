---
name: trailer-voice
description: Speak the chosen lines with local Qwen3-TTS — design one reference voice per character from the cast card, clone every line from it, gate on speaker similarity, measure the seconds, and hand the editor files not predictions.
---

# Voice

`studio/voice.py` (to build), two ComfyUI workflows under `workflows/`,
outputs under `library/<book>/trailer/voice/`. Evidence:
`docs/analysis/research/trailer-iconic-lines-and-moments.md` §1.6, §4, §7.
Engine: **Qwen3-TTS 1.7B** (VoiceDesign, CustomVoice, Base) installed in the
user's ComfyUI as `qwen3-tts-comfyui`; local, free, 24 kHz mono.

## The brick — Brick 1 again: a voice is BOUND by a reference clip, never described per line

`generate_voice_clone()` takes **no `instruct`** (signature read from the
installed pack); `generate_custom_voice` drops it on 0.6B. The same instruct
rendered twice drifts timbre ("distant vs close", third-party, PROPOSED
until `test_same_instruct_five_seeds_spreads_wider_than_clone_five_seeds`
runs locally). The pack's own docstring says it: **Voice Design once →
SaveVoice → clone every line.**

## The recipe, per character with a bound line

1. **Instruct** from the cast card + analysis, English, 15–40 words:
   age band ("a man in his late thirties"), gender, register from
   `profile.mental` ("precise, quick, dry"), class/role ("educated London
   professional"), texture from epithets ("lean, clear, slightly nasal"),
   measured pace. **Never** name an accent (drifts to US), a real actor
   (blocked), or a duration ("finish in 5 seconds" does nothing). Era goes
   into *diction* ("formal, clipped Victorian phrasing"), not accent.
2. **Reference**: render a neutral 8–12 s clip with that instruct on a fixed
   seed — a sentence of the character's own from the pool, NOT a trailer
   line. `SaveVoice` → `voices/<char>.calm.{wav,qvp,txt}`.
3. **Emotion is a second reference**, not an instruct: `voices/<char>.peak.*`
   from the same instruct + "speaking urgently, raised pitch, fast". Two
   references, calm and peak, are the whole emotion vocabulary a trailer
   needs.
4. **Lines**: `FB_Qwen3TTSVoiceClone` from the saved prompt, `ref_text`
   supplied (else you are in x-vector mode), one seed per **character**,
   `max_new_tokens` ≤ 512 for a ≤ 12-word line (the runaway failure mode).
5. **Gate** (mirrors `identity.py`): speaker-embedding cosine between each
   rendered line and its reference ≥ 0.75 (`resemblyzer==0.1.4`;
   `speechbrain==1.1.1` ECAPA if it will not build against the torch pin).
   Below: re-roll with a new seed, three tries, then the line becomes a
   card. The threshold is untested — `test_threshold_separates_two_designed_voices`
   on 20 lines before trusting it.
6. **Measure, do not predict.** Every rendered line writes
   `lines/<beat>.<n>.json {text, speaker, register, seed, seconds, similarity}`.
   `05-dialogue` chooses the line for the slot from `seconds`. The speaking
   rate belongs to the *designed voice*, not to English: fit
   `seconds = a·vowel_groups + b` per voice from 20 rendered lines →
   `voice/<char>/rate.json`, `@pytest.mark.local`, fail if residual P90 > 15%.
   The old `0.22 × vowels + 0.45` never met a rendered line.
7. **Post**: HPF 90 Hz, +2 dB at 3 kHz, light small-room reverb (pre-delay
   ~15 ms, RT ~0.4 s), mono centre, −20 LUFS-S per line before the ducker.
   Normalise per character, not per line — 4.8 of the measured 7.1 dB spread
   is *between* characters and is characterisation.

`DialogueInferenceNode` is for continuous scenes with `pause_*` timing; a
trailer wants each line as its own file on its own slot. Per-line clone path.

## Who speaks what

- A first-person narrator (Watson, Utterson) is a character with a card;
  design them. `01-story` must emit `narrator` per book.
- A pure omniscient narrator: design "the author's voice" from the author's
  era and gender, use it only for the title-echo line, prefer the card.
- No speaker (unattributed source quote) → card, never a voice.
- Retire `audio_qwen3tts_tts_single_speaker` for this use: it clones
  `voice_narrator_attenborough.wav` — a real person's voice on a commercial
  trailer.

## Workflows (API-format JSON + manifest, as `comfy.py` expects)

```
audio_qwen3tts_design_reference.json
  1 FB_Qwen3TTSVoiceDesign     {text, instruct, model_choice=1.7B, language=English, seed}
  2 FB_Qwen3TTSVoiceClonePrompt {ref_audio<-1, ref_text=text}
  3 FB_Qwen3TTSSaveVoice        {voice_clone_prompt<-2, audio<-1, ref_text, filename}
  4 SaveAudio                   {audio<-1, filename_prefix}
  inject: text, instruct, seed, filename, filename_prefix

audio_qwen3tts_clone_line.json
  1 FB_Qwen3TTSLoadSpeaker {filename}
  2 FB_Qwen3TTSVoiceClone  {target_text, voice_clone_prompt<-1, ref_text<-1,
                            model_choice=1.7B, seed, max_new_tokens=512}
  3 SaveAudio              {audio<-2, filename_prefix}
  inject: filename, target_text, seed, max_new_tokens, filename_prefix
```

Layout under `library/<book>/trailer/voice/`:
```
voices/<char>.calm.wav  .qvp  .txt      reference + prompt + ref_text
voices/<char>.peak.wav  ...
lines/<beat_id>.<n>.wav                 24 kHz mono, raw
lines/<beat_id>.<n>.json                text, speaker, register, seed, seconds, similarity
voice.json                              instructs, seeds, gate results, cards[]
```
Every line file is keyed on its recipe (text, voice reference digest, seed,
tokens) — a cache keyed on the beat id would re-use a stale read after the
line changed, the defect this pipeline has had three times.

## The mix (`08-assemble` owns the filter; this is the spec)

No duck exists in `assemble.py` today; the 12–15 dB rule was a paragraph.
PROPOSED: each line at −20 LUFS-S; the bed at −26 LUFS-S inside the line's
window (6 LU under), untouched outside; attack 160 ms, release 0.8–1.2 s;
one window per line. In build sections split the bed (`acrossover=split=250
4000`) and sidechain the mid band only, so the low end keeps building under
the voice. Gate: `test_line_sits_six_lu_over_bed_in_its_window` on a
synthetic bed + tone through `ebur128`.

## Tests that cost nothing

Contract tests use a `FakeComfy` returning a recorded wav. Everything that
renders is `@pytest.mark.local`. No test calls a paid API; Qwen3-TTS is free.
