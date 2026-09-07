---
name: trailer-shots
description: Generating the clips - H3 constants, framing, camera, and the coverage economics.
---

# Shots

`step_07_clips.py` (the round: renders, reads, gates, prices), `build_clips.py`
(a take's values), `frame_budget.py` (price), `shot_grammar.py` (the frame).

## A take costs 77 frames before it delivers any picture

**ONE TAKE, ONE SHOT.** Coverage carved into several shots inside one generation
is what produced four moments of one image (`build_clips.py:4`, BUILD row 21);
`_one_take_per_shot` refuses a beat used twice, Scarlet is 22 beats / 22 shots /
reuse 1.0, `[Shot N]` markers are dead. **Never reuse a shot** — for a rule of
three, build a similar one. So a take is `a + b * frames`, `frames =
legal_frames(24 * (shot + 2.85))`: 69 frames of tax for the 2.6s reference leak
plus the 0.25s handle, 8 for the mean snap UP onto H3's 17-frame ladder, the
same 77 at any shot length. That leak is H3's r2v path OPENING on the reference
image: for ~2.1s the shot is the character on the grey sheet before entering the
scene — the binding working, held hard.

| frames | 90 | 107 | 124 | 141 | 175 | 192 | 209 | 226 | 243 | 260 | 277 | 294 | 362 (cap) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MEASURED min | 4.5* | 4.9 | 5.7 | 6.3 | 8.2 | 9.0 | 10.1 | 11.2 | 12.4 | 13.6 | 17.6 | 16.1 | 22.0 |
| min per picture s | 5.02 | 3.07 | 2.48 | 2.08 | 1.84 | 1.75 | 1.72 | 1.70 | 1.70 | 1.70 | 2.02 | 1.72 | 1.80 |

**THE FLOOR IS 1.70 MIN PER PICTURE SECOND AND IT OPENS AT 192 FRAMES.** Run 18
timed all 22 takes over 13 frame counts, the first round to time more than one
(`learnings.jsonl`, gate `cycle`): 4088 frames, 12707s render + 553s read = **221
min against the 210 min share, 134 min per finished minute**. Seconds per frame
CLIMB, 2.67 (141f) → 3.64 (362f), at nearly the rate the 77-frame tax amortises
away, so the two cancel: from 192 frames a picture second costs a flat 1.70–1.80
min and never gets cheaper; under 175 it walls up — 2.08, 2.48, 3.07, 5.02.
**277 is the hole in that floor**: 2.02 min per picture second, +37% over
`79 + 2.49/frame`, the worst-priced take of the 22 — 1054.9s where 294 frames
cost 968.7s. Unexplained (`rendered_twice_if_lost` can put two renders in one
row, but 286s is no second render). **A measured band with one hole, not a
law.** Tax is still 42% of the render, now 88 min of the share. *Both 90f takes:
532.3s and 271.3s — a round's FIRST take carries 261s of model load and is never
a point on the line, except in the code: `cycle_points` filters on gate and
`frames` alone (`frame_budget.py:120`), so B00 IS in the fit, and `typed_slope`'s
`a` is a MEDIAN — one row deep. Drop B00 and a falls 79 → 61 — 18s charged to
every take, 386s a plan that no take renders.* The floor sizes
the step alone: 210 ÷ 1.70 = **123s is the most picture step 07 can deliver**,
0.85 × 210 ÷ 1.70 = **105s is what step 06 may plan** — it planned 99.2s.

Coverage has ONE free variable and it is the SHORT end: deleting a setup returns
its picture frames PLUS 77. **Run 18's twelve takes under 192 frames are 28% of
the cut and 37% of the clock** — 27.6s of the 99.2s played for 4715s of the
12707s rendered; priced as the table does (frames less tax) that is **2.45 min a
picture second, 44% over the floor**, against B18's 8.75s for 16 min. (B00's
532.3s carries 261s of model load no fold returns.)
**Fold every phrase under 5s into its neighbour; an accent is a purchase — name
it, buy at most two.** **But the fold is a step-06 ORDERING job.** It needs two
shorts ADJACENT in the cut, same location, same cast: of run 18's seven sub-5s
phrases only B10+B11 and B21+B19 qualify — B03+B04 are adjacent and cross St
Bartholomew's to 221B. Those two return 279s of render and two sheets, **320s
of a 660s overrun, not the whole of it**, and unevenly: B10+B11 folds 828s into
209 frames at 605s (**−223s**); B21+B19 folds 1024s into 294 frames at 969s
(**−56s, 5%**). **Fold INTO the 192–243 band — a fold landing past 260 returns
almost nothing** — and plan short spans of one location ADJACENT, or the rule
above has nothing to fold. The two accents (B00 0.75s, B06 0.5s) are
also the ONLY shots `steps_for` would drop to 4 steps (`FAST_SIZES` +
`FAST_SECONDS` 1.0, `build_clips.py:96`): fold them and `FAST_INSERTS` has no
subject left, and the take it waits on is a render nobody gets back. **Fold
before you optimise a step count.**
`test_longer_shots_are_cheaper_per_picture_second` is right in FRAMES (1488 vs
831); in SECONDS the saving stops at 192.

