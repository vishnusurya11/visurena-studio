# Cut rhythm: why run 10 read as a song, and the walk that stops it

Scope: `studio/trailer_edit.py` — the beat walk (`plan_cuts`) and the four pure
measuring functions `qc.py` can read off the delivered picture.

## 1. The finding

An editor watched run 10's master and named the defect in one sentence:

> the music grid owns every cut … the viewer starts counting within 4 shots and
> predicts cuts; picture becomes wallpaper for the audio.

The numbers behind it:

| | run 10 (105 s master, 92.5 BPM cue) |
|---|---|
| cuts on beat | 38 / 50 = **76%**, whole trailer |
| shots at exactly one of three musical lengths | **31 / 51** (1 bar ×14, half bar ×10, 3 beats ×7) |
| longest run of equal shots | **8** (#15-22) and **9** (#38-46) |
| act medians | 2.46 / 2.42 / **1.67** s — act 2 indistinguishable from act 1 |
| the one hold | 4.29 s at **15%** of runtime |
| before the card | 2.50 + 2.50 s of dark picture |

The mechanism was in the module's own docstring: `cut_points` took, for every
step, *the onset NEAREST the arc's next position, unconditionally* — "the music
therefore owns every cut". Owning every cut is the defect. `BEATS_BY_POSITION`
then offered only whole-beat counts, so the three musical lengths were the only
lengths available; and `hold_at_breath` fired whenever the cue had no title
moment (by run 10 that was every cue), parking the single hold at 15%.

`is_uniform` passed all of it, because it measures max-minus-min over the
**whole list**: two long shots anywhere else hide a run of nine identical ones.

## 2. The brick

A trailer's cut is not one rhythm, it is **three acts with three different
relationships to the music**, and the picture must be *unpredictable inside each
one*. Three rules follow, and they are in tension:

1. **Act shape** — act 1 holds, act 3 cuts; the medians must strictly decrease.
2. **No counting** — no four shots within two frames of each other; cut-interval
   std/mean ≥ 0.35 in **every** 12 s window (not over the whole cut — run 10
   measured varied overall while holding ten cuts of 1.21-1.25 s between 83 s
   and 94 s).
3. **On beat only where it earns it** — acts 1-2 ≤ 50% on beat, act 3 ≥ 80%.

Rule 3 forces act 3 onto whole beats. Rule 2 then has to come from somewhere
other than landing off the pulse — so act 3 varies by cutting *different beat
counts* (3, 1, 2, 1, 3, 1, 2, 1, 2), never by drifting off the grid.

## 3. What the walk does now

**Acts are fractions of the DURATION, not of the cue** (`ACT_BANDS`
0-30 / 30-66 / 66-90 / 90-100%). The no-reuse rule (one take, one shot) makes
most pictures far shorter than their cue, and a 25 s picture still has to open,
turn and climax.

**Nominal shot length is in BARS** (`ACT_BARS` = 1.40 / 0.80 / 0.44 / 0.44), so
a 120 BPM test metre and a 92 BPM cue read the same shape and the seconds
follow the tempo.

**One figure, nine shots long** (`FIGURE`), applied as multiples of the act's
nominal: five longs and four stabs, alternating.

- The longs **outnumber** the stabs, so the median of any stretch is a long and
  the act median is the act's nominal. With four of each, the median sits
  between a stab and a long and *one* shot cut short by a hit moved act 2's
  median from 2.5 s to 1.33 s (measured).
- The stabs are **deep** (≈0.35 of a long). A long-stab-long window reaches
  std/mean 0.35 only when the stab is under about 0.4 of its neighbours.
- Nine is odd against a four-beat bar, so the figure never lines up with the
  music. There is no RNG to seed: the figure is a pure function of the shot
  index and the metre, so the same cue re-cut gives the same picture frame for
  frame.

**The figure replays when a shot is cut short** (`FIGURE_SERVED` = 0.75). An L0
event that truncates a long would otherwise flip the act's long/short balance,
and the act median with it. **It restarts at each act boundary** (`ACT_PHASE`):
acts 1-2 open on their longest shot; act 3 opens on the stab — the climax begins
by cutting, not by holding.

**Landing is act-dependent** (`BEAT_LOCK` = 0.66):

- acts 1-2 (`free_landing`) move a cut only onto an **anchor** — a phrase start,
  a stopdown, a hit, or the edge of a measured dialogue slot — and otherwise
  land wherever the figure asked, pushed three frames clear of the pulse
  (`off_grid`). Without that nudge roughly one free cut in twelve lands on a
  beat by arithmetic accident, and every accident reads as the grid still
  showing.
- act 3 (`nearest_grid`, `LEVEL_REACH` = 0.6) takes the highest-level grid point
  near the target: a beat always outranks a half-beat, so act 3 cuts on whole
  beats and nothing else.
- **L0 events are honoured everywhere** (`respect_event`). Hits, stopdown starts
  and the title hit are allowed in any act — that is what "on beat where it
  earns it" means.

**The hold ends the picture** (`hold_span`). With a reachable title hit it opens
on the last stopdown before it; otherwise `hold_length` back from the picture's
own end, on a beat, preferring a downbeat that costs no more than one beat. It
is at least `HOLD_MIN` = 3.0 s, longer than the widest act cap so it reads as a
hold, and never longer than the tail band — a 4.5 s hold on a 25 s picture would
swallow half of act 3.

**Act 1 may hold two bars** (`ACT_CAPS` = 2.0 / 1.0 / 1.0 / 1.0, floored by
`max_shot`, ceilinged at 6 s). `MAX_SHOT` (4 s) exists to stop a 7.42 s shot at
the *climax*, where the corpus target is 0.54 s. Act 1 is the opposite case: a
flat 4 s ceiling under a 92 BPM cue pins every opening shot to exactly 4.00 s —
the uniformity the module exists to prevent. Two bars is one musical statement,
and at 120 BPM it *is* 4 s, so nothing moves on the test metre.

## 4. Measured results

Test metre: 100 s cue, hits at 16 / 40 / 64 / 88, stopdowns 85.5-86.5,
phrase starts every 16 beats, dialogue slots 30-34 and 52-56, `title_hit` 88,
stretch = `LITERARY_STRETCH` (2.5).

| | run 10 | 88 s @ 120 | 25 s @ 120 | 88 s @ 92 | 25 s @ 92 |
|---|---|---|---|---|---|
| shots | 51 | 56 | 13 | 44 | 10 |
| act 1 median (s) | 2.46 | **3.52** | **3.88** | **3.69** | **4.92** |
| act 2 median (s) | 2.42 | **2.13** | **2.38** | **2.63** | **2.92** |
| act 3 median (s) | 1.67 | **1.00** | **0.75** | **1.29** | **0.67** |
| strictly decreasing | no | yes | yes | yes | yes |
| longest equal run | 8 / 9 | **2** | **1** | **1** | **1** |
| interval variation (worst 12 s window) | — | **0.400** | 0.471 | **0.361** | 0.383 |
| on beat, act 1 | — | **0.22** | 0.00 | 0.14 | 0.00 |
| on beat, act 2 | — | **0.16** | 0.20 | 0.07 | 0.00 |
| on beat, act 3 | — | **1.00** | 1.00 | 0.95 | 1.00 |
| on beat, whole cut | **0.76** | 0.58 | 0.50 | 0.51 | 0.44 |
| hold | 4.29 s at 15% | 4.5 s, ends the picture | 3.0 s | 6.5 s | 3.5 s |

Targets, all met: act 1 median ≥ 1.25 bar (2.50 s at 120, 3.26 s at 92); act 3
median ≤ 0.625 bar (1.25 s / 1.63 s); longest equal run < 4; interval variation
≥ 0.35; act 1-2 on beat ≤ 0.5; act 3 on beat ≥ 0.8; one hold ≥ 3.0 s ending the
picture.

The "three musical lengths" tell is gone where it matters. Run 10 put 31 of 51
shots (61%) on one of three lengths. Now, across acts 1-2 — where the viewer
does the counting — the three commonest lengths cover 8 of 29 shots (28%) at
120 BPM and 5 of 23 (22%) at 92 BPM. Over the whole cut it is 28 of 56 (50%) at
120 BPM, because act 3 is deliberately on whole beats and there are only three
beat counts to spend there; at 92 BPM, where the beat is longer and the counts
spread wider, it falls to 13 of 44 (30%).

## 5. Rules that could not all hold at once

1. **Act-3 variety vs act-3 on-beat.** Act 3 must be ≥ 80% on the beat, which
   means whole-beat lengths, which means only two or three distinct lengths.
   *On-beat wins*; variety comes from the beat COUNTS (3, 1, 2, 1, 3, 1, 2, 1, 2
   — std/mean 0.44) rather than from off-grid landings. This is why the
   whole-cut "three lengths" number stays near 50% at 120 BPM.
2. **Act-1 median vs the 4 s cap at slow tempi.** At 92 BPM a bar and a quarter
   is 3.26 s and `MAX_SHOT` is 4.0 s — there is 0.74 s of room between the
   target median and the ceiling, so every long shot clips to exactly 4.00 s.
   *The median wins*: act 1's ceiling is raised to two bars (`ACT_CAPS`).
   Measured with the flat cap restored, the 92 BPM cue gives act medians
   2.85 / 1.96 / 1.29 s (act 1 short of 3.26 by 0.4 s) and an interval
   variation of 0.307 on the 25 s picture — both fail. It is also the one
   place this work departs from "every gap <= `max_shot(bar)`": at 120 BPM
   two bars IS `max_shot`, so the test metre is untouched.
   Consequence for another department: `qc.on_cap_fraction` is computed against
   `max_shot(bar)`, so on a sub-120 BPM cue it will now read act-1 shots as
   "at the ceiling". It should use `act_cap(start / duration, bar)` instead.
3. **Monotonicity of the cut count vs act bands that scale with duration.**
   `fit_points` steps the duration down half a bar at a time until the cut count
   fits the takes. The walk is monotone over two bars of shortening, but a
   single half-bar step can add up to two cuts (three at 140 BPM), because the
   acts are fractions of the duration while the shots are fixed lengths in bars.
   *Convergence wins*: a wobble costs `fit_points` one more iteration, never its
   termination. Tested as "monotone at lag 4, adjacent rise ≤ 2".
4. **`HOLD_MIN` vs `FINAL_HOLD`.** The sound department moved `FINAL_HOLD` from
   3.0 to 4.5 s while this was being written. `FINAL_HOLD` sizes the title
   CARD; the picture's hold is now its own constant (`HOLD_MIN` = 3.0, editor's
   rule 8) so the two cannot drag each other around. On a 25 s picture a 4.5 s
   hold is 18% of runtime and swallows half of act 3.
