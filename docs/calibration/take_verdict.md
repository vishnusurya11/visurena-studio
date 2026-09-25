# take_verdict calibration

Benched by scripts/calibration/bench.py against the casebooks.

## Bench 2026-09-24 -- take_verdict@0b606bdc

rows 802 (154 without this judge's inputs, not counted); machine_version git:ceec663; flag rate 0.075; refusals per unit {'20260822113400/ep01': 11, '20260822113400/ep02': 7, '20260822113400/ep03': 15, '20260822113400/ep07': 2, '20260822113400/ep11': 6, '20260822113400/ep12': 7, '20260822113400/ep14': 8, '20260827135508/ep04': 1, '20260827135508/ep06': 1, '20260827135508/ep09': 2}; expected GPU minutes 420

- recall on owner rows: 0.000 [0.000, 0.000] on 0/0
- recall on all rows: 0.000 [0.000, 0.000] on 0/0
- synthetic (own column): 0.000 [0.000, 0.000] on 0/0
- reject-only recall (unknown class): 0.690 [0.508, 0.827] on 20/29
- false refusals (weighted): 0.065 [0.048, 0.087] on 40/619


| class | tp | fn | synthetic tp/n | fp | tn | unmeasured |
|---|---|---|---|---|---|---|
| pass | 0 | 0 | 0/0 | 40 | 579 | 0 |
| unknown | 20 | 9 | 0/0 | 0 | 0 | 154 |

misses (fault rows passed), by path:
- episodes/ep07/takes/r2v/attempts/T18_fail3.mp4
- episodes/ep11/takes/r2v/attempts/T00_fail1.mp4
- episodes/ep11/takes/r2v/attempts/T03_fail1.mp4
- episodes/ep11/takes/r2v/attempts/T06_fail2.mp4
- episodes/ep11/takes/r2v/attempts/T06_fail3.mp4
- episodes/ep11/takes/r2v/attempts/T15_fail1.mp4
- episodes/ep11/takes/r2v/attempts/T16_fail1.mp4
- episodes/ep11/takes/r2v/attempts/T20_fail1.mp4
- episodes/ep13/takes/r2v/attempts/T08_fail1.mp4
