# Blurry Faces and Eyes in Local AI Video: Measuring a Face-Refine Pass on One Episode

*Source date: 2026-10-19. A small face in a rendered AI video take often comes out blurred or without eyes. The studio built a crop-and-redraw "face refine" pass, measured it on 15 faces across 9 takes, and shipped the version that drew clearer eyes on mid-size faces, while the study's own automatic eye metric failed on this art style and small faces under about 20 pixels stayed faceless.*

## The question

The studio turns public-domain books into short, square, AI-animated episodes. Each episode is built from many short video clips, called takes, rendered by the MiniMax-H3 video model. When a character is small in the frame, the face often comes out soft, with smeared or missing eyes. The question was: can a second, targeted pass over just the face region fix this within the episode's time budget (6 hours of machine time), without making the face look like a different person or adding flicker from frame to frame?

## What existed before

- **The first face pass (F2).** An earlier pass cropped faces, redrew each crop through the video model, and pasted it back. It used an older face detector (MTCNN) and only ran on takes classed as wide or full shots, and only for faces at or under 60 pixels. In the first Jekyll and Hyde episode, that meant 2 takes were refined and T01 (a face about 15 pixels tall) had no row at all.
- **The first master.** The episode's first full pass (master_iter1) had 2 refined takes.
- **The 1024 and 15-step experiments.** A wide-shot setting (15 sampling steps, second LoRA at 0.4) had been added as a flag, but kept off.

Terms used below:
- **H3**: MiniMax-H3, the video model that renders each take.
- **ref2va**: H3's reference-image mode, which takes character sheets as input.
- **LoRA**: a small add-on weight file that changes a model's look or speed.
- **Gate**: an automatic pass/fail check a result must clear before it is kept.
- **Seam**: the visible edge where a pasted face crop meets the rest of the frame (wall: 18).
- **Flicker**: frame-to-frame change inside the face region. A high number means the face shimmers.
- **Facenet / CCIP / clip_vision**: three identity measures. Each compares the face to the character's reference sheet.
- **Drift**: how far the redrawn face moves from the base face.
- **av3**: the studio's standard final upscale (realesr-animevideov3, 4x).
- **SeedVR2**: an alternative video upscaler tested as a replacement for av3.
- **Laplacian variance**: a sharpness number. More texture or edges gives a higher value.

## Method

**Research sweep first.** Before any GPU work, ten web research agents swept news and community reports from about April 2026 onward for newer methods (face restorers, anime-safe detectors, video upscalers, H3 community fixes). Their findings are in the study's PLAN_FINAL document. The conclusion was that nothing new beat the plan already in place: detect, track, crop, redraw through H3, and paste back. The sweep added ports of ideas (a lost-subject guard, a size gate with hysteresis, a drift cap, a body-detector fallback) and three bench arms.

**Round 1 bench (one take set, 9 takes, 15 faces).** Takes T01, T05, T06, T07, T08, T13, T15, T18 (a control the studio had already liked) and T26 were used, with T01 and T07 forced in even though the selection step would have skipped them.
- **A0**: the take as rendered (the baseline).
- **A1/A2**: the new refine crops, pasted back at take scale.
- **A3**: T01 and T06 re-rendered with the 15-step wide setting. No refine.

