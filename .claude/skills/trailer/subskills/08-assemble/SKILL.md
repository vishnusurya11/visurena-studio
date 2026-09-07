---
name: trailer-assemble
description: The cut, the black, the sound design, the mix, and the gates - what goes where, and the ffmpeg defaults that lie about it.
---

# Assemble

`studio/trailer_assemble.py`, `trailer_cut.py`, `sfx.py`,
`scripts/trailer/assemble.py`, `scripts/trailer/qc.py`.

**Measured** = run on this machine or corpus. **Reasoned** = follows from craft
sources or arithmetic, not measured here. Treat reasoned as the default to
beat, not as evidence.

## Order of operations

Most bugs here are an operation at the wrong point, not a wrong parameter.

1. Measure every clip's luma, pick the hero, derive one grade filter per clip
2. Resolve every shot to the take it will use, **then** count uses
3. Cut segments, conforming size/rate/pixfmt on the way out
4. Insert black spans as segments, kept OUT of the shot arrays — UNBUILT; the
   only `color=c=black` in the stage is the card's (`trailer_assemble.py:224`)
5. Render the card, **measure the card**, append
6. `concat -c copy`, then measure the real duration
7. Level each line, **write the level sheet** — `mix_with_lines` writes it at
   `:681`, before the bed is shaped and before a sample of the master exists
8. Per source: conform, normalise, filter, place, automate
9. Sum with `normalize=0`, measure the **whole** graph once
10. One gain, one limiter, explicit `-t`, encode, tag colour — the gain
    bounded by the PEAK, not by the target (see The master gain)
11. Gate the FILE against `plan.json` and that sheet — a sheet written five
    operations before the file, which is the whole reason it is an intention
    and not a measurement. No manifest here: the pipeline's step 10 writes it
    AFTER the gate, cut-list-free.

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

One frame in twenty of the corpus is essentially black (5th percentile 3.2,
above). We generate exactly one black span, by accident of the title card being
on black.

**Dips to black create separation; cuts create connection.** Black belongs where
the sentence ends, between phrases, never between two shots that belong to each
other. A dip inside a phrase is a stammer.

| span | frames @24 | reads as |
|---|---|---|
| blink | 2-4 | a flinch, an impact |
| beat | 6-12 | phrase boundary, a breath |
| hold | 20-36 | a full stop |
| dead | >48 with silence | a playback failure |

**Black with sound is suspense. Black with silence is an ending.** Both together
happen exactly once, before the title, and only because the cue does it too.

Budget 3-6s across 90-120s, in 3-5 events (~4% of runtime). **Cut to black, do
not fade** — a fade is a dissolve and reads soft; the card already does this
right, the TYPE fades and the PICTURE cuts.

UNBUILT, and honest about it: nothing places a black span and no `blackdetect`
runs in `qc.py`. Three failures wait for whoever builds it:

1. **Black corrupts the shot statistics.** A 0.25s span entering `lengths` makes
   it the min, inflates `max/min`, and can flip `is_uniform`. Keep blacks in a
   separate array; compute length gates from picture shots only.
2. **Black doubles the scene-cut count.** `scene_cuts()` sees a cut to black and
   a cut back as two changes — six spans inflate by twelve, 40% of the 29 cuts
   measured in the first trailer. Subtract `2 * len(blacks)`.
3. **The black is not the same black.** `color=c=black` in `yuv420p` gives luma
   16 (limited range); a full-range clip gives 0. Cutting between them flashes.
   Detect with `blackdetect=d=0.05:pix_th=0.10`.

## Sound design is a pass, not a filter

**Budget: 3-5 designed events in 90-120s.** Synthesising a hit is free, so the
default failure is one per cut — and a trailer with eleven impacts has none,
because an impact is a contrast and a contrast against a floor of impacts is
nothing. **A designed event marks a turn in the story or a reveal in the
picture**; a cut does not earn one.

**In the body, a synthesised hit reinforces a MEASURED cue impact and never
invents one** — a hit against a flat bed reads as SFX layered on a trailer, the
same hit on the cue's own jump reads as the film hitting. Never on the first
cut: no floor yet to be a peak above.

