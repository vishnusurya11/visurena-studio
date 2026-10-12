# R2-S: take speed on the 4090, round 2 (2026-10-10)

Researcher S (SPEED), round 2. Research plus read-only local inspection. Nothing was installed, no GPU job
was run, and no code or workflow was edited. It builds on `F_research_h3_workflows.md`, `P2_quality_speed_plan.md`,
`S_skeptic_verdict.md`, `BENCH_phase0.md` and `docs/research/ref2v_speed_2026-09-16.md`, and does not repeat them.
**Starting point:** the 4-step LoRA graph `video_minimax_h3_r2v_turbo_ref8_ref4_singularity` is approved, so it is the
`<base>` for every new name below.

## 0. What the machine actually is (read today, not assumed)

| Item | Value | How read |
|---|---|---|
| Python / torch / CUDA | 3.12.10 / **2.11.0+cu130** / CUDA 13.0, cuDNN 9.19 | `python_embeded\python.exe -c "import torch..."` |
| GPU | RTX 4090, sm_89, driver 591.86, 24 GB | torch + `nvidia-smi` |
| triton | `triton-windows 3.5.0.post21` (imports). torch 2.11 expects triton 3.6, so treat torch.compile as unsupported here. | import + `pip_before_sage.txt` |
| sageattention | `2.2.0+cu128torch2.10.0andhigher.post5`. `import sageattention` fails: **`DLL load failed while importing _fused`** (the cu128 wheel on a cu130 torch). | import |
| xformers 0.35 | built for torch 2.10 cu128 / py3.10, so its C++ ops do not load. Unused. | import warning |
| comfy-kitchen | 0.2.35. `int8_attention_is_available()` = **True**. Exports `int8_attention`, `sage_attention`, `sol_attn`, `flash_attention`. | import |
| ComfyUI | 0.36.0 (`3dd559d81`, 2026-09-20). Dynamic VRAM (comfy-aimdo) on. **The Comfy model compiler (CUDA graphs) is already on**: "graph breaks: 3, rogues: 0" on every take. | `comfyui.prev2.log` |
| Engine now | PID 43272, started 21:42: `--windows-standalone-build --reserve-vram 2`. **No `--use-ck-attention`**: the bench's CK relaunch (21:38, BENCH §8) was replaced, and production is back to pytorch attention. | `Get-CimInstance` |
| Singularity int8 | 200 layers `int8_tensorwise`, `convrot: true`, groupsize 256, run natively through `ck.int8_linear` ("Native ops: … int8_tensorwise") | safetensors header + log |
| Take graph | node 3 `PathchSageAttentionKJ` = `disabled`; plain `VAEDecode` (H3 VAE is internally tiled 256 px + temporal chunks); SaveVideo CRF 10 | the workflow JSON |
| Custom nodes of note | KJNodes (Sage patch, TorchCompile nodes), `ComfyUI-MiniMax-H3-Turbo`, `dynamic-ramcache`, `reservedvram`, `ComfyUI-FlashVSR_Ultra_Fast.disabled`. **No** Sage-safety, TeaCache/MagCache, TRT-VAE or H3-TAE node is installed. | `custom_nodes\` |

### Where a take's seconds go (production batch, 2026-10-10 13:25-13:41, 8 steps, renders queued back to back)

| Phase | Seconds | Note |
|---|---|---|
| TE encode (Qwen3-VL 32B nvfp4: emulated nvfp4 on Ada) + ref/guide encode | ~5-6 | 14.96 GB TE staged each take |
| DiT re-upload after the TE swap + 208 LoRA patches + step-1 warm | ~6 | wall from "prepared" to the bar's start |
| Sampling, 8 steps | 63-101 (8.3-13 s/it) | s/it grows faster than frame count, which means attention-heavy |
| Video + audio VAE decode, CreateVideo, CRF-10 save | ~15-21 | |

With 4 steps (approved) a production take is about **12 + ~36 + ~18 ≈ 66 s**. Sampling is now only about 55 % of
the take, so the remaining levers are worth less than they were at 8 steps. WotW ep22-27 spent **60-81 min per
episode in `takes`** (`timing.jsonl`). I use **30 renders per episode** (25 takes plus retakes) to convert per-take
seconds into minutes per episode.

## 1. Ranked top 5

### #1. Comfy Kitchen int8 attention, scoped to the take graph by a core node (no install, no restart)
**New file:** `video_minimax_h3_r2v_turbo_ref8_ref4_singularity_ckattn_comfyorg.json`

- **What changed since F/BENCH:** both treated CK as the global launch flag `--use-ck-attention`. That flag switches
  every job on the shared engine, Scarlet's and the Qwen-Image/Krea/VL jobs included, which is why the bench got blocked.
  ComfyUI 0.36 ships a **core node `ModelAttentionBackend`** (`comfy_extras/nodes_model_advanced.py:381`,
  experimental) with `backend = "comfy kitchen attention"` → `comfy_kitchen_int8`. It sets the attention per model
  through `set_model_optimized_attention`. H3's DiT calls `optimized_attention(..., transformer_options=...)`
  (`comfy/ldm/minimax/model.py:199`), so the override reaches it. **One node in one graph, so nothing else on
  the engine changes.**
- **Graph:** `UNETLoader(1) → LoraLoaderModelOnly(2, 4-step @1.0) → ModelAttentionBackend(new, "comfy kitchen attention") → node 3 (disabled) → MiniMaxH3SigmaShift(4)`.
  The manifest should declare no `sage_attention` change. Its optional defaults must match the graph (S's acceptance rule).
- **Gain:** the 2026-09-16 research measured CK on a 4090 at **1.34x whole prompt (124 f) and 1.79x on the sampler (328 f)**.
  At our 4-step ~36 s sampling, a 1.35-1.6x sampler gain is **−9 to −13 s per take, so −4.5 to −6.5 min per episode**.
  That agrees with S's −5 to −7. The longest dialogue takes (D2 175 f, 15 s/it) gain the most.
- **Risk:** int8 Q·K is a small numerical change. In Comfy-Org #15263, the comfy-kitchen int8 path ran cleanly on the
  exact shape where Sage produced noise. Our token count is about 31 k (768²×175 f; scaled from the 1088×1952×362 f
  = 231 k case), far below every reported noise cliff (151-167 k on sm_120, 231 k on the 4090). The node is marked
  experimental. CK may also interact with the Comfy model compiler: watch the "graph breaks" count.
- **Verify (≈10 GPU min):** replay the 6 bench shots (S2 S3 S4 S6 D1 D2) on `<base>` vs `<base>_ckattn_comfyorg` with
  the same seeds through `scripts/bench/h3_arms.py`. Assert on the *ran* graph that the node is present and
  `backend = comfy kitchen attention`. Read s/it from the sampler bar (`scripts/bench/timing.py`). Accept if s/it
  drops at least 20 %, banding is non-inferior, clones are 0, identity is within 0.02, lag is within ±0.1 s, and the
  contact sheets get the eye. Also report a per-frame PSNR vs `<base>` (expect ≥ 30 dB; a 3090 Sage report measured
  30 dB vs SDPA).
- **Adopt / rollback:** `scripts/episode/takes_r2v.py` `BASE = "…_ref4_singularity_ckattn_comfyorg"`. Rollback: `BASE = "video_minimax_h3_r2v_turbo_ref8_ref4_singularity"`.

### #2. SageAttention 2.2 post6 cu130 (the A/B partner of #1, or its fallback)
**New file:** `video_minimax_h3_r2v_turbo_ref8_ref4_singularity_sage_woct0rdho.json` (node 3 `sage_attention: sageattn_qk_int8_pv_fp16_cuda`, `allow_compile: false`)

- **Wheel:** `sageattention-2.2.0+cu130torch2.10.0andhigher.post6-cp310-abi3-win_amd64.whl` (16.7 MB, 2026-07-17,
  144 k downloads; abi3 covers py3.12; "torch2.10.0andhigher" covers 2.11). URL:
  `https://github.com/woct0rdho/SageAttention/releases/download/v2.2.0-windows.post6/sageattention-2.2.0%2Bcu130torch2.10.0andhigher.post6-cp310-abi3-win_amd64.whl`.
  post6 fixes an out-of-bounds read that "caused black or noise outputs" (PR 98). post7 (2026-10-09) is ROCm-only, so
  **there is no newer CUDA wheel**. **SageAttention3 is not an option:** KJ's `sageattn3` modes call `sageattn3_blackwell` (sm_100/120 only).
