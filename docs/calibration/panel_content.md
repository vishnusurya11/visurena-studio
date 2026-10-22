# panel_content calibration

Benched by scripts/calibration/bench.py against the casebooks.

## Bench 2026-09-24 -- panel_content@d4999c73

rows 196 (104 without this judge's inputs, not counted); machine_version git:ceec663; flag rate 0.025; refusals per unit {'20260827135508/ep09': 4, '20260827135508/ep10': 1}; expected GPU minutes 35

- recall on owner rows: 0.000 [0.000, 0.000] on 0/0
- recall on all rows: 0.000 [0.000, 0.000] on 0/0
- synthetic (own column): 0.000 [0.000, 0.000] on 0/0
- reject-only recall (unknown class): 0.174 [0.070, 0.371] on 4/23
- false refusals (weighted): 0.015 [0.003, 0.078] on 1/69


| class | tp | fn | synthetic tp/n | fp | tn | unmeasured |
|---|---|---|---|---|---|---|
| pass | 0 | 0 | 0/0 | 1 | 68 | 104 |
| unknown | 4 | 19 | 0/0 | 0 | 0 | 0 |

misses (fault rows passed), by path:
- episodes/ep09/storyboard_prev_v1/shot_00.png
- episodes/ep09/storyboard_prev_v1/shot_01.png
- episodes/ep09/storyboard_prev_v1/shot_02.png
- episodes/ep09/storyboard_prev_v1/shot_03.png
- episodes/ep09/storyboard_prev_v1/shot_05.png
- episodes/ep09/storyboard_prev_v1/shot_06.png
- episodes/ep09/storyboard_prev_v1/shot_07.png
- episodes/ep09/storyboard_prev_v1/shot_08.png
- episodes/ep09/storyboard_prev_v1/shot_09.png
- episodes/ep09/storyboard_prev_v1/shot_11.png
- episodes/ep09/storyboard_prev_v1/shot_12.png
- episodes/ep09/storyboard_prev_v1/shot_13.png
- episodes/ep09/storyboard_prev_v1/shot_14.png
- episodes/ep09/storyboard_prev_v1/shot_15.png
- episodes/ep09/storyboard_prev_v1/shot_16.png
- episodes/ep09/storyboard_prev_v1/shot_17.png
- episodes/ep09/storyboard_prev_v1/shot_19.png
- episodes/ep09/storyboard_prev_v1/shot_20.png
- episodes/ep09/storyboard_prev_v1/shot_22.png

## Bench 2026-10-22 -- panel_content@102307af

rows 197 (105 without this judge's inputs, not counted); machine_version git:71aaf69; flag rate 0.025; refused artefacts per unit {'20260827135508/ep09': 4, '20260827135508/ep10': 1}; distinct (artefact, rule) refusals 9; expected GPU minutes 35

### owner truth (the headline)

- recall on owner rows: unarmed, n=0 (NO LABELS)
  - recall, episode-cluster bootstrap: too few clusters (0 episodes, under 10)
- false refusals on owner rows: unarmed, n=0 (NO LABELS)
  - false refusals, episode-cluster bootstrap: too few clusters (0 episodes, under 10)

### internal consistency (agent / default / synthetic rows: the ladder agreeing with itself, not truth)

- recall on all rows: 0.000 [0.000, 1.000] on 0/0
- synthetic (own column): 0.000 [0.000, 1.000] on 0/0
- reject-only recall (unknown class): 0.174 [0.070, 0.371] on 4/23
- false refusals on all rows: 0.015 [0.003, 0.078] on 1/69; weighted share 0.015

| class | tp | fn | synthetic tp/n | fp | tn | unmeasured |
|---|---|---|---|---|---|---|
| copies | 0 | 0 | 0/0 | 0 | 0 | 1 |
| pass | 0 | 0 | 0/0 | 1 | 68 | 104 |
| unknown | 4 | 19 | 0/0 | 0 | 0 | 0 |

misses (fault rows passed), by path:
- episodes/ep09/storyboard_prev_v1/shot_00.png
- episodes/ep09/storyboard_prev_v1/shot_01.png
- episodes/ep09/storyboard_prev_v1/shot_02.png
- episodes/ep09/storyboard_prev_v1/shot_03.png
- episodes/ep09/storyboard_prev_v1/shot_05.png
- episodes/ep09/storyboard_prev_v1/shot_06.png
- episodes/ep09/storyboard_prev_v1/shot_07.png
- episodes/ep09/storyboard_prev_v1/shot_08.png
- episodes/ep09/storyboard_prev_v1/shot_09.png
- episodes/ep09/storyboard_prev_v1/shot_11.png
- episodes/ep09/storyboard_prev_v1/shot_12.png
- episodes/ep09/storyboard_prev_v1/shot_13.png
- episodes/ep09/storyboard_prev_v1/shot_14.png
- episodes/ep09/storyboard_prev_v1/shot_15.png
- episodes/ep09/storyboard_prev_v1/shot_16.png
- episodes/ep09/storyboard_prev_v1/shot_17.png
- episodes/ep09/storyboard_prev_v1/shot_19.png
- episodes/ep09/storyboard_prev_v1/shot_20.png
- episodes/ep09/storyboard_prev_v1/shot_22.png
