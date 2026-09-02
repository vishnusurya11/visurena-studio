---
name: trailer
description: Cut a trailer for a book that has a screenplay - reference-bound shots, music-driven timeline, measured cut arc. Use when building or fixing a trailer, song video, or episode from library/<book>/.
---

# Trailer

A trailer for a book we have already adapted. Everything here is downstream of
two bricks; if you only remember two things, remember these.

## Brick 1 — identity is BOUND, never described

A prompt naming Holmes is not evidence that Holmes will appear.

The 2026-08-25 trailer generated twelve excellent reference sheets and then
rendered every keyframe with `image_krea2_turbo_draft` and **no image input at
all**. Nothing in the chain ever told the model that Holmes looked like
anything. The result: a different man in every shot. The episode chain in the
same repo *did* bind (`ref_image_1: __SH-char-watson__`) — so this was never a
missing capability, only a missing wire.

**The rule: a shot that shows a character carries that character's reference
image, and a shot that cannot is a failing shot.** `ShotSpec.unbound_cast()`
asks what the JOB will carry, never what the prompt says. `build_plan.py`
refuses a plan with any unbound shot rather than rendering it and hoping.

Two corollaries, both measured:

- **A shared seed does NOT hold identity.** Two stills at identical seed
  777777 with an identical style block returned a different person, a
  different horse, and a different banner. The seed fixes the noise, not the
  semantics — everything the prompt leaves unspecified is re-rolled. Seed
  locking holds *layout*. Use a **different seed per shot**; a shared one was
  measured to drift face and voice.
- **Both layers are needed.** The reference pins the instance; the character's
  physical description, repeated verbatim in every shot prompt, pins the
  category. Drop either and the face drifts.

Never put an audio reference in a shot where the face matters: identity
similarity collapses 0.886 → 0.088, and no amount of steps or reference
sizing recovers it.

## Brick 2 — the music is the timeline, and the timeline is MEASURED

Generate the cue first, then measure what it actually plays, then cut to that.

The old assembler cut its title card at 75.21s when the cue's own +37 LU
impact was at 80.5s — the braam landed two seconds *into* the button shot. It
had also inherited a 4.0 LU wall-of-sound bed instead of the 9.7 LU cue,
purely because `SH-cue-action_*` sorted first in a glob. **File order chose
the trailer's entire dynamic shape.**

`studio/beatmap.py` decodes the audio and reads its envelope directly:
`onsets()` gives the candidate cut grid, `structural_impacts()` the few big
hits, `stopdowns()` where the floor drops out, `title_moment()` the late hit
with silence in front of it. Cues are chosen by `trailer_fitness()`, never by
filename.

Do not scrape ffmpeg's `ebur128` log for this. An earlier version did, this
build prints only a summary, and the parse returned `[]` — which callers
reported as "0 impacts". `envelope()` now raises rather than returning
nothing. **A measurement that cannot fail is not a measurement.**

## The cut

