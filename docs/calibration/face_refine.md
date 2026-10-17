# Face refine gate -- calibration (2026-10-17)

The gate keeps a refined face crop only when it does no harm (`studio/face_refine.decide`,
measures in `studio/face_gate.py`). Calibrated on the 2026-10-16 F2/F3 test crops of Jekyll ep01
(`docs/audit/2026-10-16_model_tests/faces/`): F2 (H3 crop re-render, kept by the owner's eye)
against F3 (SeedVR2 on the crop, refused by eye: scratchy line noise, no features). Measures at
window scale (the crop shrunk back to the take's window, 96 px for T00/T22, 292 px for T19);
identity and the face count on the 768 crops, six samples each.

| take | arm | seam | face-region flicker take -> pasted | ratio | faces src/ref | identity src -> ref |
|---|---|---|---|---|---|---|
| T00 (wide, 30 px) | F2 | 7.3 | 12.34 -> 11.74 | 0.95 | 4 / 4 | 0.145 -> 0.589 |
| T00 | F3 | 2.0 | 12.34 -> 16.04 | 1.30 | 4 / 4 | 0.145 -> 0.273 |
| T22 (wide, 36 px) | F2 | 8.0 | 20.39 -> 19.24 | 0.94 | 5 / 5 | 0.242 -> 0.439 |
| T22 | F3 | 2.0 | 20.39 -> 23.41 | 1.15 | 5 / 5 | 0.242 -> 0.285 |
| T19 (medium close, 123 px) | F2 | 9.2 | 8.05 -> 6.51 | 0.81 | 6 / 6 | 0.804 -> 0.845 |
| T19 | F3 | 2.7 | 8.05 -> 10.62 | 1.32 | 6 / 6 | 0.804 -> 0.781 |

Walls (`studio/face_refine.py`):
- **flicker** pasted <= 1.10 x the take's + 0.5: F2 0.81-0.95 pass, F3 1.15-1.32 fail. The one
  measure that separates the arms.
- **seam** <= 18 levels in the feather band: F2 7.3-9.2. F3 is lower (it hardly changes the
  border), so the seam wall guards a regression; it does not separate these two arms.
- **identity** may not drop by more than 0.05 (the research plan's bar); F2 raised it on every
  take, F3 dropped T19 by 0.023.
- **faces** unchanged, one missed detection allowed: equal on all six.

Thin: three takes, one seed each. Recalibrate on the first episodes' refine.json rows (every row
carries its measures) before tightening anything.

Matching (who each track is) was checked by eye on ep01's six selected takes (T00, T06, T07,
T18, T22; T03 has no small face): Lab colour of the head and hat, half facenet, plus a plan
position only from "at the LEFT/CENTRE/RIGHT" said of one subject. A travel direction ("walk on
to the RIGHT") put Utterson on Enfield's face on T22 and is no longer read; hue-only colour put
Hyde's face on the child on T07 (a black hat has no hue) and Lab replaced it.
