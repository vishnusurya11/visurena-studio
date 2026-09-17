# take_zoom calibration -- episode 10, 2026-09-16

`studio/take_zoom.py` measures how far a take's push actually travelled: the
apparent scale change from the first frame to the last (`ratio` > 1 tighter,
< 1 pulled back).  This is the calibration that chose its walls.

Source: every take in `library/20260822113400_a-study-in-scarlet/episodes/ep10/takes/r2v/T*.mp4`
and every superseded render in `.../takes/r2v/attempts/`, 768x768, read with the
shipped settings (`GRID=9`, `RADIUS=0.35`, `SAMPLES=12`, `SPLIT=1.07`,
`MIN_INLIERS=8`).  Two-shot takes (T18, T22, T29, T31) are read up to their
internal pin (the second anchor's frame in `shots.json`).  The plan's `motion`
string gives the planned reach.  No GPU, no credit: numpy + PIL + ffmpeg, about
2-5 s per take on CPU.

Labels are the reviewer's frame strips: **over-pushed** (ended a size tighter
than planned) = T05 first render (`T05_fail1.mp4`, the canonical positive:
it ends on nostrils), T12, T13, T16, T25, T28, T33; **fine** = T07, T08, T09,
T14, T21, T24, T27.

## What is measured, and why the subject

Between consecutive sampled frames a 9x9 lattice of overlapping Hann windows is
phase-correlated; each textured window gives one displacement vector.  A zoom
about the centre c moves content at p by `d = (s - 1)(p - c) + t`, which is
linear in `(s - 1, t)`, so RANSAC over two-window samples finds the largest set
of windows agreeing on one similarity and least squares on those inliers gives
the step's scale.  Steps compound into the ratio; a step over `SPLIT` is
re-read through its middle frame so every phase correlation stays inside its
window.

The same displacement field is fitted twice:

- `camera`: every window votes.  This is the whole-frame RANSAC the brief
  asked for -- the room, the plate, the camera's own move.
- `ratio`: only the windows within `RADIUS` (0.35 of the frame) of the centre
  vote.  The plan centres the frame on the thing it pushes in on, and that
  thing is what the reviewer sizes.

They differ where the model walks the subject at the lens while the room stays
put (T12: 1.98 subject vs 1.80 camera; T33: 1.52 vs 1.44; T29: 1.31 vs 1.59
the other way, the window frame growing while the flame at centre does not).
Against the labels the whole-frame read separates by **-0.11** (T33 1.44 sits
under fine T14 1.47 and T09 1.55); the subject read by **+0.02**.  The subject
read is judged; both are returned.

## The labelled takes

| take | reviewer | size | planned reach | dir | ratio (subject) | camera | min inliers | monotonic | read to frame | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| T16.mp4 | over-pushed | medium_close | forearm | push | 2.40 | 2.35 | 29 | yes | end | HARD: planned forearm travelled 2.40x, over the 2.00x wall |
| T13.mp4 | over-pushed | medium_close | hand | push | 2.16 | 2.06 | 44 | yes | end | HARD: planned hand travelled 2.16x, over the 1.55x wall |
| T25.mp4 | over-pushed | close | hand | push | 2.12 | 2.05 | 34 | yes | end | HARD: planned hand travelled 2.12x, over the 1.55x wall |
| T12.mp4 | over-pushed | medium | stride | push | 1.98 | 1.80 | 17 | yes | end | ok |
| T05_fail1.mp4 | over-pushed | close | hand | pull | 1.93 | 1.91 | 47 | yes | end | HARD: planned hand travelled 1.93x, over the 1.55x wall |
| T28.mp4 | over-pushed | close | hand | push | 1.63 | 1.59 | 11 | yes | end | HARD: planned hand travelled 1.63x, over the 1.55x wall |
| T33.mp4 | over-pushed | medium | stride | push | 1.52 | 1.44 | 38 | yes | end | ok |
| T14.mp4 | fine | close | hand | push | 1.50 | 1.47 | 36 | yes | end | advisory: planned hand travelled 1.50x, near the 1.55x wall |
| T09.mp4 | fine | insert | hand | push | 1.48 | 1.55 | 15 | yes | end | advisory: planned hand travelled 1.48x, near the 1.55x wall |
| T21.mp4 | fine | medium | stride | push | 1.47 | 1.44 | 35 | yes | end | ok |
| T07.mp4 | fine | medium_close | forearm | push | 1.46 | 1.44 | 31 | yes | end | ok |
| T24.mp4 | fine | insert | hand | push | 1.37 | 1.36 | 43 | yes | end | ok |
| T08.mp4 | fine | close | hand | push | 1.28 | 1.26 | 49 | yes | end | ok |
| T27.mp4 | fine | medium_close | hand | push | 1.26 | 1.24 | 10 | yes | end | ok |

## Walls chosen

