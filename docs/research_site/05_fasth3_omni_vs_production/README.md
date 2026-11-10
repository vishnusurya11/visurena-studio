# FastH3-Omni versus production on small faces

*Source date: 2026-10-21. A bench that asked whether a newer video model draws small faces better than the model the studio ships. Short answer: no. Production stays.*

## The question

The studio renders each short-episode take with a video model called MiniMax-H3, run locally in ComfyUI on one 24 GB GPU. Small faces (roughly 20 to 70 pixels tall) are where the studio's pictures most often fail. Eyes go soft, faces drift, and figures duplicate.

A newer variant of the same family, called FastH3-OmniRef, was reported to sample faster. The question was narrow: on the same four episode takes, does FastH3 draw small faces better than the current production graphs, and is it fast enough to be worth switching?

## What existed before

- Production (arm A) used two graphs. One uses a Singularity v1.3 base with a turbo LoRA (T06 and T18). The other uses a WULI base (T13 and T26). Both use the Spark-H3 sparse attention node.
- The studio had a face-measurement harness (eye sharpness, identity similarity, duplicate-person checks, and take-level checks such as frozen-frame share). It had never been checked for repeatability on a take with several people in frame.
- An earlier prompt bench had already rendered old-prompt takes on the production graphs. Those were reused as one of the two seeds for arm A where the graph matched exactly.

## Method

**Arms.**
- A = production, each take on its own production graph.
- B = FastH3 split pair, run through ComfyUI's own video-sparse-attention node (VSA, keep 10 percent of tokens). A second variant with dense attention (B2) was planned but not run.

**Takes and faces.** Four episode takes (T06, T13, T18, T26). Six faces were scored. One planned face (T06 Hyde, about 11 pixels tall) was dropped because the reader could not measure him reliably.

**Seeds.** Four seeds per arm: the delivered seed, then plus 1000, plus 2000, plus 3000.

**Pre-registered rules.** Written before any render (PREREG.md), then amended by a dated file (PREREG_amend_2026-10-21.md) before the B-arm renders. The amendment changed three things: the B model (split pair), the attention (VSA, not Spark), and the identity veto (from "any one face" to "mean over six faces"). The amendment also raised the GPU cap from 30 to 45 minutes and moved identity to the first step of the rule.

The rule, in order:
1. Identity veto: reject if the six-face mean of facenet drops by more than 0.05, or the mean CCIP distance rises by more than 0.05.
2. Duplicates: B's clone frames must not exceed A's.
3. Eyes: the eye score must rise by more than 5 on at least 4 of the 6 faces. Faces win only if all three hold.

Cost was reported but was not part of the face verdict. The cost rule was that B's steady seconds-per-step must be at most 1.3 times A's.

**Measures.** Per face: eye sharpness (a pupil-band score on the face crop), a Laplacian sharpness score, facenet and CCIP identity distances, and clip similarity (reported only). Per take: frozen-frame share, a warp check, and a take verdict. Per job: GPU seconds, first-step seconds, steady seconds per step, peak VRAM, and disk read.

**Agents and debate rounds.** The bench and its review ran as separate roles, each written to its own file:
- one bench agent wrote the report (REPORT.md) after the crash-run;
- two critics reviewed it independently, a skeptic and an expert (DEBATE_critic_skeptic.md, DEBATE_critic_expert.md);
- one defender answered both critics (REBUTTAL.md);
- one judge (the "gavel") ruled on every claim, first on the report (VERDICT.md), then on the amended bench (VERDICT_v2.md).

That is one round of critique, one rebuttal, and one judgement, followed by a second judgement after the amended bench. The source folder does not record a count of model calls.

## Results

### Load and crash (first attempt, before the split)

| Item | Value | Source |
|---|---|---|
| Run | FastH3 as shipped, one job | REPORT.md |
| Outcome | Crashed on the first sampler step | REPORT.md |
| Error | Tensor size 24 vs 768 in the output layer | REPORT.md |
| Time to crash | 300.3 s, of which about 270 s streaming 21.0 GB from the data drive | REPORT.md |
| Production cold first step | 9.0 s from NVMe, then 3.31 s per step | REPORT.md |

