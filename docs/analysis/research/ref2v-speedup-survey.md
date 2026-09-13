# ref2v speedup survey — is there a newer turbo LoRA, and what else is left?

Researched 2026-09-12. Question from the owner: "do we have the latest turbo
LoRA for ref2v on MiniMax-H3, and are there better settings/LoRAs since
OpenVDN's release?"

## Answer 1: we are already on the newest ref2v turbo LoRA

`lightx2v/Minimax-h3-Turbo` file tree, read via the HF API:

| line | versions published |
|---|---|
| **ref2v** | `4step_v0.1`, **`8step_v1.0_768p`** |
| fl2v | `4step_v0.1`, `4step_v1.0_768p`, `4step_v1.1_768p`, `4step_v1.2_768p`, `8step_v1.0_768p`, `8step_v1.0` |

We run `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`.
**That is the newest ref2v turbo LoRA that exists.** There is no ref2v v1.1 or
v1.2. The v1.1/v1.2 progression is fl2v-only.

The one other ref2v option is `ref2v_turbo_4step_v0.1`, which would halve
sampling steps — but it is pre-v1.0 lineage. Do not confuse it with the fl2v
4-step v1.2: taking that would reintroduce exactly the family mismatch the
owner caught on 2026-09-10 (camera-scale pumping), recorded in
`scripts/episode/takes_r2v.py`.

## Answer 2: every H3 accelerator shipped since is fl2v or t2v, not ref2v

| candidate | task family | verdict |
|---|---|---|
| `OpenVDN/vdn-minimax-h3` (hybrid linear attention, 82 GB) | **t2va only** — pipeline loads `workflow="t2va"`, card never mentions reference images | rejected: wrong task |
| `lightx2v/Minimax-h3-Turbo-SLA` (sparse linear attention) | **fl2v only** (`fl2v_turbo_4step_v0.1_768p_sla`) | rejected: wrong family |
| `ibyteohdear/MiniMax-H3-Pruned-LightX8-Fused` (pruned, rank-8 AdaLN, bf16) | **FL2VA** | rejected: wrong family |
| `rzgar/minimax-h3_ref2va_8Step_motion_enhancer` | ref2va ✅ | rejected: motion/anatomy quality not speed; card says to *disable* the lightx2v LoRA; NSFW-focused; ~18 downloads/month |
| `taurusduan/MiniMax-H3-FL2VA-Ref2VA-Hybrid-NVFP4` | ref2va ✅, NVFP4 | see caveat below |

**The finding:** ref2v is the neglected branch of H3 acceleration. The whole
ecosystem is optimising fl2v/t2v. There is *one* model-level lever left for
our path -- the 4-step ref2v turbo, see Round 2 -- and nothing else.

### NVFP4 caveat (needs verification before spending time on it)

NVFP4 native matmul is Blackwell (sm_100+). Our 4090 is Ada (sm_89), so an
NVFP4 ref2va checkpoint would most likely be *dequantized* at runtime — a VRAM
saving, plausibly a speed *loss*. On Ada the native fast path is fp8 (e4m3),
which our current `minimax_h3_ref2va_pruned_fp8_scaled.safetensors` already is.
OpenVDN's own numbers are all B200/H200, which is consistent with this.

## So the speedups left are runtime, not model

Current workflow —
`D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\video\video_minimax_h3_r2v_turbo_ref8.json`

| lever | current | proposed | note |
|---|---|---|---|
| `PathchSageAttentionKJ.sage_attention` | **`"disabled"`** | `sageattn_qk_int8_pv_fp8_cuda` | the node is wired in and switched off; ref2v has never used Sage |
| sageattention wheel | **broken** — `DLL load failed importing _fused` (cu128/torch2.10 wheel on torch 2.11.0+cu130) | reinstall for cu130/torch2.11/cp312, or roll the stack back to cu128 | blocks the lever above; KJNodes imports with no try/except, so flipping the field first hard-fails the prompt |
| `UNETLoader.weight_dtype` | `"default"` | `fp8_e4m3fn_fast` | Ada has native fp8; checkpoint is already fp8_scaled |
| launch `--reserve-vram` | `2` | drop, or `0.5` | 2 GB off 24 GB pushes H3 into more offload |
| `allow_compile` | `false` | `true` (after Sage works) | untested here |
| steps | `8` | 8 | already turbo; 4-step ref2v is v0.1 lineage, quality risk |