**Step 07's measured failure is a MISSING BEAT, not a wrong face — 21 to 4.**
21 `drop_beat` rows (8 at 391s left, 7 at 594s, 6 at 52s) against four identity
rows ever. `drop_beat` fires only on a beat's FIRST take and stops it forever,
and `render_round` walks `plan["beats"]` = cut order (0.0 → 90.46), so the beats
with no clip are the ones LATE in the cut: run 6 dropped B14-B21, eight closing
beats, with 391s left (`test_step_07_clips.py:322`). There is no graceful shed —
whole beats are refused — and the cut's last two shots are its two longest takes
(B20 362f, B18 294f): one refusal at the tail costs 8.75s of picture, one at the
head 0.5s. *Not all dear takes are late — B02 is 277 frames at cut position 2.*
**The plan must be affordable at a = 79, not a = 0. There is no other valve.**

The price is a LINE, the machine is a CURVE, and the line STEERS. Least squares
on those 22 rows is `-80 + 3.54/frame` — a negative intercept, which is what a
line through a convex curve always gives — so `Cycle.from_rows` refuses it
(`test_a_fit_with_a_negative_intercept_falls_back_to_the_typed_slope`) and run 19
prices on `typed_slope`: b = 2.49 through the median row, a = 79. **Every honest
fit this machine produces is rejected the same way.** The pin sits on the median
ROW, not on the machine: **5.1% HIGH at 175f** (515s priced, 489.6s measured over
four takes) and 26% LOW at 362f (980s, 1319s), **sign changing at ~205 frames** —
+17% at 107, +14% at 141, +2.7% at 192, −4% at 226, −8% at 243, −16% at 294.
A per-take `a` of 79s makes SETUPS look dear and LENGTH look cheap — the direction
it is already wrong in — and on a phrase-heavy book, every take under 205 frames,
it OVER-charges by 12–17% and cuts a plan that would have fitted: the mirror of
run 18's overrun, and a failure no learnings row has seen.
Run 18 priced 4088 frames at 10179s and spent 12707s, 47% of that overrun on its
four takes past 243. **Never let this price choose take LENGTH: plan no take over
243 frames** — 192–243 is the only band that is on the floor, priced within 8%,
AND above the fold: 175 frames covers a shot of at most 4.44s (`legal_frames`
less the 2.85s tax), which the fold above already deletes.
And the cap survives a corrected pricer, because a second measurement says it
too — the MARGINAL frame. Seconds per picture second across the rungs, one or
two takes each: 103 (226→243), 99 (243→260), 110 (260→294), **124 at 294→362**;
a whole FRESH setup, its reader sheet included, sells picture at
(743.0 + 20.65) / 7.275 = **105s**. **Past 260 frames the next frame costs more
than a new setup does; past 294 it costs 18% more** — B20's top 68 frames bought
2.83s for 350.6s. So a hold the cut wants longer than 7.3s is TWO beats, never
one long take. The value cap 260 and the price cap 243 were measured
independently and landed on adjacent rungs — only the price one goes away when `Cycle.from_rows` fits.
`LONG_TAKE = 243` forces round one's longest live beat to 243 frames for a second
frame count and buys nothing: the plan renders 13 counts unaided and their fit is
rejected. Scarlet paid zero (B20 asks 362). The exposure is a longest **SHOT**
under **7.3s**, not 10.1s: `frames_this_round` compares FRAMES, and 243 frames is
10.125s of TAKE, 7.275s of shot once the 2.85s comes off. From a 192-frame
longest beat that is 51 frames and **200.8s measured (743.0 − 542.2), 3.3 min**,
of take the cut never plays; the typed 2.49 s/frame calls it 127s.

## The ladder is priced in setups

**A ROUND'S MODEL SWAP IS 421s AND IS PAID AT BOTH ENDS.** The two `read` rows
solve the session exactly — 552.6s/20 sheets and 428.7s/14 sheets → **20.65s a
sheet** (typed 20.0 is right) and a **160s session, not the typed 240**. The read
frees the engine (`reader(free=True)`), so the NEXT round's first render
re-streams H3: the 261s between run 18's two 90f takes. `retry_cost` charges 240
and counts that reload at zero. At 175 frames MEASURED (489.6s, four takes) a
rung is 489.6 + 421 = **911s against 510s a setup — one rung = 1.78 setups**, not
1.43; one more setup in a round already staged is the render plus 20s
(`take_cost`). And the swap is charged PER BEAT — `ladder.py:82` gates every
climb on its own `cost_seconds` — but PAID PER ROUND: one rerolling beat is
underpriced by 181s, four are overpriced by 539s. **Never open a round for one
beat.** Run 6: two takes of one beat, 33 min, the reading 4.0 → 3.5 against a
3.0 threshold — half a trait bought, more than a whole one still owed — and
B14-B21 dropped with 391s left (`test_step_07_clips.py:322`). Those two are the
only failing identity rows step 07 has ever written; the other two are
`accepted_unverifiable`. **A rung that WORKS writes nothing** — `Climb.settle`
returns on `ok` before it learns — so the ledger cannot say a rung ever bound a
face, and never will: an empty identity section is a CLEAN round, not a skipped
gate (run 18, all 20 bound takes passing first). So the ladder's price is not
the rungs, which almost never fire — it is `RETRY_RESERVE` 0.15: **31 min of the
share, 18s of picture, three setups**, out of the plan before a frame renders
(`fits`, `cue_spans.fit_to_budget`).

