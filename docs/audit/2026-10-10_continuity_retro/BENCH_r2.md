# BENCH r2: the round-2 H3 take bench (R2_verdict §3)

Ran 2026-10-11, 00:45 to 01:50 on the GPU (65 min of the 2 h 15 min hard stop), at $0, on the local ComfyUI.
The engine was PID 43272 (`--reserve-vram 2`, no CK flag): no relaunch, no install, and no foreign job queued.
The arms were judged in the verdict's order, then re-scored with the owner's **INVENTED-SPEECH** check, which was added mid-run (17eab28).

**Result:**
- **No arm passes every hard check.** Nothing is adopted. Production `takes_r2v.BASE` is unchanged.
- **The 4-step base is not wired.** See §6.

Scratch:
- Renders, ran graphs and `runs.jsonl` with knobs, ffprobe size and phases are in `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\bench\r2\runs_B2..B6\`.
- Measures are in `...\r2\measures_r2.json` and `...\r2\speech_tail.json`.

## 0. The instrument, before any GPU (CPU, test-first)

| Commit | What |
|---|---|
| bcb8312 | The overlay carries every knob: the whole model-patch chain (attention node), scheduler, sampler, ref_image_size, job canvas, restaged panel. `knobs()` reads all of them and the panel's pixel size. A panel that is not its canvas is refused. The render size is read back. |
| 3ea5461 | The interior seam check: 18/572 WotW panels, all 18 confirmed by eye as two pictures in one cell, 0 false positives (`bench_evidence/r2/seam_panels_wotw.jpg`). **16 of them already read `stacked` and still shipped on the ladder's keep_best.** The gap was the terminal, not detection. |
| f5316b1 | A per-take phase record (`takes/r2v/phases.jsonl`), read from ComfyUI's log ring. The live engine's `comfyui.log` was overwritten by a failed second launch at 21:55, so no file is a source. |
| 76dff68 | The face-crop sheet tool (`contact.py faces`). |
| 17eab28 | The INVENTED-SPEECH check and the `*_review.mp4` copies. |

The overlay's guard fired once, on my own plan. The block 5 re-cut panels were named `S3_992.png`, not `shot_*`, so `panel_px` was unreadable and the build refused them.

## 1. Blocks 0-2

| Block | Result |
|---|---|
| 0 engine | Queue empty, flags as the verdict says. |
| 1 canvas probe | A3 at 992x992 with 22 frames **rendered 992x992** (94.8 s). The R2V node honours the canvas, so R2_Q §0a is confirmed on the artefact. |
| 2 determinism | S4 A3 re-rendered: **PSNR 99 (bit-identical frames) against phase-0 S4_A3.** The phase-0 controls stand. |

## 2. Block 3: CK int8 attention (`..._ckattn_comfyorg`), OUT

| shot | s/it A3 → CK | gain | prompt s A3 → CK | PSNR vs ctl | clones | id ctl → CK | lag | banding ctl → CK | invented speech |
|---|---|---|---|---|---|---|---|---|---|
| S2 | 12.98 → 7.53 | 42 % | 180 → 86 | **22.2** | 0 | - | - | .235 → .241 | - |
| S3 | 14.38 → 8.14 | 43 % | 166 → 80 | **26.1** | 0 | - | - | .281 → .283 | - |
| S4 | 8.28 → 4.89 | 41 % | 98 → 81 | 28.8 | 0 | .800 → .790 | 0 | .270 → .259 | **"Indeed." (ctl clean)** |
| S6 | 10.87 → 6.28 | 42 % | 114 → 113 | **25.3** | 0 | .762 → .744 | 0 | .419 → .425 | clean |
| D1 | 5.57 → 3.47 | 38 % | 95 → 72 | 28.7 | 0 | .834 → .833 | 0 | .279 → .284 | laugh (= ctl, prompt-asked) |
| D2 | 15.11 → 8.11 | 46 % | 131 → 158 | **25.2** | 0 | .879 → **.857** | -.01 | .286 → .283 | clean |

**Speed:**
- Sampling is 38-46 % faster on every shot.
- Mean banding is .2960 against .2949 (+.001, so it is non-inferior).

**Out on three hard rules:**
- PSNR is under 28 dB on 4 shots.
- D2 identity is -0.022 (the allowance is -0.02).
- S4 has an invented word.

**The PSNR wall needs a re-ruling:**
- Seed-to-seed PSNR on A3 is 12.9 dB (S4) and 17.3 dB (S6).
- A1 against A3 is 18-24 dB.
- CK is the closest any change gets to the control, and on the face sheet (`faces_B3_ck.jpg`) it is visually indistinguishable.
- 28 dB was a guess, not a calibration.

**What this block leaves open:**
- The S4 invented word is real. The control's tail is already at -30 dB of sound, so the 4-step tail is fragile under any perturbation (§5).
- Sage stays a separate install window, per the verdict.
- **The BASE switch was not prepared.** It failed hard rules.

## 3. Block 4: schedule, OUT (shift 6 beta, shift 6 simple)

| shot | banding ctl / beta / simple | id ctl / beta / simple | lag | clones | invented speech beta / simple |
|---|---|---|---|---|---|
| S2 | .235 / .222 / .223 | - | - | 0 | - |
| S3 | .281 / .278 / .281 | - | - | 0 | - |
| S4 | .270 / .220 / .231 | .800 / .809 / **.774** | 0 | 0 | **"Heed."** / clean |
| S6 | .419 / .369 / .418 | .762 / .746 / .740 | 0 | 0 | clean / clean |
| D1 | .279 / .328 / .308 | .834 / .819 / .834 | 0 | 0 | laugh = ctl |
| D2 | .286 / .294 / .296 | .879 / .888 / .867 | -.01 | 0 | clean / clean |
| mean banding | .2949 / **.2851** / .2929 | | | | |

**shift 6 beta:**
- It was the banding leader: better on 4 of 6 shots, with D1 worse by .049.
- It passed identity, lag and clones.
- **It is out on the INVENTED-SPEECH check:** S4 says "Heed." where the control is clean.

**shift 6 simple:**
- **It is out on S4 identity (-0.026).**

**Both cells kept their content** by eye (`contact_B4_S3.jpg`, `contact_B4_S4.jpg`): the S3 frogs at 8 %, the S4 smoke column, no new figure. The schedule stays 12/beta. The face sheet is `faces_B4_schedule.jpg`.

The timing is unchanged, as expected for an arm with the same NFE: beta averages 101.7 s per prompt.

## 4. Block 5: canvas 992 (and the 896 probe), OUT

These ran on shift 6 beta, which was the leader when the block started; it was disqualified afterwards by the speech check.
The 992 panels were a centre square re-cut from the 1024 `storyboard/shot_NN.png`. That is not `panels.py`'s gutter-trimmed cut, so the framing differs slightly.

| shot | s/it 768 → 992 | ratio | prompt s 768 → 992 | id 768 → 992 | banding 768 → 992 |
|---|---|---|---|---|---|
| S2 | - | - | 121 → (orphan, collected from history) | - | .222 → .207 |
| S3 | 13.42 → 33.15 | **2.47x** | 138 → 197 | - | .278 → .277 |
| S4 | 7.99 → 18.07 | 2.26x | 79 → 125 | .809 → **.784** | .220 → .229 |
| S6 | 10.66 → 24.46 | 2.29x | 100 → 158 | .746 → **.708** | .369 → .433 |
| D1 | 5.74 → 12.54 | 2.18x | 62 → 104 | .819 → .836 | .328 → .384 |
| D2 | 15.18 → 35.66 | **2.35x** | 110 → 219 | .888 → .863 | .294 → .338 |
| D2 @896 | 15.18 → 24.25 | 1.60x | 110 → 163 (1.47x) | .903 | .382 |

**Out on every count:**
- The median whole-prompt time is **1.59x** the 768 run (the wall is 1.25x).
- s/it passes the 2.3x cliff on S3 and D2, which means partial offload.
- Identity is worse by -0.025 on S4 and -0.038 on S6.
- Mean banding is .311 against .285.

**896 is not worth its own window:** 1.47x time, banding .382.

**One owner-eye note:** 992 **keeps the S3 frogs at 50 %** (`contact_B5_S3.jpg`), as the shipped 8-step does, and the 768 4-step does not. The face sheet is `faces_B5_canvas.jpg`.

## 5. Block 6 and the INVENTED-SPEECH re-score

Nothing survived, so the leader is A3 itself. A3 seed 2 now exists for S3, S6 (phase 0), D2 and D1 (block 6).

- **D2 A3 s2:** clean (id .912, 0 clones, no tail words).
- **D1 A3 s2:** **1 clone frame**. D1 is held to 0, so this is a hard failure of the 4-step base on a second seed. A1 (8-step) also had 2 clone frames on D1 at seed 1.

**INVENTED-SPEECH method** (`scripts/bench/speech_tail.py`, CPU Whisper):
1. Find where the guide falls silent.
2. If the take's own audio in the tail is louder than -45 dB, hear the whole take and the whole guide.
3. Every word after the line's last shared word is invented.

A tail heard on its own hallucinated "see you next week" on the S4 control, so it is never transcribed alone.

| take | tail dB | heard after the line | lower-face motion tail/line |
|---|---|---|---|
| S4 shipped 8-step (A0) / A1 | -57.6 / -57.6 | - / - | 0.12 / 0.15 |
| S4 A3 (4-step) / A3 s2 / B2ctl | -30.2 / -92.4 / -30.2 | - / - / - | 0.33 / 0.31 / 0.33 |
| S4 CK | -24.7 | **"Indeed."** | 0.34 |
| S4 shift6 beta | -24.0 | **"Heed."** | 0.43 |
| S4 shift6 simple / 992 | -22.3 / -17.4 | - / - | 0.43 / 0.58 |
| D1 every arm, A3, A3 s2, shipped A0, A1 | -15 to -19 | "ha ha ha …" | 0.76-1.19 |
| S6, D2 every arm | about -93 (S6) / -54 to -94 (D2) | - | 0.05-0.32 |

**The D1 laugh is asked for by the shot's own prompt:** "At 00:03, as the line ends, his head tips back as a laugh shakes through his shoulders". It is on the shipped 8-step take too. It is not invented, and the check needs a prompt-asked-action exemption before production use.

**Root-cause candidates for cycle 1** (to prove at 95 %, not fixed in production):
1. **The digitally silent tail of the guide.** H3 is given silence it is free to fill.
2. **The 4-step LoRA.** On the same S4 seed, the tail energy rises from -57.6 dB (8-step) to -30.2 dB (4-step), and the lower-face motion in the tail rises from 0.12-0.15 to 0.31-0.33. The 4-step base sits at the edge of speaking.
3. **The shift / attention change.**
   - CK pushes the tail to -24.7 dB and a word.
   - Shift 6 halves `audio_scale` (12/3 = 4 → 6/3 = 2) and gives -24.0 dB and a word.
   - 992 gives -17.4 dB, with no word that time.
4. **Prompt-directed tail actions** (D1's laugh). These are a writer's choice, not a model fault; the check must read them from the prompt.

**Review copies:**
- They are in `bench_evidence/r2/review/*_review.mp4`: 20 files, S4/S6/D1/D2 × A3/CK/beta/simple/992.
- H3's audio is replaced by the recorded guide, as in the master. I checked one: the S4_B3ck tail reads -120 dB.

## 6. The 4-step LoRA: NOT wired

The precondition was that the 4-step base, under its schedule winner, passes the hard checks. The winner is 12/beta, which is A3 itself, and A3 fails three of them:
- **Content against the 8-step production:** by 50 % of S3, the 4-step loses most of the frogs on both seeds; A0 and A1 keep 4-5 (`D:\temp\...\scratchpad\bench\r2\S3_8v4.jpg`).
- **Clones:** D1 seed 2 has 1 clone frame.
- **Silent-tail fragility:** the S4 tail carries sound and the mouth moves (§5).

**Prepared, not committed:**
- `takes_r2v.take_values` passes `steps` only when the manifest declares it, with a test.
- The patch is `...\scratchpad\bench\r2\prepared_4step_take_values.patch`, and the test is beside it.
- The LoRA was not copied to `C:\comfy_models\loras\minimax_h3\`. It is present at `ComfyUI\models\loras\minimax_h3\minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors`.

## 7. Projected minutes per episode (30 renders; 5.55 h is the R2_verdict phase-3 base)

| Scenario | Δ per take (measured) | Δ per episode | Episode |
|---|---|---|---|
| A3 4-step (the base of the projection) | - | 0 | 5.55 h |
| + CK int8 (if re-ruled in) | sampling -18 s (151 vs 260 s over 6 shots) | **-9 min** | ≈ 5.40 h |
| + shift 6 (either) | ±0 | 0 | 5.55 h |
| + canvas 992 | sampling +57 s, decode +8 s | **+33 min** | ≈ 6.1 h |
| + canvas 896 | sampling +36 s, decode +12 s | +24 min | ≈ 5.95 h |
| 8-step A1 (today's production) | sampling +55 s | +27 min | ≈ 6.0 h |

## 8. Adoption and rollback, one line per arm

| Arm | Adopt | Rollback |
|---|---|---|
| CK int8 `..._ckattn_comfyorg` | **No.** PSNR wall, D2 id -0.022, S4 invented word. Re-rule the 28 dB wall and re-test against the speech check. | n/a (BASE untouched; rollback would be the A3 name) |
| shift6 beta `..._shift6beta_vllmomni` | **No.** S4 invented "Heed." (banding leader, owner eye on `faces_B4_schedule.jpg`). | n/a |
| shift6 simple `..._shift6simple_modeltc` | **No.** S4 identity -0.026. | n/a |
| canvas 992 / 896 | **No.** Time 1.59x / 1.47x, identity, banding. Owner note: frogs kept. | n/a |
| 4-step A3 as BASE | **No.** S3 content, D1 s2 clone, silent-tail sound (§6). | `BASE = video_minimax_h3_r2v_turbo_ref8_crf_visurena` (unchanged) |
| P-WORDS sheet (block 7) | **Cut.** Droppable by the verdict; the window went to the invented-speech re-score the owner raised. | - |

## Evidence

All under `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\r2\`:
- `faces_B3_ck.jpg`, `faces_B4_schedule.jpg`, `faces_B5_canvas.jpg`
- `contact_B4_S3.jpg`, `contact_B4_S4.jpg`, `contact_B5_S3.jpg`, `contact_B5_S4.jpg`, `contact_B5_D2.jpg`
- `seam_panels_wotw.jpg`
- `review\*_review.mp4` (20)

**Publishable (flag):**
- The R2V canvas is honoured (992 measured).
- CK int8 attention gives 38-46 % faster sampling on ref2va on a 4090.
- H3's invented speech in silent guide tails, the measurement method, and the 8-step vs 4-step tail energy.

These belong in the planned public ref2va bench, including the arms that lost.
