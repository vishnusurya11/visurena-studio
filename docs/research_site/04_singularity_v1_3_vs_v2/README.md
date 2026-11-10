# Singularity v2 versus v1.3: a GPU A/B on small-face takes

*Source date: 2026-10-21 (Seattle time). One RTX 4090 with 24 GB of VRAM, 64 GB of RAM, ComfyUI 0.41.2.*

*We swapped in a newer community fine-tune of the video model and kept everything else fixed. It gave no clear gain on faces and ran about 4.9 times slower, so the studio kept the old model.*

## The question

The studio renders its short episodes with MiniMax-H3, a video model, run in a reference-to-video mode called ref2va. The studio uses a community fine-tune of that model called Singularity. The version in production is v1.3, a pruned build (a smaller file with parts removed). A newer build, v2, had just been released. The studio owner asked whether v2 would help.

The test had one narrow aim. Small faces were the weak point of recent episodes. Faces at 30 to 60 pixels tall turned soft, lost their eyes or drifted between frames. The question was whether v2 draws those faces better, and what it costs to run.

Terms used below:

- **H3**: MiniMax-H3, the base video model.
- **ref2va**: the H3 mode that takes reference pictures of the characters and makes a clip from them.
- **LoRA**: a small add-on file that nudges a model toward a style. Both arms used the same two LoRAs at strengths 1.0 and 0.7.
- **Gate**: a pass or fail check that a take must clear before it can ship.
- **DQ**: the studio's quality checks on a finished take.
- **Ledger**: the running record of jobs and their cost in time.

## What existed before

- The production model was Singularity v1.3 pruned. Its file is about 21 GB and sits on the fast NVMe system drive.
- Episode 01 had already shipped with four takes routed to the Singularity graph (the workflow that uses this model). The other 24 takes used a different graph, called Wuli.
- The v2 file is about 34 GB. It was downloaded to the slow hard disk, not the NVMe drive.

## Method

**Arms.** Two arms, identical in every input except the model file:

- Arm A: Singularity v1.3 pruned, the production model.
- Arm B: Singularity v2, the candidate.

**Inputs.** Four takes from episode 01, chosen because their faces were small:

| take | scene | faces in the shot |
|---|---|---|
| T06 | Enfield tells the door story; Hyde is tiny in frame | Enfield 52 px, Hyde 11 px |
| T13 | Enfield at the door | Enfield 60 px |
| T18 | Utterson and Enfield walk | Utterson 45 px, Enfield 33 px |
| T26 | Two-shot handshake | Utterson 69 px, Enfield 63 px |

**Controls.**

- The same seeds, prompts, reference pictures, frame counts, LoRAs, 8 sampler steps and the euler/beta sampler.
- The graph came from the production builder, run on a copy of the book's folder. The only change between the two graphs was the model file name.
- Every job ran alone on an empty queue, one at a time. All four v1.3 jobs ran first, then the model cache was cleared, then all four v2 jobs ran.
- A harness check came first. The v1.3 renders of T06 and T18 matched episode 01's delivered takes pixel for pixel (mean squared error 0 on every sampled frame). So the harness reproduces production.

**Face rule.** A face passes only if all three hold:

1. The eye-clarity score rises by more than 5.
2. The flicker score (frame-to-frame jitter inside the face) is not worse.
3. No identity term gets worse by more than 0.05.

The identity terms are facenet (higher is better), CCIP (lower is better) and clip (higher is better). The source calls this the "round-2 rule" and applies it to every tracked face. It does not say the rule was written down in advance.

**Measures.**

- Time: ComfyUI's job history gives the execution seconds and the per-step timings.
- Faces: the studio's face tracker and the cast-matching step give the per-face numbers.
- Motion: a warp score (G-WARP) and a take verdict from the studio's measure step. The verdict here is run without the full production checks, so it is not the full DQ.
- Eyes: a human read of the strips (a mid-shot frame and 384-pixel face zooms), plus four frames from each 3-second clip.

**Agents and debate rounds.** The source does not record how many agents or debate rounds were used. Each take ran with one seed.

**Compute.** The GPU work took 2,029 seconds (33.8 minutes) of a 40-minute cap. Nothing was skipped.

## Results

### Time per take

