---
name: trailer-assemble
description: The cut, the black, the sound design, the mix, and the gates - what goes where, and the ffmpeg defaults that lie about it.
---

# Assemble

`studio/trailer_assemble.py`, `trailer_cut.py`, `trailer_edit.py`, `sfx.py`,
`scripts/trailer/assemble.py`, `scripts/trailer/qc.py`.

**Measured** = run on this machine or corpus. **Reasoned** = follows from craft
sources or arithmetic, not measured here. Treat reasoned as the default to
beat, not as evidence.

## Order of operations

Most bugs here are an operation at the wrong point, not a wrong parameter.

1. Measure every clip's luma, pick the hero, derive one grade filter per clip
2. Resolve every shot to the take it will use, **then** count uses
3. Cut segments, conforming size/rate/pixfmt on the way out
4. Insert black spans as segments, kept OUT of the shot arrays
5. Render the card, **measure the card**, append
6. `concat -c copy`, then measure the real duration
7. Per source: conform, normalise, filter, place, automate
8. Sum with `normalize=0`, measure the **whole** graph once
9. One gain, one limiter, explicit `-t`, encode, tag colour
10. Write a manifest. Gate the FILE against the manifest.

## The cut

The arc: opens ~1.50s, RISES to 1.33s for a breath a third in, falls to a 0.54s
trough at 85-90%, then DECELERATES into a ~3.0s hold. It is a **diagnostic
prior, not a target** — no ASL makes a trailer better. Uniformity IS a defect,
and it is a generated pipeline's default because clips come back one size.

**Shape lives in the RATIOS, not the lengths.** `max/min >= 2.0` passes a
monotone ramp from 2.4s to 0.6s, which feels like nothing. Read `r = L[i+1]/L[i]`:

| ratio | reads as | use |
|---|---|---|
| 0.75-0.85 | building | 3-5 in a row inside a phrase |
| < 0.70 | stutter | an accent, never twice running |
| 0.90-1.10 | plateau | max 6 in a row, early only |
| > 1.50 | **reset** | at phrase boundaries, >=3 per trailer |

**Reasoned, and load-bearing:** a sequence builds because it accelerates *and
then resets long*. The ear normalises to a tempo in about four events, so
continuous acceleration flattens into a new steady state — you get faster and
it feels the same. The reset re-establishes the reference the next acceleration
is measured against.

**The phrase is the unit, not the shot.** 5-8 phrases of 3-5 shots sharing a
subject, place or idea. Cut within a phrase on connection; cut between phrases
with a change of state — a length reset, a black, a designed hit, or a change
of camera direction. One per boundary, not all four.

Camera direction is a boundary signal you already own, since every shot's move
is in the plan. Push into push continues energy; push into static is a brake and
reads as a full stop whatever the lengths do.

**The hold:** one shot >=3x the median. A trailer's credibility comes from the
one shot it was willing to stay on. First third or the button, never in the
80-90% band.

**The accent:** <=0.5x its neighbours, landing on a measured onset. 2-4 per
trailer, never adjacent. An accent landing on nothing in the envelope is a
dropped frame.

**Two adjacency rules no length gate catches:** never place two adjacent shots
from the same take (they read as one shot with a jump cut in it), and a motif
needs three appearances — two reads as an accident.

## The grade

The prompt buys intent, not exposure: a verbatim grade string in every prompt
still gave clips spanning **11.9 to 48.4** luma. Match to one hero — the median,
floored at **32** — matching spread as well as mean, because correcting
brightness alone leaves flat clips flat.

The floor is 32 because the corpus median is **28/255** with a 5th percentile of
3.2. Trailers ARE dark; a floor of 58 washes out the gloom the material wants.

## Black is a layer, not an absence

The corpus sits at 28/255 mean luma with a 5th percentile of **3.2** — at least
one frame in twenty is essentially black. We currently generate exactly one
black span, by accident of the title card being on black.

**Dips to black create separation; cuts create connection.** So black belongs
where the sentence ends, between phrases, never between two shots that belong to
each other. A dip inside a phrase is a stammer.

