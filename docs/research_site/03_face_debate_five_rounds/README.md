# The Face Debate: Five Rounds on Anime Faces and Eyes

Source date: 2026-10-21 (Seattle time, PDT)

*Eight proposals and three refutations per round, five rounds, then a bench on the GPU. The result: the eye is limited by the model's 32-pixel token, no tested cure makes a lit eye on a small face, and the work that shipped was truthful timing, one cache fix, one worker fix and advisory warnings.*

## The question

Visurena Studio turns public-domain books into short, AI-drawn video episodes. Each episode runs on one local GPU. The studio owner asked for four things at once: make the faces better (especially the eyes), remove the blur on small faces, raise overall quality, and cut the total machine time. The owner also asked for every step to be examined, for online research, and for strong debate before any change.

The problem is specific. In the episode for *Jekyll and Hyde*, faces between about 15 and 120 pixels tall came out soft. Some eyes had no iris. One child's mouth changed from closed to open when the take was refined. The research asked two questions: what makes these eyes soft, and what can be changed without making the film worse somewhere else?

## What existed before

Before this debate, the episode pipeline already had a face refinement step ("face refine"). It works like this:

1. The take is drawn by the video model (MiniMax-H3, called H3 below), in a square 768 by 768 canvas.
2. A tracker follows each face through the take and records its size.
3. Each face that is soft enough is cropped, redrawn by H3 at a lower strength, checked by a set of gates, and pasted back onto the take. The gates check things like identity, head turn, flicker and seams.
4. The episode is upscaled once at the end.

Earlier benches (2026-10-19) had already measured that faces under about 20 pixels gain identity but not features, and that a 1024-pixel draw helped small faces but cost about 1.75 times the render time. The debate itself also found a timing error: a round-3 proposal read summed span times as a 24-minute tracking cost. Round 4 showed it was a unit error and withdrew it.

Two terms used below:

- **Token.** H3 builds the picture from patches of about 32 by 32 pixels. A face or eye smaller than one patch cannot carry detail the model does not already hold.
- **Gate.** A pass/fail check that a render must clear before it is used. The episode pipeline has gates for identity, head turn (in degrees), flicker (frame-to-frame change), seams and more. A "wall" is a gate threshold.

## Method

**Agents and rounds.** Each of the five rounds had 8 proposer agents, each proposing one change, and 3 refuter agents, each trying to break proposals. A chair (the build lead) wrote a ledger after each round. The ledger sorted every proposal into one of three groups:

- **Adopted:** no refuter broke it, the mechanism and a number were stated, and it was already measured or could be benched in 15 GPU minutes or less.
- **Open:** the one bench that would decide it is named.
- **Refuted:** the refutation is named.

The sources do not say whether the chair was a separate agent from the build lead, so this write-up calls the chair "the chair" only. In total, the five rounds used 40 proposer agents and 15 refuter agents (8 and 3 per round). The external review of a third-party workflow (see below) is a separate piece of research and is not counted in those totals. The sources do not name the number of agents for it.

**Arms and seeds on the GPU.** The GPU work ran in one session, from 01:20 to 04:10 PDT, and took about 55 minutes in total (41 minutes of H3 renders, 14 minutes of vision-language reads). The rule was a hard stop at 45 priced minutes for the H3 arms. The main arms:

- **C4, smaller crop margin.** Seven faces re-cropped with a tighter margin (2.4 to 1.6), about 13.7 GPU minutes including the setup.
- **C2, expression wording in the crop prompt.** Five renders (four faces and a control) with two seeds for some faces, about 5.4 GPU minutes.
- **C9, 1024 first draw.** Four takes (T01, T13, T18, T26) drawn at 1024 by 1024 with the same seeds as the stored 768 draws, about 8.2 GPU minutes.
- **Spark attention on and off.** Two takes (T13 with 209 frames, T26 with 73 frames), each drawn with Spark on and off.
- **P1, a vision-language reader.** Fourteen reads, two seeds each, asking whether the mouth is open, closed, smiling or neutral.

**What was measured.** Eye size (a cel score, a count of how much of the eye reads as a drawn eye), gate values, flicker, identity match, head turn, the time each arm took, and the human-looked strips. The ledgers required each arm to be judged against labelled strips, not by the measure the arm itself would raise. The build lead also looked at the strips by eye.

**Pre-registered rules.** Each arm was written with its falsifier before it ran. For example, the C9 arm was to pass only if flicker stayed under the production wall (1.10 times the control plus 0.5) on every face and the eye score gained at least 5 points.

