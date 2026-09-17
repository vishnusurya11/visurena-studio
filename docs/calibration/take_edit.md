# take_edit calibration -- episode 10, 2026-09-16

`studio/take_edit.py` reads one free series per take -- the mean |difference|
between consecutive frames on a 64x64 grey (DQ analyst G's `framediff.py`) --
and asks two things of it.

Source: every kept take in `library/20260822113400_a-study-in-scarlet/episodes/ep10/takes/r2v/T*.mp4`
with `placed_seconds` from `shots.json`; the superseded renders in
`attempts/` for the pulse.  The shipped module's own run, 2 s for 30 takes.

## post-cut: the frames the edit trims

The edit keeps `placed_seconds` of every take and trims the rest (6-22
frames: HANDLE + the token grid).  `post_cut` compares the trimmed steps'
mean and peak against the last `TAIL = 10` placed steps' mean:

```
fires  when  rest.mean > POST_CUT_RATIO (2.0) x last10.mean  AND  rest.max > POST_CUT_MAX (8.0)
```

| take | last 10 placed | trimmed mean | trimmed max | row |
|---|---|---|---|---|
| T28 | 4.07 | 8.48 | 14.5 | **adv** -- the collapse two frames past the cut (G §3) |
| T29 | 1.44 | 5.06 | 8.6 | **adv** |
| T06 | 4.86 | 5.84 | 6.9 | ok (ratio 1.2) |
| T04 | 2.21 | 2.60 | 6.7 | ok (under 8) |
| T31 | 3.82 | 3.35 | 4.8 | ok |
| the other 25 | 0.5-3.8 | 0.4-3.0 | <= 4.0 | ok |

Analyst G ran the same rule over ep05 and ep07: zero fires.  Two of thirty on
ep10, both the reviewer's run-out takes; the numbers separate by a factor of
two on the ratio and by 1.7 on the peak (T29 8.6 against T06 6.9).

## pulse: a period in the motion

```
detrend   the series less its DETREND = 73 frame centred moving mean (a push is a trend)
lags      PULSE_LAGS = 12..36 frames
fires     autocorrelation > PULSE_R = 0.5 at the lag, twice the lag and three times (PULSE_CYCLES = 3)
          AND the residual's std >= PULSE_AMP = 0.5 of the series' median step
period    the FUNDAMENTAL: the first autocorrelation peak over 0.5 from lag 3 up
```

| file | best lag | cycles | r | amp | fundamental | row |
|---|---|---|---|---|---|---|
| T05 | 23 | 5 | 0.85 | 0.65 | 23 | **adv** `23f x5 r 0.85` -- the breathing G named (§7) |
| T04 (current, post-review render) | 24 | 3 | 0.83 | 0.69 | 4 | **adv** `4f x3 r 0.83` -- every fourth step is 0, the next 2x: a 4-frame stutter, not a breath |
| T04_fail1 (the reviewed render) | 20 | 5 | 0.81 | 0.40 | 20 | ok -- under the amplitude floor |
| T21 | 12 | 3 | 0.73 | 0.13 | 4 | ok -- grain |
| T20 | 34 | 3 | 0.53 | 0.18 | 4 | ok -- grain on a static wide |
| T10 | 12 | 1 | 0.64 | 0.15 | 4 | ok |
| T01, T03, T24, T33 | 12-24 | 1 | 0.50-0.52 | 0.11-0.25 | -- | ok |
| T05_fail1, T05_fail2 | -- | 0 | 0.22-0.23 | 0.14-0.20 | -- | ok |
| the other 19 | -- | 0 | <= 0.38 | -- | -- | ok |

Without the amplitude floor the three-cycle rule fires on T05, T04, T21 and
T20; the last two correlate on a faint 4-frame ripple at a sixth of their
median step.  The floor is set where the data breaks: 0.65 / 0.69 above, 0.40
(T04_fail1) and 0.18 below.  T04_fail1 is a reviewed WATCH for another reason
(a figure standing while the camera walks) and its 20-frame, 5-cycle, r 0.81
signal at amp 0.40 is the nearest miss; the floor at 0.5 is one render wide
on that side.

A monotone push cannot fire: after the 73-frame detrend an accelerating push
leaves a residual at 0.1-0.2 of its median (the synthetic in
`tests/test_take_edit.py` reads 0.15) and no correlation over 0.5 at any lag.

## Both rows are advisory, scored 5

The score ranks attempts (best-of-N prefers the take that did not collapse or
breathe); neither row fails a take.  Promotion waits for a second episode's
populations.
