# Removing the head-area warp by pasting only the face

*Source date: 2026-10-19 (audit folder), replay results up to 2026-10-20. Abstract: the studio's face-refine step re-draws a whole square around each face and pastes that square back, so hat, hair, collar and background wobble; a CPU-only replay shows that pasting only the face removes the ring change almost entirely, but eye clarity, flicker and the number of kept takes are not yet cleared, and no GPU bench has run.*

## The question

The studio makes short episodes from public-domain books. Each episode is built from video "takes", short clips of a character rendered by a local video model. Faces in these takes are often small (15 to 115 pixels tall in a 768 pixel frame). To make small faces readable, the pipeline cuts a square around each face, enlarges it, re-draws it with the video model (MiniMax-H3, a text-and-reference-image-to-video model), and pastes the result back into the frame.

On the Jekyll and Hyde episode (ep01, master_iter2), the owner reported that the head area warps: the hat brim, hair and collar appear to bend and drift from frame to frame. The question for this work was: where exactly does the warp come from, and can the paste be changed so it stops, without a new render?

Terms used below. **H3**: the MiniMax-H3 video model. **Take**: one generated clip, here 768 pixels square. **Refine**: the re-draw of a face crop by H3. **Ring**: the pasted area outside the face itself (hat, hair, ears, collar, background). **Gate**: an automatic check that decides whether a refined take is kept. **DQ**: the studio's data-quality checks. **Denoise**: how much of the source the model may change; 0 keeps everything, 1 redraws everything.

## What existed before

Before this work the paste used one of two masks. Faces 40 pixels or taller used a square feather that replaced all but the outer 8 percent of the crop. Smaller faces used a head-shaped ellipse about 0.7 by 1.0 face heights that still covered the hat crown, hair and collar. The seam gate only read the outer band of the window, and a flicker gate measured frame-to-frame change. Neither gate measured what happened inside the ring, so a drifting hat line passed every check.

## Method

**Source material.** Eleven tracks in eight takes (T05, T06, T09, T10, T13, T15, T23, T26) were audited on the iter1 and iter2 episode masters. iter1 is the earlier master; the takes did not change between the two, so any difference outside the pasted area counts as the paste.

**Audit measures.** Per frame, the window was cut from both masters and shrunk to 384 pixels. Three measures were taken: mean absolute difference (MAD, a 0 to 255 level scale) between iter1 and iter2; geometric shift, from optical flow (Farneback, OpenCV); and wobble, the standard deviation over time of the ring's average displacement. The control was an unrefined take.

**Replay arms.** The refined crops that already existed were re-pasted on the 768 take frames, so no GPU was needed. Each arm changes only the paste.

| arm | what it changes |
|---|---|
| R0 | today's mask (control) |
| R1 | face-only ellipse, about 0.55 by 0.65 face heights, feather inside the face |
| R2a | R1 plus a low-frequency lock from the take and a colour match on the ring |
| R2 | R2a with a stricter band |
| R3 | R2 plus a similarity transform fitted to the ring by optical flow |

A later round (round 2) added R2 with exact take pixels outside the face, plus a new "turn" gate. The turn gate rejects a take when the redraw rotates the face more than 5.5 degrees.

**Agents and debate.** The question was split across eight written angles (audit, flow-aligned paste, face-only masks, eye-only refine, latent-masked video-to-video, temporal consistency, alternatives without a paste, and community methods). The source files do not record how many agents or debate rounds were used, so none is counted here.

**Pre-registered pass marks.** The plan set these before the replay: ring change at most 1.0 (control 0.4); ring warp at most 0.1 px at 384 (control 0.02); ring wobble at most 0.05 px; outside the mask beyond the feather exactly equal to the take; seam at most the old wall of 18; face-edge alignment at most 0.5 px; eye clarity no more than 5 percent below R0; identity no loss against R0.

**Limits of the method.** The replay ran on CPU, so the video model's own behaviour under a new mask was not tested. The source does not define the eye-clarity score, so this write-up reports it as measured and does not claim a direction.

## Results

### Audit of the current paste (iter1 to iter2, window at 384 pixels)

Control (unrefined take): MAD about 0.4, flow about 0.02 px.

