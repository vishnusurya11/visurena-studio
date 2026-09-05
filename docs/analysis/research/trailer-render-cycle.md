# The trailer render cycle: what a take costs, and why

Step 07 is the trailer's only fixed cost. Everything else — how many setups the
story authors, how long the cue is, how long the trailer runs — is derived from
how many takes the machine can render in its share of the six-hour ceiling. So
the cycle is not a performance detail. It is the number the whole plan is built
on, and until run 11 it was a number nobody had measured.

## What run 10 measured

19 takes, first take started 12:36:53, last promoted 17:32:48: **15.76 min per
take**, 295.9 min of a 316-min run. The anatomy of one cycle:

| part | minutes | what it is |
| --- | --- | --- |
| H3 sampling, 175 frames @ 8 steps, 1344x768 | 7.25 | compute |
| H3 reload after the unload | ~4.6 | **model swap** (inferred from the gap) |
| Qwen3-VL contact-sheet read | ~3.7 | load + one sheet |

**8.3 of every 15.76 minutes — 53% — was a model swap, not compute.** The cause
was one line of policy: `describe_frames` called `_live(free=True)`, which posts
`/free {unload_models, free_memory}` to ComfyUI before every read. That unloads
H3's DiT (fp8), the qwen3vl text encoder and both VAEs — about 16 GB — and the
next take re-streams all of it off the spinning disk the models live on. The
free is correct in isolation: run 4 died the other way, with Qwen3-VL loading
beside a staged H3 and landing half on the CPU (6:52 to load, 10:23 to answer,
past the 600 s gate timeout). What was wrong was the *unit*: one swap per take.

Two further wastes measured on the same run:

- takes were a flat 175 frames (7.29 s); the cut used ~2.0 s plus a 2.6 s head
  trim, so **65 frames per take were sampled and thrown away** — about 50 min of
  the run;
- `take_seconds()` had a 7.0 s floor, which existed so ONE take could hold FOUR
  shots. Under "one take, one shot" it holds one, and the floor was pure waste.

## What changed

### 1. The round is the unit

`studio/ladder.py` gained `Climb`: the same ladder (rungs, gate, terminal,
learnings, `capped`, `DROPPED`) advanced **one attempt at a time** instead of
driven to completion per beat. `climb()` is now that object driven to the end,
so single-subject steps are unchanged, byte for byte, in behaviour.

Step 07 drives many climbs a round at a time:

1. **render** — every live beat's next take, back to back, nothing freeing the
   engine, so H3 stays resident across the whole phase;
2. **read** — one `describe.reader()`: the engine is freed ONCE (lazily, at the
   first read, so a round with no face to read unloads nothing) and every
   contact sheet of the round is answered while Qwen3-VL is resident;
3. **gate** — each take settled against its own beat's sheet; the beats that
   bound are finished, the beats that failed take a rung and ask for round 2.

Rounds continue until no beat asks for a take, or the budget refuses one.
Twelve beats that bind first try now cost **one unload and one reader session**
for the whole step, instead of twelve of each.

### 2. Render only the frames the cut uses

`take_seconds(beat_id, plan)` = `shot.seconds + HEAD_TRIM (2.6) + HANDLE (0.25)`,
floored only by `READ_WINDOW` (0.75 s), which is what the identity reader needs
to sample three different moments. `frames_for()` rounds that up onto H3's
`frames % 17 == 5` grid. A 2.0 s shot is 4.85 s → **124 frames**, against 175
before: 29% fewer frames sampled per take.

`frames_of()` now samples past `HEAD_TRIM` rather than past `frames.HEAD_LEAK_SECONDS`
(1.0 s). This was latent before and would have become a real bug: with a 4.85 s
take, two of three stills would land inside the 2.6 s reference leak, where the
frame *is* the reference sheet — the identity gate would have been passing on a
picture of its own answer.

The frame count is part of `recipe_for`, so a beat whose shot grew re-renders,
and a reroll — same plan, same seconds — keeps the same frame count.

### 3. The cycle is measured, not typed

Every round writes `Learning(step="07", gate="cycle", measured=<seconds per
fresh take, render plus its share of the read>, threshold=RENDER_SECONDS,
action="round_N")`, and every reader session writes `gate="read"` with what the
session itself cost. `render_seconds(rows)` is the median of this book's cycle
rows, falling back to the `RENDER_SECONDS` constant when no run has measured
one. Reused takes are excluded — a cache hit is not a measurement.

`RENDER_SECONDS` stays at 16 x 60. It is run 10's measured truth and it must not
be lowered by argument: lowering it by argument (to 11 min) is exactly what made
run 10 plan 25 setups, render 19, and drop the last six — which are the climax.
Run 11 will measure the new one and the constant becomes a fallback nobody uses.

