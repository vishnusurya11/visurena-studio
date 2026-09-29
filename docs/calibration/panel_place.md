# panel_place — place constancy across a setup's panels (advisory)

Built 2026-09-28 from the stager agent's prototype (five-agent debate,
`docs/audit/2026-09-28_grid_place_constancy_plan.md`). `studio/measure/place.py`:
column light profile of the upper half, 8x8 structure of the wings (centre 40 % dropped),
light side (R-L)/(R+L); a panel is read against the staged room (`storyboard/anchors/<setup>.png`,
else the setup's place picture) and against its mirror.

## Numbers (CPU, 2026-09-28)

| panel | vs plate | prof_same | side panel / plate | reading |
|---|---|---|---|---|
| ep14 waterloo s05 | wide_establishing | -0.56 | +0.43 / -0.27 | MIRROR (rails right, plate left) |
| ep14 waterloo s07 | " | -0.36 | +0.33 / -0.27 | MIRROR |
| ep14 waterloo s08 | " | +0.87 | | held |
| ep14 waterloo s09 | " | +0.58 | | held |
| ep14 attic s21 | wide_establishing (night) | -0.04 | -0.08 / +0.35 | marginal |
| ep14 biology s00/s02/s03/s04 | wide_establishing | +0.25 / +0.36 / +0.23 / +0.29 | all +0.4..+0.5 | held — the re-dressing (a cabinet grid b invented) is invisible to this measure |
| ep06 knots s15 | wide_night | +0.84 | | copies the plate |
| ep06 road s04 | wide_establishing | +0.69 | | held |
| ep06 banks s26 | wide_night | +0.63 | | held |
| ep06 knots s11 / s12 | wide_night | flagged | | a PLANNED over-the-shoulder reverse pair — a true flip, not a fault |

Same-render pairs on ep14: profile 0.56, wings 0.47; different-render pairs 0.31 / 0.27.
A hue histogram, Lab mean and pHash separate nothing (ep14's within-setup hue similarity is
HIGHER than ep06's). The first measure kept as the negative result.

## Rule as built

`mirrored(read)`: `prof_same < 0` AND the light sides are opposite with both |side| > 0.08.
Catches s05, s07; misses s08's -0.10 (an advisory band under 0.15 would list it). A shot
whose prose names a reverse must be exempt before this is a wall.

## What it cannot see

Re-dressing on the same walls. That needs the VLM content rung asked "list the furniture
on the left wall / right wall" per panel, judged in code against the plate's list.

## Calibration owed

Five episodes' panels (ep06, ep09-13): recall on the owner's catches, false-refusal rate,
flag rate — a dated row here per run; a wall only after that.
