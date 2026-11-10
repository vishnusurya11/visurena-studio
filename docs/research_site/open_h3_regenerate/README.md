# Open-H3-Regenerate-2K: can it improve a local H3 anime video pipeline?

Desk research, 2026-10-29. No downloads, no installs, no GPU runs. Anything not found in a source is marked "unverified".

## 1. Does it exist, and is it what was claimed?

Yes, with two corrections.

- Publisher: NVIDIA's NVlabs Sana team (author post by Enze Xie), not a separate NVIDIA product. Project page: https://nvlabs.github.io/Sana/Open-H3-Regenerate-2K/ . Code: https://github.com/NVlabs/Sana/tree/sol-engine/models/Open-H3-Regenerate-2K . Weights: https://huggingface.co/Efficient-Large-Model/Open-H3-Regenerate-2K .
- What it is: an open replacement for MiniMax's API-only H3-Regenerate-2K. It is a rank-576 LoRA merged from three adapters (NVIDIA refiner rank 384, LightX2V FL2VA Turbo v1.2 rank 128, LMS Sharp v1.0 rank 64), applied to the frozen MiniMax-H3 transformer. Pipeline: encode the draft once, 2x latent upscale, re-noise to sigma 0.909, three Euler steps (0.909, 0.857, 0.667 to 0), CFG off, decode with a fast VAE.
- The 87% figure is real but narrow: a 50-case, 20-session, 200-judgement blinded study; 174 votes for Open-H3, 26 for the official API (project page above). It compares sharpness and aesthetics against the official API. It does not test identity preservation.
- The "5.0x faster than the API" headline is not supported in the body. The body gives 87.26 s to 22.45 s (3.9x) against NVIDIA's own dense baseline, on one B200, 5 s clip.
- Claimed ComfyUI route: no official ComfyUI nodes exist. A community custom node pack exists (https://github.com/rdh9616/ComfyUI-Open-H3-Regenerate, Apache-2.0) plus a community latent upscaler (https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler, MIT). Overview: https://comfyui-wiki.com/en/news/2026-10-27-open-h3-regenerate-2k
- The "extracted LoRA" is Kijai's refiner-only LoRA (refiner part only, no Turbo, no Sharp): rank 384, 5.87 GB, and a rank 16 at 155 MB. https://huggingface.co/Kijai/MiniMax-H3-experimental/tree/main/loras . The README of the node pack says it needs LightX2V Turbo v1.2 and LMS Sharp to match NVIDIA's reference. A ready-made "two-stage latent upscale with the extracted LoRA" workflow file was not found (unverified); the LBH repo ships `workflow_templates/minimax_h3_r2v_Latent Upscaler example workflow.json`, which is the closest.

## 2. Findings per question

**Face restoration with identity (replaces face refine?)** No evidence it can. It is a whole-frame refiner with no reference-image input in any source read. An independent test on an RTX 5090 (https://github.com/inkseq/h3-studio/issues/795) found that at NVIDIA's default settings (start sigma 0.909, 3 steps) "faces change identity; expression and props drift". Identity held at start sigma 0.8 or with the 2-step grid (0.7, 0.494). That test used live-action-style dialogue drafts, not anime, and tested identity by eye only. Whether a 480p far face is made identifiable is a sharpness question, but the model redraws from the draft's own latent: if the draft is not the character, the pass can invent a different face. The "brings the face back, even mid-walk" claim is from the YouTube post only: unverified.

**Temporal consistency.** It is a video model: the whole 5 to 15 s clip goes through in one pass (121 frames for 5 s; 360 for 15 s). Not per-frame. Temporal flicker is therefore handled by the model. Clips under 5 s are padded by holding the last frame to 121 frames, so short takes waste compute.

**Upscale role / final step.** Outputs: 768p (1344x768), 1080p, 2K (2560x1440), 4K (3840x2160). Every size listed is 16:9. The node pack says "portrait drafts get portrait sizes", and the `Latent Upscaler (3D)` takes arbitrary target dimensions with aspect lock, so 1:1 may work but is unverified. The CLI center-crops drafts to cover 1344x768, which would cut a square draft; the ComfyUI pack's behaviour on 1:1 is unverified.

**Reference images / character sheets.** Not supported by NVIDIA's code or the community nodes. H3 itself supports ref2va (up to 9 reference images; https://comfyui-wiki.com/en/news/2026-08-03-minimax-h3-open-weights-comfyui ), and the refiner is the H3 transformer plus a LoRA, so feeding references through the ref2va conditioning node is architecturally conceivable. Whether the refiner LoRA tolerates it is unverified and is not a documented feature. This is the owner's specific question: answer is "no documented way; would be a research experiment".

**License.** Hugging Face card: refiner LoRA, fast VAE decoder and base model follow the MiniMax H3 Community License; the latent upscaler, LightX2V and LMS Sharp keep their own licenses; no blanket license (https://huggingface.co/Efficient-Large-Model/Open-H3-Regenerate-2K ). Secondary sources say the H3 Community License allows commercial use under USD 20M yearly revenue but its territory excludes the United States, EU, UK and South Korea; use there needs a commercial license sold via Comfy (https://comfy.org/minimax/license.md , https://support.comfy.org/articles/6065098425-minimax-commercial-licensing-who-needs-a-license-and-how-to-get-one ). The license text itself was not read. This applies to any local H3 use, including the current pipeline, not only to this refiner. Check it against the actual LICENSE file and your attorney.

**Weights and sizes** (node pack README, https://github.com/rdh9616/ComfyUI-Open-H3-Regenerate ; base sizes from the Comfy wiki page above):

| File | Size |
|---|---|
| open_h3_regenerate_2k_lora.safetensors (merged, FP32) | 12.4 GB |
| sharp_curve_branches.safetensors | 1.2 GB |
| fast_h3_vae_noncausal_24l.safetensors | 6.5 GB |
| latent upscaler (3D conv) | size unstated |
| H3 FL2VA base: bf16 61.7 GB / int8 31.7 GB / pruned int8 19.5 GB | |
| Qwen3-VL-32B text encoder: bf16 48 GB / int8 25.3 GB / nvfp4 14.6 GB | |
| H3 video VAE fp16 | 4.9 GB |
| Kijai refiner-only LoRA rank 384 / rank 16 | 5.87 GB / 155 MB |

Much of the H3 base set is likely already on a machine that runs ref2va; only the refiner pieces are new.

**VRAM.** NVIDIA's reference path needs about 150 GB (B200). The community pack's fast decoder peaks at 21 GB for 5 s at 2K and 45 GB for 15 s at 2K, on a 72 GB card. On a 32 GB RTX 5090, 2K worked in int8 with SageAttention 2 (a fp8 base was needed before that); reported peak 31 GB but that reflects ComfyUI filling the card (issue #795). No 24 GB measurement exists; fit on a 4090 is unverified and would need the pruned int8 base plus offload.

**Speed.** NVIDIA: 22.45 s per 5 s clip on a B200 (their optimized engine, Linux only, not usable on a 4090). Community, RTX 5090, ComfyUI, int8, CUDA 13 plus sage2, per 5 s clip (issue #795): 1080p 2-step about 70 s; 2K 2-step about 145 s; 2K 3-step (sigma 0.8) about 199 to 212 s. An RTX 4090 is slower than a 5090; no 4090 measurement was found.

## 3. Verdicts

1. Replace face refine: no. Whole-frame, no reference input, documented identity drift at default settings.
2. Improve or replace the final upscale: plausible, needs a bench. It is a generative refiner (adds detail), while RTX VSR is a faithful upscaler. Because it replaces rather than follows the upscale, "upscale last, once" can still hold: the refiner becomes the single last step instead of VSR.
3. Send character sheets during the upscale: no documented way. Experimental only.
4. Practical: license has an unresolved territory question; no official ComfyUI route; community nodes work on Windows; 24 GB fit unproven.
5. Added time: see the bench plan. Rough estimate for about 150 s of video (30 clips of 5 s), assuming a 4090 runs 1.3 to 1.6x slower than the 5090 figures: 2-step at 1080p-class sizes about 0.8 to 1.1 h; 2-step at 2K-class sizes about 1.6 to 2.3 h (square 1536x1536 has 64% of the pixels of 2560x1440, so somewhat less). All inside the 6 h budget, but unmeasured on our hardware.

## 4. Bench plan

Create NEW workflow files only. Suggested names: `open_h3_regen_full_<source>.json` (method 1) and `open_h3_regen_kijai_lora_<source>.json` (method 2).

Downloads (do not start without the owner's go):
- Node pack: https://github.com/rdh9616/ComfyUI-Open-H3-Regenerate (pin a commit; the tester pinned `9b686c5`) and https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler
- From https://huggingface.co/Efficient-Large-Model/Open-H3-Regenerate-2K : `lora/open_h3_regenerate_2k_lora.safetensors` (12.4 GB), `lora/sharp_curve_branches.safetensors` (1.2 GB), `vae_fast/fast_h3_vae_noncausal_24l.safetensors` (6.5 GB), `latent_upsampler/` (size unstated)
- Method 2 extra: Kijai rank-384 LoRA (5.87 GB) from the URL above; LightX2V FL2VA Turbo v1.2 and LMS Sharp v1.0 (links not verified here; the project page credits them). Existing local H3 base, text encoder and the 8-step turbo LoRA are reused.
- Workflow sources: `example_workflows/` in the rdh9616 repo (Draft Video, Decode Saved Latent, Prompt to 2K) for method 1; the LBH `workflow_templates` JSON as the starting point for method 2. Both must be copied to new names, never edited in place.

Protocol (3 to 4 takes, one per case):
1. A close dialogue face take (control: should already pass).
2. A far/mid-walk face take, the case the YouTube post claims.
3. A two-character take.
4. A fast-motion take.
For each take, produce five arms from the same H3 draft: (A) current chain: face refine then RTX VSR; (B) face refine then Open-H3 full pipeline, 2-step grid (0.7, 0.494); (C) same with start sigma 0.8, 3 steps; (D) the Kijai-LoRA two-stage rig, 2-step; (E) Open-H3 on the un-refined draft, no face refine. Fix output size to the nearest allowed to 1536x1536; if 1:1 fails, use 1080p and record the crop.
Measure: seconds per clip and peak VRAM on the 4090; identity score against the character sheet (existing gate); seam, flicker, drift gates; side-by-side crops of the face at 100%; check that face-pasted regions are not redrawn into a different person; check audio sync (hold the draft audio, as the tester found silence broke lip match).
Decision rule: adopt only if identity gate pass rate is not lower than arm A, and the visual crop is judged better by the owner. No spend; all local.

## Sources
- https://nvlabs.github.io/Sana/Open-H3-Regenerate-2K/
- https://github.com/NVlabs/Sana/tree/sol-engine/models/Open-H3-Regenerate-2K
- https://huggingface.co/Efficient-Large-Model/Open-H3-Regenerate-2K
- https://github.com/rdh9616/ComfyUI-Open-H3-Regenerate
- https://github.com/LBH-123-AI/Comfyui_Minimax_h3_latent_Upscaler
- https://huggingface.co/Kijai/MiniMax-H3-experimental/tree/main/loras
- https://github.com/inkseq/h3-studio/issues/795
- https://comfyui-wiki.com/en/news/2026-10-27-open-h3-regenerate-2k
- https://comfyui-wiki.com/en/news/2026-08-03-minimax-h3-open-weights-comfyui
- https://comfy.org/minimax/license.md
- https://support.comfy.org/articles/6065098425-minimax-commercial-licensing-who-needs-a-license-and-how-to-get-one