## Results

### Round by round

| Round | Agents | Adopted | Open | Refuted | What the round decided |
|---|---|---|---|---|---|
| 1 | 8 proposers, 3 refuters | 8 | 11 | 9 | Adopted only $0 items (logging, a guard, docs). Refused the wide-eye prompt words and a head-tile reference. Left the 1024 draw open, to be benched on four takes |
| 2 | 8 proposers, 3 refuters | 9 | 13 | 8 | Found the first round's 1024 premise partly wrong (the render row existed). Adopted cost and log items. Kept the eye yardstick (a measure of how well an eye reads) as the first open question |
| 3 | 8 proposers, 3 refuters | 7 | 16 | 9 | Verified the H3 licence text. Refused a 32-pixel floor on the refine and closed the per-frame width idea. Found the white glare under a brim is the sheet's own look, so the eye yardstick must not grade it as a fault |
| 4 | 8 proposers, 3 refuters | 10 | 17 | 9 | Withdrew the "24 minutes of tracking" target (unit error). Adopted the timing fix, the cache key, the whisper worker fix and the tiny-face advisory. Ordered the GPU session (one ComfyUI session, grouped by model, 45-minute stop) |
| 5 (final) | 8 proposers, 3 refuters | 9 | 20 | 7 | Falsified the mouth-ratio measure. Corrected the flicker column (the quoted numbers were the wrong column). Merged the two 1024 proposals into one gated arm. Refused FlashVSR without a bench. Set the commit order and the ranked GPU session |

### Adopted (no GPU render setting changed)

These are the changes that went into the code. None changes how a face is drawn.

| Item | What it does | Number from the sources |
|---|---|---|
| Measured clock | Records how long each refine row waited for the GPU and how long it ran | Stage 972 s of wall time for ep01; 898 s of it was GPU time (92 percent). The earlier "24 minutes of tracking" was a unit error (spans overlap) |
| Readable clause | Logs which of five rules sent a take to the tracker | T19 passed 120.3 px and was tracked with no reason on record; the 120 px wall was left as it was |
| Master-eye cache key | Drops the plan row from the cache key (the verdict is still recomputed from current inputs) | Expected re-read of about 1 minute instead of about 17 minutes (estimate, not measured on a second episode) |
| Whisper worker | Starts the speech-check worker at the first clip and restarts it once if it dies | A 527 s fallback row; expected 60 to 120 s (not measured on a live fault) |
| Tiny-face column | Logs a warning when a named face is under 100 px in the panel | Recall 4 of 4 below 70 px, precision 7 of 8 (in-sample) |

### Refuted by the bench

| Item | Prediction | Measured |
|---|---|---|
| C4, margin 2.4 to 1.6 | A clearly better eye on the three faces under 46 px | 4 of 7 renders refused on head turn (4.1 to 6.8 degrees). The gate eye score fell on 5 of 7. By eye, no crisper eye than margin 2.4, and the head was re-posed |
| C2, expression wording | T08 child's mouth open, T09 Hyde's grin removed | All four refused: the child turned 7.1 to 8.3 degrees, Hyde turned 9.9 to 13.8 degrees, and a second face appeared. The child's lips did part (4 of 4 reads), but the head moved. The grin was not removed (4 of 4 reads still "smile") |
| P1, vision-language expression reader | 7 of 7 agreement with the labels | 7 of 12 agreement. Caught the two smiles (4 of 4) but flipped on controls and missed one mood |
| A41, eye-band flicker column | SeedVR2 at least 1.5 times the 768 control | 0.98 to 1.02 times (0.94 to 1.04 for av3). Dead |
| C5, paste refined core after upscale | Face-to-background texture ratio between 0.8 and 1.2, opens C5 below 0.6 | 7.8, 1.05, 2.2 and 2.7. Nothing under 0.6, so C5 closed |
| Face-refine mouth ratio | Child at least 2 times the controls | 1.03, inside the control band (0.94 to 1.05). T09 Hyde 1.31 caught, T10 kept at 1.22 |

### C9: the 1024 first draw (the one lead that worked)

Drawing the small-face takes at 1024 gave more eye detail on faces under 70 pixels. It did not give a lit eye at 37 pixels.