**The button is the exception, deliberately.** With shots never reused the
picture ends BEFORE the cue's title hit (run 10: `title_impact None` on every
seed of every caption), and chasing a hit the cue may not have is how the card
came to be held over a bed already faded to −46 LUFS. So there the event is
MADE, not found: bed STOPS on the last cut, room tone runs the held breath, the
impact lands while the card is alive. MEASURED `title_hit_lu −13.0`,
`pre_title_silence_s 1.7` (asked 2.2). **Half a second of that is arithmetic and
only 0.4 of it is ebur128's window:** `qc._runs` names a stretch by its FIRST and
LAST sample, so N readings 100 ms apart measure (N−1)×0.1 — one sample short of
what they cover, on every duration this stage reports. `PRE_TITLE_SILENCE`'s own
note predicts 2.0 s → 1.6 from the window alone and MEASURED 1.5; the last
music-only gap, 6.290 s with no window at either edge, reads **6.2**.
**A constant tuned against a biased measurement is where the bias then lives**:
2.2 is 1.5 asked + 0.4 + 0.1 + 0.2 of margin. `assemble` calls
`trailer_cut.title_moment` (arithmetic on the last cut, detecting nothing) and
**never `structural_impacts()`** — `beatmap`'s impact-with-a-stopdown belongs to
the music step.

**The floor under a silence goes where the silence IS, not where the arithmetic
put one.** `designed_layer` (`scripts/trailer/assemble.py:37-50`) takes
`hard_out`, `hit` and `seconds` and nothing else, so the only room tone in the
trailer is the one the last cut implies; it never reads the cue plan, and the
cue plan is where the silences are typed. MEASURED, momentary, on the delivered
Scarlet master: mean **−89.3 LUFS across 35.5–40.8 s** and **−85.8 across
64.6–70.0 s**. The shaped bed reads −85.9 / −82.3 over the same spans, so the
mix did not make the holes — `music/plan.json` carries `trough` spans at
**35.019–40.859** and **64.178–70.018**, 5.84 s each; `cue_qc.HOLDS` forbids
cutting inside one (`cue_qc.py:20`), so step 06 lays exactly ONE shot across
each (shot 12 35.000→40.875, shot 17 64.167→70.000) and 08 puts nothing under
them. **A trough is a silence the trailer CHOSE**, and the design's answer to
one is a line: this cue has three troughs and four line windows, the 1.15 s
trough got one (21.68–23.99) and the two 5.84 s troughs got none. `room_tone`'s
own note names the fault — "digital silence … a dropped stream is what that
sounds like: a fault, not a held breath" — and it is laid across the 6.7 s of
button and across none of the 11.7 s of body that needs it. Room tone belongs
under every trough the plan already names; no detector is needed. QC cannot see
it: `cue_qc.lines_in_troughs` asks whether every LINE sits in a window, never
whether every window has a line, and returns **1.0 for zero lines** while
sitting in the cue FLOOR (`cue_qc.py:82`, `trailer_stage_spec.py:246`) — run 18
scored it 1.0 with two troughs empty.

**Three elements, three jobs, not interchangeable:**

- **`sub_drop` is a lead-IN.** Starts before the event, lowest point on the cut.
  Pressure, not an event.
- **`riser` is a lead-IN with a deadline.** Its peak is its last sample, so place
  it at `cut - seconds` and TRUNCATE at the cut. A riser continuing past the cut
  tells the audience the cut was not the event.
- **`impact` is the event.** Sample-exact on the cut frame.

Never stack a riser and a sub-drop **on a body event** — same seconds, same
function, two lead-ins make one muddy one. Alternate them: sub-drop for dread,
riser for velocity. `designed_layer` does stack both at the hard out (riser
2.5 s, sub 2.4 s, both ENDING on the last cut); nothing grades the button's
texture, so treat that as an unverified exception and mud anywhere else.