Not a regression: because Sage was `disabled` in the workflow all along, any
"it got slower" is from the torch 2.11 move (the `Conv3d` VAE-memory workaround
a node now patches in) or `--reserve-vram`, not from losing Sage.

## Possibly publishable

If the A/B produces real numbers, "ref2v is the neglected branch: measured
acceleration options for MiniMax-H3 reference-to-video on consumer Ada" is a
genuine gap — nobody has published ref2v-specific numbers, and the four repos
above all fail on task-family grounds. Worth a short benchmark writeup +
possibly a corrected ComfyUI workflow published as a standalone artifact.

## Sources

- https://huggingface.co/api/models/lightx2v/Minimax-h3-Turbo/tree/main
- https://huggingface.co/api/models/lightx2v/Minimax-h3-Turbo-SLA/tree/main
- https://huggingface.co/OpenVDN/vdn-minimax-h3
- https://huggingface.co/ibyteohdear/MiniMax-H3-Pruned-LightX8-Fused
- https://huggingface.co/rzgar/minimax-h3_ref2va_8Step_motion_enhancer

---

# Round 2 — ref2v-specific findings

## Correction: there IS one family-correct model lever

ComfyUI's own native H3 docs name the ref2v turbo as
**`minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16`** — 4 steps, and it is
genuinely ref2v family, not fl2v. We run the 8-step v1.0. Halving steps is
the single biggest available cut to sampling time (~2x on the sampler).

The catch is version lineage, not family: v0.1 predates the v1.0 we use. So
this is a quality A/B, not a free win — but it is the only model-level speed
option that does NOT reintroduce the 2026-09-10 family mismatch.

## Our settings are already correct or already optimal

| setting | ours | authority | verdict |
|---|---|---|---|
| `shift_video` / `shift_audio` | `12` / `3` | "recommended shift values for reference-to-video are shift_video (12) and shift_audio (3)"; H3's trained defaults | **correct** |
| `ref_image_size` | `match` | docs: `match` (faster) vs `max` (stronger identity, up to 2048px short edge) | **already the fast option** — do not switch to `max` |
| steps | `8` (turbo) | docs default is 20 non-turbo | **already turbo** |
| reference ceiling | 9 (plate + sheet + <=4 faces + pins) | docs: "up to 9 reference images, 3 reference videos, 3 standalone reference audio clips" | **at the ceiling** |

Shift and sampler are coupled to the adapter: "the shift values and sampler
must match the adapter you're using, as reusing settings with mismatched
adapters produces poor results." So an adapter swap (8-step -> 4-step) means
re-checking shift, not inheriting 12/3 blindly.

## Reference count is a real, ref2v-only speed lever

"High-resolution or numerous references remain in the attention sequence" —
the guidance for degraded R2V performance is explicitly to "keep reference
count and shorten reference clips."

This is the lever no benchmark covers and it is specific to our path: every
reference we pass costs attention-sequence length for the whole sample. We
pass up to 9. `MAX_FACES = 4` (widened from the node's ceiling reasoning on
2026-09-12) is therefore a *speed* setting as well as a fidelity setting.
Worth measuring: 9 refs vs 6 refs vs 4 refs, same take, same seed.

## Sage attention: the claim, and the caveat

ComfyUI's own estimate is that SageAttention "can roughly double generation
speed with minimal quality loss" — unverified per-system. The H3-specific
caveat: "some H3 layers fall outside supported dtypes, causing expected
fallback warnings." So expect warnings, not a clean 2x, and measure.

## FL2V vs Ref2V — settled

The owner asked whether fl2v lacks audio, and whether dialogue could be
lipsynced later instead. Per ComfyUI's native docs:

- **FL2VA does have audio.** All three families are audio-capable (t2va,
  fl2va, ref2va); fl2va generates native stereo audio including dialogue.
  Audio is not the differentiator.
- **FL2V cannot take reference images.** "Connect images to `first_frame`
  and/or `last_frame` on the `MiniMaxH3ImageToVideo` node" — only those two
  temporal boundaries. Identity from references requires Ref2V/Ref2VA.

So the blocker is structural, not audio: fl2v gives exactly TWO anchors, and
a take in our engine is a run of consecutive shots with an approved panel
anchored at EACH shot's start frame (`h3_anchors`, `takes_r2v.py`). A 4-shot
take needs 4+ anchors. fl2v cannot express our take at all, and would also
discard the cast sheets, the plate and the storyboard sheet.

