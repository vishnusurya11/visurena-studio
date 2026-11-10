# Pika H3 Flex on a consumer GPU: speed, quality, recipes (2026-11-03)

Web research only. Nothing downloaded, nothing run on a GPU by the author.
Tags: TESTED = someone measured it and says how. CLAIMED = a page says it, no test shown.

## Short answer

Maybe, and it is cheap to find out. Nobody has published an anime test, a split-sigma recipe, or a 4090 number for the Turbo LoRA.

- The Turbo LoRA (4-step Ref2VA, on Singularity v2) halves the reference setup's step count (8 to 4). Per-step cost does not change. So a take should cost about 55% of today's time. That is an estimate from step count. CLAIMED.
- The only real 4090 number is for the plain 6-step adapter: 162 to 182 s for 5 s at 1344x768 (FL2VA, no refs). TESTED.
- A 4070 test shows the 6-step Pika is slower than LightX2V 4-step (7m11s vs 4m59s) at equal image quality. So Pika's gain is quality (audio, faces), not speed. TESTED, one poster.
- The "split sigma for action" method is not written down anywhere I could reach. The the tutorial video is the only source, and its transcript is still blocked.
- Provenance: the Turbo LoRA is a community fusion (akhaliq), not an official Pika file. The plain adapter is official.

Verdict: run 3 test arms (below). Do not rebuild the production graph on this until faces and lip sync pass by eye.

## Gap 1. Consumer-GPU numbers

| GPU | Setup | Clip | Time | Per step | Status | Source |
|---|---|---|---|---|---|---|
| RTX 4090 | Pika 6-step FL2VA adapter, 1344x768, ~120 frames | 5 s | 162-182 s (avg 172) | ~29 s | TESTED (attention backend not stated, no refs) | note.com rossy_laboratory |
| RTX 5090 | Pika 6-step vs base 25-step, 768x1376 | 10 s | 4 m 55 s vs 20 m 34 s (4.18x) | ~49 s | TESTED (X post) | DeepForest X |
| RTX 5090 | Pika 6-step T2V, 768x1344 | 5 s | 98-102 s | ~17 s | TESTED | TrueNorthAI note |
| RTX 5090 | Pika 6-step R2V (refs) | 5 s | 132 s | ~22 s | TESTED | TrueNorthAI note |
| RTX 5090 | Pika 6-step R2V, English dialogue + BGM | 15 s | 696 s | ~116 s | TESTED | TrueNorthAI note |
| RTX 3090 Ti | Flex 6-step vs LightX2V 8-step | 5 s | 146.8 s vs 212.6 s | 24 vs 27 s | TESTED, single run | aireiter |
| RTX 4070 | Pika 6-step, 832x1216 | 5 s | 7m11s | ~72 s | TESTED (X post) | sep_is_heim X |
| RTX 4070 | LightX2V Turbo 4-step / 8-step, same | 5 s | 4m59s / 9m14s | ~75 / 69 s | TESTED | same |
| RTX 4070 Ti S 16 GB | R2V, 5 refs, 768x1376: DMAD 4-step 113 s, Pika 6-step 160 s (140 with RefMod), LightX2V 8-step 210 s, 20-step 510 s | 5 s | as listed | | TESTED | comfylab note |
| H200 | 848x480, 121 frames: official 6-step 60 s, Turbo 4-step 40 s, 2-step ~25 s, 8-step HD 70 s | 5 s | | ~10 s | TESTED by uploader | akhaliq HF |
| A100 | official 6-step 109 s, Turbo 4-step 66 s | 5 s | | | TESTED by uploader | akhaliq HF |