| span | frames @24 | reads as |
|---|---|---|
| blink | 2-4 | a flinch, an impact |
| beat | 6-12 | phrase boundary, a breath |
| hold | 20-36 | a full stop |
| dead | >48 with silence | a playback failure |

**Black with sound is suspense. Black with silence is an ending.** Both together
happen exactly once, before the title, and only because the cue does it too.
Anywhere else the audience checks their connection.

Budget 3-6s across 90-120s, in 3-5 events (~4% of runtime). Measure the
delivered file: `blackdetect=d=0.05:pix_th=0.10`.

**Cut to black, do not fade to it.** A fade is a dissolve and reads soft. Note
the card already does the right thing: the TYPE fades, the PICTURE cuts.

Three failures, in the order you will hit them:

1. **Black corrupts the shot statistics.** A 0.25s span entering `lengths` makes
   it the min, inflates `max/min`, and can flip `is_uniform`. Keep blacks in a
   separate array; compute length gates from picture shots only.
2. **Black doubles the scene-cut count.** `scene_cuts()` sees a cut to black and
   a cut back as two changes — six spans inflate by twelve, 40% of the 29 cuts
   measured in the first trailer. Subtract `2 * len(blacks)`.
3. **The black is not the same black.** `color=c=black` in `yuv420p` gives luma
   16 (limited range); a full-range clip gives 0. Cutting between them flashes.

## Sound design is a pass, not a filter

**Budget: 3-5 designed events in 90-120s.** It is free to synthesise a hit, so
the default failure is one per cut — and a trailer with eleven impacts has none,
because an impact is a contrast and a contrast against a floor of impacts is
nothing.

**A designed event marks a turn in the story or a reveal in the picture.** A cut
does not earn one. The tell of a stock sound pack is a hit on the seventh cut
for no reason but that the cut was there.

**A synthesised hit reinforces a MEASURED cue impact; it never invents one.**
`structural_impacts()` returns where the cue actually jumps. A hit against a flat
bed reads as SFX layered on a trailer; the same hit on the cue's own jump reads
as the film hitting. Never on the first cut — there is no floor yet to be a peak
above.

**Three elements, three jobs, not interchangeable:**

- **`sub_drop` is a lead-IN.** Starts before the event, lowest point on the cut.
  Pressure, not an event.
- **`riser` is a lead-IN with a deadline.** Its peak is its last sample, so place
  it at `cut - seconds` and TRUNCATE at the cut. A riser continuing past the cut
  tells the audience the cut was not the event.
- **`impact` is the event.** Sample-exact on the cut frame.

Never stack a riser and a sub-drop on one event — same seconds, same function,
two lead-ins make one muddy one. Alternate them: sub-drop for dread, riser for
velocity.

**The five-layer impact.** We synthesise three; the two missing are what make a
hit sound expensive:

| layer | band | envelope | starts |
|---|---|---|---|
| tick | 2-6 kHz | `exp(-300*t)` | t=0 |
| body | 80-400 Hz | `exp(-7*t)` | t=0 |
| sub | 48→16 Hz | `exp(-1.4*t)` | t=0 |
| **tail** | LPF 1.2k noise | `exp(-2.2*t)` | t=0 |
| **pre-swell** | reversed tail+body | `areverse` | ENDS at t=0 |

**No tick and the hit reads LATE even when sample-exact**, because the ear times
a transient by its high-frequency edge — this gets misdiagnosed as a sync
problem. **No tail and the hit happened in a box**; tail length IS the scale
control (0.8s a room, 1.8-2.4s a cathedral, >3s eats the next shot). "Sounds
like a stock pack" almost always decodes to "has no tail". **No pre-swell and
the hit is sudden rather than inevitable** — that layer is what separates a
sound effect from sound design.

**The hit is made by the silence in front of it.** 0.4-0.8s before, the bed
drops 6-9 dB and releases exactly on the hit. But check whether the cue already
does it — `title_moment()` only returns an impact with a stopdown in front, so
the title event is always in the already-done case, and a second dip there is
the double-breath that reads as a mastering error.

**If placement must be wrong, be wrong LATE.** ITU-R BT.1359 puts detection at
~45 ms for audio leading picture and ~125 ms lagging — the ear expects sound
after light. At 24fps that is 1 frame early vs 3 frames late.
