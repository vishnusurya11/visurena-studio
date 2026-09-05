---
name: trailer-shots
description: Generating the clips - H3 constants, framing, camera, and the coverage economics.
---

# Shots

`studio/trailer_shot.py`, `scripts/trailer/build_clips.py`.

## Measured cost on a 4090

| | |
|---|---|
| one 10.1s clip (243f, 8 steps, 1344x768, r2v, 2 refs at `max`) | **~11.4 min** (mean 683s, range 650-781) |
| 1 minute of raw clip | ~67 min |
| 1 minute of finished trailer | ~87 min |

The finished-cut figure is higher because each take loses its first **2.6s** to
the reference leak, leaving ~7.5s usable.

**A second prompted shot in one generation is FREE** — 707s vs 683s, within
noise. Two setups for one render. Use `[Shot 2] At 00:05.000,` — marker first,
milliseconds required. `At 00:05.000, [Shot 2]` is off-spec.

## Setup economics — the repetition fix

Target **≤1.4 shots per setup**, most setups used once, max reuse 4. Shipped
trailers ran 3.0x and 3.8x with PERFECTLY UNIFORM reuse, which is the same
defect `is_uniform()` refuses for shot lengths, one level up and ungated.

Motif reuse and coverage reuse are OPPOSITE: a motif must be near-identical
framing to read as repetition; coverage reuse must start at a different moment
of the take or it reads as a stutter.

## The reference leak

H3's r2v path OPENS on the reference image and animates it — for ~2.1s the shot
is the character on the grey sheet backdrop — before entering the scene. That
is the binding working, held hard. `HEAD_TRIM = 2.6` discards it.

## Say how big the person sits in frame

Faces collapse in wides at ANY resolution; the driver is **head size in frame**,
not pixel count. Saying nothing about framing gets an establishing wide with a
small figure turned away — the first two bound clips read unmistakably as the
Criterion and as 221B, and in neither could you see who the person was.

`FRAMING` gives each register a shot size, tightening from a medium in the
quiet passages to head-and-shoulders on the hits.

## Camera

A closed vocabulary, written as prose with amplitude and speed: *"The camera
pushes in with small amplitude at slow speed."* Bracket syntax `[Push in]` is
the hosted Hailuo dialect and does nothing on H3. H3 drifts by default when the
prompt says nothing, so a static frame must be asked for.

Three moves per register, chosen by beat index — one move per register makes
every quiet shot the same slow push, and a slow drifting push is the most
recognisable tell of generated video.

## H3 constants — it rewrites illegal values silently

- `frames % 17 == 5`. Off-grid snaps UP. 243f = 10.1s is the efficient unit.
- **1344x768 is native AND the pixel cap**; canvas multiple is 32.
- fps 24 is a module constant, not a parameter.
- **8 steps, not 4** — at 4 the final Euler step drops sigma ~0.72 to zero, one
  step doing three quarters of the denoising.
- No CFG, no negative prompt. `BasicGuider` has neither — and an exclusion
  moved into the positive prompt is still a request for the thing it names.
  **Fill the slot instead**: name the occupant, the surface or the motion that
  takes the place of what you are excluding (`studio/affirm.py`, and the two
  measured failures in the parent SKILL).
- i2v resizes the start frame with `crop="disabled"` — a plain stretch.

## LoRA

The trailer renders with `minimax_h3_turbo_4step_ema_ckpt850` @0.8 (workflow
`video_minimax_h3_r2v_turbo`). That LoRA is **FL2V-lineage on a ref2va base**:
its own author "has not validated r2v quality", so identity retention through
it is unmeasured. Three Ref2V-lineage alternatives sit in
`models/loras/minimax_h3/`, all through `video_minimax_h3_r2v_turbo_lxref`
(dedicated LoRA node, sigma shift video 12 / audio 3):

| LoRA | steps | note |
|---|---|---|
| `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16` | 8 | lightx2v, 2026-09-03, ≤768p — matches our 8-step/736p config; users report it keeps references better |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` | 4 | lightx2v, earlier |
| `MiniMax-H3-Ref2VA-Acc-8Step` | 8 | measured **707s vs 683s — no speed gain**; cleaner look in an UNCONTROLLED probe (different seed and action line) |

A look in an uncontrolled probe is not evidence. The controlled A/B is
`scripts/trailer/lora_ab.py`: one beat, the same seeds through every variant,
scored by the gate's own metric (trait-card `distance` to the reference sheet,
bound = distance < DISTINCT_AT) and wall seconds, one JSON line per take in
`trailer/main/ab/ab.jsonl`. Local GPU only. Run it when no trailer is
rendering (it shares the GPU):

    uv run python -m scripts.trailer.lora_ab <codex_id> --beat B00 --seeds 3

Switch `build_clips.WORKFLOW` / `take_values` to a variant only on its
numbers; a take's recipe fingerprint names the workflow and LoRA, so a switch
re-renders every take (`render_or_reuse`).

OpenVDN's `vdn-minimax-h3` does not apply: text-to-video only (no reference
conditioning, which is our whole identity mechanism), licence excludes the USA,
and its headline 11.23s is 8x B200 distributed — single-GPU is 51s against 133s
dense, so ~2.6x per GPU, diffusers-only.