Lipsync-later is also the wrong direction for us: ref2va is driven by the
line's OWN cast wav anchored at its frame. Generating speech in-model and
lipsyncing afterwards would discard the cast voices (gated on measured
similarity) and break the audio-first rule (picture cut to MEASURED voice).

The *useful* version of that question: for takes with no dialogue we anchor
silence — does the audio branch still cost time? Untested, and cheap to test.

## No published 24 GB benchmarks exist — confirmed

"Early RTX 3090 results vary substantially with resolution, duration,
references and offload settings. There is not yet a defensible expected speed
for a generic 24 GB card." No per-step or per-clip 4090 timings published
anywhere found. This is the publishable gap.

## Sources (round 2)

- https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native
- https://docs.comfy.org/tutorials/video/minimax/minimax-h3
- https://kingy.ai/ai/ai-guides/minimax-h3-comfyui-local-guide/
- https://comfy.icu/node/MiniMaxH3SigmaShift

---

# Round 3 — the ref2v 4-step, dated

Per-file commit dates from the HF API (`tree/main?expand=true`):

| file | added | 768p-tagged |
|---|---|---|
| `ref2v_turbo_4step_v0.1_comfyui_bf16` | **2026-08-13** | **no** |
| `ref2v_turbo_8step_v1.0_768p_comfyui_bf16` (ours) | **2026-09-03** | yes |

And the fl2v line shows what the tag means:

| fl2v version | added | 768p-tagged |
|---|---|---|
| `4step_v0.1` | 2026-08-07 | no |
| `4step_v1.0_768p` | 2026-08-11 | yes |
| `4step_v1.1_768p` | 2026-08-20 | yes |
| `4step_v1.2_768p` | 2026-09-04 | yes |

**The `768p` tag appears at v1.0 and on every version after it. The untagged
v0.1 releases are the pre-768p generation.**

## Verdict on the 4-step

The ref2v 4-step v0.1 is not merely "an older version" — it predates
lightx2v's 768p ref2v recipe entirely. We render at **768x1344**. So the
4-step is out of its trained resolution envelope, not just behind on quality.

It remains the only family-correct model-level speed lever (~2x on the
sampler, 8 steps -> 4), and it is worth an A/B, but with a *predicted* failure
mode to look for rather than a vague "might be worse": resolution-domain
artifacts — soft or mushy detail, and structural drift along the tall 1344
axis. If the A/B fails, it should fail that way; if it fails some other way,
the cause is elsewhere.

Do not inherit shift 12/3 into the 4-step run. Shift is coupled to the
adapter ("the shift values and sampler must match the adapter you're using"),
and 12/3 is the 8-step v1.0 recommendation.

## The thing actually worth waiting for

lightx2v iterated fl2v three times (v1.0 -> v1.1 -> v1.2) and ref2v once
(v0.1 -> v1.0). A **ref2v 4step v1.x, 768p-tagged** would be the real win:
half the steps inside the trained envelope. It does not exist yet. Watching
`lightx2v/Minimax-h3-Turbo` for it is worth more than forcing v0.1.

## Why fl2v is out, final form (owner, 2026-09-12)

Beyond the anchor-count and reference arguments: fl2v interpolates between two
frames and therefore has **no information about anything not visible in
them**. A subject rotation or a camera pan down requires the model to invent
the back of a head, or the floor — and it will invent it differently on every
take. Reference images ARE that off-frame context. This is the structural
reason ref2v is required for our shot language, independent of everything else.

---

# Round 4 — alibaba-pai/MiniMax-H3-Acc-LoRAs vs lightx2v

Owner asked which is better. Read the actual safetensors header via an HTTP
range request (first 256 KB) rather than trusting the card.

## What the file says about itself

`MiniMax-H3-Ref2VA-Acc-8Step.safetensors`, 1.37 GB, added 2026-08-26.
Embedded `__metadata__`:

    lora_rank      64
    lora_alpha     64.0
    pdd_block_size 4
    pdd_num_steps  32
    lora_targets   to_q,to_k,to_v,to_out.0,ff.net.0.proj,ff.net.2,adaln_proj.linear

728 tensors. Key shape: `token_refiner.refiner_blocks.0.attn.to_k.lora_down` /
`.lora_up` (362 each), plus bare `proj_out.weight`, `audio_proj_out.weight`.

Format probes: `lora_down`/`lora_up` naming, **zero** keys carrying a
`diffusion_model.` prefix, zero `lora_A`/`lora_B`.