- **Install (its own window, queue empty, engine stopped):**
  ```
  cd D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable
  mkdir D:\wheels\sage
  curl -L -o "D:\wheels\sage\sageattention-2.2.0+cu128torch2.10.0andhigher.post5-cp310-abi3-win_amd64.whl" https://github.com/woct0rdho/SageAttention/releases/download/v2.2.0-windows.post5/sageattention-2.2.0%2Bcu128torch2.10.0andhigher.post5-cp310-abi3-win_amd64.whl
  curl -L -o "D:\wheels\sage\sageattention-2.2.0+cu130torch2.10.0andhigher.post6-cp310-abi3-win_amd64.whl" https://github.com/woct0rdho/SageAttention/releases/download/v2.2.0-windows.post6/sageattention-2.2.0%2Bcu130torch2.10.0andhigher.post6-cp310-abi3-win_amd64.whl
  python_embeded\python.exe -m pip install --force-reinstall --no-deps "D:\wheels\sage\sageattention-2.2.0+cu130torch2.10.0andhigher.post6-cp310-abi3-win_amd64.whl"
  python_embeded\python.exe -c "import sageattention, sageattention._fused; from sageattention import sageattn_qk_int8_pv_fp16_cuda; print('ok')"
  ```
  **Rollback:** `python_embeded\python.exe -m pip install --force-reinstall --no-deps "D:\wheels\sage\sageattention-2.2.0+cu128torch2.10.0andhigher.post5-cp310-abi3-win_amd64.whl"`.
  The rollback restores today's state exactly: unimportable and harmless, because node 3 is `disabled` in every production graph.
  `--no-deps` matters: without it, pip may pull a different torch.