### Amended bench: per face (mean of 4 seeds; difference is B minus A)

| Face | Eye score A to B | Change | Rose by more than 5? | Face px A to B |
|---|---|---|---|---|
| T06 Enfield | 79.1 to 96.4 | +17.3 | Yes, but unreliable (see below) | 79 to 69 |
| T13 Enfield | 139.4 to 108.5 | -31.0 | No | 67 to 70 |
| T18 Utterson | 75.7 to 68.1 | -7.6 | No | 57 to 46 |
| T18 Enfield | 69.0 to 36.5 | -32.5 | No | 41 to 35 |
| T26 Utterson | 63.7 to 60.9 | -2.8 | No | 69 to 69 |
| T26 Enfield | 48.9 to 47.4 | -1.5 (about -17.8 with a reader zero removed) | No | 67 to 64 |

### Amended bench: the rule

| Step | Measured | Threshold | Outcome |
|---|---|---|---|
| 1. Identity | facenet mean -0.010; CCIP mean -0.002 | veto below -0.05 or above +0.05 | Passes |
| 2. Duplicates | 0 clone frames in A or B | B not above A | Passes |
| 3. Eyes | Rose on 1 of 6 faces (0 of 6 after the re-score) | 4 of 6 | **Fails** |
| Cost (report only) | 0.86 per step, 0.92 per job | at most 1.3 per step | Passes |

### Take scores and frozen-frame share

| Take | A take score (seeds 1 to 4) | B take score (seeds 1 to 4) | B frozen-share failures |
|---|---|---|---|
| T06 | 95, 95, 95, 95 | 95, 95, 95, 100 | None |
| T13 | 44, 43, 44, 50 | 11, 0, 21, 32 | Seeds 1 and 2 hard fail (41 % and 60 %) |
| T18 | 95, 95, 95, 95 | 95, 95, 100, 100 | None |
| T26 | 83, 83, 76, 83 | 55, 83, 65, 82 | Seed 1 hard fail (46 %) |

Production had no frozen-share failures on its 16 renders. FastH3 had three in 16.

### Cost

| Take | A seconds per step | B seconds per step | Step ratio | Job ratio |
|---|---|---|---|---|
| T06 | 6.78 | 6.05 | 0.89 | 0.92 |
| T13 | 9.64 | 7.35 | 0.76 | 0.86 |
| T18 | 5.34 | 5.02 | 0.94 | 0.96 |
| T26 | 3.38 | 2.88 | 0.85 | 0.95 |
| Mean | | | 0.86 | 0.92 |

The first load of the 22 GB base from the system drive cost about 13 s once per sitting. GPU time for the whole amended bench was 35.8 of the 45-minute cap, including the 300 s crash-run.

### Measurement repeatability

The first measurement of the T06 Enfield face in arm A, seed 2, gave two different eye scores on the same file: 118.3 and 69.9. The cause was in the production face-reader, not the renders. When one detector died mid-run, the harness handed the remaining takes to a second, photo-trained detector, which read street lamps as faces.

After the fix, all eight T06 files read the same way twice. Under one reader, arm A's Enfield score on T06 sits between 106 and 118. The re-score on the fixed reader gave T06 Enfield 111.7 to 104.8 (change -6.9), not a rise. No face rose by more than 5 on the fixed reader.

## Images

![Summary card of the amended bench: per-face eye scores, identity, duplicates, the eye rule failing, and the pick of production](images/ab_summary_v2.png)
*Look at the "Eyes" row: B rose on one face of six and the rule needs four.*

![T26 handshake strip: production on top rows and FastH3 split (VSA) interleaved across four seeds](images/ab_strip_t26.png)
*Look at the face sizes and the sharpness of the eyes and hat: the two arms draw the Utterson face at about the same size, and the FastH3 faces look softer.*

