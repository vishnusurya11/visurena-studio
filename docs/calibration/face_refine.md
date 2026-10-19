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
- **seam** <= 18 levels in the feather band (2026-10-17; round 2 below measures it outside the head, wall 10): F2 7.3-9.2. F3 is lower (it hardly changes the
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

- Seam 11.7-12.9 and flicker ratio 0.70-0.90: both inside the walls; SEAM_MAX stayed 18 then (round 2 below: 10, measured outside the head).
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
- **Pre-filter reads the smallest face too.** A take is declined before the tracker only when the
  warp gate's MTCNN tracks are >= 120 px at their smallest (`min_px`, running median over 51 frames;
  recorded from 2026-10-19), never their median (a push-in from 80 to 300 px has a median near 190).
  The one 120 px wall is read on boxes from two detectors (MTCNN there, face_yolov8m here) that
  draw a face box differently; uncalibrated between them, so the bench should log both on its takes.

## Round 2 (2026-10-19, face-blur round 2: docs/audit/2026-10-19_face_blur/PLAN_FINAL.md 1a-3)

Round 1 (`docs/audit/2026-10-19_face_blur/bench/BENCH.md`) refused 3 of 15 faces on the seam and read
every refine as WORSE on its eye measure, while the strips showed drawn eyes where the takes had
smudges. Round 2 re-measures round 1's own 15 refined crops through the production gate
(`scripts/episode/face_refine.gate_job`, the real CCIP / clip_vision_h worker, facenet, CPU+GPU, no
render); the inputs to every wall are the fixture `tests/fixtures/face_blur_round1_rows.json`.

| take | face | px | paste | old seam (wall 18) | seam, feather | seam, paste used | drift | CCIP sheet src -> ref | clip src -> ref | facenet src -> ref | eye src -> ref | round 1 | round 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T01 | Utterson | 38 | soft | 21.5 | 11.8 | 7.3 | 24.2 | 0.154 -> 0.052 | 0.82 -> 0.88 | 0.04 -> 0.58 | 54 -> 61 | seam 21.5 &gt; 18.0 | kept |
| T01 | Enfield | 33 | soft | 20.1 | 11.1 | 5.6 | 24.1 | 0.100 -> 0.044 | 0.81 -> 0.89 | 0.31 -> 0.68 | 55 -> 36 | seam 20.1 &gt; 18.0 | kept |
| T05 | Enfield | 101 | feather | 15.1 | 8.3 | 8.3 | 20.6 | 0.041 -> 0.043 | 0.84 -> 0.89 | 0.63 -> 0.69 | 113 -> 102 | kept | kept |
| T06 | Enfield | 79 | feather | 7.9 | 4.3 | 4.3 | 16.6 | 0.039 -> 0.021 | 0.89 -> 0.90 | 0.63 -> 0.74 | 88 -> 101 | kept | kept |
| T06 | Hyde | 15 | soft | 12.8 | 6.4 | 0.7 | 22.9 | 0.155 -> 0.065 | 0.68 -> 0.80 | 0.39 -> 0.48 | 0 -> 0 | kept | kept |
| T07 | Hyde | 59 | feather | 10.8 | 6.3 | 6.3 | 17.1 | 0.021 -> 0.011 | 0.89 -> 0.95 | 0.72 -> 0.72 | 2 -> 5 | kept | kept |
| T07 | child | 38 | soft | 23.9 | 13.7 | 8.9 | 31.6 | 0.204 -> 0.060 | 0.55 -> 0.77 | 0.20 -> 0.35 | 0 -> 23 | seam 23.9 &gt; 18.0 | kept |
| T08 | Hyde | 78 | feather | 6.2 | 3.1 | 3.1 | 11.6 | 0.019 -> 0.019 | 0.90 -> 0.93 | 0.70 -> 0.80 | 47 -> 14 | kept | kept |
| T08 | child | 50 | feather | 11.9 | 6.9 | 6.9 | 23.9 | 0.081 -> 0.033 | 0.75 -> 0.79 | 0.36 -> 0.41 | 43 -> 70 | kept | kept |
| T13 | Enfield | 60 | feather | 8.4 | 4.2 | 4.2 | 18.0 | 0.041 -> 0.031 | 0.87 -> 0.91 | 0.63 -> 0.69 | 93 -> 98 | kept | kept |
| T15 | Enfield | 95 | feather | 8.8 | 4.0 | 4.0 | 17.1 | 0.027 -> 0.025 | 0.86 -> 0.90 | 0.73 -> 0.77 | 105 -> 100 | kept | kept |
| T26 | Utterson | 69 | feather | 9.0 | 5.0 | 5.0 | 15.8 | 0.037 -> 0.034 | 0.84 -> 0.89 | 0.60 -> 0.77 | 30 -> 79 | kept | kept |
| T26 | Enfield | 67 | feather | 14.4 | 5.9 | 5.9 | 18.9 | 0.095 -> 0.060 | 0.80 -> 0.84 | 0.33 -> 0.52 | 40 -> 74 | kept | kept |
| T18 | Utterson | 54 | feather | 10.8 | 6.1 | 6.1 | 19.2 | 0.151 -> 0.033 | 0.89 -> 0.93 | 0.35 -> 0.73 | 57 -> 79 | kept | kept |
| T18 | Enfield | 39 | soft | 16.0 | 8.6 | 5.4 | 21.7 | 0.102 -> 0.051 | 0.84 -> 0.91 | 0.27 -> 0.78 | 47 -> 64 | kept | kept |

