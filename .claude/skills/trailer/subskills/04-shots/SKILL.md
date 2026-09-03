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
- No CFG, no negative prompt. `BasicGuider` has neither; negations go in the
  positive prompt.
- i2v resizes the start frame with `crop="disabled"` — a plain stretch.

## LoRA

`MiniMax-H3-Ref2VA-Acc-8Step` is matched to the r2v path; the `ckpt850` line is
FL2V-family. Measured **707s vs 683s — no speed gain**. Quality looked cleaner
in an UNCONTROLLED probe (different seed and action line); a real A/B is
outstanding.

OpenVDN's `vdn-minimax-h3` does not apply: text-to-video only (no reference
conditioning, which is our whole identity mechanism), licence excludes the USA,
and its headline 11.23s is 8x B200 distributed — single-GPU is 51s against 133s
dense, so ~2.6x per GPU, diffusers-only.
