# P2: quality and speed, the bench plan and the build list (2026-10-10)

Debater P2 (QUALITY + SPEED), continuity retro. Read-only: no code, workflow or library file
changed, nothing rendered. Inputs: E (measured causes), F (H3 levers), G (image and master
levers), A and D for context, E's frames in
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\quality\`,
the take graph `comfy_studio/workflows/video/video_minimax_h3_r2v_turbo_ref8.json` and its
manifest, ComfyUI's `comfy_extras/nodes_video.py`, and `timing.jsonl` for ep24-27.

## 0. The position in one paragraph

E measured that the pixel chain did not regress: the **picture source** did (Krea2-Cinematic
references in ep01-03, Qwen-Image 2.1 panels from ep05), and the **take model** changed at ep04
(Singularity int8, the same turbo LoRA loaded twice). F and G mostly offer *speed* levers and
*post* upscalers. Upscalers are the wrong first answer. A learned 2x cannot restore texture the
panel never drew. So the bench answers E's two causes first, at the lowest GPU cost, with the
encode held fixed. Speed comes from the levers that are free in quality (attention, step count).
Detail comes last, and only if the speed levers have paid for it. One encode fix (the take's
CRF-23 save) is certain enough to ship with the bench, but it still goes through the bench,
because shipping on a green test without measuring the artefact is the "fix that changes
nothing" trap.

## 1. Reconciling E with F and G

| E's cause (ranked) | Lever that answers it | Source | Verdict |
|---|---|---|---|
| 1. Qwen-Image panel is the look | Krea2 restyle of the panel; Krea2 picture + full sheet staged beside the panel; refs-only (ep01-03 recipe) | E §5, G #3, P2 | **Bench round 2.** This is the change the owner sees. |
| 2. Singularity int8 + LoRA at 1.7 | LoRA once; 4-step v0.1 (Singularity's own pairing); stock fp8 + LoRA once as the ep01-03 reference | E §5, F #4 | **Bench round 1.** Doubles as the biggest speed lever. |
| 3. 768 ceiling + CRF-23 take save | `crf` on SaveVideo (new workflow); lossless segment extract (code) | E §3, P2 | **Ship with round 1** as the fixed encode for every arm. |
| 4. H3 drops ~2/3 of panel detail, decays over the take | latent upscaler 1.5x refine | F #3 | **Round 4, conditional.** Only if rounds 1 and 3 free at least 40 min. |
| 5. Still substitutes (zoompan) | one more seed with a different move TYPE; a smoother push | E §3, P2 | Code and rung change, §5.6. |
| 6. One-figure sheet crops (659-952 px) | full sheet vs crop as the face ref | E §3 | Round 2, arm B4. |
| (speed) attention off | Sage 2.2 cu130 wheel or `--use-ck-attention` | F #1 | **Round 3.** |
| (post) Lanczos 2x | RTX VSR per take; FlashVSR fallback | F #2, G #1 | **Round 0** on shipped takes. It costs about 10 GPU minutes, so test it now, but it does not fix causes 1 and 2. |
| (speed) grid steps 25 → 6-8 | Turbo8 / Viggle LoRA | G #2 | **Deferred.** It saves about 12 min, and its vendor names duplicates as the failure, which is our worst fault. Run only after the panel source is settled. |

**Two corrections to the research before any GPU time is spent:**

- **G's "2048 native grid" hypothesis mostly does not apply to what we drew.** E §1 shows that
  the grids actually drawn were 1x1, 2x1, 3x1 and 2x2 at 1024 per cell. No 3x3 (3072²) exists.
  A 2x2 is exactly 2048², which is native. Only the **3x1 (3072x1024)** layout is off-distribution,
  and that is aspect ratio rather than pixel count. Test it from data already on disk, with no render: compare
  panel sharpness, the duplicate count from `people_check` and `panel_content` faults by layout
  (1x1 / 2x1 / 3x1 / 2x2) across ep20-27. If 3x1 cells are worse, the fix is in the code (stop
  drawing 3x1, or draw two 2x1), not in a workflow.
- **Laplacian sharpness is not a quality measure here.** E measured late takes *sharper*
  (mid 106-145) than the owner's good ep01-03 (64-91). A measure that ranks the owner's bad set
  above his good set must not decide an arm. That point drives the judging protocol in §3.

A further observation from E's frames (`contact_early.png` / `contact_late.png`): faceting is
already present in ep01-03 (the ep03 narrator close-up), because it is the Cinematic_Artstyle
house look the owner picked on 2026-09-18. What differs late is (a) **flat fills and empty
walls** where early frames had painted texture, (b) **many more medium-close faces**, where
faceting reads hardest (E's late contact sheet is 9 of 12 faces against 3 of 12 early), and (c)
**darker chapters**, which expose the CRF-23 banding. Point (b) is composition and belongs to
the plan writer, not to a workflow. The bench cannot fix it, and P2 flags it to the other
debaters.

## 2. The bench: shots, arms, order, GPU minutes

### 2.1 Shots (same seed as shipped, read from each take's `T*.graph.json`)

Six calibration shots, picked from episodes the owner has judged:

| # | Shot | Why |
|---|---|---|
| S1 | ep03, the three graphs already replayed in `library/20260827135508_the-war-of-the-worlds/poc_singularity/` (moving wide, narrator at gate, rim crowd); use the moving wide | owner-good era, Krea refs; the 2026-09-19 A/B gives a prior result to compare against |
| S2 | ep03 narrator at gate (same folder) | the duplicate-figure case that justified Singularity |
| S3 | ep24 T05 (frogs, wide) | E's panel-vs-take evidence |
| S4 | ep24 T12 (two men MCU under foliage) | faceted faces, two figures |
| S5 | ep20 shot 05 | the panel already has the moustached man **twice**: a fault born in the panel |
| S6 | one ep27 take with a spoken line (first `lines.json` dialogue take) | lip-sync lag and audio (the turbo LoRA costs audio, per F) |

### 2.2 Rounds (run in this order; each round's winner is the next round's base)

Every arm saves with the **same** SaveVideo crf (10), so the encode never confounds a comparison.
Arm A0 is the shipped file itself and costs nothing.

**Round 0 — post only, on shipped takes (no H3), ~10 GPU min + ~10 CPU min**
- R0a: calibrate the measures (§3) on all shipped takes of ep01-03 against ep20-27. CPU only.
- R0b: S3, S4 and S6 shipped takes through Lanczos 2x / RTX VSR `ULTRA` 2x / RTX VSR
  `HIGHBITRATE` 2x / FlashVSR v1.1 tiny 2x (the node is installed but disabled; enable it in the bench session only).
- R0c (no GPU): the grid-layout data check from §1.

**Round 1 — take model and LoRA (cause 2) + encode (cause 3), 6 shots x 4 arms = 24 renders, ~65 GPU min**

| Arm | UNET | LoRA | Steps | Workflow file |
|---|---|---|---|---|
| A0 | shipped take (CRF 23) | | | none (existing file) |
| A1 | Singularity int8 | 8-step ref2v @1.0 + @0.7 (today) | 8 | `video_minimax_h3_r2v_turbo_ref8_crf_visurena.json` |
| A2 | Singularity int8 | 8-step ref2v @1.0 once | 8 | `video_minimax_h3_r2v_turbo_ref8_single_lightx2v.json` |
| A3 | Singularity int8 | ref2v **4-step v0.1** @1.0 once | 4 | `video_minimax_h3_r2v_turbo_ref8_ref4_singularity.json` |
| A4 | stock `minimax_h3_ref2va_pruned_fp8_scaled` | 8-step ref2v @1.0 once (the ep01-03 recipe) | 8 | `video_minimax_h3_r2v_turbo_ref8_stockfp8_visurena.json` |

A0 vs A1 isolates cause 3, A1 vs A2 the 1.7x LoRA, A2 vs A4 int8 Singularity vs stock, and A3
the step count. Run all A4 shots back to back: the stock fp8 sits on the HDD (19.5 GB, about 2 min per load), so it should load once. Time each
arm from the ComfyUI log's s/it and phase times, not from wall clock, so load time does not
count against an arm. The top two arms get a **second seed** on all six shots (+12 renders,
~25 min), because one seed per arm cannot separate close arms.

Shift for A3: keep 12/3 for the first pass, as F warns; if A3 is close, add one shift 8 run on
S1 and S6.

**Round 2 — picture source (causes 1 and 6), on the round-1 winner; S3, S4, S5, S6 x 4 arms = 16 renders + 4 Krea passes, ~45 GPU min**

| Arm | What H3 is shown | New file |
|---|---|---|
| B0 | Qwen panel (as shipped) | round-1 winner, reused |
| B1 | the Qwen panel **restyled by Krea2 + Cinematic_Artstyle** at denoise 0.35 (keeps composition, room and pinned cells; takes the Krea2 texture) | `image_krea2_turbo_t2i_lora_restyle_visurena.json` |
| B2 | the Qwen panel + the episode's Krea2 place picture (3072x2048) + the **full** character sheet as extra refs | none (runner staging only; `takes_r2v.graph_for` already adds refs past slot 2) |
| B3 | refs-only, the ep01-03 recipe: Krea2 place picture + full sheet, no panel | none (staging only) |
| B4 | B0 with the full sheet in place of the `sheet_front` crop (cause 6) | none |

B3 is the owner's known-good recipe, but it conflicts with the 2026-09-28 "one room per setup"
ruling (grids chain on the anchor cell) and with D's location work. That makes it a
**reference arm, not a candidate**, unless it wins by a wide margin. B1 is the candidate that keeps
the room continuity and changes only the texture. Check B1 against the memory rules "one picture
per entity / no edited views" and "no composed frame zero": B1 restyles the whole panel in
place and composites nothing. Treat it as a ruling for the owner if the debate reads it otherwise.

**Round 3 — speed, free in quality, on the round-2 winner; 6 shots x 2 arms = 12 renders, ~25 GPU min + one restart**

| Arm | Change | File |
|---|---|---|
| C1 | Sage 2.2 `sageattn_qk_int8_pv_fp16_cuda` on node 3 (cu130 wheel installed) | `<winner>_sage_woct0rdho.json` |
| C2 | no graph change; ComfyUI launched with `--use-ck-attention` (comfy_kitchen 0.2.35, already importable) | none; launch flag only |

Accept an arm only if, at the same seed, the frame-level difference from the round-2 winner stays
within the seed-to-seed spread measured in round 1, and if the S2/S5 duplicate count does not
rise. RunComfy warns that Sage can blur H3 on some machines.

**Round 4 — detail, conditional, 3 shots (S1, S4, S6), ~15-20 GPU min**
- D1: `<winner>_latentup_lbh123.json`: untiled, 1.5x to 1152², 2-3 refine steps, `lock_audio`
  on. Run it only if rounds 1 and 3 together cut at least 40 min per episode. It costs +50-100
  min per episode (F). Re-check the pinned `MiniMaxH3AddGuide` cells, which live in 768 space.

**Round 5 — stills (cause 5), 3 ep20 shots that shipped as stills, ~8 GPU min**
- E1: one extra seed with a **different move type** (memory: H3 obeys direction, and a freeze
  calls for a new move type, not a new amount) at the winner config.
- E2 (CPU): the still push rendered from a 4x supersample (the `zoompan` from a 2x scale steps
  on integer pixels, which is the visible judder).

**Total: about 3.3 h of GPU (10 + 90 + 45 + 25 + 20 + 8 min), one evening, $0.** All of it is local.

## 3. How the bench is judged (not by green gates)

1. **Calibrate the rulers first (R0a).** A measure may decide an arm only if, on shipped
   takes, it ranks ep01-03 (owner: good) above ep20-27 (owner: low quality), with AUC >= 0.75.
   The candidates:
   - **flat-patch share**: the share of 16x16 blocks inside a face or person box (from the existing
     `measure/boxes`) with luma variance under a floor. This measures the "hard polygonal patches";
   - **mid-band texture energy**: a DoG band (sigma 1-4) on the background outside the person boxes.
     This measures "flat fills, empty walls", and unlike Laplacian it does not reward crunch;
   - **dark-gradient banding**: a comb index on the luma histogram of smooth regions with luma < 60;
   - **detail retention**: take mid-frame band energy divided by panel band energy (E's 477 → 145);
   - **tail decay**: first-frame band energy against last-frame band energy.
   Laplacian is kept as a reported column only (it fails calibration by E's own table).
2. **Faults, counted as faults (not as a pass/fail gate):** the duplicate-figure count
   (`people_check` count vs the plan), identity against the sheet (`studio/identity_gate.py`),
   lip lag on S6 (the mux-lag measure), and frozen share.
3. **The look judge, calibrated:** `studio/judges/look.py` sees each arm pair blind (side by side,
   order randomised). It counts only if it first prefers ep01-03 over ep20-27 on five shipped
   pairs. If it fails that, it is dropped from the bench and the bench says so.
4. **Owner view (optional, nothing waits on it):** one side-by-side page with the round winners
   against A0. Following the 2026-09-24 ruling, no step parks on a person; his pick, when he
   gives one, overrides the measures.
5. **Speed:** s/it, sample phase, decode phase and whole prompt, read from the ComfyUI log for
   every render.
6. **Decision rule per round:** the winner is the fastest arm that has no worse fault counts
   than the baseline and that beats it on at least two of the calibrated measures. A speed arm
   that loses on any calibrated measure is rejected however fast it is.

## 4. Build list: new workflow files (no existing file is edited)

Each file is a copy of its base, plus a `.manifest.json` beside it. Rollback means pointing the
name back, nothing more.

| New file (in `comfy_studio/workflows/...`) | Base | Change |
|---|---|---|
| `video/video_minimax_h3_r2v_turbo_ref8_crf_visurena.json` | `video_minimax_h3_r2v_turbo_ref8` | node 17 SaveVideo: `"format": "mp4", "format.codec": "h264", "format.codec.encoding": "re-encode", "format.codec.encoding.crf": 10` (the dotted DynamicCombo keys, the same convention as `sampling_mode.temperature` in the Krea2 graph). **Validate with `validate_workflow` and `ffprobe` (bitrate > 5 Mb/s) before trusting it.** The node exposes no preset (x264 medium). |
| `video/video_minimax_h3_r2v_turbo_ref8_single_lightx2v.json` | same | the crf change + `lora_second` removed, node 3 wired to node 2 |
| `video/video_minimax_h3_r2v_turbo_ref8_ref4_singularity.json` | same | the crf change + single LoRA `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` @1.0, steps 4. **Its manifest must drop the `steps` inject, or `takes_r2v.STEPS=8` silently overrides the 4** (check the ran `T*.graph.json`) |
| `video/video_minimax_h3_r2v_turbo_ref8_stockfp8_visurena.json` | same | the crf change + UNET `minimax_h3_ref2va_pruned_fp8_scaled`, single LoRA @1.0 (bench reference only) |
| `video/<winner>_sage_woct0rdho.json` | the round-2 winner | node 3 `sage_attention: sageattn_qk_int8_pv_fp16_cuda`; manifest optional default changed to match |
| `video/<winner>_latentup_lbh123.json` (conditional) | the round-3 winner | + `MinimaxH3LatentUpscaler3D` → `MinimaxH3LatentUpscaler3DRefineHandoff` (untiled, `lock_audio` on) → second `SamplerCustomAdvanced` with a 2-3 step partial schedule |
| `video/video_seedvr2_upscale_rtxvsr_nvidia.json` | `video_seedvr2_upscale` (its LoadVideo / SaveVideo frame) | SeedVR2 node → the RTX Video Super Resolution node, scale 2, `ULTRA`; SaveVideo crf 10. Per take, never on the assembled cut |
| `video/video_seedvr2_upscale_flashvsr_lihaoyun6.json` (fallback) | `video_seedvr2_upscale` | → FlashVSR v1.1 tiny, LCSA sparse attention on |
| `image/image_krea2_turbo_t2i_lora_restyle_visurena.json` | `image_krea2_turbo_t2i_lora` | `EmptyLatentImage` → `LoadImage` + `VAEEncode` of the panel cell (1024); KSampler denoise 0.35; Cinematic_Artstyle 1.0; prompt expansion off (`30:24` false); output 1024, then the existing panel path down to 768 |

Manifest trap to fix in every new manifest: the base manifest's `optional.unet_name` names the
**stock fp8**, not Singularity, and `optional.sage_attention` is `disabled`. Each new manifest's
optional defaults must match its own graph, so a default can never quietly undo the change.

### Downloads

| What | Size | URL | Needed by |
|---|---|---|---|
| Sage 2.2 wheel `sageattention-2.2.0+cu130torch2.10.0andhigher.post6-cp310-abi3-win_amd64.whl` (abi3 covers our Python 3.12.10) | tens of MB | https://github.com/woct0rdho/SageAttention/releases | round 3 C1 |
| LBH latent upscaler `minimax_h3_latent_upscaler_3d_conv_v1_fp16.safetensors` + nodes | 691 MB | https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler · https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler (refine: https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus) | round 4 only |
| FlashVSR v1.1 weights (if not already beside the disabled node) | per the HF card | https://huggingface.co/JunhaoZhuang/FlashVSR-v1.1 | round 0 fallback |
| **Nothing else.** On disk already: 4-step v0.1 ref2v LoRA (HDD), stock fp8 ref2va (HDD), Singularity int8 (NVMe), Krea2 + Cinematic LoRA, RTX VSR nodes + `nvidia_vfx`. | | | |

Copy the 4-step LoRA to `C:\comfy_models\loras\minimax_h3\` if it wins, so production reads it from the NVMe.

## 5. Fixes that are not take workflows

1. **Take SaveVideo crf (E cause 3).** It is a node parameter, so it ships as the `_crf_visurena`
   file above, and every later variant inherits it. Disk cost: about 6-10 Mb/s per take, so
   roughly 1-2 GB per episode instead of about 300 MB.
2. **Lossless segment extract (code, test-first).** `assemble.py`'s segment extract re-encodes at
   x264 fast CRF 17, the second of three lossy generations. It is an intermediate, so make it
   `-qp 0 -preset ultrafast` (same frames, no loss, a few seconds slower). The only lossy
   encodes left are then the take save at CRF 10 and the master at CRF 14.
3. **Sage install.** Replace the cu128 wheel with the cu130 post6 wheel in the portable Python,
   in a session with no run live (pause the autopilot first). Rollback: reinstall the cu128 wheel.
   The production graph is unchanged until a `_sage_` file is named.
4. **NVENC for book compilation.** `studio/book_compilation.cut_argv` re-encodes every piece with
   libx264 fast CRF 16, about 100,800 frames at 1536². On the i9-13900K that is roughly 20-35 min
   (estimate; time it once). `h264_nvenc` on the 4090 runs that in about 5-7 min, and the
   4090's two NVENC engines allow two pieces at once. Argv: `-c:v h264_nvenc -preset p6 -tune hq
   -rc vbr -cq 16 -b:v 0 -spatial-aq 1 -temporal-aq 1 -bf 3 -profile:v high -pix_fmt yuv420p`,
   keeping the bt709 tags. Every piece must go through the same argv so the book still joins by
   stream copy. Make the encoder a parameter that defaults to libx264, so rollback is one
   argument. Accept it if the frame counts are identical, SSIM against the x264 piece is >= 0.98,
   and the join check still counts every frame.
   - *Better still, for future episodes:* `assemble` forces a keyframe at the card boundary
     (`-force_key_frames`), so the book can **stream-copy** both pieces of a square-matched
     Short with zero re-encode and zero generation loss. Existing ep01-27 masters still need NVENC.
   - **The episode master stays on libx264 slow CRF 14.** It is the deliverable and costs about
     1-3 min (the `assemble` stage measured 77-175 s on ep27). The episode join is already
     stream copy, so NVENC saves about 2 min there, which is not worth the quality.
5. **Single vs double turbo LoRA.** Decided by round 1 (A1 vs A2 vs A3), not by argument. The
   2026-09-19 A/B that adopted 1.0 + 0.7 compared it only against **stock**, never against
   Singularity with a single LoRA.
6. **Panel source: Qwen vs Krea.** Decided by round 2. P2's prior is B1 (keep the Qwen grid for
   layout and room continuity, add a Krea2 texture pass), because it attacks E's top cause
   without undoing the 2026-09-28 room ruling.
7. **The 2048 native-grid hypothesis.** Answered by the R0c data check (§1). Only the 3x1 layout is
   suspect. A fix, if any, goes in `grids.py` layout choice, not in a workflow.
8. **Slideshow zoom shots (E cause 5).** (a) Rung: before a shot goes to the still terminal,
   give it one more seed with a different **move type**. That costs about 1.5-2.5 min per shot,
   and ep20 had 7 such shots. (b) Cap: at most 2 stills per episode, and a still holds no longer
   than 3 s; past the cap the shot is cut shorter or merged into its neighbour. (c) When a still is
   unavoidable, render the push from a 4x supersample (`STILL_PUSH` 1.06 over 4x the pixels
   gives sub-pixel steps), and later run it through RTX VSR with the takes.

## 6. Minutes per episode after adoption (against the 6.0 h median)

Measured basis (`timing.jsonl` ep24-27): takes 60-81 min, take_dq + take_content + take_eye
30-62 min, grids 15-87 min, plan 37-142 min, assemble 4-9 min, QC 8-47 min.

| Change | Δ min / episode | Basis |
|---|---|---|
| A3 4-step (if it wins) | −20 to −30 | sampling 83 s → ~42 s x 25 takes + retakes |
| Sage / CK (if accepted) | −8 to −15 | −25-30 % of the sampling that remains |
| Take crf 10 | +0-1 | encode only |
| Lossless segments | +0-1 | |
| Krea2 restyle per panel (B1) | +6-10 | ~25 cells x 15-20 s + one model swap |
| RTX VSR per take, replacing Lanczos | +3-5 | G |
| Stills rung (≤ 4 shots) | +5-10 | one take each |
| **Net, full adoption** | **≈ −15 to −30** | **≈ 5.5-5.75 h** |
| Net if 4-step loses (Sage only) | ≈ +5 to +20 | ≈ 6.1-6.3 h, over budget; then take B1 alone, or pay for it with the plan stage |
| + latent upscaler 1.5x | +50-100 | adopt only with 4-step and Sage both in, and even then ≈ 6.4-7 h: **over budget, so it stays a bench result, not a default** |
| Book compilation NVENC | −15 to −28 per book compile | outside the episode clock |

The largest speed lever is not in P2's scope: the plan stage (37-142 min) and the check windows
(30-62 min) together cost more than the takes do. P2 flags them to the other debaters.

## 7. Rollback

Each change is a name or an argument:
- the take workflow: `scripts/episode/takes_r2v.py:52 BASE` (the episode runs on whatever name sits there;
  `graph_for(base=...)` already lets the bench run any arm without touching `BASE`). Rollback is
  setting it back to `video_minimax_h3_r2v_turbo_ref8`, whose file is never edited;
- the panel restyle: one flag in the panel step, off by default until it wins;
- the per-take VSR: one flag in assemble; when off, the Lanczos 2x in `assemble.tail` stands;
- NVENC: the `encoder` argument defaults to libx264;
- Sage: reinstall the cu128 wheel, and the production graph keeps `disabled` until the `_sage_` file is named.

A switch follows the repo rules: test first, the architecture page updated if a step changes
(the restyle and the per-take VSR are new steps), a decision file, and a `docs/DECISIONS.md` line.

## 8. Licence flags (flags only, not legal advice; the owner's attorney decides)

- **Qwen-Image 2.1**, which already draws the grids: secondary sources say the Qwen Research License
  (non-commercial). This affects the current chain, not only the proposals, and is one more reason the
  Krea2 path (Krea 2 Community License, free under USD 1M revenue) matters. The Restore and
  Viggle/Turbo8 LoRAs inherit the 2.1 terms.
- H3 base, Singularity (apache-2.0 card) and the fal realism LoRA: the MiniMax H3 Community License.
- FlashVSR ComfyUI node: GPL-3.0 (code); its weights follow the HF card. RTX VSR: NVIDIA SDK terms.
- Sage (woct0rdho builds): Apache-2.0. LBH upscaler: MIT nodes / apache-2.0 weights.

## 9. Publishable (standing goal)

The bench in §2 is the first published **ref2va** quality and speed comparison on a consumer
4090 (F §6: every public grid is fl2va or t2v). It would carry LoRA x1 vs x2, 4 vs 8 steps,
Sage vs CK attention, and int8 Singularity vs stock fp8, judged by measures *calibrated against a
human's good/bad split* rather than by Laplacian. That calibration step is the novel part. It
could ship as a small public repo (configs, seeds, per-phase seconds, the calibrated measures
as a pip-installable script) and as an entry in `MiniMax-AI/awesome-minimax-h3-integration`.
The Krea2 restyle-over-layout pass (B1) is a natural standalone ComfyUI workflow if it wins.