## Three reasons it loses for our pipeline

**1. It is not a speed win at all.** `Ref2VA-Acc-8Step` is *8 steps* — exactly
what we already run. There is no step reduction on offer. It is a quality play,
not a speed play, so it does not answer the question we are asking.

**2. PDD needs a custom decoding loop we do not have.** Parallel Decoding
Distillation, `pdd_num_steps=32` with `pdd_block_size=4` (a 32-step teacher
covered in blocks of 4 => 8 passes). The repo ships `minimax_h3_pdd.py`
(11.3 KB) to implement that loop, against Diffusers' `ModularPipeline`
(`diffusers >= 0.40.0`). Our workflow samples with `SamplerCustomAdvanced` +
`euler` + `BasicScheduler`, which does not implement parallel decoding. So even
with keys remapped, ComfyUI would not reproduce PDD's intended behaviour.

**3. Wrong key format for ComfyUI.** No `diffusion_model.` prefix. Note the
size correspondence: lightx2v ships `bf16` at 1.38 GB (diffusers keys) AND
`comfyui_bf16` at 1.95 GB (ComfyUI keys). alibaba-pai's 1.37 GB matches the
diffusers side only — there is no ComfyUI variant.

## Scorecard

| | lightx2v (ours) | alibaba-pai |
|---|---|---|
| ref2v/ref2va support | yes | yes |
| steps | 8 | **8 (no gain)** |
| ComfyUI-format file shipped | **yes** (`comfyui_bf16`) | no (diffusers keys) |
| needs custom sampler code | no | **yes** (`minimax_h3_pdd.py`) |
| 768p-tagged | **yes** | not stated |
| date added | 2026-09-03 | 2026-08-26 |
| published settings | shift 12/3 documented | **none** |
| published speed numbers | none | none |

**Verdict: stay on lightx2v.** It is newer, 768p-tagged to our exact geometry,
ships a ComfyUI-format file, and needs no custom sampler. alibaba-pai offers
zero step reduction and would require both a key remap and a ComfyUI port of
PDD to even evaluate.

Worth noting in their favour: alibaba-pai *did* build a ref2va variant, and
their `results/` folder benchmarks against lightx2v's turbo 4-step 768p — so
they treat lightx2v turbo as the baseline to beat. If someone ports PDD to
ComfyUI, revisit for QUALITY at 8 steps, never for speed.

---

# Round 5 — `_bf16` vs `_comfyui_bf16`: what the headers say

Owner asked the difference. Read both safetensors headers by range request.
**Same LoRA, two key formats.** Not two models.

| | `..._768p_bf16` (1.38 GB) | `..._768p_comfyui_bf16` (1.95 GB) |
|---|---|---|
| tensors | 624 | 624 |
| dtypes | 624 BF16 | 416 BF16 + **208 F32** |
| declared format | `key_format: minimax-h3-diffusers` | `target_format: ComfyUI generic LoRA`, `source_format: Diffusers PEFT LoRA` |
| key prefix | none | **`diffusion_model.`** (all 624) |
| key style | `token_refiner.refiner_blocks.0.attn.to_k.lora_A.default.weight` | `diffusion_model.blocks.0.attn.qkv_proj.lora_A.weight` |
| adapter pairs | 312 A + 312 B | 208 A + 208 B (+208 `alpha` F32 scalars) |
| attention projections | **separate** `to_q` / `to_k` / `to_v` | **fused** `qkv_proj` |
| extra conversion | — | `swi_glu_mapping: Diffusers [value;gate] -> ComfyUI [gate;value]` |
| training provenance | `alpha: 8` | `training_rank: 128`, `training_scale: 0.0625` |

Both were trained once: rank 128, scale 0.0625 (= alpha 8 / rank 128).

## Why the ComfyUI one is bigger despite the same tensor count

ComfyUI's H3 implementation uses a **fused QKV projection**; Diffusers keeps
`to_q`/`to_k`/`to_v` separate. Three independent rank-128 deltas cannot be
folded into one rank-128 delta on the fused `[3*d_out, d_in]` matrix — the
conversion has to widen the adapter (a taller, partly-zero `lora_B`) to keep
the three sub-deltas independent. Fewer, larger tensors. Plus 208 F32 `alpha`
scalars, which cost nothing. That is the ~41 % growth.

## Which to use

**`_comfyui_bf16` — the one we already load.** Correct.