- **Gain:** about the same as #1. Measured elsewhere: 3090 129 → 94 s (−27 %), 4070 −29 %, 3090 sampler 1.37x. For us that is **−8 to −12 s per take, −4 to −6 min per episode**.
- **Why #2, not #1:** it needs an environment change on a shared engine, and it carries the known H3 Sage
  faults: noise above about 160 k tokens on sm_120 (#15263, root cause unsettled, possibly the fp8-PV kernels), and a
  4090 32-bit address overflow at 231 k tokens (liaowu-boos `ComfyUI-MiniMaxH3-SafeSageAttention`). At about 31 k tokens we are
  clear of both. Use the **`pv_fp16`** kernel, never `pv_fp8`/`auto` (auto picks fp8-PV on sm_89). The sageattn quant
  kernels also need triton, and triton-windows 3.5 against torch 2.11 is an untested pair, so the import test above must include a call.
- **Verify:** the same 6-shot replay, run as a three-way comparison `<base>` / `_ckattn_comfyorg` / `_sage_woct0rdho`. Keep the
  faster of #1/#2 if both pass. If they tie, keep **#1** (no install, scoped).

### #3. Bake the 4-step LoRA into the Singularity int8 file (skip per-take patching)
**New files:** the one-off merge graph `video_minimax_h3_r2v_turbo_ref8_ref4_singularity_mergesave_visurena.json`
(`UNETLoader(Singularity int8) → LoraLoaderModelOnly(4-step v0.1 @1.0) → ModelSave(filename_prefix "diffusion_models/Minimax-h3_Singularity_v1.3_int8_ref4merged")`)
and the take graph `video_minimax_h3_r2v_turbo_ref8_ref4_singularity_merged_visurena.json` (UNET =
`Minimax-h3_Singularity_v1.3_int8_ref4merged.safetensors`, LoRA node removed, node 3 wired to node 1).

- **Mechanism (read in ComfyUI source):** each take, the 15 GB TE pushes the 20 GB DiT out of VRAM. The DiT is then re-uploaded,
  and each LoRA'd int8 layer is **dequantized, has the delta added, and is requantized** (`ops.py:269-336`,
  `requantize_from_float(..., stochastic_rounding=seed_key)`). The log shows "208 patches attached" on every take
  (104 with one LoRA). A layer streamed rather than resident pays this on **every step**. A merged file pays it never.
  `ModelPatcher.model_state_dict_for_saving` saves quantized layers through `LazyCastingQuantizedParam`
  (`model_patcher.py:1730`), so the core `ModelSave` writes an int8-convrot file with the LoRA baked in. No external quantizer is needed.
