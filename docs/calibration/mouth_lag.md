# mouth_lag calibration

Benched by scripts/calibration/bench.py against the casebooks.

## Bench 2026-10-22 -- mouth_lag@20f6482e

standing: advisory: production never refuses on it; no mouth reader passes the exam (2026-10-21)

rows 804 (804 without this judge's inputs, not counted); machine_version git:c26aab7; flag rate 0.000; refused artefacts per unit {}; distinct (artefact, rule) refusals 0; expected GPU minutes 0

### owner truth (the headline)

- recall on owner rows: unarmed, n=0 (NO LABELS)
  - recall, episode-cluster bootstrap: too few clusters (0 episodes, under 10)
- false refusals on owner rows: unarmed, n=0 (NO LABELS)
  - false refusals, episode-cluster bootstrap: too few clusters (0 episodes, under 10)

### internal consistency (agent / default / synthetic rows: the ladder agreeing with itself, not truth)

- recall on all rows: 0.000 [0.000, 1.000] on 0/0
- synthetic (own column): 0.000 [0.000, 1.000] on 0/0
- reject-only recall (unknown class): 0.000 [0.000, 1.000] on 0/0
- false refusals on all rows: 0.000 [0.000, 1.000] on 0/0; weighted share 0.000

| class | tp | fn | synthetic tp/n | fp | tn | unmeasured |
|---|---|---|---|---|---|---|
| pass | 0 | 0 | 0/0 | 0 | 0 | 619 |
| unknown | 0 | 0 | 0/0 | 0 | 0 | 185 |

misses (fault rows passed), by path:
- none
