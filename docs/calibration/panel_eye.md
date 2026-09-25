# panel_eye — the panel judge, measured on real panels

## First contact 2026-09-25 — one accepted, published episode, 23 panels

Run with the live tools (DWPose keypoints, the Qwen3-VL size read, EasyOCR,
facenet faces, and the box workflow for hats and landmarks).

| measure | read | ruling |
|---|---|---|
| landmark (box workflow) | 587 faults over 23 panels: 225 "bridge" boxes on one panel, 39 "gasworks", 30 "windmill"; every word asked returned masks | the installed route (LayerMask ObjectDetectorMask over SAM) is not a scored detector; **not measured** until a node emits boxes with scores and labels (`panel_eye.SCORED_BOXES = False`) |
| hat (box workflow) | no fault fired, but the same unscored route | not measured, same switch |
| cost | 27 words × 23 panels = 621 GPU jobs; 4,204 s wall for the judge | with the box asks off: keypoints + one size read per panel |
| posture (stored content row) | 1 fault, shot 18: standing where the plan asks lying | a real catch — the fault class the owner caught by eye on this episode's takes, now read at the panel |
| framing (keypoints vs planned size) | 5 advisories | advisory as designed; the size read is the second vote |
| stacked, copy, clones, lettering | 0 | — |

The first run of the judge also died on a 120 s ask timeout while another
session's render held the shared GPU; the per-ask timeout is 900 s and a dead
ask is a missing measure for that panel, never a crash of the judge.