- **Gain:** **−2 to −6 s per take (−1 to −3 min per episode)**. This is the least certain number: it is the
  share of the ~6 s "prepared → first step" gap that is patch work. The graph also gets one node simpler and one less
  file to load. It does **not** change s/it unless layers are being streamed.
- **Risk:** low for quality if the saved requantization matches the runtime one (same convrot recipe, same per-key
  seed). The merge pins the strength at 1.0, so a strength change means a new merge. The file is 21 GB on C: (271 GB free).
  It must be redone if Singularity or the LoRA changes. **Run after #1/#2 are settled**, because both stack on top of it.
- **Verify:** same seed on 3 shots, `<base>` vs `_merged`. Expect PSNR ≥ 45 dB, ideally bitwise-equal frames. Time
  "prepared → first step" and the whole prompt from the log. Assert on the ran graph that the UNET is the merged file and no LoRA node is present.
- **Commands:** submit the merge graph once. Then copy
  `D:\Projects\KingdomOfViSuReNa\alpha\ComfyUI_windows_portable\ComfyUI\output\diffusion_models\Minimax-h3_Singularity_v1.3_int8_ref4merged_00001_.safetensors`
  to `C:\comfy_models\diffusion_models\Minimax-h3_Singularity_v1.3_int8_ref4merged.safetensors`. Rollback: `BASE` back to the unmerged name.
- **Publishable:** "bake a turbo LoRA into an int8-convrot H3 checkpoint with stock ComfyUI" is a five-node recipe
  that nobody documents (PulpCut did it for the FL2VA lineage with no ref2va numbers). It can be shipped with the bench.

### #4. VAE decode tail: TensorRT H3 VAE (bench only, deferred)
**New file (if run):** `video_minimax_h3_r2v_turbo_ref8_ref4_singularity_trtvae_lihaoyun6.json` (node pack
`github.com/lihaoyun6/ComfyUI-H3VAE_TRT`, ONNX `huggingface.co/lihaoyun6/MiniMax-H3-VAE-ONNX`).

- At 4 steps the ~15-21 s decode+save tail is about a quarter of a take. The core VAE was already optimised (Comfy-Org PR #15446, kijai,
  merged 2026-08-09, in our 0.36): chunked I/O, bitwise-identical output, but **speed unchanged** (14.6 → 13.9 s at
  175×1344×768). The only faster decoder is the TRT pack, which claims "up to 1.7x". That would be **−4 to −7 s per take, −2 to −3.5 min per episode**.
- **Why deferred:** the claim names no GPU or resolution. Builds reportedly take up to 5 h. Windows is unstated. A
  grid-pattern bug was fixed only on `main`. It needs a TensorRT matching CUDA 13. Kijai's H3 TAE / madebyollin `taeh3`
  are **preview-only** decoders and are rejected for finals.