| measure | face (pasted) | ring (hat, hair, collar, background) |
|---|---|---|
| mean level change | 17 to 25 | 6 to 13 |
| geometric shift (flow) | 1.3 to 4.1 px | 1.3 to 3.7 px |
| wobble (std of ring shift over time) | n/a | 0.2 to 0.9 px; T06 Hyde 1.3 to 2.0 px |
| flicker, iter1 to iter2 | n/a | falls from 2.4 to 1.9 |

The ring is about 80 percent of the pasted pixels. Flicker went down, so the flicker gate passed. The warp is a slow shift of ink lines, not extra noise.

### Replay: ring metrics by arm (14 face windows)

Source: `replay/measures_replay.json`. Values are as recorded in the file.

| arm | ring MAD, range over windows | ring warp, range | ring wobble |
|---|---|---|---|
| R0 (today) | 6.0 to 13.3 | 1.0 to 3.1 | 0.3 to 2.0 px (audit) |
| R1 | 0.016 to 0.082 | 0.005 to 0.013 | about 0.003 (T05) |
| R2a | 0.014 to 0.070 | 0.005 to 0.012 | about 0.003 (T05) |
| R3 | 0.020 to 0.087 | 0.005 to 0.013 | about 0.003 (T05) |

Every arm brings the ring change below the pass mark of 1.0 on all 14 windows. This is true by construction: a face-only mask leaves the ring as the take's own pixels, so the ring check passes whenever the mask is correct. The ring numbers show the paste is doing what the mask says; they do not show the picture looks right.

### Replay: eye clarity and identity

Eye score, take against R0 and R1 (higher is read as clearer; the source does not define the scale):

| window | take | R0 | R1 | change R0 to R1 |
|---|---|---|---|---|
| T05 Enfield | 103.9 | 69.8 | 64.4 | -8 percent |
| T06 Enfield | 82.6 | 74.1 | 71.0 | -4 percent |
| T10 Hyde | 114.6 | 87.4 | 90.1 | +3 percent |
| T13 Enfield | 108.9 | 102.9 | 100.9 | -2 percent |
| T15 Enfield | 79.2 | 90.9 | 75.7 | -17 percent |
| T18 Hyde | 65.5 | 22.5 | 20.4 | -9 percent |

Identity score (a face-similarity measure; take, R0 and R3): R3 stays within 0.03 of R0 on every window listed in the source (for example T05 0.618 take, 0.684 R0, 0.676 R3; T10 0.834 take, 0.565 R0, 0.571 R3). The R0 score is often higher than the take's, which is the H3 redraw at work.

Under R1, eye clarity drops more than the 5 percent pass mark on T15 (-17 percent) and T05 (-8 percent). R2a and R2 are mixed: R2 falls to 40.0 on T05 and 71.1 against 101.6 on T13, but rises on T26 Hyde and T08. The source does not explain these swings.

### Round 2: exact take pixels and the turn gate

Round 2 measured R2 again on the same windows with exact take pixels outside the face. Ring change and warp are exactly 0.000 on every window (by construction). Flicker rose under R2 on the windows checked: T08 from 17.9 (take) to 22.9; T18 Hyde from 21.9 (take) to 25.6. The source does not say whether this is visible or a metric artefact.

The round-2 gate re-judged every refined person:

