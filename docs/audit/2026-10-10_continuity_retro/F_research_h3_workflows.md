# F. H3 take workflows: what the community has that we don't (2026-10-10)

Researcher F. Question: the owner says take output is low quality and wants faster
renders. Hard budget: a 2-3 min episode (~25 takes) in <= 6 h total machine time.
Scope: community MiniMax-H3 workflows, fine-tunes, LoRAs, speed levers and video
upscalers, ranked into a top-5 shortlist with a proposed workflow name for each.
**No workflow file was created**; the names are for the debate.

Prior research this builds on (not repeated here):
- `docs/research/ref2v_speed_2026-09-16.md`: phase timings, FastH3/TaoMate rejected, the Sage/CK/int8-convrot A/B that was proposed.
- `docs/analysis/research/ref2v-speedup-survey.md`: ref2v LoRA lineage, the 4-step v0.1 dating, alibaba-pai PDD verdict.

## 1. What we run today (read from disk, not assumed)

`comfy_studio/workflows/video/video_minimax_h3_r2v_turbo_ref8.json`, built by
`scripts/episode/takes_r2v.py`:

| Node | Setting |
|---|---|
| UNETLoader | `Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8.safetensors` (21 GB) |
| LoraLoaderModelOnly x2 | `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16` at **1.0, then again at 0.7** (1.7 total) |
| PathchSageAttentionKJ | **`disabled`**. The log says "Using pytorch attention". |
| Sampler | euler / beta, 8 steps, MiniMaxH3SigmaShift 12 / 3, BasicGuider |
| CLIP | `qwen3vl_32b_minimax_h3_nvfp4_awq` |
| Canvas | **768 x 768** (1:1, `studio/canvas.py`), 24 fps; upload is a Lanczos 2x (`canvas.DELIVER`) |
| Launch | `--reserve-vram 2` |

The sampling cost, measured from `ComfyUI/user/comfyui.prev.log` (2026-10-09): **8/8 in
1:22, 10.3-10.4 s/it**. A whole prompt takes 112-197 s, so 25 takes come to about 50-85
min before retakes. That agrees with the owner's 80-100 min once retakes are counted.

The environment has not changed since 2026-09-16. The installed wheel is still
`sageattention-2.2.0+cu128torch2.10.0andhigher.post5` on `torch-2.11.0+cu130`, so
Sage still cannot import. `comfy_kitchen 0.2.35` is present.

Already installed and unused: `seedvr2_videoupscaler` (with `seedvr2_ema_3b_fp16`),
`ComfyUI-FlashVSR_Ultra_Fast.disabled`, `Nvidia_RTX_Nodes_ComfyUI` (RTX Video Super
Resolution), `comfyui-frame-interpolation`, and
`MiniMax-H3-Ref2VA-Acc-8Step.safetensors` (alibaba-pai). The ref2v 4-step v0.1 LoRA is
also on disk.

## 2. Ranked shortlist (top 5)

The ranking is expected gain per unit of risk to our failure modes: duplicated
characters, identity drift, and lip-sync lag. "Plugs in" means it fits the current graph
and `takes_r2v.py` injection without a new runner.

### #1. Turn attention on: Sage 2.2 cu130 wheel (or CK int8 attention)
**Proposed:** `video_minimax_h3_r2v_turbo_ref8_sage_woct0rdho.json`

