# Lip sync through MiniMax-H3's audio reference: an inconclusive bench and a mouth ruler that was broken

*2026-10-21 (Seattle time). We tested whether feeding the recorded voice line as a reference audio makes an AI-generated character's mouth follow the words. The bench could not give a clear answer, because the instrument that measures mouths turned out to be faulty. Production stays as it was, and nothing was wired.*

## The question

Our video model, MiniMax-H3, makes each short video take from a text prompt, reference pictures and, optionally, audio. In production, the recorded voice line for a take is already given to H3 as a timed audio guide at frame 0. The prompt also says that a reference called `<Audio 1>` is "the take's complete audio track". But no graph ever supplied an `<Audio 1>` reference.

The question was: if we supply the recorded line as a real `<Audio 1>` reference, do the mouths follow the words better than they do now?

Two terms used below:

- **H3** is MiniMax-H3, the video model. **ref2va** is its mode that builds a video from reference images and audio.
- **Lip sync** here means that the mouth opens and closes on the spoken phrases, at the same moment as the voice.

## What existed before

- **Production feeds the voice as a timed guide.** A `MiniMaxH3AddGuide` node puts the recorded line into the take's timeline at frame 0. The model writes its own soundtrack next to it. The mux lag (how far the soundtrack sits from the line) read 0.000 s on every take we checked.
- **The mouth was measured by a face-landmark tool.** A MediaPipe FaceMesh reading of the inner-lip gap was lined up against the voice's loudness envelope. It was advisory only: it could not block a take.
- **The published guidance is mixed.** The MiniMax-H3 model card describes `<Audio N>` as a reference for voice timbre (how a voice sounds), with up to 3 clips of 2 to 15 seconds. The ComfyUI documentation says a reference audio needs at least one reference picture or video. Community notes differ on whether audio references help timing. We found no published, measured result on lip sync with H3.
- **Prior claim in our own report.** The first report said that `<Audio N>` is a timbre channel and carries no timing. This claim was later tested and found false (see Results).

## Method

**Test takes.** Three dialogue takes from the first episode of a Jekyll and Hyde series, all with the same Wuli 8-step model setup. Each take has one close-up of a speaking character. The three takes were the only ones where the face-landmark tool could read the mouth.

**Arms of the bench.**

- **Arm A (production).** The delivered graph, unchanged, at its own seed (s1) and at seed plus 1000 (s2). One re-render of the delivered T25 take was pixel-identical to the file that shipped.
- **Arm B (candidate).** The same graph plus one extra input: the same staged voice composite wired to the reference-audio input. The prompt was not changed. There were 10 renders in total (4 for T25, 3 each for T19 and T22 on arms A and B).

**Rebuttal renders.** Seven more renders tested the claims the first report made:

- **R (reference only).** The timed guide removed, and only the `<Audio 1>` reference kept.
- **N (no audio).** No audio input at all. This is a control for what the prompt alone does.
- **F (frozen audio latent).** The voice is encoded and locked as the audio part of the latent, so the video is generated against a fixed audio stream. It uses only core ComfyUI nodes.

**Measures.**

- *Soundtrack timing.* The zero-lag correlation (r0) between the take's own soundtrack loudness and the recorded line's loudness, plus the mux lag from the studio's audio-sync module.
- *Mouth lag.* The FaceMesh aperture against the voice envelope, with the lag in frames (at 24 frames per second, one frame is about 42 ms).
- *Identity.* Three face-similarity scores (facenet, CCIP, clip) for the tracked character, compared between arms.
- *Voice match.* An ECAPA speaker-embedding similarity between the soundtrack and the recorded line.

**Pre-registration.** Before the bench, the rule was written down: B wins only if the lag improves on at least 2 of 3 takes, correlation rises, no identity score gets worse than 0.05, and no new gate failures appear. For the rebuttal, a second rule said that the reference "carries timing" if the soundtrack correlation is at least 0.5 with the mux lag inside 0.042 s, and at least 0.2 above the no-audio control.