- **Verify, if ever:** decode the same 3 latents both ways (`SaveLatent` from a `<base>` take). Require PSNR ≥ 40 dB
  and the banding ruler non-inferior, and time the decode node alone.

### #5. Measure the phases per take before and after each switch (no workflow; the instrument the four above need)
- Production has no per-phase record. `timing.jsonl` stops at the stage, and today's phase split had to be rebuilt
  from `comfyui.prev2.log` by hand (log lines with `\r` progress bars; parser at
  `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\r2s\phases.py`).
  Promote `scripts/bench/timing.py`'s sampler-bar reader into the take step (test first). Record per take: encode,
  first-step gap, s/it, steps, decode+save, and whether the UNET or TE node re-ran.
- This turns #1-#4 from estimates into per-episode facts, and it gives the publishable ref2va bench its production column.
  It also catches the silent failure classes: an attention patch that does not reach the model (s/it unchanged),
  "a fix that changes nothing", and RAM-pressure-cache evictions. On 2026-10-10 the UNETLoader node re-ran on 5 of 9 takes
  after foreign prompts, which cost the NVMe re-read but showed no measurable pre-sampling penalty (8.8 vs 9.9 s).

## 2. Looked at and rejected (with the number that kills it)

| Lever | Verdict | Why |
|---|---|---|
| torch.compile (triton-windows + KJ `TorchCompileModel*`) | **Reject** | The Comfy model compiler (CUDA graphs) already runs. woct0rdho notes that comfy-aimdo breaks full-graph compile and asks for `--disable-dynamic-vram`, which would change the memory regime of the whole shared engine. triton-windows 3.5 vs torch 2.11 (3.6 expected) is a mismatched pair. Every take has a different frame count, so dynamic shapes mean recompiles or a dynamic graph. The ck int8 linears are custom ops and add graph breaks. Typical DiT gain is 10-20 % of sampling (≈ −4-7 s per take), for minutes of compile on each new shape and a cache that does not survive restarts. Not worth it. |
| fp8 fast matmul (`fp8_e4m3fn_fast`, `--fast fp8_matrix_mult`) | **Reject** | We already run native **int8** GEMM (`ck.int8_linear`). On a GeForce 4090, dense int8 is 660 TOPS while FP8 with FP32 accumulate is 330 TFLOPS (FP16-accumulate 660). int8 is at least as fast as fp8 on this card, and on CUDA 13 int8-convrot beat fp8 by 8-30 % (09-16 research). The stock fp8 file also lives on the HDD (19.5 GB, about 2 min per load). |
| `--fast fp16_accumulation` / `cublas_ops` | Reject | They touch fp16 matmuls only. Our linears are int8 and the rest is bf16. |
| TeaCache / MagCache / EasyCache / FBCache | **Reject** | At 4 steps, skipping one call is 25 % of the trajectory. EasyCache "cannot combine with Turbo LoRAs". The safe EasyCache setting kept 1.14x at 8 steps with a crosshatch weave at default. The besthub 4090 numbers (1.43-2.0x) are 20-step, called draft-only, with no quality measure. Duplicates and drift are our worst faults. |
| Sol-Attn / comfy-kitchen block-sparse | Reject | It duplicated a character at tau 1.8, and the gain at the safe tau 1.4 was 6 % (F). |
| SageAttention3 | N/A | Blackwell-only kernels. |
| Batching takes (batch 2 per sampler) | Reject | The 4090 is compute-bound at about 31 k tokens. Batch 2 doubles activations next to a 20 GB DiT, saves nothing in FLOPs, and breaks per-take seeds and resume. |
| "Encode-all" (TE for all takes first, then sample) | Reject for now | The win is the ~5-6 s TE encode plus the ~6 s DiT re-upload per take (≈ 6 min per episode at most). But `MiniMaxH3ReferenceToVideo` emits conditioning plus guide latents per take, and core ComfyUI has no save/load for that pair, so it would need a custom node and a two-pass runner. Revisit only if #5 shows the swap is above 10 s. |
| `--highvram` / pin everything resident | Reject | TE 15 GB + DiT 20 GB + VAE 5 GB do not fit in 22.5 GB usable. Dynamic VRAM already swaps them in about 6 s from pinned RAM (64 GB). |
| Latent upscaler, VSR per take | Out of scope | They cost time, not save it (F #3, BENCH §3). |

## 3. Budget (per episode, 30 renders, on top of the approved 4-step)

| Change | s per take | min per episode | Confidence |
|---|---|---|---|
| 4-step (approved, already counted by S/BENCH) | −35 to −40 | −15 to −20 | measured |
| #1 CK attention (or #2 Sage) | −9 to −13 | **−4.5 to −6.5** | 4090 CK measured elsewhere; ours not |
| #3 merged LoRA | −2 to −6 | −1 to −3 | mechanism read in source; size unmeasured |
| #4 TRT VAE (deferred) | −4 to −7 | −2 to −3.5 | vendor claim only |
| **#1 + #3** | **−11 to −19** | **−5.5 to −9.5** | |

The `takes` stage goes from 60-81 min (8-step) to about 35-50 min with 4-step + #1 + #3. The episode's 6 h problem is
still the plan stage (37-142 min) and the check windows (take_dq + take_content + qc ≈ 45-85 min). The take renderer is no
longer the long pole after 4-step.

## 4. Order of work (one GPU window of about 30 min, queue empty)

1. #1: write `<base>_ckattn_comfyorg.json` plus its manifest (test first: manifest defaults equal graph knobs). Replay 6 shots.
2. #2 only if #1 fails quality or gains under 20 %: the wheel swap above, then the same 6-shot replay as a three-way.
3. #3 on the winner: merge once, 3-shot bitwise/PSNR check, then `<winner>_merged_visurena.json`.
4. #5 lands with the first switch, so the first production episode reports its own phase table.
Each switch: `takes_r2v.py BASE` line, a decision file, a `docs/DECISIONS.md` line. No step or stage changes, so the
architecture page needs only the take step's workflow name.

## Sources

- https://github.com/woct0rdho/SageAttention/releases (post5/post6/post7 assets and notes, via the GitHub API)
- https://github.com/Comfy-Org/ComfyUI/issues/15263 (H3 + Sage noise cliff, CK clean on the same shape)
- https://github.com/Comfy-Org/ComfyUI/pull/15446 (H3 VAE chunked I/O, merged 2026-08-09, bitwise-identical, speed same)
- https://comfy.icu/extension/liaowu-boos__ComfyUI-MiniMaxH3-SafeSageAttention (4090 32-bit overflow at 231 k tokens)
- https://comfyui-wiki.com/en/news/2026-09-22-h3vae-trt · https://github.com/lihaoyun6/ComfyUI-H3VAE_TRT
- https://comfyui-wiki.com/en/news/2026-08-04-kijai-minimax-h3-tae (TAE: preview only)
- https://www.besthub.dev/articles/running-minimax-h3-locally-comfyui-setup-faster-downloads-and-vram-peak-management-eae294f24697 (4090 EasyCache numbers, 20 steps)
- Local: `ComfyUI\comfy_extras\nodes_model_advanced.py` (ModelAttentionBackend), `comfy\ops.py` (int8 + LoRA requant path),
  `comfy\model_patcher.py` (quantized save), `comfy\ldm\minimax\model.py`, `comfy\cli_args.py`; `ComfyUI\user\comfyui.prev2.log`;
  `docs\research\ref2v_speed_2026-09-16.md`; `BENCH_phase0.md` `bench_evidence\timing_b1.json`.
