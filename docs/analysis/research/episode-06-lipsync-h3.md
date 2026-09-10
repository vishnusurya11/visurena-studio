# Episode lip-sync on H3 — a panel speaks our cloned line

Research, 2026-09-10. Question: can a storyboard panel (Start Frame) plus one
of our own cloned voice lines drive a local MiniMax-H3 take in which the
person in the panel *speaks that line* with moving lips — instead of today's
silent i2v take with the voice laid on afterwards. Two takes were rendered on
this box; every number below is **measured here** unless tagged otherwise.

## 0. The brick

H3 pins a first frame not by masking pixels but by adding a **conditioning
row on the target timeline**: `MiniMaxH3ImageToVideo` stores the frame as a
`minimax_keyframes` entry and the DiT places it at `cond_t = FRAME_RESCALE ×
frame_idx` (`comfy/ldm/minimax/model.py` "cond" segment). `MiniMaxH3AddGuide`
does the same for **audio**: it VAE-encodes the clip and appends an
`audio_latent` keyframe at the same timeline position ("cond_audio" segment,
`FRAME_RESCALE` per pixel frame, 1.0 per audio latent frame;
`comfy_extras/nodes_minimax_h3.py:165-236`, `model.py:373-393`). Video and
audio are sampled jointly, so a take conditioned on our clip at t=0 regenerates
that clip on its own track and animates the face against it. That is a
different mechanism from the ref2va `<Audio N>` voice reference, which enters
the *reference* span before the timeline with no frame index (`model.py:395-`)
and can only lend timbre to words the model synthesises from `<d>` text.

So: **fl2va base + first_frame (identity and space) + AddGuide(audio, frame_idx)
(the words, the timing, the mouth).** No model swap, no reference tags.

## 1. The workflow

`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\video\video_minimax_h3_i2v_turbo_speak.json`
`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\video\video_minimax_h3_i2v_turbo_speak.manifest.json`

Derived from `video_minimax_h3_i2v_turbo` (fl2va fp8, EMA ckpt850 turbo LoRA
0.8, euler + beta, 8 steps) with two nodes added and one wire moved:

| node | class | inputs |
|---|---|---|
| 20 | `LoadAudio` | `audio` (inject `audio`, type `audio_path`) |
| 21 | `MiniMaxH3AddGuide` | `positive` ← 8:0, `latent` ← 8:1, `audio_vae` ← 7:0, `audio` ← 20:0, `frame_idx` (inject `audio_frame_idx`) |
| 10 | `BasicGuider` | `conditioning` ← **21:0** (was 8:0) |

Inject points: everything `i2v_turbo` has, plus `audio` and `audio_frame_idx`.
Required: `prompt`, `start_image`, `audio`. No existing workflow in
`comfy_studio` wired `MiniMaxH3AddGuide` before this one. The node resamples
the clip to the audio VAE's rate itself; a 24 kHz mono wav goes in as is.

## 2. The two takes

Panel: `library\20260822113400_a-study-in-scarlet\episodes\ep01_short\frames\S11.png`
(Watson, medium close-up, mouth closed, 768×1344).
Line: `library\...\episodes\ep01\work\ab_indextts2.wav` — "I had not said a
word about Afghanistan. Not one word.", 4.33 s, 24 kHz mono, Watson's cloned
voice (IndexTTS2).

Common values: 768×1344, 8 steps, seed 81011, fps 24, turbo LoRA 0.8,
euler/beta, sage_attention disabled (the template default), `start_image` =
S11.png, `audio` = ab_indextts2.wav.