**Count WHERE the events are, not how many.** All four designed cues sit in the
last ~8 s, so the body carries **none** while "3-5 events" reads as satisfied —
**and that placement pins the loudest moment to the last frame of picture.**
Both lead-ins are peak-limited to `sfx.HEADROOM` 0.70 and summed `normalize=0`
onto a bed still at `BED_TP` −1.0 there: `bed_expr`'s windows come from the
LINES only, so nothing ducks the bed under a designed cue. MEASURED, run 18:
`peak_position` **1.0** against 0.78–0.92; it reports a plateau where it BEGINS,
so the loudest short-term window inside the picture starts within 0.05 s of the
last cut (hard out 99.2 s, picture 99.208 s) with both lead-ins inside its 3 s.
**That flag is 08's and no cue can move it** — step 03's ride finishes its climb
on the bar before the stop, so the music peaks there too, and a climax reads as
0.85 only because something comes AFTER it. **Only one end is available.**
`peak_position`'s window is already `[3.0, picture)` with `picture` the last
CUT (`qc.py:423,435`), so the card, the hit and all but 8 ms of the room tone
sit OUTSIDE it already and what is inside is the two lead-ins; MEASURED, the
loudest short-term reading in that window is its LAST sample, 99.1999 s at
−11.0 LUFS. Excluding more means excluding the last cut. The fix is lead-ins
that FINISH before it.
**Reasoned, not measured: which of the ride and the lead-ins owns the peak.**

**The five-layer impact.** Three branches render, two layers are missing, and
one branch is not the layer it stands for:

| layer | band | envelope | in `sfx.impact` (`sfx.py:69-80`) |
|---|---|---|---|
| tick | 2-6 kHz | `exp(-300*t)` | **no** — UNSEEDED white noise, HPF 1.2 kHz, `exp(-38*t)` |
| body | 80-400 Hz | `exp(-7*t)` | 90 Hz sine, HPF 70 |
| sub | 48→16 Hz | `exp(-1.4*t)` | yes, verbatim |
| **tail** | LPF 1.2k noise | `exp(-2.2*t)` | no |
| **pre-swell** | reversed tail+body | `areverse` (ENDS at t=0) | no |

**No tick and the hit reads LATE even when sample-exact** (the ear times a
transient by its high-frequency edge) — misdiagnosed as a sync problem. **No
tail and the hit happened in a box**; tail length IS the scale control (0.8s a
room, 1.8-2.4s a cathedral, >3s eats the next shot), and "sounds like a stock
pack" almost always decodes to "has no tail". **No pre-swell and the hit is
sudden rather than inevitable.** Only the sub is the row it sits in: what stands
where the tick should be is white noise
through `highpass=f=1200` on `exp(-38*t)` — **182 ms to −60 dB where a tick is
23** — broadband decay with a transient in it, not an edge. **Which makes the
missing tail the same filter, mirrored:** the same `anoisesrc` through
`lowpass=f=1200` on `exp(-2.2*t)`, one branch and one `amix` input, not a new
synthesiser. Anyone who "fixes" the tick to `exp(-300*t)` first, without adding
that branch, deletes the only long broadband energy the hit has.

**The hit is made by the silence in front of it.** 0.4-0.8s before, the bed
drops 6-9 dB and releases exactly on the hit — for a BODY hit, and only if the
cue does not already dip there; a second dip is the double-breath that reads as
a mastering error. At the title there is nothing to duck: the bed is already
gated to zero and the silence is the 2.2 s of room tone.

**If placement must be wrong, be wrong LATE.** ITU-R BT.1359 puts detection at
~45 ms for audio leading picture and ~125 ms lagging — the ear expects sound
after light. At 24fps that is 1 frame early vs 3 frames late.

## The line layer — a line is a shot with its own sound

Spoken lines (`09-voice`) arrive as measured files, one per slot, each at
`voice.LINE_LUFS` −20. The bed is ducked **only inside the line's window**:

```
volume=volume='(1-k0*ramp0)*(1-k1*ramp1)*...*gate':eval=frame,alimiter=...:level=disabled
```

- **Full band, never a crossover.** Run 10 split the bed and compressed
  250–4000 Hz only, so the pulse and the air hit straight through the line and
  the deepest the bed got was 6.2 LU. Band-split is what you do when the bed is
  the point; here the LINE is.
- **An envelope, not `sidechaincompress`. A duck's depth must be a number the
  mix WRITES, not one a compressor arrives at** — a compressor's depth is a
  consequence of a threshold, a ratio and how loud the key happened to be, and
  the first duck graph here measured **0.4 dB** with nothing in the filter text
  saying so. The windows are known before a sample is rendered, so the lookahead
  is free and every number asked for OF THE BED is the number applied.
