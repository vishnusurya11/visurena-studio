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

## Jekyll ep01 (Kawajiri noir, 2026-10-18): the first real refine.json rows (P07, 2026-10-19)

Two takes refined; six picks ended `no_faces` (T05, T06, T13, T21, T23, T24: 579 s of CPU tracking
bought nothing, because the tracker finds faces under 60 px and these were bigger). Measures at
window scale from `takes/r2v/refine.json`:

| take | face | seam | flicker src -> refined | ratio | faces | identity src -> ref |
|---|---|---|---|---|---|---|
| T08 | child_of_hyde_incident | 12.44 | 17.44 -> 15.64 | 0.90 | 1 / 1 | 0.222 -> 0.426 |
| T18 | gabriel_john_utterson | 11.74 | 23.36 -> 17.75 | 0.76 | 1 / 1 | 0.362 -> 0.729 |
| T18 | richard_enfield | 12.94 | 20.17 -> 14.04 | 0.70 | 1 / 1 | 0.283 -> 0.833 |

- Seam 11.7-12.9 and flicker ratio 0.70-0.90: both inside the walls; **SEAM_MAX stays 18**.
- Identity gains +0.20 (T08), +0.37 and +0.55 (T18): the refine does what it is for on a face under
  60 px, and nothing on a face the tracker cannot find (it is already readable).
- Selection therefore reads the warp measure's `tracks: [{median_px, life}]` (render px), never
  face-at-end (T08's is 0.31 while its child track is under 60 px). A take is declined only when
  every planned face is tracked, for >= 80 % of the take, at >= 60 px.
- Paste order: cut scale, then the one upscale (owner 2026-10-18, 24caaeb), replacing the 2026-10-17
  "after the 4x" text above. The idle-GPU A/B on T18 (sharpness and facenet identity, before/after
  the order change) is still owed; never auto-revert on it.

## Every soft face (2026-10-19, face-blur fixes #1-#2; owner: "fix that")

The 60 px wall above declined faces of 60-110 px, whose eye is 5-10 px: the mush the owner named on
ep01 (docs/audit/2026-10-19_face_blur/pipeline_audit.md section 2). Now:

- **Wall** `SMALL_FACE_PX` 120, read per track as its smallest face after a running median over 51
  frames; no plan size, no face-at-end. ep01 replay (fixture of the audit's face_yolov8m samples):
  T01 T05 T06 T08 T10 T13 T15 T18 T20 T23 T26, 1,512 s priced (T08 and T18 were 363 s of it).
- **Denoise** `denoise_for(px)` = 0.45 + 0.05 x log2(60 / px), held to 0.40-0.55: 0.45 stays the
  point the owner kept (T08 55 px, T18 41 px); 30 px reads 0.50, 120 px 0.40. Uncalibrated beyond
  that point: the bench's arm A2 measures it. Every refine.json person row carries `denoise` and
  `face_px` so it can be refit.
- **Walls unchanged** (identity, seam, flicker, faces, change). The window now follows the face's
  smoothed size, so seam and flicker are measured with every window brought to the track's median
  side (`face_gate.at_side`).