| status | people |
|---|---|
| kept before (today's gate) | 14 of 16 |
| kept now (with the turn gate) | 11 of 16 |
| newly rejected | T08 child of Hyde (turn 9.3 degrees), T09 Hyde (8.0 degrees), T26 Enfield (5.8 degrees) |
| rejected both times | T01 Utterson and T01 Enfield (seam 19.3 and 18.3, above the old wall of 18) |

The turn gate removes three takes that looked acceptable to the old gate. The source does not say whether those three takes actually look worse to a viewer; that needs an eye check.

### Images

The strips are in the Images section below. The face-only arms look like the take around the hat and collar, while the face itself carries the H3 redraw.

## Images

![T13 Enfield, 60-pixel face: take, R0 control, R1, R2a, R2 and R3 side by side. Look at the hat band and the collar lines, which stay with the take in R1 to R3.](images/arms_t13_all.png)

![T05 Enfield, 104-pixel face, same six columns as the T13 strip. Compare the hat edge and hair in R0 against R1 to R3, where the ring numbers fall to the take's level.](images/arms_t05_all.png)

![T06 Enfield, 78-pixel face, same six columns as the T13 strip. Compare the eyes in R0 against R1 to R3, where the eye score is the measure to watch.](images/arms_t06_all.png)

![T08 round 2: the top row is the face crop with take, R0, R1, R2 and the H3 redraw; the bottom row is the wider frame. Look at the eye and the outline of the hat; R2 keeps the take's outline.](images/round2_t08_strip.png)

![T18 changed-pixel maps for R0, R1 and R2. Each map marks pixels that differ from the take. Look at the hard vertical boundary in R1 and R2; the source does not explain it, and it needs an eye check for a visible seam.](images/changed_map_t18.png)

![Audit crop for T13 (Enfield, 60 pixels): row one shows iter1 and iter2, the difference map and the mask; row two shows the flow arrows. Look at the hat band and the lapel, where the lines moved.](images/audit_crop_t13.png)

![Audit crop for T06 Hyde (14 pixels, two-person take): the street and lamps differ because the other person's window repainted them. Look at the background on the right side of the window.](images/audit_crop_t06_hyde.png)

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

## Verdict

Paste only the face. On the CPU replay, a face-only mask keeps the hat, hair, collar and background as the take's own pixels, and the ring change falls from 6 to 13 levels to below 0.1 on all 14 windows. The audit attributes the warp the owner saw to the redrawn square (hat, hair, collar, background), which slides against the untouched pixels, not to the take's own motion.

This is not yet a shipped fix. Three things are open: eye clarity falls more than the 5 percent pass mark on two windows under R1, the round-2 gate rejects three takes that the old gate kept, and no GPU bench has tested whether a head-only denoise (the masked re-render) does better. The best candidate for shipping is R1 or R2a, once the eye-clarity loss is explained or accepted.

## What changed in the pipeline

The source does not list commit subjects, and no change to the master or to the face-refine code is recorded in the markdown notes. The changes the sources describe are:

- A replay harness that re-pastes existing refined crops on the 768 take frames, with the measures for each arm (`replay/measures_replay.json`).
- A round-2 harness that adds the R2 arm with exact take pixels outside the face, and a re-judge of every refined person under the new turn gate (`replay/round2/regate.json`).
- The source folder also holds an ep01 master cut named iter3 (1080 and 720 pixel files) and four iter2-versus-iter3 comparison clips (T10, T13, T18, T26). The markdown notes do not describe them, and they were not analysed for this write-up.

## Limits and open questions

- **The ring metric is circular.** A face-only mask makes the ring the take's pixels, so a pass on the ring metric is guaranteed. The eye score, the identity score and a visual check are the real tests.
- **Eye clarity is not defined in the source.** The 5 percent pass mark is applied as written, but the scale and its direction are the studio's, not stated in these files.
- **Flicker rose under R2 in round 2** on the windows checked. Not explained.
- **The changed-pixel map shows hard vertical boundaries** under R1 and R2 on T18. Whether a viewer sees them is unknown.
- **No GPU bench.** The masked re-render (H3 denoising only the face, with the outside held to the take) was planned but not run. The candidate node pack for it was not installed and its licence was not confirmed.
- **Two-person takes** (T06, T10, T26) are worse: one person's window covers the other person and the street. The audit flags these as caveats; the replay numbers for them are reported above but not separated further.
- **Short segments.** T05, T09 and T10 have only 7 to 23 interior frames, so their wobble numbers are weak.
- **Coarse flow.** Farneback at 384 pixels reads shifts of 1 to 4 pixels as an order of magnitude only.
- **Denoise was not varied.** The share of the warp caused by the redraw strength is unmeasured.
- **Licences of candidate tools** (a third-party H3 node pack, SAM 3.1, RAFT weights, a face-parsing model) were not confirmed; no download was made.

## Sources

PLAN ("Face fix without head warp: plan", 2026-10-19); AUDIT OF OUR PASTE ("Head-area warp: audit of our own paste", 2026-10-19); FLOW-ALIGNED PASTE (2026-10-19); FACE-ONLY MASKS (2026-10-19); EYE-ONLY REFINE (2026-10-19); LATENT-MASKED V2V (2026-10-19); TEMPORAL CONSISTENCY (2026-10-19); ALTERNATIVES WITHOUT PASTE (2026-10-19); COMMUNITY 2026 (2026-10-19); replay results (measures_replay, round2 measures and regate, studio audit folder 2026-10-19_face_warp).
