# G: Image chain and final-master research (2026-10-10)

Researcher G, continuity retro. The question: the owner says the videos look low quality and wants faster renders, inside <= 6 h of machine time per 2-3 min episode. This file covers the image side (sheets, grids, panels, edits) and the final master (upscale, grain, encode). H3 take settings are out of scope.
No workflow files were created. `comfy_studio/workflows/image/*.json` was read and not touched.

## 0. What the chain does today (read from the repo, not assumed)

| Stage | Current setting | Source |
|---|---|---|
| Sheets | Krea2 turbo fp8, Cinematic_Artstyle LoRA, 8 steps er_sde cfg 1, 1536x1024, then USDU 2x (Remacri, denoise 0.2), about 40-60 s each | `comfy_studio/workflows/image/image_krea2_cinematic_2x.manifest.json` |
| Grids | `image_qwen_image_2_1_edit_multi`, **width = 1024*cols, height = 1024*rows** (a 3x3 grid is **3072x3072, 9.4 MP**), 25 steps, cfg 1, no turbo LoRA | `scripts/episode/grids.py:322-323` |
| Panels | Each cell is cut, its gutter removed, cropped square and **downscaled to 768** (`storyboard/h3/shot_NN.png`) | SKILL.md "Panels" |
| Takes | H3 ref2va at 768x768 | `studio/canvas.py` |
| Master | One concat pass: **lanczos 768 -> 1536** (`DELIVER = 2`), x264 slow CRF 14 | `scripts/episode/assemble.py:798-801` |
| Measured time | Grid draws about 17 min per episode (14 draws). Takes are about 130-190 min. | `docs/audit/2026-09-27_episode_speed_plan.md`, `2026-09-30_five_hour_plan.md` |

**Finding 1: the panel is not starved of pixels.** A 3x3 cell is 1024 px and the take reads it at 768, so the panel is downscaled, not upscaled. The `canvas.GRIDS` docstring ("682x682 at nine ... with an upscale") is out of date: `grids.py` overrides the canvas size.
The real risk is somewhere else. **3072x3072 is 2.25x Qwen-Image 2.1's native 2048x2048** (sources: aiweekly.co, aicybr.com). A DiT sampled above its training resolution tends to soften detail and repeat structure, and a repeated structure looks a lot like the duplicate-figure fault. So each panel's detail may sit below what a 1024 px cell suggests. This is a hypothesis: no source measures it for 2.1. Candidate 3 below tests it.

**Finding 2: what the viewer sees is limited by the master, not the picture chain.** Every take is 768 px. The only upscale is a lanczos interpolation, which adds no detail. The 2x is still worth doing because it moves the upload into a higher YouTube tier (the `canvas.DELIVER` docstring). The cheapest visible gain is to make that 2x a learned upscale, and the tool for it is **already installed and unused**:
- `ComfyUI_windows_portable/ComfyUI/custom_nodes/Nvidia_RTX_Nodes_ComfyUI`
- `nvidia_vfx` package
- torch 2.11.0+cu130

`ComfyUI-FlashVSR_Ultra_Fast` is also installed but disabled. `FastFilmGrain` from `comfyui-vrgamedevgirl` is installed.

**Finding 3: license flag, for the owner and his attorney (this is not legal advice).** Several secondary sources say Qwen-Image 2.1 is released under the **Qwen Research License (non-commercial research and evaluation only)**. Earlier Qwen-Image releases were Apache-2.0.
- The grids already run on Qwen-Image 2.1.
- Every 2.1 LoRA listed below inherits that license: Viggle turbo, Restore LoRA.
- If the channel is or becomes monetised, this needs a decision.
- Qwen-Image-Edit 2511 and Qwen-Image 2512 come from the earlier line. Check their licenses separately.
- Krea 2 is under the Krea 2 Community License, which is free for commercial use under USD 1M annual revenue.

Sources: https://aiweekly.co/alerts/alibaba-ships-qwen-image-21-7b-dit-with-native-2048x2048-and-rgba-drops-apache, https://aicybr.com/blog/qwen-image-2-1-local-image-generation-editing-guide, https://comfyui-wiki.com/en/models/krea/krea-2

## Ranked top 5

Ranking is by expected visible gain per machine-minute, with evidence quality and plug-in cost as tie-breakers.

### 1. RTX Video Super Resolution per take, replacing the lanczos 2x: `video_rtx_vsr_take_2x_comfyorg.json`

