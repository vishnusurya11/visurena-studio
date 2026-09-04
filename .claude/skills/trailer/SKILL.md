---
name: trailer
description: Cut a trailer for a book that has a screenplay - reference-bound shots, music-driven timeline, measured cut arc. Use when building or fixing a trailer, song video, or episode from library/<book>/.
---

# Trailer

## Run it — the blind path

```
uv run python trailer.py <codex_id>
```
One command, one 6-hour ceiling, zero credits, no questions. Read
`library/<book>/trailer/main/qc.json` and `learnings.jsonl` afterwards.
The contract every step honours — input, output, gate, adapt ladder,
fallback, time share — is `BLUEPRINT.md`; what is built vs proposed is
`BUILD.md`; the registry is the `trailer` stage of `stages.yaml`. Everything
below this line is for the agent that BUILDS or FIXES a step, not the one
that runs it.


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

## Brick 2 — the cut is a METRIC object; cut on the grid the music actually keeps

Generate the cue first, then measure what it actually plays — its **metre**
(beats, downbeats, bars) and its **events** (hits, stopdowns, slots) — select
the seed on that structure, and cut in beats. Break the grid only where the
music breaks it.

**MEASURED 2026-09-03:** the delivered Scarlet cut had 35 of 44 cuts "on an
onset" and, tracked against the music's own beat, **12 of 44 on a beat and 4
of 44 on a downbeat** — about 2× chance for both. `onsets()` is a loudness
grid; it has no bar. The full rule, the seed fitness with metric and slot
terms, the beat walk that respects `MIN_SHOT` and the cap at 60–180 BPM, the
instrumental and vocal sheets, and the instrumental-vs-vocal eligibility rule
are in `subskills/03-music`. The history below is why measurement exists.

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

## Brick 3 — a trailer line needs no scene and takes a side

The iconic *moment* is the same thing in pictures: an image that needs no
scene and changes the story. Neither is a property of the text. Both are
**what a culture kept**, so external evidence (Wikiquote, revid-keyed — 30 of
30 analysed books resolve, median 18.5 quotes) outranks every text feature,
and the text features are the floor for the book nobody kept — graded on a
held-out corpus, never on themselves.

**MEASURED:** the previous `line_value` scored 26 of 38 real trailer lines
negative ("This is Sparta!" −7.6, every question −6.6) and put a Ferrier
errand above all of them, because it penalised the two features that define
the format — short, and a question a later line answers. And the screenplay is
the wrong pool: 4 of Scarlet's 19 kept quotations survived adaptation; the
title sentence lives only in `source/chapters/`. Finder, scorer, ordering and
the moment features are in `subskills/05-dialogue`.

## The coupling rule — a line is a shot

A line is bound to its speaker's picture (Brick 1), occupies whole beats in a
measured slot (Brick 2), and is chosen *for the slot it fits* — never
compressed into one. `lines = min(slate, measured_slots)`, cap 4. Its voice is
bound by a reference clip, never described per line (`subskills/09-voice`), and
its duration is read from the rendered file, never predicted.

The trailer is the fold of the timing rule over the cue's events plus slots,
the slots filled from the oracle's ranked list in hook → answer → threat →
title → button order. Every pipeline stage has a check that can fail on the
DELIVERED file, not on the plan — a gate whose expectation is derived from the
thing it checks cannot fail. Build order and status: `BUILD.md`.

## Subskills

Read the one you need; each carries what was measured rather than assumed.

| | |
|---|---|
| `subskills/01-story` | lead, opposition, turn, what stays unanswered, element-level selection |
| `subskills/02-refs` | reference sheets, identity binding, character collision |
| `subskills/03-music` | metre + events, seed fitness, the beat walk, instrumental and vocal sheets |
| `subskills/04-shots` | H3 constants, framing, camera, coverage economics, costs |
| `subskills/05-dialogue` | four pools, Wikiquote iconicity, the held-out scorer, ordering, slots, moments |
| `subskills/06-style` | the house look and how to try others |
| `subskills/07-cards` | title cards, typography, and two silent failures |
| `subskills/08-assemble` | the cut, the grade, the mix, the gates, three ffmpeg traps |
| `subskills/09-voice` | Qwen3-TTS: design once, clone every line, gate on similarity, measure seconds |

## Agents

| | |
|---|---|
| `trailer-story` | structure and selection, before any render, spends nothing |
| `trailer-art` | reference sheets and visual register |
| `trailer-cinematographer` | the clips, ~11 min per setup |
| `trailer-editor` | cut, grade, mix, cards, QC — free, iterate here |


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
2. `build_music.py` — several seeds, chosen on measured fitness: metre,
   tempo, title-on-downbeat, lift, **slots**, late reach.
3. `build_plan.py` — setups from the screenplay's authored shots; cuts from
   the beat walk over the cue's metre and events; the line slate from the
   four pools, ordered hook → answer → threat → title → button.
   **Refuses unbound shots and a slate with no hook.**
4. `build_voice.py` — design one reference per speaking character, clone
   every line, gate on similarity, write measured seconds. Lines are then
   chosen for their slots.