**Who checked the work.** One report agent ran the bench and wrote the first report. Two critics, one with a skeptic brief and one with an expert brief, reviewed it in parallel. A defender answered both critics in one rebuttal round, with new renders. A separate arbiter ("gavel") then ruled on every claim, on the CPU only. After the ruling, a further worker fixed the ruler and wrote a stricter test, the mouth exam. In total: 1 report agent, 2 critics, 1 defender, 1 arbiter and 1 fix worker, with one debate round (critique, rebuttal, ruling).

**Cost.** The bench used about 693 GPU seconds (about 11.5 minutes) on a local RTX 4090. The rebuttal used about 496 GPU seconds. Everything else ran on the CPU at no cost.

## Results

### 1. The first bench (folded ruler, now known to be wrong on mouth lag)

These mouth-lag numbers come from the faulty ruler. Treat them as void. They are kept because the first report used them.

| take | arm | mouth lag (frames) | correlation | readable share of frames | G-WARP gate |
|---|---|---|---|---|---|
| T19 | A seed 1 (delivered) | +17 | 0.47 | 0.73 | eye |
| T19 | A seed 2 | not measured | 0.30 | 0.66 | eye |
| T19 | B seed 1 | not measured | not measured | 0.41 | fail |
| T19 | B seed 2 | not measured | not measured | 0.44 | fail |
| T22 | A seed 1 (delivered) | +13 | 0.54 | 0.99 | pass |
| T22 | A seed 2 | not measured | 0.28 | 0.96 | pass |
| T22 | B seed 1 | +8 | 0.34 | 1.00 | pass |
| T22 | B seed 2 | +8 | 0.31 | 0.91 | pass |
| T25 | A seed 1 (delivered) | -1 | 0.61 | 0.98 | pass |
| T25 | A seed 2 | -1 | 0.61 | 0.94 | pass |
| T25 | B seed 1 | -5 | 0.59 | 0.87 | pass |
| T25 | B seed 2 | -1 | 0.72 | 0.95 | pass |

Against the pre-registered rule, the first bench read "lag better on 1 of 3 takes", which fails the rule. The rebuttal then showed the lag numbers were not reliable.

Identity scores (mean of two seeds, arm A to arm B) were close: facenet 0.777 to 0.788, 0.725 to 0.729 and 0.824 to 0.804 across the three takes. The largest drop was 0.019. The mux gate read 0.000 or -0.010 s on all 12 renders.

### 2. Soundtrack timing: the reference does carry timing

This test removed the timed guide. Renders on takes T22 and T25, at the same seed.

| render | soundtrack r0 | mux lag | voice match (ECAPA) |
|---|---|---|---|
| T22 A seed 1 (production guide) | 0.981 | 0.00 s | 0.842 |
| T22 R seed 1 (reference only) | 0.982 | 0.00 s | 0.878 |
| T22 R seed 2 (reference only) | 0.983 | 0.00 s | 0.865 |
| T22 N seed 1 (no audio) | 0.141 | +0.47 s | 0.331 |
| T25 A seed 1 (production guide) | 0.970 | -0.01 s | 0.847 |
| T25 R seed 1 (reference only) | 0.971 | -0.01 s | 0.911 |
| T25 N seed 1 (no audio) | 0.151 | +0.66 s | 0.374 |

So the `<Audio 1>` reference, on its own, copies the recorded voice onto the soundtrack at the right time. Without any audio, the model says the words late and in a different voice. This is a result about the soundtrack, not about the mouth. It is measured on one model version (Wuli v1.3), with 5 renders.

### 3. Frozen audio latent: feasible with core nodes

The F arm locked the voice as the audio part of the latent, with no download.

| render | soundtrack r0 | mux lag | voice match (ECAPA) |
|---|---|---|---|
| T22 F seed 1 | 0.989 | 0.00 s | 0.946 |
| T25 F seed 1 | 0.977 | -0.01 s | 0.944 |

The voice came through unchanged. Whether the mouths improve is not known.

### 4. The mouth ruler fails its own validity tests

The mouth ruler was re-scored with the voice sign kept and the lag search limited to a fixed window. These are the wrong-voice test (does the right line beat two wrong lines?) and the known-offset test (can the ruler find a known shift?).

