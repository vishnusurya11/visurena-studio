# R2-P: a sharper, more textured storyboard panel without redrawing identity (2026-10-10)

Round-2 researcher P. The work was online research plus read-only inspection. No GPU was used, and no code, workflow or library file was changed.

What I read first:
- E §1-3
- G #2, #3 and Finding 3
- P2 §1-2
- S §1
- BENCH_phase0 §1 and §4
- `bench_evidence/restyle_d035_top_qwen_bottom_krea.jpg`
- the ep27 `storyboard/contact.png`
- `scripts/episode/grids.py`, `studio/storyboard_grid.py` and `scripts/episode/panels.py`
- `comfy_studio/workflows/image/image_qwen_image_2_1_{edit_multi,storyboard_3x3,t2i}.json`

**The constraint the arms are judged under:** H3 reads the panel at **768²**. `panels.py` takes a 1024 cell and LANCZOS-downscales it to `NATIVE`. Any detail finer than what 768 px can hold is thrown away before H3 sees it, so a 2x super-resolution of the panel buys nothing unless the panel is downscaled again afterwards.

The lever is therefore not more pixels. It is **mid-frequency material texture**, such as tweed weave, plaster, brick mortar, wood grain and mud, painted into the picture at a scale that survives at 768. Faces must stay the same pixels or the same person. The B1 Krea restyle lost on exactly that point: identity fell by 0.08 and it produced a mosaic.

## 0. Four free findings from the inspection (before any arm)

1. **The grid prompt asks for the flat, faceted look in so many words.**
   - `grids.py` `STYLE` (v1) says: "a flat angular stylised 3d CGI look ... broad simplified shapes, strong flat colour, high chroma, clean poster-like edges, NO photoreal skin or cloth".
   - The v2 line that ships says: "Drawn in the art style of <image2>: angular stylised 3D shapes, visible brush-stroke colour texture, flat high-chroma colour" (`ep27_grid_study_essay_1x1_s06.txt`).
   - The house Krea lead `refs_pack.STYLE_LEAD` also says "heavily angular 3d art style".
   - Krea2 with the Cinematic LoRA turns "angular" into painterly modelling. Qwen obeys words literally: the 09-20 docstring records that Qwen used a reference for content until told to use it for style. "Flat colour" and "simplified shapes" are therefore an instruction, and the B1 restyle amplified the same words into a mosaic.
   - This is the cheapest cause of E's "flat faceted faces, plain walls" that anyone has looked at.
2. **At cfg 1.0 the negative prompt does nothing.**
   - The Comfy docs for Qwen-Image 2.1 say: "CFG 1. At this value the negative prompt has no effect."
   - `grids.py` samples at `cfg=1.0` with `NEGATIVE = "... two men dressed alike, two men in the same hat, duplicated people ..."`. **The anti-duplicate negative has never been live.** The ep20 shot 05 duplicate man came out of a grid whose negative forbade it.
3. **ep27 shipped a seam into H3.**
   - `library/<wotw>/episodes/ep27/storyboard/h3/shot_10.png` has a full-height pure-white column at x=520 (column mean 254.9).
   - `h3/shot_16.png` has one at x=252 (column mean 255.0). It is also visible in `storyboard/contact.png`.
   - Qwen drew an in-picture split, the panel cutter or gutter guard did not catch it, and H3 copies the panel. This needs a CPU check: any panel column or row whose mean is at least 250 across 95 % of its length.