- ASKED (never delivered): an ABSOLUTE **−16 LUFS** through a limiter, never
  `volume=` alone (run 10's +11.8 dB, 3,096 samples at full scale, flat 24.2);
  bed under **−24 LUFS momentary PEAK** — a ceiling, not a mean, because run
  10's bed averaged −14.8 there and peaked −9.1; depth whatever reaches that,
  clamped **10–18 dB**; **20 ms** attack, **150 ms** lookahead, **800 ms**
  release. Over 18 dB is a PLACEMENT fault — the line was put on a hit — and
  `bed_under_line_lu` names it rather than the mix hiding it.
- **8 LU is the FLOOR of the separation, not its value.** `duck_depth` is
  `min(18, max(10, bed_lu + 24))`, so the −16-over-−24 derivation holds only
  where neither clamp binds — bed peak above −14 LUFS. Below that the bed is
  already under the ceiling and the code still takes the 10 dB the norm asks
  for. MEASURED, run 18: bed peaks −22.5 / −17.5 / −11.8 / −7.6 → depths 10 /
  10 / 12.2 / 16.4 → `line_over_bed_lu` **16.11 / 14.71 / 8.52 / 7.32** — 8.8 LU
  of spread on a number this file used to call derived and constant, running
  the wrong way: **the quieter the bed under a line, the bigger the hole dug
  under it.** `bed_under_line_lu` is tested one-sided (`> -24` flags,
  `trailer_stage_spec.py:374`), so a bed ducked to **−34.0** passes unremarked.
- A card (over-black line) is never laid: `line_windows` skips `line.card`, so
  it has no file, no duck and no voice in the master.
- **The ffmpeg default that lies here is `volume`'s `eval`.** It defaults to
  `once`: the expression is evaluated at t=0, where every ramp is 0 and the gate
  is 1 — the graph text still reads as a duck while the bed comes back un-ducked
  and never stops. `eval=frame` or nothing.
- Gates, real ffmpeg, PASSING: `test_the_pulse_and_the_air_duck_too` (≥ 10 LU in
  each of 40–200, 250–4000, 6000–16000 Hz),
  `test_the_bed_is_out_of_the_way_in_the_first_two_hundred_ms`,
  `test_a_quiet_take_still_clears_the_bed_it_ducked`. The mix writes
  `lines.level.json` because QC cannot grade a duck the mix did not write down.

### The limiter revises the target, per line, by the take's crest

`line_gain` is `LINE_TARGET_LUFS − integrated(raw)` (`trailer_assemble.py:579`),
applied by `level_line` (:616) as `volume=`, pushed through
`alimiter=limit=0.6683`, and **never re-measured**. Every dB the gain drives a
take's PEAK over that ceiling, the limiter takes back out of its loudness.
MEASURED on run 18's four takes and the four files the mix wrote from them:

| take | raw I / TP | gain | peak over the ceiling | delivered I | lost |
|---|---|---|---|---|---|
| `00-0` | −20.13 / −1.39 | +4.13 | 6.24 dB | **−17.83** | 1.83 |
| `02-0` | −20.14 / −2.08 | +3.86 | 5.28 dB | **−17.03** | 1.03 |
| `01-0` | −20.06 / −3.93 | +3.94 | 3.51 dB | **−16.77** | 0.77 |
| `04-0` | −20.08 / −5.33 | +3.92 | 2.09 dB | **−16.29** | 0.29 |

The rank order is exact. Not one line reaches −16, and the four land **1.54 dB
apart** on the stage whose whole job is to make them equal. `09-voice` hands over
−20.1 within 0.08 dB, so the spread is made HERE — and nothing absorbs it:
`duck_depth` sizes its hole from the BED's peak alone, whichever line it is.

**A gain measured before a limiter is not a level after it.** What survives is
set by the take's crest, which no part of this stage chose: the duck's depth is
a number the mix WRITES, the line's level is one it asks and the limiter
revises. Re-measure the levelled file, or ask a target no take must be limited
to reach — never a bigger number, because the overshoot grows with the gain
and **raising `LINE_TARGET_LUFS` to answer "no dialogues" widens the spread.**

The suite cannot see it. Both tolerance tests (`test_line_layer.py:267,273`) allow
`abs=1.5` and `00-0` misses by **1.83** — but their fixtures are 440 Hz sines:
MEASURED, `quiet_line` (−33.75 / −30.06) lands at −12.31 dBTP after its
+17.75 dB and reads −16.05, and the hot fixture lands at −12.31 too — both
8.8 dB UNDER the ceiling. **Neither test engages the limiter, so the tolerance is
never spent** — a limiter test whose fixture never reaches it is a test of
`volume=`. BUILD row 34 installed it without re-measuring after it.

### The floor fail today is a flatness lottery, not the loudness

`level_line` ends every line at `alimiter=limit=0.6683` (`LINE_TP` −3.0 less
`LIMITER_MARGIN` 0.5), which by definition pins samples AT that ceiling.
MEASURED with `astats` on run 18's four levelled lines: `Peak level dB`
**−3.500248**, `Max level` **21899** on every one — `db_to_linear(−3.5)` × 32768
to the sample — with **36 / 38 / 80 / 10** samples pinned there. Flat factor
counts CONSECUTIVE samples at the peak, so it reads 0.0 / **0.869314** / 0.0 /
0.0: only line-1 landed two of its pins adjacent.

`lines_are_clean` demands `flat == 0.0` on every line and sits inside
`floor_pass`, so that coin toss is a FLOOR failure. **A limiter's output is a
plateau at its ceiling; a zero-tolerance flatness gate on a limited signal
fires on the limiter working.** It was written against run 10's 3,096 samples
at FULL SCALE, flat factor 24.2 — a line that clipped because there was no
limiter — and now fails the limiter installed to stop that, on 28× fewer
samples 3.5 dB down; neither test that touches it (`test_qc.py:449`,
`test_trailer_stage_spec.py:196`) has ever seen a limited take.

**And the recut cannot move it.** `line_gain` never reads the placement, so the
recut re-levels the same file to the same target through the same limiter: run
18's `09/floor` logged `CLIPPED lines` on attempts 1, 2 AND 3, 27 s each, then
`ship_flagged`.

Clipping is flatness at FULL SCALE: `Peak level dB` at `LINE_TP −
LIMITER_MARGIN` is the limiter holding, `Max level` 32767 is the converter
running out. Measure the flat factor BEFORE `level_line` limits, or gate on the
peak's VALUE — never on its adjacency.

### The line QC grades is not the line the master plays

Lines are **mono, 24 kHz** (`voice.py:118` conforms `-ac 1 -ar 24000`;
`level_line` changes neither); the bed and the delivered master are stereo
48 kHz — `ffmpeg -i` on the shipped Scarlet mp4 reads `aac (LC), 48000 Hz,
stereo`. `mix` hands the mono file to `amix` with only an `aresample`, so the
graph auto-inserts the rematrix. MEASURED on run 18's `line-0.level.wav`: as
the file sits, and as `qc.py` reads it, −17.83 LUFS / **−3.14 dBTP**; through
`mix`'s own graph (`amix=inputs=2:normalize=0` over a silent stereo bed) the
true peak is **−6.15 dBTP** — 3.01 dB, the dual-mono 0.7071 to the decimal.
BS.1770 SUMS the channels, so that same 0.7071 leaves LOUDNESS alone and the
whole 3 dB lands on the peak. Two consequences, opposite in sign:

- **Safe:** every loudness number about a line survives the rematrix —
  `−16 over −24`, `line_over_bed_lu`, the duck depths do not move. Anyone who
  forces the line to stereo expecting the dialogue to come UP measures nothing.
- **Not safe:** `line_tp` is a **floor** term (`lines_are_clean`, `<= −3.0`,
  `trailer_stage_spec.py:196,325`) and the peak it grades exists in no file this
  pipeline delivers. Run 18 read −3.14 / −3.39 / −3.15 / −3.21 — **0.14 dB
  from failing the floor** over a peak the master never sees, on the same gate
  that already fails on the flat factor. `LIMITER_MARGIN` 0.5 likewise buys
  intersample headroom in the mono domain for a signal that arrives 3 dB under
  its own ceiling.

**Grade a peak in the domain it will be summed in, or keep it out of the
floor.** The master's own true peak is measured on the delivered file (run 18,
−1.78 dBTP); `line_tp` protects a file nobody hears.