| Take (face) | Eye score, 768 to 1024 (as the source gives it) | Note |
|---|---|---|
| T01 (Utterson, about 37 px) | 44 to 56; 57 to 80 | Still under one token; the scene re-staged its extra people |
| T06 (Enfield) | 113 to 127 | Above the wall |
| T13 | 132 to 133 | Little change |
| T18 | 77 to 98; 71 to 86 | Two faces, two pairs |
| T26 | 31 to 122; 73 to 68 | One large gain, one small loss |

The source lists two before-and-after pairs for some faces without saying what each pair measures, so both are shown as written.

Other C9 numbers: flicker inside the production wall on 8 of 9 faces (the one failure is Hyde at 4.29 against a 4.12 limit). Identity better on 8 of 9. Blocking (the person-box overlap with the 768 take) for T01 was 0.0 to 0.88 across the counts, and the vision reader said the blocking had changed for T01 and T06. Cost was 103 to 251 seconds per take, 1.6 to 2.0 times a 768 take.

The first pre-registered rule ("+5 on every face") failed on T13 (+1.7) and T26 Enfield (-5), which were already readable faces.

### Spark attention (production setting)

| Take | Frames | Spark on | Spark off | Note |
|---|---|---|---|---|
| T26 | 73 | 72 s (the delivered take, byte for byte) | 54.5 s (24 percent faster) | Under Spark's 12,288-token threshold; the off draw was a different take |
| T13 | 209 | 128 s (the delivered take, byte for byte) | 213 s (66 percent slower) | Long take; the off draw had a different seed path (eye score 132 to 154) |

Spark pays on long takes and costs on short ones. The sources propose a per-take switch above the threshold, not a default change.

### Timing and the episode budget

The studio's budget is at most 6 hours of machine work per 2 to 3 minute episode. The projection for the next episode (ep02) is about 4.0 hours (238 minutes without plan-ahead, 209 minutes with it). The sources treat that as a projection with a falsifier: if ep02 takes more than 4.2 hours, the projection is wrong.

The earlier "3.5 hour" headline was dropped in round 5 because its savings were mostly repair-only costs that a clean pass never sees.

### Tests

Thirteen new tests were written first (red) and then passed (green). The fast test subset (documents, budget and skill checks) passed 237 tests. The full suite ran 13,905 passing, 4 failing, 5 skipped and 10 expected failures. The four failures were the build's own and were fixed in the closing commit.

## Images

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