Findings:
- No source gives 4090/5090/3090 numbers for Turbo 2/4/8-step, or for lite_r32 vs full. Gap stays open. The lite file has the same architecture cost; I expect equal speed (inference, not measured).
- Per-step cost does not drop with fewer steps. The saving is only the step count (uploader, CLAIMED; consistent with the 4070 data).
- Scaling is worse than linear in clip length: 15 s took 5.3x a 5 s clip (TESTED, TrueNorthAI).
- Refs add time: R2V 132 s vs T2V 100 s on the same 5090 (TESTED).
- A 4090 at 1344x768, 6 steps, 5 s is about 29 s/step. The reference setup's production number of 52 s/step is for longer takes with refs and a guide. Not comparable until P0 is run.
- The first run is slow (181 s vs 128 s on 4070 Ti S). Do not time cold loads.
- Official tutorial claim "about a minute for 5 s on a single card" has no card named. Ignore it.
- VRAM (CLAIMED, aireiter): stock-like 480p 5 s uses 66-69 GiB before offload; 24 GB cards need offload. The reference setup already run int8 pruned bases, so this is the reference setup's known regime.

## Gap 2. Quality reports

Nothing covers anime or lip sync with a reference audio. All items below are general.

- Faces: a write-up says the official distill reduces the thin look and face distortion common to low-step turbos. CLAIMED. The the tutorial video (relayed, not seen) says faces stay readable at far and mid distance where LightX2V pixelates. CLAIMED.
- Image vs LightX2V: poster says image quality equal, Pika audio better (4070 test). TESTED, n=1.
- Hair, tone: Pika has more natural hair than DMAD 4-step, widest dark range, least flat-area jitter; LightX2V 8-step has crushed blacks. TESTED by eye, n=1 (comfylab).
- Hands and action: Pika says it trails on physics, multi-scene, lighting/materials, and action-heavy reference tasks. CLAIMED (Pika's own blog). Users report limbs collapsing in intense fights. CLAIMED. Few-step files: "fast motion is the weakest case" (uploader).
- Popping on fine high-frequency detail at 4 steps in a latent-upscale second pass; keep 6. CLAIMED (WAS, via ComfyUI Wiki).
- Style: surreal prompts drift CG; "no dramatic improvement over existing accelerated setup" (rossy note). TESTED, n=3 prompts, live-action only.
- Camera: moves are advisory; give each an endpoint ("pushes in and stops on her face"); timing off by 0.2-0.3 s; "wide shot" renders as medium unless the subject is described small in a big room. CLAIMED (ComfyUI docs). Camera pumping on the FL2VA-lineage LoRA with ref2va was seen in the reference setup's own earlier work, so use Ref2VA files only.
- Lip sync: no report. Audio quality drops below 6 steps (uploader, CLAIMED). The reference setup's guide is a recorded voice, so lip sync/mux lag must be checked by us.
- Singularity v2 fixes the audio-reference path (V1 did not condition on it properly) and widens action coverage. CLAIMED (model card via ComfyUI Wiki). This matters for us because the setup feed an audio guide.
- Uploader side-by-sides (Turbo 4-step on Singularity v2 vs official on stock H3, 5 prompts) exist in the HF repo; the claim "faster and better-looking" is the uploader's. CLAIMED.
- No side-by-side of Turbo vs LightX2V 8-step on the reference setup's kind of shot exists.

## Gap 3. Exact recipes

Official 6-step adapter (TESTED by Comfy-Org, PR #70):
- Sampler lcm, BasicGuider cfg 1.0, ManualSigmas `1.0, 0.972973, 0.923077, 0.8, 0.571429, 0.333333, 0.0`, LoraLoaderModelOnly 1.0, no turbo stacked.
- I checked the math: these are the knots 1000/750/500/250/100/40/0 after shift 12. So they already include the video shift; adding a shift node on top would double it.

Turbo LoRA (CLAIMED by uploader):
- LoraLoaderModelOnly 1.0 alone. Steps = the file's number (2, 4, 8). cfg 1.0. Scheduler `simple`. Sampler euler, lcm or res_multistep. Flow shift 12 (Ref2VA, 6 for FL2VA), audio shift 3.
- Baked Flex strength 0.5 (2/4-step), 0.6 (8-step HD).
- The 4-step Ref2VA file is the one "recommended with Singularity" (card). It uses lightx2v ref2v v0.1; Singularity v2's own card also recommends v0.1 for 4 steps. So v0.1 on v2 is the matched pair. CLAIMED.
- The uploader's sampler sweep script tests res_multistep+simple, lcm+simple, lcm+beta, euler+beta at 4 steps, but ships no results. The reference setup's production euler/beta is in that sweep; no winner is published.

Split sigma for action: NOT FOUND. The uploader's action script uses a single plain `BasicScheduler simple` (no split, no shift code). The the tutorial video is the only likely source. Plausible reading (my guess, not sourced): run the first steps at high sigma with one setting and finish with another via SplitSigmas. Do not build on this.

Latent-upscale finish (the 960x544 to 1920x1088 recipe):
- Report: 6-step pass at 960x544, latent upscale, 4-step pass at 1920x1088, then to 2560x1440, 3 m 17 s, GPU not stated. CLAIMED. Nodes and denoise not given.
- Tools that exist: rockerBOO/h3-latent-upscaler (GPL-3.0): `MiniMax H3 Latent Upscale`, `Conditioning Upscale` (keep wired, scale and method must match), `Add Noise (resample)`, `Shift Sigmas (video->audio)`. Suggested pass 2: scale 1.5, bilinear, `simple`, 15 steps, denoise 0.4 (starting points, not tuned, with a normal model). Stock LatentUpscaleBy and AddNoise break on the joint audio-video latent. Set audio_denoise 0 to keep audio. TESTED? No. CLAIMED by the repo.
- For us this is not needed: the reference setup's finish is the RTX 2x upscale. Skip.

lite_r32 vs full: lite keeps 96.1% of the fused spectral energy (CLAIMED), is 0.3 GB vs 3.9 GB. No quality comparison anywhere. Worth one arm because it also cuts load time.

Singularity v2 vs v1.3: v2 = same recipe, retrained: wider action, tighter prompt following, audio-reference fix, stronger style naming. No benchmark between them. CLAIMED. The reference setup already have the v2 pruned int8 convrot r2 file on disk (names only).

the second 8-step base merge compatibility: no source. the second 8-step base is a different 8-step setup of ours; stacking the Turbo on a distilled merge is untested. Treat as unknown. Keep the second 8-step base for close/medium until an arm beats it.

## Gap 4. Provenance and risk

- Official: Pika-Labs/Pika-H3-Flex adapters (fl2va, ref2va, rank 128, 1.96 GB bf16 ComfyUI files), merged into Comfy-Org/MiniMax-H3 (PR #70). Pika says no end-to-end ComfyUI render was verified before upload (CLAIMED via ComfyUI Wiki).
- Turbo LoRA: akhaliq upload (a copy sits under another user's name; one tool listing also shows a Pika-Labs path, so ownership is unclear). Built by rank-concatenating Pika's adapter with LightX2V and pDMD distills; error 2.6e-7 vs stacking (author's number, CLAIMED). HF Community tab shows no discussions at all, so no user bug reports exist yet. Absence of reports is not evidence of safety.
- Licence: MiniMax H3 Community License Agreement, derivatives under the same terms; has regional and commercial limits (US/EU/UK/Korea named by one writer). Not legal advice. The pDMD part is Apache 2.0. Check before publishing episodes commercially.
- Safetensors only, no custom nodes, so code risk is low.
- Known issues: audio degrades below 6 steps; 4- and 8-step files are not interchangeable; 2-step is draft only; do not stack other accelerators; fast motion weakest; popping at 4 steps in upscale pass; limbs collapse in hard fights (reports); stylised LoRAs trained on undistilled H3 need re-testing. Frozen frames and camera pumping: seen in the reference setup's own FL2VA-lineage test, not in any outside report.

## Gap 5. Newer than 2026-11-02

Nothing found. No Pika Flex v1.1 or v2. Official ComfyUI templates are `video_pika_h3_flex_t2v` (needs ComfyUI 0.43.2+), `_ref2va` and `_fl2va` (0.30.0+). Ref2VA takes up to 9 images, 3 videos, 3 audio clips (12 total). The reference setup's ComfyUI 0.43 is fine for ref2va; verify the patch level if the setup load the t2v template. The Turbo LoRA page dates from 2026-10-29. The the tutorial video title: "MiniMax H3 - Pika H3 Flex + Nvidia Regen 2K Upscale ComfyUI Walkthrough". Description, chapters and transcript still blocked (YouTube page and a transcript mirror returned nothing). To get them: owner pastes the description, or runs yt-dlp --write-auto-subs on his side.

## Addendum A. The RunningHub 4090 lead (second tutorial video)

Video claims, 5 s clip at ~1 MP on an RTX 4090 (CLAIMED). I could not reach the video, its description, the RunningHub workflows or the truncated "github.com/ama..." repo. My searches found no such repo.

| Step | Time (5 s) | Gain |
|---|---|---|
| Official workflow | ~125 s | |
| + SageAttention + Sol-Attn | ~50 s | 2.5x |
| + Kijai's Sol VAE | ~47 s | small |
| + SelfLift 2-stage latent upscale | ~29 s (5 s), ~61 s (10 s) | 1.6x |

Two cautions. The 125 s baseline is below the independent 4090 test (162-182 s, TESTED), so it was probably a better-set-up baseline. And the reference setup's graph already runs "comfy kitchen attention", a fast path. The 125 to 50 s jump is likely mostly "default attention to a fast backend", which the setup already have. The reference setup's Sol gain will be smaller than 2.5x.

The nearest independent 4090 repo is ling5717/Pika-H3-Flex-4090 (GPL-3.0, TESTED on Windows, CUDA 13). A 15 s 1344x768 text-to-video takes ~370-380 s; Ref2VA 1344x768, 243 frames, 398 s. It launches with `--use-ck-attention --reserve-vram 3.5`. It uses FFN chunking and a low-peak LoRA node. No Sol-Attn, no SelfLift. That is about 25 s per 1 s of video at 6 steps with ck-attention, close to the reference setup's 28.5 at 8 steps. So the real gain has to come from fewer steps, sparse attention, the VAE and the low-res first stage.

### 1. Sol-Attn

- NVIDIA method (paper arXiv 2607.24027): training-free block-sparse attention. No special weights. CLAIMED.
- It is already in ComfyUI core. Node `BlockSparseAttention` (category advanced/model), file `comfy_extras/nodes_sparse_attention.py`, merged 2026-09-06 (PR 16072). Kernels are in comfy-kitchen (PR 117, merged 2026-08-29, needs 0.2.33 or newer).
- TESTED by reading the reference setup's files: the reference setup's ComfyUI has that node file, it calls `ck.sol_attn`, and the reference setup's comfy_kitchen is 0.2.40. SageAttention 2.2.0 and triton-windows 3.5 are also installed.
- Node inputs (read from the reference setup's file): backend (Sol-Attn tau, top-k SLA, VSA), tau default 1.3 (0-4), start_percent 0.2, end_percent 1.0, min_tokens 12288 (shorter runs stay dense), extra_tokens 256, sink_conditioning default `exact_kv_and_rows` (text, audio and reference rows stay exact), dense_blocks, verbose.
- Conflict with the reference setup's backend: none expected. The core author said the node does not replace the dense backend, which is still `ModelAttentionBackend` or `--use-ck-attention`. Keep the reference setup's node and add BlockSparseAttention. CLAIMED, not run.
- Wheel build: none for us, the kernel ships in comfy-kitchen. Risk: the reference setup's 0.2.40 wheel may lack a Windows sm_89 kernel. The node then says "no compiled sol_attn kernel for this GPU" and runs dense. A PR tester on Windows had to patch the build. Turn `verbose` on to see. Unknown until run.
- Older community packs are redundant: kijai/ComfyUI-SolAttn_triton (Apache-2.0, now deprecated, tested 4090/5090), Saganaki22 and r-vage ComfyUI-sol-attn, quzopl/ComfyUI-SolAttn-H3 (CuTe DSL, Linux-oriented, the Triton fallback is slower than Sage). Do not install these.
- Measured: attention kernel 1.3-1.65x over SageAttention on 4070 Ti and 5090 (TESTED by repo authors, kernel only). End to end on a 5090, 15 s, 20 steps: 9.91 vs 8.92 s/it, about 10% (TESTED, one pair). Gains are small under ~12k tokens. The first `start_percent` fraction runs dense, so in a 4-step run step 1 of 4 is dense (96 of 183 s in one 5090 report).
- Quality: an approximation. About 30.7 dB PSNR vs dense even with routing off (quzopl). Speech degraded in one case with sink mode text. Reference-image runs can lose speed (0.9x at 16k rows).
- Applies to ref2va with a guide, and to Singularity and the second 8-step base? It patches attention in the shared DiT, so yes by construction. The default sink setting is meant to keep reference and audio rows exact. No source tested a guide with Sol. CLAIMED.

### 2. Kijai's Sol VAE

- ComfyUI PR 17411, merged 2026-10-28. A distilled decoder (NVlabs, Efficient-Large-Model/Sol-H3-VAE) that decodes the whole clip at once, no tiles. File `minimax_h3_sol_vae_int8_convrot.safetensors` in Comfy-Org/MiniMax-H3 `vae/`. It is already on the reference setup's disk and unused. The reference graph loads `minimax_h3_video_vae_fp16`.
- Decode time on a 5090, 1344x768x124: fp16 H3 10.7 s, int8 H3 4.61 s, Sol fp16 3.28 s, Sol int8 1.70 s. TESTED by the PR author. A 4090 is slower.
- Quality cost: 39 dB PSNR vs the stock decoder. Sol int8 vs Sol fp16 is 61 dB (no loss). Issue 17429 reports faint seams on a 128 px grid on smooth skin. Anime has big flat areas, so look for exactly this.
- Memory: 2.4 GiB of activations, grows with length, cannot tile.
- Saving: about 9 s per 5 s clip on a 5090, so about 1.5-2 s per 1 s of video from fp16. The stock int8 convrot VAE (4.6 s) is a lower-risk first step.

### 3. SelfLift Progressive Sampler

- Repo facok/comfyui-SelfLift (licence not stated on its page). Node "Progressive Sampler (MiniMax H3)". Run early steps at low resolution, lift the latent, finish at full resolution. The H3 version is experimental and not validated by the paper.
- Inputs: sampler and sigmas like SamplerCustom. Only `euler` with s_churn 0 (the setup use euler). Also `transition_step`, `lowres_scale`, `rho`, `w_min`, `w_max`, `latent_upsample`, `upscaler_model`, `upscaler_unload`, experimental `highres_tiling`.
- Lifter: LBH-123-AI/Minimax_h3_latent_Upscaler v1 (Apache-2.0, 345 M params, ~691 MB). The bf16 file `minimax_h3_latent_upscaler_3d_conv_v1_bf16.safetensors` is already in the reference setup's `models\latent_upscale_models\`. It needs the repo's custom node pack (not installed). With no lifter, `rho=0.6, w_min=w_max=1` is the author's starting point.
- The only concrete values published are `transition_step=6`, `lowres_scale=0.5` from a one-seed diagnostic. A 384 px short edge may be outside H3's training range. I found no exact 2-stage recipe (stage steps, denoise). Other sources: DrakenZA's multi-stage sampler (any sampler, 2-8 stages, tested only on a toy model); rockerBOO's pack (GPL-3.0) suggests lift 1.5x, 15 steps, denoise 0.4 for a plain model.
- Audio and guide: SelfLift's page says nothing about ref2va or guides. DrakenZA says audio state carries across stages (toy tests). Open issue CGlide 39: an error with audio timeline mode in the SelfLift H3 sampler. So MiniMaxH3AddGuide plus SelfLift is UNTESTED, the biggest unknown.
- Anti-flicker claim (manual sigmas to Euler + Simple removes opening-frame flicker): the video's claim only, CLAIMED. The reference setup use euler with beta. Check the first 10 frames in every arm.

### 4. The workflow repo and JSONs

Not found. RunningHub needs a login and no search returned the six workflows or a repo starting "ama". Ask the owner for the repo URL in the video description. That is the one missing input. From the names, the graph is probably: base H3 + Pika LoRA, BlockSparseAttention, Sol VAE, stage-1 sampler, H3 latent upscale, stage-2 sampler.

### 5. Does it apply to the reference setup's graph?

Sol-Attn and Sol VAE belong to the shared DiT and VAE. SelfLift is sampler-level. Nothing is Pika-specific except the step count. CLAIMED by construction, nothing tested with a guide. The reference setup's graph already differs from the video: ckattn, int8 pruned, 8-step turbo, 1280x736. Expect smaller gains.

## Recommended test arms (max 4)

Start from production graph the reference production graph (Singularity v1.3 int8, two turbo LoRAs 1.0 + 0.7, euler/beta 8 steps, SigmaShift 12/3, ckattn, fp16 VAE, 1280x736). Keep refs, storyboard last ref, voice guide, CRF 10, seed. Test shots: one 12 s wide action take and one medium dialogue take. Reference today: 28.5 s per 1 s of video. Predictions are estimates from step counts and the claims above, not measurements.

| Arm | Graph change | Predicted s per 1 s video | Why |
|---|---|---|---|
| A1 | Base Singularity v2 pruned int8 convrot r2. Delete both turbo LoRAs. One LoraLoaderModelOnly `pika_h3_flex_turbo_4step_ref2va` 1.0 (lite_r32 is a same-speed variant). euler, BasicScheduler simple, 4 steps, SigmaShift 12/3, keep ckattn. | 15-16 | Core Pika arm. Needs a 3.9 GB (or 0.3 GB) download. |
| A2 | A1 plus core `BlockSparseAttention` (Sol-Attn, tau 1.3, start 0.2, sink exact_kv_and_rows) after ckattn, plus the VAE `minimax_h3_sol_vae_int8_convrot` instead of fp16. Both already on disk. Also run the same two changes on today's 8-step recipe as a control. | 11-14 | Cheapest speedup, no new files. The control separates Sol from Pika. |
| A3 | A2 plus SelfLift H3 Progressive Sampler in place of SamplerCustomAdvanced: euler, lowres_scale 0.5, transition_step 2 of 4, lifter = H3 latent upscaler bf16 (on disk, node pack needed). | 8-11 | The video's last step (0.62x claimed). Highest risk: guide audio, faces at half resolution. |
| A4 | A1 with `pika_h3_flex_turbo_8step_hd_ref2va`, 6 steps, plus A2's sparse attention and Sol VAE | 15-17 | Quality fallback if A1 faces or action look soft. |

Whole episode (150 s of video): takes are about 71 min now. A1 about 38 min, A2 about 31 min, A3 about 21 min. Stop at the first arm that passes by eye. Wide and full shots first. Keep the second 8-step base for close and medium until an arm beats it on the same seed.

Pass criteria, by eye: faces at wide and medium distance, identity against the sheet, no limb or hand morph, no camera pumping, no opening-frame flicker, flat-colthe reference setup's seams (Sol VAE), line-art stability (sparse attention), lip sync and mux lag against the guide wav, clean line audio. Log s per step and total render per take after a warm run, with sol_attn verbose on to confirm the kernel ran.

## Sources

- Rossy lab, RTX 4090 measured (TESTED): https://note.com/rossy_laboratory/n/n659395cd0cb8?hl=en
- Comfy lab, 4070 Ti S (TESTED): https://note.com/comfylab/n/n5aa240debf48?hl=en
- TrueNorthAI, RTX 5090 (TESTED): https://note.com/truenorthai/n/nf2b53afadc86?hl=en
- DeepForest, 5090 6-step vs 25-step: https://x.com/DeepForest_Inc/status/2115935879017701581
- Kamimoto, 4070 Pika vs LightX2V (via search snippet; page itself returned 402): https://x.com/sep_is_heim/status/2115957073997681124
- akhaliq Turbo LoRA card, files, timings, scripts: https://huggingface.co/akhaliq/Pika-H3-Flex-Turbo-LoRA
- Same repo, copy under sekkit: https://huggingface.co/sekkit/Pika-H3-Flex-Turbo-LoRA
- ComfyUI Wiki, Turbo: https://comfyui-wiki.com/en/news/2026-11-02-pika-h3-flex-turbo
- ComfyUI Wiki, Flex (sigma knots, NebSH latent upscale, popping): https://comfyui-wiki.com/en/news/2026-10-29-pika-h3-flex
- Comfy-Org PR #70 (official sigmas, lcm, cfg 1): https://huggingface.co/Comfy-Org/MiniMax-H3/discussions/70
- ComfyUI docs, Pika H3 Flex templates and known issues: https://docs.comfy.org/tutorials/video/pika/pika-h3-flex
- Pika research blog (method, weaknesses, no anime eval): https://pika.art/blog/pika-h3-flex-research
- Review with 3090 Ti and VRAM notes: https://aireiter.com/blog/pika-h3-flex-review-open-weights-6-step-video-model
- WAS Pika-H3-Flex-PTD alternative (4-step merge, no timings): https://huggingface.co/WAS/Pika-H3-Flex-PTD
- rockerBOO h3-latent-upscaler (GPL-3.0): https://github.com/rockerBOO/h3-latent-upscaler
- Singularity v2 notes: https://comfyui-wiki.com/en/news/2026-10-22-h3-singularity-v2
- Tutorial video (page only, no transcript): https://www.youtube.com/watch?v=5sC-FjwGqmQ
- ling5717 Pika-H3-Flex-4090 (4090, GPL-3.0, TESTED): https://github.com/ling5717/Pika-H3-Flex-4090
- ComfyUI core Sparse Attention PR 16072: https://github.com/Comfy-Org/ComfyUI/pull/16072
- comfy-kitchen Sol-Attn PR 117: https://github.com/Comfy-Org/comfy-kitchen/pull/117
- ComfyUI Wiki, sparse attention and compiler: https://comfyui-wiki.com/en/news/2026-09-08-h3-sparse-attention-compiler
- kijai ComfyUI-SolAttn_triton (deprecated): https://github.com/kijai/ComfyUI-SolAttn_triton
- quzopl ComfyUI-SolAttn-H3: https://github.com/quzopl/ComfyUI-SolAttn-H3
- r-vage ComfyUI-sol-attn: https://github.com/r-vage/ComfyUI-sol-attn
- Sol H3 VAE, ComfyUI PR 17411: https://github.com/Comfy-Org/ComfyUI/pull/17411
- facok comfyui-SelfLift: https://github.com/facok/comfyui-SelfLift
- DrakenZA multi-stage sampler PR: https://github.com/DrakenZA/Comfyui-H3-DrakenNodes/pull/1
- LBH-123-AI H3 latent upscaler (Apache-2.0): https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler
- CGlide issue 39, audio mode error with the SelfLift sampler: https://github.com/CGlide/ComfyUI-CGlide/issues/39