Pre-registered rules (written before the run, in the plan's section 3): a fix passes a face only if eye sharpness is at least 1.5 times A0, flicker is within 1.10 times the take plus 0.5, identity does not drop by more than 0.05, the seam is 18 or less, and the CCIP distance is at most A0 plus 0.03. Eye sharpness was the Laplacian variance of the eye band.

**Round 2 bench (after the skeptic pass).** The round-2 refine added a least-cost tracker with a head-likeness bar, a soft paste with a feathered head mask under 40 pixels, a drift wall of 35, a seam wall of 18, the CCIP and clip_vision identity terms, and a cel-valid eye score (it counts compact dark pupils rather than raw sharpness). The round-2 arms were:
- **A2**: the round-2 refine at its code head, on the same 15 faces.
- **A2b**: A2 followed by a second pass with the LMS sharpness LoRA.
- **A3b**: T01 and T06 re-rendered with 8 steps, res_2m sampler and beta57 scheduler.
- **A3c**: T01 and T06 re-rendered at 1024x1024, 8 steps.
- **A4**: 3-second clips (72 frames) of T06, T08 and T13, upscaled by av3 versus SeedVR2 3B at 1536.

Round-2 "numbers pass" meant: the cel eye score rose by more than 5, flicker was no worse than the take's, and facenet, CCIP and clip_vision were each no worse than 0.05 below the take. A row passed only if the numbers passed and the eye was clearly better on the strip.

**Agent and debate counts.** The sources give one ten-agent research sweep and one skeptic pass on the round-2 code. They do not give a count of debate rounds for the bench, and this write-up does not invent one.

**Production run.** The round-2 refine was then applied to the first episode's repair (a re-cut of master_iter2). Ten takes were refined before the one av3 upscale, and the other takes were kept byte for byte.

## Results

### Round 1: the first refine arm and the wide-render arm

| Arm | Faces | Result by the pre-registered rule | Notes |
|---|---|---|---|
| A1/A2 (round-1 refine) | 15 | 0 of 15 pass | Eye sharpness 0.58 to 1.12 times A0 (band B), never 1.5 times. Flicker inside its wall on 15 of 15 and lower on 14. Identity up on 14 of 15, never down. Gate kept 12 of 15 (refused T01 Utterson at seam 21.5, T01 Enfield at 20.1, T07 child at 23.9). |
| A3 (15-step wide render) | 4 | 0 of 4 pass | Eye 0.82 to 1.17 times A0. Identity flat. One flicker wall miss (T01 Enfield 13.16 to 15.30). The re-render changed the scene: a background figure became two men. |

Execution: the round-1 refine took 19.5 minutes of GPU for 15 crops. The 15-step draw took 123 s (T01) and 142 s (T06), against 45 s and 59 s for the delivered takes. The round-1 report concluded that the eye metric was not valid on this art style. Dark wrinkle hatching in the old takes was counted as texture, so the metric fell when the refine replaced hatching with clean cel shading.

### Round 2: the refine arms, per face

The round-2 table uses the cel eye score (median over the track, A0 to arm). The Laplacian value is shown for reference only.

| Take | Person | Face px | Eye cel A0 to A2 | Lap A0 to A2 | Flicker take to pasted | Facenet A0 to A2 | CCIP A0 to A2 | Seam / drift | Gate | By eye |
|---|---|---|---|---|---|---|---|---|---|---|
| T01 | Utterson | 36 | 44 to 52 | 47 to 43 | 26.46 to 25.31 | 0.06 to 0.48 | 0.128 to 0.061 | 19.1 / 24.7 | refused (seam) | Eye drawn, but background ghost shows through paste |
| T01 | Enfield | 30 | 55 to 28 | 38 to 20 | 13.23 to 10.60 | 0.31 to 0.74 | 0.102 to 0.044 | 19.1 / 24.1 | refused (seam) | Ghost of background; half hidden |
| T05 | Enfield | 100 | 118 to 79 | 1127 to 735 | 15.71 to 14.42 | 0.64 to 0.64 | 0.040 to 0.050 | 14.3 / 22.5 | kept | No visible gain; A0 already drawn |
| T06 | Enfield | 52 | 113 to 92 | 550 to 482 | 10.66 to 9.00 | 0.63 to 0.78 | 0.042 to 0.042 | 6.0 / 19.4 | kept | Marginal gain |
| T06 | Hyde | 11 | 0 to 0 | 6 to 6 | 3.29 to 2.09 | 0.36 to 0.37 | 0.153 to 0.062 | 9.2 / 21.8 | kept | No change; a dark sliver |
| T07 | Hyde | 47 | 24 to 0 | 334 to 276 | 12.23 to 8.90 | 0.67 to 0.79 | 0.017 to 0.015 | 11.2 / 17.5 | kept | Eyes blank by design; jaw slightly sharper |
| T07 | Child | 38 | 0 to 0 | 18 to 19 | 63.86 to 27.78 | 0.19 to 0.57 | 0.165 to 0.031 | 27.4 / 43.3 | refused (drift and seam) | Refusal is right by eye |
| T08 | Hyde | 50 | 37 to 59 | 293 to 306 | 6.45 to 5.82 | 0.67 to 0.67 | 0.048 to 0.061 | 6.3 / 12.9 | kept | Eyes clearer; smirk becomes a grin (see Limits) |
| T08 | Child | 43 | 48 to 66 | 153 to 117 | 13.54 to 11.88 | 0.34 to 0.46 | 0.074 to 0.028 | 10.7 / 26.2 | kept | Clean blue eyes; mouth closes |
| T13 | Enfield | 60 | 132 to 125 | 534 to 395 | 5.71 to 4.02 | 0.64 to 0.74 | 0.035 to 0.034 | 9.1 / 20.0 | kept | Clearly better: A0 left eye is a smear |
| T15 | Enfield | 94 | 89 to 61 | 2396 to 1423 | 6.42 to 4.70 | 0.72 to 0.76 | 0.030 to 0.023 | 9.4 / 19.3 | kept | No gain; A0 already reads |
| T26 | Utterson | 68 | 31 to 57 | 557 to 380 | 4.77 to 3.47 | 0.58 to 0.76 | 0.037 to 0.032 | 8.4 / 17.2 | kept | Clearly better: defined eye and pupil |
| T26 | Enfield | 62 | 73 to 45 | 380 to 207 | 5.89 to 3.92 | 0.35 to 0.53 | 0.091 to 0.058 | 13.3 / 23.4 | kept | Better: defined eye in place of soft one |
| T18 (control) | Utterson | 45 | 77 to 84 | 170 to 175 | 22.19 to 17.30 | 0.25 to 0.64 | 0.107 to 0.033 | 11.1 / 20.6 | kept | Clearly better: A0 had no eyes |
| T18 (control) | Enfield | 33 | 71 to 71 | 60 to 47 | 19.20 to 12.40 | 0.29 to 0.83 | 0.120 to 0.052 | 16.1 / 22.9 | kept | Better: defined eyes in place of squint smudge |

Round-2 per-arm verdicts:

| Arm | Pre-registered pass | GPU minutes | Verdict |
|---|---|---|---|
| A2 (round-2 refine) | 4 of 15 (T08 Hyde, T08 child, T26 Utterson, T18 Utterson) | 18.6 (15 crops, 32 to 136 s each) | Production arm. By eye, 8 of 15 faces are clearly better. Flicker lower on all 15. Identity never fell past a wall. |
| A2b (LMS sharpness LoRA second pass) | 2 of 3 | 9.7 (3 faces) | Not adopted. Gain small by eye, about 2.1 times A2's GPU cost for the same faces. The gate refused T08 child ("faces 3 != 1"). The LoRA licence is not stated; bench use only. |
| A3b (8 steps, res_2m, beta57) | Fail | 3.5 | Not adopted. Eye down on T01 (44 to 17) and T06 Enfield (113 to 100). Flicker up on 3 of 4. Mushier than A0 on T01. |
| A3c (1024x1024, 8 steps) | Fail on flicker | 6.1 | The most promising lead. Eye up on 3 of 4 faces and identity up on all four. Clean ink lines on T01 both faces. But flicker rose on 3 of 4 (one above its wall), it re-composed the background, and its motion check (G-WARP) was not measured. Cost 1.75 times A3b's 8-step render. |
| A4 (SeedVR2 3B instead of av3) | Fail | 18.9 (SeedVR2); 29 s (av3) | Not adopted. Face flicker 19 to 30 percent above av3's. Clip score fell 0.065 below av3 on T13, past the 0.05 wall. About 2.5 to 6.4 hours per episode at this speed. It draws sharper pupils and more grain. |

Round-2 full bench GPU was about 57 minutes. Tracking and gating ran on CPU, overlapped with the renders.

### The episode repair: iteration 1 against iteration 2

| Measure | master_iter1 | master_iter2 |
|---|---|---|
| Takes refined before the one av3 upscale | 2 | 10 (T05, T06, T09, T10, T13, T15, T23, T26, plus T08 and T18 from iter1) |
| Output | not stated | 3072 x 3072 square, 3,348 frames, 2 min 19.5 s, 856 MB |
| Audio loudness | not stated | -14.2 LUFS, -1.6 dBTP |
| Takes passing the take check | not stated | 27 of 28 (T01 fails gait) |
| Flagged takes shipped | not stated | 2 (T01 gait, T08 clones), 12.0 s of the master |
| Repair clock | not stated | 1.61 h of a 2.38 h cap |

Before-and-after strips are in the Images section. In the episode repair, T01 was re-rendered at 1024 as a new draw; both men became visible, but T01's face paste was refused twice by the seam gate (19.3 and 18.3 against a wall of 18), so its faces are cleaner but still small.

## Images

The strips show the same frame before and after. Read each as: top row is the full frame, lower rows are zooms on the face.

![Jekyll and Hyde episode 1, take T01: iteration 1 on the left and iteration 2 on the right, with the full frame on top and a zoom on Utterson's face below. Look at the two faces at the bottom: the pasted refine is cleaner, but a ghost of the background still shows.](images/ab_strip_t01_iter1_vs_iter2.png)

![Take T13 before and after the repair: iteration 1 on the left, iteration 2 on the right. Compare the face zooms on the lower rows to see the refined Enfield face in iteration 2.](images/ab_strip_t13_iter1_vs_iter2.png)

![Take T26 before and after the repair: iteration 1 on the left, iteration 2 on the right. Compare the face zooms on the lower rows to see which eyes the repair changed.](images/ab_strip_t26_iter1_vs_iter2.png)

![Round 1, take T01 with three arms: the take as rendered (left), the round-1 refine (middle) and the 15-step wide re-render (right). Look at the wide re-render: the background figures change, which shows why a re-render is a new draw and not a fix.](images/round1_strip_t01_wide15_render.png)

![Round 2, take T01 with five arms: the take (A0), the round-1 refine, the round-2 refine, the 8-step res_2m draw (A3b) and the 1024 draw (A3c). Look at the bottom row: A3c draws the cleanest ink lines on the top-hatted face, while A3b washes the face out.](images/round2_strip_t01_arms.png)

![Round 2, take T13 with the take and three refine arms. Look at the left eye of the Enfield face zoom: the take has a smear, and the refine arms draw both eyes symmetrically.](images/round2_strip_t13_refine.png)

![Round 2, control take T18 (the take the owner had already liked). Look at the Utterson face zoom: the take has no eyes, and the refine arms draw them with pupils.](images/round2_strip_t18_control.png)

![Round 2, take T08 with the take and the refine arms. Look at the child's face (bottom row): the refine draws clear blue eyes, but her open mouth closes. The Hyde face (middle row) changes from a smirk to a grin.](images/round2_strip_t08_expression.png)

![Round 2 upscale test on take T06, three versions of the same 3-second face crop: a plain 768 crop, av3 (middle) and SeedVR2 3B (right). Look at the lines: SeedVR2 is crisper at the pupils, but av3 is smoother and cleaner on the flat cel areas.](images/round2_strip_t06_upscale.png)

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

## Verdict

- **Ship the round-2 refine for mid-size faces, roughly 33 to 68 pixels.** It draws clearer eyes where the take has none or a smear (T13, T26, T18 and T08 faces) and does not add flicker or identity loss. Its gate refused the three crops with a visible ghost.
- **Keep av3 as the one final upscale.** SeedVR2 looks crisper at the pupils but flickers more, loses identity on T13, and would take hours per episode.
- **Keep the wide-shot 15-step setting off, and do not adopt the 8-step res_2m setting or the LMS second pass.** None of them improved the faces enough to justify the cost or the drift.
- **Faces under about 15 to 20 pixels do not get a face from a refine.** T06 Hyde (11 to 13 px) was unchanged in every arm. The fix there is a closer framing at plan time, not a second pass.
- **The pre-registered pass rule was not met by any arm in either round.** The studio's own eye metric did not measure what it was meant to on this style. The round-2 report recommended shipping the round-2 refine on the strips and by eye, which the sources say was the deciding read, and the refine was then applied to the episode repair.

## What changed in the pipeline

The sources give commit hashes and what each one did. They do not give the full commit subjects, so the changes are described in plain words.

- **Round-1 refine (commits feb2732 and 531294b):** the new face tracker, the 120-pixel size line (up from 60), smoothed crops and a denoise scaled to face size (0.35 to 0.55).
- **Round-2 refine (commit 8f7cbc5):** the least-cost tracker and head-likeness bar, a soft paste under 40 pixels, the seam wall of 18, the drift wall of 35, and the CCIP and clip_vision identity terms. The round-2 refine was also run on the first episode's repair.
- **Wide-shot setting (commit a5f0973):** the 15-step setting added as a flag and kept off after the round-1 bench.
- **1024 take graph (commit 2aa3a4a, in the comfy_studio repository):** a new workflow file for the 1024 draw, kept separate from the existing workflow.
- **Repair freeze (commits 7cdb216, 52e90bc, d5d5587, 837d1d9):** after a repair run wrongly re-rendered the delivered takes, these commits froze the delivered bytes during a repair and made the dry check show what would render. This is a process change, not a visual one, and it stops a repair from re-rendering delivered takes.

The round-2 report also recommends a fix to the identity reader: after the worker exits on an idle gap longer than 120 seconds, it should restart once before giving up. The sources do not say this fix was built.

## Limits and open questions

- **The sample is small.** It is 15 faces on 9 takes from one episode, judged by one owner's eye and one set of automatic gates.
- **The eye metric failed.** In round 1 it counted the old takes' hatching as texture. In round 2 the cel eye score reads smears as pupils and reads blank-eyed faces as zero. Neither metric is a reliable eye measure on this style. A real measure would need an eye detector, which the studio has not yet accepted.
- **Expression changes.** On T08 the refine closed the child's open mouth and turned Hyde's smirk into a grin. Drift stayed under its wall, so no gate catches expression changes.
- **Faces stay faceless below about 15 to 20 pixels.** T01 Enfield and Utterson stayed small after the repair, and T06 Hyde remained a dark sliver.
- **Ghosting on crowded frames.** Where two figures overlap, the crop's background shows through the paste. The gate refused these crops, which is right, but the faces are not clean.
- **The 1024 draw is promising but unproven.** It was the only arm to draw clean faces on the small T01 figures, but it re-composed the background and raised flicker on three of four faces. It was not measured for motion.
- **Upscaler cost.** SeedVR2 is too slow for a full episode at the tested size, so its quality cannot be judged at the episode scale.
- **Metric changed between rounds.** Round 1 used sharpness and round 2 used the cel eye score, so the two rounds' numbers cannot be compared directly.
- **Licence review pending.** The base model's licence has a territory clause that the studio has not finished reviewing. The LMS LoRA's licence is also unstated, so it is bench-only. Both are owner and legal items.
- **Not uploaded.** The repaired episode was delivered to the studio's master folder, but the publish step parked and nothing was uploaded.

## Sources

- PLAN_FINAL (face blur, final plan, 2026-10-19)
- ITER2_RESULT (Jekyll and Hyde episode 1, master_iter2 face repair, 2026-10-19)
- RERUN (procedure for re-running the episode's face repair, 2026-10-19)
- BENCH (round-1 GPU bench, 2026-10-19)
- BENCH_R2 (round-2 GPU bench, 2026-10-19)