## The master gain spends PLR; it does not make loudness

`mix` measures the whole graph once and applies one gain:
`min(TARGET_LUFS - I, (TARGET_TP - TP) + LIMITING_DB)`. **TARGET_TP is −2.0 and
LIMITING_DB is 2.0, so the second term IS `-TP`** — the constants annihilate and
that branch means *push the programme to 0.0 dBTP*. So

    delivered = min(TARGET_LUFS, I - TP) = min(-14.0, -PLR)

**The gain can never buy loudness; it can only spend the programme's
peak-to-loudness ratio.** MEASURED: run 18 delivered **−15.46 LUFS** — not
−14.0, so the ceiling branch bound. The floor asks −15.5..−12.5, so **any mix
whose pre-sum PLR exceeds 15.5 dB floor-fails by arithmetic**, and no recut can
move it (a recut changes the picture; PLR lives in the bed). Run 18 cleared it
by **0.04 dB**: the arithmetic did not stop being true, the bed landed inside
it. What failed the floor was the flat factor above. And the branch is no near
miss: a second measured master, `learnings.jsonl:210` (step 09/floor), logs
**−16.7 LUFS, TP −1.8, clean lines** — a floor failure on loudness ALONE.
Two of two measured masters were bound by the PEAK branch; −14.0 never has.