**Seam.** The old measure was |refined - take| in the outer 8.3 % band of the window. T01 x2 and T07's
child (30-38 px) sit in windows floored at 96 px (2.6-3.2 faces wide, not 2.4); H3 repainted that
background (shop panes into brick, the railing erased) and the feather pasted it: the measure was
right, the paste was wrong. Now a face under 40 px (`face_paste.SOFT_PX` = MIN_SIDE / MARGIN) is pasted
through a soft head mask (1 on an ellipse of 0.7 x 1.0 face heights round the head, a smoothstep to 0
at 1.8x, times the window's own feather; no sharpening anywhere on the paste path), and the seam is
the paste's mean level change OUTSIDE the head (`face_gate.collateral`). Through the old feather the
new measure reads 0.41-0.58 of the old on all 15 rows (median 0.55), so **SEAM_MAX 18 -> 10**: every
hard-paste verdict is unchanged (kept 3.1-8.6, refused 11.1-13.7), and the soft paste takes the three
refused faces to 5.6-8.9. A crop 60 levels off its take still fails the soft paste
(tests/test_face_refine_pastes_a_small_face_softly.py). By eye (scratch strip of T01 and T07 at 3x):
the hard paste cut T07's railing at the box edge; the soft paste keeps it.

**Drift** (`face_gate.drift`, mean |refined - take| inside the face box, T8mars Parity Stitch's idea):
own faces 11.6-31.6 (T07's child, a blob given its face, the top); another row's refined face against a
take's face (64 px regions, 210 pairs) from 23.9, p5 32.4, median 48.9. **DRIFT_MAX 35.**

**Identity.** facenet is a photo model (T01 Utterson 0.04 on his own take). CCIP
(`ccip-caformer-24-randaug-pruned`, OpenRAIL; imgutils' preprocessing ported, MIT; dghs-imgutils not
installed, it pins numpy<2) and clip_vision_h run in `studio/anime_id_worker.py` under the embedded
python, on the sheet's face cut like a take window and 4 + 4 sampled crops. Own sheet: refined CCIP
0.011-0.064, never up by more than 0.002; the other person's sheet on the same crops (12 swaps on
T01 T06 T07 T08 T18 T26): 0.152-0.324. clip rose on all 15 (0.770-0.947 refined) but overlaps the swaps
(0.548-0.852). Rule: CCIP rules (rise > **0.03** or crossing the same-character line 0.1785
refuses); else facenet and clip must BOTH fall (> 0.05, **CLIP_DROP**) to refuse; unread -> facenet
alone. Cost: 12.8 s to load, 1.2 s a face on the GPU, 7.5 s on 4 CPU threads (9 pictures).

**Eyes** (`studio/face_eye.py`, logged, never a wall): the local contrast of the two strongest compact
dark blobs (6-150 px, span <= 22 px, aspect <= 3, fill >= 0.35, darker than the skin median by
max(40, 35 %)) in rows 0.18-0.50 of the 128 px face crop. Written before round 1's numbers were read
and not tuned on them. It ranks the refine above the take on the owner's named faces (T13 93 -> 98,
T26 Utterson 30 -> 79, T26 Enfield 40 -> 74, T06 Enfield 88 -> 101) and on 7 of the 8 faces the bench
read by eye (T01 Enfield 55 -> 36 is the miss); the round-1 Laplacian ranked 2 of those 8. Hyde is
drawn with blank glaring eyes: 0-47 either way, out of its domain.

**Tracking** (`studio/face_track.py`, the script's `take_tracks` / `run_of`; replayed on the 9 bench
takes with the worker's faces down to 0.3 and people): weak faces (0.3-0.6) only continue a track,
within one face height; a lost face re-acquires only its own head. Head colour against the track's
FIRST head overlapped (491 same-person pairs p5 0.70; 275 other p90 0.80); at the 11 real re-acquires
the same person read 0.48-1.00 against the LATEST head and another person 0.46-0.89, so the rule is
relative: at least as like its own latest head as any rival within one sample, and >= 0.4. People
(person_yolov8m-seg, on disk, every 6th frame): a face at 0.100 of the person's height (509 pairs, p10-p90
0.086-0.164), centre 0.125 down; a body made Utterson's T01 track jump onto Enfield, so bodies never
lengthen a track and only make far figures (< 24 px, >= 24 frames, no face near): none on these 9
takes. The crop is the face's soft span (on < 120 px, off > 150), on H3's 17k+5 grid inside its shot
(a trim <= 8 frames and a quarter of the life), one frozen side. Replay against round 1: T01 Utterson
one track 0-120 (round 1 about 0-105), Enfield 0-57 with a 56-frame crop (73); T06 Hyde from frame 0
(17); T08 Hyde's crop stops where his face passes 150 px (141 frames, 175); matched crop frames
1,707 -> 1,673.

**Time per episode (estimate, 11-13 tracked takes, 15-20 faces):** the detector's people +5-7 s a
take on the CPU (T01 8.4 -> 13.6 s, T13 12.3 -> 19.2 s; GPU 0.9 -> 1.8 s), about +1.2 min; the anime
terms 13 s + 7.5 s a face on the CPU, about +2.3 min, inside the gate while later crops render; drift,
eyes and the soft seam under 1 s a face; GPU about -0.3 min (crop frames -2 %). Wall clock about
+1 min (the last take's gate and the worker loads); about +4 min if none of it overlapped.

Still owed: the bench's round-2 GPU arm (render with the new runs and soft paste, owner's eye on the
strips); the 0.4 colour floor, the 24 px body line and DRIFT_MAX 35 are one episode's numbers.
