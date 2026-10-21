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
new measure reads 0.41-0.58 of the old on all 15 rows (median 0.55), so **SEAM_MAX 18 -> 10 (withdrawn, below)**: every
hard-paste verdict is unchanged (kept 3.1-8.6, refused 11.1-13.7), and the soft paste takes the three
refused faces to 5.6-8.9. A crop 60 levels off its take still fails the soft paste
(tests/test_face_refine_pastes_a_small_face_softly.py). By eye (scratch strip of T01 and T07 at 3x):
the hard paste cut T07's railing at the box edge; the soft paste keeps it.

**Seam, fix round (2026-10-19 PM; the skeptic's probe).** That measure averaged mask x change over
EVERY pixel outside the head. A small face's soft mask is ~0 over most of its 96 px window, so the mean
was diluted: a crop 60 levels off read 2.5 at a 13 px face, 6.3 at 20 px, 14.7 at 30 px; a +80 halo
right outside the head 2.6 at 13 px. The table's 5.6-8.9 for the three soft faces was that dilution.
The seam is now |refined - take| weighted by the paste mask's slope |grad m| outside the head
(`face_gate.edge_weight` / `edge_change`): the change where the paste passes from the crop to the take,
a ring in head radii for the soft mask, the edge band for the feather. It reads a change D as D at any
size (tests/test_face_gate_reads_the_seam_at_any_face_size.py: 60 levels at 13-36 px, a halo, a change
inside the head reads 0), and through the feather it is round 1's band seam again (15 rows, -1.3 / +0.8),
so **SEAM_MAX is 18 again**. Production gate on round 1's crops with the real CCIP / clip worker
(`bench/round2/gate_smoke.json`): 12 kept, T01 x2 and T07's child refused on the seam, as in round 1.
The soft mask reads the same crops alike (6.1-16.3 kept, 19.8-25.1 refused): it spreads an edge, it
does not hide one; whether it LOOKS cleaner is the eye's, on the GPU arm's strips.

| take | face | px | paste | round-1 band seam | seam, feather | seam, soft mask | seam, paste used | fix-round verdict |
|---|---|---|---|---|---|---|---|---|
| T01 | Utterson | 38 | soft | 21.5 | 22.0 | 22.1 | 22.1 | seam 22.1 &gt; 18 |
| T01 | Enfield | 33 | soft | 20.1 | 20.1 | 19.8 | 19.8 | seam 19.8 &gt; 18 |
| T05 | Enfield | 101 | feather | 15.1 | 14.8 | 15.3 | 14.8 | kept |
| T06 | Enfield | 79 | feather | 7.9 | 8.2 | 8.7 | 8.2 | kept |
| T06 | Hyde | 15 | soft | 12.8 | 11.5 | 9.9 | 9.9 | kept |
| T07 | Hyde | 59 | feather | 10.8 | 11.6 | 12.1 | 11.6 | kept |
| T07 | child | 38 | soft | 23.9 | 23.4 | 25.1 | 25.1 | seam 25.1 &gt; 18 |
| T08 | Hyde | 78 | feather | 6.2 | 6.1 | 6.1 | 6.1 | kept |
| T08 | child | 50 | feather | 11.9 | 12.6 | 13.0 | 12.6 | kept |
| T13 | Enfield | 60 | feather | 8.4 | 8.3 | 8.7 | 8.3 | kept |
| T15 | Enfield | 95 | feather | 8.8 | 8.4 | 8.3 | 8.4 | kept |
| T26 | Utterson | 69 | feather | 9.0 | 8.0 | 8.8 | 8.0 | kept |
| T26 | Enfield | 67 | feather | 14.4 | 13.4 | 13.2 | 13.4 | kept |
| T18 | Utterson | 54 | feather | 10.8 | 10.8 | 11.4 | 10.8 | kept |
| T18 | Enfield | 39 | soft | 16.0 | 15.8 | 16.2 | 16.2 | kept |

Probe, not built (`bench/round2/seam_match.py`): matching the crop's low frequencies to the take's
outside the head (R - blur(R - S) x ramp, sigma face/8) reads the three at 16.0-17.9 and lowers every
kept row 10-48 %: a candidate cleaner blend, to be judged by eye before it is wired.

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
relative: at least as like its own latest head as any rival within one sample, and >= 0.4. Fix round:
with no rival present, and at every sample, a head must read at least the track's own running reading
(median of its 5 nearest consecutive head pairs) less **SELF_SLACK 0.15** (`bench/round2/self_step.py`,
`self_like.py`: 520 same-person consecutive pairs at worst 0.098 under it; nine of ten same-person
re-acquires within 0.04; other people p50 0.33 and p90 0.15 under it, 36 of 416 pass); a track with no
pair of its own is held to the floor only (a bar of 1.0 cut T07's child out). Detections go to tracks by
least total cost (Hungarian: distance from the constant-velocity prediction in reaches, size step in
SIZE_JUMPs, 1 - head likeness): a nearest-first greedy swapped two faces of 36 / 32 px crossing. The
stitch no longer counts the lost piece's own original as its rival. Replay on the 9 bench takes:
identical tracks, +0.4 s. People
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
+1 min (the last take's gate and the worker loads); about +4 min if none of it overlapped. The
anime worker exits after 120 s idle, so takes gated further apart reload it (12.8 s each): up to
about +2.5 min more CPU, overlapped with renders. The fix round's tracker adds about 0.05 s a take.

Still owed: the bench's round-2 GPU arm (render with the new runs and soft paste, owner's eye on the
strips); the 0.4 colour floor, the 24 px body line and DRIFT_MAX 35 are one episode's numbers.

## Face-warp fix: paste the face core only (2026-10-19)

Owner, ep01 master_iter2: "the face fix and eye fix is warping the video around" the head. The audit
(`docs/audit/2026-10-19_face_warp/audit_our_paste.md`, PLAN.md) measured the cause: 9 of 11 tracks pasted
the whole re-rendered square through an 8 % feather, so H3's redraw of the hat, hair, collar and background
replaced the take's (ring MAD 6-13 against a 0.4 control, ink lines 1.3-3.7 px off at 384, wandering with
std 0.2-2.0 px). The flicker wall and the outer-band seam could not see it.

**The paste now** (`studio/face_paste.paste_mask`, `band_lock`, `Paster.paste_one`): only a face-core ellipse,
0.55 x 0.65 face heights round the tracked face (`faces` per frame in new track files, else the window's own
face point), the feather 0.3 face heights INSIDE the outline, exactly 0 beyond it, the same rule at any face
size. In the feather the take's low frequencies replace the redraw's (sigma 0.08 face heights), the redraw's
ink lines stay. The crop is placed by the float box it was cut by (`box_at`, `face_in_patch`): the mask sits
on the face to the sub-pixel; the patch itself is never resampled twice.

**$0 CPU replay** (`docs/audit/2026-10-19_face_warp/replay/measures_replay.json`, strips in `replay/strips/`):
the existing refined crops of the 14 kept ep01 tracks (T05 T06x2 T08 T09 T10x2 T13 T15 T18x2 T23 T26x2) pasted
onto the delivered takes at 768, windows read at 384. R0 = the old paste (HEAD's `face_paste`), R1 = face
core, R2a = R1 + band lock + per-frame Lab match on a ring, R2 = R2a + a ring-fitted similarity registration
(DIS flow, LMEDS, smoothed over 9 frames), R3 = the production `Paster` (face core + band lock + float box).
Harness check: R0's ring MAD sits within 3-7 % of the audit's master-scale numbers on 10 of 11 tracks (T06
Hyde -14 %); its ring flow reads lower (0.90-2.57 vs 1.28-3.73) because the audit read the x4 master.

| measure (ranges over 14 tracks) | R0 | R1 | R2a | R2 | R3 (chosen) |
|---|---|---|---|---|---|
| ring MAD (audit ring: old mask > 0.5 outside the face box) | 6.05-13.31 | 0.02-0.08 | 0.01-0.07 | 0.01-0.07 | 0.02-0.09 |
| ring warp, Farneback px at 384 | 0.90-3.11 | 0.01-0.09 | 0.01-0.08 | 0.00-0.05 | 0.01-0.08 |
| ring wobble, std of the ring's shift | 0.15-2.06 | 0.00-0.07 | 0.00-0.06 | 0.00-0.04 | 0.00-0.06 |
| gate ring warp (1.2-1.8 core radii) | 0.89-2.75 | 0.00-0.01 | 0.00-0.01 | 0.00 | 0.00-0.01 |
| pixels outside the mask moved | (whole square) | 0 | 0 | 0 | 0 |
| outline low-frequency step | 3.63-11.92 | 0.96-3.81 | 0.64-2.67 | 0.63-2.03 | 0.88-2.61 |
| eye band lines vs R0's redraw | 0 | 0.64-2.41 | 1.15-3.25 | 1.88-7.63 | 0.77-2.57 |
| face flicker / the take's | 0.57-0.94 | 0.68-0.96 | 0.75-0.97 | 0.77-0.97 | 0.69-0.96 |

Facenet to the sheet: R3 within -0.01 / +0.03 of R0 on every track (the face core is the same redraw). The
gate on R3: old seam 6.0-16.0 (the logged 6.1-15.1, kept), flicker ratio 0.67-0.95, outside 0, ring warp
<= 0.01: all 14 stay kept. By eye (strips take | R0 | R3): the take's hat band, brim, hair, ears, collar and
background return (R0 had redrawn T18's background into a building and T13's hat band); the drawn eyes are
the redraw's. Refused: R2's similarity warp (registration gained 5-10 %, 40 % only on T06 Hyde, and the
resample blurred the eye lines 2-3x); R2a's Lab match (its per-frame L shift moves 0.9-3.2 levels frame to
frame, a face-wide flicker, for 0.2-0.4 levels less outline step).

**Walls**: `OUTSIDE_MAX` 1 level (rounding), `RING_WARP_MAX` 0.25 px at 384 (the old paste 0.89-2.75, the
face core <= 0.01). The seam keeps round 1's ruler (feather band, a small face's soft head ring) and its
wall 18; the flicker is read on the face-core paste. Residual, by eye: where H3 turned the head (T08's child)
the redrawn face now sits in the take's hood, a pose mismatch the old square hid under a redrawn head; the
GPU bench (PLAN.md 3b, masked re-render) is the next arm. Uncalibrated beyond ep01's 14 tracks.

## Face-warp fix, round 2: brow to chin, the head re-seated, the turn wall (2026-10-19)

The skeptic's review of round 1 (722050e): `CORE_RADII (0.55, 0.65)` were used as RADII, so the outline ran
1.1 x 1.3 face heights across. Drawn over the real frames, it crossed the hat band, the brim's lower edge, the
hair at both sides, the ears, the jaw and the collar's top, and the production Paster still moved the brim and
hairline 0.41-1.42 px at 384 (T05, T18 inside the range the owner complained about). Round 1's ring-warp wall
read a ring where its mask was exactly 0, so it was zero by construction. T08's child was kept with the head
H3 turned. Round 1 also read ep01's tracks as the margin's 1 / 2.4 face: their track files hold no `face_px`,
so T06's 13.5 px Hyde (window 96) was pasted through a core three times his face.

**The paste now** (`studio/face_paste`):
- The core is brow to chin and cheek to cheek: `CORE_HALF` 0.35 across, 0.34 up, 0.34 down (face heights from
  the face box's centre). It is a superellipse of power 4 above the centre, so it is square-shouldered over the
  eyes, and an ellipse below. Its `CORE_FEATHER` is 0.08 face heights, inside the outline. The eyes
  (face_yolov8m: -0.23 to -0.15, out to +-0.22) are the redraw's whole.
- A track file without `face_px` reads its refine.json row's `face_px` over the window side (`face_share`).
- Each redraw frame is put back on the take's head first (`head_shift`). The shift is the median Farneback
  flow take -> redraw on the ring 1.0-1.8 core radii (hat, hair, ears), read at <= 384 px and held to 0.06
  face heights. It is applied with a cubic shift. H3's redraws sit 0.7-2.9 px at 384 off the take's head and
  jitter 0.8-3.9 frame to frame. Under a still head that jitter is the face swimming (the skeptic's shear).
- `paste_patch` is the one paste. The Paster and the gate (`face_gate.pasted_of`) both call it. `blend` now
  rounds instead of truncating (it read 1 level dark where the redraw equals the take).

Probe before the build (`scratchpad fw2/shapes.py`, `reg.py`, `jitter.py`): shrinking the outline alone did
not lower the flow in the feather (0.3-0.9 px for every shape). That flow is the redrawn features next to it,
so the band is not the brim. A smoothed (9-frame) similarity registration changed it by 0-30 % and left the
shear alone. Its eye-line "blur" in round 1's table was a metric artifact: the difference to an UNshifted
redraw scores any shift as lost lines, and the high-pass energy of the eyes is unchanged by a Lanczos shift.
A per-frame translation took the shear 2.72 -> 0.94 (T18 Utterson), 3.08 -> 1.07 (T18 Enfield),
2.65 -> 1.13 (T08).

**$0 CPU replay** (`docs/audit/2026-10-19_face_warp/replay/round2/`: `measures_round2.json`, `regate.json`,
`strips/<track>_f<frame>.png` take | R0 | R1 | R2 | redraw, `strips/<track>_changed.png` where each arm
changed the take). Each arm is the Paster as it shipped or ships, over the delivered takes at 768, read at
384, on the 14 kept tracks. R0 is iter2's paste, R1 is round 1 (722050e), R2 is this round.

| measure (14 tracks) | R0 iter2 | R1 round 1 | R2 this round |
|---|---|---|---|
| ring MAD (the audit's ring) | 1.26-13.21 | 0.01-0.09 | 0.00 |
| brim / hairline flow, px at 384 (round 1's upper feather, the skeptic's region) | 0.70-5.38 | 0.23-1.47 | 0.09-0.45 |
| brim wobble (std of its shift) | 0.12-4.76 | 0.04-1.35 | 0.01-0.37 |
| jaw / collar flow | 1.40-5.30 | 0.51-1.38 | 0.07-0.20 |
| face-vs-head shear, frame to frame, excess over the take | 0.07-1.28 | 0.13-2.61 | 0.12-1.05 |
| facenet to the sheet, R2 - R0 | | | -0.07 / +0.08 |
| face flicker, paste / take (gate) | | | 0.86-1.01 |

The 0.45 brim flow is T06's 13.5 px Hyde; every other track reads <= 0.34. By eye (strips): the take's hat
band, brim, hair, ears, jaw and collar stay. The changed maps show R2 touching only brow-to-chin (R1 took
in the hat band and the collar). The eyes are the redraw's (T13, T18, T26 drawn where the take smudged
them). The "eye lines vs redraw" column rises under R2 (1.88-16.0 against R0's 1.86-9.16) only because the
redraw is shifted onto the take's head. Against R0, the cel eye score rises on 7 of the 12 readable tracks and falls by 6 or less on 4. T13 falls 103 -> 71, though its strip shows both eyes drawn.

**Gate** (`studio/face_gate.paste_measures`, walls in `studio/face_refine`). It reads the paste the Paster makes.
- Outside the core: <= 1 level moves. Every track reads 0.
- **Band warp**: flow take -> paste on the feather and out to 1.2 core radii, `BAND_WARP_MAX` 0.9. R2 reads
  0.27-0.67, and T01's refused faces 0.72-0.95. Read on their own bands, iter2's paste reads 0.46-1.19 and
  round 1's 0.33-0.93. The wall guards against a gross misregistration; it refuses none of ep01.
- **Turn**: the median change of MTCNN's eye line, take -> redraw, over 12 crop pairs at 768 where both read a
  face's landmarks. The face is the one nearest the window's face point; at 6 pairs, or taking the largest
  face, T09 swung to Enfield beside him. `TURN_MAX` is 4 deg. The faces kept by eye read 0.55-2.84 deg.
  T08's child reads 9.34, T09's Hyde 8.03 (a tilt and a smirk), T26's Enfield 5.80 (profile -> three-quarter)
  and T01's Utterson 5.55 (already refused on its seam). A face no detector reads (T06's Hyde) has no turn.
- **Core flow** (take -> paste where it is the redraw whole) is logged, never a wall. After the head shift
  it read T08 2.95, the same as T05 2.95 and T18 3.00: it does not separate a turned head.
- **Regate**: a row measured before these walls (its measures have no `band_warp`) is re-decided on CPU
  before the cut pastes it. `scripts/episode/face_refine.regate_room` runs in `assemble.face_paste_wrap`. It
  keeps the row's stored measures (identity, drift, seam) and takes the paste's measures and the turn again.
  ep01, replayed in memory (`regate.json`; refine.json is not written): 11 of the 14 kept faces stay kept.
  T08, T09 and T26 Enfield fall back to the take.

Uncalibrated beyond ep01's 16 rows. ep01's track files carry no per-frame faces, so its cores sit on the
window's own face point.

## Tiny-face rung (2026-10-19, face-blur round 2 builder; `scripts/episode/tiny_face.py`)

The refine's seam and drift refusals of a planned 20-40 px face (smallest tracked height, `min_px`) on a Spark
take of a square episode earn ONE 1024x1024 draw of the take (bench arm A3c). The draw is kept only when take_dq,
take_content and the take eye pass it; then it is refined again. Replayed on the bench's own refine rows:

| take | face | min / median px | refine | planned | graph | rung |
|---|---|---|---|---|---|---|
| T01 | Utterson | 36 / 37.9 | seam 19.1 > 18 | shot 1 face | Spark (wide) | yes |
| T01 | Enfield | 30 / 33.0 | seam 19.1 > 18 | shot 1 face | Spark (wide) | yes (same draw) |
| T07 | child | 38 / 39.3 | drift 43.3, seam 27.4 | shot 7 face | Wuli (insert) | no: no 1024 Wuli graph; an insert's subject is the boots |
| T06 | Hyde | 11 / 13.5 | kept | shot 6 face | Spark (full) | no: kept, and under the 20 px floor |

The 20 px floor: A3c drew T06's 10-11 px Hyde with no face either way (eye 0 -> 0). The 40 px line is the soft
paste's own (`face_paste.SOFT_PX`). Uncalibrated: a 1024 draw has been judged by no gate yet. The first rung rows
(the eye verdict, take_dq's warp and flicker rows, the refine of the new bytes) are its calibration set.

## The face debate bench (2026-10-21; `docs/audit/2026-10-21_face_debate/`, FINAL.md and `bench/`)

Five debate rounds (8 proposers x 3 refuters) left 20 OPEN items; the ones benchable in <= 15 GPU min each ran
on 2026-10-21 in the paused window (~44 GPU min: VL reads 3, Spark A/B 2 + 8, C9 8, C4 14, C2 5, plus CPU). The
library was only read; every write is under the debate folder. Judged by the production gate (`fs.gate_job`:
turn, seam, flicker, CCIP, clip), the cel eye score on the same track boxes, and the strips by eye.

**C9, a 1024x1024 draw of the same seed (A3c's one change), 5 takes / 9 faces** (`bench/metrics_h3.json`, strips
`bench/strips/c9_T*_strip.png`). Eye cel A0 -> 1024, own tracks: T01 Utterson 44 -> 56, Enfield 57 -> 80; T06
Enfield 113 -> 127, Hyde (10 px) 0 -> 0; T13 Enfield 132 -> 133; T18 Utterson 77 -> 98, Enfield 71 -> 86; T26
Utterson 31 -> 122, Enfield 73 -> 68. Face-window flicker inside the production wall (1.10x + 0.5) on 8 of 9 (T06
Hyde 4.29 > 4.12); CCIP to the sheet DOWN (better) on 8 of 9, clip up on 7 of 9. By eye T13/T18/T26 hold the 768
draw's blocking frame for frame (same seed); T01 re-stages its extras (the couple becomes two women; the person
boxes still match the PANEL at IoU 0.98, as the 768 draw does). Cost 103-251 s a take (1.6-2.0x). The
pre-registered rule (gain >= +5 on every face, flicker inside the wall on every face) fails on T13 (+1.7), T26
Enfield (-5) and the 10 px Hyde, so the 1024 first draw is NOT adopted as a route; it is the strongest lead for
faces under ~70 px, where it gained +12 to +91 on 6 of 6, with identity up. The production path to it stays the
09_08 tiny-face rung (refused 20-40 px faces); widening that rung to 70 px is an owner decision (FINAL.md).

**C4, margin 2.4 -> 1.6 (MIN_SIDE 56), 7 faces: REFUTED.** Gate: 4 of 7 refused on turn (4.1-6.8 deg; T01
Enfield also seam 25.5), 3 kept; the gate's eye score fell on 5 of 7 (T18 Utterson 77 -> 67, T08 child 48 -> 43,
T01 Enfield 55 -> 45, T26 Enfield 73 -> 59, T06 Enfield 113 -> 90) and rose only on refused rows (T13 132 -> 150,
T18 Enfield 71 -> 75). By eye the tighter window re-poses the head more (less context for the guide) and draws no
crisper eye than margin 2.4; T01 Enfield's 1.6 crop drew a readable face but repainted the window (seam 25.5).
The margin stays 2.4.

**C2, the person's expression clause in the crop prompt, 5 renders: REFUTED as a cure.** T08 child (the card's own
"writhes and screams, mouth wide open"): the redraw parts the lips (the VL reads the mouth open) but turns the
head 8.3 / 7.1 deg and warps the band (0.96) or doubles a face; T09 Hyde ("cold, closed-mouth stare"): still
grins, turn 13.8 / 9.9, eye 32 -> 0, a second face. A positive verb is obeyed in part; an absence clause is not
(H3 obeys direction, not amount); neither passes the gate. T13 control kept (eye 132 -> 121). The crop prompt
stays as it is; T08-type expression drift has no prompt cure on this evidence.

**P1 / A37, the VL "same expression?" read on the 14 stored pairs (2 seeds each, agreeing pairs only): 7 of 12
labelled reads agree with the LOOK labels.** It tells the T08 and T09 smiles from their sources (4 of 4) but flips
on the controls (T13 late, T15 late "smile" vs "neutral", T26 mid) and misses T18 p1's mood. Not a classifier
(the pre-registered 7/7 fails); the `expr` column is not built. Wall/engine per read 1.14 warm (4.4-6.8 s engine,
+0.6 s wall; the first read 51 s cold): setup is not the VL's problem (A16).

**A36 blocking: a new draw at a new canvas is a new draw.** 768 take vs 1024 draw person-box IoU: T01 0.0-0.88
(extras re-staged), T06 0.66-0.84; the VL reads both "different" (T06: "moved slightly forward, cane lower").
Against the PANEL both canvases match at IoU 0.90-0.99 on every person. The layout objection to C9 is the seed
lottery every retake already runs, judged by take_content and the take eye; it is not the canvas.

**A40 (C5 pre-test): closed.** Fine texture av3 adds above the 768 base, face window / rest of frame on the iter3
master: T13 7.8, T18 1.05, T26 2.2, T10 2.7 (predicted 0.8-1.2; the ink lines confound it, as refuter 3 said).
Nothing under 0.6, so C5 (paste after av3) closes by its pre-registered rule; arm B was not rendered.

**A41 (eye-band luminance flicker column): DEAD.** On the stored A4 clips SeedVR2 reads 0.98-1.02x the 768
control (av3 0.94-1.04x) where the production face-region flicker had separated it 19-30 %. The column is not
built; `face_paste.region_flicker` stays the ruler. Measures live under `bench/eye_probe.py`, not in `studio/`.

**Spark-H3 A/B (new_models-6), identical seeds.** T26 (73 f, ~11k tokens, under Spark's 12,288 `min_tokens`):
Spark on 72 s and byte-identical to the delivered take (deterministic), off 54.5 s: Spark COSTS 32 % on a short
take and the dense draw is another seed (Utterson eye 31 -> 61, Enfield 73 -> 0). T13 (209 f): see FINAL.md.