5. `build_clips.py` — one take per setup, reference-bound. ~11 min each.
6. `assemble.py` — cut, title on the measured hit, the line layer ducked
   6 LU, synthesised sound, mix; QC on the delivered master.

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

## Content bugs no mechanical gate will catch for you

Every gate in this pipeline passed a plan for *A Study in Scarlet* that
contained no Sherlock Holmes and rose to no climax. The plan was fully bound,
correctly cut, properly graded — and for a different story. **A check gates
only what it measures.** Three that had to be added:

- **Bind the story's lead, not `cast[0]`.** Rank characters by presence across
  the whole book (`leading_characters`) and bind the most central one present
  in each scene. Refuse a plan where the lead appears in almost no beats.
- **Take the arc position from the BEAT index, not the scene index.** Eleven
  beats over twenty-two scenes caps position at 0.48, below the `hit`
  threshold, so every beat comes back `quiet` or `build` and nothing peaks.
  Refuse a plan missing any register.
- **Choose reference sheets by story-wide ranking, not by sampling scenes.**
  Sampling gave *Jekyll and Hyde* a reference set with no Henry Jekyll — he
  ranks second in the book but did not speak in the twelve scenes drawn — and
  spent a sheet on Enfield, who ranks sixth.

Sampling was wrong twice for the same reason: **a sample of scenes is not a
measure of centrality**, and centrality is what a trailer needs.

Two more coherence rules, cheap and worth it:

- **The action line must feature the character the shot is bound to.** Holmes's
  reference under the line "Gregson sits in the arm-chair" tells the model two
  different things about who is on screen. Preferring a line that names the
  bound character also happens to land the book's own famous opening.
- **Character COLLISION is the identity problem wearing different clothes.**
  Where a book never describes anyone, generating from the profile alone gives
  every character the same generic prompt and therefore the same face. Use the
  book's epithets — "the solemn butler", "the lawyer", "a little man" — which
  are the author describing someone in the fewest words they thought necessary.

## The free win not taken this run

A second angle **inside one H3 generation is free** — measured 631s for a
243-frame two-shot clip against 690s for a single-shot one, the same within
noise. The prompt grammar for it is `[Shot 2] At 00:05.000,` (marker first,
milliseconds required; `At 00:05.000, [Shot 2]` is off-spec and is still wrong
in several job files in the older repo).

This run rendered one continuous take per beat, so eleven beats bought eleven
setups. Prompting two shots per generation would have bought twenty-two for
the same GPU time, which is the single largest quality-per-second lever
available — a trailer's problem is always variety.

The catch is that H3 chooses the exact cut frame, so the clip must be cut on
its own internal boundary rather than on the music grid. The workable shape is
to prompt the second shot, then let `beatmap`'s onset grid pick which side of
the internal cut each trailer shot comes from — treat it as two takes in one
file, not as a pre-cut sequence.

## H3 generates audio, and this pipeline throws it away

The base checkpoint is `fl2va` — first-last to video **and audio** — so every
clip arrives with a diegetic track (measured −39.8 LUFS on a rendered take).
`extract()` drops it with `-an`.

That is defensible: trailer practice is to discard production audio and
rebuild, and a literary-register cut is carried by one music cue. But it is
free material. The shape worth trying is the standard priority stack —
narration, dialogue, **source audio**, music, added SFX — with the clip's own
track sitting low under the bed and ducked, so a door or a carriage lands
under the music instead of the bed carrying every moment alone.

Do not mix it in flat. Levels across generated takes vary by roughly the same
spread as generated speech, so each take needs its own gain before the mix,
and the ducker threshold is an ABSOLUTE level — per-source normalisation has
to happen before it, not after.

## Two ffmpeg traps that cost hours

**`alimiter` re-levels by default.** Its auto-level is ON, so it limits and
then pushes the result back up. Tightening the limit made the mix *louder* —
peaks went −0.55 → +0.53 → +0.95 dBTP across three attempts while I lowered
the ceiling each time. **Always `alimiter=limit=N:level=disabled`.**

Peaks rising as the limit falls is not a tuning problem; it means the model of
the chain is wrong. Measure the *sources* at that point, not the chain. Doing
so found the rest of it: the MiniMax bed arrives at **0.00 dBTP**, already
clipping, and a synthesised impact measured **+0.72 dBTP** before anything was
mixed with it. No sample-peak limiter downstream can bring that sum under a
*true*-peak ceiling — headroom has to exist at the source.

**The mix never terminates.** `apad` makes the bed an infinite stream, `amix`
defaults to `duration=longest`, and `-shortest` does not reliably bound a
filter-graph output. It ran for 45 minutes at a fixed byte count across two
attempts, and I misread it once as slow and once as dead. **Bound the output
with an explicit `-t`** at the picture's measured duration; the same mix then
finishes in 2 seconds.

A process that neither finishes nor errors is the hardest failure to read,
because every check short of "did it terminate" returns something reassuring.

**On loudness generally:** do not chain normalisers. `loudnorm` only enters
linear mode when `measured_LRA <= target_LRA`, and a trailer cue's range is far
wider than the default 7 LU, so it silently falls back to dynamic and re-gains.
Measure once, compute one gain, apply it, and keep a disabled-auto-level
limiter as a net rather than as the mechanism.