**The call step 06 should make** (`affordable_takes`, `scripts/trailer/step_06_plan.py:81`):

```python
from scripts.trailer.step_07_clips import RENDER_SECONDS, render_seconds_for   # import
return max(1, int(ctx.budget.remaining("07") // render_seconds_for(ctx)) - RETRY_RESERVE)
```

`render_seconds_for(ctx)` returns `RENDER_SECONDS` verbatim until a run has
written a cycle row, so making the change is safe before run 11 and correct
after it.

### 4. Four steps for inserts, behind a flag that is OFF

`steps_for(beat_id, plan)` returns `FAST_STEPS` (4) only when every shot of the
beat is an `insert` or `extreme_close` **and** runs 1.0 s or less, and only when
`FAST_INSERTS` is True. It is `False`, and it stays False until one take is
measured against its eight-step twin. The published objection to four steps —
the last Euler step dropping sigma from ~0.72 to zero, three quarters of the
denoising in one step — is about faces and motion, and an insert held 0.8 s is
under twenty frames of an object. That is an argument, not a measurement, and
the flag turns on from a measurement.

## The budget, per round

A round is priced before it is staged:

- `read_seconds(sheets)` = `SESSION_SECONDS` (240 s: the unload, Qwen3-VL off
  disk, the first sheet) + `SHEET_SECONDS` (20 s) per further sheet;
- `take_cost(staged)` = one render + the marginal read for adding this take to
  the round — a whole session for the first take, one sheet for each after;
- a beat is dropped only when its FIRST take is unaffordable at that price. A
  take rendered with no time left to read it would ship ungated, which is worse
  than not rendering it;
- a retry is priced at `RETRY_COST` = one render + one session, because a retry
  round has to open a session of its own.

Run 6's rule — "a retry may cost this beat, never a later one" — used to be
priced as `RENDER_SECONDS * (beats_left + 1)`. It is now structural: every
beat's first take is rendered in round 1, so a reroll can only spend another
reroll.

`SESSION_SECONDS` and `SHEET_SECONDS` are estimates (3.7 min measured per read
in run 10, when every read included a cold load; ~4 s measured for a resident
read in run 5's step 02). They are budget *reserves*, deliberately generous, and
run 11 measures both.

## Expected cycle — EXPECTED, not measured

From the critique's arithmetic (2.49 s/frame at 8 steps, measured 09-03: a
175-frame take 7.25 min after the one before it, with no read between):

| model | cycle/take | takes in the 210-min share | takes in 297 min (run 10's carry) |
| --- | --- | --- | --- |
| run 10, as measured | 15.76 min | 13 | 18 |
| batched read, H3 resident (175 frames) | **~7.45 min** | **28** | 39 |
| + render only what the cut uses (avg 124 frames) | **~5.34 min** | **39** | 55 |
| + 4-step inserts (UNMEASURED) | ~2.8-3.8 min | 54-75 | 77-117 |

Under "one take, one shot", takes are shots, so the trailer's length follows:
12 takes is ~25 s, 28 takes ~56 s at a 2 s mean, 39 takes ~78 s. The whole
51-shot picture, which is 13.4 h of rendering on run 10's cycle, is ~4.5 h at
5.34 min a take — inside the six-hour ceiling, ~4 books a day on one 4090.

None of this is measured. It is the same 2.49 s/frame arithmetic applied to a
different unit of work, and the reload time inside it (4.6 min) is itself
inferred from a gap between file mtimes, not timed.

## What run 11 must measure

1. **H3 reload time** — the 4.6 min in the table is inferred from the gap
   between take mtimes. Round 1 pays it at most once; the `cycle` learning of
   round 1 against round 2 is the measurement.
2. **The reader session** — the `read` learning: how long an unload plus a cold
   Qwen3-VL plus N resident sheets actually takes, against the 240 s + 20 s/sheet
   reserve. If a resident sheet really is ~4 s, `SHEET_SECONDS` drops and rounds
   get cheaper still.
3. **Per-take sampling at 124 frames** — the `cycle` learning. The arithmetic
   says 2.49 s/frame scales linearly with frame count; H3 is a DiT with
   quadratic attention over the temporal axis, so a shorter take may be *cheaper
   than* linear. Either way the number to plan on is the one the round writes.
4. **Whether the identity gate still reads the same** at 124 frames with the
   stills taken past HEAD_TRIM rather than past 1.0 s. The reads should get
   stricter, since the reference leak is no longer in the sample.
5. **One insert at 4 steps against its 8-step twin**, before `FAST_INSERTS` is
   ever set True.