| constant | value | applies to | evidence |
|---|---|---|---|
| `OVER_PUSH` | 1.55 | a finger's / a hand's breadth | hand-planned over-pushed: T28 1.63, T05_fail1 1.93, T25 2.12, T13 2.16; hand-planned fine: T14 1.50, T09 1.48, T24 1.37, T08 1.28, T27 1.26. Margin **+0.08 above, -0.05 below**. |
| `OVER_PUSH_LONG` | 2.0 | a forearm, one long stride | forearm: T16 2.40 over-pushed vs T07 1.46 fine (T01 1.48 unlabelled). Stride: T12 1.98 over-pushed sits 0.02 UNDER the wall, T33 1.52 over-pushed is not caught, T21 1.47 fine. Only two labelled per reach: a guess held by the data, not a fit. |
| `OVER_PUSH_ANY` | 2.5 | any plan | T03_fail1 2.74 is the only take over it; nothing labelled fine is within 1.0 of it. |
| `ADVISORY_PUSH` | 1.4 | hand / finger, advisory | flags T14 1.50 and T09 1.48 (both fine) as "near the wall" -- a look, not a fail. |
| `WRONG_WAY` | 1.15 | advisory | a planned pull-back that read tighter (or the reverse) by this much. T05 (current, planned pull-back) reads 0.99: no pull happened, and no advisory fires at 1.01. |

### Honest reading of the margin

Every fine take is under 1.55; six of the seven over-pushed takes are over it
and the seventh, T33 at 1.52, is under it by 0.03.  The gap between the
nearest hand-planned pair (T28 1.63 / T14 1.50) is 0.13, and the read-to-read
noise across the lattice settings swept below is about +-0.05.  That is a
**fit to fourteen labelled takes, not a separation**: a wall anywhere in
1.51-1.62 gives the same verdicts.  Six of the seven over-pushed takes read >=
1.63 and every fine take <= 1.50; the strong cases (>= 1.9: T05_fail1, T12,
T25, T13, T16) are clear of every fine take by 0.4 or more, and those are the
takes that "end on nostrils".  T33 (1.52) is the one the measure cannot
honestly call: it is 0.02 from T14, and it was planned as a stride, which the
reach walls allow to 2.0 -- under `judge` it passes.  T12 (1.98, stride) sits
0.02 under its wall and passes too.  If the owner wants stride-planned pushes
held to a hand's breadth, `REACH_WALLS["stride"]` is the one line to change:
at 1.55 it catches T12 (1.98) and passes T21 (1.47), and T33 stays a hair
under.

### Settings swept

Subject-region RANSAC, separation = (lowest over-pushed) - (highest fine):

| GRID | RADIUS | downsample | SPLIT | SAMPLES | separation | note |
|---|---|---|---|---|---|---|
| 9 | whole frame | 1 | 1.12 | 6 | -0.20 | the brief's whole-frame read: T12 1.27, T25 1.34, T33 1.34 vs fine T08 1.27, T24 1.35 |
| 9 | 0.20 | 1 | 1.12 | 6 | -0.07 | too few windows: T05_fail1 on 7 inliers reads 1.46 |
| 9 | 0.27 | 1 | 1.12 | 6 | -0.12 | T09 (hand sliding on the book) 1.56 on 9 inliers |
| 9 | 0.27 | 2 | 1.12 | 6 | +0.05 | T28 on 4 inliers |
| 9 | 0.35 | 1 | 1.12 | 6 | +0.02 | T12 1.60 on 8 inliers |
| 9 | 0.35 | 1 | 1.07 | 6 | +0.01 | |
| 9 | 0.35 | 1 | 1.04 | 12 | +0.01 | |
| 9 | 0.35 | 1 | 1.07 | 12 | **+0.02** | **shipped**: T12 1.98 on 17 inliers, T28 1.63 on 11 |
| 9 | 0.35 | 1 | 1.12 | 12 | +0.02 | |
| 9 | 0.50 | 1 | 1.12 | 6 | -0.20 | |
| 13 | any | any | 1.12 | 6 | -0.11 to -0.40 | 110 px windows cannot hold a 12 % step: T05_fail1 reads 1.21 |

Two other estimators were tried and rejected: a scale sweep of the centre crop
by normalised cross-correlation, direct first-to-last (separation -1.3: the
subject's non-rigid change kills the NCC peak and the sweep runs to its
bound) and compounded over the sampled frames (-0.17).

### Synthetic accuracy (the test fixtures, 256 px, shipped settings)

| truth | read | error |
|---|---|---|
| 0.50 | 0.494 | -1.1 % |
| 0.70 | 0.697 | -0.4 % |
| 1.00 | 1.000 | 0.0 % |
| 1.30 | 1.288 | -1.0 % |
| 1.80 | 1.764 | -2.0 % |
| 2.50 | 2.422 | -3.1 % |
| 1.50 with a walker a fifth of the frame wide crossing | 1.479 | -1.4 % (RANSAC discards him from both reads) |
| 1.60 a half-frame subject growing in a still room | 1.552 subject, 1.198 camera | the T12 case |