| | |
|---|---|
| URL | https://github.com/woct0rdho/SageAttention/releases (v2.2.0-windows.post6, 2026-07-17; post7 2026-10-09) |
| Author | woct0rdho (Windows builds of thu-ml SageAttention) |
| File | `sageattention-2.2.0+cu130torch2.10.0andhigher.post6-cp310-abi3-win_amd64.whl` replaces the cu128 wheel; node 3 set to `sageattn_qk_int8_pv_fp16_cuda` (or `auto`). Alternative with no graph change: launch flag `--use-ck-attention` (comfy_kitchen int8 attention, already importable). |
| Claimed gain | ComfyUI docs say "roughly 2x". The measured H3 numbers are lower: RTX 3090 129 -> 94 s (-27%, comfylab); RTX 4070 342 -> 242 s (-29%, note.com); 4090 CK attention 1.34x whole prompt (cited 2026-09-16) |
| Evidence | Several independent single-machine reports agree on 25-35%. No 4090 + ref2va + Singularity number exists. |
| Our estimate | Sampling 83 s -> ~58 s, so ~25 s less per take, **~10-15 min less per episode**. It does not touch decode (15-25%). |
| Quality risk | int8 QK is a small numerical change. RunComfy warns that Sage can blur H3 on some machines, so the DQ gate must judge one take. |
| License | Apache-2.0 |
| Plugs in | **Yes.** Node 3 already exists and `sage_attention` is already an inject slot. The only change is the wheel. |

Why it ranks first: it is the only lever that is near-free in quality and needs no
graph surgery. It was proposed on 2026-09-16 and never run. Note: Sol-Attn (kijai's
repo is now deprecated in favour of built-in comfy-kitchen sparse attention) is
**not** recommended. One tester got a **duplicated character at tau 1.8** (19% faster),
and at tau 1.4 the gain was only 6%. Duplication is our worst failure mode.

### #2. Replace the Lanczos 2x on delivery with a real video upscaler
**Proposed:** `video_upscale_flashvsr_lihaoyun6.json`, with the faster fallback
`video_upscale_rtxvsr_nvidia.json`. These are not H3 graphs: they run once on the
assembled master, not per take, and they sit beside the existing `video_seedvr2_upscale.json`.

| Candidate | URL / author / file | 4090 time for our master (~174 s, ~4,200 frames, 768² -> 1536²) | Evidence | License | Plugs in |
|---|---|---|---|---|---|
| **FlashVSR v1.1, tiny mode** | github.com/lihaoyun6/ComfyUI-FlashVSR_Ultra_Fast (801 stars); weights `JunhaoZhuang/FlashVSR-v1.1` | ~15 fps at 1408x768 on a 4090 D (aireet/flashvsr-sm89-ops, JSON benchmarks, LPIPS 0.011). At our 2.36 MP output, **~6-10 fps, so ~7-12 min per episode**. ComfyUI docs: 10 s 720p -> 1080p in ~41 s. | Benchmarks plus the official card. Warning: wrappers without LCSA sparse attention lose quality. | GPL-3.0 (node); weights per card | **Installed, disabled.** Rename the folder to enable. |
| **NVIDIA RTX Video Super Resolution** | `Nvidia_RTX_Nodes_ComfyUI` (NVIDIA) | Vendor claim: "near instant"; one user upscaled 81 frames on a 4070 Ti "near instantly". **~1-3 min per episode.** | Vendor claim plus anecdote. Conservative and GAN-like: it adds less detail. | NVIDIA SDK terms | **Installed.** |
| SeedVR2 3B (fp16 on disk) | github.com/numz/ComfyUI-SeedVR2_VideoUpscaler | numz README: 4090 3B fp8 ~2.4-3.2 s/frame at ~1080p, so **3-4 h per episode**. | Benchmarks. Best fidelity in every comparison. | Apache-2.0 | Installed, but **over budget** for a whole master. Only for a thumbnail or a 5 s hero shot. |

Why it ranks second: `canvas.py` itself says the Lanczos 2x "adds NO detail". The
master is 0.59 MP, below every YouTube HD tier. A VSR model is the cheapest place to
add perceived detail, because one pass on the master costs minutes and no retakes.
Risk: VSR can sharpen artefacts, and any text or title card must bypass it. The test
is to run QC and the eye judges on one shipped master upscaled both ways.

### #3. Two-pass: H3 latent upscaler, then a short refine at 1.5x
**Proposed:** `video_minimax_h3_r2v_turbo_ref8_latentup_lbh123.json`

