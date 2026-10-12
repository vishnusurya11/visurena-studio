# C1-A: audio tail, invented speech, and the mouth in silence

Cycle 1, researcher A, 2026-10-11. CPU only, $0, no GPU, no code edits.

Evidence: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\C1_A_evidence\`
- `strip_1.jpg`, `strip_2.jpg`, `strip_3.jpg`: every shipped take the measures flagged. Each row shows mouth crops from 0.8 s and 0.3 s before the line ends (white times) and then through the shipped tail (yellow times).
- `strip_4_loudtails.jpg`: shipped takes whose own audio sounds in the tail (above -45 dB) and were not flagged on the mouth.
- `strip_5_random_clean.jpg`: a recall check. Eight random unflagged takes, each with at least 1.5 s of shipped tail.
- `shipped_fixed.rows.json`: one row per shipped dialogue take (204 rows). `bench_cal.rows.json`: the same measures on the BENCH_r2 / phase-0 arms (18 rows).

Scripts are in `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c1\`:
- `survey.py`, `measure_tail.py`, `analyse.py`, `strips.py`, `placed_check.py`, `fix_stale.py`
- Raw output: `shipped.json`, `shipped_fixed.json`, `bench_cal.json`

## 0. Verdict in one paragraph

**What ships.** The risk is a mouth that moves while the master is silent. In the two shipped books it is rare but real.
- I checked 204 shipped dialogue takes (WotW 124, Scarlet 80). 154 of them have a readable face and at least 0.25 s of shipped tail.
- **2 takes, seen by eye, articulate inside the placed seconds with nothing asked for in the prompt:**
  - **wotw/ep10/T21:** H3 says "Moving!" again, with the mouth shaping it at 4.35-4.55 s; the shot ships to 4.58 s.
  - **wotw/ep26/T25:** her mouth opens and works from 4.3 to 5.3 s, over -22 dB of invented sound; the shot ships to 5.83 s.
- **4 more show mouth action in the tail that the prompt itself asked for:**
  - ep25/T21, the laugh. Only 0.15 s of it ships.
  - ep04/T02, "breath saws in his open mouth".
  - ep22/T12, "his mouth forms the soft call".
  - scarlet/ep11/T17, a bite of biscuit.
- **About 15 hold a static parted mouth, smile or grimace.** That is acting, not speech.
- **No Scarlet take articulates in silence.**

**Mechanism (95 %).**
- H3 does not copy the guide's tail. It writes its own audio and its own mouth together.
- The guide's tail is exact digital zero (-120 dB) in 100 % of the takes measured. In that zero, the audio stream is free.
- When H3 fills the tail with a voiced sound, the mouth moves with it. When the tail it generates stays quiet, the mouth stays shut: 0 articulations in every eye-checked quiet tail.
- **Every invented word measured echoes the line's last word:** "...a man indeed. *Indeed.*", "*Heed.*", "Keep moving. *Moving!*" H3 continues the utterance across the cliff edge of the silence.

**What raises the odds.**
- **4-step instead of 8-step:** 1 seed pair, about 65 %.
- **shift 6 / audio_scale 2 instead of shift 12 / 4:** 2 of 3 shots, about 70 %.
- **CK attention:** 1 shot.
- **Seed:** the same arm on another seed moves the S4 tail from -30 dB to -92 dB, so seed is the largest single factor measured.
- **Tail length:** not a driver.
- **Prompt "as he speaks" after the line:** not a driver (0 of 25). Only explicit mouth actions are (3 of 3).

**Room tone vs digital silence** is the strongest untested lever. The community reports point to it, and so does the echo signature. It needs one GPU A/B (§4, fix 3).

## 1. The instrument (CPU)

For each shipped take with a `voice*` LoadAudio guide, from its `takes/r2v/T??.graph.json`:
1. **Guide.** I read the staged wav in `ComfyUI/input`. Where the guide speech ends comes from `invented_speech.speech_end` (the last 50 ms window above -45 dB).
2. **Shipped seconds.** These are the placed seconds of the take's run, from `placed.json`. This is the same rule as `assemble.segments_of`: a dialogue shot takes no head trim, so the shipped tail runs from the line end + 0.25 s to the placed end.
3. **Tail audio.** I measured the RMS of the take's own audio over the whole tail and over the shipped tail. If the tail is louder than -45 dB, CPU Whisper (`voice_qc.transcriber(device='cpu')`) hears the whole take and the whole guide, and `invented_speech.extra` returns any words after the last shared word. This is the 17eab28 method unchanged.
4. **Mouth.**
   - MediaPipe FaceLandmarker (`studio/models/face_landmarker.task`, already in the repo, `studio/measure/mouth.py`) on every frame. The aperture is inner lip 13-14 over the eye distance. I used the largest face, with up to 3 faces read.
   - Smoothing is a 3-frame median, because single-frame landmark dropouts broke the runs.
   - A mouth counts as **open** at or above max(0.06, 0.3 × the line's p90 aperture). It is **flagged** when it stays open for at least 6 frames (0.25 s) in the shipped tail.
   - **Calibration:** on S4_B3ck ("Indeed.") the track holds 0.14-0.18 from 3.21 to 3.88 s and the run is 11 frames. On S6 the run is 0.
5. **Eye.** I looked at every flag (23 takes), every sounding tail (15) and 8 random clean takes, as crops through the tail.

**Limits:**
- The open-run measure flags open mouths, not articulation. By eye it over-flags static parted lips, smiles and grimaces about 6:1. The audio channel catches what the mouth measure misses: ep10/T21's word sits in the last 5 frames, so its run reads 2.
- 16 takes have no readable face (profile, beard, small figure).
- **Stale guides.** 5 early-Scarlet takes (ep01 T18/T20/T22, ep02 T20/T22) were driven by unhashed `voice_NN.wav` files that a later episode overwrote in `ComfyUI/input`. Their guides disagree with `placed.json` by 1.2-3.2 s. For those 5 I re-derived the line end from `placed.json` and re-heard them against their line texts. All are clean. **The 17eab28 check gives a false "invented" verdict on any take whose staged guide was overwritten.**

## 2. Measured on the shipped episodes

**Counts:**

| | n |
|---|---|
| shipped dialogue takes (WotW 27 eps + Scarlet 15) | 204 (124 + 80) |
| readable face | 188 |
| readable face and shipped tail of 0.25 s or more | 154 |
| shipped tail under 0.25 s (nothing to ship) | 34 |
| every guide tail (digital zero) | -120 dB, 204/204 |

**The take's own tail dB:**

| | below -70 | -70 to -45 | -45 to -30 | above -30 |
|---|---|---|---|---|
| WotW | 83 | 27 | 9 | 5 |
| Scarlet | 71 | 6 | 1 | 2 |

**Invented words (Whisper):**

| take | words | in the master? |
|---|---|---|
| wotw/ep10/T21 | "Keep moving. **Moving!**" (-14.9 dB) | **Yes.** The word sits at about 4.3-4.6 s and the shot ships to 4.58 s. The mouth shapes it (strip_1 row 1). |
| wotw/ep25/T21 | "HAHAHAHAHA" (prompt-asked laugh; this is the bench's D1) | 0.15 s of it ships |
| (scarlet ep02 T20/T22) | were false, from a stale guide | clean after the fix |

**Mouth articulating in the shipped silent tail, by eye** (strips 1-4):

| take | tail dB | what moves | prompt asked? |
|---|---|---|---|
| **wotw/ep10/T21** | -14.9 | "Moving!" at 4.35-4.55 s | no ("his arm goes on waving") |
| **wotw/ep26/T25** | -22.4 | the mouth opens and works from 4.3 to 5.3 s, with sound but no word Whisper could name | no ("her head tips ... body begins to sway") |
| wotw/ep04/T02 | -63.8 | open-mouthed panting | **yes**, "breath saws in his open mouth" |
| wotw/ep22/T12 | -30.1 | the beard moves on a call | **yes**, "his mouth forms the soft call" |
| wotw/ep25/T21 | -16.0 | a laugh (0.15 s ships) | **yes**, "a laugh shakes through his shoulders" |
| scarlet/ep11/T17 | -84.6 | a bite | **yes**, eating |

**Static, not speech:** these hold a parted mouth, a smile or bared teeth. They are judged acting, not a fault: wotw ep01/T11, ep02/T16, ep02/T22, ep13/T13, ep13/T24, ep14/T11, ep14/T12, and scarlet ep05/T05, ep08/T11, ep09/T16, ep09/T18, ep09/T28, ep12/T14, ep13/T02, ep13/T17, ep14/T22, ep11/T23.

**False flags:** scarlet ep01/T18 and ep12/T22. The shot cuts away, or the face is small.

**Sounding tails with a closed mouth** (strip_4): ep04/T22, ep06/T28, ep15/T21 (-19.8 dB), ep18/T21, ep19/T19, ep22/T06 (drinking) and ep22/T20. This is H3's own ambience; every take's `overall_soundscape` asks for it.

**Recall:** 8 random unflagged takes with long shipped tails were all clean by eye (strip_5).

**Shipped verdict.** 2 of 154 eligible takes (1.3 %) ship a mouth that speaks into silence when the prompt did not ask for it. Both are WotW (ep10, ep26), and both have a loud tail (above -25 dB). 4 more ship mouth actions the writer asked for.

## 3. Root cause

### 3a. The mechanism: 95 %, measured on 2 shipped takes and 7 bench takes, and survives the skeptic test below

- **The ComfyUI code** (`comfy_extras/nodes_minimax_h3.py` `MiniMaxH3AddGuide`; `comfy/ldm/minimax/model.py` 363-458):
  - The voice guide is encoded by the audio VAE and placed as **conditioning rows** (`audio_pos`) beside the target audio latent.
  - The target audio is denoised from noise like the video.
  - The guide is a strong hint, not a clamp. There is **no audio mask, no audio CFG** (the graph runs `BasicGuider`, CFG-free and distilled), and no audio-strength input.
  - The only audio knobs are `MiniMaxH3SigmaShift.shift_audio` (with `audio_scale = shift_video / shift_audio`) and the guide's content and length.
- **Audio and mouth are one sample.**
  - On the bench, all 7 arms with a tail at or above -25 dB hold the mouth open for 7-25 frames.
  - All 11 arms with a tail at or below -53 dB hold it for 0-3 frames (`bench_cal.rows.json`).
  - In shipped takes, both true articulations have tails at -14.9 and -22.4 dB.
  - Quiet tails show no articulation in any eye-checked take.
- **Skeptic test.**
  - A loud tail does not imply a moving mouth: 7 shipped loud tails are ambience over a closed mouth.
  - So the cause is not "the tail has sound". It is "**H3 chose to continue the voice into the zero**".
  - Every word measured is an echo of the line's last word: Indeed/indeed, Heed/indeed, Moving/moving. That is continuation, not hallucination from nothing.

### 3b. Candidate causes, scored

| candidate | evidence | confidence it RAISES the risk | 95 %? |
|---|---|---|---|
| **Digital-zero tail** (the `anullsrc` padding in `takes_r2v.composite`, `scripts/episode/takes_r2v.py:407`) | 204/204 guides are exact zero. The model never outputs zero; it writes its own ambience, so zero is out of distribution. Community: silence gives gibberish, and the fixes reported are trimming the reference and adding a soundscape (HF MiniMax-H3 discussions #64, #76). This is the only shared precondition of every invented word, but there is no contrast arm (no take was ever rendered with room tone). | about 60 % | **No:** needs fix 3's A/B |
| **Seed** | S4 4-step, same everything: seed 1 gives -30.2 dB, seed 2 gives -92.4 dB. The 8-step D1 laugh is on every seed. | high variance (a 60 dB spread) | yes, as variance, not as a cause |
| **4-step LoRA vs 8-step** | S4 at the same seed: -57.6 → -30.2 dB, mouth p90 0.063 → 0.085, run 3 → 3. D1 laughs on both. D2/S6 silent on both. One shot moves. | about 65 % | No (n = 1 seed pair) |
| **shift 6 (audio_scale 4 → 2)** | S4: shift-12 4-step -30.2, shift-6 arms -24.0 / -22.3 / -17.4 with runs of 7 / 12 / 25 and "Heed." D2: shift-6 at 992 gives -53.8 vs about -94. S6: no change. | about 70 % | No (2/3 shots, confounded with canvas in B5) |
| CK int8 attention | S4 "Indeed." at -24.7. One shot. | about 50 % | No |
| Tail length | Shipped open-flag rate by shipped-tail length: 0-1 s 6/35, 1-2 s 9/62, 2-4 s 3/38, 4 s+ 5/19. No trend. The 2 true cases have take tails of 1.7 and 3.7 s. | not a driver | yes (as a negative) |
| Prompt "as he speaks / talks / says" placed AFTER the line | 36/204 takes. This is a template fault: `episode_ref_official.beat_sentences` re-times the plan's follow-on clauses from `line_end`, so a clause written "as he speaks" lands in the silence. In about 25 eligible takes it produced no articulation by eye. | not a driver | yes (as a negative) |
| Prompt EXPLICIT mouth action after the line (laugh, call, open-mouth panting, bite) | 3 of 3 eligible moved the mouth as asked | writer's choice, obeyed | yes |
| Book / style | WotW 14 of 15 sounding tails, and both true cases; Scarlet 2 sounding tails (one was 1 of the 5 stale-guide re-reads). Possibly the WotW soundscapes (crowds, guns, the common) or the stylised faces. | unexplained | No |

**Not the cause:** the master's sound. `trailer_assemble.extract -an` drops H3's audio, and the recorded line is laid instead. Masters carry no invented audio.

## 4. Online research (2026)

- **HF MiniMaxAI/MiniMax-H3 discussion #64** (ref2v with audio reference): users report "jibberish for any silent moments". One fix: **trim the reference audio to about the length of the line**, which "resolved the issue". The same thread recommends an explicit `overall_soundscape` against mumbling in quiet moments, and a closing period inside `<d>`.
- **HF discussion #76** (gibberish at the start or in silence): "the model does NOT do silence well"; "will mumble when done talking" without a closing period. Workarounds offered:
  - ambient sound ("soft background tone"), and the word "silently";
  - a voice reference of 4 s or less;
  - one user reports no gibberish on the hybrid fl2va/ref2va checkpoint at 50 steps with no turbo LoRA.

  No official answer exists, and seeds vary.
- **BennyDaBall/MiniMax-H3-Workflows (HF):** "anchor t=0 with room tone", with at least 1.2 s of lead-in before the first line. "Few-step audio blowout is the classic turbo failure mode … if you drop steps further, check your audio peaks." This agrees with the 4-step tail rise.
- **minimaxh3.co lip-sync test:** "plenty of models keep the jaw moving after the words stop". The fix there is "give the shot something to do after the dialogue". Ours already does this, with a beat timed from the line's end.
- **THEval** (arXiv 2511.04520) scores **Silent Lip Stability** on VAD-silent stretches of 300 ms or more. Models range from 0.62 to 0.96. This is a published metric we could report beside ours.
- **ComfyUI H3 nodes** (read locally): no audio mask, no audio guidance scale, no per-region audio strength. **There is no node-level control to clamp the tail.** The levers are the guide's content and length, `shift_audio`, steps and seed.
- **Conflict to respect.** `composite()`'s docstring has a MEASURED reason never to make the guide shorter than the take: a short guide ends the model's clock early. "Trim the guide" from the community is about *reference* audio (timbre), not the frame-anchored guide. Any trim must stay a bench arm.

## 5. Fixes, ranked (cheapest proof first)

| # | fix | why | cheapest proof | cost |
|---|---|---|---|---|
| 1 | **Gate it** (production `invented_speech` and a mouth row in the take gate). Fail = the take's shipped tail sounds above -45 dB **and** (Whisper hears words after the line, **or** the mouth reads open for 6 or more frames with ≥ 2 rises across the threshold). **Exempt** a tail whose post-line clause asks for a mouth action (laugh, call, shout, open mouth, eat, drink). Hash-check the guide against `placed.json`. Cure = a new seed (seed spans 60 dB). | Catches both shipped cases. Seed is the largest measured factor. | **CPU, now:** replay the rule over `shipped_fixed.rows.json`. Expected fails: ep10/T21 and ep26/T25; expected exemptions: ep25/T21, ep04/T02, ep22/T12, scarlet ep11/T17. Write the test first, against those rows as fixtures. | $0, about 10-15 s CPU per dialogue take (1 Whisper pass when loud, FaceMesh on the frames) |
| 2 | **Template fix:** after the line, `beat_sentences` rewrites or strips speech verbs (speaks / talks / says / as he says it) from re-timed clauses, and never writes a speech verb after `line_end`. | A correctness fault: the prompt contradicts its own `<Audio 1> … over silence` sentence. Measured harmless so far (0/25), so it is hygiene, not a cure. | **CPU:** a unit test on `beat_sentences` with "as he speaks" → no speech verb after the mark. Re-render nothing. | $0 |
| 3 | **Room tone in the guide's tail instead of digital zero.** `composite()` mixes a low bed into the padding only, at about -50 to -55 dBFS: the episode's own ambience or brown noise. The line stays where it is. | Matches what H3 itself writes (its quiet tails are -55 to -95 dB, never zero) and what the community advises. It removes the "cliff" the model echoes across. | **GPU A/B, about 15 min:** S4 (the arm that invents: 4-step shift-6 beta, and CK) × 3 seeds × {zero, room tone at -50 dB}, plus D2 as the silent-tail control. Pass: tail words 0/3 and mouth runs ≤ 3 frames with room tone, against at least 1/3 inventing with zero; lip-sync lag unchanged (`measure/mouth.lag`); D2 and S6 still silent. | about 12 renders × 95 s |
| 4 | **Dialogue takes stay on 8-step, shift 12/3**, even if 4-step or shift 6 are adopted for narration. | 4-step and shift 6 each raised S4's tail by 27-40 dB. Narration takes have no guide voice, so a tail there cannot speak. | Already the state (BASE unchanged). Make it a rule in the BENCH arm table: a speed arm must pass the INVENTED-SPEECH check on S4, D1 and D2 × 2 seeds. | $0 |
| 5 | (bench only) **Guide that ends 0.3 s after the line**, with the take's audio latent left to H3. | The community's "trim" advice. Risks the early-clock fault `composite()` documents. | Run it as a 3rd arm of fix 3 only, and measure lip lag and arrival. | in fix 3 |
| 6 | (last) **Prompt "silently" / "mouth closed" after the line** | LESSONS: H3 ignores absences and amounts. Ours already says "closes on the last word" and "over silence for the rest of its length", and the 2 cases still talked. | A 4th arm of fix 3, only if 3 fails | in fix 3 |

**Not proposed:**
- Cutting the shot early. The placed seconds are the voice's ruler (`feedback_the_voice_is_the_ruler`).
- Any audio-CFG or mask node. None exists in the H3 nodes.

**Re-renders owed.** wotw/ep10/T21 and wotw/ep26/T25 are shipped faults. Whether to retake them is the owner's ruling. The scope says shipped files are never overwritten.

## 6. Publishable (flag)

H3 ref2va invents speech in digitally silent guide tails, and the signature is an **echo of the line's last word**.

Supporting material:
- the coupling of audio and mouth in the tail;
- the shipped prevalence (2 of 154, 1.3 %);
- the CPU instrument: Whisper plus FaceMesh aperture, with the stale-guide trap;
- once fix 3 has run on the GPU, the room-tone A/B.

This fits the planned public ref2va bench, and it can be reported beside THEval's Silent Lip Stability.

## 7. Sources

- HF MiniMax-H3 discussion #64: https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/64
- HF MiniMax-H3 discussion #76: https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/76
- BennyDaBall H3 workflows: https://huggingface.co/BennyDaBall/MiniMax-H3-Workflows
- minimaxh3.co lip-sync test: https://minimaxh3.co/blog/minimax-h3-lip-sync
- THEval (Silent Lip Stability): https://arxiv.org/pdf/2511.04520
- Local: `D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\comfy_extras\nodes_minimax_h3.py`, `...\comfy\ldm\minimax\model.py`, `...\comfy\model_base.py` 2145-2268