The reads on real takes are far noisier than this (non-rigid faces, hands,
cloth): the sweep above, not this table, is the error bar.

## The unlabelled takes

| take | reviewer | size | planned reach | dir | ratio (subject) | camera | min inliers | monotonic | read to frame | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| T00.mp4 | - | wide | hand | push | 1.20 | 1.20 | 49 | yes | end | ok |
| T01.mp4 | - | medium | forearm | push | 1.48 | 1.48 | 44 | yes | end | ok |
| T02.mp4 | - | insert | hand | push | 1.72 | 1.73 | 40 | yes | end | HARD: planned hand travelled 1.72x, over the 1.55x wall |
| T03.mp4 | - | wide | hand | push | 1.56 | 1.26 | 28 | yes | end | HARD: planned hand travelled 1.56x, over the 1.55x wall |
| T04.mp4 | - | medium | hand | push | 1.11 | 1.12 | 11 | no | end | advisory: the zoom reversed mid-take |
| T05.mp4 | - | close | hand | pull | 0.99 | 0.95 | 9 | no | end | advisory: the zoom reversed mid-take |
| T06.mp4 | - | medium | stride | push | 1.14 | 1.57 | 8 | no | end | advisory: the zoom reversed mid-take |
| T10.mp4 | - | medium_close | hand | push | 1.23 | 1.22 | 48 | yes | end | ok |
| T11.mp4 | - | insert | hand | push | 1.34 | 1.35 | 33 | yes | end | ok |
| T15.mp4 | - | medium | hand | push | 1.19 | 1.19 | 21 | yes | end | ok |
| T17.mp4 | - | insert | hand | push | 1.73 | 1.72 | 13 | yes | end | HARD: planned hand travelled 1.73x, over the 1.55x wall |
| T18.mp4 | - | medium_close | hand | push | 1.27 | 1.26 | 42 | yes | 85 | ok |
| T20.mp4 | - | wide | hand | push | 1.12 | 1.14 | 49 | yes | end | ok |
| T22.mp4 | - | close | hand | push | 1.26 | 1.24 | 32 | yes | 77 | ok |
| T26.mp4 | - | insert | hand | push | 1.14 | 1.14 | 36 | yes | end | ok |
| T29.mp4 | - | insert | hand | push | 1.31 | 1.59 | 25 | yes | 145 | ok |
| T31.mp4 | - | medium | stride | push | 1.43 | 1.40 | 23 | yes | 85 | ok |
| T03_fail1.mp4 | - | wide | hand | push | 2.74 | 2.11 | 18 | yes | end | HARD: planned hand travelled 2.74x, over the 1.55x wall |
| T04_fail1.mp4 | - | medium | hand | push | 1.17 | 1.09 | 9 | no | end | advisory: the zoom reversed mid-take |
| T05_fail2.mp4 | - | close | hand | pull | 2.01 | 1.98 | 48 | yes | end | HARD: planned hand travelled 2.01x, over the 1.55x wall |
| T15_fail1.mp4 | - | medium | hand | push | 1.34 | 1.36 | 22 | yes | end | ok |
| T15_fail2.mp4 | - | medium | hand | push | 1.25 | 1.25 | 16 | yes | end | ok |
| T20_fail1.mp4 | - | wide | hand | push | 1.29 | 1.27 | 47 | yes | end | ok |
| T29_fail1.mp4 | - | insert | hand | push | 1.29 | 1.41 | 36 | yes | 145 | ok |

Flags on unlabelled takes, checked on their frame strips:

- **T03 1.56 (hard by 0.01)**: real.  The plan says "both gate posts keep the
  frame edges"; they leave it and the villa grows about 1.7x.  Its superseded
  render `T03_fail1` reads 2.74.
- **T02 1.72 (hard)**: real by eye; the hand on the rifle grows about 1.7x.
- **T17 1.73 (hard)**: doubtful.  The fist drops out of the bottom of frame as
  planned and the last sample is bare boards; the read may come from the
  boards sliding.  Check by eye before trusting it.
- **T05_fail1 / T05_fail2 (hard, 1.93 / 2.01)**: the plan now says pull-back
  (shot 5 was rewritten after these), so the verdict is "over the wall" plus
  "planned pull-back but the picture read 1.93x".  Under the push they were
  rendered from, they are hard by 0.4.
- **T05 (current) 0.99**: the pull-back did not happen; not an over-push.
- Low-inlier reads (T04 11, T05 9, T06 8, T27 10, T04_fail1 9): measured, but
  on the fewest windows; T06 (Brigham walking, stride) reads 1.14 subject vs
  1.57 camera and is non-monotonic -- the man's walk, not the camera's.