| | |
|---|---|
| URL | https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler (254k downloads, apache-2.0) · nodes https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler (MIT, 730 stars) · refine fork https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus (updated 2026-10-08) |
| Files | `minimax_h3_latent_upscaler_3d_conv_v1/minimax_h3_latent_upscaler_3d_conv_v1_fp16.safetensors` (691 MB) -> `models/latent_upscale_models/`. Nodes: `MinimaxH3LatentUpscaler3D`, `MinimaxH3LatentUpscaler3DRefineHandoff` (`lock_audio` on by default keeps pass-1 audio bit-exact) |
| Claimed gain | Upscales the 24-ch latent directly, so it skips VAE decode/encode. Pass 2 adds real detail at the target resolution. |
| Evidence | **Weak.** The author publishes no numbers. comfylab (RTX 3090, fl2va, 736x416 -> 1344x768): **tiled refines duplicated content** (512 tiles: duplicates in most frames); untiled was clean but 340 s. No ref2va test exists anywhere. |
| Our estimate | Base 768² 8 steps as today, then 1.5x to 1152² with a 2-3 step partial-denoise refine (sigmas[0] < 1). That is 2.25x tokens at roughly 25-35 s/step, plus a larger decode, so **+2-4 min per take, +50-100 min per episode**. 2x (1536²) would be about 4x tokens, too slow and near OOM. |
| Risks | (a) duplication, our worst fault, so **untiled only**; (b) our `MiniMaxH3AddGuide` pinned cells are 768-space and must be re-checked in pass 2; (c) `lock_audio` must stay on, because the voice is the ruler. |
| License | MIT nodes / apache-2.0 weights; the base remains under the H3 Community License |
| Plugs in | Partly. Two new nodes after `SamplerCustomAdvanced`, plus `takes_r2v.py` must learn a second sigma schedule. |

Why it ranks third: it is the only lever that adds generated detail inside H3 rather
than after it. It only fits the budget if #1 and/or #4 pay for it. It is unproven on
ref2va, so it is an A/B on 3 takes, not a switch.

### #4. Fix the LoRA recipe: one LoRA, or the Singularity author's own 4-step pairing
**Proposed:** `video_minimax_h3_r2v_turbo_ref4_singularity.json`, plus a control
`video_minimax_h3_r2v_turbo_ref8_single.json` (8-step v1.0 at 1.0 once)

| | |
|---|---|
| URL | https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity (apache-2.0; files unchanged since v1.3 on 2026-09-05; w4a8 added 2026-09-18) |
| Author | WarmBloodAban / AIGC-Singularity |
| Files | `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` (**already on disk**). The model card's only recommended accelerator is "`minimax_h3_ref2v_turbo_4step_v0.1` (Enables 4-step fast inference)". |
| Claimed gain | Sampling 8 -> 4 steps. sepiablue's 4090-class grid: lightx2v 4 steps = **3.44x vs base 20**, against 2.08x at 8 steps. For us that is **83 s -> ~42 s per take, ~17 min less per episode**. |
| Evidence | Author recommendation plus a speed benchmark (fl2va, 4070). No published quality A/B on ref2va. The 2026-09-12 survey dates v0.1 as pre-768p. Our canvas is now 768² (0.59 MP), which is **inside** the 768p envelope; the 768x1344 that motivated that warning is gone. |
| Why it matters for quality too | We stack the 8-step LoRA at **1.0 + 0.7 = 1.7 total strength**. That setting came from the downloaded community workflow and was A/B'd only against the stock base (2026-09-19), never against a single LoRA on Singularity. Over-strength distill LoRAs are the classic cause of the "over-sharpened / plastic / deep-fried" look (see the r2v_turbo manifest note on non-EMA ckpt850). Community consensus (wildminder guide): the turbo LoRA costs audio and fast-motion quality, and strength 0.75 is more stable than 1.0. |
| Risks | 4 steps: fast motion breaks first and hard cuts smear into dissolves (h3-turbo-eval grid). Shift must be re-checked; do not inherit 12/3 blindly. |
| License | apache-2.0 (Singularity) / apache-2.0 (lightx2v) |
| Plugs in | **Yes.** Only file names, strengths and the step count change. `lora_second` gets dropped or set to 0. |