| take | frames | v1.3 seconds | v2 seconds | slowdown |
|---|---|---|---|---|
| T26 | 73 | 72.7 | 536.0 | 7.4x |
| T18 | 141 | 74.9 | 294.1 | 3.9x |
| T06 | 175 | 89.5 | 534.2 | 6.0x |
| T13 | 209 | 105.3 | 322.7 | 3.1x |
| **Sum** | 598 | **342.4** | **1,687.0** | **4.9x** |

- The first sampler step took 7 to 13 seconds on v1.3 and 180 to 415 seconds on v2. The large first-step cost is the weights streaming in from disk.
- Steady-state steps cost 1.12 to 1.28 times as much on v2, because v2 does not fit in the 24 GB card. Part of it streams from system RAM on every step.
- Every v2 job read 18 to 45 GB from the slow hard disk. The job did not load the model once. It reloaded it each time.
- The GPU was busy 75 to 78 percent of the time on v1.3 and 18 to 38 percent on v2.

### Why v2 is bigger

v1.3 is the pruned build. v2 is not pruned, and its per-block adaptation matrices are full-size. ComfyUI stages 32.4 GB for v2 against 20.0 GB for v1.3. On a 24 GB card, v2 can never be fully resident.

### Face measures

Each row shows the face's pixel height and the scores for v1.3 and then v2 (arrow means "becomes").

| take | person | pixels v1.3 to v2 | eye clarity | flicker | facenet | CCIP | clip | passes the rule? |
|---|---|---|---|---|---|---|---|---|
| T06 | Enfield | 52 to 54 | 113 to 66 | 15.17 to 14.13 | 0.64 to 0.61 | 0.034 to 0.030 | 0.894 to 0.873 | no (eye) |
| T06 | Hyde | 11 to 11 | 0 to 0 | 3.29 to 3.00 | 0.36 to 0.37 | 0.153 to 0.138 | 0.696 to 0.640 | no (too small; clip) |
| T13 | Enfield | 60 to 112 | 98 to 85 | 3.86 to 4.99 | 0.67 to 0.77 | 0.033 to 0.028 | 0.869 to 0.860 | no (eye, flicker) |
| T18 | Utterson | 45 to 30 | 77 to 27 | 21.48 to 19.34 | 0.24 to 0.15 | 0.115 to 0.170 | 0.880 to 0.852 | no (eye, CCIP) |
| T18 | Enfield | 33 to 21 | 71 to 30 | 17.55 to 15.29 | 0.29 to 0.22 | 0.121 to 0.142 | 0.851 to 0.809 | no (eye) |
| T26 | Utterson | 69 to 75 | 67 to 0 | 2.55 to 5.02 | 0.53 to 0.45 | 0.052 to 0.039 | 0.871 to 0.865 | no (eye, flicker) |
| T26 | Enfield | 63 to 66 | 30 to 45 | 3.56 to 7.03 | 0.25 to 0.31 | 0.105 to 0.113 | 0.812 to 0.788 | no (flicker) |

- **Result: 0 of 7 faces pass the rule.**
- Eye clarity is 0 on Hyde's blank eyes by design, so that row is not a real eye score.
- v2 changed the framing on two takes. In T13 it moved the camera closer, so Enfield's face grew from 60 to 112 pixels. In T18 it pulled the camera back, so both faces shrank. Per-face numbers on those two takes therefore compare different shots, not only different models.

### Motion and take verdict

| take | G-WARP S (v1.3 to v2) | G-WARP Se (v1.3 to v2) | state | take verdict, no cells |
|---|---|---|---|---|
| T06 | -1.43 to 0.25 | 0.88 to 1.93 | pass to pass | 95 PASS to 95 PASS |
| T13 | 1.08 to 2.46 | 1.28 to 1.88 | pass to warn | 11 FAIL to 54 FAIL |
| T18 | 1.61 to 1.00 | 2.24 to 1.65 | warn to pass | 95 PASS to 100 PASS |
| T26 | -0.17 to 0.38 | 0.88 to 1.65 | pass to pass | 82 PASS to 85 PASS |

- Se, the warp score for a section, was higher on v2 in three of four takes.
- T13 fails in both arms on the hard "frozen whole take" row. 94 percent of its frames are static on v1.3 and 68 percent on v2. Production rendered T13 on the Wuli graph, not Singularity, so this failure is specific to the Singularity graph on this card.

### Cost per episode

Episode 01 routed 4 of its 28 takes (632 frames) to the Singularity graph.