| test | result | pass bar |
|---|---|---|
| Right line beats both wrong lines, 10 bench renders | 8 of 10 | 9 of 10 |
| Right line beats both wrong lines, all 17 readable renders | 12 of 17 | 9 of 10 |
| Shift null (true alignment beats shifted copies at p < 0.05), 17 renders | 11 of 17 | not set |
| Known offset found within 2 frames, no-audio renders | 0 of 2 (T22 found +8 for a true +12; T25 saw no signal for a true +16) | 2 of 2 |

On the no-audio renders, the mouth opened about 7 to 9 frames after the line on T22 and about 2 frames after it on T25. The ruler misplaced the first and missed the second.

The first exam (exam v1) gave FAIL for three readers: FaceMesh with a 20-frame window (wrong-line 7 of 10), FaceMesh with a 12-frame window (7 of 10), and a face-crop motion reader (8 of 10). Exam v1 had its own flaws: its truth came from the same estimator it graded, and its shifts overlapped. So its FAIL verdicts were weak evidence. Exam v2 takes its truth from hand labels of mouth-open runs. No reader has passed exam v2, because the labels are not yet made.

### 5. Faults found in the ruler, and fixed

- **Fold bug.** The voice envelope was already normalised, then passed through an absolute-value step a second time. Silence became a bump, so the ruler matched silence to the mouth. Every advisory mouth-lag row written before the fix was wrong. The fix is in the commit with the subject "fix the voice fold in the mouth ruler" (`b5e9cff`). On a synthetic mouth that is 5 frames late, the old ruler read +19 frames and the fixed one reads +5.
- **Clipped peak.** The lag search was limited to plus or minus 12 frames. On delivered T19 the true peak sat at +16 frames, and the ruler reported "0 frames, in sync". The ruler now searches 40 frames each way and says "cannot tell" when the peak sits at or beyond 12 frames. This is in commit `74ee8bc`, along with exam v2 and its tests.

## Images

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

The images below are charts and summary cards only. Frame strips from the H3 renders are not included.

![The first bench summary card, now superseded: the production arm was recommended and the reference was judged not to move the mouths. Read it for the table, not the verdict, which the later ruling replaced.](images/bench_summary_card.png)