Measured across 50 released trailers (Redfern's US Horror data set, CC-BY):
median shot length opens ~1.50s, **rises** to 1.33s for a breath around a
third in, accelerates to a 0.54s trough at 85–90%, then **decelerates** into a
final hold of ~3.0s. Loudness peaks in the same 80–90% band and collapses in
the last tenth. Both arcs agree; that collapse is the stopdown before the
title.

Note the shape is not "shots get shorter throughout" — the first half is flat
(Q1 1.06s, Q2 1.07s) and all the acceleration is in the second half (Q3 0.73s,
Q4 0.63s).

**The arc is a diagnostic prior, not a target.** Lieu is explicit that no
average shot length makes a trailer better or worse. Generate to the story,
then check against the arc and investigate deviations.

**What IS a defect is uniformity.** Every shot the same length is the single
most-named amateur tell, and it is a generated pipeline's *default* output,
because the model hands back clips of one fixed size. `assemble.py` refuses a
cut whose shot lengths are all equal.

### Register

| | action/horror | literary (use this for a canonical text) |
|---|---|---|
| structure | 6 sections, escalating | mood map; may have no climax |
| shot length | 1.5 → 0.54 → 3.0s | the same shape, stretched ~2.5x |
| music | 2–3 cues, drop at 80–90% | **one cue, whole** |
| voice | dialogue fragments | **no voice-over at all** |
| sells | the withheld how/why | tone, faces, a world |

A canonical text has no spoiler to protect. Barry Jenkins on the *Moonlight*
trailer: *"you don't have any damn clue what that movie is about. But you know
exactly what it feels like."* That is the job here.

### The repeated motif — a feature, not a compromise

A short in-world action repeated as the rhythm bed is a named prestige device
(Woollen's chalkboard in *A Serious Man*; Garrett calls diegetic percussion
the defining technique of the past decade). It is also the cheapest thing this
pipeline can render. **It converts the fixed-clip-length problem from a tell
into an intention.** Reuse beats deliberately — but start each use at a
different moment of its take, or repetition reads as a stutter.

Straight cuts by default. "Dips to black create separation, cuts create
connection" — a dissolve must mean something.

## The sound

**Generate the diegetic layer; SYNTHESISE the designed layer.**

Asked for a "deep ominous impact boom", Stable Audio 3 returned a mid-heavy
thump measured **12.7 dB short of sub** (≤60 Hz peak −15.5 dB against −2.8 dB
in the mids). Every "deep", "sub" and "chest-heavy" adjective was ignored
below 120 Hz. That is a training-distribution ceiling and it is exactly the
band a trailer lives in.

`studio/sfx.py` synthesises the braam/riser/sub-drop with ffmpeg. Measured
here: `sub_drop` −2.2 dB below 60 Hz against −14.7 dB above 120 Hz — the exact
inverse of the generated boom. It is also sample-exact (so the cue lands on
the frame you cut it to) and deterministic (so the trailer rebuilds
identically tomorrow).

Mix: two-pass `loudnorm` — single-pass runs in *dynamic* mode and reshapes the
dynamics you chose the cue for. Land at −14 LUFS / −1.0 dBTP; the old trailer
measured −0.03 dBTP, a dB over the EBU R128 ceiling. `alimiter` is sample-peak,
so `limit=0.891`. Pin `-ar 48000`.

If there is dialogue, duck the bed 12–15 dB, 4 frames down and 20–30 frames
up. Absent ducking is "one of the surest signs of a less experienced editor."

## Hard constants — MiniMax-H3 rewrites illegal values silently

From `comfy_extras/nodes_minimax_h3.py`, encoded in `studio/h3.py`:

- **`frames % 17 == 5`.** Off-grid counts snap UP. 243f = 10.1s is the
  efficient unit.
- **1344×768 is native AND the pixel cap**; canvas multiple is **32**.
  Anything larger is silently area-scaled back.
- **fps 24 is a module constant**, not a parameter.
- **8 steps, not 4.** At 4 steps the final Euler step drops sigma from ~0.72
  straight to zero — one step doing three quarters of the denoising. That is
  the arithmetic behind "mushy" and "motion smear".
- **No CFG, no negative prompt.** `BasicGuider` has neither. Put negations in
  the positive prompt; there is nowhere else.
- i2v resizes the start frame with `crop="disabled"` — **a plain stretch**. A
  keyframe at the wrong aspect is distorted, then animated. Match exactly.

Camera language is a closed vocabulary written as prose with amplitude and
speed ("pushes in with small amplitude at slow speed"). `[Push in]` bracket
syntax is the *hosted Hailuo* dialect and does nothing on H3. H3 drifts by
default when the prompt says nothing about the camera, so always say something.

## Order of work

1. `build_refs.py` — reference sheets, from `analysis/` so they answer to the
   book. They belong to `library/<book>/refs/`, shared by trailer, song and
   episode: a character who looks one way in the trailer and another in
   episode one is two characters to the audience.
2. `build_music.py` — several seeds, chosen on measured fitness.
3. `build_plan.py` — beats from the screenplay, cut to the measured grid.
   **Refuses unbound shots.**
4. `build_clips.py` — one long take per beat, reference-bound. ~17 min each.
5. `assemble.py` — cut, title on the measured hit, synthesised sound, mix.

Cost: zero. Everything is local GPU; no paid API is involved at any step.

## Observed on the first bound run — read before the next one

**The reference leak is real and it is the binding working.** H3's r2v path
opens on the reference image and animates it — for ~2.1s the shot is the
character standing on the grey sheet backdrop — then moves into the scene.
Every take gives up its first 2.6s (`HEAD_TRIM`). Budget for it: a 10.12s take
yields ~7.5s of usable footage.

**Character binding is much stronger than location binding.** With
`char-*` on `ref_image_1` and `loc-*` on `ref_image_2`, the person is held
hard and unmistakably; the place is *blended*. A bar interior plate plus the
slug name "the Criterion Bar" produced an arcade carrying the bar's tables and
gaslights. Treat the location ref as a palette and texture cue, not a set.

**H3 invents lettering even when told not to.** The Criterion plate contains
no text whatsoever, and the rendered clip still put "CRISTERION" on a sign.
`NO_TYPE` is in every prompt and did not prevent it. At 1.4–4s a shot this is
usually below notice; do not spend renders fighting it. If a word must be
legible, F12 is the rule: typeless plate, composite the type in post.

**Location plates come back populated.** `PLATE_FRAME` says "no people, no
figures" and the Criterion plate returned a room full of drinkers. It happens
to flatter this location, but it means those extras can bind into shots. If a
plate must be empty, verify it rather than trusting the prompt.