| case | Singularity takes per draw | change |
|---|---|---|
| v1.3 today (from the studio's cost fit) | about 320 s (5.3 min) | none |
| v2 as measured here (+336 s mean per take) | about 1,664 s (27.7 min) | +22 min per draw; each retake of a wide take adds about 5.6 min |
| v2 on the NVMe drive with weights cached (estimate, never measured) | about 360 s | about +0.7 min |

The studio's episode budget is six hours of machine time. The measured +22 minutes fits inside it, but it buys no face gain.

## Images

![Summary card: v1.3 against v2 on all four takes, with the studio's pick](images/singularity_ab_summary.png)
Look at the summary card: one win each for v1.3 and v2 on the faces, two ties, and a render-time column that shows the 4.9 times slowdown.

![T06 labelled strip: Enfield tells the door story, v1.3 left and v2 right](images/singularity_ab_t06.png)
T06 is a tie. Compare the Hyde figure in the far street and the crispness of the ink lines in the close-up row.

![T13 labelled strip: Enfield at the door, v1.3 left and v2 right](images/singularity_ab_t13.png)
T13 is the one take where v2 looks better. Look at the eyes in the close-up row: v2 has two dark, symmetric eyes, while v1.3 has one pale, glowing eye. Much of the gain comes from v2 framing Enfield closer.

![T18 labelled strip: Utterson and Enfield walk, v1.3 left and v2 right](images/singularity_ab_t18.png)
T18 is the one take where v1.3 looks better. v2 pulled the camera back, and both of its faces turned to soft mush in the close-ups.

![T26 labelled strip: two-shot handshake, v1.3 left and v2 right](images/singularity_ab_t26.png)
T26 is a tie. The faces match, but v2 moves the hands more during the shot, which roughly doubles the face flicker.

![T13 motion strip: four frames from each arm over the same clip](images/singularity_ab_t13_motion.png)
Four frames from each arm's T13 clip. The source measures 94 percent of frames static on v1.3 and 68 percent on v2, which is the frozen-take failure the take verdict flags.

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

Audio: none. The four audio files in the source folder are silence placeholders, not listening samples, so none are copied.

## Verdict

**Reject v2 as a drop-in replacement, for now.**

- **Faces: no gain.** By the pre-registered rule, 0 of 7 faces pass. By eye, v2 wins one take (T13, largely because it framed the face bigger), loses one (T18) and ties two (T06 and T26).
- **Speed: much worse here.** v2 cost 4.9 times the GPU time of v1.3 on the same four takes. The source attributes the gap to the file size (v2 does not fit on the card) and to re-reading the weights from the slow hard disk on every job.
- **Look: unchanged.** Both arms stay in the 1990s cel style. Neither drifted toward photoreal.
- **Production is unchanged.** Nothing was switched.

The studio would revisit v2 only if both of these hold:

1. v2 is moved to the NVMe system drive, which has about 22 GB free. The file is 34 GB, so this needs space freed first.
2. A multi-seed test shows a face gain that one seed per take cannot show.

## What changed in the pipeline

No production code, configuration or existing workflow was changed. The test added:

- A copy of the production graph with one change, the model file name.
- Test scripts to stage the inputs, run the four takes in each arm, and measure the faces, time and motion.
- Raw records: per-job run files, a per-job digest, RAM and disk counters, and a ledger of jobs.

The source does not list commit subjects for this test.

## Limits and open questions

- **One seed per take.** A single seed can hide a real face gain or create a false one.
- **Framing changed.** v2 framed two of four takes differently (T13 closer, T18 wider). Face size drives the eye score more than the model does, so those two takes do not compare cleanly.
- **Small sample.** Four takes and seven tracked faces.
- **Not measured:** v2 on the NVMe drive with weights cached; v2 inside the face-refine graph or the tiny-face graph. The face-refine and tiny-face graphs also load v1.3, so swapping v2 into them would add the same reload cost per job. That cost was not priced.
- **Storage effect.** The source's speed estimate for NVMe is not measured, so the speed verdict could change on fast storage. The face results were measured on the hard disk setup.

## Sources

- AB (GPU A/B, Singularity v2 versus v1.3, 2026-10-21)
- Strip cards: SUMMARY, T06, T13, T18 and T26 labelled strips, plus the T13 motion sheet (same date)