![Three columns: the stored 768 take, the production refine, and a 1024 redraw of Utterson's face in episode one. Look at the eyes and the hat brim.](images/c9_1024_t01_strip.png)
The 1024 redraw (right) re-stages the street: the extra people move and the eye gain on this face is small (44 to 56, and 57 to 80) and still under one 32-pixel token. This is why a layout check was added before any 1024 minute is spent.

![Three columns: the stored 768 take, the production refine, and a 1024 redraw of a face in take T26, shown in a close crop.](images/c9_1024_t26_strip.png)
The 1024 redraw (right) of T26 is one example of uneven results: the eye score rose on one face (31 to 122) and fell on another (73 to 68).

![Three columns: the stored take, the production refine, and a redraw with the child's expression prompt. The child's head turns in the redraw.](images/c2_expression_t08_strip.png)
With the expression wording, the child's lips part, but the head turns (8.3 degrees), and the redraw was refused.

![Two columns: the source frame (left) and the expression redraw (right) for Hyde's face in episode one. The smile is present on the right.](images/c2_expression_t09_pair.png)
The expression redraw keeps Hyde's smile on the right, while the source on the left is closed-mouthed. The prompt was meant to remove the grin, and it did not.

![Three columns: the stored take, the production refine, and a margin-1.6 redraw of a face in episode one. The head is re-posed in the redraw.](images/c4_margin_t18_strip.png)
The tighter crop (margin 1.6) moves the head, and the gate refused it on the head turn.

![Two columns: the 768 take (left) and the 1024 draw (right) for T01, with boxes around the main figure. The street behind them changes.](images/blocking_t01_pair.png)
In the 1024 draw a man in a top hat stands beside the main figure and the two women in the background change; the vision reader's answer was "two women now together, a man in a top hat appears".

![Four columns with a face and its edge map, showing the texture ratio after the upscale on four faces. Ratio values are printed on each column.](images/texture_ratio_faces.png)
The added-texture ratio on the four faces (T13, T18, T26, T10) was 7.8, 1.05, 2.2 and 2.7. The ink lines confound the ratio, and nothing fell under the 0.6 needed to reopen the upscale-then-paste route (C5).

![Three columns with three rows of an eye band on Hyde's face: the control at 768, an upscaled version (av3), and a SeedVR2 version. The flicker values are printed on each column.](images/flicker_eyeband_t13.png)
The flicker values were 1.33 (control), 1.24 (av3) and 1.33 (SeedVR2), so the eye-band flicker column did not separate the upscalers.

![Three columns: the stored take, the production refine, and a Spark-off redraw of T13 (the third column is labelled spark_off_T13).](images/spark_t13_strip.png)
The Spark-off draw of T13 is a different seed draw, not the same take with a faster setting. The sources note its eye score moved from 132 to 154 and its flicker from 5.1 to 5.5.

## Verdict

1. **The eye floor is the model's token.** Nothing found in five rounds, or on this bench, draws a lit iris into a 4 to 10 pixel eye at 768 pixels.
2. **More pixels per face is the only lead that moved the eye.** The 1024 first draw helped faces between 33 and 68 pixels. It is a new draw, not a refinement, so it changes the composition and costs about twice the time.
3. **No tested cure fixed the expression drift.** The mouth-ratio measure failed (it missed the child and refused a kept face), and the vision reader was not reliable enough to use as a gate.
4. **Upscalers did not help the eye.** SeedVR2 flickered, the proposed FlashVSR arm had no 4090 or anime number and was refused without a bench, and the av3 upscaler stayed.
5. **What shipped:** truthful timing, one cache-key fix, one whisper-worker fix, and two advisory columns. No render setting was changed.

Open decisions for the studio owner, before more GPU time: whether the tiny-face redraw may widen to faces under 70 pixels, whether Spark may switch on for long takes only (a five-take test on ep02 was proposed first), whether a 2160-pixel square delivery may be benched (it changes the shipped spec), whether the ONNX eye detector may be downloaded for the eye yardstick, and the H3 licence application (see Limits).

## What changed in the pipeline

Plain-English commit summaries, from the sources:

- **Measured clock and readable-clause log** (commit 907616f): refine rows record their real GPU and wait times; the tracker records which rule sent a take to it; the decisions file was updated.
- **Master-eye cache key and panel-eye books** (commit b008100): the cache key no longer includes the plan row, and the panel-eye reader's counts are written into its signed record.
- **Whisper worker fix** (commit b8c6ba1): the speech-check worker starts at the first clip and restarts once on failure, with its error output saved to a file.
- **Tiny-face advisory column** (commit fecdd4a): logs a warning when a named face is under 100 pixels in the panel. It does not trigger a redraw.
- **Closing commit** (commit 4db2098): tests and gates updated to read the new columns; the content-check code hash was re-pinned (the gate version did not change).

Other changes: the episode skill's rules and lessons were updated, and a dated decision line was added.

## Limits and open questions

- **The eye yardstick was never built.** The anime eye detector (an ONNX model under an OpenRAIL licence) could not be downloaded during the debate, so every eye score in the research is the older cel score, which counts smears as pupils.
- **The vision reader was not validated.** It agreed with the labels 7 of 12 times.
- **Seed collision in one bench.** The C2 seed-1 crops overwrote the seed-0 files in the shared folder. The gate rows for each seed are correct and the verdict rests on them, but the pair images for seed 0 show seed-1 bytes.
- **Small sample.** Most arms used one seed and between four and seven faces.
- **Projections, not measurements.** The ep02 time projection (about 4.0 hours) and the expected savings from the master-eye cache and the whisper worker are estimates. ep02 timing will test them.
- **Licence.** The MiniMax-H3 licence lists the United States among its excluded territories and points to an application route. The studio's application status is unknown to this research. This write-up grades nothing legal; the licence question belongs to the studio owner and counsel.
- **Third-party workflow not adopted.** A workflow from an outside author, "dual H3 face refine", was reviewed as data only and not run. Its face pass is the same kind as the studio's, run hotter, on one face per clip, with a box paste and no gates. Its whole-take latent upscale was estimated at +40 to 60 minutes per episode (an estimate, not a measurement), and its photoreal LoRAs were judged the wrong look for a cel-anime book. The review's verdict: adopt nothing.

## Sources

- FINAL (face debate, build lead's closing report, 2026-10-21)
- LEDGER round 1, LEDGER round 2, LEDGER round 3, LEDGER round 4, LEDGER round 5 (chair's ledgers, 2026-10-21)
- ANALYSIS (external review of a third-party H3 face-refine workflow, 2026-10-21)