The plain `_bf16` in ComfyUI would match **zero** keys (nothing carries the
`diffusion_model.` prefix ComfyUI looks for) and would silently apply nothing —
it fails as a no-op, not an error. Worth knowing as a failure signature.

## This sharpens the alibaba-pai verdict

alibaba-pai's `Ref2VA-Acc-8Step` has `lora_down`/`lora_up` keys, **no**
`diffusion_model.` prefix, separate `to_q,to_k,to_v`, and `ff.net.0.proj` /
`ff.net.2` SwiGLU targets. So porting it to ComfyUI needs exactly the
conversion above: prefix, QKV fusion with adapter widening, the
`[value;gate] -> [gate;value]` SwiGLU reorder, and alpha scalars. lightx2v did
that work and shipped the result; alibaba-pai did not.

Scaling differs too: alibaba-pai is `lora_rank 64 / lora_alpha 64.0` (scale
1.0); lightx2v is rank 128 / scale 0.0625. A port could not reuse our
`strength_model: 1.0` unexamined.

---

# Round 6 — is the alibaba-pai LoRA better QUALITY? (owner dropped the speed question)

Downloaded all 9 ref2va demo videos from the repo's `results/` folder and
probed them. The comparison cannot answer the question, for two objective
reasons.

## Reason 1: their comparison renders lightx2v at HALF the pixels

| variant | rendered resolution |
|---|---|
| `ref2va_baseline_{1,2,3}` | **1344x768** |
| `ref2va_acc_8step_v1_{1,2,3}` (theirs) | **1344x768** |
| `ref2va_turbo_4step_v0.1_768p_{1,2,3}` (lightx2v) | **960x544** |

960x544 = 0.52 MP; 1344x768 = 1.03 MP. Exactly half. Systematic across all
three prompts, not a one-off. Their own model gets full resolution, the
competitor gets half. Whatever the intent, the comparison is not like-for-like.

Useful side effect: an independent third party ran the lightx2v ref2v 4-step
v0.1 at 960x544 — corroborating Round 3's inference from the missing `768p`
tag. It is a ~544p-era model. Our 768x1344 is out of its envelope.

## Reason 2: their comparison predates our LoRA entirely

They benchmark against lightx2v **turbo 4-step v0.1** (added 2026-08-13).
Our `ref2v_turbo_8step_v1.0_768p` landed 2026-09-03 — eight days AFTER
alibaba-pai published (2026-08-26). So their comparison set does not, and
could not, contain the LoRA we actually run. It compares their 8-step against
a 4-step at half resolution.

## What the demos do show

Extracted matched-timestamp frames, `baseline` vs `acc_8step` (both 1344x768),
full-frame and 100 % centre crop. PDD at 8 steps holds up well against their
own full-step baseline: two-person anatomy stays coherent, faces resolve,
garment texture is if anything finer than baseline; baseline retains slightly
more floor-tile texture. Frames are not content-aligned (a distilled model
does not track the baseline frame-for-frame), so this is an impression, not a
measurement.

Caveat that outranks all of the above: these are the authors' own
cherry-picked demos, rendered with their own pipeline. Author demos are the
weakest class of evidence.

## Verdict

**Unknown, and not answerable from published material.** No one has compared
alibaba-pai PDD 8-step against lightx2v ref2v 8-step v1.0 768p at equal
resolution. The only way to know is to run it — which requires the port below.

**Cost of finding out:** a ComfyUI key converter (prefix, QKV fusion with
adapter widening, SwiGLU `[value;gate] -> [gate;value]`, alpha scalars, and a
rank-64/scale-1.0 vs rank-128/scale-0.0625 rescale) AND a ComfyUI
implementation of PDD's parallel-decoding loop, which currently exists only as
`minimax_h3_pdd.py` against Diffusers `ModularPipeline`. Without the decoding
loop, loading the LoRA would not reproduce PDD at all.

**Recommendation: do not adopt.** Our LoRA is newer, 768p-matched, ComfyUI
native, and documented. The alibaba-pai path is a research project, not a
setting change.

## Possibly publishable (standing goal)

A ComfyUI custom node implementing **Parallel Decoding Distillation for
MiniMax-H3** plus a Diffusers-PEFT -> ComfyUI LoRA key converter for H3 does
not exist. The converter alone is generally useful — it unlocks every
diffusers-format H3 LoRA for ComfyUI users, and the fused-QKV adapter-widening
step is the non-obvious part. That is a standalone package, not a patch to a
vendored fork. Flagged, not started; it is off the episode critical path.