The delivered true peak follows `TP_LINEAR` (0.80 → −1.94 dBFS sample; run 18
read **−1.78 dBTP**), never the −2.0 the gain aimed at: the "safety net" limiter
is the operating limiter, doing ~1.9 dB of reduction — what cutting
`LIMITING_DB` from 5.5 to 2.0 was meant to stop. Raising it back to chase the
floor does nothing but turn the extra dB into gain reduction: run 10's wall of
sound from the other side.

**The second ffmpeg default that lies is `alimiter`'s `level`, and it governs
every ceiling in this stage.** It defaults to ENABLED: the filter limits and
then re-levels the result back up to make up what it took, so `limit=` sets a
make-up gain as much as a ceiling. MEASURED while the limit was being
TIGHTENED across three attempts, the delivered true peak went **−0.55 → +0.53 →
+0.95 dBTP** (`trailer_assemble.py:55`). **A limiter that makes up its own gain
inverts its own control** — which is why the working answer to "too loud" was
headroom at the SOURCE (`BED_TP` −1.0, `sfx.HEADROOM` 0.70, `LIMITING_DB`
5.5 → 2.0) and never a tighter master, and why all six carry `level=disabled`:
the bed's (`:458`) and each line's (`:627`) through `limiter()`, the master's
(`:314`), one per synthesised cue (`sfx.py:52,65,79`). What holds it is a grep,
not a measurement: `test_every_limiter_disables_auto_level`
(`test_trailer_edit.py:464`) asserts every `alimiter=limit=` LINE in `sfx` and
`trailer_assemble` carries the argument — so a limiter written in `trailer_cut`
or `cue_edit`, or split across two source lines, raises what it was added to
lower and no test says so.

**The third ffmpeg default that lies is `anoisesrc`'s `seed`, and it lies about
IDENTITY, not level.** It defaults to **−1** — a fresh random seed every render
(`ffmpeg -h filter=anoisesrc`). `room_tone` pins `seed=11` (`sfx.py:106`);
`impact` (`:74`) and `riser` (`:61`) do not, so `sfx.py`'s own claim that "the
envelope is deterministic so the same trailer rebuilds identically tomorrow" is
false for two of the four designed cues. MEASURED: two renders of the crack
branch differ byte for byte (md5 `c63f3b2a…` vs `415ec89c…`); two at
`seed=11` are identical. Five renders of `sfx.impact` at identical arguments:
`Peak level dB` **−3.098039** on every one — `HEADROOM` 0.70 to the sample —
RMS spread 26 mdB, and flat factor **0.0 / 0.0 / 0.756 / 0.724 / 0.828**. That
is the line layer's flatness lottery reproduced on a signal nobody gates: **a
plateau at a limiter's ceiling is a property of the LIMITER, not of
`level_line`.** And step 09's two recuts (`step_09_qc.py:22`) re-render
`hit.wav` and `riser.wav` through `build_at` on every attempt, so no change to
the designed layer can be A/B'd against the version it replaced. Seed every
synthesised source, or stop claiming a rebuild.

So raise the average BEFORE the sum (what `BED_TP` −1.0 and the source headroom
are for), or accept −PLR. **No test asserts a delivered master's integrated
loudness** — every `integrated_lufs` in the suite is handed to a constructed
`QCReport`.

## QC reads the delivered file, never the plan

