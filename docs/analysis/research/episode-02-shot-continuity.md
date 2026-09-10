# Episode shot continuity — one scene, 10–15 shots, 9:16, one 4090

Research, 2026-09-10. Question: how to keep the same room, positions, wardrobe
and light across 10–15 locally rendered shots of one scene, and how to cut the
seconds per shot. Every number below is tagged **measured here** (this box, the
repo's own ledgers/logs), **reported** (a cited third party), or **expected**
(arithmetic, not yet run). Nothing was rendered for this document.

## 0. The brick

A shot has two continuities and they are held by two different mechanisms:

- **Identity** (who) is held by a *reference* — H3's `<Picture N>` blocks,
  measured in this repo to hold a face "hard and unmistakably"
  (`.claude/skills/trailer/SKILL.md` §"Observed on the first bound run").
- **Space** (where, which pose, which light) is held by a *pixel anchor* — a
  first frame, a last frame, or the previous clip's tail. A reference cannot do
  this: the location ref was measured to be "blended", a palette not a set
  (same section), and `MiniMaxH3ReferenceToVideo` carries no frame index for a
  reference (`nodes_minimax_h3.py:241-356`; the refvideo manifest says it
  outright: "reference blocks carry no frame index and no positional
  embedding").

So continuity is generated at the **image** level (one master frame, each
shot's start frame derived from it), and the video model is asked only to
animate a frame it was handed, with the cast refs riding along for identity.
Everything in §5 follows from that.

## 1. What H3 is on this box (read before comparing anything)

- Model: **MiniMax-H3**, 33 B omni-modal video+audio DiT, open weights
  2026-08-03, two checkpoints: `fl2va` (t2v / first / last / first+last frame)
  and `ref2va` (up to 9 ref images, 3 ref videos, 3 ref audios)
  ([comfyui-wiki open-weights](https://comfyui-wiki.com/en/news/2026-08-03-minimax-h3-open-weights-comfyui)).
  Native ComfyUI nodes: `comfy_extras/nodes_minimax_h3.py`
  (`MiniMaxH3ImageToVideo` = fl2va with optional `first_frame`/`last_frame`;
  `MiniMaxH3AddGuide` = anchor an image **or a 5/22/39… frame clip** at any
  `frame_idx`, chainable; `MiniMaxH3ReferenceToVideo` = ref2va).
- Constants (`studio/h3.py`): 24 fps fixed; `frames % 17 == 5`; short edge
  forced to 768; pixel cap 768×1344; canvas multiple 32. **9:16 native canvas
  is exactly 768×1344** — `adapt_canvas(768, 1344)` is a fixed point (area =
  cap, no rescale). The i2v start frame is resized with `crop="disabled"` = a
  stretch (`nodes_minimax_h3.py:145`), so the start frame must be 768×1344.
- Installed weights (`ComfyUI/models/diffusion_models/`): both bases in bf16,
  int8-convrot, pruned-bf16, pruned-fp8 (`minimax_h3_{fl2va,ref2va}_pruned_fp8_scaled.safetensors`, 21 GB each);
  TE `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (15.7 GB); video VAE
  5.2 GB, audio VAE 0.6 GB. LoRAs in `models/loras/minimax_h3/`: fl2v turbo
  4-step v1.0/v1.1/v1.2 768p, fl2v turbo 8-step v1.0, ref2v turbo 4-step
  v0.1, **ref2v turbo 8-step v1.0 768p**, ckpt850/v4 community turbos,
  Ref2VA-Acc-8Step.
- Workflows (`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\video\`):
  `video_minimax_h3_r2v_turbo` (production, `scripts/trailer/build_clips.py:67`),
  `video_minimax_h3_i2v_turbo` (start frame), **`video_minimax_h3_flf_turbo`**
  (start + end frame, sigma shift node, built for exactly this chaining and
  never run), `video_minimax_h3_r2v_turbo_lxref` (ref2v 8-step LoRA),
  `video_minimax_h3_r2v_turbo_refvideo` (ref clip as blocking hint).
- Production take: ref2va pruned fp8 + ckpt850 EMA turbo @0.8, euler/beta,
  **8 steps**, 1344×768, `ref_image_size: "max"` (`build_clips.py:139`), two
  ref slots (char, loc). `sage_attention` is an inject point but
  `build_clips.take_values` does not set it and the manifest default is
  `"disabled"` (`video_minimax_h3_r2v_turbo.manifest.json`) — so **Sage is OFF
  in production** despite the manifest prose saying "SageAttention ON".
- Measured cycle (run 18, `learnings.jsonl` gate=`cycle`, model resident,
  `subskills/04-shots/SKILL.md`): 124 f = 336–352 s, 175 f = 482–497 s,
  192 f = 542 s, 243 f = 743 s, 362 f = 1319 s; ≈ 2.49 s/frame + 79 s.
  Cold first take of a round: 532 s at 90 f (261 s of load).
- The 2.6 s **reference leak** (`HEAD_TRIM`): the r2v path opens on the
  reference sheet for ~2.1 s before entering the scene, so every r2v take
  pays ~77 frames (`04-shots/SKILL.md` §"A take costs 77 frames"). That is a
  property of ref2va with no keyframe; an i2v/FLF take opens on the pinned
  frame (expected, not yet measured on this box).

### The model swap, measured from ComfyUI's own log

`ComfyUI/user/comfyui.prev2.log`, 2026-09-05 (H3 r2v takes, same settings):

| event | wall | what it is |
|---|---|---|
| 22:19:27 TE requested → 22:21:27 DiT requested | 120 s | Qwen3-VL-32B nvfp4 load + encode |
| 22:21:27 DiT requested → 22:26:45 audio VAE | 318 s | DiT load **+** sampling |
| 22:27:47 first take total | **527 s** | cold |
| 22:32:32 / 22:43:49 / 22:48:50 next takes | **280 / 289 / 299 s** | warm, model resident |
| 23:02:08 → 23:14:44 after a `/free` | **757 s** | the same take + reload (TE 118 s, DiT ~5 min) |
| 23:19:03 → 23:28:12, 23:32:33 → 23:41:35 | 551 / 543 s | reload again, again |

Reload = 250–470 s on top of a ~260–300 s take. It is **disk-bound**:
every model file lives on `D:`, and `D:` is physical disk 0 = `WDC WD40EZAZ`,
a 5400-rpm HDD (PowerShell `Get-Partition`/`Get-Disk`); 21 GB DiT + 15.7 GB TE
at HDD speed is ~5–6 min. `C:` is the `WD_BLACK SN850X` NVMe with 313 GB free
(`df`). The retrospect's "8.3 of 15.76 min was model swap"
(`docs/analysis/research/trailer-render-cycle.md`) is this, and it is already
fixed *in policy* by the round-based step 07 (one `/free` per round) — but any
future pipeline that interleaves a VLM read, an image edit, or another video
model between H3 takes pays it again unless the weights move to NVMe.

## 2. Comparison table

Seconds are for **one ~5 s shot at 9:16** on this 4090 unless noted. "Identity"
= does the face survive; "Space" = does the room/pose/light survive a cut.

| approach | identity hold | space hold | VRAM (24 GB) | s per 5 s shot | installed here | evidence |
|---|---|---|---|---|---|---|
| **H3 ref2va + cast refs** (production) | strong on char; loc ref *blended* | none across shots (each take re-invents the set) | fits, fp8 DiT 21 GB; TE swapped | **336–352 s** at 124 f (measured, resident), +77 f leak tax | yes, production | `04-shots/SKILL.md`; run 18 rows |
| **H3 fl2va i2v** (start frame pinned) | inherited from the start frame; decays with motion | strong at t=0, drifts by t=5 s | same as above | 1152×640×243 f: **334 s** measured (`benchmarks/minimax_h3/h3_ltx_rtx/README.md`); 768×1344×124 f: expected 200–260 s (2.49 s/f w/o refs, minus leak) | workflow yes, never run in the trailer | manifest `video_minimax_h3_i2v_turbo` |
| **H3 fl2va FLF** (start + end frame) | as i2v | **strongest**: both ends pinned, next shot starts where this ends | same | as i2v + one keyframe encode (expected) | workflow `video_minimax_h3_flf_turbo` built 2026-08, **never run** | manifest text; `nodes_minimax_h3.py:148-152` (last frame is cover-cropped, first is stretched) |
| **H3 ref2va + AddGuide(frame 0 = start frame)** — refs for identity, pixel anchor for space | strong (refs) | strong at t=0 | same | as r2v (refs ride every step) | node exists in core; no workflow | `nodes_minimax_h3.py:164-238`; the H3-Motion-Context pack chains latents on the ref2va node and "preserves existing reference blocks" ([repo](https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context)) — evidence ref2va accepts anchors; **unmeasured** |
| **H3 tail-latent chaining** (Motion Context / Herrgotts suite) | as previous clip | seamless motion+audio across the join; 22-frame pinned head trimmed (0.92 s/clip) | same | as i2v | **not installed** | [Motion Context](https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context), [Herrgotts](https://comfyui-wiki.com/en/news/2026-08-11-h3-infinite-continuation-suite); caveat: "losses compound like photocopying a photocopy… restart the chain on scene cuts"; turbo LoRAs "soften picture detail" |
| **H3 RefMods** (the 09-07 item) | claimed: identity injected at conditioning level, no "bleeding" of ref aesthetics into the set | none | +~1 MB | as i2v (no live ref encode) | **not installed**; needs `ComfyUI-MiniMaxH3Mod` | [comfyui-wiki 2026-09-07](https://comfyui-wiki.com/en/news/2026-09-07-minimax-h3-refmods), [GitHub](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod), [HF](https://huggingface.co/malcolmrey/minimaxh3). **No measured numbers anywhere; 5 days old** |
| **H3 subject LoRA** (fal trainers t2v/i2v/flf/ref2va) | strong if trained; ~2.5 h cloud per LoRA | none | +LoRA | as i2v | trainer is hosted (paid); output `.safetensors` | [fal guide 2026-08-10](https://fal.ai/learn/devs/how-to-train-a-lora-for-minimax-h3); guide is about *style*, silent on identity |
| **LTX-2.5 22B distilled i2v / flf2v** | from the frame only | flf2v: both ends pinned (`first_strength`/`last_strength` 0.7) | 22.67 GiB all-in ([reported](https://runaihome.com/blog/ltx-2-5-local-ai-video-hardware-guide-2026/)); 10 s clips stall at VAE decode | **i2v 225 s, flf2v 270 s median** at 1280×704 5 s; 8 s = 267 s (measured, 110 clips, `comfy_studio/benchmarks/ltx25/TIMINGS.md`) | yes: int8 transformer, gemma4 int8, VAEs; workflows `video_ltx25_{i2v,flf2v}` | portrait **unmeasured** here |
| **LTX-2.3 Ingredients IC-LoRA** (one composite ref sheet) | multi-element sheet; reports of multi-character refs "all become invalid" until wired as in-context | optional first frame | dev/distilled fp8 22B | trained bucket 768×448×121 f, 30 steps on dev; unmeasured | LoRA + workflow `video_ltx23_ingredients` present | [HF card](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients), [issue #3](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients/discussions/3) |
| **Wan 2.2 I2V-A14B fp8 + lightx2v 4-step** | from frame | i2v: start only; **FLF2V** native template pins both | 2×14 GB fp8 experts, loaded in turn; 81 f 720p fits | **reported ~3 min** with Lightning, 26 min without, 720p on a 4090 ([stable-diffusion-art](https://stable-diffusion-art.com/wan-2-2-first-last-frame-video/)); 480×832 faster | weights + 4-step LoRAs + KJ wrapper installed; **no comfy_studio workflow**; unmeasured here | [Wan 2.2 FLF2V template](https://comfy.org/workflows/video_wan2_2_14B_flf2v-7016f027bcf1/) |
| **Wan 2.2 + SVI 2.0 Pro / wan22fmlf** (anchor + motion latents, first-middle-last) | anchor frame keeps pulling back to identity | multi-frame pins; "biased towards less motion because of the anchor" | as Wan | as Wan | `ComfyUI-Wan-SVI2Pro-FLF`, `wan22fmlf` installed, no SVI LoRA seen | [SVI 2.0 Pro](https://wanx-troopers.github.io/svi.html); wan22fmlf README: use 704×1280, **720×1280 flickers mid-frames** |
| **Wan 2.2 Animate** | replacement of a person in a *driving video* | inherits the driving video | 14B fp8 | n/a for shot generation | weights installed (`models/diffusion_models/wan/`) | needs a driving clip — a motion-transfer tool, not a shot generator |
| **Wan2.2-VACE-Fun-A14B / Phantom / MAGREF** (ref-to-video on Wan) | ref-conditioned; Phantom "noticeable facial inconsistencies", MAGREF "abrupt brightness" per [Wan-Animate paper](https://arxiv.org/pdf/2509.14055) | none across shots | 14B class | unmeasured | **none installed**; Phantom/MAGREF are Wan 2.1-era | [VACE-Fun](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B), [MAGREF](https://arxiv.org/html/2505.23742) |
| **Qwen-Image-Edit 2511** (start-frame edits) | "notably better" character/multi-person consistency (official) | edits one image → same set by construction | 20 GB fp8; loads beside nothing else | **16 s** per edit warm, 67–76 s cold (measured, `benchmarks/results/image_qwen_image_edit_2511_two_images__…/report.json`) | yes; workflows `image_qwen_image_edit_2511_{single_image,two_images}` | [Comfy blog](https://blog.comfy.org/p/qwen-image-edit-2511-and-qwen-image), [storyboard workflow](https://civitai.com/models/2293093/qwen-image-edit-2511-continuous-storyboard-generation) |
| **FLUX.2 Klein 9B + Consistency LoRA** (up to 5 refs) | community LoRA "cuts drift in the parts you did not ask to change" | same | 9.4 GB fp8 | unmeasured | `flux-2-klein-9b-fp8` + `Flux2-Klein-9B-consistency-V2` installed; no workflow | [Civitai](https://civitai.com/articles/27410/flux2-klein-9b-consistency-lora) |
| Nano Banana / FLUX Kontext | — | — | — | — | **not local** (Higgsfield/Gemini; Kontext not installed) | paid fallback only |

## 3. Findings by question

### (a) First–last-frame chaining

- H3 has three native ways to pin space, all in core, none yet exercised by
  the trailer: `first_frame`/`last_frame` on `MiniMaxH3ImageToVideo`;
  `MiniMaxH3AddGuide` at any `frame_idx`, including a **multi-frame clip**
  (5/22/39… frames) — i.e. the last 22 frames of shot N anchored at frame 0
  of shot N+1, then trimmed, without a custom node; and the two community
  packs that do the same on the *latent* so audio and motion continue.
- The community's measured cost of latent chaining: 22 frames (0.92 s) lost
  per clip to the pinned head; audio "top end goes first"; picture loss
  "minimal by comparison"; restart the chain at every scene cut.
- The last-frame pin is a **cover-crop**, the first-frame pin a **stretch**
  (`nodes_minimax_h3.py:145,150`) — both keyframes must be exactly 768×1344.
- Wan 2.2 FLF2V (native template) and LTX-2.5 flf2v both exist and both are
  cheaper per shot than H3 on this box (LTX-2.5 flf2v 270 s measured; Wan
  ~3 min reported) — but they carry **no identity reference**; the face is
  whatever the two frames say, and a 14B/22B model interpolating between two
  stills of the same person is the best case for those models, not the
  general case. The SVI/FLF node README is honest: "shouldn't work but kind
  of works if the subject is in about the same spatial position".
- Drift over a chain is real for every model: the Stable-Video-Infinity
  thread reports "exposure and contrast increasing with each 81 frames step
  as well as loss of character consistency" for naive i2v extension
  ([issue #51](https://github.com/vita-epfl/Stable-Video-Infinity/issues/51)).
  **A chain of N hops needs a check between hops, and the master frame, not
  the previous shot, must be the anchor of record** (§5).

### (b) Reference / multi-reference identity

- H3 refs are the only identity mechanism this repo has measured, and it
  measured them working: face held hard, location blended, a third face by
  prompt only came back "a different clean-shaven man each time"
  (`trailer-retrospect.md` run 6b). Two-subject binding
  (`scripts/trailer/two_subject_ab.py`) is built and **unmeasured**.
- The ref2v **8-step 768p LoRA** (lightx2v, 2026-09-04) is installed and is
  the matched-family turbo for ref2va; the production ckpt850 is an fl2v-
  lineage LoRA on the ref2va base whose author "has not validated r2v
  quality". `scripts/trailer/lora_ab.py` is the controlled A/B, unrun.
- **RefMods (2026-09-07)**: "pre-encoded conditioning-level adapters",
  1–1.6 MB, extracted in one pass from identity thumbnails, applied between
  the conditioning loaders and the guider; claim: identity without the live
  VAE reference encode and without the reference's *aesthetics bleeding into
  the scene* — which is precisely the "location blended / grey sheet leak"
  defect measured here. Author malcolmrey; node pack MIT; **zero published
  measurements**. Worth one probe, not a redesign.
- H3 **turnaround LoRA** ([matlod](https://huggingface.co/matlod/minimax-h3-turnaround)):
  five rotated views of a subject from one reference in one pass on the
  ref2va base — a cheaper way to make the multi-angle character sheet than
  Ideogram boxes (measured 2:56 each). "Cannot be stacked with video
  generation". Optional.
- Wan-family references (Phantom, MAGREF, VACE-Fun) are a second model
  family, second text encoder, second set of sheets — and the Wan-Animate
  paper's own comparison shows facial inconsistency (Phantom) and brightness
  jumps (MAGREF). Nothing installed. Not recommended while H3 refs work.
- LTX-2.3 Ingredients: one composite sheet, trained at 768×448×121 f on the
  **dev** model at 30 steps; the HF thread shows the multi-reference failure
  was a wiring error (sheet fed as first frame instead of in-context) and
  that "both characters render", identity "requires further measurement".
  A 30-step dev pass at 22B is not a cheap shot.

### (c) The Hailuo/MiniMax news of 2026-09-07/08

Nothing from MiniMax itself on those dates. The comfyui-wiki news index for
that week ([list](https://comfyui-wiki.com/en/news)) is what surfaced:

| date (URL) | item | relevance |
|---|---|---|
| 09-07 | **MiniMax H3 RefMods** — 1 MB conditioning adapters "for character consistency across generations" | the "Ref2V LoRA" the owner saw; §3b |
| 09-07 | H3 Singularity — fused/pruned fine-tune of ref + fl + b25-49 into one int8 checkpoint (19.6 GB), "restores distant faces", pairs with ref2v 4-step LoRA | one checkpoint for both i2v and r2v = **no fl2va↔ref2va swap**; unmeasured |
| 09-08 | H3 block-sparse attention node + Comfy memory compiler in core (PR #16072, #15861) | speed, §4 |
| 09-06 | FL2V Turbo LoRA v1.2 (installed) | audio cleaner; "potential visual trade-offs vs v1.1" |
| 09-04 | Ref2VA Turbo 8-step 768p (installed) | §3b |
| 09-04 | MiniMaxH3-CLIPCached — conditioning 29.9 s → 1.1 s on cache hit, TE unloaded (frees ~14.6 GB) | speed, §4 |
| 09-04 | VDN-H3 | t2v only, no refs, US-excluded — n/a (already noted in `04-shots/SKILL.md`) |

fal's hosted H3 LoRA trainers (t2v/i2v/flf/ref2va) are 2026-08-10/11
([VP Land](https://www.vp-land.com/stories/fal-adds-lora-training-for-minimax-h3-starting-with-an-open-source-realism-people-lora)),
not September. Hosted Hailuo "Subject Reference" (S2V-01) is 2025 and is
the paid ancestor of ref2va. Higgsfield's catalog (checked via
`models_explore`) lists `minimax_h3` with `image_references` + start/end
frame at 9:16 — a paid escape hatch, not a local answer.

### (d) Image-level continuity, then i2v

This is the recommendation. Evidence that it is the right layer:

- Qwen-Image-Edit 2511 is measured here at **16 s** per edit and the official
  release notes list "notably better consistency" and multi-person identity;
  a community "continuous storyboard" workflow does exactly one-prompt-per-
  shot from one base image.
- The existing `image_qwen_image_edit_2511_two_images` workflow is the
  compositor: image 1 = location plate, image 2 = character sheet, prompt =
  "place the person from image 2 into image 1 …" (its own manifest example).
- An 8 s clip is 22× the cost of the still it came from (`ltx25/TIMINGS.md`:
  "always worth rendering a plate twice and picking"); at 16 s per edit, five
  candidate start frames per shot cost 80 s against a 300 s take.
- The same doc's Moby-Dick retro: 36 % of shots needed a re-render. Checking
  the *start frame* before the take moves most of that fix pass to the
  16-second stage.
- FLUX.2 Klein 9B + consistency LoRA is the installed alternative editor (5
  refs); no workflow, unmeasured. Keep as the B option if Qwen-Edit drifts
  wardrobe.

### (e) 9:16 specifics

| model | native vertical | note |
|---|---|---|
| H3 | **768×1344** (fixed point of `adapt_canvas`; = pixel cap) | render native; a 16:9→9:16 crop keeps 432×768 of 1344×768 = 32 % of the pixels. Every frame handed to i2v/FLF must already be 768×1344 (stretch/crop otherwise) |
| Wan 2.2 A14B | 480×832, **704×1280** | wan22fmlf README: 720×1280 causes mid-frame flicker; official card lists 720×1280 |
| LTX-2.3 | trained 9:16; 736×1280 or 768×1280 practical on 24 GB; 1088×1920 "5090 or better" | [LTX portrait guide](https://ltx.io/blog/ltx-2-3-portrait-video), [WaveSpeed](https://wavespeed.ai/blog/posts/ltx-2-3-portrait-video-9-16-workflow-2026/) |
| LTX-2.5 | 704×1280 (same pixel count as the measured 1280×704, so the same ~225 s expected) | portrait unmeasured here |
| Qwen-Edit 2511 | any; output the master at 768×1344 and never resize after | — |

Render vertical natively everywhere; no model above gains from a landscape
render cropped down. (H3's own 1344×768 "does not work reliably here" note in
`h3_ltx_rtx/README.md` is stale: run 18 timed 22 takes at 1344×768.)

## 4. Cutting the seconds per shot on this 4090

Ordered by measured or best-evidenced size of the win.

| lever | now | after | evidence |
|---|---|---|---|
| **No `/free` between takes; one VLM session per round** | done in step 07 (`ladder.Climb`, `render-cycle.md`) | keep. Any new pipeline stage must obey it | log: 527–757 s reload takes vs 256–300 s warm (§1) |
| **Move H3 weights to NVMe** (`C:`, 313 GB free): fl2va fp8 21 GB, ref2va fp8 21 GB, TE 15.7 GB, VAEs 5.8 GB ≈ 64 GB | D: HDD; TE load 118–120 s, DiT ~5 min | expected < 30 s per model (NVMe ≥ 3 GB/s) | `Get-Disk`: D: = WD40EZAZ HDD; log timestamps. Memory note "moving it to NVMe are user-side" — do it |
| **i2v/FLF instead of r2v for the shots** | 77-frame leak tax + refs at `"max"` riding every step (node tooltip: "'max' can be several times slower") | 124 f per 5 s shot instead of 192 f: run 18 says **542 s → 336–352 s** for the frame drop alone; the ref-token cost is on top | `04-shots/SKILL.md`; `nodes_minimax_h3.py:265-266` |
| **Fixed cost per take, not steps** | 192 f at 4 steps 630 s vs 8 steps 720 s — steps are 13 % of the take | attack the intercept: TE encode (~30 s reported on a 5080; CLIPCached), VAE decode, ref encode | `benchmarks/results/…lxref-cost-curve-6…/report.json` |
| **SageAttention actually on** | `sage_attention: "disabled"` default, not injected | reported 1.5–2× on attention on a 4090, "2–4×" on long video sequences; H3 delta **unmeasured here** | [ComfyUI-Attention-Optimizer](https://github.com/D-Ogi/ComfyUI-Attention-Optimizer); sageattention 2.2.0 + triton 3.5 installed |
| **Block-sparse attention node + Comfy compiler** (core, 09-08) | not used | reported 43 s/step for 720p×158 f on a **5060**; 4090 unmeasured; OOM interaction with the compiler, fallback `--disable-comfy-compiler` | [comfyui-wiki 09-08](https://comfyui-wiki.com/en/news/2026-09-08-h3-sparse-attention-compiler); local ComfyUI is v0.35.0 (2026-09-09), so it should be present |
| **CLIPCached** for rerolls | each reroll re-encodes | same prompt + same pixels = 1 s instead of ~30 s, and the TE is unloaded on a hit | [node](https://github.com/Mu5hr00moO/ComfyUI-MiniMaxH3-CLIPCached); Ref2VA "fixed reference slots" caveat |
| **Shorter shots + handle only** | `take_seconds = shot + 2.6 + 0.25` | with i2v the 2.6 s goes to ~0 (expected): 3 s shot = 90 f | `build_clips.take_seconds` |
| **8 → 4 steps** (v1.2 fl2v 4-step, shift 6/3) | 8 | only 13 % on the cost curve; the repo's own objection (last Euler step σ 0.72→0) stands; use for inserts only | `render-cycle.md` §4 |
| **Resolution 768×1344 → 640×1152 + upscale** | 1.03 MP | 0.74 MP measured 334 s at 243 f (i2v); upscale route estimated ~3 min extra, never run | `h3_ltx_rtx/README.md` |
| Two shots in one generation | one take, one shot | free second setup inside a take (631 vs 690 s measured) — legal here because an episode wants *continuity*, and the trailer's reuse objection was about replaying frames | `SKILL.md` §"The free win not taken" |
| LTX-2.5 for shots without a face | — | 225 s i2v / 270 s flf2v measured; length nearly free (155 + 14 s/s) | `ltx25/TIMINGS.md` |

Expected per-shot budget after the first four rows, i2v 768×1344×124 f, 8
steps, H3 resident on NVMe: **~4–5 min** (2.49 s/f ≈ 309 s minus the ref
overhead, plus 16 s × candidates for the start frame). Not measured — the
probe in §6 measures it.

## 5. Recommended protocol — one scene, 10–15 shots

**Generated once per scene (image stage, all cheap):**

1. Cast sheets — already in `library/<book>/refs/` (shared across trailer,
   song, episode by rule).
2. Location plate at 768×1344 (Krea 2, 27 s median measured) — verified
   empty by a read, since plates "come back populated".
3. **MASTER frame** `M`: Qwen-Edit 2511 two-image composite (plate + lead
   sheet) at 768×1344, seed-varied ×5, pick by the metrics in step 6. `M`
   fixes wardrobe, light direction, furniture, the lead's position. `M` is
   the anchor of record for every shot; nothing downstream replaces it.
4. Per shot k: **start frame `S_k`** = Qwen-Edit 2511 single-image edit of
   `M` (camera/blocking instruction: "the same room and light; the camera is
   now over his shoulder…") — 16 s each, ×3 candidates. For a *continuation*
   shot (k follows k−1 without a time skip) edit from `M` **and** hand the
   previous take's last frame as image 2, so pose continues; never edit from
   the previous edit alone (chain drift, §3a).

**Per shot (video stage):**

5. H3 fl2va **FLF** when `S_{k+1}` exists (start = `S_k`, end = `S_{k+1}`;
   the cut lands on a frame both shots own); H3 **i2v** for the last shot and
   for any shot whose successor is a time skip. Cast refs: run the A/B in §6
   to decide between (i) plain fl2va, (ii) ref2va + `AddGuide(frame 0 = S_k)`,
   (iii) RefMods. Frames = `legal_frames(24 × (shot + 0.25))`; no 2.6 s tax
   unless the probe measures a leak on i2v.
6. Steps 8, LoRA matched to the base (fl2v 8-step v1.0 on fl2va; ref2v 8-step
   v1.0 on ref2va); Sage on; H3 never freed inside the round.

**Checked between shots (all local, all sub-second on the ComfyUI python,
which has `timm`, `open_clip_torch`, `lpips`, `onnxruntime-gpu`, `mediapipe`
installed; DINOv3 ViT-L weights at `models/dinov3/`; ViTPose-wholebody ONNX at
`models/detection/`; ArcFace/insightface **not** installed — `uv add` it or
run it in the ComfyUI python):**

| what | metric | on which frames | gate |
|---|---|---|---|
| identity | ArcFace cosine (insightface `buffalo_l`) face crop vs. the sheet's face | `S_k` before the take; take frames at 25/50/75 % after | see §6 |
| subject | DINO cosine, VBench "subject consistency" form ([VBench++](https://arxiv.org/html/2411.13503v1)) | consecutive sampled frames within a take; `S_k` vs `M` | §6 |
| set/light | CLIP cosine, VBench "background consistency"; mean Lab ΔE of the frame vs `M` (background mask from the face box) | `S_k` vs `M`; last frame of k vs `S_{k+1}` | §6 |
| seam | LPIPS between the last frame of take k and `S_{k+1}` (FLF) or the first frame of take k+1 (i2v) | one pair per cut | §6 |
| pose | ViTPose torso-centre offset, normalised by width | last frame of k vs first of k+1 on continuation cuts only | §6 |
| semantics | the existing Qwen3-VL trait read (`describe.py`, `DISTINCT_AT`) | once per round, batched | unchanged |

A frame that fails at step 4 is re-edited (16 s); a take that fails at step 5
is re-rolled once, then the *start frame* is replaced — never a third seed.

## 6. The smallest probe — one scene, 5 shots

Same scene, same lead, 9:16, shots of 3–4 s, all three video variants on the
same five start frames, seeds fixed. Outputs a JSONL like `ab.jsonl`.

| arm | what | takes |
|---|---|---|
| A | fl2va FLF on `S_1..S_5` (4 FLF + 1 i2v) | 5 |
| B | ref2va + lead ref + `AddGuide(0 = S_k)` | 5 |
| C | ref2va refs only (today's production path), same prompts | 5 |
| D (optional) | A + RefMod of the lead | 5 |

Fifteen takes + 15 start-frame edits + master ≈ 15 × ~5 min + 5 min ≈ **80
min** if the expected i2v cycle holds, ~2 h at today's 336 s. Measure, do not
assume:

**Pass/fail — the first job of the probe is the self-similarity floor:**
compute every metric on `M` against its own five seed-siblings and on the
sheet against itself at three crops; the pass line is the 10th percentile of
that distribution, and the numbers below are priors to be replaced by it.

| gate | pass | warn | fail |
|---|---|---|---|
| ArcFace cosine, take mid-frame vs sheet | ≥ 0.50 | 0.40–0.50 | < 0.40 (a different man — same failure class as run 6b's prompt-only Watson) |
| DINO cosine, `S_k` vs `M` | ≥ 0.70 (framing changes lower it) | 0.60–0.70 | < 0.60 |
| CLIP background cosine, `S_k` vs `M` | ≥ 0.90 | 0.85–0.90 | < 0.85 (a different room) |
| Lab ΔE, background of shot 5 vs `M` (cumulative drift over the chain) | ≤ 5 | 5–8 | > 8 |
| LPIPS at each cut (FLF: last frame vs `S_{k+1}`) | ≤ 0.15 | 0.15–0.25 | > 0.25 (visible jump) |
| pose torso-centre offset on continuation cuts | ≤ 0.10 W | 0.10–0.20 | > 0.20 |
| i2v head leak (frames until DINO(frame, `S_k`) drops below 0.9 — should be 0) | ≤ 5 f | 6–24 f | > 24 f (the 2.6 s tax is back) |
| cycle, resident, 768×1344×~90 f | ≤ 300 s | 300–360 | > 360 (no gain over r2v) |
| Qwen3-VL trait distance | as today (`DISTINCT_AT` 3) | — | — |

Decision rule: pick the arm with the most takes passing *all* of ArcFace,
CLIP-bg and LPIPS; on a tie, the cheaper cycle. If A passes ArcFace on ≥ 4
of 5, refs are not needed in the video stage for this scene type and every
take gets cheaper; if A fails ArcFace and B passes, the anchor+refs graph is
the production path; if only C passes, identity cannot be carried by a start
frame at all and continuity has to come from B-style anchoring on r2v.

## 7. Unresolved

1. **Does i2v/FLF on H3 have a head leak?** The 2.6 s tax is measured on r2v
   only. Expected zero on a pinned frame; nobody here has measured it.
2. **Does ref2va honour an `AddGuide` pixel anchor?** Core wiring allows it;
   the Motion-Context pack chains latents on it; unmeasured.
3. **RefMods**: no numbers exist anywhere; compatibility with turbo LoRAs and
   with the pruned fp8 base unstated.
4. **How much of the take is the TE/ref encode?** The lxref curve's ~350 s
   intercept at 4 steps is not explained by the 79 s step-07 constant; the
   swap is on the HDD and `ref_image_size: "max"` is "several times slower"
   by the node's own tooltip — decompose it with timestamps before buying
   any of §4's speed items.
5. **Sage on H3**: engaged in the manifest prose, disabled in the manifest
   default, never injected; one A/B settles it.
6. **9:16 on LTX-2.5** and **Wan 2.2 on this box**: nothing measured; Wan
   has weights but no `comfy_studio` workflow.
7. **Qwen-Edit wardrobe drift over 15 edits of `M`**: the storyboard
   workflow claims it; the probe's Lab ΔE row measures it.
8. **ArcFace threshold** on illustrated / period-costume faces: calibrate on
   the sheet's own seed-siblings before trusting 0.50.
9. **H3 Singularity** (one checkpoint for fl2va + ref2va) would delete the
   base swap between arms A and B; unmeasured quality.

## Sources

Repo: `.claude/skills/trailer/SKILL.md`; `.claude/skills/trailer/subskills/04-shots/SKILL.md`;
`.claude/agents/trailer-cinematographer.md`; `studio/h3.py`; `studio/comfy.py`;
`scripts/trailer/build_clips.py`; `docs/analysis/research/trailer-retrospect.md`;
`docs/analysis/research/trailer-render-cycle.md`;
`library/20260822113400_a-study-in-scarlet/trailer/main/learnings.jsonl`;
`D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\comfy_extras\nodes_minimax_h3.py`;
`D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\user\comfyui.prev2.log`;
`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\video\*.manifest.json`;
`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\benchmarks\ltx25\TIMINGS.md`;
`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\benchmarks\minimax_h3\h3_ltx_rtx\README.md`;
`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\benchmarks\results\video_minimax_h3_r2v_turbo_lxref__lxref-cost-curve-6__20260827T054313Z\report.json`;
`D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\custom_nodes\{ComfyUI-Wan-SVI2Pro-FLF,wan22fmlf}\README.md`.

Web: [H3 open weights (comfyui-wiki)](https://comfyui-wiki.com/en/news/2026-08-03-minimax-h3-open-weights-comfyui) ·
[Ref2VA Turbo 8-step](https://comfyui-wiki.com/en/news/2026-09-04-minimax-h3-turbo-ref2v-8step) ·
[H3 RefMods](https://comfyui-wiki.com/en/news/2026-09-07-minimax-h3-refmods) · [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod) ·
[H3 Singularity](https://comfyui-wiki.com/en/news/2026-09-07-h3-singularity) ·
[Sparse attention + compiler](https://comfyui-wiki.com/en/news/2026-09-08-h3-sparse-attention-compiler) ·
[CLIPCached](https://comfyui-wiki.com/en/news/2026-09-04-minimaxh3-clipcached) ·
[FL2V Turbo v1.2](https://comfyui-wiki.com/en/news/2026-09-06-minimax-h3-fl2v-turbo-v1-2) ·
[H3 Motion Context](https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context) · [Herrgotts suite](https://comfyui-wiki.com/en/news/2026-08-11-h3-infinite-continuation-suite) ·
[fal H3 LoRA guide](https://fal.ai/learn/devs/how-to-train-a-lora-for-minimax-h3) · [VP Land](https://www.vp-land.com/stories/fal-adds-lora-training-for-minimax-h3-starting-with-an-open-source-realism-people-lora) ·
[H3 turnaround LoRA](https://huggingface.co/matlod/minimax-h3-turnaround) ·
[Wan 2.2 FLF2V template](https://comfy.org/workflows/video_wan2_2_14B_flf2v-7016f027bcf1/) · [Wan 2.2 FLF timing](https://stable-diffusion-art.com/wan-2-2-first-last-frame-video/) · [Wan2.2-I2V-A14B](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B) ·
[SVI 2.0 Pro](https://wanx-troopers.github.io/svi.html) · [SVI drift thread](https://github.com/vita-epfl/Stable-Video-Infinity/issues/51) ·
[Wan-Animate paper](https://arxiv.org/pdf/2509.14055) · [MAGREF](https://arxiv.org/html/2505.23742) · [Phantom](https://arxiv.org/pdf/2502.11079) · [Wan2.2-VACE-Fun](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B) ·
[LTX-2.3 Ingredients](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients) · [Ingredients issue #3](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients/discussions/3) ·
[LTX-2.5 24 GB guide](https://runaihome.com/blog/ltx-2-5-local-ai-video-hardware-guide-2026/) · [LTX-2.3 portrait](https://ltx.io/blog/ltx-2-3-portrait-video) ·
[Qwen-Image-Edit 2511 (Comfy blog)](https://blog.comfy.org/p/qwen-image-edit-2511-and-qwen-image) · [2511 storyboard workflow](https://civitai.com/models/2293093/qwen-image-edit-2511-continuous-storyboard-generation) ·
[FLUX.2 Klein consistency LoRA](https://civitai.com/articles/27410/flux2-klein-9b-consistency-lora) ·
[SageAttention on 4090](https://github.com/D-Ogi/ComfyUI-Attention-Optimizer) ·
[VBench++ metrics](https://arxiv.org/html/2411.13503v1).