- **What:** NVIDIA's VSR as a ComfyUI node. It offers quality modes `ULTRA`, `HIGHBITRATE_*`, `DENOISE_*` and `DEBLUR_*`, a scale of 1-4x, 8 or 10-bit, and chunks of about 16 MP per batch. It keeps frame count and fps.
- **URL:** https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI (Apache-2.0, about 577 stars). Discussion: https://reddit.sentinel-team.org/posts/1rrk71v/snapshots/2026-03-13T21%3A28%3A18.36706Z
- **Files:** no model file. It uses the `nvidia-vfx` runtime, already installed. It needs cu130 torch, which is present. Super Resolution works on any RTX card; frame generation needs a 40-series.
- **Claimed gain:** a learned 2x with mild denoise and deblur, close to real time. One r/comfyui user processed a 768x768, 731-frame clip "in seconds, faster than loading the video".
- **Evidence quality:** medium-low. The evidence is anecdotal Reddit with no metrics.
  - For it: "more natural, less smoothed" than SeedVR2.
  - Against it: some users saw "almost no change at 2x", banding in shadows, and "more like Lanczos than generative".
  - It is conservative and invents nothing, which suits our identity gates. It also cannot add the detail H3 never drew.
- **4090 time:** seconds per take, so under 5 min per episode including I/O.
- **Plug-in:** a per-take pass after take acceptance, before `assemble`. It mirrors the per-shot rule in the `video_seedvr2_upscale` manifest: never run it on the assembled cut, so no window straddles a hard cut. `assemble` would then concat 1536 parts with no lanczos. The same node at `scale 1` with `DEBLUR_*` could also be tried on panels (see #3).
- **Test:** pick 3 takes from the owner-judged episodes (wide, medium, close). Render lanczos, RTX ULTRA and RTX HIGHBITRATE side by side. Score each with the existing sharpness measure plus `take_dq`, and let the owner choose. **Cost about 10 min.**

### 2. Qwen-Image 2.1 turbo for grid draws (25 -> 6-8 steps): `image_qwen_image_2_1_edit_multi_turbo6_viggle.json`

- **What:** a step-distillation LoRA on the unchanged Qwen-Image 2.1 base, 6 steps, cfg 1, no negative prompt.
- **URL:** https://huggingface.co/Viggle/Qwen-Image-2.1-viggle-turbo. Write-up: https://comfyui-wiki.com/en/news/2026-09-29-viggle-turbo-v03
- **Files:**
  - `Qwen-Image-2.1-viggle-turbo-v0.3-6step-lora-r256.safetensors` (1.3 GB), or the `-r128` cut (680 MB)
  - merged int8 convrot, fp8 and GGUF transformers are also available
  - custom nodes `viggle_turbo.py` ("Viggle Turbo Sigmas" + BasicGuider + euler)
- **Claimed gain:** about 4.5-5x faster. Vendor timings, base 40 steps against 6 steps: 6-reference group at 1248x1888, 25.8 s -> 5.9 s; panorama at 2176x1088, 14.3 s -> 2.9 s.
- **Evidence quality:** medium. These are the vendor's own timings with visual comparisons only.
- **Documented caveats (they matter here):**
  - "Complex edits (multi-reference composition, face swaps, identity preservation) can produce **duplicated or ghosted figures** and identity drift." That is exactly ep16's fault class.
  - Slightly softer fine texture.
  - Colours a few percent less saturated.
  - The ComfyUI port was "largely written with an AI coding assistant".
- **Alternatives:**
  - **Turbo8:** https://huggingface.co/chriswritescode/Turbo8-LoRA-Qwen-Image-2.1, file `turbo8_lora_step2500.safetensors` (1.36 GB), 8 steps, euler/simple, cfg 1. It ships `comfyui/turbo8_edit.json` and supports up to 10 references. On 192 held-out prompts its PickScore was 21.94 against the teacher's 22.15, and its edit DINOv2 similarity to the teacher was 0.967. Community testers report edits hold best at about 0.65 strength and 16 steps. This is the better-evidenced one.
  - **Alibaba PAI Fun-Acc 4-step:** https://huggingface.co/alibaba-pai/Qwen-Image-2.1-Fun-Acc-LoRAs, file `Qwen-Image-2.1-Fun-Acc-4Step.safetensors`. It is official, but it needs a custom sigma schedule and has no native ComfyUI support yet (Kijai branch only). It also says some edit outputs come out "slightly blurrier and darker". Skip it for now.
- **4090 time:** grids are about 70 s each today, so expect about 15-20 s each. That saves about 12 min per episode, more on grid redraw rungs.
- **Plug-in:** a new template beside `image_qwen_image_2_1_edit_multi`, plus a `LoraLoaderModelOnly`. `grids.py:graph_for` would pick it with steps 6-8 or 16.
- **Gate:** run it only through the existing panel gates (G-CROWD, people_check, panel_content). Run it on the owner-judged calibration set first; accept it only if the duplicate-figure rate does not rise. The speed is small next to takes, so **the duplicate risk outranks the time saved**.

### 3. Per-panel refine at native resolution: `image_qwen_image_2_1_panel_refine_ausboss.json`

- **What:** a Qwen-Image 2.1 "Restore" LoRA. It is trained on damaged-to-clean pairs, including video stills and downscales, to redraw a picture **in place** at about 2 MP per pass. It is paired with the Viggle 6-step turbo.
- **URL:** https://huggingface.co/ausboss/Qwen-Image-2.1-Restore-LoRA. Workflow: https://civarchive.com/models/2988629/qwen-image-21-tiled-upscale (AusBoss nodes >= 2.9.0, ComfyUI >= 0.38).
- **Files:**
  - `qwen-image-2.1-restore.safetensors` (159 MB, rank 32)
  - `Qwen-Image-2.1-viggle-turbo-v0.3-6step-lora-r128.safetensors`
  - optional `texture_fix_vae_for_qwen_image_2.1_bf16.safetensors`
  - base `qwen_image_2.1_int8_convrot.safetensors`, which we already have
- **Settings:** 8 steps with turbo or 25 without, cfg 1, euler/simple, denoise 1. Strength 1.0 for small sharp inputs, 0.5 for blurry ones.
- **Claimed gain (the author's own tests):**
  - 37 shrunk pictures: SSIM 0.578 -> 0.766, same-face 0.821 -> 0.905, worst-corner drift 2.35 -> 0.26 px.
  - Better spatial fidelity than SeedVR2 (0.42 px) and an Elusarca Detail Enhancer (2.07 px).
  - Stated limits: "redraw, not recovery". **Small faces may be redrawn as a different person.**
- **Evidence quality:** medium-low. Single-author metrics on a 5090.
- **4090 time:** about 11 s per pass on a 5090, so about 15-20 s on a 4090. For 25 panels, **about 7-8 min per episode**.
- **Plug-in:** a new step between `panels.py` and the panel gates. It takes the cut 1024 px cell, redraws it at 1024² (or upscales to 1536 and redraws), then downscales to 768 for H3. The panel gates must re-read the refined panel, and `panels.py` already re-gates on changed pixels.
- **Paired test of Finding 1:** render one setup's 3x3 at 3072² (today) and at 2048² (native, 682 px cells), then 2048² + this refine. Measure panel sharpness and the people and face gates. If native + refine wins, the grid drawer gets cheaper as well: 2048² is 0.44x the pixels.
- **Cheaper non-generative arm:** RTX VSR `DEBLUR_ULTRA` at scale 1 on the panel. This takes seconds and carries no identity risk. Run it in the same test.

### 4. Film grain plus a master encode for YouTube's higher tier: `video_master_grain_vrgamedevgirl.json` (or a pure ffmpeg pass in `assemble.py`)

- **What:** add fine, temporal, luma-weighted grain **after** the upscale and before the final encode. This hides the AI "plastic" smoothness and gives YouTube's encoder texture it keeps as detail instead of flattening into banding.
- **Node:** `FastFilmGrain` from comfyui-vrgamedevgirl (installed, `nodes.py:172`). In ffmpeg: `noise=c0s=5:c0f=t+u` (luma only, temporal), with x264 `-tune grain` so the encoder does not smooth it away.
- **Sources:**
  - https://invideo.io/faq/how-do-you-add-film-grain-blur-and-color-grading-to-ai/ (vendor): grade, then grain, then an optional 0.3-0.8 px soften; "if you can see grain consciously, it's too much".
  - https://sync.so/blog/the-film-grain-problem: do not denoise AI footage, because it worsens the plastic look.
- **Evidence quality:** low (vendor blogs), but cheap and reversible.
- **Encode:**
  - YouTube's 2160p SDR guidance is 35-45 Mbps at 24-30 fps (https://support.google.com/youtube/answer/1722171).
  - Whether a higher upload resolution earns VP9/AV1 is **mixed evidence**. A 1440p50 upload got VP9 while 1440p25 got AVC (https://filmdaft.com/how-to-get-better-image-quality-on-your-youtube-videos/). Another test measured 4K VP9 at 8 Mbps against 1 Mbps for the 1080p stream (https://www.provideocoalition.com/uploading-to-youtube-is-4k-worth-it/).
  - Our 1536² is above the 1440 short edge. 2160² is the next tier (RTX VSR scale 2.8125, or 3x then crop).
- **4090 time:** grain under 1 min. A CRF 14 encode at 2160² costs a few CPU minutes. An unlisted pair of uploads is free.
- **Test:** upload the same 20 s at 1536² and at 2160² as unlisted, wait for full processing, and read the codec and bitrate in "Stats for nerds". Keep whichever serves VP9/AV1 at the higher bitrate.

### 5. SeedVR2 7B (sharp) only for stills, not video: `image_seedvr2_7b_sharp_still_numz.json`

- **What:** single-image super-resolution for the **sheets and place pictures**. These feed every grid and are rendered once.
- **URL:** https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler (v2.5.5; code MIT, weights Apache-2.0). Readme: https://huggingface.co/numz/SeedVR2_comfyUI/blob/main/README.md
- **Files:**
  - `seedvr2_ema_7b_sharp_fp16.safetensors` (or `seedvr2_ema_7b_fp8_e4m3fn_mixed_block35_fp16.safetensors`)
  - `ema_vae_fp16.safetensors` (present)
  - `seedvr2_ema_3b_fp16.safetensors` is present today
- **Settings:** batch_size 1 for images; color_correction `lab`; latent_noise_scale 0.05-0.15 if it over-sharpens.
- **Claimed gain:** "most accurate" conservative upscaler in Comfy's own comparison (https://docs.comfy.org/tutorials/utility/video-upscale.md). About 3 s per 2 MP image on a 5090 (Restore LoRA author's comparison).
- **Why only stills:** our own manifest `video_seedvr2_upscale.manifest.json` records a measured 4090 run with a 1008 s DiT phase and frame ghosting, worst on animated content. Comfy's table gives about 312 s for 10 s of 720p even on a 5090. Over 3 minutes of video that is hours, which busts the 6 h budget.
- **Plug-in:** it replaces or follows the USDU 2x Remacri pass in the sheet workflow, and is compared on `sheet_dq` plus the owner's eye. The gain is probably small: Krea2 + USDU is already 3072x2048 and the grid only reads it at a reference size. **Rank 5: try it only if #1-#4 leave sheets as the visible weak point.**

## Considered and ranked below the top 5

| Candidate | URL / files | Why not top 5 |
|---|---|---|
| FlashVSR v1.1 (installed, disabled) | https://github.com/OpenImagingLab/FlashVSR, https://github.com/lihaoyun6/ComfyUI-FlashVSR_Ultra_Fast; weights Apache-2.0 (HF card) | Generative one-step VSR, 11.8x faster than SeedVR2-3B (paper arXiv 2510.12747). Comfy measured about 41 s per 10 s of 720p to 1080p (GPU not named), so about 15-25 min per episode. Ghosting reports depend on settings. Fallback if RTX VSR (#1) adds too little detail. |
| Nunchaku int4 Qwen-Image-Edit-2511 | https://huggingface.co/QuantFunc/Nunchaku-Qwen-Image-EDIT-2511 | Edits are rare in the episode chain and already have the Lightning 4-step LoRA (`Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16`). The speed claims (2-11x) come from the vendor, and quality drops at low rank (r32 < r128). Little to gain. |
| Qwen-Image 2.1 Fun-Acc 4-step (official) | https://huggingface.co/alibaba-pai/Qwen-Image-2.1-Fun-Acc-LoRAs | No ComfyUI support yet, and needs custom sigmas. Revisit when it lands in core. |
| Krea2 Realism V2 LoRA | https://huggingface.co/zeroooo719/Krea2-realism-V2 (MIT, trained on Raw, used on Turbo, strength 1.0-2.0) | A photoreal look pulls against the owner-picked Cinematic_Artstyle (WotW refs style). Sheets already take only 40-60 s on Krea2 turbo's 8 steps, and no 4-step Krea2 distill was found. No speed or quality case. |
| Qwen-Image-Edit 2511 "Upscale2K" LoRA | https://huggingface.co/starsfriday/Qwen-Image-Edit-2509-Upscale2K (2511 version exists) | Same job as #3, but on the older edit model and with no metrics. |

## Budget impact (estimates; measure before claiming)

| Change | Machine time per episode | Visible effect |
|---|---|---|
| #1 RTX VSR per take | +3-5 min | learned 2x instead of lanczos; unmeasured |
| #2 grid turbo | -10 to -15 min | none intended; risk of duplicate figures |
| #3 panel refine | +7-8 min (or about 1 min for the RTX deblur arm) | sharper first frames into H3 |
| #4 grain + encode | +1-3 min CPU | less "AI smooth"; possibly a better YouTube tier |
| #5 SeedVR2 stills | +1-2 min (sheets only) | small |

Net: roughly time-neutral. The 6 h budget is driven by takes and model loads, not this chain. Any real speed gain lies on the H3 side and in load times (the `.hdd_bak` working set), which this research does not cover.

## Evidence caveats

- No source gave a measured RTX 4090 time for any candidate. Every 4090 number above is extrapolated from 5090, A100 or unnamed-GPU figures.
- The Qwen-Image 2.1 ecosystem is three weeks old (released 2026-09-20). Turbo and Restore LoRAs are community or vendor releases with self-reported metrics.
- Per `feedback_gates_are_not_quality`, every candidate is judged on the owner-judged episodes, not on green gates.
