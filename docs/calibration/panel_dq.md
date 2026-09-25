# panel_dq calibration

Benched by scripts/calibration/bench.py against the casebooks.

## Bench 2026-09-24 -- panel_dq@4c23e62a

rows 196 (0 without this judge's inputs, not counted); machine_version git:ceec663; flag rate 0.046; refusals per unit {'20260827135508/ep05': 5, '20260827135508/ep07': 3, '20260827135508/ep09': 1}; expected GPU minutes 63

- recall on owner rows: 0.000 [0.000, 0.000] on 0/0
- recall on all rows: 0.000 [0.000, 0.000] on 0/0
- synthetic (own column): 0.000 [0.000, 0.000] on 0/0
- reject-only recall (unknown class): 0.043 [0.008, 0.210] on 1/23
- false refusals (weighted): 0.046 [0.024, 0.089] on 8/173


| class | tp | fn | synthetic tp/n | fp | tn | unmeasured |
|---|---|---|---|---|---|---|
| pass | 0 | 0 | 0/0 | 8 | 165 | 0 |
| unknown | 1 | 22 | 0/0 | 0 | 0 | 0 |

misses (fault rows passed), by path:
- episodes/ep09/storyboard_prev_v1/shot_00.png
- episodes/ep09/storyboard_prev_v1/shot_01.png
- episodes/ep09/storyboard_prev_v1/shot_02.png
- episodes/ep09/storyboard_prev_v1/shot_03.png
- episodes/ep09/storyboard_prev_v1/shot_04.png
- episodes/ep09/storyboard_prev_v1/shot_05.png
- episodes/ep09/storyboard_prev_v1/shot_06.png
- episodes/ep09/storyboard_prev_v1/shot_07.png
- episodes/ep09/storyboard_prev_v1/shot_08.png
- episodes/ep09/storyboard_prev_v1/shot_09.png
- episodes/ep09/storyboard_prev_v1/shot_10.png
- episodes/ep09/storyboard_prev_v1/shot_11.png
- episodes/ep09/storyboard_prev_v1/shot_13.png
- episodes/ep09/storyboard_prev_v1/shot_14.png
- episodes/ep09/storyboard_prev_v1/shot_15.png
- episodes/ep09/storyboard_prev_v1/shot_16.png
- episodes/ep09/storyboard_prev_v1/shot_17.png
- episodes/ep09/storyboard_prev_v1/shot_18.png
- episodes/ep09/storyboard_prev_v1/shot_19.png
- episodes/ep09/storyboard_prev_v1/shot_20.png
- episodes/ep09/storyboard_prev_v1/shot_21.png
- episodes/ep09/storyboard_prev_v1/shot_22.png