Every gate above the cut runs on `plan.json`. A gate whose expectation comes
from the plan is the plan grading itself — it passed a Scarlet plan with no
Holmes in it. `scripts/trailer/qc.py` reads the **master**:

1. track the master's own audio with `beatmap.metre()` (no extraction step);
2. scene-detect the picture at `SCENE_THRESHOLD` **0.1** and report which of
   `plan.json`'s cuts the picture does not show (`missing_cuts`; run 18:
   none, on 27 detected). **0.1 is a corridor with a wall on both sides, not a
   maximum:** MEASURED on the delivered Scarlet master against its 45 planned
   cuts, 0.35 finds 23, 0.2 finds 44, 0.1 finds all 45 with nothing extra,
   0.05 double-counts 18. A `cuts` count means nothing without its threshold,
   and "be safe, go lower" re-flags `cuts_on_L0` for a non-picture reason;
3. report `cuts_on_beat`, `cuts_on_downbeat`, `cuts_on_L0`, `title_on_downbeat`.

**But only the picture and the loudness curve come from the master.** Every
number about the DIALOGUE is read from files the mix wrote about itself:
`line_over_bed_lu`, `line_tp`, `line_flat_factor`, `line_crest_db` measure
`line-N.level.wav`; `bed_under_line_lu` measures `<master>.bed-ducked.wav`; the
windows `speech_occupancy` sums — and that `music_only_runs` subtracts from what
the master is heard to play — come from `lines.level.json` via
`qc.sheet_windows`. All PRE-SUM: **nothing in `qc.py` detects a voice in the
master.** MEASURED: run 18's `speech_occupancy` 0.115 is exactly
(1.59+2.31+5.74+1.75)/99.2083 — the sheet's own seconds over the picture, to
three decimals; a restatement of the mix's intention, not a reading of the file.
**Reading the sidecar the same stage just wrote is the mix grading itself, and
it is the only version of that mistake that looks like a measurement.**

**And a shape that measured NOTHING reports a clean sheet.** `measure_shape`
returns `{}` the moment `loudness_readings` comes back empty (`qc.py:418-419`)
— one ffmpeg log-format change away, since `trailer_assemble.READING` (`:464`)
is a regex over `-v info` text — and `report` splats `**(shape or {})`
(`qc.py:385`), so every shape field falls to its pydantic default. Every one of
those defaults is the PASSING side, three of them ON their target to the
decimal: `speech_occupancy` **1.0** against a `speech_target` of **0.0**,
`peak_position` 0.85 (centre of 0.78–0.92), `act3_over_act2_lu` 2.0 = 2.0,
`pre_title_silence_s` 1.5 = 1.5, `hard_out` **True**, and
`line_tp`/`line_flat_factor` **empty**, so `lines_are_clean` is True
(`trailer_stage_spec.py:286-334`), and
`test_a_report_with_no_shape_claims_nothing_and_still_passes`
(`test_qc.py:441`) asserts exactly that. **The same file's other measurement
failure goes the other way**: `loudness()` returns `(0.0, 0.0)` on a parse
failure (`qc.py:48`), and 0.0 fails −15.5..−12.5. One master, two failure
paths — the loudness one fails closed, the shape one fails open, and an
unparsed ebur128 log would have deleted run 18's flat-factor floor failure and
all five of its shape flags at once. **An unmeasured field is a verdict about an
unmeasured file. Default every gate field to the failing side —
`speech_occupancy` 0.0, `hard_out` False, `peak_position` 0.0 — or make the
shape mandatory.**

Beat targets (numbers to beat, not to pass) — and one that is NOT a target:
`cuts_on_beat ≥ 0.80` over the whole trailer was REMOVED from `QC_TARGETS` for
forcing a music video, so run 18's 0.41 is ungraded. What is graded:
`cuts_on_downbeat` ≥ 0.30, `cuts_on_L0` 1.0, `title_on_downbeat` true,
`line_over_bed_lu` ≥ 5, and per-act `cuts_on_beat_act3` ≥ 0.80,
`cuts_on_events` ≥ 0.90. Run 18 over 27 cuts: 0.33 / **0.22** / true /
**7.32–16.11** / **0.444** / **0.815**. Write the report next to the master as
`qc.json`; step 10's manifest embeds it whole, so a stale `qc.json` ships as the
manifest's own verdict.

