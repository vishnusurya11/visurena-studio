# Frozen starts are render variance, not a plan fault

Measured 2026-09-15 over all 51 shots in episodes 6 and 7 whose camera moves.

## The hypothesis that failed

Take 18 of episode 7 froze for 1.0 s at its start and held still for 26 % of its
length. Its plan reads:

> The camera tracks **a hand's breadth** to the right across the whole shot; his
> head turns to the other chair; his crossed foot comes down to the carpet.

A hand's breadth across a **7.29-second** shot is the smallest travel in the
vocabulary spread over one of the longest shots in the episode — about 0.015 m/s.
The obvious reading is that the camera has nothing to do for seven seconds, and
that the fault is the unmeasured relationship between two numbers each fine on
its own: the shot's length comes from the measured voice line, the camera's
travel is authored by hand, and nothing compares them.

That reading is wrong.

## What the measurement says

Travel converted to metres by the body-scale table (hand's breadth 0.10,
forearm 0.40, stride/pace 0.75, long stride 1.00, tread 0.25), divided by the
take's measured seconds:

| | n | median travel |
|---|---|---|
| froze (share > 5 % or start ≥ 0.5 s) | 4 | 0.037 m/s |
| clean | 47 | 0.072 m/s |

The medians differ, and the distributions say that means nothing. The four
freezes sit at **0.013, 0.015, 0.059 and 0.312 m/s** — spread across the entire
range, with the last among the fastest-travelling shots in either episode. And
the slowest shots are mostly clean:

| ep | shot | m/s | frozen |
|---|---|---|---|
| 6 | 24 | 0.013 | **yes** |
| 6 | 14 | 0.015 | no |
| 7 | 18 | 0.015 | **yes** |
| 6 | 4 | 0.015 | no |
| 7 | 0 | 0.016 | no |
| 7 | 12 | 0.016 | no |
| 6 | 13 | 0.016 | no |
| 7 | 2 | 0.312 | **yes** |

Episode 7 shot 0 and shot 12 travel a hand's breadth over 6.33 s — a slower
creep than shot 18's — and neither freezes. No threshold on this axis separates
the two groups, and any that appeared to would be fitted to four points.

## What actually fixes it

The retry ladder. `takes_r2v --retake=N` bumps the seed by `101 × tries` and
keeps the old file as `T<NN>_failN.mp4`. Measured on this episode:

- take 13: cut-landing 0/1 HARD, 75.0 → re-roll → **100.0**
- take 18: frozen 2.25 s, 39.6 → re-roll → 71.9 (frozen 1.0 s) → re-roll

4 of 51 moving shots froze, about 8 %, and the same shot renders clean on a
different seed with the same prose. That is sampling variance in MiniMax-H3, and
the cure is another sample, not another rule.

## Why this is written down

Because the hypothesis is a good one and it will be proposed again. It has the
right shape — the fault class this pipeline keeps producing is exactly "two
numbers, each fine, whose relationship nobody measures" — and that shape is why
it deserved measuring rather than believing.
