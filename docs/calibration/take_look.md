# take_look calibration -- episode 10, 2026-09-16

`studio/take_look.py` reads 8 frames spread evenly over a take (first and last
included, decoded at native size by one ffmpeg `select`) with
`studio/look_gate.py`'s own numbers -- 5th-percentile luma, near-black share,
dominant-hue share, mean luma -- and judges the take's medians and its ends.

Source: every kept take in `library/20260822113400_a-study-in-scarlet/episodes/ep10/takes/r2v/T*.mp4`,
768x768.  The analysis was DQ analyst C's (`scratchpad/dq10/C.md`, 9 frames per
take); the shipped module's own run reproduces it to the digit on every take
named below (11 s for 30 takes, CPU).

## The walls

```
HARD      look_gate.no_black_floor(median p5, median near-black)    p5 > 15 and near-black < 0.10
ADVISORY  near-black first -> last drops by BLACK_DROP  = 0.20      (scored 15)
          or dominant-hue share rises by SHARE_RISE     = 0.25
ADVISORY  median mean luma > LEVEL_MEAN = 100 with median p5 > 15    (scored 5)
```

## The table (ep10, shipped module)

| take | p5 | black | hue | first -> last black | first -> last hue | row |
|---|---|---|---|---|---|---|
| T20 | 43 | 0.01 | 0.40 | .01 -> .01 | .38 -> .44 | **HARD** no floor -- the one print in the cut (a sunlit wide, waved through at sheet time as "sunlit wide", Q20_0 p5 53) |
| T16 | 3 | 0.36 | 0.42 | .45 -> .18 | .31 -> .75 | adv: black lost, hue rose -- the doorway push ends on a face filling the frame, jamb gone |
| T28 | 0 | 0.56 | 0.51 | .66 -> .28 | .39 -> .79 | adv: black lost, hue rose -- the head turn to the window lights the wall |
| T18 | 7 | 0.20 | 0.38 | .49 -> .16 | .49 -> .38 | adv: black lost -- **the known false alarm**: a two-shot take whose planned cut goes from a hat under the doorway to a man walking off in the sun |
| T31 | 2 | 0.63 | 0.41 | .58 -> .69 | .45 -> .39 | ok -- the cleanest take, the reference for "obeyed" |
| T07 | 1 | 0.65 | 0.24 | .54 -> .70 | .27 -> .24 | ok (darkens on the push) |
| T13 | 0 | 0.52 | 0.34 | .39 -> .53 | .34 -> .35 | ok (darkens) |
| T15 | 3 | 0.43 | 0.42 | .36 -> .50 | .36 -> .39 | ok (darkens) |
| T03 | 17 | 0.12 | 0.28 | .11 -> .12 | .33 -> .27 | ok -- one frame short of the no-floor rule, as analyst C said |
| T25 | 2 | 0.52 | 0.51 | -- | .32 -> .53 (+0.21) | ok, under SHARE_RISE |
| the other 20 | 0-8 | 0.35-0.86 | 0.11-0.58 | -- | -- | ok |

1 hard, 3 advisory (2 named faults + T18), 26 clean.  ep05 / ep07 / ep09 under
analyst C's per-take medians: takes with no floor 3 / 1 / 15, so the hard rung
is live on the bad episode and nearly quiet on the good ones.

## Level

The level advisory (mean > 100 with p5 > 15) is subsumed by the hard rung on
T20 (117 / 43 / 0.01) and quiet on every other ep10 take (T18 at 98 / 7 is the
closest).  Analyst C's per-take medians say it fails 15 of ep09's 28 takes
(episode median 95 / 17.8) and none of ep05 / ep07; the ep09 takes it names
are ones whose near-black is kept by a shadow while the picture sits a stop
up -- a print between two projections.

## The T18 false alarm, and why it stays

The row takes `(video, seconds)` and reads the whole take.  A two-shot take's
planned internal cut is a planned change of picture, and the first -> last
drop across it is not a loss.  Reading the first segment only would need the
take's anchors (as `face_end.row` does) -- a one-argument change to the
interface when the row moves from advisory to anything harder.  Two-shot takes
in ep10: T18, T22, T29, T31; only T18 crosses a light change.

## Per-picture `one_hue` (studio/look_gate.py)

The same analysis moved the share wall behind the floor: `one_hue` is now
`lifted and (share > ONE_HUE_SHARE or entropy < HUE_ENTROPY_FLOOR)`.  The
unconditional share wall had fired at sheet time on Q09_0 (0.60), Q18_0A
(0.64) and Q28_0A (0.85 over p5 ~ 0, the lamp insert), and on 45/225 ep05 and
31/225 ep07 take frames -- the good episodes.  The roll-up is unchanged in
effect (ep09 median share 0.67 over p5 17.8 / near-black 0.09 still fails
both ways; ep07 and ep10 pass), and `tests/test_look_gate.py::TestCalibration`
still holds on the cells on disk.