**But the beat numbers are not the verdict.** The owner's three rejections —
"music too loud … no dialogues" — are two numbers `qc.py` derives from the mix's
own sheet, and both are FLAGS, so the master ships carrying them:

| number | Scarlet | norm | today |
|---|---|---|---|
| `music_only_fraction` | **0.765** | 0.40–0.50 | flag |
| `longest_music_only_s` | **21.0** | 15.0 | flag |
| `speech_occupancy` | **0.115** | `speech_target` 0.30 | flag |
| `peak_position` | **1.0** | 0.78–0.92 | flag |
| `integrated_lufs` | −15.46 | −15.5..−12.5 | passes by 0.04 dB |

Three quarters of the runtime is bed with nothing over it and 11.4 s of line
carries a 99.2 s picture — while every mix gate passed. **The mix is not what the
owner heard: the RATIO is not the defect, the OCCUPANCY is**, which is why three
rounds of level changes moved nothing.

**And 0.765 is the DISCOUNTED figure.** `music_only_runs` (`qc.py:169`) keeps a
moment only where the master is above `AUDIBLE_M` **−40 LUFS** momentary AND
outside a line window, so a stretch the bed has dropped out of is neither term
and simply leaves the fraction. MEASURED, run 18: 0.765 + 0.115 = **0.880** —
**11.9 s of the 99.2083 s picture, one frame in eight, is under −40 LUFS with
nobody on it**. It is not head slack: only 2.92 s of picture precedes the first
line window, so at least 9 s of it sits BETWEEN lines — and the runs agree, the
longest line-to-line gap being 53.159 → 91.168, **38.0 s**, against a
`longest_music_only_s` of **21.0**.

**And the dropouts have coordinates.** MEASURED directly: 116 momentary
readings under −40 inside the picture — 11.6 s, the same hole the 11.9 above
reads through `_runs`' one-sample bias — of which **10.7 s is two blocks,
35.5–40.8 and 64.6–70.0**, the cue's two long troughs, not scatter. The second
splits that 38.0 s gap into 11.3 and **21.0**, which IS the reported
`longest_music_only_s`. So the number this file nominates for the floor is
currently being SET by the defect: re-run `music_only_runs` with those spans
above −40 and `music_only_fraction` goes 0.765 → **0.880** while
`longest_music_only_s` goes **21.0 → 37.9**. Fill them at `ROOM_TONE_LUFS`
**−45** and neither number moves at all, because `AUDIBLE_M` is **−40**
(`qc.py:149`) — **the stage's own designed atmos sits 5 dB below the level its
own gate calls "something is playing"**, two constants in two modules nobody
reconciled. Either way the ear is fixed and the metric is not; that is the shape
of the discount, not an argument against fixing it.

**So every music-only number is improved by dead air, and the fraction most of
all.** Quieting the bed in the gaps — the obvious answer to "music too loud" —
drops `music_only_fraction` sample by sample without adding a word. The RUN
resists it: `longest_music_only` reads `runs[:-1]` (`qc.py:189`), so its 21.0 s
are BODY and not the 6.2 s montage the norm allows, and it only moves if a hole
is cut in the ONE longest stretch, wide enough to break the 0.15 s `SAMPLE_GAP`
— which is what already happened to the 38.0 s gap. Coarser to game, not immune.
And a line lost in the sum, buried by the master limiter or gone in the encode,
still has its window masked by the sheet: the fraction DROPS again and
`speech_occupancy` does not move. **A gate whose "layer present" test is a −40 dB
audibility threshold cannot tell a voice from a bed, so every way of making the
trailer emptier scores as progress.**

Which decides the floor. Occupancy is *decided* upstream (steps 03/04 place the
line windows) and only *delivered* here, but the gate is 08's, and
`trailer_stage_spec.py:355-361` makes all three FLAGS. Put
**`speech_occupancy`** in `floor_pass` first: alone of the three it reads no
level at all, so no mix can satisfy it — only more line placed can — which is
also why it cannot catch a line that vanished in the sum. Put
**`longest_music_only_s`** beside it; leave `music_only_fraction` out, the
number this file used to nominate. Until they are floored nothing in the floor
looks at them: run 18 failed the floor on a limiter's flat factor and its
cue's hold spans instead (`cuts_inside_sustain` 3, `long_shots_on_sustains`
0.667) and shipped anyway. **A verdict you can measure and do not floor is a verdict you
have decided to ship.**
