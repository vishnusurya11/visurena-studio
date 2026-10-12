# R2-Q: faces and texture, new levers for H3 takes (2026-10-10)

Round-2 researcher Q. This was online research plus reading code on disk. Nothing was rendered, no GPU was used, and no
workflow, code or library file was changed. Scratch work (a sigma calculator and the downloaded READMEs) is in
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\sig.py` and
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\r2q_dl\`.

Base for every arm: `D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\video\video_minimax_h3_r2v_turbo_ref8_crf_visurena.json`
(node 1 Singularity v1.3 int8 · node 2 ref2v 8-step v1.0 768p @1.0 · `lora_second` same file @0.7 · node 3 Sage disabled ·
node 4 MiniMaxH3SigmaShift 12/3 · node 8 MiniMaxH3ReferenceToVideo, `ref_image_size` match · node 9 BasicScheduler **beta** 8 ·
node 11 euler · node 17 SaveVideo crf 10).

Round 1 already covered these, and they are not repeated here: Sage/CK attention, RTX VSR and FlashVSR, the LBH latent upscaler,
4-step v0.1, LoRA once vs twice, the fal People LoRA, the TuTu cinematic LoRA, grain, and the Krea restyle.

---

## 0. Two findings from reading the code (no web needed, and they outrank everything found online)

### 0a. The 768x768 canvas is our own ceiling, not H3's

- `ComfyUI\comfy_extras\nodes_minimax_h3.py` (installed build 3dd559d81, 2026-09-20). `MiniMaxH3ReferenceToVideo.execute`
  calls `_empty_av_latent(width, height, length)` **with the width and height verbatim**. `adapt_canvas` (short edge forced
  to 768) is called in exactly one place: the **reference-video** branch (`cw, ch = adapt_canvas(vw, vh)`). The git history
  shows this has been the case since the node landed (57500fc5b, 2026-08-03).
- `studio/h3.py` (commit ba7eb9c, 2026-09-02) ports `adapt_canvas` onto the **output canvas**. `canvas.size()` therefore
  returns 768x768 for 1:1, and `check_canvas` refuses anything else ("the short edge is always 768"). The commit's
  evidence was a 640x384 request that "rendered 1280x768". On today's node that could only come from a graph that went
  through some other path (a subgraph or Resolution Selector). The R2V node in the current file does not do it.
- The model's real limit is an **area** cap: `MAX_PIXELS = 768*1344` (1.03 MP). ComfyUI's H3 tutorial says the
  "native canvas" is about 0.98 MP and warns only against going above the 768x1344 area
  (https://docs.comfy.org/tutorials/video/minimax/minimax-h3). The ref2v 8-step LoRA was distilled at 1344x768
  (ModelTC model table; comfyui-wiki 2026-09-04).
- **Our 768x768 takes use 0.59 MP, which is 57 % of the trained pixel budget.** A 1:1 canvas at the cap is **992x992**
  (0.98 MP; 1024x1024 is over the cap). Every face gets 1.29x the linear pixels and 1.67x the area. HF Comfy-Org/MiniMax-H3
  discussion #30 and the FaceRefine README both name head size in pixels as the cause of H3's face collapse, and this is
  the cheapest place to buy those pixels.
- Check before believing it (about 20 s of GPU): submit the base graph with `width 992, height 992, length 22` and ffprobe
  the output. If it reads 992x992, the ceiling is ours. If it reads 768x768, something rewrites it and Arm 1 is void.

### 0b. Our sampler schedule is not the one the turbo LoRA was distilled on

- ModelTC (the lightx2v authors) document the distillation grid as **uniform**: `q_i = (N-i)/N`, then shifted
  (https://github.com/ModelTC/Minimax-H3-Turbo README, "Note on shift"). Their own ComfyUI Ref2VA example graph
  (`example_workflows/video_minimax_h3_ref2v_lightx2v_turbo.json`) uses **`simple`** with euler. We run **`beta`**.
- The shift is contested:
  - **12/3**: lightx2v's own release post, HF lightx2v/Minimax-h3-Turbo discussion #51 (2026-09-03). This is what the house
    adopted on 2026-09-11.
  - **6/3**:
    - vllm-omni's recipe validates every request against the artifact and rejects a mismatch. It lists
      `minimax_h3_ref2v_turbo_8step_v1.0_768p` at `flow_shift 6`.
    - niw/mmh3 `docs/ref2va.md` runs it "at the shifts it was trained with: `--shift-video 6 --shift-audio 3`".
    - comfyui-wiki's 2026-09-04 card gives training shifts 6/3.
    - Every other 768p row in ModelTC's table is 6/3.
- The sigmas the model is actually evaluated at (8 steps, computed with ComfyUI's scheduler maths, `scratchpad\sig.py`):

| schedule | sigma points the DiT sees (last NFE in bold) |
|---|---|
| **today: shift 12, beta** | 1, .995, .983, .961, .923, .855, .721, **.425** |
| distillation grid if 12/3 is right (shift 12, simple) | 1, .988, .973, .952, .923, .878, .800, **.632** |
| distillation grid if 6/3 is right (shift 6, simple) | 1, .977, .947, .909, .857, .783, .667, **.462** |

  Today's schedule matches **neither** contract on 6 of its 8 points. A few-step distilled student evaluated off its
  grid is a known source of "over-cooked" or faceted output. Beta at shift 12 also packs three NFEs above 0.96, where
  little detail is decided. The house's only recorded beta-vs-simple judgement ("simple = softer",
  `video_minimax_h3_r2v_turbo.manifest.json`) was made on the old community ckpt850 FL2VA LoRA at 6 steps, not on this LoRA.
  Note that "softer" is the opposite of the faceting the owner complains about.

Both findings are free to test, and both feed Arms 1 and 2.

---

## 1. Ranked top 5 bench arms

Costs come from the phase-0 bench on this 4090 (`BENCH_phase0.md` §2): 8-step sampling of 8.1-15.8 s/it for 90-175
frames at 768x768, about 18-30k tokens. From those numbers, s/it grows as about tokens^1.27. An episode is about 30 renders,
retakes included. Budget: median 5.55 h after phase 3, ceiling 6 h, so there are about 25 min of headroom.

### #1. Native canvas: 992x992 (and 896x896) instead of 768x768
**Workflows:**
- `video_minimax_h3_r2v_turbo_ref8_crf_visurena_native992_comfyorg.json`
- sub-arm `video_minimax_h3_r2v_turbo_ref8_crf_visurena_native896_comfyorg.json`
- paired speed arm `video_minimax_h3_r2v_turbo_ref8_ref4_singularity_native992_comfyorg.json` (the A3 4-step graph at 992)

| | |
|---|---|
| Source | Stock node source (§0a); ComfyUI H3 tutorial "native canvas 0.98 MP"; ModelTC model table (ref2v 8-step distilled at 1344x768); HF Comfy-Org/MiniMax-H3 discussion #30 (faces fail when the head is small in frame) |
| Node changes vs base | node 8 `width` 992, `height` 992 (896/896 for the sub-arm). Nothing else in the graph. In the bench, the overlay sets them directly, because `takes_r2v.py` gets 768 from `canvas.size()` |
| Inputs that must follow | The panel staged as `<Picture>` must be **992** (today `panels.py` LANCZOS-downs the 1024 cell to 768). With `match` the panel is never upscaled, so a 768 panel under a 992 canvas is a lower-resolution anchor than the canvas. For the bench, re-cut the shipped shots' 1024 cells to 992. Sheets need nothing: under `match` they scale to the canvas area, so they get 1.67x more face pixels automatically |
| Evidence | **Medium.** The mechanism is read from the source and the vendor docs. No public 1:1 H3 A/B at 768 vs 992 exists, and #30's poster says faces distort on wides "regardless of input res" (the reply attributes that to head size). |
| 4090 cost / take | Tokens x1.67, so s/it about x1.92. Sampling at the median take is about 90 s, rising to about 173 s. VAE decode is about +60 %. **About +100 s per render, about +50 min per episode at 8 steps: over budget on its own.** 896²: about +50 s, **+25 min**. **992 + 4-step (A3): about ±5 min vs today**, because 4 steps at 992 cost what 8 steps cost at 768. VRAM: a 175-frame take goes from 30k to about 50k tokens on the 21 GB int8 model with `--reserve-vram 2`. Watch for partial offload, which shows as an s/it cliff. |
| Risks | Duplicates: more canvas can mean more room for a second figure, and the clone counter must stay at 0. Composition changes with resolution at a fixed seed: same seed does not mean same picture, so judge per shot, not per pixel. Delivery: 992 to 1536 is a 1.55x non-integer Lanczos (`canvas.py` warns about ringing). Either deliver at 1984 (2x) or use RTX VSR, which won narrowly in phase 0. |
| Production cost if it wins | Test-first changes to `studio/h3.py` (`adapt_canvas` stays for reference videos only, and the output canvas rule becomes area <= 768*1344 on the 32 grid), `canvas.size`, `panels.py` (992), and `assemble` DELIVER. That is an architecture-page change (canvas service). |
| Acceptance | Owner's eye on 1:1 face crops (S4, S6, D1, D2); banding non-inferior; identity >= A1; clones 0; lip lag within ±0.1 s; ran-graph assertion that `width`/`height` are 992 **and** ffprobe reads 992x992 |

Why first: it is the only lever that adds face pixels **inside** generation without a second pass. The faceted look is a
face drawn from too few tokens and then sharpened by the distillation, and this raises the token count where the face is.

### #2. Put the sampler back on the LoRA's contract: `simple` scheduler, with the shift split 12 vs 6
**Workflows (three cells, all zero cost):**
- `video_minimax_h3_r2v_turbo_ref8_crf_visurena_simple_modeltc.json`: node 9 `scheduler` beta to **simple**. Node 4 stays 12/3.
- `video_minimax_h3_r2v_turbo_ref8_crf_visurena_simple6_vllmomni.json`: node 9 **simple** and node 4 `shift_video` 12 to **6** (`shift_audio` stays 3).
- `video_minimax_h3_r2v_turbo_ref8_crf_visurena_ersde_kijai.json`: node 11 `sampler_name` euler to **er_sde** (core sampler, stochastic noise re-injection each step). Node 9 stays beta, 12/3.

| | |
|---|---|
| Source | ModelTC README + example graph (simple, uniform grid); lightx2v HF discussion #51 (12/3); vllm-omni `recipes/MiniMaxAI/MiniMax-H3.md` and niw/mmh3 `docs/ref2va.md` (6/3); comfyui-wiki 2026-08-07 (Kijai: lightx2v turbo LoRA "0.75 strength, 4 steps, er_sde or sa_solver") |
| Files | None new. All nodes are core. `manifest.optional.scheduler/shift_video` must match each graph (the phase-0 manifest trap). |
| Evidence | **Medium for `simple`** (it is the authors' own graph). **Contested for 6 vs 12** (official post vs two implementations that validate against the artifact). **Low for er_sde** (one tester note, on a different LoRA family). The house rendered one iteration at 6/3 on 2026-09-11 and replaced it **because it was a "mismatch", not because it was measured worse**. |
| 4090 cost / take | **0 s.** Same NFE count. |
| Risks | Lower shift moves NFEs to low noise: more texture, less structural settling, so duplicates and limb errors may rise. Singularity's duplicate fix was measured at 12/beta. The audio schedule is derived from the same base grid (`MiniMaxH3SigmaShift` docstring), so **lip lag must be re-measured** on all 4 dialogue takes. The house's 2026-08-07 note recorded "disco lights" from res_multistep on ckpt850, so stochastic samplers can misfire on distilled LoRAs. |
| Acceptance | Same as #1. Cells that tie on banding and identity are ranked by the owner's eye on face crops. A cell that raises clones on any shot is out. |

Why second: it costs nothing, it takes a GPU-hour, and it corrects a contract violation whatever the outcome. If
`simple6` wins, its last NFE at 0.46 (vs 0.425 today, but with the middle of the schedule moved down) is the most
plausible free fix for "plastic". It should run **before** #1 so that #1 is measured on the right schedule.

### #3. Per-shot face refine with H3 itself: ComfyUI-H3-FaceRefine (Carasibana)
**Workflow:** `video_minimax_h3_r2v_turbo_ref8_crf_visurena_facerefine_carasibana.json`. This is a second graph run on a
finished take, with the same models resident, so there is no model swap.

| | |
|---|---|
| URL | https://github.com/Carasibana/ComfyUI-H3-FaceRefine (MIT, 461 stars, v1.1.2, pushed 2026-09-13; 13 issues, all closed). Audio lock: `custom_nodes/ComfyUI-H3-NativeAudioLock` from https://github.com/Shrek3OnVH5/MiniMax-H3-NativeAudio-MusicVideo-Workflow |
| What it does | Detects and tracks the face per frame (YOLO), smooths the crop (centre window 21, size window 51), crops to a canvas (`auto_capped_768`, crop_factor 2.5), **re-renders the crop with `MiniMaxH3ReferenceToVideo` img2img** (H3 Inject Video Latent + Per-Frame Denoise; bigger faces get less denoise: 1.0x at <= 30 px down to 0.35x at >= 120 px), audio locked to the take's own track via `MiniMaxH3NativeAudioLock`, then stitches back (feather 6, colour_match 1.0, face-only paste, fade where no face is found). PySceneDetect splits shots at hard cuts. |
| Node changes vs base | Keep nodes 1, 2, `lora_second`, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15. **Add** `VHS_LoadVideoPath` (the take), `H3FaceTrackCrop` (detector `bbox\face_yolov8m.pt`, **already on disk**; `select` = identity_reference with the staged `sheet_front`; `identity_model` = `clip_vision`, because the README says insightface is for photographs and ours are painted), `H3InjectVideoLatent`, `H3PerFrameDenoise` (wraps the MODEL after node 4), `MiniMaxH3NativeAudioLock` (take audio). Node 8's `width/height/length` come from the track node, and **ref 1 = the character's sheet_front**, which re-anchors identity on every frame. Node 9 `denoise` **0.35-0.40** with 8 steps (the README says not to use SplitSigmas). Then `H3FaceStitchBack` goes into node 16/17 (crf 10), and the original take audio is muxed unchanged. |
| Install (environment change; do it in a window when nothing else is running, not mid-series) | Clone the pack. Copy the AudioLock folder in. `pip install insightface scenedetect` into `python_embeded`. **Hazard:** `onnxruntime 1.23.2` and `onnxruntime-gpu 1.23.2` are **both** installed, and the README warns that this silently puts identity matching on the CPU. Impact-Pack and the subpack, VHS, ultralytics 8.3.235 and SAM are already present. |
| Evidence | **Medium-low.** The README shows before/after frames only, with no metrics and no GPU timing. Issue #14 (re-locking onto another person) was fixed in 1.1.2. Issue #19 (Per-Frame Denoise ignored denoise) was closed 2026-09-28. Known artefacts, as the README states them: the face "boils" if the box jitters, the head drifts against the body above moderate denoise, short shots get less smoothing and shiver, and multiple people need one chained pass each. Third-party warning (seedance.tv "fix faces at a distance"): a detailer can replace the face with a "flawless stranger", so lower denoise and stronger reference fix that. |
| 4090 cost / take | The crop canvas is 512-768, which is 0.44-1.0x our take's tokens. At 8 steps that is about 35-110 s, plus encode/decode of the crop (about 10-15 s) and detection (seconds). **About 50-120 s per face subject.** Applied only to takes whose main face is between about 40 and 160 px tall (wide and medium shots; not close-ups, which do not need it, and not crowds), about 8-14 renders per episode: **+10-25 min per episode.** That only fits next to the 4-step A3 savings (-10 to -25 min). |
| Risks | Lip-sync: the mouth is re-rendered at 0.35-0.40 denoise under the locked audio, so lag must be re-measured. Seams at hat brims and collars, which our costumes have plenty of. Every refined take needs the clone and identity gates re-run. A wrong subject in two-shots (manual pick or `identity_reference` fixes it). |
| Acceptance | Same face crops before and after. Identity to the sheet must **rise**. Lag within ±0.1 s. No visible seam on a frame-by-frame scrub of 2 takes. Clones 0. |

Why third: it is the only temporally aware face lever found that keeps **our** look, because the refiner is H3 with the same
LoRA, not CodeFormer. It also attacks the first-to-last decay on faces directly, because every frame's face is re-anchored to
the sheet. It ranks below #1 and #2 because it costs install work and time on every take.

### #4. Feed the references at full resolution: `ref_image_size` max
**Workflow:** `video_minimax_h3_r2v_turbo_ref8_crf_visurena_refmax_comfyorg.json`: node 8 `ref_image_size` match to **max**.
Nothing else changes.

| | |
|---|---|
| Source | Node source: `max` scales a reference down only if its short edge is over 2048 (`REF_IMAGE_SHORT_EDGE`). `match` scales every reference down to the **canvas area**, which is 0.59 MP today. ModelTC: distillation used `match`. ComfyUI tutorial: "Reference tokens ride along every sampling step… face angle can drift away from the reference as the clip goes on". |
| Why it might matter | A `sheet_front` crop (659-952 x 2048, about 1.6 MP) is cut to about 480x1230 under `match`, so the face is about 120-150 px. Under `max` it stays at full size, with a face of about 200-250 px. The panel (768) is unchanged, because `max` never upscales. |
| Evidence | **Low.** The mechanism is from the source. It is off the LoRA's training distribution, and no public test exists. |
| 4090 cost / take | About +1-1.5k tokens per character reference (2-4 refs) on 18-30k: **+5-20 % sampling, +5-15 s per render, +3-8 min per episode.** |
| Risks | Off-distribution input to a distilled student: identity could get better or worse. Larger references can pull the model toward copying the sheet's pose ("the panel IS the sheet", A §2). |
| Note | It is partly subsumed by #1, because at 992 `match` already gives references 1.67x the area. Run it at 768 only, or as a 2x2 with #1 if #1 wins. |

### #5. A newer distill with a "plastic fixed" claim: larryvrh v4 step600 EMA as the turbo LoRA
**Workflow:** `video_minimax_h3_r2v_turbo_ref8_crf_visurena_v4ema600_larryvrh.json`:
- node 2 `lora_name` changes to `minimax_h3\minimax_h3_turbo_v4_step600_ema_pruned_comfyui.safetensors` @1.0 (**already on disk**, `models\loras\minimax_h3\`; the non-pruned file will not patch the pruned base correctly)
- **delete `lora_second`** and wire node 3 to node 2
- node 9 `simple`, 8 steps; node 4 12/3

| | |
|---|---|
| URL | https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora (apache-2.0, 208k downloads); pruned conversion https://huggingface.co/Momoking/MiniMax-H3-Turbo-Lora-ComfyUI |
| Claim | "the over-sharpening / plastic look of the v1 (~850) line is fully resolved in v4", with "finer micro-detail (faces, fingers, texture)". 6-8 steps is best; above 8 it gets over-sharp. Strength 0.8-0.95 if it looks grainy. |
| Ref2va evidence | Prompt Mastery's RunningHub workflow "Minimax H3, most realistic skin" (2026-09-28) runs **Singularity ref2va + EMA-600 @1.0 + fal People** as its "God Tier" for skin, with the caveat "backgrounds go soft and complex prompts get ignored". Its "Balanced" tier is ref2v 8-step v1.0 + People. https://www.runninghub.ai/post/2104471397757386753/ |
| Evidence | **Low.** The author's own claim plus one workflow author's tier notes. No numbers. |
| 4090 cost / take | **0** (it replaces a LoRA patch, and one patch instead of two saves a little). |
| Risks (high) | This is a T2V/FL2VA-lineage LoRA on ref2va. Its v1 sibling (ckpt850) gave **camera-scale pumping** on episode 1 (the 2026-09-10 manifest note), and that is why the house moved to the dedicated ref2v LoRA. "Complex prompts get ignored" collides with "H3 obeys direction" (camera verbs are our control surface), so the cut/move judges must read every render. |
| Why still in the top 5 | It is the only distill on disk whose stated purpose is to remove the plastic look, and it costs 6 renders to rule in or out. |

---

## 2. Bench plan for these arms (same shots and seeds as phase 0: S2 S3 S4 S6 D1 D2, `scripts/bench/h3_arms.py` overlay, ran-graph knob assertions)

| Order | Arm | Renders | GPU (about) |
|---|---|---|---|
| 0 | canvas probe: 992x992, 22 frames, ffprobe | 1 | 1 min |
| 1 | #2 three cells x 6 shots | 18 | 40 min |
| 2 | #1 on #2's winning schedule: 896, 992, 992+4-step x 6 (panels re-cut to the canvas from the 1024 cells) | 18 | 70 min |
| 3 | #5 x 6 | 6 | 15 min |
| 4 | #4 at 768 x 6 (2x2 with #1 only if #1 wins) | 6 | 15 min |
| 5 | #3 on the 4 face takes of the winner (after the install window) | 4 | 10 min + install |
| | **total** | 53 | **about 2.5 h** |

Judging:
- Phase 0 showed that only **banding** votes. `texture` would reward the crunch, and `face_flat` is inverted. So the face
  question is decided by the **owner's eye on 1:1 face crops** (a contact sheet of the face box at the 8/50/92 % frames), and
  identity, clones and lag are hard non-inferiority checks.
- A face-specific ruler is worth calibrating on the same content-matched good/bad split before this bench. Phase 0's ruler
  scored the whole frame, and the bad faces were small.
- One candidate is the share of 8x8 blocks inside the face box with near-zero variance whose neighbours differ by a step
  edge (polygonal patches), normalised by face height.

## 3. Temporal decay (first frame to last loses 20-45 % detail): what exists

**No H3-specific fix was found.** The levers that act on the decay, in order of evidence:
1. **#3 FaceRefine** re-anchors the face on every frame to the sheet. This is the only lever aimed at the decay on faces.
2. **#1 native canvas** and **#4 refmax** give the references more tokens. The ComfyUI tutorial ties reference drift over a
   clip to the reference's pull at every step, and its own fix ("turn Lightning off, 25 steps") costs about 3x and is out of budget.
3. **Shorter takes.** E measured "longer takes end softer", and the house's lip-lag lesson already favours shorter takes.
   This is a planning rule, not a workflow.

Looked at and rejected:
- Guide frames mid-take or at the last frame (`MiniMaxH3AddGuide`): house rule "no last-frame pin" (freeze or dissolve).
  HF discussion #55 also reports that dense guides freeze the face.
- FreeInit-style re-noising: it needs repeated full samplings (2-3x).
- Sliding windows: our takes (90-175 frames) are inside the 5-15 s trained range.
- Seedance's warning applies to extension chains, which we do not run.

## 4. Looked at and ranked below the top 5

| Candidate | Source | Why not |
|---|---|---|
| LTX-2.5 hybrid refine of the H3 take (decode, LTX x2 latent upscale, 3 steps from sigma 0.78) | https://ai-muninn.com/en/blog/minimax-h3-ltx-hybrid-refine-rtx5090 (measured: 0.909 repaints the face into another person, 0.85 changes props, 0.78 keeps both; 5090 hybrid 40 s vs native 1344x768 51.5 s). `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` and ComfyUI-LTXVideo are **on disk** | It refines at 1536² with a second 22 GB stack on a 24 GB card, which means model swaps per take unless it is batched after all takes. Estimated **+40-70 min per episode**. A different model repaints our painted look. It is the best "more detail" lever if #1 fails, but it is over budget. |
| fal People LoRA, new evidence only | RunningHub (above) uses it on Singularity ref2va. HF Comfy-Org/MiniMax-H3 #55: at 1.0 it removed ref2va's red-cheek colour drift at 768 (not at 256/512) | Round-1 #5, not repeated. Add 0.6-0.8 to #2's winner if the owner wants more skin. Photoreal pull against the painted house look. |
| Video face restore (CodeFormer/GFPGAN per frame, Faceless "Face Restore (Video)") | runcomfy node pages; facerestore_cf | Per-frame, so it flickers. It pulls toward photographic faces, the "flawless stranger". |
| SVFR (CVPR 2025), KEEP, DicFace, PGTFormer, DVFace | arXiv 2506.13355, 2604.14560; SVFR has a ComfyUI wrapper | SVFR runs on SVD (heavy, minutes per clip). The others have no ComfyUI node. All are trained on photographed faces. |
| NAG (normalized attention guidance) | ChenDarYen/ComfyUI-NAG, NAG-Extended | No H3 implementation (supported: Flux, Wan, Hunyuan, SD3.5, SDXL, Krea2). |
| CFG-Zero*, APG, dual sampling with a CFG>1 first pass | RunComfy "MiniMax H3 Dual-Sampling R2V" (no settings published) | They need CFG>1, which doubles the NFE per step. The dual-sampling graph publishes no numbers. |
| Detail Daemon / Lying Sigma | ComfyUI-Detail-Daemon (not installed) | Image-model evidence only, nothing on video or distilled models. RES4LYF **is installed** if anyone wants a 6-render curiosity. |
| res_2s / RES4LYF ClownSampler | RES4LYF (installed) | 2 NFE per step. The house's res_multistep "disco lights" note. No H3 evidence. |
| t8star `minimax_h3_ref2va_patchin_hf102` | https://huggingface.co/t8star/minimax_h3_ref2va_patchin_hf102 | Scales the patch-projection high-frequency weights by 1.02. Its own card measures +1.3-1.9 % on a skin proxy and says "not a proven de-oil/de-wax model". 31.7 GB, on stock (not Singularity). |
| MiniMax-H3 x Z-Image "spatial detail graft" (joeygambino, SeaArt) | civarchive SeaArt page, 2026-08-22, 6 downloads | Stock ref2va, so it loses Singularity's duplicate fix. 40-series builds are GGUF only (slower). One preview image. |
| fl2va/ref2va hybrids (b25-49, r1024; sandpies, xtanqn, binglingzhimeng) | HF, 5-16k downloads | No quality claims or evidence ("experimental / subjective"). Stock-derived, so they lose Singularity. |
| T8 "Face Refine Parity" nodes | runcomfy page for T8mars/comfyui-minimax-h3-audio-T8 | Its parameter documentation is empty and the algorithm is unexplained. |
| Newer Singularity | HF API: last modified 2026-09-18, v1.3 int8 / w4a8 only | None exists. Round 1's statement still holds. |

## 5. Publishable (flag)

- §0a and §0b are generalizable, verifiable findings. The first is that ComfyUI's R2V node honours any canvas up to the
  768x1344 area, so square users are throwing away 43 % of the pixels. The second is that the ref2v 8-step schedule
  contract is contested (12/3 vs 6/3) and that `beta` is off the documented distillation grid.
- Measured in the bench, they make a short public note or issue (lightx2v discussion #51, ModelTC) and a row in the
  ref2va consumer-4090 benchmark already flagged in `BENCH_phase0.md` §10.

## Sources

- https://github.com/ModelTC/Minimax-H3-Turbo (README, COMFYUI_SETUP_AND_INFERENCE.md, example_workflows, inference_minimax_h3.py)
- https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions/51 · https://comfyui-wiki.com/en/news/2026-09-04-minimax-h3-turbo-ref2v-8step · https://comfyui-wiki.com/en/news/2026-08-07-minimax-h3-turbo-lightx2v
- vllm-project/vllm-omni `recipes/MiniMaxAI/MiniMax-H3.md` · niw/mmh3 `docs/ref2va.md` (via GitHub code search)
- https://docs.comfy.org/tutorials/video/minimax/minimax-h3 · https://docs.comfy.org/built-in-nodes/MiniMaxH3SigmaShift
- https://github.com/Carasibana/ComfyUI-H3-FaceRefine (README, issues) · https://github.com/Shrek3OnVH5/MiniMax-H3-NativeAudio-MusicVideo-Workflow
- https://huggingface.co/Comfy-Org/MiniMax-H3/discussions/30 · https://huggingface.co/Comfy-Org/MiniMax-H3/discussions/55
- https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora · https://huggingface.co/Momoking/MiniMax-H3-Turbo-Lora-ComfyUI · https://www.runninghub.ai/post/2104471397757386753/
- https://huggingface.co/fal/MiniMax-H3-Realism-People-LoRA · https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity
- https://ai-muninn.com/en/blog/minimax-h3-ltx-hybrid-refine-rtx5090 · https://ai-muninn.com/en/blog/minimax-h3-rtx5090-config-stack
- https://www.seedance.tv/blog/minimax-h3-fix-faces-at-a-distance · https://www.runcomfy.com/comfyui-workflows/minimax-h3-dual-sampling-workflow-ref2va-turbo-lora
- https://huggingface.co/t8star/minimax_h3_ref2va_patchin_hf102 · https://huggingface.co/sandpies/Minimax-H3-fl2va-ref2va-hybrid-unpruned-int8 · https://huggingface.co/xtanqn/MiniMax-H3-fl2va-ref2va-b25-49-r1024-r0
- https://github.com/ChenDarYen/ComfyUI-NAG · https://arxiv.org/pdf/2506.13355 (DicFace) · https://arxiv.org/pdf/2604.14560 (DVFace)