4. **Licence flag, not legal advice.** The Qwen-Image 2.1 weights carry the **Qwen Research License Agreement**, which "permits non-commercial research and evaluation; commercial use requires a separate licence" (model card, https://huggingface.co/Qwen/Qwen-Image-2.1).
   - Every 2.1 LoRA below inherits that question.
   - The Fix LoRA shows **no licence tag at all** on its Hugging Face repo.
   - This applies to the grids that already ship. It is for the owner and his attorney.

## 1. What the sources say about each lever

### 1a. Sampler, steps, cfg and shift for Qwen-Image 2.1
- **Official settings:** the model card uses 40 steps at **2048² native**, with aspect sizes 2400x1792, 2752x1536 and so on. It names no guidance argument (https://huggingface.co/Qwen/Qwen-Image-2.1).
- **Comfy templates** (https://docs.comfy.org/tutorials/image/qwen/qwen-image-2-1): 25 steps, cfg 1, euler/simple.
  - About 1 MP (1024²) is the baseline.
  - "Detail such as hands settles by about 30" steps.
  - **cfg 2 "follows dense prompts more closely but can over-sharpen edges"**, and cfg 5 "degrades quality badly".
  - The edit node's `resolution` is a per-reference pixel budget: 0 keeps the native size, and 1024 gives about 1 MP. We pass 1024, so a 3072x2048 sheet reaches Qwen at about 1 MP.
  - Shift is not documented. A community note for Qwen-Image 1 says that higher shift fixes blurry or dark output and lower shift adds detail. That is unverified for 2.1.
- **Our draw** is 25 steps, cfg 1, euler/simple, 1024 per cell and an encoder budget of 1024. That is the template exactly: under the official step count, at a quarter of native pixels per panel, and with guidance off.
- **The Fix LoRA's tuned recipe** (https://comfyui-wiki.com/en/news/2026-09-23-qwen-image-2-1-fix): 20 steps, **cfg 3**, sampler `seeds_2`, scheduler `sgm_uniform`, with **APG (1, 10, 0.3) + FreSca (1, 2, 8)** before the sampler and a negative prompt aimed at "gpt-image blotches, washed-out colours, AI slop, blur".
  - APG reins in the oversaturation and over-sharpening that cfg above 1 causes.
  - FreSca scales the guidance's high-frequency band, which is a direct texture lever.
  - **Both are native ComfyUI nodes and are present here:** `ComfyUI/comfy_extras/nodes_apg.py` and `nodes_fresca.py`.

### 1b. Detail and realism LoRAs for 2.1 (Qwen-Image 1 LoRAs do not transfer)
| LoRA | URL / file | Evidence | Fit for us |
|---|---|---|---|
| **Qwen-Image-2.1-Fix** (e-n-v-y) | https://huggingface.co/e-n-v-y/Qwen-Image-2.1-Fix, `qwen-image-2.1-fix-1.0-comfy.safetensors` 112 MB + `Qwen Edit 2.1 Optimal Settings.json.zip` | Low. 15 before/after pairs from a single author, 18k downloads a month, and early weights were re-issued. Users dispute whether the gain comes from the LoRA or from the APG/FreSca/negative settings. | Targets exactly "blotchy fine texture, flat washed colour". Its training data is unknown, so it may pull toward photographic. The settings can be tested without the LoRA (arm 2 vs 3). |
| **Restore LoRA** (ausboss) | https://huggingface.co/ausboss/Qwen-Image-2.1-Restore-LoRA, `qwen-image-2.1-restore.safetensors` 152 MB. Tiled workflow: https://civarchive.com/models/2988629 (AusBoss nodes >= 2.9.0) | Medium-low, from the author's own tests. Face match 0.79 -> 0.88 on 29 images. SSIM 0.578 -> 0.766. Corner drift 0.26 px against SeedVR2's 0.42. | An in-place redraw at about 2 MP, run on the **same Qwen UNET as the grids, so no model swap**. Author: "small faces (~100 px) can come back a slightly different person". Strength 0.75 lets "more of Qwen's own texture" through. Plain Qwen 2.1 without the LoRA "adds texture, gritty skin, older faces, shifts a few px". |
| Glamour Realism (civitai 2986100) | 45 AI portraits of women, strength 0.6 | anecdotal | Off-target: portrait-only and photographic. Rejected. |
| Elusarca Detail Enhancer (civitai 2956730) | trigger "enhance this image" | Lists its base as "Qwen 2". Author: "the base model can improve it just by prompting". Drift 2.07 px in ausboss's comparison. | Rejected: base unclear and worst drift. |
| Viggle turbo / Turbo8 (G #2) | see G | Vendor names **duplicated or ghosted figures** as the failure. | Speed only. Already deferred by S. |

**Duplicate-figure risk:** no 2.1 LoRA reports it except Viggle, which does report it. Every arm below re-runs `people_check` and G-CROWD.

### 1c. ControlNet tile and masked refine
- **No tile ControlNet exists for Qwen-Image 2.1.** Alibaba PAI's `Qwen-Image-2.1-Fun-Controlnet-Union` (7.5 GB) covers Canny, Depth, Grayscale, HED, Lineart, MLSD, Pose, Scribble and inpaint. Tile is not among them, and ComfyUI support was pending as Kijai PR #16519 at 2026-09-24 (https://comfyui-wiki.com/en/news/2026-09-24-qwen-image-2-1-fun-controlnet-union).
- The Restore LoRA is the 2.1 substitute for "tile at low denoise": it redraws in place at denoise 1, held by the LoRA rather than by a ControlNet.
- **Masked refine inverted for identity:** refine everything **except** the face boxes, then paste the original face pixels back with a feathered mask. This puts texture on cloth, walls and ground and costs zero identity. The bench already finds face boxes (the `face_flat` ruler reads "8x8 inside faces >= 64 px").

### 1d. SeedVR2 image mode on panels
- Installed (`custom_nodes/seedvr2_videoupscaler`, 3B weights present).
- It is fidelity-first: "flat fills and cel-shaded regions upscale cleanly ... aims for fidelity over stylization" (https://upsampler.com/blog/seedvr2-diffusion-upscaler). Over-sharpening shows as "plastic skin" (https://apatero.com/blog/seedvr2-removing-artifacts-complete-guide-2025). One user reports about 32 s for 1024 -> 2048.
- **For the panel it is the wrong tool.** It sharpens what Qwen drew, but it does not add the material texture that is missing, and its 2x output is LANCZOS-downscaled back to 768. Rejected for panels. G #5 already keeps it for sheets only.

### 1e. Qwen-Image-Edit "enhance" LoRAs
- There is no 2511 enhance or upscale LoRA. The nearest is `tlennon-ie/qwen-edit-skin`, which is for 2509 and is skin realism (https://huggingface.co/tlennon-ie/qwen-edit-skin).
- It is photographic, built for an older model, and pulls against the house look. Rejected.

### 1f. How practitioners prepare first frames for i2v and ref2v
- LTX's guidance is that a high-quality input image improves the output (https://docs.ltx.video/open-source-model/usage-guides/image-to-video). The first frame is the visual anchor, so its blur and artefacts carry into the clip.
- Recipes upscale with a learned model, resize to the model's **exact** working size with a high-quality downscale, and sharpen lightly or not at all, because halos get amplified over frames.
- Some add a small noise "so diffusion rebuilds micro-texture" (https://www.runcomfy.com/comfyui-workflows/easy-video-upscaler-for-footage-in-comfyui-hd-detail-restoration).
- **We already do the important part:** a supersampled 1024 cell is downscaled to exactly 768.
- The gap is upstream: the drawing has no material texture to keep.

### 1g. Prompt wording that makes Qwen draw texture
- Guides for Qwen 2512 and 2.0 (fal.ai and civitai/30826) say the model "rewards good prompting" and renders "natural material textures: surfaces, fabrics" when they are named.
- They say 1-3 sentences beat long term lists, and that a named light source beats "cinematic lighting".
- Name **materials and wear per surface** ("herringbone tweed with visible weave, cracked plaster, brick with mortar lines, wet rutted mud"), and drop "flat colour", "simplified shapes" and "poster-like edges".
- Keep the slot citation, "in the art style of <imageN>", because that is the measured lever for style (09-20).
- Evidence: medium for the direction, none measured on 2.1 stylised art.

## 2. Ranked top 5 bench arms

**Shots:** BENCH's S3, S4, S5 (ep20 T05, which has the duplicate) and S6, plus **two ep27 study panels** (shots 03 and 12, a medium-close face). The ep27 panels give the owner-bad side of the content-matched calibration pairs.

**Judging:**
- at 768 (`h3/`), because that is what H3 sees;
- with S's rules: **banding is the only calibrated ruler** (AUC 0.849), **texture is reported only and never votes**, because it voted for the mosaic;
- identity (the face similarity the bench already uses against `sheet_front`), `people_check` duplicates, `panel_content`, and the seam check from §0.3;
- then **one H3 take for the top 2 arms on S4 and S6**, because a panel win is not a take win. That is memory `a-fix-that-changes-nothing`.

The owner's eye on a contact sheet decides.

**Timing basis:** 4090 times are extrapolated, not measured. The base is the edit_multi manifest on a 4090 (1 ref about 25 s, 3 refs about 35 s, 5 refs about 90 s) and E's grid median of about 70 s per draw. An episode has about 25 panels in about 14 draws.

| Rank | Arm | What changes | 4090 s per panel (Δ per episode) | Identity risk | Duplicate risk | New workflow |
|---|---|---|---|---|---|---|
| **1** | **P-WORDS: texture wording, flatness words out** | v3 grid prompt: keep `<imageN>` style citation; drop "flat / simplified / poster-like / angular"; add one sentence naming each visible surface's material + wear + a named light source (from `setups[].described` / `light`) | **+0** (same graph) | low: slots and cast clauses untouched | neutral | **none**: a `--prompt=v3` in `grids.py` (code change, test-first). Template stays `image_qwen_image_2_1_edit_multi` |
| **2** | **P-GUIDE: cfg 2.5 + APG + FreSca, negative made live** | Same graph + `APG(1,10,0.3)` + `FreSca(1,2,8)` on the model; cfg 2.5 (sweep 2 / 3); steps 25 -> 30 (hands settle ~30). Sub-arm 2b: sampler `seeds_2`/`sgm_uniform` vs euler/simple | about **2x** per step (two passes): about 35-50 s amortised (**+12-18 min**) | low-medium: cfg 2 "over-sharpens edges" (Comfy); APG is there to stop it | **may FALL**: the anti-duplicate negative becomes live for the first time | `image_qwen_image_2_1_edit_multi_apgfresca_comfyorg.json` |
| **3** | **P-RESTORE-MASKED: same-UNET restore refine, faces kept** | After the grid, per cell: upscale 1024 -> about 1.4 MP, Restore LoRA @0.75, 25 steps (or 8 with Viggle turbo), cfg 1, encoder `resolution` 0; then **composite the ORIGINAL face boxes back** (feathered) and LANCZOS to 768. Unmasked variant 3b for comparison | about **15 s** (turbo) / **about 40 s** (25 steps) (**+6-17 min**); no model swap (same `qwen_image_2.1_int8_convrot`) | **masked: about 0**; unmasked: real for faces under about 100 px, which is every wide/medium cell | low (in-place; text and small objects may be re-spelled or shifted a few px) | `image_qwen_image_2_1_panel_refine_masked_ausboss.json` (+ needs AusBoss nodes >= 2.9.0 only for the tiled variant; a single-pass graph needs none) |
| **4** | **P-FIX: Fix LoRA on top of arm 2** | e-n-v-y Fix LoRA 1.0 via `LoraLoaderModelOnly`, its 20-step `seeds_2`/`sgm_uniform` cfg 3 APG/FreSca recipe and its negative | as arm 2, about 35-45 s (**+12-16 min**) | medium: unknown training set; may pull toward photographic, away from the house look | unknown, measure | `image_qwen_image_2_1_edit_multi_fix_envy.json` |
| **5** | **P-NATIVE: one panel per draw at 1536²** | 1x1 grids for every shot, `width=height=1536`, chained on the setup's anchor/room picture exactly as 1x1 grids are today; still LANCZOS to 768 | about 60-90 s (**+10-22 min** over today's 15-90 min of grids) | neutral | **lower in theory** (one picture, one cast clause, no neighbour cell to borrow from) but unmeasured: run P2's **R0c CPU layout check first** (duplicates and panel faults by layout across ep05-27) | **none**: same template, size inject. 2048² as sub-arm only if 1536 wins (about 4x the pixels of a 1024 cell) |

### Why this order
- **1 first.** It is free, it is the only arm aimed at the written cause, and it can run with every other arm. If the words alone remove the facets, arms 2-5 compete for a smaller gap. Risk: memory `walls-follow-the-chapter`, because material words drawn from a quiet interior chapter may over-texture a night sky. Read the panels across the 4+2 shot mix.
- **2 next.** It needs no download, and both nodes are native. It is the only lever that also attacks the **duplicate-figure** fault, through the live negative. Its cost is grid time, which is cheap next to takes. Risk: the over-sharpening named in the Comfy docs. That is why APG is included and banding is the vote.
- **3** is the identity-safe answer to E's "H3 copies the panel". It adds texture after the composition and the cast are already fixed, and the face-paste makes the B1 failure mode (faces redrawn) impossible by construction. It ranks below 1-2 because it is a new step with a face-box dependency and a mask seam to inspect.
- **4** is arm 2 plus an unlicensed single-author LoRA. Run it only to split "settings vs LoRA", which the Fix LoRA's own users dispute.
- **5** costs the most and touches the 09-28 one-room ruling. A grid holds the room in one denoise. Separate draws hold it only through the staged room or anchor picture, which the ruling already accepts for chained grids, but 25 separate re-imaginings of a room have not been measured. Run it only if R0c shows that 2x2 cells carry the duplicates and faults.

### Ranked below the top 5 (and why)
| Candidate | Why not |
|---|---|
| Krea2 img2img restyle at 0.25-0.35 | It lost in BENCH §4: mosaic, content loss, identity -0.08. It also sends the "angular" words through a second model. |
| SeedVR2 (3B/7B) image mode on panels | Fidelity-first and adds no material texture; its 2x is downscaled back to 768 anyway. Keep it for sheets (G #5). |
| RTX VSR `DEBLUR_*` at scale 1 on the panel | It takes seconds and carries zero identity risk, but deblurs a picture that is not blurred (a supersampled 1024 -> 768). It is worth one line in the bench as a **control**, not as an arm. |
| ControlNet tile at low denoise | No tile ControlNet exists for Qwen 2.1. A cross-model tile pass (SDXL/Flux) would restyle, as Krea did. |
| Qwen-Edit 2509/2511 skin or "enhance" LoRAs | Built for an older model, photographic, and pull against the stylised house look. |
| Encoder `resolution` 1024 -> 1536/0 (references reach Qwen at higher res) | Already measured 09-20: "raising the encoder to 1536 and the sampler to 40 steps ... bought very little for the extra time" (`storyboard_grid.style_clause`). |
| Viggle / Turbo8 grid turbo | Speed only, and its vendor names duplicates as the failure (G #2, S deferred). |

## 3. Cost of the bench (estimate)
- **Arms:** 6 panels x (1 + 2a/2b + 3 + 3b + 4 + 5) is about 42 Qwen draws or refines, roughly 25-35 min.
- **Takes:** 4 H3 takes for the top 2 arms on S4 and S6, roughly 10-14 min.
- **Swaps:** one Qwen load. No Krea swap.
- **Downloads:** Restore LoRA 152 MB and Fix LoRA 112 MB. Both are local, with $0 spend.

## Sources
- https://huggingface.co/Qwen/Qwen-Image-2.1 (steps, native sizes, licence)
- https://docs.comfy.org/tutorials/image/qwen/qwen-image-2-1 (cfg 1 makes the negative inert, cfg 2 over-sharpens, steps ~30 for hands, encoder `resolution`)
- https://comfyui-wiki.com/en/news/2026-09-23-qwen-image-2-1-fix and https://huggingface.co/e-n-v-y/Qwen-Image-2.1-Fix
- https://huggingface.co/ausboss/Qwen-Image-2.1-Restore-LoRA, https://civitai.com/models/2989697, https://civarchive.com/models/2988629/qwen-image-21-tiled-upscale
- https://comfyui-wiki.com/en/news/2026-09-24-qwen-image-2-1-fun-controlnet-union
- https://upsampler.com/blog/seedvr2-diffusion-upscaler, https://apatero.com/blog/seedvr2-removing-artifacts-complete-guide-2025
- https://huggingface.co/tlennon-ie/qwen-edit-skin
- https://docs.ltx.video/open-source-model/usage-guides/image-to-video, https://www.runcomfy.com/comfyui-workflows/easy-video-upscaler-for-footage-in-comfyui-hd-detail-restoration
- https://fal.ai/learn/devs/qwen-image-2512-text-to-image-prompt-guide, https://civitai.com/articles/30826
- civitai 2986100 (Glamour Realism), 2956730 (Elusarca Detail Enhancer)

## Caveats
- Every 4090 time above is extrapolated from the 4090 edit_multi manifest, E's grid medians and the ausboss 5090 timings. None is measured.
- The Qwen-Image 2.1 ecosystem is three weeks old. Every LoRA here comes from a single author and reports its own metrics.
- Per memory `gates-are-not-quality`, the owner's eye on content-matched panels is the judge. The texture ruler must not be promoted to a vote.