5. **Act medians exclude the closing hold.** It is the button, not a cut length;
   counting it makes the fastest act measure as the slowest. The editor's rule 5
   already scopes act 3 to 66-90%, and the hold sits at 90-100% on a long
   picture — but on a 25 s picture it starts at 88%, so `act_medians` drops the
   last shot explicitly.

## 6. Bug found and fixed on the way

`usable_events` drops any event that falls less than one shot after the event
before it. On a 44.96 s walk the hold's own start fell 0.42 s after the cue's
second hit and **was the thing dropped** — the walk sailed past it and the
picture ended with no hold at all, three cuts busier than the 46.26 s walk above
it. `with_hold` now arranges the events around the hold instead: the hold
outranks them, so the events move.

## 7. The measuring functions

Pure, tested, and importable by `qc.py` so the plan and the delivered master are
graded by one ruler:

- `act_medians(points, duration)` → `[act1, act2, act3]`, hold excluded.
- `longest_equal_run(points, fps=24)` → most consecutive shots within
  `EQUAL_FRAMES` (2) frames of each other. Sliding, so a run cannot hide behind
  long shots elsewhere the way it did under `is_uniform`.
- `interval_variation(points, window=12.0)` → the **least** std/mean over any
  12 s window; the whole-cut figure for pictures shorter than the window.
- `on_beat_fraction(points, grid, act=None, duration=None, tolerance=ON_BEAT)` →
  share of one act's cuts within `ON_BEAT` (0.04 s, `qc.ON_GRID`) of the grid.

Supporting: `act_of`, `act_lengths`, `act_cap`, `median`, `variation`.