| take | `audio_frame_idx` | frames | seconds | render | file |
|---|---|---|---|---|---|
| A | 0 | 124 = `frames_for(4.33 + 0.5)` | 5.16 | 668 s (cold: TE + DiT + both VAEs loaded off the D: HDD; sampling + decode ≈ 8 min of it) | `episodes\ep01\work\lipsync_a.mp4` |
| B | 12 (0.5 s silent head) | 141 = `frames_for(4.33 + 0.5 + 0.5)` | 5.87 | 631 s (also a reload — another session's TTS jobs evicted TE and DiT between the takes; TE 09:10 → DiT 09:12 → done 09:20, 10:27 in the engine log) | `episodes\ep01\work\lipsync_b.mp4` |

The exact values of each take are beside it as `lipsync_a.json` /
`lipsync_b.json`; the judge's numbers as `lipsync_*_judge.json`; the stills as
`lipsync_*_030.png`, `_mid.png`, `_end.png` and a panel | 0.3 s | mid | end strip
`lipsync_*_strip.png`, all under
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260822113400_a-study-in-scarlet\episodes\ep01\work\`.

## 3. Verdict

Judge: stills at 0.3 s / mid / last frame (`ffmpeg -ss … -frames:v 1`); the
take's own track extracted to 24 kHz mono and scored against the input with
`studio.voice_ear.similarity` (ECAPA cosine; same-speaker line 0.55; the
input against a *different* TTS render of the same line, `ab_qwen.wav`,
scores 0.784); Whisper large-v3-turbo through
`studio.voice_qc.any_transcriber` (ComfyUI path) with `voice_qc.error_rate`;
and mouth motion — mean absolute frame-to-frame difference of a 270×130 crop
over the moustache/lips/chin — per frame against the track's RMS envelope.

| measure | A (frame 0) | B (frame 12) |
|---|---|---|
| Whisper heard | "I had not said a word about Afghanistan. Not one word." | "I had not said a word about Afghanistan, not one word." |
| WER against the line | **0.00** | **0.00** |
| voice similarity to input | **0.844** (above the 0.784 of a re-synthesis) | **0.705** (above 0.55; below A) |
| mouth motion, mean during the line | 7.04 | 7.79 |
| mouth motion, mean in the silent tail | 1.41 (5× less) | 0.55 (14× less); head 0–0.5 s: 2.54 |
| corr(mouth motion, audio RMS), per frame | 0.43 | 0.39 |
| face still Watson | yes — same face, moustache, hat, cravat, coat, glassware | yes — same |
| framing held | yes — the panel's mild push-in, no widening, no pull-back | yes — same mild push-in |
| mouth at 0.3 s / mid / end | open on a syllable / open, teeth visible / closed | **closed** (inside the silent head) / open, teeth visible / closed |

What held (A): the words are ours verbatim, the voice is closer to our clip
than a second TTS render of the same text is, the lips move on the line and
stop after it, identity and framing are the panel's. What did not: the track
is a **regeneration** through the audio VAE and the DiT, not a copy —
similarity 0.844, not 1.0; listen before trusting a take's audio for the mix
(the protocol below keeps our original wav on the master anyway). Take A
begins speaking on frame 1, so its first frame (mouth closed, the panel) cuts
straight into an open mouth; take B was rendered to give the line a silent
head. B did: at 0.3 s the mouth is still closed, the line lands after the beat, the words are again verbatim, and the ratio of line motion to tail motion is higher than A's. Its voice similarity is lower (0.705 vs 0.844) — one seed each, so that is a sample of one per condition, not a rule; both clear the same-speaker line.

## 4. Protocol for a dialogue shot

1. **Audio first.** Render the line (`say_lines.py`, IndexTTS2/Qwen3 clone),
   QC it with `voice_qc` as today. Its measured length `L` seconds drives the
   take, not the plan's slot.
2. **Head and tail.** Choose the silent head `h` (0.25–0.5 s; the panel is
   mouth-closed, so give it a beat before the first syllable) and the tail
   handle `t` = 0.5 s. `audio_frame_idx = round(24 h)`;
   `frames = studio.h3.frames_for(h + L + t)`. AddGuide crops audio that runs
   past the video's end silently, so an under-length take loses the end of the
   line — always cover `h + L`.
3. **Identity** is the panel's: the same Start Frame path as every other
   take, so nothing new. The character sheet is not fed (fl2va has no ref
   slot); if a panel's face drifts, fix the panel, not the take.
4. **Prompt** — the Start Frame skeleton `episode_take_prompt.py` already
   emits, with the RULES line replaced for speaking shots:
   - keep the alignment line and `Begin exactly from <Picture 1>: <frame>`;
   - say who speaks to whom and where the listener is (`Holmes, just
     off-screen`), then **`physically speaking with natural lip movement on
     every syllable`**, then the line itself as
     **`(S1) <d>[English] <the exact words of the wav>.</d>`**;
   - a silent head if `h > 0`: `At the start of the shot he is silent for
     half a second, mouth closed`;
   - `After the line he falls silent, mouth closed, and the frame holds to
     the cut`; the LOCK sentence unchanged;
   - `overall_soundscape: <name>'s voice, close and dry, …; no other voice; no
     music.` and `non_diegetic_music: N/A`.
   The exact text that rendered A and B is in `lipsync_a.json` /
   `lipsync_b.json` under `values.prompt`.
5. **Gate** every dialogue take with the judge above (`voice_qc` WER within
   the existing threshold on the take's own track; `voice_ear.similarity` ≥
   0.55; mouth-motion ratio line/tail ≫ 1); then judge the end frame by eye as
   today's review does.
6. **Mix**: on the master, use the take's picture and **our original wav**
   aligned at `h` — the picture is synced to it by construction, and the wav
   is the clip the voice cast was approved on. Keep the take's track only as
   a fallback.
7. **Cost**: a speaking take is the same H3 call as a silent one plus one
   audio VAE encode — no model swap, no ref2va. Warm, expect the i2v_turbo
   curve (T10 158 f 362 s, T11 90 f 226 s in `ep01_short/shots/shots.json`);
   the two takes here were both reloads (10:27 and 11:05 wall) because another session's jobs evicted the models in between; sampling + decode alone ran ≈ 8 min for 124–141 frames at 768×1344.

## 5. Open

- `shots.py` is untouched: wiring is (a) an `audio` + `audio_frame_idx` in
  `values_for` when the shot has a spoken line, (b) the prompt swap in §4.4,
  (c) frames from the wav, and (d) the judge as a gate. A follow-up change,
  not this research.
- Two-person dialogue in one frame (who moves, `(S1)`/`(S2)` with one anchored
  track) is unmeasured; so is a line anchored mid-shot after a silent action.
- Multiple lines in one take: chain AddGuide nodes, one per line at its
  `frame_idx` — the node is built to chain, unmeasured here.
- Does the audio anchor survive `ref2va` (identity refs + anchored line)?
  `MiniMaxH3AddGuide` accepts any H3 AV latent, so the wiring is legal;
  the trailer lane would want it. Unmeasured.