![T18 walk-away strip: production and FastH3 across four seeds, with the best take per seed marked](images/ab_strip_t18.png)
*Look at the Enfield figure in the lower rows: FastH3's figures are smaller in frame and their faces are less defined.*

![Verdict card written by the judge after checking the report and both critiques](images/gavel_verdict_card.png)
*Look at the "claim" column: most of the first report's claims were ruled as failing, including the claim that the bug was publishable.*

![The first report's summary card, kept for the record and superseded by the amended bench](images/first_report_card_superseded.png)
*This card is kept as it was. Its "re-run this bench unchanged" line was overruled by the judge.*

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

No audio was produced by this bench.

## Verdict

**Production stays.** Under the amended rule, FastH3 with ComfyUI's VSA attention did not win.

- It did not fail on identity. No identity loss was detected. That does not prove the faces match.
- It did not add duplicate people.
- It did not raise the eye score on enough faces. One face out of six rose, and the rule needs four.
- Its faces were softer. Its sharpness score was lower on 22 of 24 seed pairs under the repeatable reader.
- It froze more often on two takes.
- It was about 8 percent faster per job. That is not enough to offset the extra retakes its frozen frames would cause.

The judge also overruled the first report's card line that said to re-run the bench unchanged. Its claim that the bug was publishable upstream was also withdrawn, because the bug had been fixed in ComfyUI on 2026-10-18.

## What changed in the pipeline

- **Production face-reader fix (commit 279a054 on master).** A reader that died mid-run is now replaced with a fresh worker, and the same take is read again by the same kind of detector. Only two deaths in a row hand the takes to the photo detector. Each refine row records which detector read it.
- **Unreadable eyes are no longer zeros.** A zero eye score on a face 24 pixels or taller is now marked unread, not zero. Below that size, a zero is still a real measurement.
- **New tests.** One test checks that the same file is read the same way on every run. One checks that an unreadable eye is not counted as zero. The full test suite had three failures from an unrelated peer edit, which passed on rerun.
- **Nothing in the production graphs changed.** No workflow JSON was edited. The new bench graphs are new files in the audit folder.

## Limits and open questions

- **One take per face, four seeds.** Six faces across four takes is a small sample. The noise model is rough.
- **The A arm is confounded.** Two takes ran on a different base, LoRA and scheduler. This was a product comparison, not a test of the model alone.
- **Only VSA with keep 10 from step 0 was tested.** Production keeps 20 percent of tokens with four dense warm-up steps. The softness could come from the attention rather than the model. The dense variant (B2) was not run because the amendment only allowed it on a near miss.
- **ComfyUI is not FastVideo's reference setup.** ComfyUI's VSA tiles are 4-by-4-by-4 cubes, not the 128-token tiles in FastVideo's contract. The file is an INT8 export. FastVideo's own receipt says it was not validated on this GPU.
- **The identity veto was changed before rendering.** This is allowed by the dated amendment, and it was made on measured false-veto rates, not on the results.
- **Process lapses.** The GPU lock was released while a job was still queued. A key was sent to the shared console. The measurement script was edited after the renders. The judge found no sign that the edit was tuned to the results, but the lapses are recorded.
- **The face measures are only now repeatable.** Before the fix, a take with several people could switch readers mid-run. Any face bench older than the fix should be re-scored before it is trusted.
- **Open:** the one-variable test (dense FastH3 against dense production at the same seeds) is still unanswered. The studio decides whether to spend GPU time on it.

## Sources

- REPORT (job-4 bench report, 2026-10-21)
- PREREG (pre-registration, 2026-10-21)
- PREREG amendment 1 (2026-10-21, before the B-arm renders)
- DEBATE critic, skeptic (2026-10-21)
- DEBATE critic, expert (2026-10-21)
- REBUTTAL (defender's answer, 2026-10-21)
- VERDICT (judge's ruling on the report, 2026-10-21)
- VERDICT v2 (judge's ruling on the amended bench, 2026-10-21)
- REPEATABILITY (face-measure repeatability and fix, 2026-10-21)