Why it ranks fourth: it is a zero-cost A/B with a plausible quality cause *and* a 2x
sampler win. The 3-way A/B is: 8-step at 1.7 (today) / 8-step at 1.0 / 4-step v0.1 at
1.0. Same seed, same 3 takes, judged by the DQ, content and eye gates.

### #5. A people-realism LoRA on top of Singularity
**Proposed:** `video_minimax_h3_r2v_turbo_ref8_realism_fal.json`

| | |
|---|---|
| URL | https://huggingface.co/fal/MiniMax-H3-Realism-People-LoRA (2026-08-10, 82k downloads, 467 likes) |
| Author | fal |
| File | `h3-realism-people-t2v-i2v-r2v.safetensors`, trigger `r34l1sm` at the start of the prompt, strength 1.0 (0.6-0.8 lighter). It touches only the shared attention projections and says it is r2v-compatible. |
| Claimed gain | Realistic faces, skin texture, film lighting. |
| Evidence | **The best of any H3 style LoRA:** 19 same-seed on/off pairs plus a 16-config human review. Untested with turbo LoRAs and with Singularity, a merge whose card already claims "de-oiled skin" and so may double up. |
| Alternative | Civitai "Minimax H3 Cinematic Version (Official Release)" by TuTu_1018 (civitai.com/models/2937734, 2026-09-14, 591 MB, no trigger, 0.5-0.7). It claims fewer unwanted auto-cuts and less limb distortion. **No examples on the page**, so it is weaker evidence. |
| Time | ~0 (one more LoRA patch) |
| License | MiniMax H3 Community License (same as the base we already run) |
| Plugs in | Yes: a third LoraLoaderModelOnly plus a trigger word in `h3_prompt`. |

Why it ranks last: the evidence is decent, but the domain is uncertain (modern people
vs. Victorian and period casts) and it interacts with two other adapters. Test it only
after #4 has settled the LoRA stack.

## 3. Free, not a workflow: the Singularity prompt specification