![The arbiter's verdict card: all arms tie, the mouth ruler fails the wrong-line and known-offset tests, and the reference is shown to carry soundtrack timing. Read the red cells for the failed tests.](images/gavel_verdict_card.png)

![Zero-lag soundtrack timing for the four audio arms on takes T22 and T25. The green trace is the take's own soundtrack and the grey trace is the recorded line. Look at the R row: it lines up with the production row, and the no-audio row does not.](images/soundtrack_doors_chart.png)

![The fold bug in one plot: the production mouth reading (green) is compared with the true voice (grey) and with the folded voice (red) on three lines. Look at how the folded voice flattens into a constant in the silent stretches.](images/mouth_fold_bug_plot.png)

Audio (A/B listening material, all eight are soundtracks generated by H3 from the same line; each pair is the same take, production arm and candidate arm):

- [T19, arm A, seed 2](audio/ab_t19_arm_a_seed2.wav) and [T19, arm B, seed 1](audio/ab_t19_arm_b_seed1.wav). Listen for the voice matching the line and the timing of the first phrase.
- [T22, arm A, seed 2](audio/ab_t22_arm_a_seed2.wav), [T22, arm B, seed 1](audio/ab_t22_arm_b_seed1.wav) and [T22, arm B, seed 2](audio/ab_t22_arm_b_seed2.wav). Listen for the timing of the two-sentence line.
- [T25, arm A, seed 2](audio/ab_t25_arm_a_seed2.wav), [T25, arm B, seed 1](audio/ab_t25_arm_b_seed1.wav) and [T25, arm B, seed 2](audio/ab_t25_arm_b_seed2.wav). Listen for the single phrase and the silence after it.

The audio is H3 output, so the same licence review should cover it.

## Verdict

**Not shown.** The bench neither proved nor disproved that the reference improves mouths. The ruler that would have judged the mouths cannot tell the right line from a wrong one, and cannot find a known offset. A result that the instrument cannot see is not a result.

**Production is unchanged. Nothing is wired.** Wiring the reference would make every delivered take out of date, so it was not done.

**Two claims from the first report were overturned:**

1. "The `<Audio 1>` reference is a timbre channel that carries no timing" is false on this model. With the timed guide removed, the reference alone copies the soundtrack onto the line's timing.
2. "The production mouth lag was +13 and +17 frames late" is void. Both figures came from the fold bug.

**Confirmed:** the fold bug existed in the code; the production mouth row was affected; the mouth-lag advisory is still not a gate.

## What changed in the pipeline

- **Fold fix (`b5e9cff`).** The mouth ruler no longer folds the voice envelope. A test composes the lag against a mouth that is shifted by a known amount.
- **Window fix and exam v2 (`74ee8bc`).** The ruler searches 40 frames each way and reports "cannot tell" if the peak is at or beyond 12 frames. Exam v2 with its labelled-truth design and three tests was added. A lesson was added to the episode skill's archive about checking the instrument before the result.
- **Production:** no change to the graphs, prompts, or the take gates. The mouth row is still advisory.

## Limits and open questions

- **Small sample.** Three takes, two seeds per arm, one model version (Wuli v1.3). The soundtrack result rests on 5 renders.
- **Seed noise is large.** A fresh seed of the same production graph differed from the delivered seed by as much as the two arms differed (for example, T22 read +8 frames on one seed and -1 on the other).
- **The mouth reader works on close shots only.** FaceMesh could read 1 to 2 percent of frames on the medium shots and the anime style of this book. It is not a usable judge for this style.
- **Pre-registration timing.** The first report said the rule was written before any render. It was not: it was written after one check render and while the first B render was running. No B result existed when the rule was written, but the sentence in the report was wrong. The rebuttal's own rule file was written after its first smoke render had finished and before its first rule-tested render, and the rebuttal disclosed one later edit to its time line (the rules themselves were not changed).
- **The identity comparison used different frame ranges** for the two arms on some takes, and the face tracker fell back to a weaker detector under memory pressure, so identity moves of up to 0.02 are noise.
- **The G-WARP gate flip on T19 is a threshold crossing**, with two seeds (scores 2.42 and 2.59 to 2.80 against a wall of 2.5). It is not evidence of a fault.
- **The prompt still names an `<Audio 1>` that the graph does not supply.** This is a prompt and graph inconsistency with an unmeasured effect. Removing the name or wiring the reference each needs its own test, judged by a reader that passes the exam.
- **Open questions:**
  - Does the frozen audio latent change the mouths? Unknown.
  - Does a lead-in of about 1.2 seconds before the first spoken word help? Untested.
  - Does a new reader, such as a face-detector crop with lower-face motion scored per phrase, pass exam v2? Not yet labelled.
- **Next steps, in order** (all free, on the CPU, until the last): hand-label mouth-open runs on the 17 renders and 5 development takes; grade the existing readers on exam v2 once; pre-register a bench rule on a reader that passes; only then run a GPU bench with at least six seeds per arm; then run the prompt-truth test.
- **Publishable, once the steps are done:** (a) a short note and tool on validating lip-sync measures for stylised generated video, covering the fold bug and the wrong-line and known-offset exam; (b) a measured note on H3's three audio routes. The first measurement is the soundtrack-timing result, which is too small to publish yet.

## Sources

- REPORT, VERDICT, PREREG, PREREG_rebuttal, REBUTTAL (studio audit, 2026-10-21, lip sync via H3 audio reference, job 5)
- Exam RESULT (studio audit, 2026-10-21, mouth ruler and mouth exam)
- DEBATE critic skeptic, DEBATE critic expert (studio audit, 2026-10-21)
- MiniMax-H3 model card (Hugging Face); ComfyUI MiniMax-H3 documentation; ComfyUI-wiki MiniMax-H3 prompt guide; AMD day-0 MiniMax-H3 article; Atlas Cloud MiniMax-H3 lip-sync guide; Singularity v2 model card (Hugging Face); MiniMax-H3 Hugging Face discussion 91 (as cited in the REPORT and REBUTTAL)