And the reserve never reaches a rung, because the PRICE spends it first. It holds
back 1890s; run 18's price was wrong by **2528s — 20% of the share against a 15%
reserve** — gone before a gate could fail, and the step still finished 660s past
210 min. Cap at 243 and the error is 1343s: 71% of the reserve, leaving 547s —
short of one 911s rung. **Budget the ladder at zero.** `RETRY_RESERVE`'s FLAG
names the reroll count as what measures it; ONE reroll has ever been spent. It
is an error bar, not a retry fund. And **`A_TYPED = 0.0` is refuted, not
unmeasured**: at a = 0 the price is 20% low over all 22 takes, at a = 79 it is
0.9% **HIGH** over the 18 under 243 (8630s priced, 8551s measured) — setups
overpriced, the direction named above. `Cycle.from_rows` reads zero rows on a
fresh book, so step 06 AND round one price every book's FIRST run at a = 0,
blind to 22 × 79s = 29 min —
**the second run of a book is the first one priced right.**

**RUNG 0 IS THE FIRST TAKE, NOT A RETRY.** `ask` reads `plan[attempts]` and
gates only `attempts > 0` (`ladder.py:76-82`); `seed_for` hands `reroll_seed`
i=0 the unchanged base seed (`step_07_clips.py:136`). All 22 of run 18's cycle
rows read `reroll_seed seed 51000+7i` on their FIRST render, and
`test_step_07_clips.py:316` says it outright: the `reroll_seed` identity row is
the first take being gated, the reroll comes after. With `tries=1` there is no
seed-only retry at all — the ladder's ONE retry is `alternate_setup`, a new seed
AND `tightest="close"` for the whole take. **Never reorder `ladder_for`**:
`alternate_setup` first re-frames every beat's FIRST take to close, which
rewrites the prompt, which changes the recipe fingerprint (`build_clips.py:144`),
which re-renders all 22 takes — the whole share spent on the ladder. **Spend a
render only on a change you could not have made for free**: a cheaper face goes
in `take_values`, never in the rung order.

## Say how big the person sits in frame

Faces collapse in wides at ANY resolution; the driver is **head size in frame**,
not pixel count. Saying nothing about framing gets an establishing wide with a
small figure turned away — the first two bound clips read unmistakably as the
Criterion and as 221B, and in neither could you see who the person was.

`size_for` does not tighten on the hits, it reverses them: section, sustain and
trough take `widest(seconds, bound)`, capped at `BOUND_FLOOR="medium"`, so every
bound span over 1.5s is exactly `medium` and every phrase is `medium_close`.
Scarlet: 10 medium, 10 medium_close, 2 insert — three framing paragraphs across
22 renders, the longest shots carrying the smallest heads.

**FRAMES ARE THE ONLY CURRENCY.** `take_frames` reads `seconds` and nothing else,
so size, angle, camera and wording are FREE — a close costs what the medium costs,
and tightening is always legal (`MIN_SECONDS` only forbids going WIDER).
The clock buys duration and setup COUNT, so the free variables carry all the
variety there is; a constant size series is the defect `is_uniform()` refuses for
shot lengths (`assemble.py:141`), ungated one level up, and `choose_sizes` — no
same size twice in a row — is called by nothing.

## Camera

A closed vocabulary, written as prose with amplitude and speed: *"The camera
pushes in with small amplitude at slow speed."* Bracket syntax `[Push in]` is
the hosted Hailuo dialect and does nothing on H3. H3 drifts by default when the
prompt says nothing, so a static frame must be asked for. A move is motivated when
its sentence names a CAUSE and a DESTINATION; the table keyed on register is gone,
because three variants of drift are still drift.

## H3 constants — it rewrites illegal values silently

- `frames % 17 == 5`. Off-grid snaps UP, 8 frames on average. Ceiling 362f.
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
conditioning, our whole identity mechanism), USA-excluded licence, diffusers-only,
and its headline 11.23s is 8x B200 — single-GPU 51s vs 133s dense, ~2.6x.