The Singularity repo ships
`MiniMax_H3_Singularity_Prompt_Writing_Specification_Enhanced_EN.md` (2026-09-12). It
documents the **H3 training-corpus prompt layout**: `subject_definitions` /
`summary` / `retention_analysis` (fully_preserved, attribute_transfer, ...) /
`detailed_description` shot-by-shot with `[Shot 2] At 00:03.000` timestamps /
`overall_soundscape`. It says "camera chain = position + movement + direction +
speed/amplitude + subject followed". It also says a `<Picture N>` is a keyframe only
when it genuinely anchors time; an appearance-only image belongs inside a Subject
definition. This bears directly on the camera and duplication memories ("H3 obeys
direction, not amount", "Shot form is the quality"). Compare it with `studio/h3_prompt.py`
before any LoRA work. It costs nothing to render.

## 4. Looked at and rejected

| Candidate | Why not |
|---|---|
| Singularity `v1.3_Pruned_w4a8` (11.8 GB) | Needs starsfriday's experimental W4A8 loader. Reports describe it as slower than int8 and in one case corrupt. Weight error 7.3% rms vs 1.0% for int8_convrot. |
| Singularity GGUF (Abiray, Q3-Q8) | GGUF dequantizes on the fly, so it is slower than native int8 on a 24 GB card. Only a VRAM lever, and we don't need one. |
| NVFP4 H3 checkpoints | Emulated on Ada (sm_89). A speed loss on a 4090. |
| PulpCut `minimax_h3_ref2va_pruned_turbo_int8_convrot` (turbo merged into ref2va) | The merged LoRA is the lightx2v `ema_pruned` FL2VA lineage, the family that caused camera-scale pumping (2026-09-10). Its timings are Apple M1 only, with a one-prompt SSIM. The *idea* (merge the turbo into the base so no runtime LoRA patch is needed) is sound; it should be done ourselves with Singularity plus the chosen ref2v LoRA once #4 settles. |
| FX-FeiHou `MiniMax-H3-Remix v0.6` | No dates, no samples, no benchmarks. |
| Sol-Attn sparse attention | Duplicated a character at tau 1.8; only 6% faster at the safe tau 1.4. |
| EasyCache / Spectrum / Cache-DiT | Lossy at 8 distilled steps. Spectrum needs 30-50 steps and doesn't fire on R2V for some users. EasyCache "cannot combine with Turbo LoRAs". |
| FastH3-8-Step-V2, TaoMate, OpenVDN | Not ref2va (2026-09-16 / 09-12 research, unchanged). |
| RIFE / GIMM frame interpolation | H3 already renders 24 fps with joint audio. Rendering fewer frames shortens the audio and the lip-sync it carries, so interpolation buys nothing safe for takes. |
| Newer lightx2v ref2v LoRA | None. HF tree as of today: ref2v is still only `4step_v0.1` (2026-08-13) and `8step_v1.0_768p` (2026-09-03). |
| Newer Singularity than v1.3 | None. All weight files are dated 2026-09-05 / 09-18. |

## 5. Budget check (per episode, 25 takes, estimates marked ~)

| Configuration | Takes (no retakes) | Note |
|---|---|---|
| Today | 50-85 min | measured |
| #1 + #4 (Sage, 4-step) | ~25-45 min | ~2x on sampling; decode unchanged |
| #1 + #4 + #3 at 1.5x | ~75-145 min | the detail pass is paid for by the speed levers |
| + #2 FlashVSR on master | +7-12 min | one pass |

Even the heaviest stack leaves most of the 6 h for plan, refs, voice, grids, retakes
and QC. All numbers marked ~ are extrapolations from other GPUs and models. The
debate should treat them as hypotheses, and the first GPU slot should run the
same-seed A/B on 3 takes in this order: #1, #4 (3-way), #3, then #2 on an existing
master.

## 6. Publishable (standing goal)

There is no public 4090 benchmark of **ref2va** speed or quality levers. Every grid
found (jo-nike h3-turbo-eval, sepiablue, comfylab) is fl2va or t2v. The 3-take A/B above,
published as a small JSON-backed benchmark repo (configs, seeds, seconds per phase,
DQ/identity metrics), would be the first ref2va benchmark on consumer hardware and
would make a natural companion entry in `MiniMax-AI/awesome-minimax-h3-integration`.

## Sources

- https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity (+ prompt spec, file tree via HF API)
- https://huggingface.co/lightx2v/Minimax-h3-Turbo (file tree via HF API)
- https://huggingface.co/Abiray/MiniMax-H3-Singularity-GGUF
- https://github.com/wildminder/awesome-minimax-H3/blob/main/guides/minimax-h3-performance.md
- https://comfylab.dev/blog/workflows/minimax-h3-comfyui-speed-vram-rtx-3090/
- https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler · https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler · https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus
- https://github.com/woct0rdho/SageAttention/releases
- https://github.com/kijai/ComfyUI-SolAttn_triton
- https://docs.comfy.org/tutorials/utility/video-upscale
- https://github.com/aireet/flashvsr-sm89-ops · https://huggingface.co/JunhaoZhuang/FlashVSR-v1.1 · https://github.com/lihaoyun6/ComfyUI-FlashVSR_Ultra_Fast
- https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler
- https://huggingface.co/fal/MiniMax-H3-Realism-People-LoRA
- https://civitai.com/models/2937734/minimax-h3-cinematic-version-official-release
- https://huggingface.co/PulpCut/MiniMax-H3-Ref2VA-Turbo-INT8-ConvRot
- https://huggingface.co/FX-FeiHou/MiniMax-H3-Remix
- https://huggingface.co/starsfriday/MiniMax-H3-w4a8
- https://civitai.com/articles/33693 (CongXS "70% less time": no data, ignored)
